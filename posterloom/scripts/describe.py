#!/usr/bin/env python3
"""Vision helpers for PosterLoom's generation pipeline.

Two jobs, both served by the same MiniMax chat endpoint:

1. `describe_identity()` — turn a photo into a factual description of the
   person in it, so the image prompt can name that person instead of attaching
   the photo.

   This exists because of a measured finding: when a photo is attached to the
   image request, the model reproduces the photograph's continuous tone and the
   flat-print style collapses back into a photograph — even with an explicit
   "render as a print, not a photo" instruction. Describing the subject in
   words and generating from text keeps the print treatment. The trade-off is
   that likeness becomes a text description rather than a pixel copy, so the
   description is asked for hard, checkable facts only.

2. `classify_style()` — ask a vision model whether a generated image is a flat
   limited-ink print or a photograph. This is the acceptance gate for
   generation: pixel statistics could not separate the two reliably (a
   duotone-treated photograph and a true flat print have nearly identical
   colour histograms), but a vision model separates them correctly.

Neither function puts an API key into a file, a prompt, or a log.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

CHAT_URL = "https://api.minimaxi.com/v1/text/chatcompletion_v2"
VISION_MODEL = "MiniMax-Text-01"

IDENTITY_PROMPT = (
    "You are writing a reference sheet for a poster illustrator. Return ONLY a JSON object, "
    "no markdown, no commentary, with these keys, each a short phrase of 2-8 words: "
    "age, gender, face_shape, jawline, eyes, brows, nose, mouth, facial_hair, skin, marks, "
    "hair, hairline, clothing, head_angle, gaze, expression. "
    "Describe only what is visible. If a feature is absent, use \"none\"."
)

SCENE_PROMPT = (
    "Describe this image for a poster illustrator. Give ONLY observable facts — no art style, no "
    "mood words. Cover: the main subject and its spatial relationships, secondary elements, "
    "setting, notable shapes and lines, light direction, colour distribution, and where the "
    "quiet areas are. Be specific and factual, and keep it under 120 words."
)

STYLE_QUESTION = (
    "Is this image a flat limited-ink screenprint / risograph / woodcut poster — flat colour "
    "areas, visible ink grain, hard posterised edges, no continuous photographic tone — or is it "
    "a photograph or a photorealistic render? Answer with exactly one word: PRINT or PHOTO."
)


def _api_key() -> str:
    val = os.environ.get("MINIMAX_API_KEY")
    if val:
        return val.strip()
    env_file = Path(os.path.expanduser("~/.hermes/.env"))
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == "MINIMAX_API_KEY":
                return v.strip().strip('"').strip("'")
    raise RuntimeError("MINIMAX_API_KEY is not set in the environment or ~/.hermes/.env")


def _data_uri(path) -> str:
    path = Path(path)
    suffix = path.suffix.lower().lstrip(".") or "jpeg"
    if suffix == "jpg":
        suffix = "jpeg"
    return f"data:image/{suffix};base64," + base64.b64encode(path.read_bytes()).decode()


def _chat_with_image(prompt: str, image_path, model: str = VISION_MODEL,
                     max_tokens: int = 700, timeout: int = 180) -> str:
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": _data_uri(image_path)}},
            ],
        }],
        "max_completion_tokens": max_tokens,
    }
    req = urllib.request.Request(
        CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"vision API HTTP {e.code}: {body[:200]}")
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    return content.strip()


def describe_identity(image_path) -> str:
    """A factual description of the person in the photo.

    Returns a compact prose line built from the vision model's JSON fields, in
    the order that reads naturally to an image model. The fields are kept
    short and concrete — "oval face, thick brows" beats a paragraph, and it
    leaves room in the prompt budget for the style itself.
    """
    raw = _chat_with_image(IDENTITY_PROMPT, image_path, max_tokens=600)
    fields = _parse_json(raw)
    if not fields:
        # The model returned prose instead of JSON. Use it as-is rather than
        # losing the description entirely.
        return " ".join(raw.split())
    return identity_to_text(fields)


# The order the fields are read in, and the label each gets. This is the
# order a poster illustrator would list them.
IDENTITY_FIELD_ORDER = [
    ("age", "age"),
    ("gender", "gender"),
    ("face_shape", "face shape"),
    ("jawline", "jawline"),
    ("eyes", "eyes"),
    ("brows", "brows"),
    ("nose", "nose"),
    ("mouth", "mouth"),
    ("facial_hair", "facial hair"),
    ("skin", "skin"),
    ("marks", "marks"),
    ("hair", "hair"),
    ("hairline", "hairline"),
    ("clothing", "clothing"),
    ("head_angle", "head angle"),
    ("gaze", "gaze"),
    ("expression", "expression"),
]


def _parse_json(raw: str) -> dict:
    """Pull a JSON object out of a model response, tolerating fences."""
    if not raw:
        return {}
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        obj = json.loads(text[start:end + 1])
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def identity_to_text(fields: dict) -> str:
    """Turn the JSON fields into one compact, readable line."""
    parts = []
    for key, label in IDENTITY_FIELD_ORDER:
        val = fields.get(key)
        if val is None:
            continue
        val = " ".join(str(val).split()).rstrip(".,;")
        if not val or val.lower() in ("none", "n/a", "unknown"):
            continue
        parts.append(f"{label} {val}")
    if not parts:
        return ""
    return "; ".join(parts) + "."


def describe_scene(image_path) -> str:
    """A factual description of the whole image."""
    return _chat_with_image(SCENE_PROMPT, image_path)


def classify_style(image_path) -> str:
    """'PRINT' or 'PHOTO' — whether the image reads as a flat limited-ink print."""
    answer = _chat_with_image(STYLE_QUESTION, image_path, max_tokens=10).strip().upper()
    return "PRINT" if answer.startswith("PRINT") else "PHOTO"


def classify_many(paths) -> list:
    out = []
    for p in paths:
        try:
            out.append({"path": str(p), "verdict": classify_style(p)})
        except Exception as e:  # noqa: BLE001
            out.append({"path": str(p), "verdict": "ERROR", "error": str(e)})
    return out


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="PosterLoom vision helpers.")
    ap.add_argument("image")
    ap.add_argument("mode", choices=["identity", "scene", "classify"])
    args = ap.parse_args()

    if args.mode == "identity":
        print(describe_identity(args.image))
    elif args.mode == "scene":
        print(describe_scene(args.image))
    else:
        print(classify_style(args.image))
