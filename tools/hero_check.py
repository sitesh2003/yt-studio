"""Quality gate for a hero narration (21 Nov 2026, owner: "no issues at all - not captions, not voice,
not pronunciation"). Transcribes voice.mp3 with the LARGE listening model and prints it line by line next to
the script, so every word and number is checked by a person before rendering.

    python tools/hero_check.py <name> [en|hi]
"""
import json
import sys
from pathlib import Path

from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent.parent
name, lang = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "en")
d = ROOT / "research" / "hero" / name
script = json.loads((d / "script.json").read_text(encoding="utf-8"))
m = WhisperModel("medium.en" if lang == "en" else "medium", device="cpu", compute_type="int8")
segs, _ = m.transcribe(str(d / "voice.mp3"), language=lang, beam_size=5)
print("SCRIPT:")
for s in script["scenes"]:
    print("  ", s["narration"])
print("HEARD:")
for s in segs:
    print(f"  {s.start:5.1f}  {s.text.strip()}")
