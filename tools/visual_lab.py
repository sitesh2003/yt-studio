"""Visual lab (17-18 Nov 2026, owner: "the drawings and animations are not that great ... stickman animations
... or use open source publications' pictures"). Makes SAMPLES only, for the owner to compare before anything
goes into the daily videos:
    python tools/visual_lab.py figures    -> research/visual_lab/fig_*.mp4  (one panel of a CC BY paper figure)
    python tools/visual_lab.py stick      -> research/visual_lab/stick_*.mp4 (the rigged stick character)
"""
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "research" / "visual_lab"
W, H, FPS = 1080, 1920, 30
FONT = str(ROOT / "assets" / "fonts" / "ArchivoBlack-Regular.ttf")
CAP_TOP = 1060          # the spoken captions sit around y 1180: nothing important goes below this line


def _font(size):
    return ImageFont.truetype(FONT, size)


def _pipe(path, frames, audio=None):
    """Write frames (PIL images) to an H.264 MP4 through ffmpeg."""
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if audio:
        cmd += ["-i", str(audio), "-shortest", "-c:a", "aac", "-b:a", "128k"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", str(path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for im in frames:
        p.stdin.write(im.convert("RGB").tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg failed")


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------------------------------------- figures
FIG_CLIPS = [  # file, crop box as fractions (x0, y0, x1, y1), the line it would sit under, panel note
    ("fingers_photo", (0, 0, 1, 1), "Scientists tested it: people gripped this sensor with dry, wet and wrinkly fingers.", "Figure 1"),
    ("dino_photo", (0.0, 0.0, 0.62, 0.41), "The fossil: an injured dinosaur rib.", "Figure 1A, cropped"),
    ("dino_ct", (0.392, 0.385, 1.0, 0.735), "Inside it, a scan found vessel-like structures still in the bone.", "Figure 3F, cropped"),
]


def figure_clip(name, box, line, note, credit, secs=6.0):
    src = Image.open(OUT / "figs" / f"{name}.jpg").convert("RGB")
    x0, y0, x1, y1 = box
    crop = src.crop((int(x0 * src.width), int(y0 * src.height), int(x1 * src.width), int(y1 * src.height)))
    # the panel fills the frame width above the caption band; upscaled with LANCZOS, then lightly sharpened
    room_w, room_h = W - 80, CAP_TOP - 300
    s = min(room_w / crop.width, room_h / crop.height)
    pic = crop.resize((int(crop.width * s), int(crop.height * s)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
    bg = Image.new("RGB", (W, H), (14, 18, 32))
    d = ImageDraw.Draw(bg)
    tag = "FROM THE REAL STUDY"
    f1 = _font(46)
    tw = d.textlength(tag, font=f1)
    d.rounded_rectangle(((W - tw) / 2 - 28, 120, (W + tw) / 2 + 28, 196), 38, fill=(255, 214, 0))
    d.text((W / 2, 158), tag, font=f1, fill=(14, 18, 32), anchor="mm")
    f2 = _font(30)
    for k, txt in enumerate((credit, note)):
        d.text((W / 2, H - 150 + k * 46), txt, font=f2, fill=(200, 206, 222), anchor="mm")
    frames = []
    n = int(secs * FPS)
    for i in range(n):
        z = 1.0 + 0.07 * ease(i / (n - 1))           # slow push-in, never a jump
        pw, ph = int(pic.width * z), int(pic.height * z)
        p2 = pic.resize((pw, ph), Image.BILINEAR)
        # crop back to the room so the picture never grows into the caption band
        cw, ch = min(pw, room_w), min(ph, room_h)
        p2 = p2.crop(((pw - cw) // 2, (ph - ch) // 2, (pw - cw) // 2 + cw, (ph - ch) // 2 + ch))
        fr = bg.copy()
        top = 260 + (room_h - ch) // 2
        fr.paste(p2, ((W - cw) // 2, top))
        frames.append(fr)
    _pipe(OUT / f"fig_{name}.mp4", frames)
    frames[n // 2].save(OUT / f"fig_{name}.jpg", quality=88)


def figures():
    picks = json.loads((OUT / "figs" / "picks.json").read_text(encoding="utf-8"))
    for name, box, line, note in FIG_CLIPS:
        figure_clip(name, box, line, note, picks[name]["credit"])
        print("made", name)


# ----------------------------------------------------------------------------------------------- stick figure
# A rigged stick character: every pose is a set of joint angles (degrees, 0 = pointing down, positive =
# towards the viewer's right), so moving from one pose to the next is a smooth turn of every joint, not a
# swap of drawings. The body squashes a little on landing and leans into a move (the animator's basics:
# ease in/out, anticipation, follow-through, a small overshoot).
POSES = {   # forearm direction = shoulder angle + elbow angle; checked so no arm passes through the head
    "stand": dict(lean=0, neck=0, l_sh=-12, l_el=4, r_sh=12, r_el=-4, l_hip=-6, l_kn=0, r_hip=6, r_kn=0, face="smile"),
    "wave":  dict(lean=-3, neck=-4, l_sh=-12, l_el=4, r_sh=120, r_el=40, l_hip=-6, l_kn=0, r_hip=6, r_kn=0, face="happy"),
    "think": dict(lean=4, neck=10, l_sh=-15, l_el=5, r_sh=12, r_el=158, l_hip=-4, l_kn=0, r_hip=8, r_kn=4, face="think"),
    "point": dict(lean=-6, neck=-6, l_sh=-10, l_el=4, r_sh=92, r_el=0, l_hip=-8, l_kn=0, r_hip=10, r_kn=0, face="talk"),
    "shock": dict(lean=-8, neck=-10, l_sh=-110, l_el=-30, r_sh=110, r_el=30, l_hip=-14, l_kn=0, r_hip=14, r_kn=0, face="shock"),
    "grip":  dict(lean=8, neck=8, l_sh=-20, l_el=-10, r_sh=60, r_el=-12, l_hip=-10, l_kn=10, r_hip=10, r_kn=-10, face="effort"),
    "slip":  dict(lean=-16, neck=-14, l_sh=-125, l_el=-20, r_sh=95, r_el=30, l_hip=-28, l_kn=22, r_hip=36, r_kn=-12, face="shock"),
    "cheer": dict(lean=0, neck=-8, l_sh=-135, l_el=-12, r_sh=135, r_el=12, l_hip=-10, l_kn=0, r_hip=10, r_kn=0, face="happy"),
}
INK = (20, 24, 40)


def _blend(a, b, t):
    out = {k: a[k] + (b[k] - a[k]) * t for k in a if k != "face"}
    out["face"] = a["face"] if t < 0.5 else b["face"]
    return out


def _seg(x, y, ang, length):
    r = math.radians(ang)
    return x + math.sin(r) * length, y + math.cos(r) * length


def draw_stick(d, cx, ground, p, scale=1.0, squash=0.0, color=INK):
    """Draw the character with its feet on `ground` at x = cx."""
    S = scale
    th, sh_len, arm1, arm2, leg1, leg2, head_r = 230 * S, 0, 120 * S, 110 * S, 150 * S, 150 * S, 62 * S
    lw = int(16 * S)
    torso = th * (1 - squash)
    hip = (cx, ground - (leg1 + leg2) * (1 - squash * 0.6))
    lean = math.radians(p["lean"])
    neck = (hip[0] + math.sin(lean) * torso, hip[1] - math.cos(lean) * torso)
    sh = (hip[0] + math.sin(lean) * torso * 0.80, hip[1] - math.cos(lean) * torso * 0.80)
    j = dict(joint="curve", width=lw, fill=color)
    d.line([hip, neck], **j)
    for side in ("l", "r"):
        e = _seg(*sh, p[f"{side}_sh"], arm1)
        h = _seg(*e, p[f"{side}_sh"] + p[f"{side}_el"], arm2)
        d.line([sh, e, h], **j)
        k = _seg(*hip, p[f"{side}_hip"], leg1 * (1 - squash * 0.3))
        f = _seg(*k, p[f"{side}_hip"] + p[f"{side}_kn"], leg2 * (1 - squash * 0.3))
        d.line([hip, k, f], **j)
        d.line([f, (f[0] + (14 if side == "r" else -14) * S, f[1])], **j)
    for pt in (sh, hip):
        d.ellipse((pt[0] - lw / 2, pt[1] - lw / 2, pt[0] + lw / 2, pt[1] + lw / 2), fill=color)
    hx, hy = _seg(*neck, 180 + p["neck"], head_r + 6 * S)
    d.ellipse((hx - head_r, hy - head_r, hx + head_r, hy + head_r), outline=color, width=lw, fill=(255, 255, 255))
    face = p["face"]
    ey = hy - 10 * S
    for sx in (-20, 20):
        if face == "think" and sx < 0:
            d.line([(hx + sx * S - 9 * S, ey), (hx + sx * S + 9 * S, ey)], fill=color, width=int(7 * S))
        elif face in ("happy", "cheer"):
            d.arc((hx + sx * S - 11 * S, ey - 8 * S, hx + sx * S + 11 * S, ey + 10 * S), 200, 340, fill=color, width=int(7 * S))
        else:
            r = (11 if face == "shock" else 8) * S
            d.ellipse((hx + sx * S - r, ey - r, hx + sx * S + r, ey + r), fill=color)
    my = hy + 24 * S
    if face in ("smile", "happy"):
        d.arc((hx - 24 * S, my - 18 * S, hx + 24 * S, my + 14 * S), 20, 160, fill=color, width=int(7 * S))
    elif face == "shock":
        d.ellipse((hx - 13 * S, my - 12 * S, hx + 13 * S, my + 16 * S), outline=color, width=int(7 * S))
    elif face == "talk":
        d.chord((hx - 18 * S, my - 10 * S, hx + 18 * S, my + 14 * S), 0, 180, fill=color)
    elif face == "effort":
        d.line([(hx - 20 * S, my), (hx + 20 * S, my)], fill=color, width=int(7 * S))
    else:
        d.line([(hx - 12 * S, my + 2 * S), (hx + 14 * S, my - 4 * S)], fill=color, width=int(7 * S))
    if face == "think":   # a small "?" beside the head
        d.text((hx + head_r + 40 * S, hy - head_r - 10 * S), "?", font=_font(int(90 * S)), fill=(40, 110, 230), anchor="mm")
    return {"hand_r": h, "head": (hx, hy), "neck": neck}


def stick_scene(name, beats, props, secs, audio=None, title=None):
    """beats: [(time_s, pose)], the character moves between them with ease in/out and a small overshoot.
    props(d, t, joints) draws the objects for that moment."""
    frames = []
    n = int(secs * FPS)
    for i in range(n):
        t = i / FPS
        k = max([b for b in range(len(beats)) if beats[b][0] <= t] or [0])
        t0, p0 = beats[k]
        t1, p1 = beats[k + 1] if k + 1 < len(beats) else (t0 + 1, p0)
        dur = min(0.45, t1 - t0)                   # a move takes up to 0.45 s, then holds (a held pose reads)
        u = (t - t0) / dur if dur > 0 else 1
        u = min(u, 1.0)
        over = math.sin(min(u, 1) * math.pi) * 0.08 if u < 1 else 0   # overshoot on the way
        pose = _blend(POSES[p0], POSES[p1], ease(u) + over * (1 if k + 1 < len(beats) else 0)) if k + 1 < len(beats) and t >= t1 - dur else POSES[p0]
        if k + 1 < len(beats) and t >= t1 - dur:
            u2 = (t - (t1 - dur)) / dur
            pose = _blend(POSES[p0], POSES[p1], min(1.0, ease(u2) + math.sin(min(u2, 1) * math.pi) * 0.06))
        breathe = math.sin(t * 2 * math.pi / 2.4) * 0.012     # idle: the body is never frozen
        land = 0.0
        if k + 1 < len(beats) and 0 <= t - t1 < 0.0:
            land = 0.04
        im = Image.new("RGB", (W * 2 // 2, H), (250, 248, 242))
        d = ImageDraw.Draw(im)
        d.line([(60, 1000), (W - 60, 1000)], fill=(205, 200, 190), width=6)
        d.ellipse((380 - 120, 990, 380 + 120, 1012), fill=(226, 222, 212))
        joints = draw_stick(d, 380, 1000, pose, scale=1.2, squash=breathe + land)
        props(d, t, joints)
        if title:
            d.text((W / 2, 150), title, font=_font(58), fill=INK, anchor="mm")
        frames.append(im)
    _pipe(OUT / f"stick_{name}.mp4", frames, audio)
    frames[int(n * 0.55)].save(OUT / f"stick_{name}.jpg", quality=88)


def stick():
    blue, red = (40, 110, 230), (230, 60, 60)

    def props(d, t, j):
        # a wet marble on a table: it slips out of a smooth hand, the wrinkly hand holds it
        top = 610
        d.rectangle((600, top, 1000, top + 30), fill=(170, 130, 90))
        d.rectangle((620, top + 30, 642, 1000), fill=(150, 112, 78))
        d.rectangle((958, top + 30, 980, 1000), fill=(150, 112, 78))
        hx, hy = j["hand_r"]
        if t < 3.0:   # smooth fingers: the marble slides away across the table
            x = 760 + max(0, t - 1.5) * 150
            d.ellipse((x - 34, top - 68, x + 34, top), fill=blue, outline=INK, width=6)
            for k in range(3):
                d.ellipse((x - 70 - k * 30, top - 18, x - 60 - k * 30, top - 8), fill=(120, 170, 255))
            d.text((800, 470), "SMOOTH", font=_font(52), fill=red, anchor="mm")
        else:         # wrinkly fingertips: it stays in the hand
            if t < 3.8:
                d.ellipse((760 - 34, top - 68, 760 + 34, top), fill=blue, outline=INK, width=6)
            else:
                d.ellipse((hx - 34, hy - 64, hx + 34, hy + 4), fill=blue, outline=INK, width=6)
                for k in range(4):
                    d.arc((hx - 30 + k * 14, hy, hx - 18 + k * 14, hy + 16), 0, 180, fill=INK, width=4)
            d.text((800, 470), "WRINKLY = GRIP", font=_font(52), fill=(20, 140, 70), anchor="mm")

    beats = [(0.0, "stand"), (0.7, "point"), (1.3, "grip"), (2.0, "slip"), (2.9, "think"), (3.6, "grip"), (4.8, "wave"), (6.0, "wave")]
    stick_scene("marble", beats, props, 6.4)

    def props2(d, t, j):
        pass
    beats2 = [(0, "stand"), (0.6, "wave"), (1.6, "think"), (2.6, "point"), (3.4, "shock"), (4.4, "cheer"), (5.4, "stand"), (6.0, "stand")]
    stick_scene("poses", beats2, props2, 6.2)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    OUT.mkdir(parents=True, exist_ok=True)
    if which in ("figures", "all"):
        figures()
    if which in ("stick", "all"):
        stick()
