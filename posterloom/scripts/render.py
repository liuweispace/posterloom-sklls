#!/usr/bin/env python3
"""One command: photo in, finished poster images out.

`posterloom.py render` closes the loop that `make` leaves open.

  1. measure the image (scene_analyze)
  2. route to a style (rank_styles)
  3. compile a prompt that fits the backend's budget (compact_prompt)
  4. generate N images (generate)
  5. write them to disk and report what was produced

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
    say(f"COUNT     {args.count}")
    if subject_override:
        say(f"SUBJECT   described from the photo ({len(subject_override)} chars)")
    if describe_error:
        say(f"NOTE      could not describe the photo ({describe_error}); "
            "using the profile's subject fields instead")
    if needs:
        say(f"TODO      needs your eyes: {', '.join(needs)}")
    say()

    try:
        result = gen.generate(
            backend_name, prompt,
            ratio=ratio, count=args.count,
            reference=reference, out_dir=out_dir, prefix=prefix,
        )
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: generation failed: {e}", file=sys.stderr)
        return 1

    for note in result.get("notes", []):
        say(f"NOTE      {note}")
    if not result.get("reference_sent") and reference:
        say("NOTE      the source photo was not sent to the backend")
    say()
    for path in result["images"]:
        say(f"IMAGE     {path}")
    say()
    say(f"Done: {result['count']} image(s) in {out_dir}")

    if args.json:
        print(json.dumps({
            "image": args.image,
            "style": chosen,
            "routed": route["primary"],
            "confidence": route["confidence"],
            "backend": backend_name,
            "model": result.get("model"),
            "requested_ratio": ratio,
            "used_ratio": result.get("used_ratio"),
            "reference_sent": result.get("reference_sent"),
            "prompt_chars": len(prompt),
            "prompt": prompt,
            "subject_described": bool(subject_override),
            "images": result["images"],
            "notes": result.get("notes", []),
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
