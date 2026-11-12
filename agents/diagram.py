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
