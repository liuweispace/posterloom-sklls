#!/usr/bin/env python3
"""Add portrait-dedicated styles to PosterLoom.

Portrait work needs styles whose whole mechanism is *preserving* a face, not
repainting it into a medium. The existing library only offered stylized
treatments (watercolor, screenprint, ink wash), which reliably redraw facial
structure and produce a different-looking person.

Each new style declares high realism and low transformation, and its prompt
block leads with explicit facial-geometry locking so the image model treats the
face as fixed geometry to render, not as content to reinterpret.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "data/styles.json"

# Anchor vocabulary reused across the three styles so routing matches the
# same normalized tokens the rest of the library already uses.
SUBJECT = ["portrait", "person", "human", "face", "headshot", "figure", "performance"]
LIGHTING = ["natural", "window-light", "studio", "soft", "directional", "practical-light", "twilight", "overcast"]
MOOD = ["quiet", "intimate", "calm", "reflective", "dignified", "contemplative", "warm"]
GEOMETRY = ["shallow-depth-of-field", "centered", "rule-of-thirds", "close-crop", "bust", "portrait-orientation"]
MATERIALS = ["skin", "hair", "fabric", "texture", "eye", "glass"]
PALETTE = ["source-derived", "muted", "warm-cool", "neutral", "earth-tone"]
REALISM = ["high", "very-high"]
TRANSFORM = ["low", "medium-low"]

PORTRAIT_STYLES = [
    {
        "id": "editorial-portrait",
        "name": "Editorial Portrait",
        "family": "photographic-portrait",
        "role": "direct",
        "status": "gold",
        "best_for": [
            "portrait and headshot",
            "magazine and interview features",
            "human-interest stories",
            "founder and team portraits",
        ],
        "reject_if": [
            "no human subject is present",
            "the user explicitly wants a painterly reinterpretation",
            "identity anchors cannot be established from the source",
        ],
        "mechanism": (
            "Render the existing face, not a new one. Treat facial geometry as fixed "
            "input: preserve face shape, bone structure, eye shape and spacing, eyebrow "
            "shape, nose and mouth shape, jawline, hairline, skin tone and texture, "
            "apparent age, expression, and gaze direction. Change only framing, lighting "
            "refinement, background treatment, and typography."
        ),
        "composition": (
            "Use editorial portrait framing with a clean headroom relationship and "
            "generous negative space. Separate the subject from the background through "
            "depth, tone, or restrained environmental context. Keep the face unobstructed "
            "and free of overlaid graphic elements."
        ),
        "lighting": (
            "Preserve the source light direction. Refine into soft directional key with "
            "gentle falloff and clean shadow separation. Do not add rim lights, catchlights, "
            "or dramatic contrast that the source does not motivate."
        ),
        "color_logic": (
            "Source-derived skin rendering with believable subsurface tone. Keep highlights "
            "soft on skin, avoid orange oversaturation, and preserve natural lip, hair, and "
            "fabric color relationships."
        ),
        "material_language": (
            "Render skin with visible but restrained texture: pores, fine lines, natural "
            "variation. Hair keeps strand direction and density. Fabric keeps weave and "
            "weight. Avoid plastic smoothing, beauty filters, and airbrushed skin."
        ),
        "typography": (
            "Small editorial serif or grotesk, usually 3-6% of poster height, placed in a "
            "text-safe zone that never crosses the face or hands."
        ),
        "realism": "high",
        "transformation": "low",
        "routing": {
            "subject": SUBJECT,
            "lighting": LIGHTING,
            "mood": MOOD,
            "geometry": GEOMETRY,
            "materials": MATERIALS,
            "palette": PALETTE,
            "realism": REALISM,
            "transform": TRANSFORM,
        },
        "negative_prompt": (
            "No changed facial features, no altered face shape or jawline, no eye-shape or "
            "eyebrow drift, no age shift, no gender shift, no beautification or plastic skin, "
            "no airbrushing, no heavy makeup addition, no changed hairline or hairstyle, no "
            "costume change, no extra or missing fingers, no duplicate or composite faces, "
            "no glamor retouch, no fantasy lighting, no dramatic rim light, no oversaturated "
            "HDR skin, no text across the face."
        ),
        "variation_knobs": [
            "crop tight-bust/half-body",
            "background simplification subtle/moderate",
            "grain fine/none",
            "type serif/grotesk/minimal",
            "caption none/tiny",
        ],
        "prompt_block": (
            "Transform the single source photograph using the **Editorial Portrait** visual system. "
            "The photograph is the factual anchor and the face is FIXED GEOMETRY, not content to reinterpret.\n\n"
            "Mechanism: Reproduce this exact person's face. Preserve face shape, bone structure, eye shape "
            "and spacing, eyebrow shape, nose and mouth shape, jawline, hairline, skin tone and texture, "
            "apparent age, expression, and gaze direction. Do not beautify, de-age, age-shift, or gender-shift.\n\n"
            "Composition: Editorial portrait framing with clean headroom and generous negative space. "
            "Keep the face unobstructed and free of graphic overlays.\n\n"
            "Lighting: Preserve the source light direction. Refine into soft directional key with gentle "
            "falloff. No unmotivated rim lights or catchlights.\n\n"
            "Color: Source-derived skin rendering, believable subsurface tone, soft highlights on skin, "
            "natural lip and hair color.\n\n"
            "Material: Skin texture with restrained visible pores and fine lines. Hair keeps strand direction "
            "and density. Fabric keeps weave and weight. No plastic smoothing or beauty filter.\n\n"
            "Typography: Small editorial serif or grotesk in a text-safe zone that never crosses the face or hands."
        ),
    },
    {
        "id": "fine-art-portrait",
        "name": "Fine Art Portrait",
        "family": "painterly-portrait",
        "role": "direct",
        "status": "gold",
        "best_for": [
            "classic painted portrait treatment",
            "cultural and heritage portraits",
            "editorial illustration of a real person",
            "portraits where some painterly surface is desired",
        ],
        "reject_if": [
            "the user needs an exact photographic likeness",
            "no human subject is present",
            "the subject is a group where individual faces must stay distinguishable",
        ],
        "mechanism": (
            "Apply a painted surface while holding the likeness constant. The brushwork "
            "describes the existing face; it must never redefine it. Keep facial proportions, "
            "feature placement, expression, and age faithful to the source, and confine painterly "
            "energy to surface, edge, and light."
        ),
        "composition": (
            "Use time-honored portrait composition with a clear value structure and a calm background. "
            "Maintain the source head angle and eyeline. Avoid cropping through the top of the head "
            "or tight jaw framing unless the source already uses it."
        ),
        "lighting": (
            "Build painterly light consistent with the source direction, using soft blended transitions "
            "and preserved shadow shape. Keep facial modeling readable rather than dramatic."
        ),
        "color_logic": (
            "Limited, harmonious painterly palette derived from the source. Modulate skin with adjacent "
            "warm and cool tones rather than uniform flesh color. Keep saturation below poster-print intensity."
        ),
        "material_language": (
            "Visible but controlled brush direction in background, clothing, and secondary planes. "
            "The face stays comparatively smooth and resolved, with detail concentrated in eyes and "
            "mouth. Avoid heavy impasto on facial features."
        ),
        "typography": (
            "Classic serif, small, low-contrast against the painted field. Sits in negative space and "
            "never overlaps the face."
        ),
        "realism": "high",
        "transformation": "medium-low",
        "routing": {
            "subject": SUBJECT,
            "lighting": LIGHTING,
            "mood": MOOD + ["reverent", "nostalgic"],
            "geometry": GEOMETRY,
            "materials": MATERIALS,
            "palette": PALETTE + ["earth-tone", "sepia"],
            "realism": REALISM,
            "transform": TRANSFORM,
        },
        "negative_prompt": (
            "No changed facial proportions, no rounder or narrower face, no exaggerated painterly features, "
            "no melted or smeared eyes, no asymmetric drift between eyes, no doll-like face, no heavy impasto "
            "on facial features, no caricature, no age shift, no beautification, no plastic skin, no costume "
            "change, no duplicate faces, no anachronistic costume, no text across the face."
        ),
        "variation_knobs": [
            "painterly energy background/light",
            "palette warm/cool/muted",
            "brush texture fine/visible",
            "type serif/classic/minimal",
            "caption none/tiny",
        ],
        "prompt_block": (
            "Transform the single source photograph using the **Fine Art Portrait** visual system. "
            "Apply a painted surface while holding the likeness constant.\n\n"
            "Mechanism: The brushwork describes this exact face and must never redefine it. Preserve facial "
            "proportions, feature placement, expression, gaze, and apparent age. Confine painterly energy to "
            "surface, edge, and light.\n\n"
            "Composition: Classic portrait composition with clear value structure and calm background. Keep "
            "the source head angle and eyeline. Avoid cropping the top of the head.\n\n"
            "Lighting: Painterly light consistent with source direction, soft blended transitions, preserved shadow shape.\n\n"
            "Color: Limited harmonious palette derived from the source. Modulate skin with adjacent warm and cool "
            "tones rather than uniform flesh color.\n\n"
            "Material: Visible controlled brush direction in background and clothing. Face stays comparatively smooth "
            "and resolved, with detail concentrated in eyes and mouth. No heavy impasto on facial features.\n\n"
            "Typography: Small classic serif in negative space, never overlapping the face."
        ),
    },
    {
        "id": "photojournalistic",
        "name": "Photojournalistic",
        "family": "documentary-portrait",
        "role": "direct",
        "status": "gold",
        "best_for": [
            "candid and reportage portraits",
            "environmental human stories",
            "street photography posters",
            "maximum likeness fidelity",
        ],
        "reject_if": [
            "the user wants a designed or art-directed look",
            "the source is already heavily manipulated",
            "no human subject is present",
        ],
        "mechanism": (
            "Maximum fidelity to the source moment. Preserve the face exactly as captured, "
            "including asymmetry, expression, skin texture, clothing, and the surrounding context. "
            "This is the lowest-transformation option available for people."
        ),
        "composition": (
            "Preserve the source framing and spatial context. Reframe only enough to improve poster "
            "proportion. Keep the subject's relationship to their environment legible."
        ),
        "lighting": (
            "Use available or practical light as captured. Allow realistic imperfection such as mixed "
            "color temperature. Do not relight into studio conditions."
        ),
        "color_logic": (
            "Honest source color with restrained editorial grading. Preserve environmental color cast "
            "and skin-under-light relationships."
        ),
        "material_language": (
            "Keep real-world texture: skin pores, hair irregularity, fabric wear, and authentic "
            "imperfection. Documentary credibility outranks polish."
        ),
        "typography": (
            "Minimal. Small sans or serif caption, or none. Never place text over the subject's face."
        ),
        "realism": "very-high",
        "transformation": "low",
        "routing": {
            "subject": SUBJECT,
            "lighting": LIGHTING + ["harsh", "ambient", "low-light"],
            "mood": MOOD + ["observational", "urgent", "spontaneous"],
            "geometry": GEOMETRY + ["environmental", "imperfect-framing"],
            "materials": MATERIALS,
            "palette": PALETTE + ["mixed-temperature"],
            "realism": REALISM,
            "transform": ["low"],
        },
        "negative_prompt": (
            "No changed facial features, no beautification, no skin smoothing, no studio relighting, "
            "no styled or staged look, no costume change, no age shift, no gender shift, no extra or missing "
            "fingers, no duplicate or composite faces, no text across the face, no HDR, no fake bokeh balls, "
            "no generic stock-photo aesthetic."
        ),
        "variation_knobs": [
            "crop conservative/as-is",
            "grading neutral/editorial",
            "grain fine/none",
            "type sans/serif/none",
            "caption none/tiny",
        ],
        "prompt_block": (
            "Transform the single source photograph using the **Photojournalistic** visual system. "
            "Maximum fidelity to the source moment.\n\n"
            "Mechanism: Preserve the face exactly as captured, including natural asymmetry, expression, skin "
            "texture, clothing, and surrounding context. This is the lowest-transformation option for people.\n\n"
            "Composition: Preserve source framing and spatial context. Reframe only enough to improve poster "
            "proportion. Keep the subject's relationship to their environment legible.\n\n"
            "Lighting: Available or practical light as captured. Allow realistic imperfection such as mixed color "
            "temperature. Do not relight into studio conditions.\n\n"
            "Color: Honest source color with restrained editorial grading. Preserve environmental color cast.\n\n"
            "Material: Real-world texture - skin pores, hair irregularity, fabric wear, authentic imperfection. "
            "Documentary credibility outranks polish.\n\n"
            "Typography: Minimal. Small sans or serif caption, or none. Never over the face."
        ),
    },
]


def main() -> int:
    data = json.loads(STYLES.read_text(encoding="utf-8"))
    existing = {s["id"] for s in data["styles"]}

    added = []
    for style in PORTRAIT_STYLES:
        if style["id"] in existing:
            print(f"skip (exists): {style['id']}")
            continue
        # keep meta style last, append portrait styles among the direct block
        idx = next(
            (i for i, s in enumerate(data["styles"]) if s.get("role") == "meta"),
            len(data["styles"]),
        )
        data["styles"].insert(idx, style)
        existing.add(style["id"])
        added.append(style["id"])

    roles = Counter(s.get("role") for s in data["styles"])
    data["direct_style_count"] = roles.get("direct", 0)
    data["meta_style_count"] = roles.get("meta", 0)
    data["version"] = "1.1.0"

    STYLES.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"added: {added}")
    print(f"direct={data['direct_style_count']} meta={data['meta_style_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
