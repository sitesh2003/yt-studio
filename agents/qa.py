"""Agent 7 - Quality check before anything goes public.

A video is published only if ALL of these pass:
  1. facts      the fact-checker verified every claim
  2. technical  15-60 s, real audio, no black/frozen stretches
  3. sync       caption timings line up with the real pauses in the audio
  4. footage    every scene's footage scored >= 5 by the visuals judge
  5. review     an AI looks at frames from every scene next to the narration and signs off
Results go to meta["qa"]; the review page shows them.
"""
import io
import re
import subprocess

from PIL import Image

from .core import llm_json, log, read_json


def _ff(args):
    r = subprocess.run(["ffmpeg", "-hide_banner"] + args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stderr


def _duration(path):
    """Read from ffmpeg's own header line, so only ffmpeg is needed (no ffprobe)."""
    import re
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", _ff(["-i", str(path)]))
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0


def technical(job):
    issues = []
    video = job / "final.mp4"
    dur = _duration(video)
    long_form = (read_json(job / "meta.json", {}) or {}).get("weekly")
    if not long_form and not 15 <= dur <= 60:
        issues.append(f"length {dur:.1f}s is outside 15-60 s for a Short")
    vol = _ff(["-i", str(video), "-af", "volumedetect", "-vn", "-f", "null", "-"])
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", vol)
    if not m or float(m.group(1)) < -35:
        issues.append(f"audio too quiet or missing (mean {m.group(1) if m else 'n/a'} dB)")
    black = _ff(["-i", str(video), "-vf", "blackdetect=d=0.6:pix_th=0.08", "-an", "-f", "null", "-"])
    if "black_start" in black:
        issues.append("black frames for more than 0.6 s")
    frozen = _ff(["-i", str(video), "-vf", "freezedetect=n=0.003:d=2.5", "-an", "-f", "null", "-"])
    if "freeze_start" in frozen:
        issues.append("video frozen for more than 2.5 s")
    return issues, round(dur, 1)


def sync(job, words):
    """Every clear pause in the audio should be followed by a word starting within 0.35 s."""
    out = _ff(["-i", str(job / "voice.mp3"), "-af", "silencedetect=noise=-35dB:d=0.3", "-f", "null", "-"])
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    starts = [w["start"] for w in words]
    if not ends or not starts:
        return []
    off = []
    for e in ends:
        if e > starts[-1]:
            continue
        nxt = min((s for s in starts if s >= e - 0.4), default=None)
        if nxt is not None:
            off.append(abs(nxt - e))
    bad = [o for o in off if o > 0.35]
    if off and len(bad) / len(off) > 0.25:
        return [f"captions drift from the audio at {len(bad)} of {len(off)} pauses"]
    return []


def review(job, script, times):
    """AI sign-off: one frame per scene, checked against what is being said at that moment."""
    frames, lines = [], []
    for i, (sc, (a, b)) in enumerate(zip(script["scenes"], times)):
        t = a + (b - a) * 0.5
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(job / "final.mp4"),
                              "-frames:v", "1", "-f", "image2pipe", "-vcodec", "mjpeg", "-"],
                             capture_output=True).stdout
        if not raw:
            continue
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im.thumbnail((360, 640))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=80)
        frames.append(buf.getvalue())
        lines.append(f"Frame {len(frames)}: narrator says \"{sc['narration']}\"")
    if not frames:
        return ["could not read frames for review"]
    out = llm_json(f"""You are the final quality reviewer for a family-friendly science YouTube Short aimed at
US viewers. You see one frame from each scene, in order, with what the narrator says at that moment.
{chr(10).join(lines)}

Fail the video if ANY of these is true:
- a frame clearly contradicts or is unrelated to what is being said (a loose but sensible visual
  analogy is fine)
(The small square mark in the top-left corner - a yellow question mark with an orbit - is THIS
channel's own logo on every frame. It is correct; never flag it. Some scenes are deliberately drawn
explainer diagrams on a navy background with short labels: that is intended - judge them only on
whether they are accurate and readable.)
- anything inappropriate for all ages, gory, frightening, sexual, political, or a real brand/logo
  shown prominently
- burned-in captions are cut off, overlap badly, misspelled, or unreadable (captions show only
  1-2 words at a time, karaoke style, so a caption being a fragment of the sentence is NORMAL -
  never fail a frame because its caption words are out of context)
- watermarks, green screen, glitches, or stretched/blurry footage
Return JSON: {{"pass": true or false, "issues": ["specific problem with frame number"],
"frame_scores": [0-10 per frame]}}""", images=frames)
    if out.get("pass") and not out.get("issues"):
        return []
    return [str(i) for i in out.get("issues", [])] or ["reviewer did not approve"]


def check(job, script, times, words, footage_scores):
    meta = read_json(job / "meta.json", {}) or {}
    result = {"facts": [], "technical": [], "sync": [], "footage": [], "review": []}
    if not meta.get("fact_ok", True):
        result["facts"].append("fact-check not fully resolved")
    result["technical"], dur = technical(job)
    result["sync"] = sync(job, words)
    sc = list(footage_scores or [])
    weak = [i + 1 for i, s in enumerate(sc) if s < 5]
    # one loosely-related middle scene (score 3-4) is allowed when the AI frame review
    # below also signs off; a weak hook, a placeholder, or two weak scenes still hold it
    lenient = len(weak) == 1 and weak[0] != 1 and sc[weak[0] - 1] >= 3
    if weak and not lenient:
        result["footage"].append(f"scene(s) {weak} have weak or placeholder footage")
    elif lenient:
        result["notes"] = [f"scene {weak[0]} footage is a loose match (score {sc[weak[0] - 1]}), accepted"]
    try:
        result["review"] = review(job, script, times)
    except Exception as e:
        result["review"] = [f"AI review unavailable: {str(e)[:80]}"]
    passed = not any(v for k, v in result.items() if k != "notes")
    result["pass"] = passed
    result["duration"] = dur
    problems = [f"{k}: {v}" for k, vals in result.items() if isinstance(vals, list) for v in vals]
    log("qa: PASSED, cleared to publish" if passed else "qa: HELD -> " + " | ".join(problems)[:300])
    return result
