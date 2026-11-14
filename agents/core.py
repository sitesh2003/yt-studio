"""Shared helpers: config, folders, the LLM call, and a tiny logger."""
import json
import os
import re
import subprocess
import sys
import time

for _s in (sys.stdout, sys.stderr):  # Windows consoles choke on emoji in video titles
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

JOBS = ROOT / "jobs"
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
for d in (JOBS, DATA, ASSETS / "music"):
    d.mkdir(parents=True, exist_ok=True)


_OVERRIDE = {}


def set_override(sections):
    """Temporarily change config sections (the weekly long video uses widescreen + smaller captions)."""
    _OVERRIDE.clear()
    _OVERRIDE.update(sections or {})


def config():
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    for k, v in _OVERRIDE.items():
        cfg[k] = {**cfg.get(k, {}), **v}
    if os.getenv("PUBLISH_MODE"):  # the cloud run sets auto: upload private + scheduled, you review in the app
        cfg["publish"]["mode"] = os.getenv("PUBLISH_MODE")
    return cfg


def log(msg):
    print(time.strftime("[%H:%M:%S] ") + msg, flush=True)


def key(name):
    v = os.getenv(name, "").strip()
    return v or None


def slug(text, n=40):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:n] or "video"


def read_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def run(cmd, cwd=None):
    """Run a command, raise with its stderr tail if it fails."""
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed:\n{r.stderr[-1500:]}")
    return r.stdout


def _contents(prompt, images):
    """Text, or text plus JPEG images (the visuals agent looks at candidate clips)."""
    if not images:
        return prompt
    from google.genai import types
    return [types.Part.from_bytes(data=b, mime_type="image/jpeg") for b in images] + [prompt]


class _ListResult(dict):
    """The model sometimes answers with a bare list where we asked for {"key": [...]}.
    Any .get("topics" / "items" / "claims" ...) on it returns that list instead of crashing."""
    def __init__(self, items):
        super().__init__()
        self.items_list = items

    def get(self, k, default=None):
        return self.items_list if k not in ("verdict", "best", "pass", "why") else default

    def __getitem__(self, k):   # x["claims"] must behave like x.get("claims"), not KeyError
        v = self.get(k)
        if v is None:
            raise KeyError(k)
        return v


def _shape(out):
    if isinstance(out, list):
        if len(out) == 1 and isinstance(out[0], dict):
            return out[0]
        return _ListResult(out)
    return out if isinstance(out, dict) else {}


def llm_json(prompt, retries=3, images=None):
    """Ask the configured LLM for JSON. Gemini free tier by default."""
    cfg = config()["llm"]
    api_key = key("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing in .env (free at aistudio.google.com/apikey)")
    from google import genai
    client = genai.Client(api_key=api_key, http_options={"timeout": 90000})
    last = None
    models = [cfg["model"]] + cfg.get("fallback_models", [])
    dead = set()
    for round_ in range(4):                      # free models get busy; go round the list a few times
        for model in models:
            if model in dead:
                continue
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=_contents(prompt, images),
                    config={"response_mime_type": "application/json",
                            "temperature": 0.2 if images else 0.9},
                )
                return _shape(json.loads(resp.text))
            except Exception as e:
                last, msg = e, str(e)
                if "404" in msg or "NOT_FOUND" in msg:
                    dead.add(model)               # retired: never try it again this run
                elif "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    time.sleep(10)                # per-minute free quota: short pause, next model
        time.sleep(20 * (round_ + 1))             # everything busy: wait, then try the list again
    raise RuntimeError(f"LLM call failed on every model: {last}")


def add_lesson(kind, text):
    """Every fault the system catches becomes a lesson the writer reads next time (data/lessons.json)."""
    path = DATA / "lessons.json"
    les = read_json(path, []) or []
    if text and all(l.get("text") != text for l in les):
        les.append({"kind": kind, "text": text[:300]})
        write_json(path, les[-40:])
