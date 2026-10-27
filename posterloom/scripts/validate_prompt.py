#!/usr/bin/env python3
import argparse, sys
from pathlib import Path

REQUIRED = [
    "Use exactly one source photograph",
    "Identity anchors:",
    "Create one finished poster",
    "Never create a collage",
    "PRIMARY STYLE",
    "NEGATIVE CONSTRAINTS",
    "FINAL CHECK",
]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("prompt")
    args=ap.parse_args()
    text=Path(args.prompt).read_text(encoding="utf-8")
    errors=[f"missing required phrase: {x}" for x in REQUIRED if x not in text]
    if errors:
        print("FAIL")
        for e in errors:
            print("-",e)
        sys.exit(1)
    print("PASS: source binding, single-poster rule, style block, negatives, and final QA are present.")

if __name__=="__main__":
    main()
