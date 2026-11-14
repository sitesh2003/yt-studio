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


def _arith(expr):
    """Value of a plain arithmetic expression (digits, + - x / ^ and brackets), or None if it is not one."""
    e = expr.replace("−", "-").replace("×", "*").replace("÷", "/").replace("x", "*").replace("^", "**")
    e = e.replace(",", "").strip()
    if not e or not re.fullmatch(r"[\d\s.+\-*/()]+", e):
        return None
    try:
        return float(eval(e, {"__builtins__": {}}, {}))   # only digits and operators reach here
    except Exception:
        return None


def _equation_ok(spec, narration):
    """Every '='-joined part that is plain arithmetic must have the same value, and every number shown
    must be one the narration says (or the computed result). Symbolic lines pass only on the numbers rule."""
    text = " ".join(str(l) for l in spec.get("lines", []))
    if not spec.get("lines"):
        return False
    parts = [p for p in re.split(r"=", text) if p.strip()]
    vals = [v for v in (_arith(p) for p in parts) if v is not None]
    if vals and any(abs(v - vals[0]) > 1e-9 for v in vals):
        return False
    said = _numbers_in(narration) | set(vals) | {abs(v) for v in vals}
    shown = {float(n) for n in re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))}
    return shown <= said


def _numberline_ok(spec, narration):
    try:
        start, jumps = float(spec.get("start", 0)), [float(j) for j in spec.get("jumps", [])]
        lo, hi = float(spec["lo"]), float(spec["hi"])
    except (KeyError, TypeError, ValueError):
        return False
    path = [start]
    for j in jumps:
        path.append(path[-1] + j)
    if not jumps or min(path) < lo or max(path) > hi or hi - lo > 40:
        return False
    said = _numbers_in(narration)
    need = {abs(start)} | {abs(j) for j in jumps} | {abs(path[-1])}
    return {n for n in need if n} <= said | {0.0}


def _graph_ok(spec, narration):
    """Only a safe formula in x (digits, operators, sin/cos/exp/log/sqrt/pi) over a finite range, and it
    must evaluate to real numbers across most of that range. Constants in it must be said aloud."""
    import math
    expr = str(spec.get("expr", ""))
    if not expr or not re.fullmatch(r"[\dx\s.+\-*/()]*((sin|cos|exp|log|sqrt|pi)[\dx\s.+\-*/()]*)*", expr):
        return False
    try:
        x0, x1 = float(spec.get("x0", 0)), float(spec.get("x1", 10))
    except (TypeError, ValueError):
        return False
    if not x1 > x0:
        return False
    env = {"sin": math.sin, "cos": math.cos, "exp": math.exp, "log": math.log, "sqrt": math.sqrt, "pi": math.pi}
    good = 0
    for k in range(21):
        try:
            v = eval(expr, {"__builtins__": {}}, {**env, "x": x0 + (x1 - x0) * k / 20})
            good += isinstance(v, (int, float)) and math.isfinite(v)
        except Exception:
            pass
    consts = {float(n) for n in re.findall(r"\d+(?:\.\d+)?", expr)} - {0.0, 1.0, 2.0}
    return good >= 17 and consts <= _numbers_in(narration)


def _circuit_ok(spec, narration):
    """A circuit is drawn only when the line is about a circuit, with known parts and a stated flow."""
    n = narration.lower()
    parts = [str(p).lower() for p in spec.get("parts", [])
             if not any(k in str(p).lower() for k in ("battery", "cell", "wire", "switch"))]   # always drawn
    known = all(any(k in p for k in ("resist", "bulb", "lamp", "led", "diode")) for p in parts)
    about = any(w in n for w in ("circuit", "current", "battery", "bulb", "resistor", "led", "diode", "electron"))
    return bool(parts) and len(parts) <= 2 and known and about and         str(spec.get("flow", "conventional")).lower().startswith(("conventional", "electron"))


def _pubchem(name):
    """(atoms, bonds) from PubChem's 3D record for a compound name, or None. Small molecules only."""
    import requests
    r = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{requests.utils.quote(name)}/SDF",
                     params={"record_type": "3d"}, timeout=20)
    if not r.ok:
        return None
    lines = r.text.splitlines()
    try:
        na, nb = int(lines[3][:3]), int(lines[3][3:6])
    except (IndexError, ValueError):
        return None
    if not 2 <= na <= 30:
        return None
    atoms = [[l[31:34].strip(), float(l[0:10]), float(l[10:20]), float(l[20:30])] for l in lines[4:4 + na]]
    bonds = [[int(l[0:3]), int(l[3:6]), int(l[6:9])] for l in lines[4 + na:4 + na + nb]]
    return atoms, bonds


def _molecule_ok(spec, narration):
    """The named compound must be in the line, and PubChem must have a small 3D structure for it;
    the real coordinates are put into the spec (the model never supplies geometry)."""
    name = str(spec.get("name", "")).strip()
    if not name or name.lower() not in narration.lower():
        return False
    try:
        got = _pubchem(name)
    except Exception:
        got = None
    if not got:
        return False
    spec["atoms"], spec["bonds"] = got
    return True


def _numbers_ok(spec, narration):
    if spec.get("type") == "Molecule":
        return _molecule_ok(spec, narration)
    if spec.get("type") == "Circuit":
        return _circuit_ok(spec, narration)
    if spec.get("type") == "Graph":
        return _graph_ok(spec, narration)
    if spec.get("type") == "Equation":
        return _equation_ok(spec, narration)
    if spec.get("type") == "NumberLine":
        return _numberline_ok(spec, narration)
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
- "Equation": the line works through a calculation or formula (e.g. "negative three times negative four
  is twelve" -> lines ["(-3) × (-4)", "= 12"]); 2-5 short lines, the last one the result. Use × for times.
- "Graph": the line describes how one quantity changes with another by a known rule (doubling, an
  inverse square, a wave): "expr" in x using + - * / ** sin cos exp log sqrt pi, with x0..x1 and short
  axis labels. Only when the rule is exactly what the line says.
- "Circuit": the line is about current in a simple loop with a battery and 1-2 parts (resistor, bulb,
  LED); "parts" and "flow" ("conventional" if the line talks about current, "electrons" if it talks
  about electrons moving).
- "Molecule": the line names one small molecule whose SHAPE matters (water, carbon dioxide, methane,
  ammonia, ethanol, glucose); give only "name" as written in the line - its real 3D structure is
  fetched from PubChem.
- "NumberLine": the line moves along numbers (adding, subtracting, negatives): start, jumps, and a
  lo..hi range that contains every landing point (span at most 40).
Use ONLY numbers and words that appear in that scene's narration; never compute or add anything.
Short labels (max 4 words). Never choose the first scene (the hook needs real footage) or a scene
with no number or process. Choosing none is fine.
Scenes: {[{"i": i, "narration": s.get("narration")} for i, s in enumerate(scenes)]}
Return JSON: {{"picks": [{{"i": scene index, "type": "Compare|Counter|Grid|Steps", "title": "max 6 words",
 "a_label": "", "a_value": number, "b_label": "", "b_value": number, "unit": "",
 "value": number, "decimals": 0, "caption": "max 6 words", "k": number, "n": number,
 "steps": ["..."], "lines": ["..."], "start": number, "jumps": [number], "lo": number, "hi": number,
 "expr": "", "x0": number, "x1": number, "x_label": "", "y_label": "",
 "parts": ["..."], "flow": "conventional or electrons", "name": ""}}]}}""")
    used = 0
    for p in out.get("picks") or []:
        try:
            i = int(p.get("i"))
        except (TypeError, ValueError):
            continue
        if not 0 < i < len(scenes) or used >= _max() or p.get("type") not in ("Compare", "Counter", "Grid", "Steps", "Equation", "NumberLine", "Graph", "Circuit", "Molecule"):
            continue
        if p["type"] != "Steps" and not _numbers_ok(p, scenes[i].get("narration", "")):
            log(f"animate: scene {i + 1} skipped, its {p.get('type')} failed the accuracy check (numbers, range or subject)")
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
