"""Put a hero Short together (20 Nov 2026): rendered shot frames + graphics + captions + narration.

    python tools/blender/hero/compose.py <name> <frames_dir>

<frames_dir>/s0, s1, ... hold each shot's PNG frames from shots.py. The graphics are drawn per frame in
step with the 3D (the gauge fills exactly as the bones turn red), using the same curves shots.py keys.
Captions, voice polish, ducked music, loudness and the corner logo are the channel's own (agents/editor),
and sound and picture are made separately then joined by copying, as editor.render does (15 Nov rule).
"""
import json
import math
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agents import editor          # noqa: E402
from agents.core import config     # noqa: E402

FPS = 30
W, H = 1080, 1920
YEL, WHITE, BLACK, RED, CYAN, GREEN = (255, 222, 0), (255, 255, 255), (0, 0, 0), (255, 50, 40), (80, 220, 255), (90, 230, 120)
CLEAR = 800   # graphics stay above this line; the captions own the band around 0.62 x height
FONT = str(ROOT / "assets" / "fonts" / "ArchivoBlack-Regular.ttf")
_F = {}


def font(size):
    if size not in _F:
        _F[size] = ImageFont.truetype(FONT, size)
    return _F[size]


def text(d, xy, s, size, fill=WHITE, anchor="mm", stroke=10):
    if size < 4:
        return
    d.text(xy, s, font=font(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=BLACK)


def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def pop(f, f0, dur=6):
    """0 -> 1.15 -> 1 scale for a label appearing at frame f0."""
    t = (f - f0) / dur
    if t < 0:
        return 0.0
    return 1.0 + 0.15 * math.sin(min(1.0, t) * math.pi) if t < 1 else 1.0


# ---------------------------------------------------------------- one drawer per template
def g_run_at_camera(d, f, n, shot):
    hold = int(shot.get("freeze_s", 0.5) * FPS)
    f0 = n - hold
    if f >= f0:
        s = pop(f, f0, 5)
        text(d, (W / 2, H * 0.30), "COULDN'T", int(150 * s), RED, stroke=12)
        text(d, (W / 2, H * 0.30 + 165 * s), "RUN?", int(190 * s), WHITE, stroke=14)


def g_size_tower(d, f, n, shot):
    cars = shot.get("cars", 6)
    step = max(4, int((n * 0.75) / cars))
    landed = sum(1 for i in range(cars) if f >= 1 + i * step + 6)
    if landed:
        s = pop(f, 1 + (landed - 1) * step + 6, 5)
        text(d, (W * 0.30, H * 0.20), str(landed), int(220 * s), YEL, stroke=14)
        text(d, (W * 0.30, H * 0.20 + 150), "CAR" if landed == 1 else "CARS", 90, WHITE)
    if landed == cars:
        f1 = 1 + (cars - 1) * step + 12
        if f >= f1:
            s = pop(f, f1, 6)
            text(d, (W * 0.70, H * 0.20 + 30), "= 1", int(110 * s), WHITE)
            text(d, (W * 0.70, H * 0.20 + 150), "T. REX", int(100 * s), YEL)


SPEC = {}
NICE = {"TAIL-TO-THIGH": "TAIL-TO-THIGH MUSCLE", "THIGH": "THIGH MUSCLES", "CALF": "CALF MUSCLES",
        "NECK": "NECK", "JAW": "JAW MUSCLES"}


def _groups_now(f, names, t0, t1):
    """The group that appeared last at frame f, on the same timetable shots.py uses."""
    n = len(names)
    cur = None
    for i, nm in enumerate(names):
        if f >= int(round((t0 + (t1 - t0) * i / max(1, n)) * FPS)) + 1:
            cur = (i, nm)
    return cur


def g_xray_scan(d, f, n, shot):
    c = SPEC["creature"]
    rv = shot.get("reveal") or {"bones": [0.3, n / FPS * 0.5], "muscles": [n / FPS * 0.5, n / FPS * 0.85]}
    text(d, (W / 2, 330), "COMPUTER MODEL", 72, CYAN, stroke=9)
    mg = shot.get("muscle_groups") or c["muscle_groups"]
    bg = shot.get("bone_groups") or c["bone_groups"]
    mus = _groups_now(f, mg, *rv["muscles"])
    bone = _groups_now(f, bg, *rv["bones"])
    if mus:
        i, nm = mus
        head, col, total = ("JAW MUSCLES" if mg == ["JAW"] else "MUSCLE BY MUSCLE"), (255, 110, 120), len(mg)
    elif bone:
        i, nm = bone
        head, col, total = "BONE BY BONE", WHITE, len(bg)
    else:
        return
    text(d, (W / 2, 420), head, 58, col, stroke=8)
    p = (i + 1) / total                   # progress through this list
    d.rounded_rectangle([W / 2 - 300, 470, W / 2 + 300, 486], 8, fill=(20, 40, 60))
    d.rounded_rectangle([W / 2 - 300, 470, W / 2 - 300 + int(600 * p), 486], 8, fill=col)
    label = "SKULL + TEETH" if nm == "SKULL" else NICE.get(nm, nm) if mus else nm
    text(d, (W / 2, 545), label, 64 if len(label) < 16 else 52, YEL, stroke=9)


def g_stress_run(d, f, n, shot):
    st = lerp(0.05, 1.0, (f - 1) / (n * 0.7 - 1))
    x0, y0, y1, w = W - 190, 330, 1050, 90          # vertical gauge on the right
    d.rounded_rectangle([x0 - 8, y0 - 8, x0 + w + 8, y1 + 8], 20, fill=BLACK)
    d.rounded_rectangle([x0, y0, x0 + w, y1], 14, fill=(30, 30, 30))
    top = y1 - (y1 - y0) * st
    col = GREEN if st < 0.45 else YEL if st < 0.8 else RED
    d.rounded_rectangle([x0, top, x0 + w, y1], 14, fill=col)
    d.line([x0 - 20, y0 + (y1 - y0) * 0.15, x0 + w + 20, y0 + (y1 - y0) * 0.15], fill=WHITE, width=6)
    text(d, (x0 + w / 2, y0 - 120), "BONE", 52, WHITE, stroke=8)
    text(d, (x0 + w / 2, y0 - 60), "STRESS", 52, WHITE, stroke=8)
    if st > 0.85:
        blink = (f // 4) % 2 == 0
        text(d, (x0 - 230, y0 + (y1 - y0) * 0.15), "BREAK!", 110, RED if blink else WHITE, stroke=12)


def g_muscle_needed(d, f, n, shot):
    g0, g1, g2, g3 = (n * p for p in (0.08, 0.35, 0.68, 0.88))
    grow = ease((f - g0) / (g1 - g0)) if f < g2 else 1 - ease((f - g2) / (g3 - g2))
    x0, x1, y = 90, W - 90, 330
    text(d, (W / 2, y - 80), "LEG MUSCLE NEEDED", 64, WHITE, stroke=9)
    d.rounded_rectangle([x0 - 8, y - 8, x1 + 8, y + 78], 20, fill=BLACK)
    d.rounded_rectangle([x0, y, x1, y + 70], 14, fill=(40, 20, 25))
    need = 0.43
    d.rounded_rectangle([x0, y, x0 + (x1 - x0) * need * grow, y + 70], 14, fill=RED)
    if f >= g1 - 4:
        text(d, (x0 + (x1 - x0) * need + 30, y + 35), "40%+", 80, YEL, anchor="lm", stroke=10)
        text(d, (W / 2, y + 150), "of its whole body", 54, WHITE, stroke=8)
    if f >= g2 + (g3 - g2) * 0.5:
        s = pop(f, g2 + (g3 - g2) * 0.5, 6)
        text(d, (W / 2, 600), "T. REX HAD", int(84 * s), WHITE, stroke=11)
        text(d, (W / 2, 705), "FAR LESS", int(110 * s), YEL, stroke=12)


def g_speed_track(d, f, n, shot):
    kmh = shot["kmh"]
    cx, cy, r = W / 2, 520, 250
    d.ellipse([cx - r - 12, cy - r - 12, cx + r + 12, cy + r + 12], fill=BLACK)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(25, 25, 30))
    top = 100                                            # dial 0..100 km/h over 240 degrees
    for v in range(0, top + 1, 10):
        a = math.radians(210 - 240 * v / top)
        o, i_ = r - 15, r - (55 if v % 20 == 0 else 35)
        d.line([cx + o * math.cos(a), cy - o * math.sin(a), cx + i_ * math.cos(a), cy - i_ * math.sin(a)],
               fill=WHITE, width=7 if v % 20 == 0 else 4)
        if v % 20 == 0:
            text(d, (cx + (r - 95) * math.cos(a), cy - (r - 95) * math.sin(a)), str(v), 40, WHITE, stroke=0)
    shown = kmh * ease(f / (FPS * 0.8)) + (0.6 * math.sin(f / 3) if f > FPS * 0.8 else 0)
    a = math.radians(210 - 240 * shown / top)
    d.line([cx, cy, cx + (r - 40) * math.cos(a), cy - (r - 40) * math.sin(a)], fill=RED, width=14)
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=RED)
    text(d, (cx, cy + 135), f"{round(shown)} km/h", 78, YEL, stroke=10)
    text(d, (cx, cy - r - 70), "TOP SPEED", 64, WHITE, stroke=9)


def g_race_pass(d, f, n, shot):
    s = pop(f, 3, 6)
    for k, (lbl, v, col) in enumerate((("T. REX", shot["kmh"], YEL), ("CAR", shot["car_kmh"], CYAN))):
        y = 300 + k * 170
        d.rounded_rectangle([70, y - 70, W - 70, y + 70], 30, fill=BLACK)
        text(d, (120, y), lbl, int(72 * s), col, anchor="lm", stroke=0)
        text(d, (W - 120, y), f"{v} km/h", int(80 * s), WHITE, anchor="rm", stroke=0)


def g_closeup_roar(d, f, n, shot):
    pass


def g_none(d, f, n, shot):
    pass


def _graph(d, f, n, curves, hit):
    """Force on the people inside against time. Both curves hold the same area (same change in speed):
    a stiff stop is a tall, narrow spike; a folding stop is low and wide."""
    x0, y0, x1, y1 = 110, 300, W - 90, 880
    d.rounded_rectangle([x0 - 30, y0 - 90, x1 + 30, y1 + 70], 26, fill=(0, 0, 0, 200))
    d.line([x0, y1, x1, y1], fill=WHITE, width=5)
    d.line([x0, y0, x0, y1], fill=WHITE, width=5)
    text(d, (x0 + 10, y0 - 50), "FORCE ON YOU", 46, WHITE, anchor="lm", stroke=0)
    text(d, (x1, y1 + 40), "TIME", 42, WHITE, anchor="rm", stroke=0)
    t = max(0.0, (f - hit) / (FPS * 1.2))          # the graph draws itself after the hit
    for width, colr, lbl in curves:
        height = 0.08 / width                        # area = height x width stays the same
        pts = []
        for i in range(0, 101):
            u = i / 100
            if u > t:
                break
            g = math.sin(math.pi * (u - 0.12) / width) if 0.12 <= u <= 0.12 + width else 0.0   # both start at impact
            pts.append((x0 + (x1 - x0) * u, y1 - (y1 - y0) * min(1.0, height) * g))
        if len(pts) > 1:
            d.line(pts, fill=colr, width=12, joint="curve")
        if t > 0.6:
            ly = max(y0 + 60, y1 - (y1 - y0) * min(1.0, height) * 0.6)
            text(d, (x0 + (x1 - x0) * (0.14 + width) + 20, ly), lbl, 46, colr, anchor="lm", stroke=7)


def g_same_speed(d, f, n, shot):
    s = pop(f, 4, 6)
    text(d, (W / 2, 330), "SAME CAR", int(90 * s), WHITE, stroke=11)
    text(d, (W / 2, 450), "SAME SPEED", int(90 * s), YEL, stroke=11)
    text(d, (W / 2, 590), "STIFF vs FOLDING", 66, CYAN, stroke=10)


def g_force_graph_rigid(d, f, n, shot):
    _graph(d, f, n, [(0.08, RED, "STIFF")], int(n * shot.get("hit_at", 0.25)))


def g_force_graph_both(d, f, n, shot):
    _graph(d, f, n, [(0.08, (120, 60, 60), "STIFF"), (0.5, CYAN, "FOLDING")], int(n * shot.get("hit_at", 0.25)) - 30)


def g_newton(d, f, n, shot):
    text(d, (W / 2, 300), "NEWTON'S SECOND LAW", 66, WHITE, stroke=9)
    s = pop(f, 10, 6)
    text(d, (W / 2, 450), "FORCE =", int(96 * s), YEL, stroke=11)
    text(d, (W / 2, 570), "CHANGE IN SPEED x MASS", int(58 * s), WHITE, stroke=9)
    d.line([160, 625, W - 160, 625], fill=WHITE, width=8)
    text(d, (W / 2, 690), "TIME TO STOP", int(64 * s), CYAN, stroke=9)
    if f > n * 0.55:
        s2 = pop(f, int(n * 0.55), 6)
        text(d, (W / 2, 780), "MORE TIME = LESS FORCE", int(66 * s2), YEL, stroke=10)


def g_history(d, f, n, shot):
    s = pop(f, 6, 6)
    text(d, (W / 2, 330), "PATENTED 1952", int(88 * s), WHITE, stroke=11)
    text(d, (W / 2, 440), "Bela Barenyi", int(58 * s), CYAN, stroke=8)
    if f > n * 0.5:
        s2 = pop(f, int(n * 0.5), 6)
        text(d, (W / 2, 590), "FIRST PRODUCTION CAR: 1959", int(60 * s2), YEL, stroke=9)


def g_cars_force(d, f, n, shot):
    """'like three small cars stacked on its teeth': the count as each car lands, then ONE BITE."""
    cars = shot.get("cars", 3)
    step = max(4, int((n * 0.75) / cars))
    landed = sum(1 for i in range(cars) if f >= 1 + i * step + 6)
    if landed:
        s = pop(f, 1 + (landed - 1) * step + 6, 5)
        text(d, (W / 2, 330), f"{landed} SMALL CAR{'S' if landed > 1 else ''}", int(96 * s), YEL, stroke=12)
    if landed == cars and f > n * 0.8:
        s = pop(f, int(n * 0.8), 6)
        text(d, (W / 2, 460), "= ONE BITE", int(110 * s), RED, stroke=12)


def g_bite_compare(d, f, n, shot):
    """Bars: the strongest bite ever measured (saltwater crocodile) against the T. rex estimate."""
    rows = shot["bars"]                    # [[label, newtons, colour-name], ...]
    top = max(v for _, v, _ in rows)
    text(d, (W / 2, 300), "BITE FORCE", 80, WHITE, stroke=10)
    for k, (lbl, v, col) in enumerate(rows):
        y = 430 + k * 210
        t0 = 6 + k * int(n * 0.28)
        grow = ease((f - t0) / (FPS * 0.9))
        if f < t0:
            continue
        colr = {"cyan": CYAN, "red": RED, "yellow": YEL}[col]
        text(d, (90, y), lbl, 54, colr, anchor="lm", stroke=8)
        d.rounded_rectangle([90, y + 45, 90 + int((W - 180) * v / top * grow), y + 125], 18, fill=colr)
        text(d, (W - 90, y + 85), f"{int(v * grow):,} N", 58, WHITE, anchor="rm", stroke=8)
    if f > n * 0.7:
        s = pop(f, int(n * 0.7), 6)
        text(d, (W / 2, 430 + len(rows) * 210 + 40), "MORE THAN 2x", int(96 * s), YEL, stroke=11)


def g_tooth_pressure(d, f, n, shot):
    st = lerp(0.1, 1.0, (f - n * 0.25) / (n * 0.5))
    x0, y0, x1 = 90, 330, W - 90
    text(d, (W / 2, y0 - 70), "PRESSURE AT THE TOOTH TIP", 58, WHITE, stroke=9)
    d.rounded_rectangle([x0 - 8, y0 - 8, x1 + 8, y0 + 78], 20, fill=BLACK)
    col = GREEN if st < 0.45 else YEL if st < 0.8 else RED
    d.rounded_rectangle([x0, y0, x0 + int((x1 - x0) * st), y0 + 70], 14, fill=col)
    if st > 0.85:
        blink = (f // 4) % 2 == 0
        text(d, (W / 2, y0 + 170), "SHATTERS BONE", 96, RED if blink else WHITE, stroke=12)


def g_coprolite(d, f, n, shot):
    text(d, (W / 2, 320), "FOSSIL POOP", 96, YEL, stroke=12)
    text(d, (W / 2, 420), "likely from a T. rex", 52, WHITE, stroke=8)
    if f > n * 0.6:
        s = pop(f, int(n * 0.6), 6)
        text(d, (W / 2, 560), "30-50% BONE", int(110 * s), WHITE, stroke=12)



STOP = set("a an the and or but so of to in on at by for from with as is are was were be been it its it's that this "
           "then than up out about into onto over".split())


def hero_captions(words, path):
    """21 Nov 2026, owner: the captions looked like they kept re-writing. Each card is at most TWO words,
    shown once for exactly as long as they are spoken (no word-by-word recolouring), the key word in yellow.
    Uses the channel's own caption style (font, outline, position), so Hindi keeps its font and shaping."""
    editor.captions([], path)                       # the channel's header and styles, no events
    head = path.read_text(encoding="utf-8")
    c, f = config()["captions"], config()["format"]
    norm = lambda w: re.sub(r"[^\w']", "", w.lower())
    cards, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        gap = words[i + 1]["start"] - w["end"] if i + 1 < len(words) else 9
        long_word = len(w["text"]) >= 9
        if len(cur) >= 2 or long_word or gap > 0.18 or w["text"].rstrip().endswith((".", ",", "?", "!", ";", ":", "\u0964")):
            cards.append(cur)
            cur = []
    if cur:
        cards.append(cur)
    lines = []
    for k, card in enumerate(cards):
        a = card[0]["start"]
        nxt = cards[k + 1][0]["start"] if k + 1 < len(cards) else card[-1]["end"] + 0.5
        b = nxt if nxt - card[-1]["end"] < 0.3 else card[-1]["end"] + 0.2
        keys = [g for g in card if norm(g["text"]) not in STOP]
        key = max(keys, key=lambda g: len(g["text"])) if keys else None
        txt = " ".join(("{\\c" + c["highlight"] + "}" + g["text"].upper() + "{\\c" + c["color"] + "}") if g is key
                       else g["text"].upper() for g in card)
        chars = sum(len(g["text"]) for g in card) + len(card) - 1
        size = int(c["size"] * 1.2)
        if chars > 11:
            size = max(int(c["size"] * 1.2 * 11 / chars), int(c["size"] * 0.75))
        lines.append(f"Dialogue: 0,{editor._ass_time(a)},{editor._ass_time(b)},Cap,,0,0,0,,"
                     f"{{\\pos({f['width'] // 2},{c['position_y']})\\fs{size}}}{txt}")
    path.write_text(head.rstrip("\n") + "\n" + "\n".join(lines) + "\n", encoding="utf-8")


def g_label(d, f, n, shot):
    """One or two lines of text from the spec, popped in: shot['label'] = ["LINE 1", "LINE 2"]."""
    s = pop(f, 4, 6)
    for k, line in enumerate(shot.get("label", [])):
        size = 96 if k == 0 else 70
        while size > 40 and font(size).getlength(line) > W - 140:     # always fits the width
            size -= 4
        text(d, (W / 2, 330 + k * 115), line, int(size * s), YEL if k == 0 else WHITE, stroke=11)


def g_grow(d, f, n, shot):
    a0, a1 = shot.get("ages", [14, 18])
    g0, g1 = n * 0.12, n * 0.85
    age = a0 + (a1 - a0) * ease((f - g0) / (g1 - g0))
    text(d, (W / 2, 320), f"AGE {age:.0f}", 120, YEL, stroke=13)
    text(d, (W / 2, 450), "+2 kg EVERY DAY", 80, WHITE, stroke=10)
    if f > g1:
        s = pop(f, int(g1), 6)
        text(d, (W / 2, 570), "SEVERAL TONNES", int(80 * s), CYAN, stroke=10)


def _brake_chips(d, shot, show_dist):
    sp = shot.get("speeds", [30, 60])
    dec = shot.get("decels") or [shot.get("decel", 7.0)] * len(sp)
    names = shot.get("lane_names") or [f"{kmh} km/h" for kmh in sp]
    for k, kmh in enumerate(sp):
        x = W * (0.27 + 0.46 * k)
        d.rounded_rectangle([x - 220, 255, x + 220, 395], 28, fill=BLACK)
        text(d, (x, 300), names[k], 62, YEL if k == 0 else CYAN if shot.get("lane_names") else RED, stroke=0)
        if show_dist:
            dist = (kmh / 3.6) ** 2 / (2 * dec[k])
            text(d, (x, 360), f"stops in ~{dist:.0f} m", 44, WHITE, stroke=0)


def g_brake_speeds(d, f, n, shot):
    _brake_chips(d, shot, False)


def g_brake_result(d, f, n, shot):
    sp = shot.get("speeds", [30, 60])
    dec = shot.get("decels") or [shot.get("decel", 7.0)] * len(sp)
    t_end = int(n * shot.get("brake_at", 0.3)) + int(max(v / 3.6 / a for v, a in zip(sp, dec)) * FPS)
    _brake_chips(d, shot, f > int(n * shot.get("brake_at", 0.3)) + 8)
    if f > t_end:
        s = pop(f, t_end, 6)
        text(d, (W / 2, 500), shot.get("result_text", "4x THE DISTANCE"), int(96 * s), RED, stroke=12)


def g_bars(d, f, n, shot):
    """Generic comparison bars: shot['bars'] = [[label, value, colour], ...], shot['unit'], shot['title']."""
    rows = shot["bars"]
    top = max(v for _, v, _ in rows)
    text(d, (W / 2, 300), shot.get("title", ""), 76, WHITE, stroke=10)
    for k, (lbl, v, col) in enumerate(rows):
        y = 420 + k * 190
        t0 = 6 + k * int(n * 0.25)
        if f < t0:
            continue
        grow = ease((f - t0) / (FPS * 0.9))
        colr = {"cyan": CYAN, "red": RED, "yellow": YEL, "white": WHITE}[col]
        text(d, (90, y), lbl, 52, colr, anchor="lm", stroke=8)
        d.rounded_rectangle([90, y + 40, 90 + int((W - 180) * v / top * grow), y + 115], 18, fill=colr)
        text(d, (W - 90, y + 78), f"~{v:g} {shot.get('unit', '')}", 56, WHITE, anchor="rm", stroke=8)


def g_energy(d, f, n, shot):
    text(d, (W / 2, 300), "MOVING ENERGY", 84, WHITE, stroke=10)
    s = pop(f, 10, 6)
    text(d, (W / 2, 420), "= 1/2 x MASS x SPEED\u00b2", int(72 * s), YEL, stroke=10)


def g_four(d, f, n, shot):
    rows = [("2x SPEED", WHITE), ("4x ENERGY", YEL), ("4x BRAKING DISTANCE", RED)]
    for k, (t_, col) in enumerate(rows):
        f0 = 6 + k * int(n * 0.22)
        if f >= f0:
            s = pop(f, f0, 6)
            text(d, (W / 2, 320 + k * 120), t_, int(84 * s), col, stroke=11)


def g_react(d, f, n, shot):
    s = pop(f, 6, 6)
    text(d, (W / 2, 320), "+ THINKING DISTANCE", int(66 * s), YEL, stroke=10)
    text(d, (W / 2, 420), "the car keeps going", int(52 * s), WHITE, stroke=8)
    text(d, (W / 2, 485), "while you react", int(52 * s), WHITE, stroke=8)

# ---------------------------------------------------------------- assembly
def run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, check=True)


def main():
    name, frames = sys.argv[1], Path(sys.argv[2])
    d = ROOT / "research" / "hero" / name
    spec = json.loads((d / "spec.json").read_text(encoding="utf-8"))
    SPEC.update(spec)
    words = json.loads((d / "words.json").read_text(encoding="utf-8"))
    job = ROOT / "jobs" / f"_hero_compose_{name}"
    shutil.rmtree(job, ignore_errors=True)
    (job / "ov").mkdir(parents=True)
    shutil.copy(d / "voice.mp3", job / "voice.mp3")
    # 1) each shot's frames -> one clip; the clips joined
    segs, gf = [], 0
    for i, shot in enumerate(spec["shots"]):
        n = int(round(shot["seconds"] * FPS))
        src = frames / f"s{i}"
        have = len(list(src.glob("*.png")))
        if have < n:
            raise SystemExit(f"shot {i}: {have} of {n} frames rendered")
        run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(src / "%05d.png"),
             "-frames:v", str(n), "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p",
             f"shot{i}.mp4"], job)
        segs.append(f"shot{i}.mp4")
        draw = globals()[f"g_{shot.get('overlay') or shot['kind']}"]
        for f in range(1, n + 1):          # 2) the graphics, frame by frame, in step with the 3D
            im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            draw(ImageDraw.Draw(im), f, n, shot)
            im.save(job / "ov" / f"{gf + f:05d}.png", optimize=False, compress_level=1)
        gf += n
    (job / "list.txt").write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy",
         "visual.mp4"], job)
    # 3) captions in the channel's own style
    # 21 Nov 2026, owner: keep the channel's own caption lines (same wording and grouping), just SMALLER
    from agents.core import set_override
    cap = dict(config()["captions"])
    cap["size"] = int(cap["size"] * float(spec.get("caption_scale", 0.8)))
    set_override({"captions": cap})
    editor.captions(words, job / "captions.ass")
    set_override({})
    shutil.copytree(ROOT / "assets" / "fonts", job / "fonts", dirs_exist_ok=True)
    # 4) sound on its own: polished voice + ducked music, levelled
    total = gf / FPS
    music = sorted((ROOT / "assets" / "music").glob("*.mp3"))
    vol = config()["music"]["volume"]
    voice_s = editor._dur(job / "voice.mp3")
    if music:
        random.seed(name)
        audio = (f"[0:a]{editor.VOICE_POLISH},apad,asplit=2[vo][key];[1:a]volume={vol}[m0];"
                 f"[m0][key]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=450[m];"
                 f"[vo][m]amix=inputs=2:duration=shortest:dropout_transition=0:normalize=0,"
                 f"atrim=0:{{total:.3f}},afade=t=out:st={{fade:.3f}}:d=0.9,{editor.LOUDNESS}[a]")
        ains = ["-i", "voice.mp3", "-stream_loop", "-1", "-i", str(random.choice(music))]
        audio = audio.format(total=total, fade=max(0.0, total - 0.9))
    else:
        audio, ains = f"[0:a]{editor.VOICE_POLISH},{editor.LOUDNESS}[a]", ["-i", "voice.mp3"]
    run(["ffmpeg", "-y", "-loglevel", "error"] + ains + ["-filter_complex", audio + ";[a]apad[ap]", "-map", "[ap]",
         "-t", f"{total:.3f}", "-c:a", "aac", "-b:a", "160k", "sound.m4a"], job)
    # 5) picture: 3D + graphics, scaled to 2K, captions and logo drawn crisp at full size
    f = config()["format"]
    k = max(1.0, float(f.get("upload_short_side", 1080)) / 1080)
    UW, UH = int(W * k) // 2 * 2, int(H * k) // 2 * 2
    own = config()["channel"].get("logo")
    logo = ROOT / own if own else ROOT / "assets" / "brand" / "logo-800.png"
    vin = ["-i", "visual.mp4", "-framerate", str(FPS), "-i", "ov/%05d.png"]
    chain = (f"[0:v][1:v]overlay=0:0:format=auto[g];[g]scale={UW}:{UH}:flags=lanczos,noise=alls=3:allf=t,"
             f"ass=captions.ass:fontsdir=fonts[c]")
    if logo.exists():
        vin += ["-i", str(logo)]
        size, pad = int(UW * 0.11), int(UW * 0.045)
        chain += f";[2:v]scale={size}:-1,format=rgba,colorchannelmixer=aa=0.85[lg];[c][lg]overlay={pad}:{int(UH * 0.06)}[v]"
    else:
        chain = chain.replace("[c]", "[v]")
    run(["ffmpeg", "-y", "-loglevel", "error"] + vin + ["-filter_complex", chain, "-map", "[v]", "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "picture.mp4"], job)
    # 6) join by copying
    out = d / f"{name}.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", "picture.mp4", "-i", "sound.m4a", "-map", "0:v", "-map", "1:a",
         "-c", "copy", "-shortest", "-movflags", "+faststart", str(out)], job)
    print(f"hero: {out} ({total:.1f}s picture, {voice_s:.1f}s voice)")


if __name__ == "__main__":
    main()
