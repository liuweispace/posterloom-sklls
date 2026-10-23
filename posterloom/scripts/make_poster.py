#!/usr/bin/env python3
"""One command: photo in, finished poster prompt out.

`posterloom.py make` is the whole workflow in one step:

  1. measure the image (scene_analyze)
  2. optionally match a reference poster to pick the style (match_reference)
  3. fill any field that still needs a human or vision model
  4. route to a style
  5. compile the locked generation prompt

Everything it can decide, it decides. Everything it cannot, it states plainly
instead of inventing. The output is the prompt plus a short report of what was
measured and what still needs you.

Usage:
  posterloom.py make photo.jpg
  posterloom.py make photo.jpg --style duotone-identity-stack
  posterloom.py make photo.jpg --reference ref-poster.jpg
  posterloom.py make photo.jpg --type portrait --mood quiet,intimate --tolerance high
  posterloom.py make photo.jpg --out prompt.txt --json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from scene_analyze import analyze  # noqa: E402
import match_reference  # noqa: E402
from rank_styles import rank  # noqa: E402
from compose_prompt import compile_prompt  # noqa: E402


def _split(value: str) -> list:
    return [x.strip() for x in value.split(",") if x.strip()]


def build_profile(args) -> tuple[dict, list]:
    """Assemble a profile, and report which fields still need a human."""
    profile = analyze(Path(args.image))
    needs = list(profile.get("_needs_vision", []))

    if args.type:
        profile["subject"]["type"] = args.type
        if "subject.type" in needs:
            needs.remove("subject.type")
    if args.summary:
        profile["subject"]["summary"] = args.summary
        if "subject.summary" in needs:
            needs.remove("subject.summary")
    if args.anchors:
        profile["subject"]["identity_anchors"] = _split(args.anchors)
        if "subject.identity_anchors" in needs:
            needs.remove("subject.identity_anchors")
    if args.mood:
        profile["mood"] = _split(args.mood)
        if "mood" in needs:
            needs.remove("mood")
    if args.tags:
        profile["subject_tags"] = _split(args.tags)
        if "subject_tags" in needs:
            needs.remove("subject_tags")
    if args.tolerance:
        profile["transformation_tolerance"] = args.tolerance
        if "transformation_tolerance" in needs:
            needs.remove("transformation_tolerance")
    # realism_value has a defensible default: a source-derived poster is
    # photographic unless the caller says otherwise, so do not ask for it.
    if args.realism:
        profile["realism_value"] = args.realism
    if "realism_value" in needs:
        needs.remove("realism_value")
    if args.ratio:
        profile.setdefault("user_preferences", {})["output_ratio"] = args.ratio

    # A human who typed a type and anchors has told us the subject. Infer the
    # person flag from that instead of demanding it again.
    if profile["subject"]["type"] in {"person", "portrait", "face", "headshot"}:
        profile["subject_tags"] = sorted(
            set(profile["subject_tags"]) | {"portrait", "person"}
        )
    return profile, needs


def main(argv):
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2

    import argparse

    ap = argparse.ArgumentParser(prog="posterloom make", add_help=True)
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
    ap.add_argument("--ratio", help="output ratio, e.g. 3:4")
    ap.add_argument("--out", help="write the prompt here")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args(argv[1:])

    try:
        profile, needs = build_profile(args)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    ref_match = None
    style = args.style
    if args.reference and not style:
        try:
            ref_match = match_reference.match(Path(args.reference))
            style = ref_match["best"]["style"]
        except Exception as e:  # noqa: BLE001
            print(f"WARNING: reference match failed ({e}); falling back to routing.",
                  file=sys.stderr)

    route = rank(profile)
    chosen = style or route["primary"]
    lock = route.get("facial_identity_lock") or {}

    try:
        result = compile_prompt(profile, forced_style=chosen)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: prompt compilation failed: {e}", file=sys.stderr)
        return 1
    # compile_prompt returns (prompt_text, meta_dict).
    prompt, meta = result if isinstance(result, tuple) else (result, {})

    if args.out:
        Path(args.out).write_text(prompt, encoding="utf-8")

    if args.json:
        payload = {
            "image": args.image,
            "style": chosen,
            "style_name": next(
                (s["name"] for s in json.loads(
                    (ROOT / "data/styles.json").read_text(encoding="utf-8")
                )["styles"] if s["id"] == chosen), chosen),
            "routed": route["primary"],
            "confidence": route["confidence"],
            "identity_lock": bool(lock.get("active")),
            "measured": profile.get("_measured", {}),
            "needs_vision": needs,
            "reference_match": ref_match,
            "prompt": prompt,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    # Human-readable report.
    print(f"IMAGE     {args.image}")
    print(f"STYLE     {chosen}")
    if not args.style:
        print(f"          (routed: {route['primary']}, confidence {route['confidence']})")
    if ref_match:
        print(f"          (matched from reference: {ref_match['measured']})")
    m = profile.get("_measured", {})
    print(f"MEASURED  contrast {m.get('contrast')} · saturation {m.get('mean_saturation')} "
          f"· density {m.get('density')} · hue clusters {m.get('hue_clusters')}")
    print(f"          palette: {', '.join(profile.get('palette', []))}")
    print(f"LOCK      {'identity lock ON' if lock.get('active') else 'no face in source'}")
    if needs:
        print(f"TODO      needs your eyes: {', '.join(needs)}")
        print("          (add with --type/--summary/--anchors/--mood/--tolerance)")
    print()
    print("=" * 68)
    print()
    print(prompt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
