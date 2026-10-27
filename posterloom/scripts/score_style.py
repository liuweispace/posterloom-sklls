#!/usr/bin/env python3
"""Measure how faithfully a generated image follows a flat-print style.

Eyeballing "does this look like a risograph print" does not scale, and it does
not survive contact with 35 styles. This computes the properties that actually
distinguish a flat two-ink print from a photo:

  flat_ratio    fraction of pixels sitting in a perfectly flat neighbourhood.
                A print has large areas of one solid ink with hard edges; a
                photo is smooth everywhere, so it has almost no flat area.
  ink_ratio     fraction of pixels that are clearly coloured rather than paper.
  hue_spread    number of distinct colour families. A two-ink print has 1-3;
                a photo has many.
  edge_hardness mean edge strength. Prints have hard boundaries; photos do not.
  photo_score   0 = unmistakably flat print, 1 = unmistakably a photograph.

`photo_score` is the headline number. It is the weighted blend above, and it
is what the render pipeline uses to decide whether a generation is acceptable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


def _load(path):
    if Image is None:
        raise RuntimeError("Pillow is required for style scoring (pip install pillow)")
    img = Image.open(path).convert("RGB")
    # Downscale so the analysis is about the visual impression, not the pixels.
    img = img.resize((256, int(256 * img.height / img.width)) if img.width >= img.height
                     else (int(256 * img.width / img.height), 256))
    return img


def score(path) -> dict:
    """Score one image. Returns a dict with the raw metrics and photo_score."""
    img = _load(path)
    w, h = img.size
    px = list(img.getdata())
    n = len(px)

    # --- flat area: neighbourhood is (nearly) one colour -------------------
    flat = 0
    edge_sum = 0.0
    edge_n = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            i = y * w + x
            r, g, b = px[i]
            d = 0
            for j in (i - 1, i + 1, i - w, i + w):
                r2, g2, b2 = px[j]
                d = max(d, abs(r - r2), abs(g - g2), abs(b - b2))
            if d <= 12:
                flat += 1
            edge_sum += d
            edge_n += 1
    inner = max(1, edge_n)
    flat_ratio = flat / inner
    edge_mean = edge_sum / inner

    # --- palette: quantize and count distinct families ----------------------
    def bucket(v):
        return v // 48

    families = set()
    ink_px = 0
    paper_px = 0
    sat_sum = 0
    for r, g, b in px:
        mx, mn = max(r, g, b), min(r, g, b)
        sat = 0 if mx == 0 else (mx - mn) / mx
        sat_sum += sat
        if mx > 225 and mn > 205:
            paper_px += 1
        elif sat > 0.18 or mx < 150:
            ink_px += 1
        families.add((bucket(r), bucket(g), bucket(b)))
    ink_ratio = ink_px / n
    paper_ratio = paper_px / n
    hue_spread = len(families)
    mean_sat = sat_sum / n

    # --- photo score --------------------------------------------------------
    # A photo: low flat area, many colour families, soft edges.
    # A print: high flat area, few families, hard edges.
    s_flat = min(1.0, max(0.0, (0.55 - flat_ratio) / 0.45))       # less flat -> more photo
    s_hue = min(1.0, max(0.0, (hue_spread - 14) / 90.0))          # many families -> more photo
    s_edge = min(1.0, max(0.0, (70.0 - edge_mean) / 60.0))        # soft edges -> more photo
    s_sat = min(1.0, max(0.0, (mean_sat - 0.22) / 0.35))          # colourful -> more photo
    photo_score = 0.45 * s_flat + 0.25 * s_hue + 0.15 * s_edge + 0.15 * s_sat

    return {
        "path": str(path),
        "flat_ratio": round(flat_ratio, 4),
        "ink_ratio": round(ink_ratio, 4),
        "paper_ratio": round(paper_ratio, 4),
        "hue_spread": hue_spread,
        "edge_mean": round(edge_mean, 2),
        "mean_sat": round(mean_sat, 4),
        "photo_score": round(photo_score, 4),
        "verdict": "photograph" if photo_score > 0.55 else
                   ("hybrid" if photo_score > 0.32 else "flat print"),
    }


def score_many(paths) -> list:
    out = []
    for p in paths:
        try:
            out.append(score(p))
        except Exception as e:  # noqa: BLE001
            out.append({"path": str(p), "error": str(e)})
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    as_json = "--json" in args
    paths = [a for a in args if a != "--json"]
    results = score_many(paths)
    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"{'file':52s} {'score':>6s} {'flat':>6s} {'ink':>6s} {'hue':>5s} {'edge':>6s}  verdict")
        for r in results:
            if "error" in r:
                print(f"{Path(r['path']).name:52s} ERROR {r['error'][:40]}")
                continue
            print(f"{Path(r['path']).name:52s} {r['photo_score']:6.3f} "
                  f"{r['flat_ratio']:6.3f} {r['ink_ratio']:6.3f} "
                  f"{r['hue_spread']:5d} {r['edge_mean']:6.2f}  {r['verdict']}")
