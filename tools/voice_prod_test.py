"""Production test of the Chatterbox narrator (16 Nov 2026) before any real video uses it: the real
agents/voice.narrate on a short three-scene script, with the daily workflow's own packages installed.
Prints PASS/FAIL lines and saves research/voice_lab/prod_test.mp3 to listen to."""
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agents import listen, voice   # noqa: E402
from agents.core import set_override   # noqa: E402

SCRIPT = {"title_options": ["Why Fingers Wrinkle In The Bath"], "scenes": [
    {"narration": "Your fingers wrinkle in the bath. But your elbows don't. Why?"},
    {"narration": "If the nerves in a finger are cut, it never wrinkles at all! So wrinkling is your body's choice."},
    {"narration": "Those grooves push water away, like the tread on a tyre. Which hand wins?"}]}
ok = True
for mod in ("kokoro", "faster_whisper", "manim", "chatterbox"):
    try:
        __import__(mod)
        print(f"PASS import {mod}")
    except Exception as e:
        print(f"FAIL import {mod}: {e}")
        ok = False
job = ROOT / "jobs" / "_voice_prod_test"
shutil.rmtree(job, ignore_errors=True)
job.mkdir(parents=True)
set_override({"voice": {"engine": "chatterbox"}})
t = time.time()
words = voice.narrate(SCRIPT, job)
print(f"engine used: {voice.last_engine}; {len(words)} words; {words[-1]['end']:.1f}s audio; {time.time() - t:.0f}s to make")
if voice.last_engine != "chatterbox":
    print("FAIL: fell back from Chatterbox")
    ok = False
text = " ".join(s["narration"] for s in SCRIPT["scenes"])
issues, notes, ratio = listen.compare(text, listen.transcribe(job / "voice.mp3"))
print(f"listen: {ratio:.0%} heard; issues {issues}; notes {notes[:4]}")
ok = ok and not issues
print("caption words:", " ".join(f"{w['text']}@{w['start']:.2f}" for w in words[:12]))
(ROOT / "research" / "voice_lab").mkdir(parents=True, exist_ok=True)
shutil.copy(job / "voice.mp3", ROOT / "research" / "voice_lab" / "prod_test.mp3")
# Hindi with the channel's fixed voice (H14: Swara +18%)
print("owner voice sample unlocked:", (ROOT / "assets" / "voice" / "owner.wav").exists())
import json as _j
hv = _j.loads((ROOT / "channels" / "hi.json").read_text(encoding="utf-8"))["voice"]
HI = {"title_options": ["उंगलियां पानी में क्यों सिकुड़ती हैं"], "scenes": [
    {"narration": "नहाते समय आपकी उंगलियां सिकुड़ जाती हैं। लेकिन कोहनी नहीं। क्यों?"},
    {"narration": "अगर उंगली की नस कट जाए, तो वो कभी नहीं सिकुड़ती! यानी ये आपके शरीर का फ़ैसला है।"},
    {"narration": "ये लकीरें पानी को हटाती हैं, जैसे टायर की ग्रिप। आप क्या सोचते हैं?"}]}
job3 = ROOT / "jobs" / "_voice_prod_test_hi"
shutil.rmtree(job3, ignore_errors=True)
job3.mkdir(parents=True)
set_override({"voice": hv})
t = time.time()
try:
    w3 = voice.narrate(HI, job3)
    print(f"hindi: engine {voice.last_engine}; {len(w3)} words; {w3[-1]['end']:.1f}s audio; {time.time() - t:.0f}s to make")
    shutil.copy(job3 / "voice.mp3", ROOT / "research" / "voice_lab" / "prod_test_hi.mp3")
    want = hv.get("engine", "edge-tts")   # fixed 17 Nov 2026: Hindi = H14, Swara (Edge) at +18%
    if voice.last_engine != want:
        print(f"FAIL: Hindi read with {voice.last_engine}, expected {want}")
        ok = False
except Exception as e:
    print(f"FAIL hindi: {type(e).__name__}: {e}")
    ok = False
# the A1 fallback still works
job2 = ROOT / "jobs" / "_voice_prod_test_k"
shutil.rmtree(job2, ignore_errors=True)
job2.mkdir(parents=True)
set_override({"voice": {"engine": "kokoro", "kokoro_voice": "af_heart"}})
w2 = voice.narrate(SCRIPT, job2)
print(f"fallback kokoro: {voice.last_engine}, {len(w2)} words")
ok = ok and voice.last_engine == "kokoro"
print("RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
