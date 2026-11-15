"""One continuous drawing board, rendered by agents/whiteboard.py with:
    manim render ... board_scene.py Board        (parameters in the JSON file named by $ANIM_PARAMS)

16 Nov 2026, owner: "instead of broken AI pics ... drawing continuously, handled properly as a narrative".
Every scene's drawing is added to the SAME board, below the last one, and is drawn on screen as the
narrator speaks: outlines first, then the colour fills in, then the labels are written. The camera glides
down the board from one drawing to the next, so the viewer never sees a hard cut - the picture grows with
the story, and the earlier drawing is still there, just above, when the camera moves on.

Each drawing is an SVG in the channel's 1080x1920 frame (agents/diagram.py style: drawn in the band
y=290..1060). Text in an SVG is redrawn here as real text (Manim's SVG reader skips <text>)."""
import json
import os
import re

from manim import (DrawBorderThenFill, LaggedStart, MovingCameraScene, SVGMobject, Text, VGroup, Write, config,
                   rate_functions)

P = json.load(open(os.environ["ANIM_PARAMS"], encoding="utf-8"))
W, H = P.get("width", 1080), P.get("height", 1920)
config.pixel_width, config.pixel_height = W, H
config.frame_height = 16.0 if H > W else 9.0
config.frame_width = config.frame_height * W / H
config.frame_rate = 30
config.background_color = P.get("background", "#0b1630")
FONT = "Archivo Black"
try:
    import manimpango
    manimpango.register_font(os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "ArchivoBlack-Regular.ttf"))
except Exception:
    pass
FW, FH = config.frame_width, config.frame_height
SW, SH = 1080, 1920              # every drawing's own coordinate frame (the video itself may be 2K)
U = FH / SH                      # scene units per SVG pixel
STEP = FH * 0.48                 # how far down the board each new drawing starts (the last one still peeks in above)
MOVE = 0.7                       # seconds the camera takes to glide to the next drawing

_TEXT = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)


def _attr(attrs, name, default=None):
    m = re.search(rf'\b{name}="([^"]*)"', attrs)
    return m.group(1) if m else default


def _clean(svg):
    """The SVG without its background rectangle and without <text> (drawn separately)."""
    svg = re.sub(r'<rect[^>]*width="1080"[^>]*height="1920"[^>]*/>', "", svg, count=1)
    svg = _TEXT.sub("", svg)
    # an invisible full-frame anchor first, so the reader's flip and placement are those of the whole frame
    # (Manim flips an SVG about the middle of whatever it contains); it is dropped before drawing
    return re.sub(r"(<svg\b[^>]*>)", r'\1<rect x="0" y="0" width="1080" height="1920" fill="#000000" fill-opacity="0.01"/>',
                  svg, count=1)


def _offset(svg):
    """A translate(x, y) on the drawing's top group (diagram.py often wraps the drawing in one)."""
    m = re.search(r'<g[^>]*transform="translate\(\s*([-\d.]+)[ ,]+([-\d.]+)\s*\)"', svg)
    return (float(m.group(1)), float(m.group(2))) if m else (0.0, 0.0)


def _labels(svg, top):
    """Text elements as Manim Text, placed where the SVG put them (SVG y grows down, Manim's up)."""
    dx, dy = _offset(svg)
    out = []
    for attrs, body in _TEXT.findall(svg):
        words = re.sub(r"<[^>]+>", "", body).strip()
        if not words:
            continue
        x = float(_attr(attrs, "x", "540")) + dx
        y = float(_attr(attrs, "y", "0")) + dy
        size = float(_attr(attrs, "font-size", "52"))
        t = Text(words, font=FONT, font_size=48, color=_attr(attrs, "fill", "#ffffff"))
        t.scale_to_fit_height(size * 0.72 * U)
        anchor = _attr(attrs, "text-anchor", "start")
        cx = (x - SW / 2) * U
        if anchor == "start":
            cx += t.width / 2
        elif anchor == "end":
            cx -= t.width / 2
        t.move_to([cx, top - (y - size * 0.36) * U + FH / 2, 0])
        out.append(t)
    return out


class Board(MovingCameraScene):
    def construct(self):
        cam = self.camera.frame
        for k, panel in enumerate(P["panels"]):
            svg = open(panel["svg"], encoding="utf-8").read()
            top = -k * STEP                     # this drawing's frame top, in board coordinates
            path = panel["svg"] + ".board.svg"
            open(path, "w", encoding="utf-8").write(_clean(svg))
            shapes = SVGMobject(path, should_center=False, height=None, width=None, stroke_width=None)
            # 1 SVG pixel = 1 unit, frame anchor spanning (0..1080, 0..1920): fit it to the frame at this point of the board
            shapes.stretch_to_fit_width(FW).stretch_to_fit_height(FH).move_to([0, top, 0])
            shapes.remove(shapes.submobjects[0])            # the invisible anchor
            labels = _labels(svg, top)
            # fill the space above the captions: AI drawings often use a small corner of the band, so the
            # drawing (shapes and labels together) is scaled up to the region and centred in it
            whole = VGroup(*shapes.submobjects, *labels)
            if whole.submobjects:
                box_top, box_bot = top + FH / 2 - FH * 0.15, top + FH / 2 - FH * 0.57
                s = min(FW * 0.88 / max(whole.width, 1e-3), (box_top - box_bot) / max(whole.height, 1e-3), 2.6)
                whole.scale(s).move_to([0, (box_top + box_bot) / 2, 0])
                for m in shapes.get_family():          # thicker lines when scaled up (labels keep their own look)
                    if hasattr(m, "stroke_width") and m.get_stroke_width():
                        m.set_stroke(width=min(m.get_stroke_width() * s ** 0.5, 18))
            secs = float(panel["seconds"])
            if k:
                self.play(cam.animate.move_to([0, top, 0]), run_time=min(MOVE, secs * 0.25),
                          rate_func=rate_functions.ease_in_out_sine)
                secs -= min(MOVE, secs * 0.25)
            parts = [m for m in shapes.submobjects if m.has_points()] or [shapes]
            draw = min(secs * 0.7, 1.2 + 0.35 * len(parts))
            write = min(secs - draw, 0.4 + 0.3 * len(labels)) if labels else 0
            self.play(DrawBorderThenFill(parts[0]), run_time=draw * (0.3 if parts[1:] else 1.0))
            if parts[1:]:
                self.play(LaggedStart(*[DrawBorderThenFill(m) for m in parts[1:]], lag_ratio=0.15), run_time=draw * 0.7)
            if labels:
                self.play(LaggedStart(*[Write(t) for t in labels], lag_ratio=0.3), run_time=max(0.3, write))
            rest = secs - draw - write
            if rest > 0.05:
                self.wait(rest)
