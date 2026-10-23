#!/usr/bin/env python3
"""posterloom — adaptive photo-to-poster CLI.

A single, dependency-free entrypoint implementing the OpenAI Agent Skills
specification layout:

    posterloom/
      SKILL.md          (manifest)
      scripts/posterloom.py   (this file — tiny deterministic CLI)
      data/ references/ styles/ schemas/ examples/ evals/

Design rules followed (per OpenAI's skills guidance):
  * Deterministic stdout, machine-readable with --json.
  * Fails loudly with a non-zero exit code and a readable message.
  * No network access, no third-party imports — standard library only.

Subcommands
-----------
  route      Rank styles for one scene profile.
  prompt     Compile a full generation prompt for one profile.
  batch      Plan a whole batch with soft repetition damping.
  styles     List the style library.
  show       Print one style contract.
  validate   Validate a profile (or all examples) against the schema.
  selftest   Run routing regression + contract coverage checks.

Examples
--------
  python3 scripts/posterloom.py route    examples/scene-portrait.json
  python3 scripts/posterloom.py prompt   examples/scene-portrait.json --json
  python3 scripts/posterloom.py batch    examples/batch-profiles.json
  python3 scripts/posterloom.py styles   --family portrait
  python3 scripts/posterloom.py show     editorial-portrait
  python3 scripts/posterloom.py validate examples/scene-portrait.json
  python3 scripts/posterloom.py selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rank_styles import rank                      # noqa: E402
from batch_plan import plan_batch                 # noqa: E402
import compose_prompt as composer                 # noqa: E402
import face_identity                               # noqa: E402


def die(msg: str, code: int = 2):
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_json(path: Path):
    if not path.exists():
        die(f"file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"invalid JSON in {path}: {e}")


def load_styles():
    data = load_json(ROOT / "data/styles.json")
    return data, [s for s in data["styles"] if s.get("role") == "direct"]


# --------------------------------------------------------------------------- #
# subcommands
# --------------------------------------------------------------------------- #
def cmd_route(args):
    profile = load_json(Path(args.profile))
    r = rank(profile, top=args.top)
    if args.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0
    d = r.get("diagnostics", {})
    print(f"PRIMARY: {r['primary']}  confidence={r['confidence']}")
    if r.get("fallback"):
        print(f"FALLBACK: {r['fallback']}")
    if r.get("hybrid"):
        h = r["hybrid"]
        print(f"HYBRID:   primary={h['primary']} secondary={h['secondary']} "
              f"({int(h['primary_share']*100)}/{int(h['secondary_share']*100)})")
    lock = r.get("facial_identity_lock") or {}
    if lock.get("active"):
        heavy = lock.get("heavy_transformation_requested")
        print("LOCK:     ON - facial identity lock active"
              + (" (heavy transformation explicitly requested)" if heavy else ""))
    else:
        print("LOCK:     off (no recognizable human face in this source)")
    if d.get("identity_guard"):
        print(f"GUARD:    {d['identity_guard']}")
    if d.get("override"):
        print(f"OVERRIDE: {d['note']}")
    print("\nRANKING")
    for item in r["ranking"]:
        why = (" | " + "; ".join(item["reasons"])) if item["reasons"] else ""
        print(f"{item['score']:6.2f}  {item['style']}{why}")
    return 0


def cmd_prompt(args):
    profile = load_json(Path(args.profile))
    prompt, route = composer.compile_prompt(profile, args.style)
    if args.route_output:
        Path(args.route_output).write_text(
            json.dumps(route, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    if args.output:
        Path(args.output).write_text(prompt + "\n", encoding="utf-8")
        print(f"WROTE {args.output}")
    else:
        print(prompt)
    return 0


def cmd_batch(args):
    profiles = load_json(Path(args.profile))
    if not isinstance(profiles, list):
        die("expected a JSON array of scene profiles")
    result = plan_batch(profiles, args.soft_cap)
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"WROTE {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_styles(args):
    _, direct = load_styles()
    rows = direct
    if args.family:
        rows = [s for s in rows if args.family.lower() in (s.get("family") or "").lower()]
    if args.portrait:
        rows = [s for s in rows if "portrait" in (s.get("family") or "")
                or s.get("id") == "photojournalistic"]
    if args.json:
        print(json.dumps([
            {"id": s["id"], "name": s["name"], "family": s["family"],
             "realism": s["realism"], "transformation": s["transformation"]}
            for s in rows], indent=2, ensure_ascii=False))
        return 0
    print(f"{len(rows)} styles\n")
    print(f"{'id':<32}{'family':<26}{'real':<9}trans")
    for s in rows:
        print(f"{s['id']:<32}{s['family']:<26}{s['realism']:<9}{s['transformation']}")
    return 0


def cmd_show(args):
    path = ROOT / "styles" / f"{args.style_id}.md"
    if not path.exists():
        die(f"unknown style '{args.style_id}' (expected styles/{args.style_id}.md)")
    print(path.read_text(encoding="utf-8"))
    return 0


def cmd_validate(args):
    schema_path = ROOT / "schemas/scene-profile.schema.json"
    schema = load_json(schema_path)
    required = schema.get("required", [])

    targets = ([Path(args.profile)] if args.profile
               else sorted((ROOT / "examples").glob("*.json")))
    targets = [t for t in targets if t.name != "batch-profiles.json"]

    failures = 0
    for t in targets:
        data = load_json(t)
        missing = [k for k in required if k not in data]
        subj = data.get("subject") or {}
        sub_required = (schema["properties"]["subject"].get("required") or [])
        missing += [f"subject.{k}" for k in sub_required if k not in subj]
        anchors = subj.get("identity_anchors") or []
        if not anchors:
            missing.append("subject.identity_anchors (min 1 required)")
        if missing:
            failures += 1
            print(f"INVALID {t.name}: missing {', '.join(missing)}")
        else:
            print(f"VALID   {t.name}")
    if failures:
        die(f"{failures}/{len(targets)} profiles invalid")
    print(f"\nOK: {len(targets)} profile(s) valid")
    return 0


def cmd_selftest(args):
    """Contract coverage + identity-lock behaviour + routing smoke test."""
    _, direct = load_styles()

    # 1. every direct style has a contract file
    missing = [s["id"] for s in direct if not (ROOT / "styles" / f"{s['id']}.md").exists()]
    if missing:
        die(f"styles missing contract files: {missing}")

    # 2. identity lock fires on faces, stays off otherwise
    face = {"subject": {"type": "portrait", "identity_anchors": ["face shape"]},
            "subject_tags": ["portrait"], "transformation_tolerance": "low"}
    land = {"subject": {"type": "landscape", "identity_anchors": ["mountain profile"]},
            "lighting": ["golden_hour"], "transformation_tolerance": "medium"}
    if not face_identity.has_face_risk(face):
        die("identity lock did NOT fire on a portrait profile")
    if face_identity.has_face_risk(land):
        die("identity lock fired on a landscape profile")

    # 3. portrait routes to an identity-safe style
    r = rank(face, top=5)
    safe = {"editorial-portrait", "photojournalistic", "fine-art-portrait"}
    if r["primary"] not in safe:
        die(f"portrait routed to {r['primary']}, expected one of {safe}")

    # scene analyzer must emit only router-recognised terms
    import glob
    frames = sorted(glob.glob(str(ROOT / "references/reference-frames/*.jpg")))
    if frames:
        from scene_analyze import analyze
        from rank_styles import load_json as _lj
        _data = _lj(ROOT / "data/styles.json")
        _vocab = {"palette": set(), "lighting": set(), "geometry": set(),
                  "materials": set()}
        for _s in _data["styles"]:
            _r = _s.get("routing", {})
            for _k in _vocab:
                _vocab[_k].update(_r.get(_k, []))
        for _f in frames:
            _p = analyze(Path(_f))
            for _k in _vocab:
                for _t in _p.get(_k, []):
                    if _t not in _vocab[_k]:
                        die(f"analyzer emitted unknown {_k} term: {_t}")

    # reference matcher must pick a valid style, and the one-command workflow
    # must produce a prompt end to end
    import glob as _glob
    _frames = sorted(_glob.glob(str(ROOT / "references/reference-frames/*.jpg")))
    if _frames:
        from match_reference import match as _match
        from make_poster import main as _make_main
        _m = _match(Path(_frames[0]))
        if not _m.get("best"):
            die("reference matcher returned no best style")
        if _m["best"]["style"] not in {s["id"] for s in _data["styles"]}:
            die(f"reference matcher chose unknown style: {_m['best']['style']}")
        # Run the workflow with output captured so selftest stays readable.
        import contextlib
        import io as _io
        _buf = _io.StringIO()
        with contextlib.redirect_stdout(_buf):
            _rc = _make_main(["make", _frames[0], "--json"])
        if _rc != 0:
            die(f"make workflow failed with rc={_rc}")
        if "prompt" not in _buf.getvalue():
            die("make workflow produced no prompt")

    # repo-level structural validation (contract headings, ids, hybrid pairs)
    import subprocess
    vr = subprocess.run([sys.executable, str(ROOT / "scripts/validate_repo.py"), str(ROOT)],
                        capture_output=True, text=True)
    if vr.returncode != 0:
        print(vr.stdout.strip() or vr.stderr.strip(), file=sys.stderr)
        die("validate_repo.py failed")

    print(f"OK: {len(direct)} styles have contracts")
    print("OK: identity lock fires on faces, silent on non-faces")
    print("OK: scene analyzer emits only router-recognised terms")
    print("OK: reference matcher and make workflow run end to end")
    print(f"OK: portrait routes to {r['primary']}")
    return 0


# --------------------------------------------------------------------------- #
def cmd_make(args):
    """One command: photo in, finished poster prompt out."""
    import make_poster as make_mod

    argv = ["make", args.image]
    for flag, value in (
        ("--style", args.style), ("--reference", args.reference),
        ("--type", args.type), ("--summary", args.summary),
        ("--anchors", args.anchors), ("--mood", args.mood),
        ("--tags", args.tags), ("--tolerance", args.tolerance),
        ("--realism", args.realism), ("--ratio", args.ratio),
        ("--out", args.out),
    ):
        if value:
            argv += [flag, value]
    if args.json:
        argv.append("--json")
    return make_mod.main(argv)


def cmd_match(args):
    """Match a reference poster to the closest built-in style."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from match_reference import match

    out = match(Path(args.reference), top=args.top)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        m = out["measured"]
        print(f"REFERENCE {args.reference}")
        print(f"  contrast {m['contrast']} · saturation {m['saturation']} "
              f"· density {m['density']}")
        print(f"  palette: {', '.join(m['palette_families'])}")
        print()
        for r in out["matches"]:
            print(f"  {r['style']:<28} {r['score']:.3f}  {r['name']}")
        if out.get("best"):
            print()
            print(f"USE: posterloom.py make <photo> --style {out['best']['style']}")
    return 0


def cmd_analyze(args):
    """Derive a scene profile from an image file."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from scene_analyze import analyze

    profile = analyze(Path(args.image))
    if args.out:
        Path(args.out).write_text(
            json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"WROTE {args.out}")
    else:
        print(json.dumps(profile, ensure_ascii=False, indent=2))
    needs = profile.get("_needs_vision", [])
    if needs:
        print(
            "\nNOTE: measured from pixels - "
            + ", ".join(needs)
            + " still need a vision model or a human.",
            file=sys.stderr,
        )
    return 0


def cmd_package(args):
    """Zip a directory of finished poster outputs."""
    import zipfile
    src = Path(args.input_dir)
    out = Path(args.zip_path)
    if not src.is_dir():
        die(f"not a directory: {src}")
    files = [p for p in sorted(src.rglob("*")) if p.is_file()]
    if not files:
        die(f"no files to package in {src}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(src))
    print(f"WROTE {out} ({len(files)} files)")
    return 0


def build_parser():
    ap = argparse.ArgumentParser(
        prog="posterloom",
        description="Adaptive photo-to-poster: route styles and compile generation prompts.",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("route", help="rank styles for one scene profile")
    p.add_argument("profile")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_route)

    p = sub.add_parser("prompt", help="compile a full generation prompt")
    p.add_argument("profile")
    p.add_argument("--style", help="force one direct style id")
    p.add_argument("--output")
    p.add_argument("--route-output")
    p.set_defaults(func=cmd_prompt)

    p = sub.add_parser("batch", help="plan a batch of profiles")
    p.add_argument("profile")
    p.add_argument("--soft-cap", type=int, default=3)
    p.add_argument("--output")
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser("styles", help="list the style library")
    p.add_argument("--family")
    p.add_argument("--portrait", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_styles)

    p = sub.add_parser("show", help="print one style contract")
    p.add_argument("style_id")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("validate", help="validate profiles against the schema")
    p.add_argument("profile", nargs="?")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("make", help="photo in, finished poster prompt out")
    p.add_argument("image")
    p.add_argument("--style", help="force a style id")
    p.add_argument("--reference", help="reference poster to match the style from")
    p.add_argument("--type", help="subject type: portrait, landscape, architecture, ...")
    p.add_argument("--summary", help="one factual sentence about the subject")
    p.add_argument("--anchors", help="comma separated identity anchors")
    p.add_argument("--mood", help="comma separated moods")
    p.add_argument("--tags", help="comma separated subject tags")
    p.add_argument("--tolerance", help="transformation tolerance: low|medium|medium-high|high")
    p.add_argument("--realism", help="realism value: low|medium|high|very-high")
    p.add_argument("--ratio", help="output ratio, e.g. 3:4")
    p.add_argument("--out", help="write the prompt here")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_make)

    p = sub.add_parser("match", help="match a reference poster to a style")
    p.add_argument("reference")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_match)

    p = sub.add_parser("analyze", help="derive a scene profile from an image")
    p.add_argument("image")
    p.add_argument("--out", help="write the profile JSON here")
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("package", help="zip finished poster outputs")
    p.add_argument("input_dir")
    p.add_argument("zip_path")
    p.set_defaults(func=cmd_package)

    p = sub.add_parser("selftest", help="run integrity checks")
    p.set_defaults(func=cmd_selftest)
    return ap


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
