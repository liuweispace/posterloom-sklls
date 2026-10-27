#!/usr/bin/env python3
"""Image generation backends for PosterLoom.

PosterLoom decides *what* to make. This module makes it.

Backends are pluggable and discovered from `data/backends.json`. Each backend
declares its own capabilities, because they differ in ways that change the
workflow rather than in details:

  - `max_prompt_chars`: MiniMax rejects prompts over 1500 characters. PosterLoom's
    full prompt is 4000-8000 characters, so the prompt has to be rebuilt for the
    budget, not truncated. `compact_prompt.build_compact` does that.
  - `supported_ratios`: MiniMax accepts 8 aspect ratios and NOT 3:5, which the
    zine styles are designed around. A style ratio that the backend cannot
    produce is mapped to the nearest supported one and reported.
  - `supports_image_reference`: whether the source photo can be sent along.
  - `max_images_per_call`: how many variations one call can return.

`generate()` is the single entry point. It returns a dict describing what was
produced, including every substitution it made, so the caller can report it
rather than hide it.
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

BACKENDS_JSON = ROOT / "data/backends.json"


def load_backends() -> dict:
    return json.loads(BACKENDS_JSON.read_text(encoding="utf-8"))


def get_backend(name: str) -> dict:
    data = load_backends()
    backends = data.get("backends", {})
    if name not in backends:
        raise KeyError(f"unknown backend '{name}'; have {sorted(backends)}")
    return backends[name]


def _api_key(backend: dict) -> str:
    """Resolve the API key from the environment or the Hermes .env file.

    The key is never written into the repo or into a prompt.
    """
    env_var = backend.get("api_key_env")
    if env_var:
        val = os.environ.get(env_var)
        if val:
            return val.strip()
        # Fall back to the Hermes .env file so the skill works from a plain
        # terminal without the user having to export anything.
        env_file = Path(os.path.expanduser("~/.hermes/.env"))
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.strip() == env_var:
                    return v.strip().strip('"').strip("'")
    raise RuntimeError(
        f"backend '{backend.get('id')}' needs {env_var}; "
        "set it in the environment or ~/.hermes/.env"
    )


def resolve_ratio(backend: dict, ratio: str) -> tuple:
    """Map a requested ratio onto one the backend supports.

    Returns (ratio_to_send, note). A note is returned whenever the requested
    ratio was changed — the caller reports it, because silently shipping a
    4:3 poster when the style asked for 3:5 is exactly the kind of thing that
    looks fine and is wrong.
    """
    ratio = ratio or "3:4"
    supported = backend.get("supported_ratios") or []
    if not supported:
        return ratio, None
    if ratio in supported:
        return ratio, None

    def parse(r):
        try:
            a, b = r.split(":")
            return float(a) / float(b)
        except Exception:
            return None

    want = parse(ratio)
    if want is None:
        return supported[0], f"ratio '{ratio}' unparseable; used {supported[0]}"

    best, best_err = None, None
    for r in supported:
        got = parse(r)
        if got is None:
            continue
        err = abs(got - want)
        if best_err is None or err < best_err:
            best, best_err = r, err
    if best is None:
        return supported[0], f"ratio '{ratio}' unsupported; used {supported[0]}"
    return best, (
        f"ratio '{ratio}' not supported by {backend.get('id')}; used {best} "
        f"(nearest of {', '.join(supported)})"
    )


def _encode_reference(path: Path) -> str:
    """Base64 data URI for the source photo."""
    data = base64.b64encode(path.read_bytes()).decode()
    suffix = path.suffix.lower().lstrip(".") or "jpeg"
    if suffix == "jpg":
        suffix = "jpeg"
    return f"data:image/{suffix};base64,{data}"


def _post(url: str, payload: dict, key: str, timeout: int = 240) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
            msg = parsed.get("base_resp", {}).get("status_msg") or body[:300]
        except Exception:
            msg = body[:300]
        raise RuntimeError(f"HTTP {e.code}: {msg}")


def _download(urls: list, out_dir: Path, prefix: str) -> list:
    """Fetch the generated images to disk."""
    saved = []
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, url in enumerate(urls, 1):
        with urllib.request.urlopen(url, timeout=120) as resp:
            blob = resp.read()
        path = out_dir / f"{prefix}-{i}.jpg"
        path.write_bytes(blob)
        saved.append(str(path))
    return saved


def call_minimax(backend: dict, prompt: str, *, ratio: str, count: int,
                  reference: Path = None, out_dir: Path = None,
                  prefix: str = "poster", timeout: int = 300) -> dict:
    """MiniMax image-01."""
    key = _api_key(backend)
    endpoint = backend.get("endpoint", "https://api.minimaxi.com/v1/image_generation")

    sent_ratio, ratio_note = resolve_ratio(backend, ratio)
    count = max(1, min(int(count), int(backend.get("max_images_per_call", 9))))

    payload = {
        "model": backend.get("model", "image-01"),
        "prompt": prompt,
        "aspect_ratio": sent_ratio,
        "n": count,
        "response_format": "url",
    }

    notes = []
    if ratio_note:
        notes.append(ratio_note)

    ref_used = False
    if reference is not None and backend.get("supports_image_reference"):
        payload["subject_reference"] = [{
            "type": backend.get("reference_type", "character"),
            "image_file": _encode_reference(reference),
        }]
        ref_used = True
    elif reference is not None:
        notes.append(
            f"backend '{backend.get('id')}' cannot take a reference image; "
            "the source photo was NOT sent — the prompt describes it instead"
        )

    limit = int(backend.get("max_prompt_chars", 1500))
    if len(prompt) > limit:
        raise RuntimeError(
            f"prompt is {len(prompt)} chars, over the {limit} limit for "
            f"{backend.get('id')}; use compact_prompt.build_compact()"
        )

    data = _post(endpoint, payload, key, timeout=timeout)
    urls = (data.get("data") or {}).get("image_urls") or []
    if not urls:
        raise RuntimeError(
            "backend returned no images: "
            + str(data.get("base_resp", {}).get("status_msg", "unknown error"))[:300]
        )

    saved = []
    if out_dir is not None:
        saved = _download(urls, out_dir, prefix)
    else:
        saved = urls

    return {
        "backend": backend.get("id"),
        "model": payload["model"],
        "requested_ratio": ratio,
        "used_ratio": sent_ratio,
        "reference_sent": ref_used,
        "images": saved,
        "image_urls": urls,
        "count": len(urls),
        "notes": notes,
    }


BACKEND_FUNCS = {"minimax": call_minimax}


def generate(backend_name: str, prompt: str, *, ratio: str = "3:4", count: int = 1,
             reference: Path = None, out_dir: Path = None,
             prefix: str = "poster", retry: int = 2) -> dict:
    """Generate images with the named backend."""
    backend = get_backend(backend_name)
    fn = BACKEND_FUNCS.get(backend.get("id"))
    if fn is None:
        raise KeyError(f"no implementation for backend '{backend.get('id')}'")

    last = None
    for attempt in range(retry + 1):
        try:
            return fn(backend, prompt, ratio=ratio, count=count,
                       reference=reference, out_dir=out_dir, prefix=prefix)
        except Exception as e:  # noqa: BLE001
            last = e
            if attempt < retry:
                time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"generation failed after {retry + 1} attempts: {last}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Generate images from a PosterLoom prompt.")
    ap.add_argument("prompt_file")
    ap.add_argument("--backend", default="minimax")
    ap.add_argument("--ratio", default="3:4")
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--reference")
    ap.add_argument("--out", default="posterloom-out")
    ap.add_argument("--prefix", default="poster")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    text = Path(args.prompt_file).read_text(encoding="utf-8")
    result = generate(
        args.backend, text,
        ratio=args.ratio, count=args.count,
        reference=Path(args.reference) if args.reference else None,
        out_dir=Path(args.out), prefix=args.prefix,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['backend']} / {result['model']}  ->  {result['count']} image(s)")
        for p in result["images"]:
            print(f"  {p}")
        for n in result["notes"]:
            print(f"  NOTE: {n}")
