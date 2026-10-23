#!/usr/bin/env python3
"""Check the compact prompt builder across every style and scene.

Verifies the four things the image pipeline depends on:
  1. the prompt fits the backend's character budget
  2. the identity lock is present whenever the scene has a face
  3. the NO PHOTOGRAPHY rule is present for semantic-reference styles
  4. the layout and colour sections survive — they are what make the output
     the requested style rather than a generic print
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from compose_prompt import load, style_by_id  # noqa: E402
from compact_prompt import build_compact  # noqa: E402

BUDGET = 1400
LONG_SUBJECT = (
    "Subject: " + ("age young; gender male; face shape oval; jawline soft; "
                   "eyes closed; brows thick; nose prominent; mouth open; skin smooth; "
                   "hair dark; hairline normal; head angle down; gaze down; "
                   "expression neutral. " * 2)
)


def main() -> int:
    scenes = {
        "portrait": load(str(ROOT / "examples/scene-portrait.json")),
        "tree": load(str(ROOT / "examples/scene-solitary-tree.json")),
        "teahouse": load(str(ROOT / "examples/scene-night-teahouse.json")),
    }
    data = json.loads((ROOT / "data/styles.json").read_text(encoding="utf-8"))
    styles = [s["id"] for s in data["styles"] if s["role"] == "direct"]

    failures = []
    lengths = []
    count = 0
    for scene_name, profile in scenes.items():
        for style_id in styles:
            style = style_by_id(style_id)
            for override in (None, LONG_SUBJECT):
                count += 1
                prompt = build_compact(profile, style, subject_override=override)
                lengths.append(len(prompt))
                tag = f"{scene_name}/{style_id}{'+long' if override else ''}"
                if len(prompt) > BUDGET:
                    failures.append(f"{tag}: {len(prompt)} chars, over {BUDGET}")
                if scene_name == "portrait" and "IDENTITY LOCK" not in prompt:
                    failures.append(f"{tag}: identity lock missing")
                if style.get("source_role") == "semantic-reference" \
                        and "NO PHOTOGRAPHY" not in prompt:
                    failures.append(f"{tag}: NO PHOTOGRAPHY missing")
                if style.get("color_system") and "COLOUR:" not in prompt:
                    failures.append(f"{tag}: COLOUR section missing")
                if style.get("composition") and "LAYOUT:" not in prompt:
                    failures.append(f"{tag}: LAYOUT section missing")

    print(f"combinations: {count}")
    print(f"length range: {min(lengths)}-{max(lengths)} chars (budget {BUDGET})")
    if failures:
        print(f"FAILURES: {len(failures)}")
        for f in failures[:20]:
            print(f"  {f}")
        return 1
    print("PASS: budget, identity lock, NO PHOTOGRAPHY, COLOUR and LAYOUT all hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
