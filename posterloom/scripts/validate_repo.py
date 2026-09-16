#!/usr/bin/env python3
from pathlib import Path
import json, sys, re

REQUIRED_STYLE_HEADINGS=[
    "## Style intent","## Best for","## Reject when","## Style DNA",
    "## Execution contract","## Style-specific prompt block",
    "## Style-specific negative prompt","## Variation knobs",
    "## Hybrid behavior","## Common failure modes","## Self-check","## Acceptance criteria"
]
LEGACY=["luma"+"scene","scene"+"-to-"+"art-lab"]

def frontmatter(text):
    if not text.startswith("---\n"):
        return {}
    end=text.find("\n---\n",4)
    if end < 0:
        return {}
    out={}
    for line in text[4:end].splitlines():
        if ":" in line:
            k,v=line.split(":",1)
            out[k.strip()]=v.strip().strip('"').strip("'")
    return out

def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
    errors=[]
    skill=root/"SKILL.md"
    if not skill.exists():
        errors.append("SKILL.md missing")
    else:
        text=skill.read_text(encoding="utf-8")
        fm=frontmatter(text)
        if fm.get("name")!="posterloom":
            errors.append("SKILL.md name must be posterloom")
        if not fm.get("description"):
            errors.append("SKILL.md description missing")
        if not re.fullmatch(r"[a-z0-9-]{1,64}", fm.get("name","")):
            errors.append("SKILL.md name violates lowercase/hyphen/length constraints")
        if len(fm.get("description","")) > 1024:
            errors.append("SKILL.md description exceeds 1024 characters")
        if len(fm.get("compatibility","")) > 500:
            errors.append("SKILL.md compatibility exceeds 500 characters")
        if len(text.splitlines())>500:
            errors.append("SKILL.md exceeds 500 lines")

    data=json.loads((root/"data/styles.json").read_text(encoding="utf-8"))
    direct=[s for s in data["styles"] if s["role"]=="direct"]
    meta=[s for s in data["styles"] if s["role"]=="meta"]
    if len(direct)!=29:
        errors.append(f"expected 29 direct styles, got {len(direct)}")
    if len(meta)!=1 or meta[0]["id"]!="controlled-hybrid":
        errors.append("controlled-hybrid meta style missing")

    files=sorted((root/"styles").glob("*.md"))
    if len(files)!=30:
        errors.append(f"expected 30 style contracts, got {len(files)}")
    for p in files:
        t=p.read_text(encoding="utf-8")
        for heading in REQUIRED_STYLE_HEADINGS:
            if heading not in t:
                errors.append(f"{p.name}: missing {heading}")

    comp=json.loads((root/"data/compatibility.json").read_text(encoding="utf-8"))
    if len(comp.get("pairs",[]))!=74:
        errors.append(f"expected 74 hybrid pairs, got {len(comp.get('pairs',[]))}")

    oa=root/"agents/openai.yaml"
    if not oa.exists():
        errors.append("agents/openai.yaml missing")
    elif "$posterloom" not in oa.read_text(encoding="utf-8"):
        errors.append("openai.yaml default_prompt must mention $posterloom")

    for p in root.rglob("*"):
        if p.resolve() == Path(__file__).resolve():
            continue
        if p.is_file() and p.suffix.lower() in {".md",".json",".py",".yaml",".yml",".txt"}:
            t=p.read_text(encoding="utf-8",errors="ignore").lower()
            for old in LEGACY:
                if old in t:
                    errors.append(f"legacy name '{old}' found in {p.relative_to(root)}")

    if errors:
        print("VALIDATION FAILED")
        for e in errors:
            print("-",e)
        sys.exit(1)

    print("VALIDATION PASS")
    print(f"- direct styles: {len(direct)}")
    print(f"- meta styles: {len(meta)}")
    print(f"- style contracts: {len(files)}")
    print(f"- compatible hybrid pairs: {len(comp['pairs'])}")
    print(f"- SKILL.md lines: {len((root/'SKILL.md').read_text(encoding='utf-8').splitlines())}")
    print("- legacy-name scan: clean")

if __name__=="__main__":
    main()
