"""LLM 封装 —— 艺术总监(文本)与美学评论官(视觉)共用。

走 OpenAI 兼容端点，按环境变量自动选 provider：
 - DASHSCOPE_API_KEY → 阿里 Qwen（文本 qwen-plus，视觉 qwen-vl-max）
 - OPENAI_API_KEY    → OpenAI（文本/视觉 gpt-4o）

所有调用都可在无 key 时优雅降级：`available()` 为假时，上层走确定性兜底。"""
from __future__ import annotations
import os
import json
import base64
from functools import lru_cache


@lru_cache(maxsize=1)
def _provider() -> dict | None:
    if os.environ.get("DASHSCOPE_API_KEY"):
        return {"name": "dashscope", "key": os.environ["DASHSCOPE_API_KEY"],
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "text_model": "qwen-plus", "vision_model": "qwen-vl-max"}
    if os.environ.get("OPENAI_API_KEY"):
        return {"name": "openai", "key": os.environ["OPENAI_API_KEY"],
                "base_url": None, "text_model": "gpt-4o", "vision_model": "gpt-4o"}
    return None


def available() -> bool:
    return _provider() is not None


@lru_cache(maxsize=1)
def _client():
    p = _provider()
    if not p:
        return None
    from openai import OpenAI
    return OpenAI(api_key=p["key"], base_url=p["base_url"])


def chat(system: str, user: str, *, as_json: bool = False, model: str | None = None,
         temperature: float = 0.7, max_tokens: int = 4096) -> str:
    """单轮对话，返回文本。as_json=True 时要求模型输出 JSON 并尽力解析容错。"""
    cli, p = _client(), _provider()
    if not cli:
        raise RuntimeError("no LLM provider configured")
    kwargs = dict(
        model=model or p["text_model"],
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=temperature, max_tokens=max_tokens,
    )
    if as_json:
        kwargs["response_format"] = {"type": "json_object"}
    resp = cli.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def chat_json(system: str, user: str, **kw) -> dict:
    """要 JSON，返回 dict。容错：剥离 ```json 围栏、截取首个 {..}。"""
    raw = chat(system, user, as_json=True, **kw)
    return _loads(raw)


def vision(prompt: str, image_path: str, *, as_json: bool = False,
           model: str | None = None, max_tokens: int = 1500) -> str | dict:
    """读一张图 + 提示词。用于美学评论官。"""
    cli, p = _client(), _provider()
    if not cli:
        raise RuntimeError("no LLM provider configured")
    b64 = base64.b64encode(open(image_path, "rb").read()).decode()
    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
    ]
    kwargs = dict(model=model or p["vision_model"],
                  messages=[{"role": "user", "content": content}],
                  max_tokens=max_tokens)
    if as_json and p["name"] == "openai":
        kwargs["response_format"] = {"type": "json_object"}
    raw = cli.chat.completions.create(**kwargs).choices[0].message.content or ""
    return _loads(raw) if as_json else raw


def _loads(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except Exception:
        i, j = raw.find("{"), raw.rfind("}")
        if i >= 0 and j > i:
            return json.loads(raw[i:j + 1])
        raise
