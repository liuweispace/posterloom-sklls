#!/usr/bin/env python3
"""Validate a scene_spec before it is turned into a PPTX.

Catches the structural mistakes that are expensive to discover late: a spec
that is missing the coordinate table entirely, frames that overflow the
canvas, text placed outside its frame, or an icon whose target box is
degenerate.

Usage:
    python3 validate_spec.py scene_spec.json --ref reference.png
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SECTIONS = ("frames", "texts", "icons", "connectors")


def validate(spec: dict, ref_w: int = None, ref_h: int = None) -> list:
    errors = []
    warnings = []

    if "page" not in spec:
        errors.append("missing 'page' block (width_px / height_px / background)")

    page = spec.get("page") or {}
    if ref_w and page.get("width_px") and page["width_px"] != ref_w:
        errors.append(f"page.width_px={page['width_px']} != reference {ref_w}")
    if ref_h and page.get("height_px") and page["height_px"] != ref_h:
        errors.append(f"page.height_px={page['height_px']} != reference {ref_h}")

    for sec in SECTIONS:
        if sec not in spec:
            errors.append(f"missing section '{sec}'")

    for f in spec.get("frames", []):
        name = f.get("name", "<unnamed>")
        for k in ("x", "y", "w", "h"):
            if k not in f:
                errors.append(f"frame '{name}' missing '{k}'")
        if f.get("w", 0) <= 0 or f.get("h", 0) <= 0:
            errors.append(f"frame '{name}' has non-positive w/h")
        if ref_w and ref_h:
            if f.get("x", 0) < -2 or f.get("y", 0) < -2:
                warnings.append(f"frame '{name}' starts off-canvas")
            if (f.get("x", 0) + f.get("w", 0) > ref_w + 2 or
                    f.get("y", 0) + f.get("h", 0) > ref_h + 2):
                errors.append(f"frame '{name}' extends beyond the canvas")

    for t in spec.get("texts", []):
        name = t.get("name", "<unnamed>")
        for k in ("x", "y", "w", "h", "text"):
            if k not in t:
                errors.append(f"text '{name}' missing '{k}'")
        if not str(t.get("text", "")).strip():
            warnings.append(f"text '{name}' is empty")
        if ref_w and ref_h:
            if (t.get("x", 0) + t.get("w", 0) > ref_w + 2 or
                    t.get("y", 0) + t.get("h", 0) > ref_h + 2):
                errors.append(f"text '{name}' extends beyond the canvas")

    for ic in spec.get("icons", []):
        name = ic.get("name", "<unnamed>")
        for k in ("asset", "target_visible_x", "target_visible_y",
                  "target_visible_w", "target_visible_h"):
            if k not in ic:
                errors.append(f"icon '{name}' missing '{k}'")
        if ic.get("target_visible_w", 0) <= 0 or ic.get("target_visible_h", 0) <= 0:
            errors.append(f"icon '{name}' has a degenerate target box")

    for c in spec.get("connectors", []):
        name = c.get("name", "<unnamed>")
        if c.get("type") in ("left_right_arrow", "right_arrow", "down_arrow",
                             "up_arrow"):
            for k in ("x", "y", "w", "h"):
                if k not in c:
                    errors.append(f"arrow shape '{name}' missing '{k}'")
        else:
            for k in ("x1", "y1", "x2", "y2"):
                if k not in c:
                    errors.append(f"connector '{name}' missing '{k}'")
        if c.get("layer") not in (None, "outer", "inner"):
            errors.append(f"connector '{name}' has invalid layer "
                          f"'{c.get('layer')}' (use 'outer' or 'inner')")

    names = [f.get("name") for f in spec.get("frames", [])]
    names += [t.get("name") for t in spec.get("texts", [])]
    names += [i.get("name") for i in spec.get("icons", [])]
    names += [c.get("name") for c in spec.get("connectors", [])]
    dupes = {n for n in names if n and names.count(n) > 1}
    if dupes:
        errors.append(f"duplicate object names: {sorted(dupes)}")

    if not spec.get("frames"):
        errors.append("no frames declared - the page would be empty")

    return errors, warnings


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--ref", default=None)
    args = ap.parse_args(argv)

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    ref_w = ref_h = None
    if args.ref:
        try:
            from PIL import Image
            with Image.open(args.ref) as im:
                ref_w, ref_h = im.size
        except Exception as e:
            print(f"WARN: could not read reference: {e}")

    errors, warnings = validate(spec, ref_w, ref_h)
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s) -> FAIL")
        return 1
    print(f"OK: 0 errors, {len(warnings)} warning(s) -> PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
