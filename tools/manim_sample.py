"""Manim engine, stage 1 sample (14 Nov 2026): a vertical 1080x1920 scene where every number on screen
is computed in code. Rendered by .github/workflows/manim-test.yml to measure quality and time on GitHub.
No LaTeX needed (Text, not MathTex), so it installs fast; LaTeX can come later for formulas."""
from manim import (BLUE, DOWN, GREEN, LEFT, ORIGIN, RIGHT, UP, WHITE, YELLOW, Create, FadeIn, Polygon,
                   Scene, Square, Text, Transform, VGroup, Write, config)

config.pixel_width, config.pixel_height = 1080, 1920
config.frame_width, config.frame_height = 9, 16
config.frame_rate = 30
config.background_color = "#0b1630"

A, B = 3, 4
C = (A * A + B * B) ** 0.5          # computed, never typed: 5.0
U = 0.55                            # scene units per triangle unit


class Pythagoras(Scene):
    def construct(self):
        title = Text("Why 3, 4 and 5 fit perfectly", font_size=46, color=WHITE).to_edge(UP, buff=1.0)
        self.play(Write(title))
        p0, p1, p2 = [x * U for x in (0, 0)] + [0], [A * U, 0, 0], [0, B * U, 0]
        tri = Polygon(p0, p1, p2, color=WHITE, stroke_width=6).move_to(ORIGIN + UP * 0.6)
        self.play(Create(tri))
        o = tri.get_vertices()
        sa = Square(A * U, color=BLUE, fill_opacity=0.45).next_to(tri, DOWN, buff=0).align_to(tri, LEFT)
        sb = Square(B * U, color=GREEN, fill_opacity=0.45).next_to(tri, LEFT, buff=0).align_to(tri, DOWN)
        self.play(FadeIn(sa), FadeIn(sb))
        la = Text(f"{A}×{A} = {A * A}", font_size=40, color=BLUE).next_to(sa, DOWN, buff=0.3)
        lb = Text(f"{B}×{B} = {B * B}", font_size=40, color=GREEN).next_to(sb, LEFT, buff=0.2).shift(DOWN * 2.6)
        self.play(Write(la), Write(lb))
        total = Text(f"{A * A} + {B * B} = {A * A + B * B}", font_size=54, color=YELLOW).to_edge(DOWN, buff=2.2)
        self.play(Write(total))
        side = Text(f"and {int(C)}×{int(C)} = {int(C * C)}", font_size=54, color=YELLOW).next_to(total, DOWN, buff=0.4)
        self.play(Write(side))
        self.wait(0.6)
        rule = Text("a² + b² = c²", font_size=72, color=WHITE).move_to(total)
        self.play(Transform(VGroup(total, side), rule))
        self.wait(1.2)
