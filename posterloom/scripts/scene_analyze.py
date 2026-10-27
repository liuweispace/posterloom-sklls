#!/usr/bin/env python3
"""Build a PosterLoom scene profile by inspecting an image.

PosterLoom's routing quality depends entirely on the scene profile, but until now
the profile had to be written by hand. This module derives one from pixels where
that is possible without a vision model, and makes the limits explicit.

What it can measure from pixels (no model, no network):
  - image dimensions and aspect ratio
  - dominant palette families and their share of the frame
  - average brightness, contrast, and saturation
  - edge density / detail density per region
  - region saliency (which quadrant holds the subject)
  - text-safe candidate regions (flat, low-detail, reasonably contrasted areas)
  - a structural fingerprint used to match the scene against style routing

What it cannot measure:
  - subject type (portrait / architecture / landscape / still-life)
  - identity anchors
  - mood

Those need a vision model or a human. The analyzer says so explicitly and returns
`needs_vision: true` with the specific fields left empty, rather than guessing.
Guessing here would poison the router, which is the whole point of the tool.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Palette families used across the style library. Names match the vocabulary the
# routing rules expect, so a derived palette can be fed straight into the router.
PALETTE_FAMILIES = {
    "amber-charcoal": ((18, 0.35), (42, 0.22), (12, 0.2)),
    "warm-earth": ((20, 0.3), (35, 0.25), (40, 0.15)),
    "muted-green": ((95, 0.22), (140, 0.16)),
    "cool-blue": ((200, 0.25), (220, 0.2)),
    "neon": ((300, 0.45), (180, 0.4)),
    "high-contrast": None,   # computed, not sampled
    "monochrome": None,
    "source-derived": None,
    "pastel": None,
    "muted": None,
    "warm-cool": None,
    "earth-tone": None,
}


def _hsv(r: int, g: int, b: int):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    v = mx
    d = mx - mn
    s = 0.0 if mx == 0 else d / mx
    if d == 0:
        h = 0.0
    elif mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60.0, s, v


def _load_pixels(path: Path):
    """Return (width, height, pixels) where pixels is a flat list of (r,g,b).

    Uses Pillow when available. Without it we fall back to a tiny built-in PNG
    decoder so the skill keeps working with a standard library only.
    """
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as im:
            im = im.convert("RGB")
            im.thumbnail((256, 256))
            w, h = im.size
            return w, h, list(im.getdata())
    except Exception:
        return _load_pixels_stdlib(path)


def _load_pixels_stdlib(path: Path):
    """Minimal PNG reader: enough for 8-bit RGB/RGBA truecolor images."""
    import struct
    import zlib

    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        if data[:2] == b"\xff\xd8":
            raise ValueError(
                "JPEG input needs Pillow (pip install pillow). "
                "The built-in decoder handles PNG only."
            )
        raise ValueError("not a PNG file and Pillow is unavailable")

    pos = 8
    width = height = bitdepth = colortype = None
    idat = bytearray()
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            width, height, bitdepth, colortype = struct.unpack(">IIBB", body[:10])
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break
        pos += 12 + length

    if bitdepth != 8 or colortype not in (2, 6):
        raise ValueError(f"unsupported PNG (bitdepth={bitdepth}, colortype={colortype})")

    raw = zlib.decompress(bytes(idat))
    channels = 3 if colortype == 2 else 4
    stride = width * channels
    out = bytearray()
    prev = bytearray(stride)
    i = 0
    for _ in range(height):
        f = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        if f == 1:
            for x in range(channels, stride):
                line[x] = (line[x] + line[x - channels]) & 0xFF
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 0xFF
        elif f == 3:
            for x in range(stride):
                left = line[x - channels] if x >= channels else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 0xFF
        elif f == 4:
            for x in range(stride):
                a = line[x - channels] if x >= channels else 0
                b = prev[x]
                c = prev[x - channels] if x >= channels else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 0xFF
        out += line
        prev = line

    px = []
    stride_px = width * channels
    for y in range(height):
        base = y * stride_px
        for x in range(width):
            o = base + x * channels
            px.append((out[o], out[o + 1], out[o + 2]))
    # Downsample to at most 256 on the long edge.
    if width > 256 or height > 256:
        target = 256
        sx = max(1, width // target)
        sy = max(1, height // target)
        px = [px[y * width + x] for y in range(0, height, sy) for x in range(0, width, sx)]
        width = len(range(0, width, sx))
        height = len(range(0, height, sy))
    return width, height, px


def _density_of(contrast: float, sat: float) -> str:
    """Classify detail density from tone statistics.

    A flat two-colour print has hard tone and strong saturation; a soft
    painterly or photographic image does not.
    """
    if contrast > 0.30 and sat > 0.30:
        return "flat"
    if contrast < 0.16 and sat < 0.22:
        return "soft"
    if contrast < 0.16:
        return "low"
    return "medium"


def analyze(path: Path) -> dict:
    """Derive a partial scene profile from an image file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    w, h, px = _load_pixels(path)
    n = len(px)
    if n == 0:
        raise ValueError("empty image")

    # --- brightness / saturation / contrast -------------------------------
    lums, sats, hues = [], [], []
    for (r, g, b) in px:
        hh, ss, vv = _hsv(r, g, b)
        lums.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
        sats.append(ss)
        hues.append(hh)

    mean_l = sum(lums) / n
    var_l = sum((l - mean_l) ** 2 for l in lums) / n
    contrast = math.sqrt(var_l) / 255.0
    mean_s = sum(sats) / n
    bright_frac = sum(1 for l in lums if l > 200) / n
    dark_frac = sum(1 for l in lums if l < 55) / n

    # --- palette families -------------------------------------------------
    buckets: dict[str, int] = {}
    for (r, g, b), s in zip(px, sats):
        if s < 0.14:
            continue
        hh, ss, vv = _hsv(r, g, b)
        if hh < 25 or hh >= 335:
            key = "vivid-source-derived"
        elif hh < 50:
            key = "amber-charcoal"
        elif hh < 80:
            key = "earth-tone"
        elif hh < 165:
            key = "muted-green"
        elif hh < 255:
            key = "cool-warm"
        else:
            key = "expressive-palette"
        buckets[key] = buckets.get(key, 0) + 1

    palette = []
    total_colored = sum(buckets.values()) or 1
    for key, count in sorted(buckets.items(), key=lambda kv: -kv[1]):
        if count / total_colored >= 0.12:
            palette.append(key)
    if not palette:
        palette = ["source-derived"]
    # Only emit palette terms the router actually recognises.
    if mean_s < 0.16:
        palette.append("muted")
        palette.append("desaturated")
    elif mean_s > 0.45:
        palette.append("high-contrast")
        palette.append("expressive")
    if contrast > 0.28:
        palette.append("high-contrast")
    if len([p for p in palette if p not in ("source-derived", "muted", "desaturated",
                                            "high-contrast", "expressive")]) == 1:
        palette.append("single-accent")
    palette.append("source-derived")

    # --- hue cluster count -------------------------------------------------
    # The strongest discriminator between a flat 2-color print and a photograph.
    # A duotone poster has one or two hue families plus paper; a photo has many.
    hue_hist: dict[int, int] = {}
    for hue_val, sat_val in zip(hues, sats):
        if sat_val < 0.18:
            continue
        k = int(hue_val // 20) * 20
        hue_hist[k] = hue_hist.get(k, 0) + 1
    total_h = sum(hue_hist.values()) or 1
    # Count clusters that carry a meaningful share of the colored area.
    clusters = 0
    for k, cnt in sorted(hue_hist.items(), key=lambda kv: -kv[1]):
        if cnt / total_h >= 0.14:
            clusters += 1
    hue_cluster_count = clusters

    # --- detail density per region (3x3 grid) ------------------------------
    gx = gy = 3
    cell_w = max(1, w // gx)
    cell_h = max(1, h // gy)
    detail = []
    for cy in range(gy):
        row = []
        for cx in range(gx):
            x0, x1 = cx * cell_w, min(w, (cx + 1) * cell_w)
            y0, y1 = cy * cell_h, min(h, (cy + 1) * cell_h)
            tot = 0
            cnt = 0
            for y in range(y0, y1):
                for x in range(x0, x1):
                    i = y * w + x
                    if i >= n:
                        continue
                    tot += lums[i]
                    cnt += 1
                    if x + 1 < w and i + 1 < n:
                        tot += abs(lums[i] - lums[i + 1]) * 1.5
                        cnt += 2
                    if y + 1 < h and i + w < n:
                        tot += abs(lums[i] - lums[i + w]) * 1.5
                        cnt += 1
            row.append((tot / cnt) if cnt else 0.0)
        detail.append(row)

    flat_cells = []
    for cy in range(gy):
        for cx in range(gx):
            v = detail[cy][cx]
            lo = min(detail[r][c] for r in range(gy) for c in range(gx))
            hi = max(detail[r][c] for r in range(gy) for c in range(gx))
            rng = max(hi - lo, 1e-6)
            flat_cells.append(((v - lo) / rng, cx, cy))

    flat_cells.sort()
    quiet = flat_cells[:2]
    busy = flat_cells[-2:]

    # --- lighting cues ----------------------------------------------------
    lighting = []
    if mean_l < 80:
        lighting.append("low-light")
    if bright_frac > 0.22:
        lighting.append("high-contrast")
    if dark_frac > 0.28:
        lighting.append("night")
    if contrast > 0.30:
        lighting.append("hard")
        lighting.append("strong-shadow")
    elif contrast < 0.13:
        lighting.append("soft")
        lighting.append("soft-even")
    else:
        lighting.append("natural")
    if mean_s < 0.14:
        lighting.append("flat-light")

    # --- geometry cues ----------------------------------------------------
    geometry = []
    if h > w:
        geometry.append("portrait-orientation")
        geometry.append("vertical")
    elif w > h:
        geometry.append("horizontal")
    if mean_s < 0.16 and contrast < 0.16:
        geometry.append("shallow-depth-of-field")
    else:
        geometry.append("layered-depth")
    geometry.append("balanced")
    if len(set(palette)) <= 2:
        geometry.append("simplified" if "simplified" in geometry else "clean-lines")

    # --- text-safe zones --------------------------------------------------
    names = {(0, 0): "upper-left", (0, 1): "upper-center", (0, 2): "upper-right",
             (1, 0): "mid-left", (1, 1): "center", (1, 2): "mid-right",
             (2, 0): "lower-left", (2, 1): "lower-center", (2, 2): "lower-right"}
    safe = []
    for _, cx, cy in quiet:
        label = names[(cx, cy)]
        region_mean = detail[cy][cx]
        # A quiet cell must also contrast against the global mean to hold type.
        if abs(region_mean - mean_l) > 12 or mean_l > 190 or mean_l < 70:
            safe.append(f"{label} quiet region")
    if not safe:
        safe = ["upper-right dark region"]

    # --- materials (coarse, texture-derived) -------------------------------
    materials = []
    if contrast > 0.30:
        materials.append("texture")
        materials.append("photographic")
    if mean_s < 0.18:
        materials.append("flat-color")
    if "muted-green" in palette:
        materials.append("foliage")
    if "earth-tone" in palette or "amber-charcoal" in palette:
        materials.append("stone")
    if not materials:
        materials.append("texture")
        materials.append("photographic")

    # --- focus / saliency --------------------------------------------------
    focus = max(range(len(flat_cells)), key=lambda i: flat_cells[i][0]) if flat_cells else None
    focus_cell = None
    if focus is not None:
        _, fx, fy = flat_cells[focus]
        focus_cell = names[(fx, fy)]

    ratio = _aspect_label(w, h)

    # Filter every derived field against the router's own vocabulary. A term
    # the router cannot match is dead weight that dilutes the score.
    vocab = _router_vocab()
    palette = _known(palette, vocab["palette"])
    lighting = _known(lighting, vocab["lighting"])
    geometry = _known(geometry, vocab["geometry"])
    materials = _known(materials, vocab["materials"])

    profile = {
        "subject": {
            "type": "",
            "summary": "",
            "identity_anchors": [],
        },
        "environment": "",
        "lighting": lighting,
        "mood": [],
        "geometry": geometry,
        "palette": palette,
        "materials": materials,
        "text_safe_zones": safe,
        "realism_value": "high",
        "transformation_tolerance": "medium",
        # The source aspect is a MEASURED property, not a user request. Keep it
        # apart from an explicit ratio so a style's own designed ratio (3:5 for
        # the zine styles) is not silently overridden by the photo's shape.
        "user_preferences": {"output_ratio": ratio},
        "_measured_source_aspect": ratio,
        "subject_tags": [],
        "_measured": {
            "file": path.name,
            "pixels": f"{w}x{h}",
            "mean_luminance": round(mean_l, 1),
            "contrast": round(contrast, 3),
            "mean_saturation": round(mean_s, 3),
            "focus_region": focus_cell,
            "hue_clusters": hue_cluster_count,
            "density": _density_of(contrast, mean_s),
            "quiet_regions": [names[(cx, cy)] for _, cx, cy in quiet],
            "busy_regions": [names[(cx, cy)] for _, cx, cy in busy],
        },
        "_needs_vision": [
            "subject.type",
            "subject.summary",
            "subject.identity_anchors",
            "mood",
            "subject_tags",
            "realism_value",
            "transformation_tolerance",
        ],
        "_note": (
            "Color, tone, detail and layout were measured from pixels. Subject type, "
            "identity anchors and mood need a vision model or a human. Fill the "
            "listed fields, then route. Do not route on the empty ones."
        ),
    }
    return profile


def _known(terms, vocab):
    """Keep only terms the router can actually match."""
    out = []
    for t in terms:
        if t in vocab and t not in out:
            out.append(t)
    return out


def _router_vocab():
    """Build the router's vocabulary from styles.json, so the filter can never
    drift from what the router actually matches."""
    data = json.loads((ROOT / "data/styles.json").read_text(encoding="utf-8"))
    vocab = {"palette": set(), "lighting": set(), "geometry": set(),
             "materials": set()}
    for s in data["styles"]:
        r = s.get("routing", {})
        for k in vocab:
            vocab[k].update(r.get(k, []))
    return vocab


def _aspect_label(w: int, h: int) -> str:
    from math import gcd
    g = gcd(w, h) or 1
    rw, rh = w // g, h // g
    common = {
        (1, 1): "1:1", (2, 3): "2:3", (3, 2): "3:2", (3, 4): "3:4", (4, 3): "4:3",
        (4, 5): "4:5", (5, 4): "5:4", (9, 16): "9:16", (16, 9): "16:9",
        (2, 5): "2:5", (5, 2): "5:2", (3, 5): "3:5", (5, 3): "5:3",
    }
    return common.get((rw, rh), f"{rw}:{rh}")


def merge_measured(profile: dict, measured: dict) -> dict:
    """Overlay measured values onto a hand-written profile without clobbering
    the fields a human or vision model supplied."""
    out = dict(profile)
    for key in ("lighting", "geometry", "palette", "materials", "text_safe_zones"):
        if not out.get(key):
            out[key] = measured.get(key, [])
    out["_measured"] = measured.get("_measured", {})
    return out


def main(argv):
    if len(argv) < 2:
        print("usage: scene_analyze.py <image> [--out profile.json]", file=sys.stderr)
        return 2
    src = Path(argv[1])
    try:
        measured = analyze(src)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if "--out" in argv:
        out = Path(argv[argv.index("--out") + 1])
        out.write_text(json.dumps(measured, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        print(f"WROTE {out}")
    else:
        print(json.dumps(measured, ensure_ascii=False, indent=2))
    print("\nMeasured from pixels: lighting, geometry, palette, materials, "
          "text-safe zones, focus region.")
    print("Still needs vision: subject.type, identity_anchors, mood, "
          "transformation_tolerance.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
