"""Free AI providers after Gemini (owner, 19 Nov 2026: no paid AI; "keep it very open").

Every provider here speaks the same OpenAI-style chat API, so one caller serves all of them. A provider
switches on by itself when its key exists as a GitHub secret; a new one is one line in PROVIDERS.
Model lists are read live from each provider (free models come and go), so a retired model never
breaks a run. Order: Groq (fast, about 1,000 requests a day), OpenRouter's ":free" models (DeepSeek,
Qwen, Llama; about 50 a day), Mistral (if a key is ever added).
"""
import base64
import json
import re
import time

import requests

from .core import key, log

PROVIDERS = [
    # name, key name, base URL, preferred text models (first one present wins), vision models
    ("groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1",
     ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "qwen/qwen3-32b"],
     ["meta-llama/llama-4-scout-17b-16e-instruct", "meta-llama/llama-4-maverick-17b-128e-instruct"]),
    ("openrouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1",
     ["deepseek", "qwen3", "llama-3.3-70b", "gpt-oss", "gemma"],      # matched against live ":free" ids
     ["qwen2.5-vl", "qwen3-vl", "llama-4", "gemma-3"]),
    ("mistral", "MISTRAL_API_KEY", "https://api.mistral.ai/v1",
     ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest"],
     ["pixtral-large-latest", "mistral-medium-latest"]),
]

_LIVE = {}      # provider -> list of model ids it offers right now
_DEAD = set()   # (provider, model) that failed for good this run


def available():
    return [p for p in PROVIDERS if key(p[1])]


def _live_models(name, k, base):
    if name not in _LIVE:
        try:
            r = requests.get(f"{base}/models", headers={"Authorization": f"Bearer {k}"}, timeout=20)
            ids = [m.get("id", "") for m in (r.json().get("data") or [])]
            if name == "openrouter":
                ids = [i for i in ids if i.endswith(":free")]     # never a paid model
            _LIVE[name] = ids
        except Exception as e:
            log(f"free_llm: {name} model list failed ({type(e).__name__})")
            _LIVE[name] = []
    return _LIVE[name]


def _pick(name, live, wanted):
    """Models to try, best first: exact ids for Groq/Mistral, name fragments for OpenRouter."""
    if name == "openrouter":
        out = []
        for frag in wanted:
            out += [i for i in live if frag in i.lower() and i not in out]
        return out[:4]
    return [m for m in wanted if (not live or m in live)][:3]


def _json_from(text):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"(\{.*\}|\[.*\])", text, re.S)
        if m:
            return json.loads(m.group(1))
        raise


def ask_json(prompt, images=None, temperature=0.9):
    """JSON from the first free provider that answers, or None if none can."""
    content = prompt + "\n\nAnswer with valid JSON only."
    if images:
        content = [{"type": "text", "text": content}] + [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(b).decode()}}
            for b in images[:4]]
    for name, kname, base, text_models, vision_models in available():
        k = key(kname)
        models = _pick(name, _live_models(name, k, base), vision_models if images else text_models)
        for model in models:
            if (name, model) in _DEAD:
                continue
            body = {"model": model, "temperature": temperature,
                    "messages": [{"role": "user", "content": content}]}
            if name != "openrouter" and not images:
                body["response_format"] = {"type": "json_object"}
            try:
                r = requests.post(f"{base}/chat/completions", json=body, timeout=120,
                                  headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
                if r.status_code in (401, 403, 404):
                    _DEAD.add((name, model))
                    log(f"free_llm: {name}/{model} refused ({r.status_code}); skipped for this run")
                    continue
                if r.status_code == 429:
                    log(f"free_llm: {name}/{model} busy or out for today; next")
                    time.sleep(3)
                    continue
                r.raise_for_status()
                out = _json_from(r.json()["choices"][0]["message"]["content"])
                log(f"free_llm: answered by {name}/{model}")
                return out
            except Exception as e:
                log(f"free_llm: {name}/{model} failed ({type(e).__name__}: {str(e)[:80]})")
    return None
