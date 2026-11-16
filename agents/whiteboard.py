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
    """One shared look for the whole board: each recurring thing and the ONE emoji that always shows it."""
    out = llm_json(f"""A science Short about {topic} is explained on a board with pictures, one picture per scene:
{lines}
The running example: {example or 'the topic itself'}
List the things that recur across the scenes (at most 6) and pick ONE standard emoji whose picture shows each
(an animal, food, plant, body part, tool, weather...), so the same thing always looks the same.
Return JSON: {{"objects": [{{"name": "...", "emoji": "..."}}]}}""")
    return "; ".join(f"{o.get('name')} = {o.get('emoji')}" for o in (out.get("objects") or [])[:6])


# 16 Nov 2026: the free AI cannot DRAW animals and objects (a mouse came out as "a circle with two loops", a tick
# as "an oval with crossed lines"; 0 of 4 acorn drawings passed). So it no longer draws them: it LAYS OUT real,
# recognisable pictures (Twemoji, already credited on the board) as groups joined by arrows, and the board draws
# those pictures on live, outline then colour, exactly as before.
GROUPS = """Show the scene as 1-3 GROUPS from left to right; an arrow between two groups means "leads to" or
"turns into". Each group is:
  "emoji": 1-2 standard emoji whose PICTURES show the real things (or the closest thing of the SAME kind:
  a spider for a tick is fine, a tree for a tick is not) (never symbols like arrows, crosses, ticks,
  question marks or letters);
  "count": 1-6, how many of the first emoji to show (use 4-6 to show "many", "more", "multiply");
  "gone": true if that thing runs out, dies or disappears (it is drawn crossed out), else false;
  "label": 1-2 words, at most 12 letters, naming it (e.g. "MORE MICE").
Use the board's emoji for things that recur. The pictures must make the sentence clear at a glance."""


def _compose(groups):
    """The groups as one board SVG in the 1080x1920 frame (pictures in the band y=290..1060)."""
    import math
    from .diagram import _esc
    # a phone screen is tall: groups are stacked top to bottom (arrows pointing down), pictures on the left,
    # the label on the right; one group alone is centred, label underneath
    n = len(groups)
    rowh = 770 / n
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920" width="1080" height="1920">',
           '<rect width="1080" height="1920" fill="#0b1630"/>']
    labels = []
    for gi, g in enumerate(groups):
        cy = 290 + rowh * (gi + 0.5)
        cx, area_w, area_h = (540, 900, 520) if n == 1 else (360, 620, rowh - 80)
        pics = [g["icons"][0]] * g["count"] + list(g["icons"][1:])
        best = max(range(1, len(pics) + 1), key=lambda c: min(area_w / c, area_h / math.ceil(len(pics) / c)))
        cols, rows = best, math.ceil(len(pics) / best)
        size = min(320, area_w / cols, area_h / rows)
        x0, y0 = cx - cols * size / 2, cy - rows * size / 2
        for j, (inner, vb) in enumerate(pics):
            r, c = divmod(j, cols)
            w = float((vb.split() + ["36"] * 4)[2]) or 36
            out.append(f'<g transform="translate({x0 + c * size + size * 0.06:.1f} {y0 + r * size + size * 0.06:.1f}) '
                       f'scale({size * 0.88 / w:.4f})">{inner}</g>')
        if g.get("gone"):
            hw, hh = cols * size / 2, rows * size / 2
            out.append(f'<path d="M{cx - hw:.0f} {cy - hh:.0f} L{cx + hw:.0f} {cy + hh:.0f} M{cx + hw:.0f} {cy - hh:.0f} '
                       f'L{cx - hw:.0f} {cy + hh:.0f}" stroke="#ff6b6b" stroke-width="16" stroke-linecap="round" fill="none"/>')
        if gi + 1 < n:
            ay = 290 + rowh * (gi + 1)
            out.append(f'<path d="M{cx:.0f} {ay - 34:.0f} L{cx:.0f} {ay + 12:.0f}" stroke="#ffd60a" stroke-width="12" '
                       f'stroke-linecap="round" fill="none"/><path d="M{cx - 24:.0f} {ay + 4:.0f} L{cx:.0f} {ay + 36:.0f} '
                       f'L{cx + 24:.0f} {ay + 4:.0f} Z" fill="#ffd60a"/>')
        label = _esc(str(g.get("label") or "")[:12].upper())
        if label:
            colour = "#ffd60a" if gi == n - 1 else "#ffffff"
            if n == 1:
                fs = min(72, 900 / (0.72 * len(label)))
                lx, ly, anchor = 540, cy + rows * size / 2 + 40 + fs, "middle"
            else:
                fs = min(60, 380 / (0.72 * len(label)))
                lx, ly, anchor = 700, cy + fs * 0.36, "start"
            labels.append(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="{anchor}" '
                          f'font-family="Archivo Black" font-size="{fs:.0f}" fill="{colour}">{label}</text>')
    return "".join(out + labels) + "</svg>"


def _board_check(png, said):
    """The board's own check (diagram._check is for stand-alone diagrams: it scores any cross 4/10 and judges
    without the voice, so it rejected every 'it runs out' picture and argued with the already fact-checked script)."""
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    im.thumbnail((540, 960))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return llm_json(f"""You check one picture for a science YouTube Short. It appears WHILE the narrator says:
"{said}"
(That sentence is already fact-checked; judge only the PICTURE.)
The picture's language: emoji pictures stand for the things (the closest emoji is fine when its label names it,
e.g. a spider labelled TICKS, both being small eight-legged animals), but a picture of a DIFFERENT KIND of thing
(a tree labelled NYMPHS, a coin labelled CELL) is WRONG; several copies mean "many"; a downward arrow means "leads to"; a red cross over a
group means it runs out or is gone.
- Does the picture show what the sentence says, so a 12-year-old hearing it would connect them? (0-10)
- Is anything in the picture WRONG for that sentence (wrong thing, wrong direction, wrong label), misspelled,
  overlapping or unreadable?
Return JSON: {{"score": 0-10, "accurate": true or false, "problems": "one line or empty"}}""", images=[buf.getvalue()])


def _groups(out):
    """The AI's groups with their pictures fetched; raises ValueError naming what is wrong."""
    from .diagram import _icon
    groups = []
    for g in (out.get("groups") or [])[:3]:
        icons = [_icon(str(e)) for e in (g.get("emoji") or [])[:2]]
        if not icons or not all(icons):
            raise ValueError(f"no picture exists for {g.get('emoji')}; use single standard emoji")
        groups.append({"icons": icons, "count": max(1, min(6, int(g.get("count") or 1))),
                       "gone": bool(g.get("gone")), "label": g.get("label") or ""})
    if not groups:
        raise ValueError("it needs 1-3 groups")
    return groups


def _draw_one(k, scenes, topic, look, lines):
    """One scene's drawing, checked; up to 2 tries (the free AI quota is shared by three channels). Returns svg or None."""
    said, note = scenes[k].get("narration", ""), ""
    for attempt in range(3):
        try:
            out = llm_json(f"""You picture, on a board, ONE step of the explanation in a science YouTube Short about: {topic}
The whole lesson, scene by scene (for context):
{lines}
Picture ONLY scene {k}: "{said}"
The board's emoji for recurring things: {look or 'pick clear, consistent emoji'}
It must be scientifically ACCURATE for exactly that sentence, and make sense at a glance without the voice.
{GROUPS}
{("The previous picture was rejected because: " + note + " Fix that.") if note else ""}
Return JSON: {{"groups": [{{"emoji": ["..."], "count": 1, "gone": false, "label": "..."}}]}}""")
            try:
                svg = _compose(_groups(out))
            except (ValueError, TypeError) as e:
                note = str(e)
                continue
            verdict = _board_check(_render_png(svg), said)
            if verdict.get("accurate") and float(verdict.get("score", 0) or 0) >= 6:
                return svg
            note = verdict.get("problems") or f"score {verdict.get('score')}"
        except Exception as e:
            note = str(e)[:120]
    log(f"whiteboard: scene {k + 1} not drawn ({note[:80]})")
    _NOTES[k] = note[:160]
    return None


_NOTES = {}   # scene index -> why it was not drawn (saved to data/board_log.json; the CI log needs a sign-in)
_COUNT = re.compile(r"pause and guess|three[,.…]*\s*two[,.…]*\s*one", re.I)


def _drawable(sc):
    """A scene worth drawing: not the countdown, and long enough to show something."""
    said = sc.get("narration", "")
    return not sc.get("anim") and not _COUNT.search(said) and len(said.split()) >= 6


def _record(script, drawn, error=""):
    try:
        path = Path(__file__).resolve().parent.parent / "data" / "board_log.json"
        rows = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        from datetime import datetime, timezone
        rows.append({"when": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), "topic": script.get("topic", "")[:90],
                     "drawn": [k + 1 for k in sorted(drawn)], "not_drawn": {str(k + 1): v for k, v in sorted(_NOTES.items())},
                     "error": error[:300]})
        path.write_text(json.dumps(rows[-40:], ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass


def plan(script, topic):
    """{scene_index: svg} for the explaining scenes, each drawing checked; {} if fewer than 2 pass.
    One shared look first, then each scene drawn on its own (focused requests draw better than one
    request for every drawing at once: 2 of 5 passed that way on the first test, 16 Nov 2026)."""
    from concurrent.futures import ThreadPoolExecutor
    scenes = script.get("scenes", [])
    # at most 4 drawn scenes; never the countdown ("Pause and guess... three, two, one" drew a blob, 16 Nov 2026)
    middle = [k for k in range(1, len(scenes) - 1) if _drawable(scenes[k])][:4]
    _NOTES.clear()
    if not middle:
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
    if not good:   # one checked drawing is still better than none (the rest of the scenes use footage)
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
    drawings = {}
    try:
        drawings = plan(script, topic or script.get("topic", ""))
        clips = render(drawings, times, job_dir) if drawings else {}
        _record(script, clips)
        return clips
    except Exception as e:
        log(f"whiteboard: no drawing board ({str(e)[:100]})")
        _record(script, {}, f"{type(e).__name__}: {e} (drawings passed: {[k + 1 for k in sorted(drawings)]})")
        return {}
