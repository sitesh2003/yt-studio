"""Slow a hero narration down so viewers can follow it (owner, 21 Nov 2026: "reduce the voice a bit slow so
you can actually listen to what is happening").

    python tools/hero_slow.py <name> <speed>      e.g. 0.88 = 12% slower, same voice and pitch

The first run keeps the original as voice_orig.mp3 / words_orig.json / scenes_orig.json, so the speed can be
changed again without slowing an already-slowed file. Word and scene timings are stretched to match; run
tools/blender/hero/timings.py <name> afterwards so the 3D is re-timed to the new voice."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
name, speed = sys.argv[1], float(sys.argv[2])
d = ROOT / "research" / "hero" / name
for f in ("voice.mp3", "words.json", "scenes.json"):
    orig = d / f.replace(".", "_orig.", 1)
    if not orig.exists():
        shutil.copy(d / f, orig)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(d / "voice_orig.mp3"), "-af", f"atempo={speed:.4f}",
                "-c:a", "libmp3lame", "-b:a", "160k", str(d / "voice.mp3")], check=True)
k = 1.0 / speed
words = json.loads((d / "words_orig.json").read_text(encoding="utf-8"))
for w in words:
    w["start"], w["end"] = round(w["start"] * k, 3), round(w["end"] * k, 3)
(d / "words.json").write_text(json.dumps(words, indent=2, ensure_ascii=False), encoding="utf-8")
scenes = json.loads((d / "scenes_orig.json").read_text(encoding="utf-8"))
(d / "scenes.json").write_text(json.dumps([[round(a * k, 3), round(b * k, 3)] for a, b in scenes], indent=2),
                               encoding="utf-8")
meta = d / "voice_meta.json"
m = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
m["speed"] = speed
meta.write_text(json.dumps(m, indent=2), encoding="utf-8")
n = len(words)
print(f"{name}: speed {speed}; {words[-1]['end']:.1f}s, {n / (words[-1]['end'] / 60):.0f} words a minute")
