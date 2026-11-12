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
                log(f"diagram: drawn for '{narration[:50]}' (score {verdict.get('score')})")
                return True
            note = verdict.get("problems") or f"score {verdict.get('score')}"
            log(f"diagram: attempt {attempt + 1} rejected ({note[:80]})")
        except Exception as e:
            note = str(e)[:120]
            log(f"diagram: attempt {attempt + 1} failed ({note[:80]})")
    return False
