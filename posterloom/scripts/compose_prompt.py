#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rank_styles import rank
import face_identity

# Two source-binding modes. Most styles treat the photograph as a visual layer to
# transform. The distillation styles treat it as semantic evidence only, so the
# global block must not tell the model to keep the photo visible.
_GLOBAL_TAIL = """OUTPUT
Create one finished poster, default {ratio} unless the user specifies another ratio.
Never create a collage, contact sheet, moodboard, scrapbook, album, multi-panel layout, or composite from unrelated source images.
{extra_output}

TYPOGRAPHY
Typography is restrained. Text normally occupies 5–10% or less of the visual area.
Use a short title only when it improves the poster. Subtitle is optional and limited to one short line.
Never cover a face, key hand gesture, important sign, architectural crown, or defining object contour.

QUALITY
Keep intentional hierarchy, believable material behavior, source-derived color logic, and style-specific edge/texture behavior.
Avoid generic AI fantasy, excessive glow, random particles, fake fog, malformed architecture, duplicated subjects, illegible typography, oversaturated HDR, and one-click-filter appearance.
"""

GLOBAL_ANCHOR = """SOURCE BINDING
Use exactly one source photograph as the factual and visual anchor.
Preserve the defining identity of the subject, especially the listed identity anchors.
Do not replace the subject with a different person, object, building, costume, location, brand, date, or historical claim.
""" + _GLOBAL_TAIL

GLOBAL_SEMANTIC_REFERENCE = """SOURCE BINDING
Use exactly one source photograph as SEMANTIC EVIDENCE — a reference for meaning, subject, gesture and relationship, not as a visual layer to keep.
The photograph is not to be reproduced, embedded, cropped, collaged, traced, or retained as photographic pixels in the output.
The poster must contain original illustration, paper and typography only.
Preserve the SEMANTIC identity of the subject: the same core subject, the same relationship, the same gesture and gaze, the same spatial logic. Reinterpret how it looks, never what it means.
Do not introduce a different person, object, building, costume, location, brand, date, or historical claim that the source does not support.
""" + _GLOBAL_TAIL


def global_block(style, ratio):
    """Build the global instruction block for the routed style."""
    semantic = (style.get("source_role") or "visual-anchor") == "semantic-reference"
    extra = (
        "The output is a single authored artwork, not a reproduction of the photograph."
        if semantic else
        "You may crop, simplify, shift, enlarge, reduce, or extend quiet background when it improves poster composition and does not alter source identity."
    )
    tmpl = GLOBAL_SEMANTIC_REFERENCE if semantic else GLOBAL_ANCHOR
    return tmpl.format(ratio=ratio, extra_output=extra)

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def style_by_id(style_id):
    for style in load(ROOT/"data/styles.json")["styles"]:
        if style["id"] == style_id:
            return style
    raise SystemExit(f"Unknown style: {style_id}")

def scene_block(profile, ratio=None):
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
Output ratio: {ratio or prefs.get('output_ratio','3:4')}
"""

def compile_prompt(profile, forced_style=None):
    route = rank(profile, top=5)
    primary = forced_style or route["primary"]
    style = style_by_id(primary)
    # Ratio precedence: an explicit user request wins, then the style's own
    # designed ratio, then the source photo's measured aspect, then 3:4.
    # The measured aspect must not beat a style's designed ratio — the zine
    # styles are 3:5 by design regardless of the photo's shape.
    prefs = profile.get("user_preferences", {}) or {}
    ratio = (
        prefs.get("requested_ratio")
        or style.get("default_ratio")
        or profile.get("_measured_source_aspect")
        or prefs.get("output_ratio")
        or "3:4"
    )
    blocks = [
        global_block(style, ratio),
        scene_block(profile, ratio),
        f"PRIMARY STYLE — {style['name']}\n{style['prompt_block']}",
    ]

    # Named color system. Competitors that specify concrete hex values rather than
    # adjectives ("warm", "muted") get measurably better color results, because the
    # model has to interpret adjectives but can execute a value.
    cs = style.get("color_system")
    if cs:
        lines = [f"COLOR SYSTEM — {style['name']}"]
        if cs.get("substrate"):
            lines.append(f"Substrate / paper: {cs['substrate']}")
        if cs.get("inks"):
            lines.append(f"Inks (exactly these two): {', '.join(cs['inks'])}")
        if cs.get("accent"):
            lines.append(f"Accent: {cs['accent']}")
        if cs.get("coverage"):
            lines.append(f"Coverage: {cs['coverage']}")
        for name, ramp in (cs.get("ramps") or {}).items():
            stops = " -> ".join(f"{k} {v}" for k, v in ramp.items())
            lines.append(f"Ramp '{name}' (shadow to paper): {stops}")
        lines.append(
            "Use these values literally. Do not substitute adjectives such as warm, "
            "muted, or vintage for the named inks."
        )
        blocks.append("\n".join(lines))

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

    # Facial identity lock. Injected for every profile containing a recognizable
    # human face, regardless of the routed style, and placed after the style block
    # so it is not diluted by aesthetic instructions.
    lock = face_identity.build(profile, style_id=primary, style_name=style.get("name"))
    if lock:
        blocks.append(lock["block"])
        negatives.insert(0, lock["negative"])

    blocks.append("NEGATIVE CONSTRAINTS\n" + "\n".join(f"- {x}" for x in negatives))

    if lock:
        if face_identity.identity_mode(primary) == "abstract":
            # An abstract illustration is not a likeness claim, so the gate checks
            # derivation rather than pixel-level facial match.
            blocks.append(
                "FRAMING\n" + lock["headroom"]
                + "\n\nDELIVERY GATE\nThis poster is not acceptable until the illustrated figure "
                "has been checked against the source for derivation: head shape, head angle, hairline, "
                "apparent age, gesture and gaze direction. If the figure has drifted into a different "
                "person or a generic one, regenerate. Do not require photographic facial fidelity — "
                "this style is explicitly non-photographic."
            )
        else:
            blocks.append(
                "FRAMING\n" + lock["headroom"]
                + "\n\nDELIVERY GATE\nThis poster is not acceptable until the generated face has been "
                "compared against the source on face shape, eye shape and spacing, eyebrow shape, nose "
                "shape, mouth shape, hairline, and skin tone. If it does not match, regenerate."
            )

    if lock and face_identity.identity_mode(primary) == "abstract":
        blocks.append(
            "FINAL CHECK\nBefore generation, verify one source image -> one independent poster, "
            "the figure is derived from the source rather than invented, the output contains no "
            "photographic pixels, typography is restrained, and no unsupported factual content is invented."
        )
    else:
        blocks.append(
            "FINAL CHECK\nBefore generation, verify one source image -> one independent poster, "
            "identity anchors are protected, typography is restrained, and no unsupported factual content is invented."
        )
    prompt = "\n\n".join(blocks)

    if lock:
        route = dict(route)
        route["facial_identity_lock"] = {
            "active": True,
            "identity_risk": lock["identity_risk"],
            "heavy_transformation_requested": lock["heavy_transformation_requested"],
            "identity_mode": face_identity.identity_mode(primary),
        }
    return prompt, route

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
