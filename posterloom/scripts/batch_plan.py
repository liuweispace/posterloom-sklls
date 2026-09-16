#!/usr/bin/env python3
import argparse, json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rank_styles import rank

def main():
    ap=argparse.ArgumentParser(description="Plan a PosterLoom batch without forcing style diversity.")
    ap.add_argument("profiles", help="JSON array of scene profiles")
    ap.add_argument("--output")
    args=ap.parse_args()
    profiles=json.loads(Path(args.profiles).read_text(encoding="utf-8"))
    if not isinstance(profiles,list):
        raise SystemExit("Expected a JSON array.")
    plan=[]
    for i,p in enumerate(profiles,1):
        r=rank(p,top=5)
        plan.append({"index":i,"primary":r["primary"],"fallback":r["fallback"],"confidence":r["confidence"],"hybrid":r["hybrid"]})
    counts=Counter(x["primary"] for x in plan)
    repeats={k:v for k,v in counts.items() if v>1}
    result={
        "jobs":plan,
        "style_repetition":repeats,
        "note":"Repeated styles are reported but never changed merely for diversity. Each source remains an independent job."
    }
    text=json.dumps(result,indent=2,ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text+"\n",encoding="utf-8")
    else:
        print(text)

if __name__=="__main__":
    main()
