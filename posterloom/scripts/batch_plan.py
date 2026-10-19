#!/usr/bin/env python3
"""Plan a PosterLoom batch.

Routes every source independently, then applies a soft repetition penalty so a
batch of near-identical scenes does not collapse onto one style. The penalty is
deliberately soft: when sources genuinely fit the same style, variety is not
worth sacrificing correctness.

Usage:
    python3 scripts/batch_plan.py profiles.json [--output plan.json] [--soft-cap 3]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rank_styles import rank


def plan_batch(profiles, soft_cap=3):
    used = []
    jobs = []
    for i, profile in enumerate(profiles, 1):
        r = rank(profile, top=5, used_styles=list(used), repetition_soft_cap=soft_cap)
        used.append(r["primary"])
        d = r.get("diagnostics", {})
        jobs.append({
            "index": i,
            "subject": ((profile.get("subject") or {}).get("type")),
            "primary": r["primary"],
            "fallback": r["fallback"],
            "confidence": r["confidence"],
            "hybrid": r.get("hybrid"),
            "facial_identity_lock": r.get("facial_identity_lock"),
            "identity_guard": d.get("identity_guard"),
            "override": d.get("override"),
            "contract": f"styles/{r['primary']}.md",
        })

    counts = Counter(j["primary"] for j in jobs)
    repeats = {k: v for k, v in counts.items() if v > 1}
    return {
        "jobs": jobs,
        "style_repetition": repeats,
        "unique_styles": len(counts),
        "total_jobs": len(jobs),
        "soft_cap": soft_cap,
        "note": (
            "Each source is routed independently. A soft penalty applies once a style "
            f"exceeds {soft_cap} uses in one batch; it never overrides a clear fit."
        ),
    }


def main():
    ap = argparse.ArgumentParser(description="Plan a PosterLoom batch.")
    ap.add_argument("profiles", help="JSON array of scene profiles")
    ap.add_argument("--output")
    ap.add_argument("--soft-cap", type=int, default=3)
    args = ap.parse_args()

    profiles = json.loads(Path(args.profiles).read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("ERROR: expected a JSON array of scene profiles.")

    result = plan_batch(profiles, args.soft_cap)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"WROTE {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
