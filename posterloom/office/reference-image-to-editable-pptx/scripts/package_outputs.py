#!/usr/bin/env python3
"""Build the icons preview contact sheet and package the deliverable ZIPs.

Produces:
    preview/icons_preview.png    contact sheet of every 128x128 icon
    editable_ppt_project.zip     full project tree
    icons_assets.zip             svg/ + png_128/ only

Usage:
    python3 package_outputs.py --project editable_ppt_project/ --out /mnt/data
"""
from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("ERROR: requires Pillow")


def build_icon_sheet(png_dir: Path, out_path: Path, cols: int = 8,
                     cell: int = 150) -> Path:
    """Contact sheet: one icon per cell on a checker so transparency shows."""
    files = sorted(png_dir.glob("*.png"))
    if not files:
        return None
    rows = (len(files) + cols - 1) // cols
    pad = 8
    label_h = 18
    sheet_w = cols * (cell + pad) + pad
    sheet_h = rows * (cell + label_h + pad) + pad

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 245, 247))
    draw = ImageDraw.Draw(sheet)

    for i, f in enumerate(files):
        r, c = divmod(i, cols)
        x = pad + c * (cell + pad)
        y = pad + r * (cell + label_h + pad)

        # checkerboard so alpha is visible
        sq = 10
        for cy in range(0, cell, sq):
            for cx in range(0, cell, sq):
                v = 225 if ((cx // sq + cy // sq) % 2 == 0) else 245
                draw.rectangle([x + cx, y + cy,
                                x + min(cx + sq, cell) - 1,
                                y + min(cy + sq, cell) - 1], fill=(v, v, v))

        with Image.open(f) as im:
            im = im.convert("RGBA")
            im = im.resize((cell, cell), Image.Resampling.LANCZOS)
            sheet.paste(im, (x, y), im)

        draw.rectangle([x, y, x + cell - 1, y + cell - 1], outline=(200, 200, 205))
        draw.text((x + 2, y + cell + 2), f.stem[:22], fill=(60, 60, 70))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return out_path


def zip_dir(src: Path, out_zip: Path, arc_root: str = None):
    if out_zip.exists():
        out_zip.unlink()
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(src.rglob("*")):
            if p.is_file():
                rel = p.relative_to(src)
                arc = f"{arc_root}/{rel}" if arc_root else str(rel)
                zf.write(p, arc)
    return out_zip


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", default=".")
    args = ap.parse_args(argv)

    proj = Path(args.project)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    sheet = build_icon_sheet(proj / "icons" / "png_128",
                             proj / "preview" / "icons_preview.png")
    if sheet:
        print(f"icons preview: {sheet}")

    proj_zip = out / f"{proj.name}.zip"
    zip_dir(proj, proj_zip, arc_root=proj.name)
    print(f"project zip:  {proj_zip} ({proj_zip.stat().st_size} bytes)")

    icons_zip = out / "icons_assets.zip"
    if (proj / "icons").exists():
        zip_dir(proj / "icons", icons_zip)
        print(f"icons zip:    {icons_zip} ({icons_zip.stat().st_size} bytes)")

    pptx = proj / "ppt" / "editable_reproduction.pptx"
    if pptx.exists():
        dest = out / pptx.name
        shutil.copy2(pptx, dest)
        print(f"pptx:         {dest} ({dest.stat().st_size} bytes)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
