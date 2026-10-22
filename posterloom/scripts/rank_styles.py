#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from collections import Counter
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
    """Symmetric normalized match.

    Uses the Dice coefficient (2|A&B| / (|A|+|B|)) so neither a terse scene
    profile nor a terse style definition is penalized. The previous form
    divided by min(len(scene), len(style)), which capped every dimension far
    below its weight and made the high/medium confidence bands unreachable.
    """
    if not scene_set or not style_set:
        return 0.0, []
    exact = scene_set & style_set
    if not exact:
        # fall back to fuzzy token overlap only
        partial = sum(
            1 for a in scene_set for b in style_set
            if a != b and token_overlap(a, b)
        )
        if not partial:
            return 0.0, []
        fuzzy = min(0.5, 0.12 * partial / max(1, min(len(scene_set), len(style_set))))
        return weight * fuzzy, []

    dice = (2.0 * len(exact)) / float(len(scene_set) + len(style_set))
    partial = sum(
        1 for a in scene_set for b in style_set
        if a != b and token_overlap(a, b)
    )
    fuzzy_bonus = min(0.12, 0.04 * partial)
    return weight * min(1.0, dice + fuzzy_bonus), sorted(exact)

def compatible_pair(a, b):
    comp = load_json(ROOT / "data/compatibility.json")
    for item in comp["pairs"]:
        if {item["style_a"], item["style_b"]} == {a,b}:
            return item
    return None

def rank(profile, top=5, used_styles=None, repetition_soft_cap=None):
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

    # Batch diversity: soft penalty only. Ten photographs that genuinely all fit
    # one style should keep it, but ten that all collide on a tie should spread.
    # Never a hard ban - correctness outranks variety.
    repetition_note = None
    if used_styles:
        cap = repetition_soft_cap
        if cap is None:
            cap = load_json(ROOT / "data/routing-rules.json").get("repetition_soft_cap", 3)
        counts = Counter(used_styles)
        for item in results:
            n = counts.get(item["style"], 0)
            if n >= cap:
                item["score"] = round(item["score"] - 3.0 * (n - cap + 1), 2)
                item["reasons"].append(f"batch repetition penalty (used {n}x)")

    # Artistic prior. Applied only as a tie-break nudge: on an exact score tie
    # the sort would otherwise fall back to alphabetical order, which is an
    # accident rather than an editorial decision. A real score difference always
    # wins, so this never overrides actual routing evidence.
    prior = rules.get("artistic_prior", {})
    art_bonus = prior.get("art_direction", {})
    plain_penalty = prior.get("plain_photographic", {})
    for item in results:
        delta = art_bonus.get(item["style"], 0) + plain_penalty.get(item["style"], 0)
        if delta:
            item["artistic_prior"] = delta

    results.sort(key=lambda x: (-x["score"], -x.get("artistic_prior", 0), x["style"]))
    top_results = results[:max(top, 2)]
    primary = top_results[0]["style"]
    fallback = top_results[1]["style"] if len(top_results) > 1 else None
    score0 = top_results[0]["score"]

    # Human-subject guardrail. A person whose likeness must survive cannot be
    # routed into a medium that repaints facial structure (watercolor, screenprint,
    # ink wash, lithograph...). The library's stylized styles are legitimate for
    # people only when the user actually asks for heavy transformation.
    person_types = {"person", "portrait", "human", "figure", "headshot", "face"}
    subject_type = str((profile.get("subject") or {}).get("type", "")).strip().lower()
    tags = norm(profile.get("subject_tags", []))
    is_person = subject_type in person_types or bool(
        tags & {"portrait", "person", "human", "face", "headshot"}
    )
    tol = str(profile.get("transformation_tolerance", "")).strip().lower()
    wants_heavy = tol in ("high", "medium-high")
    identity_risk = is_person and not wants_heavy

    identity_safe = rules.get(
        "identity_safe_styles",
        ["editorial-portrait", "photojournalistic", "fine-art-portrait"],
    )
    portrait_family = set(rules.get("portrait_family", "portrait").split("|"))
    destructive = set(rules.get("face_destructive_styles", []))
    safety_note = None

    # For a person whose likeness must survive, a face-designed style is not just
    # permitted, it is preferred. A generic style can be photographic and still be
    # the wrong tool for a face; blocking only the destructive ones lets a
    # general-purpose layout win and hand the model a face it was never tuned for.
    # "Make it artistic" is an explicit request for transformation, and it applies
    # to every subject, not just faces - a landscape can be art-directed too.
    #
    # For a person the guardrail still matters: only styles the artistic prior
    # already calls art-directed are unlocked, and the face-repainting set is
    # subtracted regardless. Likeness is fully protected; only the block on
    # stylization is lifted.
    art_intent = bool(tags & {"artistic", "art-directed", "stylize", "posterize",
                              "painterly", "experimental", "expressive"}) or bool(
        norm(profile.get("mood", [])) & {"expressive", "experimental", "raw"}
    )
    artistic_styles = set(rules.get("artistic_prior", {}).get("art_direction", {}))
    if is_person:
        # Never unlock a medium that repaints facial structure on a face.
        artistic_styles -= destructive
    elif wants_heavy:
        # Non-face subjects with heavy tolerance may use the full art-directed set,
        # including the print/painterly families.
        artistic_styles = set(
            rules.get("artistic_prior", {}).get("art_direction", {})
        ) | set(rules.get("artistic_prior", {}).get("art_direction_heavy", {}))
    if art_intent:
        boost = float(rules.get("artistic_request_boost", 12))
        for item in results:
            if item["style"] in artistic_styles:
                item["score"] = round(item["score"] + boost, 2)
                item["reasons"].append("artistic intent: art-directed style enabled")
        results.sort(key=lambda x: (-x["score"], -x.get("artistic_prior", 0), x["style"]))
        top_results = results[:max(top, 2)]
        score0 = top_results[0]["score"]
        primary = top_results[0]["style"]
        fallback = top_results[1]["style"] if len(top_results) > 1 else None
        if is_person:
            safety_note = (safety_note or "") + (
                " | artistic intent applied: art-directed styles enabled while "
                "identity lock stays active")
        else:
            safety_note = (safety_note or "") + (
                " | artistic intent applied: art-directed style enabled")

    if identity_risk:
        boost = float(rules.get("portrait_preference_boost", 18))
        for style in data["styles"]:
            if style.get("id") not in identity_safe:
                continue
            fam = style.get("family") or ""
            if portrait_family & set(fam.split("-")):
                for item in results:
                    if item["style"] == style["id"]:
                        item["score"] = round(item["score"] + boost, 2)
                        item["reasons"].append("face-designed style preferred for likeness")
        results.sort(key=lambda x: (-x["score"], -x.get("artistic_prior", 0), x["style"]))
        top_results = results[:max(top, 2)]
        score0 = top_results[0]["score"]
        primary = top_results[0]["style"]
        fallback = top_results[1]["style"] if len(top_results) > 1 else None

    if identity_risk and primary not in identity_safe and primary in destructive:
        swap = next(
            (r for r in results if r["style"] in identity_safe and r["style"] not in destructive),
            None,
        )
        if swap is not None:
            safety_note = (
                f"{primary} repaints facial structure; "
                f"routed to {swap['style']} to protect likeness"
            )
            primary = swap["style"]
            if fallback == primary:
                nxt = [r for r in results if r["style"] != primary]
                fallback = nxt[0]["style"] if nxt else None

    # Confidence is measured against the best score actually achievable in this
    # profile, not against an absolute scale. A sparse profile cannot produce a
    # high raw score no matter how well it matches, so comparing to the absolute
    # weight sum made every case look "low" and triggered the conservative
    # override below on essentially every run.
    ceiling = max([r["score"] for r in results], default=0.0)
    ratio = (score0 / ceiling) if ceiling > 0 else 0.0
    margin = (score0 - top_results[1]["score"]) if len(top_results) > 1 else 0.0

    if ratio >= 0.80 and margin >= 5:
        confidence = "high"
    elif ratio >= 0.55 or score0 >= rules.get("medium_score_floor", 0):
        confidence = "medium"
    else:
        confidence = "low"

    override = None
    reasons_note = "winner kept"
    # Conservative override only applies when the winner is genuinely weak AND a
    # conservative style nearly matches it. Previously this fired almost always,
    # collapsing every route onto the same three editorial styles.
    if confidence == "low":
        candidates = {r["style"]: r for r in results}
        conservative = rules.get(
            "conservative_styles",
            ["elegant-serif-poster", "cinematic-editorial", "documentary-poster"],
        )
        pool = [candidates[c] for c in conservative if c in candidates]
        if pool:
            best = max(pool, key=lambda x: x["score"])
            if best["score"] >= score0 - 3:
                override = best["style"]
                primary = best["style"]
                reasons_note = "conservative override"
            else:
                reasons_note = "winner kept despite low confidence"
        else:
            reasons_note = "winner kept despite low confidence"

    hybrid = None
    hp = rules["hybrid"]
    prefs = profile.get("user_preferences", {})
    # Hybrid needs an actually-decided primary; on a low-confidence route the
    # top two are noise, so blending them produces mush rather than intent.
    if (
        prefs.get("hybrid_allowed", True)
        and len(top_results) >= 2
        and confidence in ("high", "medium")
    ):
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
                "score_gap": round(gap, 2),
            }

    result = {
        "primary": primary,
        "fallback": fallback,
        "confidence": confidence,
        "ranking": top_results[:top],
        "hybrid": hybrid,
        "diagnostics": {
            "winner": top_results[0]["style"],
            "winner_score": score0,
            "ceiling": round(ceiling, 2),
            "ratio": round(ratio, 3),
            "margin": round(margin, 2),
            "override": override,
            "note": reasons_note,
            "identity_guard": safety_note,
            "batch_repetition": repetition_note,
            "is_person": is_person,
            "identity_risk": identity_risk,
        },
    }

    # Surface the facial-identity lock here too, not only in prompt compilation,
    # so every consumer (route, batch, other agents) sees that likeness
    # enforcement is active for this source.
    try:
        import face_identity as _fi
        lock = _fi.build(profile, style_id=primary)
    except Exception:
        lock = None
    result["facial_identity_lock"] = (
        {
            "active": True,
            "identity_risk": lock["identity_risk"],
            "heavy_transformation_requested": lock["heavy_transformation_requested"],
        }
        if lock
        else {"active": False}
    )
    return result

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
