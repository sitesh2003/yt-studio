"""Narrate a hand-made hero Short (research/hero/<name>/script.json) with the production narrator
(config voice: Chatterbox E2), listen back, and save voice.mp3 + words.json + scenes.json beside it.
20 Nov 2026: the 3D hero Shorts are animated on the laptop/Kaggle to these exact timings."""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agents import listen, voice   # noqa: E402

name = sys.argv[1] if len(sys.argv) > 1 else "trex"
d = ROOT / "research" / "hero" / name
script = json.loads((d / "script.json").read_text(encoding="utf-8"))
job = ROOT / "jobs" / f"_hero_{name}"
shutil.rmtree(job, ignore_errors=True)
job.mkdir(parents=True)
words = voice.narrate(script, job)
print(f"engine {voice.last_engine}; {len(words)} words; {words[-1]['end']:.1f}s")
text = " ".join(s["narration"] for s in script["scenes"])
issues, notes, ratio = listen.compare(text, listen.transcribe(job / "voice.mp3"))
print(f"listen: {ratio:.0%} heard; issues {issues}; notes {notes[:4]}")
if voice.last_engine != "chatterbox" or issues:   # never keep a narration in the wrong voice
    print("NOT SAVED: the narration must be the channel's voice (Chatterbox E2) with nothing missing")
    sys.exit(1)
shutil.copy(job / "voice.mp3", d / "voice.mp3")
(d / "words.json").write_text(json.dumps(words, indent=2, ensure_ascii=False), encoding="utf-8")
(d / "scenes.json").write_text(json.dumps(voice.scene_times(script, words), indent=2), encoding="utf-8")
(d / "voice_meta.json").write_text(json.dumps({"engine": voice.last_engine, "heard": round(ratio, 3),
                                               "issues": issues}, indent=2), encoding="utf-8")
sys.exit(0 if voice.last_engine == "chatterbox" and not issues else 1)
