#!/usr/bin/env python3
"""Match a reference poster to the closest PosterLoom style.

The idea borrowed from `poster-style-transfer`: treat a reference poster as a
reusable *design grammar*, not as content to copy. Here the grammar is matched
against PosterLoom's own style library by comparing measurable properties of the
reference image against each style's `visual_signature`.

This does not copy the reference's subject, people, or wording. It only decides
which of the 34 built-in styles speaks the same visual language, so the user gets
a style they can trust without hand-writing a style spec.

Measured from the reference image:
  - contrast, saturation, luminance
  - palette families
  - detail density (flat / soft / medium / low)

Matched against each style's visual_signature:
  - contrast range and saturation range (overlap scoring)
  - palette candidates (overlap scoring)
  - density class (exact / adjacent)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from scene_analyze import analyze, _density_of  # noqa: E402

# Pixel-measured palette family -> router palette words.
HUE2PAL = {
    "vivid-source-derived": ["high-contrast", "expressive", "vivid-source-derived"],
    "amber-charcoal": ["amber-charcoal", "earth-tone", "warm-neutral"],
    "earth-tone": ["earth-tone", "warm-neutral", "amber-charcoal", "tea-brown"],
    "muted-green": ["muted", "muted-green", "earth-tone"],
    "cool-warm": ["cool-warm", "warm-cool", "mixed-temperature", "single-hue-ramp"],
    "expressive-palette": ["expressive", "spot-color", "high-contrast"],
}

DENSITY_ORDER = ["flat", "soft", "medium", "low"]


def _density_of(measured: dict) -> str:
    """Classify the reference image's detail density."""
    return measured.get("density") or "medium"


def _overlap(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def match(reference: Path, top: int = 5) -> dict:
    profile = analyze(reference)
    m = profile["_measured"]
    contrast = m["contrast"]
    sat = m["mean_saturation"]

    density = _density_of(m)
    pal_words: set = set()
    for fam in profile["palette"]:
        pal_words.update(HUE2PAL.get(fam, []))
    pal_words.add("source-derived")

    data = json.loads((ROOT / "data/styles.json").read_text(encoding="utf-8"))
    # A family with many members is a catch-all; a family with one or two is a
    # specific answer. When four generic styles tie, none of them is a confident
    # match, so a narrow family should win the tie.
    fam_size: dict[str, int] = {}
    for st in data["styles"]:
        if st.get("role") == "direct":
            fam_size[st.get("family", "")] = fam_size.get(st.get("family", ""), 0) + 1

    results = []
    for style in data["styles"]:
        if style.get("role") != "direct":
            continue
        sig = style.get("visual_signature") or {}
        if not sig:
            continue

        c_lo, c_hi = sig.get("contrast_range", [0.0, 1.0])
        s_lo, s_hi = sig.get("saturation_range", [0.0, 1.0])

        # Range overlap: 1.0 when the measured value sits inside the style's band.
        c_score = _band(contrast, c_lo, c_hi)
        s_score = _band(sat, s_lo, s_hi)
        # Palette scoring: reward a match on the reference's DOMINANT color family,
        # not on a Jaccard overlap with the style's whole candidate list. A style
        # that lists ten possible palettes would otherwise outrank a style that is
        # exactly right but lists two.
        dom_family = profile["palette"][0] if profile["palette"] else ""
        dom_words = set(HUE2PAL.get(dom_family, []))
        cand = set(sig.get("palette_candidates", []))
        if dom_words & cand:
            p_score = 1.0
        elif pal_words & cand:
            p_score = 0.6 * _overlap(pal_words, cand)
        else:
            p_score = 0.15

        want = sig.get("density", "medium")
        d_score = _density_match(density, want)

        # Hue-cluster count: the decisive signal. A flat 2-color print has 1-3
        # hue families; a photograph has many. This is what actually separates
        # the duotone / risograph / screenprint families from the photographic
        # ones, which contrast and saturation alone cannot.
        want_clusters = sig.get("hue_clusters", [1, 12])
        cl_score = _band(m.get("hue_clusters", 6), want_clusters[0], want_clusters[1])

        # Specificity: a style whose signature is narrow (one family, tight bands)
        # is a stronger explanation of a distinctive reference than a broad one.
        # Without this, generic styles tie with the exact match.
        width = (want_clusters[1] - want_clusters[0]) + (c_hi - c_lo) + (s_hi - s_lo)
        specificity = max(0.0, min(1.0, 1.0 - (width / 6.0)))

        # Narrow-family bonus: a family with 1-2 members names a specific look;
        # a family with 5+ is a bucket. Discourage the bucket from winning.
        fam_n = fam_size.get(style.get("family", ""), 1)
        fam_conf = 1.0 / max(1.0, fam_n / 2.0)

        score = (0.24 * c_score + 0.16 * s_score + 0.18 * p_score
                 + 0.09 * d_score + 0.15 * cl_score + 0.08 * specificity
                 + 0.10 * fam_conf)
        results.append({
            "style": style["id"],
            "name": style["name"],
            "family": style.get("family", ""),
            "score": round(score, 4),
            "components": {
                "contrast": round(c_score, 3),
                "saturation": round(s_score, 3),
                "palette": round(p_score, 3),
                "density": round(d_score, 3),
                "hue_clusters": round(cl_score, 3),
            },
        })

    results.sort(key=lambda r: (-r["score"], r["style"]))
    return {
        "reference": str(reference),
        "measured": {
            "contrast": round(contrast, 3),
            "saturation": round(sat, 3),
            "mean_luminance": m["mean_luminance"],
            "density": density,
            "palette_families": profile["palette"],
        },
        "matches": results[:top],
        "best": results[0] if results else None,
        "_note": (
            "Matched on measurable properties only - contrast, saturation, palette "
            "and detail density. Subject, people and wording are not copied. "
            "Use the winning style id with: posterloom.py prompt <profile> "
            "--style <style-id>"
        ),
    }


def _band(value: float, lo: float, hi: float) -> float:
    if lo <= value <= hi:
        return 1.0
    span = max(hi - lo, 1e-6)
    if value < lo:
        return max(0.0, 1.0 - (lo - value) / (span * 2))
    return max(0.0, 1.0 - (value - hi) / (span * 2))


def _density_match(measured: str, want: str) -> float:
    if want == "any" or measured == want:
        return 1.0
    try:
        a = DENSITY_ORDER.index(measured)
        b = DENSITY_ORDER.index(want)
    except ValueError:
        return 0.5
    return 1.0 / (1 + abs(a - b))


def main(argv):
    if len(argv) < 2:
        print("usage: match_reference.py <reference-poster> [--top N]", file=sys.stderr)
        return 2
    top = 5
    if "--top" in argv:
        top = int(argv[argv.index("--top") + 1])
    out = match(Path(argv[1]), top=top)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
