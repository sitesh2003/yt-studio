"""Agent 4e - Code-drawn animation (Manim) for lines that state a number, a comparison or a process.

The planner picks at most 2 scenes per video whose line is best shown as a computed picture, and fills
ONE template (Compare / Counter / Grid / Steps in manim_templates.py) with values taken from that line.
Accuracy rule, enforced in code: every number drawn must appear in the scene's own narration (after the
fact check), so an animation can never show a number the script did not say. Manim renders on GitHub
in seconds (measured 14 Nov 2026: 6 s for 10 s of 1080x1920 video).
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from .core import config, llm_json, log

TEMPLATES = Path(__file__).with_name("manim_templates.py")
MAX_PER_VIDEO = 2   # the main channel; a channel can raise it ("animate": {"max_per_video": n})


def _max():
    from .core import config
    return int((config().get("animate") or {}).get("max_per_video", MAX_PER_VIDEO))


def available():
    return bool(shutil.which("manim"))


_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
          "ten": 10, "eleven": 11, "twelve": 12, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
          "hundred": 100, "thousand": 1000, "million": 1_000_000, "billion": 1_000_000_000, "half": 0.5}


def _numbers_in(text):
    t = text.lower().replace(",", "")
    nums = {float(x) for x in re.findall(r"\d+(?:\.\d+)?", t)}
    nums |= {float(v) for w, v in _WORDS.items() if re.search(rf"\b{w}\b", t)}
    for a, b in re.findall(r"(\d+(?:\.\d+)?)\s*(thousand|million|billion)", t):
        nums.add(float(a) * _WORDS[b])
    return nums


def _numbers_ok(spec, narration):
    said = _numbers_in(narration)
    keys = {"Compare": ("a_value", "b_value"), "Counter": ("value",), "Grid": ("k", "n")}.get(spec.get("type"), ())
    for k in keys:
        try:
            v = float(spec[k])
        except (KeyError, TypeError, ValueError):
            return False
        if v not in said:
            return False
    return True


def plan(script):
    """Mark up to 2 scenes with scene["anim"] = template spec (only lines that state a number, a
    comparison or a short process)."""
    scenes = script.get("scenes") or []
    out = llm_json(f"""A science video's scenes are below. Choose AT MOST {_max()} scenes whose line is best shown as
a simple computed graphic, and only if the line itself states the thing exactly:
- "Compare": the line compares two quantities with numbers (e.g. "40 gallons of sap make 1 gallon of syrup").
- "Counter": the line states one striking number (e.g. "about 4 to 6 milligrams").
- "Grid": the line states a proportion "k in n" with n <= 100 (e.g. "1 in 10 people").
- "Steps": the line describes a short process of 2-4 steps.
Use ONLY numbers and words that appear in that scene's narration; never compute or add anything.
Short labels (max 4 words). Never choose the first scene (the hook needs real footage) or a scene
with no number or process. Choosing none is fine.
Scenes: {[{"i": i, "narration": s.get("narration")} for i, s in enumerate(scenes)]}
Return JSON: {{"picks": [{{"i": scene index, "type": "Compare|Counter|Grid|Steps", "title": "max 6 words",
 "a_label": "", "a_value": number, "b_label": "", "b_value": number, "unit": "",
 "value": number, "decimals": 0, "caption": "max 6 words", "k": number, "n": number,
 "steps": ["..."]}}]}}""")
    used = 0
    for p in out.get("picks") or []:
        try:
            i = int(p.get("i"))
        except (TypeError, ValueError):
            continue
        if not 0 < i < len(scenes) or used >= _max() or p.get("type") not in ("Compare", "Counter", "Grid", "Steps"):
            continue
        if p["type"] != "Steps" and not _numbers_ok(p, scenes[i].get("narration", "")):
            log(f"animate: scene {i + 1} skipped, a number is not in its narration ({p.get('type')})")
            continue
        if p["type"] == "Steps" and not (2 <= len(p.get("steps") or []) <= 4):
            continue
        scenes[i]["anim"] = {k: v for k, v in p.items() if k != "i"}
        used += 1
        log(f"animate: scene {i + 1} will be a {p['type']} animation")
    return used


def render(spec, out_mp4, seconds, workdir):
    f = config()["format"]
    cap = config()["captions"]
    params = {**spec, "seconds": round(seconds, 2), "width": f["width"], "height": f["height"],
              "cap_y": cap["position_y"], "cap_h": cap["size"] * 2.4}   # two caption lines: kept empty
    pfile = Path(workdir) / f"anim_{out_mp4.stem}.json"
    pfile.write_text(json.dumps(params), encoding="utf-8")
    media = Path(workdir) / "manim_media"
    env = {**os.environ, "ANIM_PARAMS": str(pfile)}
    r = subprocess.run(["manim", "render", "-qh", "--format", "mp4", "--media_dir", str(media), "-o", out_mp4.stem,
                        str(TEMPLATES), spec["type"]], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    found = next(media.rglob(f"{out_mp4.stem}.mp4"), None)
    if r.returncode != 0 or not found:
        raise RuntimeError((r.stderr or r.stdout)[-300:])
    shutil.move(str(found), out_mp4)
    return True
