"""Manim scene templates, rendered by agents/animate.py with:  manim render ... manim_templates.py <Type>
Parameters come from the JSON file in $ANIM_PARAMS. Every template draws only what the parameters say.

Layout (14 Nov 2026): the spoken captions are burned in at a fixed height (config captions.position_y),
so every template keeps that band EMPTY: the graphic lives above it, secondary text below it.
check_layout() fails the render if anything leaves the screen or enters the caption band, so a cut-off
or covered label is never shipped."""
import json
import os

import numpy as np
from manim import (DOWN, LEFT, ORIGIN, RIGHT, UP, Arrow, Circle, Create, FadeIn, GrowFromEdge, Rectangle, RoundedRectangle,
                   Scene, Text, ValueTracker, VGroup, Write, always_redraw, config)

P = json.load(open(os.environ["ANIM_PARAMS"], encoding="utf-8"))
W, H = P.get("width", 1080), P.get("height", 1920)
config.pixel_width, config.pixel_height = W, H
config.frame_height = 16.0 if H > W else 9.0
config.frame_width = config.frame_height * W / H
config.frame_rate = 30
config.background_color = "#0b1630"
FONT = "Archivo Black"
try:   # the channel font ships in the repo; register it so Pango finds it on any machine
    import manimpango
    manimpango.register_font(os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "ArchivoBlack-Regular.ttf"))
except Exception:
    pass
YEL, WHITE, BLUE, MUTED = "#ffd60a", "#ffffff", "#4cc9f0", "#8a94a6"
FW, FH = config.frame_width, config.frame_height
PPU = H / FH                                         # pixels per scene unit
SAFE_W = FW * 0.86
MARGIN = FH * 0.05
CAP_Y, CAP_H = float(P.get("cap_y", H * 0.615)), float(P.get("cap_h", H * 0.14))
BAND_TOP = FH / 2 - (CAP_Y - CAP_H / 2) / PPU        # the caption band, in scene units
BAND_BOT = FH / 2 - (CAP_Y + CAP_H / 2) / PPU
UP_TOP, UP_BOT = FH / 2 - MARGIN, BAND_TOP + 0.3     # the graphic's region, above the captions
LOW_TOP = BAND_BOT - 0.3                             # secondary text, below the captions


def T(s, size=48, color=WHITE, max_w=None):
    t = Text(str(s), font=FONT, font_size=size, color=color)
    if t.width > (max_w or SAFE_W):
        t.scale_to_fit_width(max_w or SAFE_W)
    return t


def fit(group, top, bottom, max_w=SAFE_W):
    """Scale a group to fit between two heights and centre it there."""
    room = top - bottom
    if group.height > room:
        group.scale_to_fit_height(room)
    if group.width > max_w:
        group.scale_to_fit_width(max_w)
    return group.move_to([0, (top + bottom) / 2, 0])


def check_layout(scene):
    for m in scene.mobjects:
        if isinstance(m, ValueTracker) or not any(sm.has_points() for sm in m.get_family()):
            continue           # invisible helpers draw nothing (a ValueTracker keeps its value as a point)
        x0, x1, y0, y1 = m.get_left()[0], m.get_right()[0], m.get_bottom()[1], m.get_top()[1]
        if x0 < -FW / 2 - 1e-3 or x1 > FW / 2 + 1e-3 or y0 < -FH / 2 - 1e-3 or y1 > FH / 2 + 1e-3:
            raise RuntimeError(f"off screen: {type(m).__name__}")
        if y0 < BAND_TOP and y1 > BAND_BOT:
            raise RuntimeError(f"covers the caption band: {type(m).__name__}")


class Base(Scene):
    def title(self):
        t = T(P.get("title", ""), 72)
        return t.move_to([0, UP_TOP - t.height / 2, 0])

    def finish(self):
        check_layout(self)
        self.wait(max(0.5, float(P.get("seconds", 4)) - self.renderer.time))


class Compare(Base):
    """Two true quantities as bars: {"title", "a_label", "a_value", "b_label", "b_value", "unit"}."""
    def construct(self):
        title = self.title()
        a, b = float(P["a_value"]), float(P["b_value"])
        top_v = max(a, b)
        heads, bars = [], []
        for k, (lab, val, col) in enumerate(((P["a_label"], a, BLUE), (P["b_label"], b, YEL))):
            unit = P.get("unit", "")
            if val == 1 and unit.endswith("s"):
                unit = unit[:-1]          # "1 gallon", never "1 gallons"
            num = T(f"{P.get(('a' if k == 0 else 'b') + '_text') or _fmt(val)} {unit}".strip(), 58, col, FW * 0.42)
            name = T(lab, 44, WHITE, FW * 0.42)
            heads.append(VGroup(name, num).arrange(DOWN, buff=0.15))
        head_h = max(h.height for h in heads)
        hmax = (title.get_bottom()[1] - 0.5) - UP_BOT - head_h - 0.3
        for k, val in enumerate((a, b)):
            h = max(0.08, hmax * val / top_v)
            x = (-1 if k == 0 else 1) * FW * 0.22
            bar = Rectangle(width=FW * 0.28, height=h, fill_color=(BLUE, YEL)[k], fill_opacity=1, stroke_width=0)
            bar.move_to([x, UP_BOT + h / 2, 0])
            heads[k].next_to(bar, UP, buff=0.25)
            bars.append(bar)
        self.play(Write(title), run_time=0.7)
        for bar, head in zip(bars, heads):
            self.play(GrowFromEdge(bar, DOWN), run_time=0.8)
            self.play(FadeIn(head), run_time=0.4)
        self.finish()


class Counter(Base):
    """One big true number counting up: {"title", "value", "decimals", "unit", "caption"}."""
    def construct(self):
        title = self.title()
        d = int(P.get("decimals", 0) or 0)
        target = float(P["value"])
        v = ValueTracker(0)
        fmt = lambda x: f"{x:,.{d}f}"
        unit = T(P.get("unit", ""), 76, WHITE)
        big = T(fmt(target), 230, YEL)
        block = fit(VGroup(big, unit).arrange(DOWN, buff=0.3), title.get_bottom()[1] - 0.6, UP_BOT)
        scale, centre = big.height / Text(fmt(target), font=FONT, font_size=230).height, big.get_center()

        def draw():
            return Text(fmt(v.get_value()), font=FONT, font_size=230, color=YEL).scale(scale).move_to(centre)

        num = always_redraw(draw)
        cap = T(P.get("caption", ""), 48, MUTED)
        cap.move_to([0, LOW_TOP - cap.height / 2, 0])
        self.play(Write(title), FadeIn(num), run_time=0.7)
        self.play(v.animate.set_value(target), run_time=1.6)
        num.clear_updaters()
        self.play(FadeIn(unit), FadeIn(cap), run_time=0.5)
        self.finish()


class Grid(Base):
    """"k in n" as n dots with k lit: {"title", "k", "n", "caption"} (n <= 100)."""
    def construct(self):
        k, n = int(P["k"]), int(P["n"])
        title = T(P.get("title", f"{k} in {n}"), 84, WHITE)
        title.move_to([0, UP_TOP - title.height / 2, 0])
        cap = T(P.get("caption", ""), 50, MUTED).next_to(title, DOWN, buff=0.35)
        cols = 10 if n > 10 else n
        rows = int(np.ceil(n / cols))
        dots = VGroup(*[Circle(radius=0.5, fill_color=YEL if i < k else "#24324f", fill_opacity=1, stroke_width=0)
                        for i in range(n)]).arrange_in_grid(rows=rows, cols=cols, buff=0.3)
        fit(dots, cap.get_bottom()[1] - 0.6, UP_BOT)
        self.play(Write(title), run_time=0.7)
        self.play(FadeIn(cap), FadeIn(dots, lag_ratio=0.02), run_time=1.2)
        self.finish()


class Steps(Base):
    """A short true process: {"title", "steps": ["2-4 labels, max 4 words each"]}."""
    def construct(self):
        title = self.title()
        boxes = VGroup()
        for s in list(P["steps"])[:4]:
            t = T(s, 54, WHITE)
            box = RoundedRectangle(corner_radius=0.25, width=min(SAFE_W, t.width + 0.9), height=t.height + 0.7,
                                   stroke_color=BLUE, stroke_width=4, fill_color="#13234a", fill_opacity=1)
            boxes.add(VGroup(box, t.move_to(box)))
        boxes.arrange(DOWN, buff=0.7)
        fit(boxes, title.get_bottom()[1] - 0.5, UP_BOT)
        self.play(Write(title), run_time=0.7)
        for i, b in enumerate(boxes):
            if i:
                self.play(Create(Arrow(boxes[i - 1].get_bottom(), b.get_top(), buff=0.08, color=YEL,
                                       stroke_width=8, max_tip_length_to_length_ratio=0.35)), run_time=0.3)
            self.play(FadeIn(b, shift=UP * 0.3), run_time=0.5)
        self.finish()


class Equation(Base):
    """A worked example, one line at a time: {"title", "lines": ["(-3) x (-4)", "= 12"]}. The last line
    is the result, in yellow. Every arithmetic line was evaluated by animate.py before rendering."""
    def construct(self):
        title = self.title()
        lines = list(P["lines"])[:5]
        rows = VGroup(*[T(l, 76, YEL if i == len(lines) - 1 else WHITE) for i, l in enumerate(lines)])
        rows.arrange(DOWN, buff=0.55)
        fit(rows, title.get_bottom()[1] - 0.6, UP_BOT)
        self.play(Write(title), run_time=0.7)
        for r in rows:
            self.play(FadeIn(r, shift=UP * 0.25), run_time=0.6)
            self.wait(0.35)
        self.finish()


class NumberLine(Base):
    """Jumps along a number line: {"title", "start": 0, "jumps": [-3, -3], "lo": -8, "hi": 4}.
    Each jump is an arrow from where you are to where you land, labelled with its size."""
    def construct(self):
        from manim import Dot, Line, CurvedArrow
        title = self.title()
        lo, hi = int(P.get("lo", -10)), int(P.get("hi", 10))
        span = max(1, hi - lo)
        y = (title.get_bottom()[1] + UP_BOT) / 2 - 0.6
        x = lambda v: -SAFE_W / 2 + (v - lo) / span * SAFE_W
        axis = Line([x(lo), y, 0], [x(hi), y, 0], color=WHITE, stroke_width=6)
        step = max(1, round(span / 10))
        ticks = VGroup()
        for v in range(lo, hi + 1, step):
            ticks.add(Line([x(v), y - 0.15, 0], [x(v), y + 0.15, 0], color=WHITE, stroke_width=4))
            ticks.add(T(v, 34, MUTED).move_to([x(v), y - 0.5, 0]))
        self.play(Write(title), Create(axis), FadeIn(ticks), run_time=0.9)
        pos = float(P.get("start", 0))
        dot = Dot([x(pos), y, 0], radius=0.16, color=YEL)
        self.play(FadeIn(dot), run_time=0.3)
        for j in list(P.get("jumps", []))[:6]:
            new = pos + float(j)
            arc = CurvedArrow([x(pos), y + 0.25, 0], [x(new), y + 0.25, 0], color=BLUE, stroke_width=6,
                              angle=-1.2 if new > pos else 1.2)
            lab = T(("+" if j > 0 else "") + _fmt(j), 40, BLUE).next_to(arc, UP, buff=0.1)
            self.play(Create(arc), FadeIn(lab), dot.animate.move_to([x(new), y, 0]), run_time=0.6)
            pos = new
        self.play(FadeIn(T(_fmt(pos), 72, YEL).next_to(dot, DOWN, buff=0.9)), run_time=0.4)
        self.finish()


class Graph(Base):
    """A curve computed from a formula: {"title", "expr": "2**x", "x0": 0, "x1": 10, "x_label": "days",
    "y_label": "bacteria"}. Points are calculated here (the expression was checked safe in animate.py);
    axes and labels are plain shapes and text, no LaTeX."""
    def construct(self):
        from manim import Line, VMobject
        title = self.title()
        x0, x1 = float(P.get("x0", 0)), float(P.get("x1", 10))
        xs = np.linspace(x0, x1, 200)
        env = {"np": np, "sin": np.sin, "cos": np.cos, "exp": np.exp, "log": np.log, "sqrt": np.sqrt, "pi": np.pi}
        ys = np.array([float(eval(P["expr"], {"__builtins__": {}}, {**env, "x": v})) for v in xs])
        ok = np.isfinite(ys)
        xs, ys = xs[ok], ys[ok]
        y0, y1 = min(0.0, ys.min()), ys.max() if ys.max() > min(0.0, ys.min()) else ys.min() + 1
        top, bot = title.get_bottom()[1] - 0.9, UP_BOT + 0.9
        left, right = -SAFE_W / 2 + 0.4, SAFE_W / 2
        px = lambda v: left + (v - x0) / (x1 - x0) * (right - left)
        py = lambda v: bot + (v - y0) / (y1 - y0) * (top - bot)
        ax = VGroup(Line([left, py(y0), 0], [right, py(y0), 0], color=WHITE, stroke_width=5),
                    Line([left, bot, 0], [left, top, 0], color=WHITE, stroke_width=5))
        labs = VGroup(T(P.get("x_label", "x"), 36, MUTED).next_to([right, py(y0), 0], DOWN, buff=0.25).align_to([right, 0, 0], RIGHT),
                      T(P.get("y_label", "y"), 36, MUTED).next_to([left, top, 0], UP, buff=0.15).align_to([left, 0, 0], LEFT))
        curve = VMobject(color=YEL, stroke_width=8).set_points_smoothly([[px(a), py(b), 0] for a, b in zip(xs, ys)])
        self.play(Write(title), Create(ax), FadeIn(labs), run_time=0.8)
        self.play(Create(curve), run_time=max(1.2, float(P.get("seconds", 4)) * 0.45))
        self.finish()


def _fmt(v):
    return f"{int(v):,}" if float(v).is_integer() else f"{v:,.2f}".rstrip("0").rstrip(".")
