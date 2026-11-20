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
    mus = _groups_now(f, c["muscle_groups"], *rv["muscles"])
    bone = _groups_now(f, c["bone_groups"], *rv["bones"])
    if mus:
        i, nm = mus
        head, col, total = "MUSCLE BY MUSCLE", (255, 110, 120), len(c["muscle_groups"])
    elif bone:
        i, nm = bone
        head, col, total = "BONE BY BONE", WHITE, len(c["bone_groups"])
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
        text(d, (W / 2, H * 0.62), "T. REX HAD", int(90 * s), WHITE, stroke=11)
        text(d, (W / 2, H * 0.62 + 110), "FAR LESS", int(120 * s), YEL, stroke=12)


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


def g_cars_force(d, f, n, shot):
    """'like three small cars stacked on its teeth': the count as each car lands, then the bite force."""
    g_size_tower(d, f, n, shot)
    if f > n * 0.8:
        s = pop(f, int(n * 0.8), 6)
        text(d, (W / 2, H * 0.62), "ONE BITE", int(110 * s), RED, stroke=12)


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
        text(d, (W / 2, H * 0.64), "30-50% BONE", int(110 * s), WHITE, stroke=12)


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
    editor.captions(words, job / "captions.ass")
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
