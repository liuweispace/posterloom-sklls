#!/usr/bin/env python3
"""Check that every token the scene analyzer can emit is one the router knows.

A term the router never matches is dead weight: it silently dilutes the
normalization and makes the profile look more informative than it is.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from scene_analyze import analyze  # noqa: E402

data = json.loads((ROOT / "data/styles.json").read_text(encoding="utf-8"))
vocab = {"palette": set(), "lighting": set(), "geometry": set(), "materials": set()}
for s in data["styles"]:
    r = s.get("routing", {})
    for k in vocab:
        vocab[k].update(r.get(k, []))

imgs = sys.argv[1:] or []
if not imgs:
    print("usage: check_analyzer_vocab.py <image> [image ...]")
    sys.exit(2)

bad = []
for img in imgs:
    p = analyze(Path(img))
    for k in vocab:
        for term in p.get(k, []):
            if term not in vocab[k]:
                bad.append((img, k, term))

print("router vocabulary sizes:", {k: len(v) for k, v in vocab.items()})
if bad:
    print("\nUNKNOWN TERMS (will never match a style):")
    for img, k, term in bad:
        print(f"  {k:<11} {term:<22} <- {Path(img).name}")
    sys.exit(1)
print("\nOK: every emitted term is recognised by the router")
