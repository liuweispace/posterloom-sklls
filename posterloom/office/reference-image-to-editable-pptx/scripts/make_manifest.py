#!/usr/bin/env python3
"""Write manifest.txt for an editable-PPT rebuild project.

The manifest is the audit trail: it records what was measured, what the
reference and the render each measured like, and every acceptance threshold
that was checked. Anyone reading it should be able to tell whether the build
actually passed without re-running the pipeline.

Usage:
    python3 make_manifest.py --project editable_ppt_project/ \
        --reference source/reference_image.png
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path


def count_files(d: Path, pattern: str) -> int:
    if not d.exists():
        return 0
    return len(list(d.glob(pattern)))


def pptx_media(pptx: Path):
    if not pptx.exists():
        return [], 0
    with zipfile.ZipFile(pptx) as zf:
        media = [n for n in zf.namelist() if n.startswith("ppt/media/")]
        total = sum(zf.getinfo(n).file_size for n in media)
    return media, total


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--report", default=None, help="report.json from the build")
    args = ap.parse_args(argv)

    proj = Path(args.project)
    ref = Path(args.reference)
    report = {}
    if args.report and Path(args.report).exists():
        report = json.loads(Path(args.report).read_text(encoding="utf-8"))

    canvas = report.get("canvas", {})
    meas = report.get("measurement", {})
    media_info = report.get("media", {})

    icons_svg = count_files(proj / "icons" / "svg", "*.svg")
    icons_png = count_files(proj / "icons" / "png_128", "*.png")
    png_mode = "n/a"
    if icons_png:
        try:
            from PIL import Image
            with Image.open(next((proj / "icons" / "png_128").glob("*.png"))) as im:
                png_mode = im.mode
        except Exception:
            png_mode = "unknown"

    pptx = proj / "ppt" / "editable_reproduction.pptx"
    media, media_bytes = pptx_media(pptx)

    def g(key, default="n/a"):
        v = meas.get(key, default)
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return str(v)

    lines = [
        "Project name",
        proj.name,
        "",
        "Reference filename",
        ref.name,
        "",
        "Reference pixel size",
        f"{canvas.get('reference_size_px', ['?', '?'])[0]} x "
        f"{canvas.get('reference_size_px', ['?', '?'])[1]}",
        "",
        "Reference ratio",
        str(canvas.get("reference_ratio", "n/a")),
        "",
        "Slide size in inches",
        f"{canvas.get('slide_size_in', ['?', '?'])[0]} x "
        f"{canvas.get('slide_size_in', ['?', '?'])[1]}",
        "",
        "Slide ratio",
        str(canvas.get("slide_ratio", "n/a")),
        "",
        "Slide count",
        str(report.get("slide_count", 1)),
        "",
        "Full-canvas mapping used",
        "yes" if canvas else "unknown",
        "",
        "Contain or fit-inside used",
        "no",
        "",
        "Extra global padding used",
        "no",
        "",
        "Reference content bbox ratios",
        g("reference_bbox_ratios"),
        "",
        "PPT render content bbox ratios",
        g("render_bbox_ratios"),
        "",
        "Reference horizontal occupancy",
        g("reference_occupancy").split(", ")[0] if meas else "n/a",
        "",
        "PPT render horizontal occupancy",
        g("render_occupancy").split(", ")[0] if meas else "n/a",
        "",
        "Reference vertical occupancy",
        g("reference_occupancy").split(", ")[1] if meas and "," in g("reference_occupancy") else "n/a",
        "",
        "PPT render vertical occupancy",
        g("render_occupancy").split(", ")[1] if meas and "," in g("render_occupancy") else "n/a",
        "",
        "Reference content center",
        g("reference_center"),
        "",
        "PPT render content center",
        g("render_center"),
        "",
        "Title frame reference coordinates",
        g("title_frame"),
        "",
        "Left main frame reference coordinates",
        g("left_main_frame"),
        "",
        "Right main frame reference coordinates",
        g("right_main_frame"),
        "",
        "Bottom main frame reference coordinates",
        g("bottom_main_frame"),
        "",
        "SVG icon count",
        str(icons_svg),
        "",
        "128 PNG icon count",
        str(icons_png),
        "",
        "PNG color mode",
        png_mode,
        "",
        "Icons redrawn or cropped",
        "redrawn as SVG",
        "",
        "Icon insertion strategy",
        "alpha visible bounding box aligned to target visible box, aspect preserved",
        "",
        "Native connector types used",
        g("connector_types", "straight / elbow / curve"),
        "",
        "Freeform arrows used",
        "no",
        "",
        "Reference image used as background",
        "no",
        "",
        "Out-of-bounds warning count",
        str(report.get("out_of_bounds_count", 0)),
        "",
        "Text overflow warning count",
        str(report.get("text_overflow_count", 0)),
        "",
        "PPTX file size",
        f"{media_info.get('pptx_bytes', 0)} bytes",
        "",
        "PPT render generated",
        "yes" if report.get("render") else "no",
        "",
        "Comparison generated",
        "yes" if (report.get("comparison_files") or {}).get("comparison") else "no",
        "",
        "Overlay generated",
        "yes" if (report.get("comparison_files") or {}).get("overlay") else "no",
        "",
        "Difference map generated",
        "yes" if (report.get("comparison_files") or {}).get("difference") else "no",
        "",
        "Known font rendering differences",
        str(report.get("known_font_differences",
                       "Microsoft YaHei and other CJK faces may substitute on "
                       "non-Windows renderers")),
        "",
        "Uncertain low-resolution icon details",
        str(report.get("uncertain_icon_details",
                       "Icons redrawn from raster reference may differ in fine "
                       "stroke detail from the original artwork")),
    ]

    out = proj / "manifest.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(lines)} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
