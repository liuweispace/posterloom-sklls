#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def norm(values):
    if values is None:
        return set()
    if isinstance(values, str):
        values = [values]
    return {str(v).strip().lower() for v in values if str(v).strip()}

def scene_features(profile):
    subject = profile.get("subject", {})
    return {
        "subject": norm([subject.get("type","")] + profile.get("subject_tags", [])),
        "lighting": norm(profile.get("lighting", [])),
        "mood": norm(profile.get("mood", [])),
        "geometry": norm(profile.get("geometry", [])),
        "materials": norm(profile.get("materials", [])),
        "palette": norm(profile.get("palette", [])),
        "realism": norm([profile.get("realism_value","")]),
        "transform": norm([profile.get("transformation_tolerance","")]),
    }

def token_overlap(a, b):
    at = set(a.replace("_","-").split("-"))
    bt = set(b.replace("_","-").split("-"))
    return bool(at & bt)

def overlap_score(scene_set, style_set, weight):
    if not scene_set or not style_set:
        return 0.0, []
    exact = scene_set & style_set
    partial = set()
    for a in scene_set:
        for b in style_set:
            if a == b:
                continue
            if token_overlap(a,b):
                partial.add((a,b))
    exact_part = min(1.0, len(exact) / max(1, min(len(scene_set), len(style_set))))
    partial_part = min(0.35, 0.06 * len(partial))
    return weight * min(1.0, exact_part + partial_part), sorted(exact)

def compatible_pair(a, b):
    comp = load_json(ROOT / "data/compatibility.json")
    for item in comp["pairs"]:
        if {item["style_a"], item["style_b"]} == {a,b}:
            return item
    return None

def rank(profile, top=5):
    data = load_json(ROOT / "data/styles.json")
    rules = load_json(ROOT / "data/routing-rules.json")
    sf = scene_features(profile)
    results = []

    for style in data["styles"]:
        if style.get("role") != "direct":
            continue
        routing = style.get("routing", {})
        score = 0.0
        reasons = []
        for key, weight in rules["weights"].items():
            value, matches = overlap_score(sf.get(key,set()), norm(routing.get(key,[])), float(weight))
            score += value
            if matches:
                reasons.append(f"{key}: {', '.join(matches)}")

        prefs = profile.get("user_preferences", {})
        if style["id"] in prefs.get("prefer_styles", []):
            score += 8
            reasons.append("user preference bias")
        if style["id"] in prefs.get("avoid_styles", []):
            score -= 30
            reasons.append("user avoid penalty")

        results.append({
            "style": style["id"],
            "name": style["name"],
            "score": round(score,2),
            "reasons": reasons,
        })

    results.sort(key=lambda x: (-x["score"], x["style"]))
    top_results = results[:max(top,2)]
    primary = top_results[0]["style"]
    fallback = top_results[1]["style"] if len(top_results) > 1 else None
    score0 = top_results[0]["score"]

    if score0 >= 60:
        confidence = "high"
    elif score0 >= rules["low_confidence_threshold"]:
        confidence = "medium"
    else:
        confidence = "low"

    hybrid = None
    hp = rules["hybrid"]
    prefs = profile.get("user_preferences", {})
    if prefs.get("hybrid_allowed", True) and len(top_results) >= 2:
        gap = top_results[0]["score"] - top_results[1]["score"]
        pair = compatible_pair(primary, fallback)
        if pair and score0 >= hp["min_primary_score"] and gap <= hp["max_score_gap"]:
            hybrid = {
                "enabled": True,
                "primary": primary,
                "secondary": fallback,
                "primary_share": hp["primary_share"],
                "secondary_share": hp["secondary_share"],
                "secondary_role": pair["secondary_role"],
                "score_gap": round(gap,2),
            }

    # Conservative fallback for weak signals.
    if confidence == "low":
        candidates = {r["style"]: r for r in results}
        conservative = ["elegant-serif-poster","cinematic-editorial","documentary-poster"]
        best = max((candidates[c] for c in conservative), key=lambda x: x["score"])
        if best["score"] >= score0 - 8:
            primary = best["style"]
            hybrid = None

    return {
        "primary": primary,
        "fallback": fallback,
        "confidence": confidence,
        "ranking": top_results[:top],
        "hybrid": hybrid,
    }

def main():
    ap = argparse.ArgumentParser(description="Rank PosterLoom direct styles for a scene profile.")
    ap.add_argument("profile")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    result = rank(load_json(args.profile), args.top)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"PRIMARY: {result['primary']}  confidence={result['confidence']}")
        if result.get("fallback"):
            print(f"FALLBACK: {result['fallback']}")
        if result.get("hybrid"):
            print("HYBRID:", json.dumps(result["hybrid"], ensure_ascii=False))
        print("\nRANKING")
        for item in result["ranking"]:
            why = (" | " + "; ".join(item["reasons"])) if item["reasons"] else ""
            print(f"{item['score']:6.2f}  {item['style']}{why}")

if __name__ == "__main__":
    main()
