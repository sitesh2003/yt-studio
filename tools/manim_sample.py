"""Manim engine sample (14 Nov 2026): a vertical 1080x1920 visual proof where every number and every
corner is computed in code. Rendered by .github/workflows/manim-test.yml.

First render (same day) worked and was fast (7 s for 10 s of video) but had a label off the left edge
and no square on the hypotenuse. So: all three squares are built from the triangle's corners, numbers
sit INSIDE their squares, everything is scaled to a safe area, and check_inside() fails the render if
anything is outside the screen, so a cut-off label can never be shipped."""
import numpy as np
from manim import (BLUE, DOWN, GREEN, ORIGIN, UP, WHITE, YELLOW, Create, FadeIn, Polygon, Scene, Text,
                   TransformMatchingShapes, VGroup, Write, config)

config.pixel_width, config.pixel_height = 1080, 1920
config.frame_width, config.frame_height = 9, 16
config.frame_rate = 30
config.background_color = "#0b1630"
SAFE_W, SAFE_H = 9 * 0.86, 16 * 0.90          # keep 7% / 5% margins on every side

A, B = 3, 4
C = float(np.hypot(A, B))                     # computed, never typed: 5.0


def square_on(p, q, away_from):
    """The square built on segment p-q, on the side away from the given point."""
    p, q, away_from = map(np.array, (p, q, away_from))
    d = q - p
    n = np.array([-d[1], d[0], 0.0])
    if np.dot(n, (p + q) / 2 - away_from) < 0:
        n = -n
    return [p, q, q + n, p + n]


def check_inside(scene):
    for m in scene.mobjects:
        for pt in (m.get_corner(UP + np.array([-1, 0, 0])), m.get_corner(DOWN + np.array([1, 0, 0]))):
            if abs(pt[0]) > 4.5 + 1e-3 or abs(pt[1]) > 8 + 1e-3:
                raise RuntimeError(f"off screen: {type(m).__name__} at {pt[:2]}")


class Pythagoras(Scene):
    def construct(self):
        O, Ap, Bp = np.array([0.0, 0, 0]), np.array([A, 0.0, 0]), np.array([0.0, B, 0])
        tri = Polygon(O, Ap, Bp, color=WHITE, stroke_width=5)
        sq = {
            "a": Polygon(*square_on(O, Ap, Bp), color=BLUE, fill_opacity=0.5, stroke_width=4),
            "b": Polygon(*square_on(O, Bp, Ap), color=GREEN, fill_opacity=0.5, stroke_width=4),
            "c": Polygon(*square_on(Ap, Bp, O), color=YELLOW, fill_opacity=0.35, stroke_width=4),
        }
        fig = VGroup(tri, *sq.values())
        fig.scale_to_fit_width(SAFE_W * 0.8)
        if fig.height > SAFE_H * 0.55:
            fig.scale_to_fit_height(SAFE_H * 0.55)
        fig.move_to(ORIGIN + UP * 0.4)
        title = Text("Why do 3, 4 and 5\nfit perfectly?", font_size=56, color=WHITE, line_spacing=0.9)
        title.scale_to_fit_width(min(title.width, SAFE_W)).to_edge(UP, buff=0.9)
        self.play(Write(title))
        self.play(Create(tri))
        labels = {}
        for k, n in (("a", A), ("b", B), ("c", C)):
            labels[k] = Text(f"{int(n * n)}", font_size=60, color=WHITE).move_to(sq[k].get_center())
        self.play(FadeIn(sq["a"]), Write(labels["a"]))
        self.play(FadeIn(sq["b"]), Write(labels["b"]))
        sum_txt = Text(f"{A * A} + {B * B} = {A * A + B * B}", font_size=64, color=WHITE).to_edge(DOWN, buff=1.6)
        self.play(Write(sum_txt))
        self.play(FadeIn(sq["c"]), Write(labels["c"]))
        rule = Text("a² + b² = c²", font_size=80, color=YELLOW).move_to(sum_txt)
        check_inside(self)
        self.play(TransformMatchingShapes(sum_txt, rule))
        check_inside(self)
        self.wait(1.5)
