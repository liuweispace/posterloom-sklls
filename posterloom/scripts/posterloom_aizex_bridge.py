#!/usr/bin/env python3
"""posterloom-aizex bridge — compress PosterLoom compiled prompt to aizex-ready 300-char prompt.

Usage:
  python scripts/posterloom_aizex_bridge.py profiles/<name>.json > aizex_prompt.txt
"""
import json, sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compose_prompt import compile_prompt
from rank_styles import rank

def compress(compiled):
    # extract fields
    def grab(field):
        m = re.search(rf"{field}:\s*([^\n]+)", compiled)
        return m.group(1).strip() if m else ""
    anchors = grab("Identity anchors")
    style_name = re.search(r'PRIMARY STYLE — ([^\n]+)', compiled)
    title = grab("Requested title")
    subtitle = grab("Requested subtitle")
    # first mechanism sentence
    mech_block = re.search(r'Mechanism:\s*([^\n]+)', compiled)
    mech = mech_block.group(1).strip() if mech_block else ""
    # first negative
    neg_m = re.search(r'NEGATIVE CONSTRAINTS\n-\s*No\s+([^\n,;]+)', compiled)
    neg = neg_m.group(1).strip() if neg_m else ""
    # build aizex-ready compact prompt (300-400 chars target)
    parts = [
        f"TRANSFORM THE UPLOADED IMAGE INTO A POSTER using the {style_name.group(1) if style_name else 'poster'} style.",
        f"Keep the subject visible and recognizable.",
        f"Preserve: {anchors}.",
        f"Apply this mechanism to the uploaded photo: {mech[:200]}.",
        f"Avoid: {neg}, invented Chinese characters, generic AI gradient, fabricated text/branding, missing typography." if neg else "",
        f"Render title as serif at top: {title}." if title else "",
        f"Subtitle below title: {subtitle}." if subtitle else "",
        "Typography ≤5-10% of image, never covers subject.",
        "Generate one 3:4 poster.",
    ]
    return " ".join([p for p in parts if p]).strip()

def main():
    profile_path = sys.argv[1]
    style_override = sys.argv[2] if len(sys.argv) > 2 else None
    profile = json.loads(Path(profile_path).read_text())
    compiled, _ = compile_prompt(profile, style_override)
    print(compress(compiled))

if __name__ == "__main__":
    main()
