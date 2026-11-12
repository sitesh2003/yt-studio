"""Agent 4c - Explainer diagrams, free, for the moments no camera can film.

When stock footage has nothing that shows what the narrator is saying (a chemical sticking to the
tongue, air pockets inside an apple, sap rising in a tree), the AI draws a clean, clearly-illustrated
diagram as SVG, it is rendered to an image here (resvg, open source), and a separate check looks at
the picture and must agree it is accurate and readable before it is used.

Illustrations only - never photo-realistic - so nothing could be mistaken for real footage.
"""
import io
import re

from .core import ASSETS, llm_json, log

STYLE = """Canvas: <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920" width="1080" height="1920">.
Start with <rect width="1080" height="1920" fill="#0b1630"/> (dark navy).
Draw ONLY in the band y=220..1060 (the area below is covered by captions and phone buttons).
Flat, friendly educational illustration: simple shapes, thick 8-14px strokes, rounded corners,
bright colours only from #ffd60a (yellow), #2ec4b6 (teal), #ff6b6b (coral), #ffffff, #8ecae6.
Draw RECOGNISABLE OBJECTS (a tongue, a glass, a drop, an apple cut in half, a tree trunk), never
abstract symbols: no crosses, no bare dots standing for things. Fill most of the band - large shapes.
Show the PROCESS with arrows where something moves or changes. Big and bold, readable on a phone.
At most 3 labels, each 1-3 words, font-family="Archivo Black", font-size 52 or more, white or yellow,
never overlapping a shape outline or another label. No paragraphs, no title, no logos, no people's
faces, nothing photo-realistic. It must be scientifically ACCURATE for the sentence."""


def _render(svg):
    import resvg_py
    font = str(ASSETS / "fonts" / "ArchivoBlack-Regular.ttf")
    png = resvg_py.svg_to_bytes(svg_string=svg, font_files=[font], font_family="Archivo Black",
                                width=1080, height=1920)
    return bytes(png)


def _check(png, narration):
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    im.thumbnail((540, 960))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return llm_json(f"""You check an explainer diagram for a science YouTube Short before it is used.
The narrator says: "{narration}"
Judge the image strictly, as a 12-year-old seeing it for one second without the voice:
- would they recognise the objects and understand what is happening? Abstract symbols, crosses,
  bare dots, or a mostly empty frame score 4 or less. (0-10)
- is anything scientifically wrong, misleading, garbled, misspelled, overlapping or unreadable?
Return JSON: {{"score": 0-10, "accurate": true or false, "problems": "one line or empty"}}""",
                    images=[buf.getvalue()])


def make(narration, topic, out_png):
    """Returns True if an accurate, readable diagram was saved to out_png."""
    note = ""
    for attempt in range(2):
        try:
            out = llm_json(f"""Draw one explainer diagram as SVG for a science YouTube Short about: {topic}
It must illustrate exactly this sentence: "{narration}"
{STYLE}
{("The previous attempt was rejected because: " + note + " Fix that.") if note else ""}
Return JSON: {{"svg": "<svg ...>...</svg>"}}""")
            svg = out.get("svg") or ""
            if "<svg" not in svg:
                note = "no SVG was returned"
                continue
            svg = svg[svg.index("<svg"):svg.rindex("</svg>") + 6]
            svg = re.sub(r"<(script|foreignObject)[\s\S]*?</\1>", "", svg, flags=re.I)  # plain drawing only
            png = _render(svg)
            verdict = _check(png, narration)
            if verdict.get("accurate") and float(verdict.get("score", 0) or 0) >= 8:
                with open(out_png, "wb") as fh:
                    fh.write(png)
                with open(str(out_png)[:-4] + ".svg", "w", encoding="utf-8") as fh:
                    fh.write(svg)
                log(f"diagram: drawn for '{narration[:50]}' (score {verdict.get('score')})")
                return True
            note = verdict.get("problems") or f"score {verdict.get('score')}"
            log(f"diagram: attempt {attempt + 1} rejected ({note[:80]})")
        except Exception as e:
            note = str(e)[:120]
            log(f"diagram: attempt {attempt + 1} failed ({note[:80]})")
    return False


def _build_up(svg, stages=3):
    """The diagram drawn in stages, like a teacher at a board: background, then the objects,
    then the arrows and labels. Groups are opened up so their parts can appear one after another
    (the group's own attributes, such as a transform, are kept). Returns one PNG per stage."""
    import copy
    import xml.etree.ElementTree as ET
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    root = ET.fromstring(svg)
    kids = list(root)
    defs = [c for c in kids if c.tag.endswith(("defs", "style"))]
    draw = [c for c in kids if c not in defs]
    if not draw:
        return [_render(svg)]
    bg, rest = draw[:1], draw[1:]
    units = []                                  # (top-level element, child-or-None)
    for el in rest:
        parts = list(el) if el.tag.endswith("}g") and len(list(el)) > 1 else []
        units += [(el, c) for c in parts] or [(el, None)]
    if len(units) < 3:
        return [_render(svg)]
    out = []
    for k in range(1, stages + 1):
        keep = units[:max(1, round(len(units) * k / stages))]
        new = copy.copy(root)
        for c in list(new):
            new.remove(c)
        for c in defs + bg:
            new.append(c)
        shells = {}
        for el, child in keep:
            if child is None:
                new.append(el)
                continue
            if id(el) not in shells:
                shell = copy.copy(el)
                for c in list(shell):
                    shell.remove(c)
                shells[id(el)] = shell
                new.append(shell)
            shells[id(el)].append(child)
        out.append(_render(ET.tostring(new, encoding="unicode")))
    return out


def make_clip(narration, topic, job_dir, i, out_mp4, seconds):
    """An animated explainer for a moment no camera can film: one checked diagram, built up on screen
    in stages with soft fades. Returns True when a clip was made."""
    from .core import config, run
    png = job_dir / f"dia_{i:02d}.png"
    if not make(narration, topic, png):
        return False
    try:
        steps = _build_up(open(str(png)[:-4] + ".svg", encoding="utf-8").read())
    except Exception as e:
        log(f"diagram: build-up skipped ({str(e)[:60]})")
        steps = [png.read_bytes()]
    f = config()["format"]
    paths = []
    for k, data in enumerate(steps):
        pth = job_dir / f"dia_{i:02d}_{k}.png"
        pth.write_bytes(data)
        paths.append(pth)
    n = len(paths)
    hold_last = seconds * 0.45                      # the finished diagram stays longest
    each = max((seconds - hold_last) / max(n - 1, 1), 0.6) if n > 1 else seconds
    fade = min(0.35, each / 2)
    cmd = ["ffmpeg", "-y"]
    for k, pth in enumerate(paths):
        dur = (hold_last if k == n - 1 else each) + fade + 0.1
        cmd += ["-loop", "1", "-t", f"{dur:.2f}", "-i", str(pth)]
    if n == 1:
        flt = f"[0:v]scale={f['width']}:{f['height']},fps={f['fps']}[v]"
    else:
        flt, prev, t = "", "[0:v]", 0.0
        for k in range(1, n):
            t += each
            flt += f"{prev}[{k}:v]xfade=transition=fade:duration={fade:.2f}:offset={t - fade:.2f}[x{k}];"
            prev = f"[x{k}]"
        flt += f"{prev}scale={f['width']}:{f['height']},fps={f['fps']}[v]"
    run(cmd + ["-filter_complex", flt, "-map", "[v]", "-t", f"{seconds:.2f}", "-c:v", "libx264",
               "-pix_fmt", "yuv420p", str(out_mp4)])
    log(f"diagram: built up on screen in {n} stages")
    return True


# ---------------------------------------------------------------------------------------------
# The EXPLAINER BOARD (12 Nov 2026, after studying the most detailed explainer Shorts): instead of
# separate one-off pictures, ONE diagram for the whole explanation that GROWS scene by scene - the
# first scene draws the main object, the next adds what happens to it, the answer adds the result -
# so the viewer always sees how each new fact connects to the last one, like a teacher at a board.
# ---------------------------------------------------------------------------------------------
# The pictures on the board are Twemoji illustrations (CC BY 4.0, credited in the description): a
# large, consistent, colourful set of recognisable things - animals, foods, plants, body parts,
# weather, tools - so every step shows a real object, never an abstract shape the AI made up.
TWEMOJI = "https://cdn.jsdelivr.net/gh/jdecked/twemoji@15.1.0/assets/svg/{}.svg"
CREDIT = "Board icons: Twemoji by Twitter and contributors, CC BY 4.0"
_icons = {}


def _icon(emoji):
    """The Twemoji drawing for one emoji: (inner svg, viewBox), or None if there is no such icon."""
    code = "-".join(f"{ord(c):x}" for c in emoji if ord(c) != 0xFE0F)
    if code not in _icons:
        import requests
        try:
            r = requests.get(TWEMOJI.format(code), timeout=15)
            svg = r.text if r.ok and "<svg" in r.text else ""
        except Exception:
            svg = ""
        m = re.search(r"<svg\b[^>]*>([\s\S]*)</svg>", svg)
        vb = re.search(r'viewBox="([^"]+)"', svg)
        _icons[code] = (m[1], vb[1] if vb else "0 0 36 36") if m else None
    return _icons[code]


def _esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _board_svg(steps, upto):
    """Steps as a top-to-bottom flow in the free band (y 230-1050): the step's pictures on the left
    (joined by small arrows when a step shows one thing turning into another), its label on the right,
    an arrow down to the next step. Only the first `upto` steps are drawn."""
    n = len(steps)
    row = 820 / n
    area = 470                                     # width for the pictures, from x=130
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920" width="1080" height="1920">',
           '<rect width="1080" height="1920" fill="#0b1630"/>']
    for k, st in enumerate(steps[:upto]):
        top = 230 + k * row
        cy = top + row / 2
        out.append(f'<rect x="90" y="{top + 10:.0f}" width="900" height="{row - 20:.0f}" rx="36" '
                   f'fill="#13234a" stroke="{"#ffd60a" if k == upto - 1 else "#2b3f6e"}" stroke-width="6"/>')
        pics = st["icons"]
        gap = 50 if len(pics) > 1 else 0
        size = min(row - 70, (area - gap * (len(pics) - 1)) / len(pics), 240)
        x = 130 + (area - size * len(pics) - gap * (len(pics) - 1)) / 2
        for j, (inner, vb) in enumerate(pics):
            out.append(f'<svg x="{x:.0f}" y="{cy - size / 2:.0f}" width="{size:.0f}" height="{size:.0f}" viewBox="{vb}">{inner}</svg>')
            x += size
            if j + 1 < len(pics):
                out.append(f'<path d="M{x + 10:.0f} {cy - 16:.0f} L{x + 40:.0f} {cy:.0f} L{x + 10:.0f} {cy + 16:.0f} Z" fill="#ffd60a"/>')
                x += gap
        label = _esc(st["label"][:14].upper())
        fs = 64 if len(label) <= 8 else 54 if len(label) <= 11 else 46
        out.append(f'<text x="{130 + area + (990 - 130 - area) / 2:.0f}" y="{cy + fs * 0.35:.0f}" text-anchor="middle" '
                   f'font-family="Archivo Black" font-size="{fs}" fill="#ffffff">{label}</text>')
        out.append(f'<circle cx="90" cy="{top + 10:.0f}" r="34" fill="#ffd60a"/><text x="90" y="{top + 26:.0f}" '
                   f'text-anchor="middle" font-family="Archivo Black" font-size="44" fill="#0b1630">{k + 1}</text>')
        if k + 1 < n and k + 1 < upto:
            y0 = top + row - 14
            out.append(f'<path d="M540 {y0 - 6:.0f} L540 {y0 + 22:.0f}" stroke="#ffd60a" stroke-width="12"/>'
                       f'<path d="M515 {y0 + 14:.0f} L540 {y0 + 40:.0f} L565 {y0 + 14:.0f} Z" fill="#ffd60a"/>')
    out.append("</svg>")
    return "".join(out)


def make_board(script, topic):
    """One growing explainer board. Returns {scene_index: png bytes of the board up to and including
    that scene's step} for the scenes it covers, or {} if no accurate, readable board was made."""
    scenes = script.get("scenes", [])
    if len(scenes) < 5:
        return {}
    lines = "\n".join(f"{k}: {s.get('narration', '')}" for k, s in enumerate(scenes))
    note = ""
    for attempt in range(2):
        try:
            out = llm_json(f"""A science YouTube Short about: {topic}
The narration, scene by scene (index: words):
{lines}
Build an EXPLAINER BOARD that grows as the explanation goes: pick 2-4 scenes in the MIDDLE that are
the steps of the explanation, in order (never scene 0, the hook, never the last scene, the closing
question). For each step give a short label (1-2 words, max 11 letters, spelled correctly) and
1-3 standard emoji whose PICTURES show exactly that step - real objects (🦐 🐟 🍁 🪣 🔥 🍯 🧅 👅 💧 🌡️),
in order, so "krill turns salmon pink" is ["🦐", "🐟"]. Each emoji must be a single standard emoji
that clearly is the thing named; never a symbol, letter, flag or face used to stand for an idea,
and never a heart, coloured circle or square used to stand for a colour or a chemical (use the
real object that carries it instead: 🦐 for the pigment in shrimp, 🍣 for pink salmon meat).
The board must follow the narration's cause and effect exactly.
{("The previous board was rejected because: " + note + " Fix that.") if note else ""}
Return JSON: {{"steps": [{{"scene": index, "label": "...", "emoji": ["...", "..."]}}]}}""")
            steps = []
            for st in out.get("steps") or []:
                if not (isinstance(st, dict) and str(st.get("label", "")).strip() and isinstance(st.get("scene"), int)
                        and 0 < st["scene"] < len(scenes) - 1):
                    continue
                icons = [_icon(str(e)) for e in (st.get("emoji") or [])[:3]]
                if icons and all(icons):
                    steps.append(dict(st, icons=icons))
            steps = sorted({st["scene"]: st for st in steps}.values(), key=lambda st: st["scene"])[:4]
            if len(steps) < 2:
                note = "it needs 2-4 middle steps, each with a label and 1-3 standard emoji that exist"
                continue
            full = _render(_board_svg(steps, len(steps)))
            said = " ".join(scenes[st["scene"]].get("narration", "") for st in steps)
            verdict = _check(full, said)
            if not (verdict.get("accurate") and float(verdict.get("score", 0) or 0) >= 7):
                note = verdict.get("problems") or f"score {verdict.get('score')}"
                log(f"diagram: board attempt {attempt + 1} rejected ({note[:80]})")
                continue
            log(f"diagram: explainer board for scenes {[st['scene'] + 1 for st in steps]} "
                f"({' > '.join(st['label'] + ' ' + ''.join(st['emoji']) for st in steps)}, score {verdict.get('score')})")
            return {st["scene"]: _render(_board_svg(steps, k + 1)) for k, st in enumerate(steps)}
        except Exception as e:
            note = str(e)[:120]
            log(f"diagram: board attempt {attempt + 1} failed ({note[:80]})")
    return {}


def _drift(f, seconds):
    """A slow push-in on the board (about 6%), so a board scene is never a frozen frame: the QA
    freeze check rejected the chameleon Short on 12 Nov for an 8-second still board."""
    W, H, fps = f["width"], f["height"], f["fps"]
    n = max(1, int(seconds * fps))
    return (f"scale={W * 2}:{H * 2},zoompan=z='1+0.06*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d=1:s={W}x{H}:fps={fps}")


def board_clip(prev_png, png, out_mp4, seconds, job_dir, i):
    """One scene of the board: the board so far, with this scene's new part fading in."""
    from .core import config, run
    f = config()["format"]
    cur = job_dir / f"board_{i:02d}.png"
    cur.write_bytes(png)
    if prev_png is None:
        run(["ffmpeg", "-y", "-loop", "1", "-t", f"{seconds:.2f}", "-i", str(cur), "-vf",
             f"fps={f['fps']},fade=t=in:st=0:d=0.4," + _drift(f, seconds), "-c:v", "libx264",
             "-pix_fmt", "yuv420p", str(out_mp4)])
        return
    old = job_dir / f"board_{i:02d}_prev.png"
    old.write_bytes(prev_png)
    run(["ffmpeg", "-y", "-loop", "1", "-t", "0.8", "-i", str(old), "-loop", "1", "-t", f"{seconds + 0.5:.2f}",
         "-i", str(cur), "-filter_complex",
         f"[0:v][1:v]xfade=transition=fade:duration=0.6:offset=0.15,fps={f['fps']}," + _drift(f, seconds + 0.5) + "[v]",
         "-map", "[v]", "-t", f"{seconds:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out_mp4)])
