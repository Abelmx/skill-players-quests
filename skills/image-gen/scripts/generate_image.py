#!/usr/bin/env python3
"""Generate images via an OpenAI-compatible chat/completions endpoint.

The endpoint is expected to return generated images as base64 data URIs
embedded in the assistant message content (the pattern used by nanobanana /
Gemini image generation proxies).

Required env vars:
  IMAGE_GEN_API_KEY   — Bearer token
  IMAGE_GEN_BASE_URL  — Service base URL (e.g. https://api.example.com)
Optional:
  IMAGE_GEN_MODEL     — Model ID (default: gemini-2.0-flash-exp-image-generation)
  IMAGE_GEN_TIMEOUT   — Request timeout in seconds (default: 120)
"""

from __future__ import annotations

import argparse
import base64
import io
import os
import re
import subprocess
import sys
from typing import Any


def _ensure_deps() -> None:
    for pkg in ("httpx", "PIL"):
        try:
            __import__(pkg)
        except ImportError:
            pip_name = "Pillow" if pkg == "PIL" else pkg
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-q", pip_name],
                stdout=subprocess.DEVNULL,
            )


_DATA_URI_RE = re.compile(r"(data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\n\r]+)")


def _extract_data_uri(obj: Any) -> str | None:
    """Recursively search a JSON-like object for a data:image/… URI."""
    if obj is None:
        return None
    if isinstance(obj, str):
        m = _DATA_URI_RE.search(obj)
        return m.group(1) if m else None
    if isinstance(obj, list):
        for item in obj:
            found = _extract_data_uri(item)
            if found:
                return found
        return None
    if isinstance(obj, dict):
        for key in ("url", "image_url"):
            val = obj.get(key)
            if isinstance(val, str) and val.startswith("data:image/"):
                return val
            if isinstance(val, dict):
                inner = val.get("url", "")
                if isinstance(inner, str) and inner.startswith("data:image/"):
                    return inner
        for v in obj.values():
            found = _extract_data_uri(v)
            if found:
                return found
        return None
    return None


def _decode_and_save_png(data_uri: str, output_path: str) -> None:
    from pathlib import Path

    from PIL import Image

    _, b64_part = data_uri.split(",", 1)
    raw = base64.b64decode(b64_part)
    img = Image.open(io.BytesIO(raw)).convert("RGBA")

    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p, format="PNG")


def generate(prompt: str, output: str) -> None:
    import httpx

    api_key = os.environ.get("IMAGE_GEN_API_KEY", "").strip()
    base_url = os.environ.get("IMAGE_GEN_BASE_URL", "").strip()
    model = os.environ.get("IMAGE_GEN_MODEL", "").strip() or "gemini-2.0-flash-exp-image-generation"
    timeout = float(os.environ.get("IMAGE_GEN_TIMEOUT", "120").strip() or "120")

    if not api_key:
        raise RuntimeError("IMAGE_GEN_API_KEY is not set")
    if not base_url:
        raise RuntimeError("IMAGE_GEN_BASE_URL is not set")

    endpoint = base_url.rstrip("/")
    if not endpoint.endswith("/v1"):
        endpoint += "/v1"
    endpoint += "/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt},
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    content = (data.get("choices") or [{}])[0].get("message", {}).get("content")
    data_uri = _extract_data_uri(content)
    if not data_uri:
        data_uri = _extract_data_uri(data)
    if not data_uri:
        raise RuntimeError(
            f"No image data URI in response. Preview: {str(data)[:500]}"
        )

    _decode_and_save_png(data_uri, output)
    print(f"Image saved to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate images via OpenAI-compatible API")
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument("--output", default="output.png", help="Output file path (default: output.png)")
    args = parser.parse_args()

    _ensure_deps()
    generate(args.prompt, args.output)


if __name__ == "__main__":
    main()
