#!/usr/bin/env python3
import argparse, zipfile
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description="Package independent PosterLoom outputs.")
    ap.add_argument("input_dir")
    ap.add_argument("zip_path")
    args=ap.parse_args()
    src=Path(args.input_dir)
    out=Path(args.zip_path)
    files=[p for p in sorted(src.rglob("*")) if p.is_file()]
    if not files:
        raise SystemExit("No output files found.")
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p,p.relative_to(src))
    print(f"Packed {len(files)} files -> {out}")

if __name__=="__main__":
    main()
