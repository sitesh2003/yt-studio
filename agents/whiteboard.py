"""Agent 4d - The drawing board: the explanation is DRAWN, continuously, as the narrator speaks.

16 Nov 2026, owner: "instead of broken AI pics ... stick drawing figures, or drawing continuously, handled
properly as a narrative", with real footage still used where it helps. So the scenes that EXPLAIN (the
middle of the video) become one continuous board: each scene's drawing is drawn on screen (outline, then
colour, then labels) while it is being said, the camera glides down to the next drawing, and the earlier
drawings stay on the board. People are stick figures; objects are simple, recognisable line drawings; the
same objects come back in the same colours so the drawings connect. The hook and the real-life scene keep
real footage.

Every drawing is checked (agents/diagram._check: recognisable, accurate, readable) before it is used; a
drawing that fails is dropped and that scene falls back to footage. Rendered by Manim (agents/board_scene.py).
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .core import config, llm_json, log, run

SCENE = Path(__file__).with_name("board_scene.py")

STYLE = """Each drawing is one SVG: <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920" width="1080" height="1920">
with <rect width="1080" height="1920" fill="#0b1630"/> first (the dark board). Draw ONLY in the band y=290..1060.
It is a teacher's drawing on a dark board, drawn live while the narrator talks:
- LINE DRAWINGS with thick strokes (10-14px, stroke-linecap="round", stroke-linejoin="round"), simple
  flat fills; colours only #ffffff (chalk white), #ffd60a (yellow), #2ec4b6 (teal), #ff6b6b (coral), #8ecae6.
- PEOPLE ARE STICK FIGURES: a circle head (r 45-60) and straight lines for body, arms and legs; a simple
  pose that shows the action (holding, pointing, tasting). No faces beyond two dots and a curve, if any.
- OBJECTS are simple and recognisable (a pan, a glass, a drop, a molecule as a ball with a tail, a tree).
  Never abstract symbols, never bare dots standing for things. Large: fill most of the band.
- Arrows where something moves or changes (a line plus a small filled triangle head).
- Put the elements in the ORDER a teacher draws them: the main object first, then details, then arrows.
- At most 2 labels, 1-3 words each, <text> with font-family="Archivo Black", font-size 52-64, white or
  yellow, never overlapping a shape. No titles, no paragraphs, nothing photo-realistic.
- Only <path>, <circle>, <ellipse>, <rect>, <line>, <polyline>, <polygon>, <g>, <text>. No gradients,
  filters, images, masks, clip paths or CSS."""


def _render_png(svg):
    from .diagram import _render
    return _render(svg)


def _fix(svg):
    for ent, ch in (("&deg;", "°"), ("&nbsp;", " "), ("&rarr;", "→"), ("&times;", "×"), ("&minus;", "−")):
        svg = svg.replace(ent, ch)   # HTML names an SVG renderer does not know
    return svg


def _look(topic, example, lines):
    """One shared look for the whole board: each recurring object, how it is drawn and its colour."""
    out = llm_json(f"""A science Short about {topic} is explained with simple drawings on a dark board, one per scene:
{lines}
The running example: {example or 'the topic itself'}
List the objects that recur across the drawings (at most 6) and fix how each is ALWAYS drawn, so every drawing
matches: shape in a few words and one colour from #ffffff #ffd60a #2ec4b6 #ff6b6b #8ecae6. People are stick figures.
Return JSON: {{"objects": [{{"name": "...", "drawn_as": "...", "colour": "#..."}}]}}""")
    return "; ".join(f"{o.get('name')}: {o.get('drawn_as')}, {o.get('colour')}" for o in (out.get("objects") or [])[:6])


def _draw_one(k, scenes, topic, look, lines):
    """One scene's drawing, checked; up to 2 tries (the free AI quota is shared by three channels). Returns svg or None."""
    from .diagram import _check
    said, note = scenes[k].get("narration", ""), ""
    for attempt in range(2):
        try:
            out = llm_json(f"""You draw, live on a board, ONE step of the explanation in a science YouTube Short about: {topic}
The whole lesson, scene by scene (for context): 
{lines}
Draw ONLY scene {k}: "{said}"
Keep the board's look - every recurring object is always drawn like this: {look or 'simple, consistent shapes'}
It must be scientifically ACCURATE for exactly that sentence, and make sense at a glance without the voice.
{STYLE}
{("The previous drawing was rejected because: " + note + " Fix that.") if note else ""}
Return JSON: {{"svg": "<svg ...>...</svg>"}}""")
            svg = _fix(str(out.get("svg") or ""))
            if not svg.startswith("<svg"):
                note = "it must be one complete <svg> element"
                continue
            verdict = _check(_render_png(svg), said)
            if verdict.get("accurate") and float(verdict.get("score", 0) or 0) >= 6:
                return svg
            note = verdict.get("problems") or f"score {verdict.get('score')}"
        except Exception as e:
            note = str(e)[:120]
    log(f"whiteboard: scene {k + 1} not drawn ({note[:80]})")
    return None


def plan(script, topic):
    """{scene_index: svg} for the explaining scenes, each drawing checked; {} if fewer than 2 pass.
    One shared look first, then each scene drawn on its own (focused requests draw better than one
    request for every drawing at once: 2 of 5 passed that way on the first test, 16 Nov 2026)."""
    from concurrent.futures import ThreadPoolExecutor
    scenes = script.get("scenes", [])
    middle = [k for k in range(1, len(scenes) - 1) if not scenes[k].get("anim")][:4]   # at most 4 drawn scenes
    if len(middle) < 2:
        return {}
    example = (script.get("running_example") or "").strip()
    lines = chr(10).join(f"{k}: {scenes[k].get('narration', '')}" for k in middle)
    try:
        look = _look(topic, example, lines)
    except Exception:
        look = ""
    with ThreadPoolExecutor(max_workers=3) as pool:
        svgs = list(pool.map(lambda k: _draw_one(k, scenes, topic, look, lines), middle))
    good = {k: v for k, v in zip(middle, svgs) if v}
    if len(good) < 2:
        return {}
    log(f"whiteboard: {len(good)}/{len(middle)} checked drawings for scenes {[k + 1 for k in sorted(good)]}")
    return good


def render(drawings, times, job_dir):
    """Draw the board once, continuously, and cut it into one clip per drawn scene.
    Returns {scene_index: mp4 path}."""
    job_dir = Path(job_dir)
    work = job_dir / "board_draw"
    work.mkdir(exist_ok=True)
    order = sorted(drawings)
    panels = []
    for n, k in enumerate(order):
        p = work / f"panel_{k:02d}.svg"
        p.write_text(drawings[k], encoding="utf-8")
        a, b = times[k]
        # exact scene lengths, so back-to-back drawn scenes join frame to frame (the editor cuts each clip to
        # b - a); the last one gets half a second spare
        panels.append({"svg": str(p).replace("\\", "/"), "seconds": round(b - a + (0.5 if n == len(order) - 1 else 0), 3)})
    f = config()["format"]
    params = work / "params.json"
    params.write_text(json.dumps({"width": f["width"], "height": f["height"], "panels": panels}), encoding="utf-8")
    media = work / "media"
    r = subprocess.run([sys.executable, "-m", "manim", "render", "-qh", "--format", "mp4", "--media_dir", str(media), "-o", "board",
                        str(SCENE), "Board"], env={**os.environ, "ANIM_PARAMS": str(params)}, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=900)
    found = next(media.rglob("board.mp4"), None)
    if r.returncode != 0 or not found:
        raise RuntimeError((r.stderr or r.stdout)[-300:])
    clips, t = {}, 0.0
    for k, p in zip(order, panels):
        out = job_dir / f"draw_{k:02d}.mp4"
        run(["ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", str(found), "-t", f"{p['seconds']:.3f}", "-an",
             "-vf", f"fps={f['fps']}", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])
        clips[k] = out
        t += p["seconds"]
    shutil.rmtree(media, ignore_errors=True)
    return clips


def make(script, times, job_dir, topic=""):
    """The whole drawing board for a video: {scene_index: clip}, or {} (the video then uses footage)."""
    try:
        drawings = plan(script, topic or script.get("topic", ""))
        return render(drawings, times, job_dir) if drawings else {}
    except Exception as e:
        log(f"whiteboard: no drawing board ({str(e)[:100]})")
        return {}
