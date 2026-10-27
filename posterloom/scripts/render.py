#!/usr/bin/env python3
"""One command: photo in, finished poster images out.

`posterloom.py render` closes the loop that `make` leaves open.

  1. measure the image (scene_analyze)
  2. route to a style (rank_styles)
  3. compile a prompt that fits the backend's budget (compact_prompt)
  4. generate N images, each a different composition (variation + generate)
  5. write them to disk and report what was produced

Three posters are three DESIGNS, not three samples of one design. One API call
with `n=3` returns three samples of the same prompt — same composition, same
layout, differing only in rendering detail. Since the API takes one prompt per
request, distinct designs require distinct requests. Each request carries a
per-variant layout directive that changes the ARRANGEMENT — crop, placement,
use of negative space — and leaves the style, palette, medium and identity
lock untouched.

The full posterloom prompt (4000-8000 characters) is the right artifact for a
long-context chat model and the wrong artifact for an image API with a 1500
character cap. So this builds a second, budget-aware prompt rather than
truncating the first — the identity lock and the named colour values survive,
the scene-map restatement does not.

Usage:
  posterloom.py render photo.jpg
  posterloom.py render photo.jpg --count 3 --out ./posters
  posterloom.py render photo.jpg --style duotone-identity-stack --count 3
  posterloom.py render photo.jpg --backend minimax --ratio 3:4
  posterloom.py render photo.jpg --count 3 --json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import compact_prompt  # noqa: E402
import describe  # noqa: E402
import generate as gen  # noqa: E402
import variation  # noqa: E402
from compose_prompt import style_by_id  # noqa: E402
from make_poster import build_profile  # noqa: E402
from rank_styles import rank  # noqa: E402


def _ratio_for(style: dict, profile: dict, requested: str = None) -> str:
    """Explicit request wins, then the style's designed ratio, then the photo."""
    if requested:
        return requested
    prefs = profile.get("user_preferences", {}) or {}
    return (
        prefs.get("requested_ratio")
        or style.get("default_ratio")
        or profile.get("_measured_source_aspect")
        or "3:4"
    )


def render(argv) -> int:
    """argv excludes the program name."""
    import argparse

    ap = argparse.ArgumentParser(prog="posterloom render", add_help=True)
    ap.add_argument("image")
    ap.add_argument("--style", help="force a style id")
    ap.add_argument("--reference", help="reference poster to match the style from")
    ap.add_argument("--type", help="subject type: portrait, landscape, architecture, ...")
    ap.add_argument("--summary", help="one factual sentence about the subject")
    ap.add_argument("--anchors", help="comma separated identity anchors")
    ap.add_argument("--mood", help="comma separated moods")
    ap.add_argument("--tags", help="comma separated subject tags")
    ap.add_argument("--tolerance", help="transformation tolerance: low|medium|medium-high|high")
    ap.add_argument("--realism", help="realism value: low|medium|high|very-high")
    ap.add_argument("--ratio", help="output ratio override, e.g. 3:4")
    ap.add_argument("--count", type=int, default=3, help="how many images to generate")
    ap.add_argument("--backend", help="backend id (default from data/backends.json)")
    ap.add_argument("--out", default="posterloom-out", help="output directory")
    ap.add_argument("--prefix", default=None, help="output filename prefix")
    ap.add_argument("--no-reference", action="store_true",
                    help="do not send the source photo to the backend (default)")
    ap.add_argument("--send-reference", action="store_true",
                    help="attach the source photo to the image request "
                         "(keeps likeness, but often returns a photograph)")
    ap.add_argument("--no-describe", action="store_true",
                    help="skip the vision description and use the profile's subject fields")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    # Reuse `make`'s profile builder so both commands agree on what a profile is.
    try:
        profile, needs = build_profile(args)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    ref_match = None
    style_id = args.style
    if args.reference and not style_id:
        try:
            import match_reference
            ref_match = match_reference.match(Path(args.reference))
            style_id = ref_match["best"]["style"]
        except Exception as e:  # noqa: BLE001
            print(f"WARNING: reference match failed ({e}); falling back to routing.",
                  file=sys.stderr)

    route = rank(profile)
    chosen = style_id or route["primary"]
    try:
        style = style_by_id(chosen)
    except SystemExit as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    backend_name = args.backend or gen.load_backends().get("default", "minimax")
    ratio = _ratio_for(style, profile, args.ratio)

    # Build the budget-aware prompt for THIS backend.
    try:
        backend = gen.get_backend(backend_name)
    except KeyError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    limit = int(backend.get("max_prompt_chars", 1500))

    out_dir = Path(args.out)
    prefix = args.prefix or Path(args.image).stem
    # The reference is NOT sent by default. Measured: attaching the source
    # photo forces the model to reproduce its continuous tone, and the flat
    # print collapses back into a photograph — the same prompt returns a print
    # without the attachment and a photo with it. The photo's role is to be
    # read by the vision model, not to be pasted into the image request.
    reference = Path(args.image) if args.send_reference else None

    # Describe the photo in words before generating.
    #
    # This is measured, not stylistic preference. When the source photo is
    # attached to the image request, the model reproduces its continuous tone
    # and the flat-print style collapses back into a photograph — the same
    # prompt yields a print without the attachment and a photo with it. So the
    # default path describes the subject with a vision model and generates from
    # text. The description is factual only: no style, no mood, no artwork.
    subject_override = None
    describe_error = None
    if not args.no_describe:
        try:
            raw = describe.describe_identity(args.image)
            subject_override = compact_prompt.to_print_language(raw)
            subject_override = "Subject: " + subject_override
        except Exception as e:  # noqa: BLE001
            describe_error = str(e)

    prompt = compact_prompt.build_compact(
        profile, style, budget=limit - 60, subject_override=subject_override)

    # Three posters must be three DESIGNS, not three samples of one design.
    #
    # Measured: one API call with `n=3` returns three samples of the SAME
    # prompt. They differ in rendering detail — grain, edge softness, exact
    # crop — but the composition is the same sheet three times. That is not
    # "three options".
    #
    # The API takes one prompt per request, so distinct designs require
    # distinct requests. Each variant differs only in ARRANGEMENT: crop,
    # placement, use of negative space. The style, the ink palette, the medium
    # and the identity lock are identical across the set, so all three are the
    # same style by three compositions.
    from face_identity import identity_mode, has_face_risk

    mode = identity_mode(chosen)
    variants = variation.layout_variants(
        style, args.count, identity_mode=mode,
        has_face=has_face_risk(profile))
    if not variants:
        variants = variation.layout_variants(
            style, 1, identity_mode=mode, has_face=has_face_risk(profile))

    # With --json, stdout carries only the JSON document so it can be piped
    # into jq or a script. The human-readable summary goes to stderr.
    out = sys.stderr if args.json else sys.stdout

    def say(*parts):
        print(*parts, file=out)

    say(f"STYLE     {chosen}")
    if not args.style:
        say(f"          (routed: {route['primary']}, confidence {route['confidence']})")
    if ref_match:
        say(f"          (matched from reference)")
    say(f"BACKEND   {backend_name} / {backend.get('model')}")
    say(f"RATIO     {ratio}")
    say(f"PROMPT    {len(prompt)} chars (backend limit {limit})")
    say(f"COUNT     {len(variants)}")
    say(f"VARIANTS  {', '.join(v['id'] for v in variants)} (one request each)")
    if subject_override:
        say(f"SUBJECT   described from the photo ({len(subject_override)} chars)")
    if describe_error:
        say(f"NOTE      could not describe the photo ({describe_error}); "
            "using the profile's subject fields instead")
    if needs:
        say(f"TODO      needs your eyes: {', '.join(needs)}")
    say()

    # One request per variant, so each sheet is a different composition.
    # Each variant gets its own prompt: the style's own composition plus this
    # variant's arrangement directive.
    produced = []
    all_notes = []
    used_ratio = ratio
    model = backend.get("model")
    ref_sent = False
    failures = []

    for v in variants:
        v_prompt = prompt
        if v["text"]:
            v_prompt = compact_prompt.build_compact(
                profile, style, budget=limit - 60,
                subject_override=subject_override,
                layout_override=v["text"])
        try:
            res = gen.generate(
                backend_name, v_prompt,
                ratio=ratio, count=1,
                reference=reference, out_dir=out_dir,
                prefix=f"{prefix}-{v['id']}",
            )
        except Exception as e:  # noqa: BLE001
            failures.append(f"{v['id']}: {e}")
            continue
        for note in res.get("notes", []):
            if note not in all_notes:
                all_notes.append(note)
        used_ratio = res.get("used_ratio", used_ratio)
        model = res.get("model", model)
        ref_sent = ref_sent or bool(res.get("reference_sent"))
        for path in res["images"]:
            produced.append({"variant": v["id"], "path": path})

    if not produced:
        detail = "; ".join(failures) if failures else "backend returned no images"
        print(f"ERROR: generation failed: {detail}", file=sys.stderr)
        return 1

    for note in all_notes:
        say(f"NOTE      {note}")
    if reference and not ref_sent:
        say("NOTE      the source photo was not sent to the backend")
    if failures:
        say(f"NOTE      {len(failures)} variant(s) failed: "
            + "; ".join(failures)[:200])
    say()
    for item in produced:
        say(f"IMAGE     {item['path']}  [{item['variant']}]")
    say()
    say(f"Done: {len(produced)} image(s) in {out_dir}")

    if args.json:
        print(json.dumps({
            "image": args.image,
            "style": chosen,
            "routed": route["primary"],
            "confidence": route["confidence"],
            "backend": backend_name,
            "model": model,
            "requested_ratio": ratio,
            "used_ratio": used_ratio,
            "reference_sent": ref_sent,
            "prompt_chars": len(prompt),
            "prompt": prompt,
            "subject_described": bool(subject_override),
            "variants": [
                {"id": v["id"], "layout": v["text"]} for v in variants
            ],
            "images": [item["path"] for item in produced],
            "image_details": produced,
            "notes": all_notes,
            "needs_vision": needs,
        }, ensure_ascii=False, indent=2))
    return 0


def main(argv):
    """argv[0] is the program name, as in sys.argv."""
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    return render(argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
