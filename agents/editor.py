"""Agent 4c - Editing: cut clips to the voice timeline, burn word-by-word
captions, mix music, render a vertical MP4 and a thumbnail. FFmpeg only."""
import random

from PIL import Image, ImageDraw, ImageFont

from .core import ASSETS, config, log, run


def _ass_time(t):
    h, rem = divmod(max(t, 0), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def captions(words, path, overlays=None):
    c, f = config()["captions"], config()["format"]
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {f['width']}
PlayResY: {f['height']}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Banner,{c['font']},{int(c['size']*0.95)},&H0000E5FF,&H0000E5FF,&H00000000,&HA0000000,0,0,0,0,100,100,2,0,3,10,0,8,40,40,{int(f['height']*0.12)},1
Style: Count,{c['font']},{int(c['size']*2.6)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,12,4,5,0,0,0,1
Style: Cap,{c['font']},{c['size']},{c['color']},{c['highlight']},&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,{c['outline']},3,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines, n = [], c["words_per_line"]
    quiet = [(a, b) for (a, b, _, st) in (overlays or []) if st == "Count"]  # big 3-2-1 replaces captions
    y = c["position_y"]
    # PHRASES, not fixed chunks: a line ends at punctuation (or n words), and it leaves the screen
    # when the voice pauses, so captions breathe with the narrator instead of rolling non-stop
    groups, cur = [], []
    for idx, w in enumerate(words):
        cur.append(w)
        gap = (words[idx + 1]["start"] - w["end"]) if idx + 1 < len(words) else 9
        if len(cur) >= n or gap > 0.15 or w["text"].rstrip().endswith((".", ",", "?", "!", ";", ":")):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    flat = 0
    for gi, group in enumerate(groups):
        i = flat
        flat += len(group)
        start = group[0]["start"]
        nxt = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else group[-1]["end"] + 0.4
        end = nxt if nxt - group[-1]["end"] < 0.25 else group[-1]["end"] + 0.15
        for j, w in enumerate(group):
            ws = w["start"] if j else start
            we = group[j + 1]["start"] if j + 1 < len(group) else end
            text = " ".join(("{\\c" + c["highlight"] + "}" + g["text"].upper() + "{\\c" + c["color"] + "}")
                            if k == j else g["text"].upper() for k, g in enumerate(group))
            chars = sum(len(g["text"]) for g in group) + len(group) - 1
            if chars > 15:  # shrink long lines so they never run off a phone screen
                text = "{\\fs" + str(max(int(c["size"] * 15 / chars), int(c["size"] * 0.7))) + "}" + text
            if any(qa - 0.05 <= ws < qb for qa, qb in quiet):
                continue
            lines.append(f"Dialogue: 0,{_ass_time(ws)},{_ass_time(we)},Cap,,0,0,0,,{{\\pos({f['width']//2},{y})}}{text}")
    for (a, b, text, style) in (overlays or []):
        pos = ("{\\pos(" + f"{f['width'] // 2},{int(f['height'] * 0.42)}" + ")\\fad(80,80)}") if style == "Count" else ""
        lines.append(f"Dialogue: 1,{_ass_time(a)},{_ass_time(b)},{style},,0,0,0,,{pos}{text}")
    path.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")


def predict_overlays(script, times, words):
    """PAUSE & GUESS banner over the predict scene, and a big 3-2-1 timed to the spoken words."""
    out = []
    nums = {"three": "3", "two": "2", "one": "1"}
    for sc, (a, b) in zip(script["scenes"], times):
        if not (sc.get("predict") or "pause and guess" in sc.get("narration", "").lower()):
            continue  # the spoken words are the trigger, so a rewrite can't lose the banner
        hits = [w for w in words if a - 0.05 <= w["start"] <= b and w["text"].lower().strip(".,!?") in nums]
        hits = hits[-3:]
        start = hits[0]["start"] - 1.2 if hits else max(a, b - 3.5)
        out.append((start, b + 0.15, "PAUSE & GUESS", "Banner"))
        for k, w in enumerate(hits):
            end = hits[k + 1]["start"] if k + 1 < len(hits) else w["end"] + 0.5
            out.append((w["start"], end, nums[w["text"].lower().strip(".,!?")], "Count"))
    return out


def _dims(path):
    """Width and height from ffmpeg's own stream line, so only ffmpeg is needed (no ffprobe)."""
    import re
    import subprocess
    try:
        err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path)], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=30).stderr
        m = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", err)
        return (int(m[1]), int(m[2])) if m else (0, 0)
    except Exception:
        return 0, 0


def _vf(path):
    """Fill the frame. A landscape clip on a vertical video is NOT centre-cropped (that cuts the
    subject out); it sits whole-ish in the middle over a blurred copy of itself - the format the
    biggest explainer Shorts use, and it lets us use the far larger pool of 16:9 stock footage."""
    f = config()["format"]
    W, H = f["width"], f["height"]
    w, h = _dims(path)
    tail = f"fps={f['fps']},setsar=1"
    if H > W and w and h and w / h > 0.9:
        fg_h = int(W * 0.8) // 2 * 2          # 16:9 shown 1.4x wider than the screen, sides trimmed
        return (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                f"boxblur=28:4,eq=brightness=-0.10:saturation=1.1[bg];"
                f"[b]scale=-2:{fg_h},crop='min(iw,{W})':{fg_h}[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2-{int(H*0.04)},{tail}")
    return f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},{tail}"


def render(clips, times, words, job_dir, overlays=None):
    segs = []
    for i, (clip, (a, b)) in enumerate(zip(clips, times)):
        seg = f"seg_{i:02d}.mp4"
        vf = _vf(job_dir / clip.name)
        run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", clip.name, "-t", f"{b - a:.3f}", "-filter_complex" if "[a]" in vf else "-vf", vf,
             "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", seg],
            cwd=job_dir)
        segs.append(seg)
    (job_dir / "list.txt").write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "visual.mp4"], cwd=job_dir)

    captions(words, job_dir / "captions.ass", overlays)
    import shutil
    shutil.copytree(ASSETS / "fonts", job_dir / "fonts", dirs_exist_ok=True)
    music = sorted((ASSETS / "music").glob("*.mp3"))
    cmd = ["ffmpeg", "-y", "-i", "visual.mp4", "-i", "voice.mp3"]
    # the channel logo as a small corner mark the whole way through: branding without an intro
    # card (a logo intro in the first 2 seconds makes people swipe away)
    logo = ASSETS / "brand" / "logo-800.png"
    f = config()["format"]
    vchain = "[0:v]ass=captions.ass:fontsdir=fonts[c]"
    if logo.exists():
        cmd += ["-i", str(logo)]
        li = 2
        size, pad = int(f["width"] * 0.11), int(f["width"] * 0.045)
        vchain += (f";[{li}:v]scale={size}:-1,format=rgba,colorchannelmixer=aa=0.85[lg]"
                   f";[c][lg]overlay={pad}:{int(f['height'] * 0.06)}[v]")
    else:
        vchain = vchain.replace("[c]", "[v]")
    if music:
        mi = 3 if logo.exists() else 2
        cmd += ["-stream_loop", "-1", "-i", str(random.choice(music))]
        vol = config()["music"]["volume"]
        audio = f"[{mi}:a]volume={vol}[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]"
        cmd += ["-filter_complex", f"{vchain};{audio}", "-map", "[v]", "-map", "[a]"]
    else:
        cmd += ["-filter_complex", vchain, "-map", "[v]", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", "final.mp4"]
    run(cmd, cwd=job_dir)
    # one clean frame (no captions) from the middle of every scene, for the thumbnail designer
    (job_dir / "frames").mkdir(exist_ok=True)
    for i, (a, b) in enumerate(times):
        run(["ffmpeg", "-y", "-ss", f"{(a + b) / 2:.2f}", "-i", "visual.mp4", "-frames:v", "1",
             "-q:v", "2", f"frames/scene_{i:02d}.jpg"], cwd=job_dir)
    for s in segs:  # raw clips are kept until the video passes QA, so a repair can reuse them
        (job_dir / s).unlink(missing_ok=True)
    (job_dir / "visual.mp4").unlink(missing_ok=True)
    shutil.rmtree(job_dir / "fonts", ignore_errors=True)
    log("editor: final.mp4 rendered")
    return job_dir / "final.mp4"


YELLOW, WHITE, BLACK = (255, 222, 0), (255, 255, 255), (0, 0, 0)
FONT = str(ASSETS / "fonts" / "ArchivoBlack-Regular.ttf")  # bundled, so cloud and PC renders match


def _font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def _vivid(img):
    from PIL import ImageEnhance
    img = ImageEnhance.Contrast(img).enhance(1.18)
    img = ImageEnhance.Color(img).enhance(1.3)
    return ImageEnhance.Sharpness(img).enhance(1.4)


def _colorfulness(img):
    import numpy as np
    a = np.asarray(img.resize((120, 213))).astype(float)
    rg, yb = a[..., 0] - a[..., 1], (a[..., 0] + a[..., 1]) / 2 - a[..., 2]
    return float(np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean()) + a.std() * 0.5)


def _fill(img, w, h):
    sw, sh = img.size
    s = max(w / sw, h / sh)
    img = img.resize((round(sw * s), round(sh * s)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def _shade(canvas, y0, y1, top_dark):
    """Soft dark gradient so text pops on any footage."""
    import numpy as np
    W = canvas.width
    ramp = np.linspace(0.78, 0, y1 - y0) if top_dark else np.linspace(0, 0.78, y1 - y0)
    band = np.asarray(canvas.crop((0, y0, W, y1))).astype(float) * (1 - ramp[:, None, None])
    canvas.paste(Image.fromarray(band.astype("uint8")), (0, y0))


def _fit(d, text, max_w, start=170, low=70):
    size = start
    while size > low and d.textlength(text, font=_font(size)) > max_w:
        size -= 4
    return _font(size)


def _headline(canvas, text, cy, highlight=""):
    """Big centred line(s); highlight word(s) in yellow; heavy outline and drop shadow."""
    if not text:
        return
    d = ImageDraw.Draw(canvas)
    W = canvas.width
    words = text.upper().split()
    lines = [" ".join(words)] if len(words) <= 2 else [" ".join(words[:len(words) // 2]),
                                                       " ".join(words[len(words) // 2:])]
    hl = set(highlight.upper().split())
    font = min((_fit(d, ln, W * 0.9) for ln in lines), key=lambda f: f.size)
    lh = int(font.size * 1.08)
    y = cy - lh * len(lines) // 2
    for ln in lines:
        x = (W - d.textlength(ln, font=font)) / 2
        parts = ln.split()
        for k, w in enumerate(parts):
            col = YELLOW if w in hl else WHITE
            d.text((x + 7, y + 9), w, font=font, fill=BLACK)
            d.text((x, y), w, font=font, fill=col, stroke_width=max(6, font.size // 13), stroke_fill=BLACK)
            x += d.textlength(w + (" " if k < len(parts) - 1 else ""), font=font)
        y += lh


def thumbnail(job_dir, spec, name="thumbnail.jpg"):
    """spec: {"layout": "split"|"single", "top_scene", "bottom_scene", "top_text", "bottom_text",
    "connector", "scene", "text", "highlight"}. A plain string means a single-layout headline."""
    f = config()["format"]
    W, H = f["width"], f["height"]
    if isinstance(spec, str):
        spec = {"layout": "single", "text": spec}
    frames = sorted((job_dir / "frames").glob("scene_*.jpg"))
    if not frames:
        run(["ffmpeg", "-y", "-ss", "1.2", "-i", "final.mp4", "-frames:v", "1", "frame.jpg"], cwd=job_dir)
        frames = [job_dir / "frame.jpg"]
    imgs = [Image.open(p).convert("RGB") for p in frames]
    def pick(i):
        if isinstance(i, int) and 0 <= i < len(imgs):
            return imgs[i]
        pool = [imgs[k] for k in i if 0 <= k < len(imgs)] if isinstance(i, list) else []
        return max(pool or imgs, key=_colorfulness)

    if spec.get("layout") == "split" and len(imgs) >= 2:
        canvas = Image.new("RGB", (W, H))
        canvas.paste(_vivid(_fill(pick(spec.get("top_scene")), W, H // 2)), (0, 0))
        canvas.paste(_vivid(_fill(pick(spec.get("bottom_scene")), W, H - H // 2)), (0, H // 2))
        _shade(canvas, 0, 560, True)
        _shade(canvas, H - 560, H, False)
        d = ImageDraw.Draw(canvas)
        d.rectangle([0, H // 2 - 8, W, H // 2 + 8], fill=YELLOW)
        r = 125
        d.ellipse([W // 2 - r - 12, H // 2 - r - 12, W // 2 + r + 12, H // 2 + r + 12], fill=BLACK)
        d.ellipse([W // 2 - r, H // 2 - r, W // 2 + r, H // 2 + r], fill=YELLOW)
        d.text((W // 2, H // 2), spec.get("connector", "="), font=_font(200), anchor="mm", fill=BLACK)
        _headline(canvas, spec.get("top_text", ""), 260, spec.get("highlight", ""))
        _headline(canvas, spec.get("bottom_text", ""), H - 260, spec.get("highlight", ""))
    else:
        canvas = _vivid(_fill(pick(spec.get("scene")), W, H))
        _shade(canvas, 0, int(H * 0.45), True)
        _headline(canvas, spec.get("text", ""), int(H * 0.21), spec.get("highlight", ""))

    out = job_dir / name
    canvas.save(out, quality=93)
    (job_dir / "frame.jpg").unlink(missing_ok=True)
    return out
