#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from rank_styles import rank

cases=json.loads((ROOT/"evals/routing-cases.json").read_text(encoding="utf-8"))
fails=[]
for case in cases:
    result=rank(case["profile"],top=5)
    if result["primary"] != case["expected_primary"]:
        fails.append((case["id"],case["expected_primary"],result["primary"],result["ranking"]))

print(f"Routing regression cases: {len(cases)}")
print(f"Exact primary matches: {len(cases)-len(fails)}/{len(cases)}")
if fails:
    print("FAILURES")
    for cid,exp,got,ranking in fails:
        print(f"- {cid}: expected={exp} got={got}")
        print("  top:",[(r["style"],r["score"]) for r in ranking[:3]])
    sys.exit(1)
print("PASS")
