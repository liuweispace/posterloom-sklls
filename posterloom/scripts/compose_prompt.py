#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rank_styles import rank

GLOBAL = """SOURCE BINDING
Use exactly one source photograph as the factual and visual anchor.
Preserve the defining identity of the subject, especially the listed identity anchors.
Do not replace the subject with a different person, object, building, costume, location, brand, date, or historical claim.

OUTPUT
Create one finished poster, default 3:4 vertical unless the user specifies another ratio.
Never create a collage, contact sheet, moodboard, scrapbook, album, multi-panel layout, or composite from unrelated source images.
You may crop, simplify, shift, enlarge, reduce, or extend quiet background when it improves poster composition and does not alter source identity.

TYPOGRAPHY
Typography is restrained. Text normally occupies 5–10% or less of the visual area.
Use a short title only when it improves the poster. Subtitle is optional and limited to one short line.
Never cover a face, key hand gesture, important sign, architectural crown, or defining object contour.

QUALITY
Keep intentional hierarchy, believable material behavior, source-derived color logic, and style-specific edge/texture behavior.
Avoid generic AI fantasy, excessive glow, random particles, fake fog, malformed architecture, duplicated subjects, illegible typography, oversaturated HDR, and one-click-filter appearance.
"""

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def style_by_id(style_id):
    for style in load(ROOT/"data/styles.json")["styles"]:
        if style["id"] == style_id:
            return style
    raise SystemExit(f"Unknown style: {style_id}")

def scene_block(profile):
    subject = profile.get("subject", {})
    prefs = profile.get("user_preferences", {})
    join = lambda k: ", ".join(map(str, profile.get(k, [])))
    return f"""SCENE MAP
Subject: {subject.get('summary', subject.get('type','unknown'))}
Subject type: {subject.get('type','unknown')}
Identity anchors: {', '.join(subject.get('identity_anchors', []))}
Environment: {profile.get('environment','')}
Lighting: {join('lighting')}
Mood: {join('mood')}
Geometry: {join('geometry')}
Palette: {join('palette')}
Materials: {join('materials')}
Text-safe zones: {join('text_safe_zones')}
Realism value: {profile.get('realism_value','')}
Transformation tolerance: {profile.get('transformation_tolerance','')}
Requested title: {prefs.get('title','')}
Requested subtitle: {prefs.get('subtitle','')}
Output ratio: {prefs.get('output_ratio','3:4')}
"""

def compile_prompt(profile, forced_style=None):
    route = rank(profile, top=5)
    primary = forced_style or route["primary"]
    style = style_by_id(primary)
    blocks = [
        GLOBAL,
        scene_block(profile),
        f"PRIMARY STYLE — {style['name']}\n{style['prompt_block']}",
    ]

    if route.get("hybrid") and not forced_style:
        h = route["hybrid"]
        secondary = style_by_id(h["secondary"])
        blocks.append(
            f"""CONTROLLED HYBRID
Primary: {h['primary']} ({int(h['primary_share']*100)}%)
Secondary: {h['secondary']} ({int(h['secondary_share']*100)}%)
Secondary subsystem only: {h['secondary_role']}
Use the secondary style only for that subsystem. Do not merge the two languages uniformly.
Secondary guidance: {secondary['prompt_block']}
"""
        )

    negatives = [style["negative_prompt"]]
    if route.get("hybrid") and not forced_style:
        negatives.append(style_by_id(route["hybrid"]["secondary"])["negative_prompt"])
    blocks.append("NEGATIVE CONSTRAINTS\n" + "\n".join(f"- {x}" for x in negatives))
    blocks.append(
        "FINAL CHECK\nBefore generation, verify one source image -> one independent poster, "
        "identity anchors are protected, typography is restrained, and no unsupported factual content is invented."
    )
    return "\n\n".join(blocks), route

def main():
    ap = argparse.ArgumentParser(description="Compile a PosterLoom generation prompt.")
    ap.add_argument("profile")
    ap.add_argument("--style", help="Force one direct style id.")
    ap.add_argument("--output")
    ap.add_argument("--route-output")
    args = ap.parse_args()

    profile = load(args.profile)
    prompt, route = compile_prompt(profile, args.style)
    if args.output:
        Path(args.output).write_text(prompt + "\n", encoding="utf-8")
    else:
        print(prompt)
    if args.route_output:
        Path(args.route_output).write_text(
            json.dumps(route, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

if __name__ == "__main__":
    main()
