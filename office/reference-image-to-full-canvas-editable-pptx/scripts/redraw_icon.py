#!/usr/bin/env python3
"""Redraw an icon as SVG from measured geometry.

Icons are rebuilt, never cropped. Cropping is explicitly rejected by the
acceptance criteria because it leaves a raster rectangle on the slide, but
redrawing from a measured description produces a real vector shape with real
transparency.

The generator takes a small, explicit geometry description and emits a clean
SVG. Keeping the description in Python (rather than templating raw SVG
strings) means the shapes are computed: strokes are centred on the outline,
fills are derived from the same path, and the result is symmetric by
construction.

Every path is written into a 128x128 viewBox so the rendered PNG is exactly
128x128 with the artwork inside it.

Usage:
    python3 redraw_icon.py --kind trophy --out icons/svg/trophy_blue.svg \
        --color "#1B7FBF"
    python3 redraw_icon.py --kind flask --out icons/svg/flask_green.svg
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# A 128x128 canvas. Shapes are drawn inside a 104x104 safe area so the
# artwork never touches the edge and the 128px PNG has no clipped strokes.
C = 128
PAD = 12
S = C - 2 * PAD  # 104 usable span


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _shade(h: str, factor: float) -> str:
    r, g, b = _hex_to_rgb(h)
    def c(v):
        return max(0, min(255, int(v)))
    return "#{:02X}{:02X}{:02X}".format(c(r * factor), c(g * factor), c(b * factor))


def _lighten(h: str, amount: float = 0.55) -> str:
    """Mix a colour toward white.

    Interior detail (brain folds, gear hub, target rings) must be a
    DIFFERENT colour from the body, otherwise it renders as the same
    colour on the same colour and the detail is simply not there.
    """
    r, g, b = _hex_to_rgb(h)
    return "#{:02X}{:02X}{:02X}".format(
        int(r + (255 - r) * amount),
        int(g + (255 - g) * amount),
        int(b + (255 - b) * amount))


def _svg(body: str, stroke: str, sw: float = 6.0) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {C} {C}" width="{C}" height="{C}">
  <g fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">
{body}
  </g>
</svg>
'''


# ---------------------------------------------------------------------------
# Icon recipes. Each returns SVG body text.
# ---------------------------------------------------------------------------

def trophy(color: str, accent: str) -> str:
    cup_w, cup_h = 54, 46
    cx = C / 2
    top = PAD + 6
    bowl_bottom = top + cup_h
    stem_h = 18
    base_w = 44
    return _svg(f'''
    <path d="M {cx - cup_w / 2} {top} L {cx - cup_w / 2} {top + cup_h * 0.55}
             Q {cx - cup_w / 2} {bowl_bottom} {cx} {bowl_bottom}
             Q {cx + cup_w / 2} {bowl_bottom} {cx + cup_w / 2} {top + cup_h * 0.55}
             L {cx + cup_w / 2} {top} Z" fill="{color}"/>
    <path d="M {cx - cup_w / 2 - 2} {top + 6} Q {cx - cup_w / 2 - 18} {top + 10} {cx - cup_w / 2 - 16} {top + 26}
             Q {cx - cup_w / 2 - 14} {top + 38} {cx - cup_w / 2 + 2} {top + 36}"/>
    <path d="M {cx + cup_w / 2 + 2} {top + 6} Q {cx + cup_w / 2 + 18} {top + 10} {cx + cup_w / 2 + 16} {top + 26}
             Q {cx + cup_w / 2 + 14} {top + 38} {cx + cup_w / 2 - 2} {top + 36}"/>
    <path d="M {cx} {bowl_bottom} L {cx} {bowl_bottom + stem_h}" stroke="{color}" stroke-width="9"/>
    <path d="M {cx - base_w / 2} {bowl_bottom + stem_h + 8} L {cx + base_w / 2} {bowl_bottom + stem_h + 8}"
          stroke="{color}" stroke-width="9"/>
    <path d="M {cx - 12} {top + 16} L {cx + 12} {top + 16}" stroke="{accent}" stroke-width="5"/>
''', color, 5.0)


def flask(color: str, accent: str) -> str:
    cx = C / 2
    neck_w = 26
    neck_top = PAD + 4
    neck_bottom = PAD + 30
    body_w = 58
    body_bottom = C - PAD - 6
    return _svg(f'''
    <path d="M {cx - neck_w / 2} {neck_top} L {cx + neck_w / 2} {neck_top}
             L {cx + neck_w / 2} {neck_bottom}
             L {cx + body_w / 2} {body_bottom - 8}
             Q {cx + body_w / 2} {body_bottom} {cx + body_w / 2 - 8} {body_bottom}
             L {cx - body_w / 2 + 8} {body_bottom}
             Q {cx - body_w / 2} {body_bottom} {cx - body_w / 2} {body_bottom - 8}
             L {cx - neck_w / 2} {neck_bottom} Z" fill="{color}"/>
    <path d="M {cx - neck_w / 2 - 4} {neck_top - 4} L {cx + neck_w / 2 + 4} {neck_top - 4}"
          stroke="{color}" stroke-width="7"/>
    <path d="M {cx - 14} {body_bottom - 20} Q {cx} {body_bottom - 30} {cx + 14} {body_bottom - 20}"
          stroke="{accent}" stroke-width="5"/>
    <circle cx="{cx + 12}" cy="{body_bottom - 34}" r="5" fill="{accent}" stroke="none"/>
''', color, 5.0)


def brain(color: str, accent: str) -> str:
    """A brain silhouette with visible cortical folds.

    The fold lines are drawn AFTER the body fill and in the accent colour,
    otherwise the body fill paints over them and the icon renders as a
    featureless blob.
    """
    cx, cy = C / 2, C / 2
    r = 40
    return _svg(f'''
    <path d="M {cx - r} {cy + 6} Q {cx - r - 4} {cy - 22} {cx - 14} {cy - 24}
             Q {cx - 4} {cy - 40} {cx + 12} {cy - 30}
             Q {cx + 34} {cy - 34} {cx + 36} {cy - 10}
             Q {cx + 46} {cy + 2} {cx + 36} {cy + 16}
             Q {cx + 34} {cy + 36} {cx + 10} {cy + 30}
             Q {cx - 8} {cy + 40} {cx - 18} {cy + 26}
             Q {cx - 36} {cy + 30} {cx - r} {cy + 6} Z" fill="{color}"/>
    <path d="M {cx - 22} {cy - 10} Q {cx - 8} {cy - 18} {cx + 2} {cy - 8}
             Q {cx + 16} {cy - 16} {cx + 24} {cy - 2}" stroke="{accent}" stroke-width="4.5"/>
    <path d="M {cx - 16} {cy + 4} Q {cx - 2} {cy - 4} {cx + 8} {cy + 6}
             Q {cx + 18} {cy + 14} {cx + 10} {cy + 24}" stroke="{accent}" stroke-width="4.5"/>
    <path d="M {cx - 26} {cy + 14} Q {cx - 14} {cy + 10} {cx - 6} {cy + 20}" stroke="{accent}" stroke-width="4.5"/>
''', color, 5.0)


def gear(color: str, accent: str) -> str:
    cx, cy = C / 2, C / 2
    r_out, r_in = 42, 30
    teeth = 8
    pts = []
    for i in range(teeth * 2):
        a = i * 3.14159265 / teeth
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * _cos(a), cy + r * _sin(a)))
    d = " ".join(f"{'M' if i == 0 else 'L'} {x:.1f} {y:.1f}"
                 for i, (x, y) in enumerate(pts)) + " Z"
    return _svg(f'''
    <path d="{d}" fill="{color}"/>
    <circle cx="{cx}" cy="{cy}" r="14" fill="{accent}" stroke="{color}" stroke-width="3"/>
    <circle cx="{cx}" cy="{cy}" r="6" fill="{color}" stroke="none"/>
''', color, 4.0)


def document(color: str, accent: str) -> str:
    x, y = C / 2 - 30, PAD + 4
    w, h = 60, 92
    fold = 20
    return _svg(f'''
    <path d="M {x} {y} L {x + w - fold} {y} L {x + w} {y + fold} L {x + w} {y + h} L {x} {y + h} Z"
          fill="{color}"/>
    <path d="M {x + w - fold} {y} L {x + w - fold} {y + fold} L {x + w} {y + fold}"
          stroke="{accent}" stroke-width="4.5"/>
    <path d="M {x + 10} {y + 30} L {x + w - 12} {y + 30}" stroke="{accent}" stroke-width="4.5"/>
    <path d="M {x + 10} {y + 46} L {x + w - 12} {y + 46}" stroke="{accent}" stroke-width="4.5"/>
    <path d="M {x + 10} {y + 62} L {x + w - 22} {y + 62}" stroke="{accent}" stroke-width="4.5"/>
''', color, 5.0)


def chart(color: str, accent: str) -> str:
    x, y = PAD + 6, PAD + 8
    w, h = 88, 88
    bars = [0.32, 0.58, 0.44, 0.78, 0.62]
    bw = 12
    gap = 5
    total = len(bars) * bw + (len(bars) - 1) * gap
    sx = x + (w - total) / 2
    body = []
    for i, bh in enumerate(bars):
        bx = sx + i * (bw + gap)
        by = y + h - h * bh
        body.append(f'    <rect x="{bx:.1f}" y="{by:.1f}" width="{bw}" '
                    f'height="{h * bh:.1f}" rx="2" fill="{color}"/>')
    body.append(f'    <path d="M {x} {y + h + 4} L {x + w} {y + h + 4}" '
                f'stroke="{accent}" stroke-width="5"/>')
    return _svg("\n".join(body), color, 4.5)


def database(color: str, accent: str) -> str:
    cx = C / 2
    cy = PAD + 16
    rx, ry = 34, 11
    h = 66
    return _svg(f'''
    <path d="M {cx - rx} {cy} L {cx - rx} {cy + h}
             A {rx} {ry} 0 0 0 {cx + rx} {cy + h}
             L {cx + rx} {cy} Z" fill="{color}"/>
    <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{color}"/>
    <path d="M {cx - rx} {cy + h / 3} A {rx} {ry} 0 0 0 {cx + rx} {cy + h / 3}"
          stroke="{accent}" stroke-width="4"/>
    <path d="M {cx - rx} {cy + 2 * h / 3} A {rx} {ry} 0 0 0 {cx + rx} {cy + 2 * h / 3}"
          stroke="{accent}" stroke-width="4"/>
''', color, 5.0)


def shield(color: str, accent: str) -> str:
    cx = C / 2
    top = PAD + 6
    w = 58
    bottom = C - PAD - 6
    return _svg(f'''
    <path d="M {cx - w / 2} {top} L {cx + w / 2} {top}
             L {cx + w / 2} {top + 40}
             Q {cx + w / 2} {bottom - 20} {cx} {bottom}
             Q {cx - w / 2} {bottom - 20} {cx - w / 2} {top + 40} Z" fill="{color}"/>
    <path d="M {cx - 14} {top + 38} L {cx - 3} {top + 50} L {cx + 16} {top + 28}"
          stroke="{accent}" stroke-width="6"/>
''', color, 5.0)


def target(color: str, accent: str) -> str:
    cx, cy = C / 2, C / 2
    return _svg(f'''
    <circle cx="{cx}" cy="{cy}" r="42" fill="{color}"/>
    <circle cx="{cx}" cy="{cy}" r="30" fill="{accent}" stroke="none"/>
    <circle cx="{cx}" cy="{cy}" r="20" fill="{color}" stroke="none"/>
    <circle cx="{cx}" cy="{cy}" r="10" fill="{accent}" stroke="none"/>
    <circle cx="{cx}" cy="{cy}" r="4" fill="{color}" stroke="none"/>
''', color, 4.5)


def _cos(a):
    import math
    return math.cos(a)


def _sin(a):
    import math
    return math.sin(a)


RECIPES = {
    "trophy": trophy,
    "flask": flask,
    "brain": brain,
    "gear": gear,
    "document": document,
    "chart": chart,
    "database": database,
    "shield": shield,
    "target": target,
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True, choices=sorted(RECIPES))
    ap.add_argument("--out", required=True)
    ap.add_argument("--color", default="#1B7FBF")
    ap.add_argument("--accent", default=None)
    args = ap.parse_args(argv)

    if args.kind not in RECIPES:
        print(f"ERROR: unknown kind '{args.kind}'. "
              f"available: {', '.join(sorted(RECIPES))}", file=sys.stderr)
        return 1

    accent = args.accent or _lighten(args.color, 0.62)
    svg = RECIPES[args.kind](args.color, accent)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({len(svg)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
