"""Text-to-image for hero pages — qwen-image-2.0 via DashScope (sync endpoint).

Contract: the caller (LLM planner / demo) describes only the CONTENT of the
picture (topic-specific motif); the *look* enforces the style twice —
  1. its art.STYLE_SUFFIX is appended to every prompt (passed in by build.py);
  2. its hero_from_source() post-pass re-inks the result into the deck's exact
     palette, so colour discipline never depends on the model.

Returns None on missing key / API failure so build.py can fall back to the
look's procedural hero_generate() — the pipeline stays fully usable offline."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from urllib import request

ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MODEL = os.environ.get("PPT_IMAGE_MODEL", "qwen-image-2.0")


def _open(req, timeout):
    # DashScope / aliyun OSS are direct-reachable; bypass any env proxies
    opener = request.build_opener(request.ProxyHandler({}))
    return opener.open(req, timeout=timeout)


def generate(prompt: str, out_path: str, style_suffix: str = "",
             size: str = "1664*928", timeout: int = 150) -> str | None:
    """Generate a hero source image from a content prompt. None on any failure."""
    key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not key or not prompt:
        return None
    text = f"{prompt}. {style_suffix}" if style_suffix else prompt
    body = {
        "model": MODEL,
        "input": {"messages": [{"role": "user",
                                "content": [{"text": text}]}]},
        "parameters": {"size": size, "n": 1},
    }
    req = request.Request(
        ENDPOINT, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with _open(req, timeout) as r:
            data = json.load(r)
        url = data["output"]["choices"][0]["message"]["content"][0]["image"]
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with _open(request.Request(url), timeout) as r, open(out_path, "wb") as f:
            f.write(r.read())
        return out_path
    except Exception as e:  # noqa: BLE001 — any failure degrades to procedural art
        print(f"[genimage] degraded to procedural art: {e}", file=sys.stderr)
        return None
