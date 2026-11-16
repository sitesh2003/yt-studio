"""Voice lab (16 Nov 2026, owner: "can we modulate the voice and add some emotion to the narrator").

Renders the same short spoken-style script with:
  kokoro_af_heart.wav          - today's narrator (Kokoro, one voice)
  chatterbox_calm.wav          - Chatterbox (MIT, open source) with low emotion exaggeration
  chatterbox_lively.wav        - Chatterbox with stronger emotion exaggeration
and writes timings.txt (seconds to make each, length), so speed on the free cloud CPU is known too.
Run by .github/workflows/voice-lab.yml (manually, or on any change to this file); the MP3s are
committed to research/voice_lab/."""
import os
import sys
import time

OUT = sys.argv[1] if len(sys.argv) > 1 else "voice_lab"
WHICH = sys.argv[2] if len(sys.argv) > 2 else "all"
os.makedirs(OUT, exist_ok=True)
LINES = [
    "Water alone can't clean a greasy pan. So how does one drop of soap do it?",
    "Here's the thing. Water and oil don't mix.",
    "Now look at one soap molecule. One end loves water. The other end loves oil.",
    "So the oily ends dive into the grease, and the watery ends face out. That's the trick!",
    "Wait, really? That's it?",
    "So here's one for you. Why does hot water make it even faster?",
]
log = []


def save(name, wav, sr):
    import soundfile as sf
    sf.write(os.path.join(OUT, name), wav, sr)


def kokoro():
    import numpy as np
    from kokoro import KPipeline
    t = time.time()
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    parts = []
    for line in LINES:
        for r in pipe(line, voice="af_heart", speed=1.06):
            parts.append(r.audio.numpy())
        parts.append(np.zeros(int(24000 * 0.3), dtype="float32"))
    wav = np.concatenate(parts)
    save("kokoro_af_heart.wav", wav, 24000)
    log.append(f"kokoro af_heart: {time.time() - t:.0f}s to make, {len(wav) / 24000:.1f}s long")


def chatterbox(name, exaggeration, cfg):
    import numpy as np
    import torch
    from chatterbox.tts import ChatterboxTTS
    t = time.time()
    model = ChatterboxTTS.from_pretrained(device="cuda" if torch.cuda.is_available() else "cpu")
    parts = []
    for line in LINES:
        w = model.generate(line, exaggeration=exaggeration, cfg_weight=cfg)
        parts.append(w.squeeze(0).cpu().numpy())
        parts.append(np.zeros(int(model.sr * 0.3), dtype="float32"))
    wav = np.concatenate(parts)
    save(f"{name}.wav", wav, model.sr)
    log.append(f"{name} (exaggeration {exaggeration}, cfg {cfg}): {time.time() - t:.0f}s to make, {len(wav) / model.sr:.1f}s long")


def _words(s):
    import re
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", s.lower().replace("’", "'"))


def _missing(text, wav, sr, ear):
    """Words of `text` the listener (Whisper) did not hear in `wav`."""
    import soundfile as sf
    path = os.path.join(OUT, "_check.wav")
    sf.write(path, wav, sr)
    segs, _ = ear.transcribe(path, language="en", beam_size=5)
    heard = set(_words(" ".join(s.text for s in segs)))
    return [w for w in _words(text) if w not in heard]


def chatterbox_checked(name, exaggeration, cfg, tries=4):
    """Lively, but every word said: one sentence at a time, each one listened to, re-made (new seed) if a word
    is missing (16 Nov 2026: plain lively dropped 8% of the words)."""
    import re
    import numpy as np
    import torch
    from chatterbox.tts import ChatterboxTTS
    from faster_whisper import WhisperModel
    t = time.time()
    model = ChatterboxTTS.from_pretrained(device="cuda" if torch.cuda.is_available() else "cpu")
    ear = WhisperModel("base.en", device="cpu", compute_type="int8")
    parts, retakes, unfixed = [], 0, []
    for line in LINES:
        for sent in [s for s in re.split(r"(?<=[.?!])\s+", line.strip()) if s]:
            best, best_miss = None, None
            for n in range(tries):
                torch.manual_seed(1000 + n)
                w = model.generate(sent, exaggeration=exaggeration, cfg_weight=cfg).squeeze(0).cpu().numpy()
                miss = _missing(sent, w, model.sr, ear)
                if best is None or len(miss) < len(best_miss):
                    best, best_miss = w, miss
                if not miss:
                    break
                retakes += 1
            if best_miss:
                unfixed.append(f"{sent!r} still missing {best_miss}")
            parts += [best, np.zeros(int(model.sr * 0.15), dtype="float32")]
        parts.append(np.zeros(int(model.sr * 0.15), dtype="float32"))
    try:
        os.remove(os.path.join(OUT, "_check.wav"))
    except OSError:
        pass
    wav = np.concatenate(parts)
    save(f"{name}.wav", wav, model.sr)
    log.append(f"{name} (exaggeration {exaggeration}, cfg {cfg}, checked by ear): {time.time() - t:.0f}s to make, "
               f"{len(wav) / model.sr:.1f}s long, {retakes} re-takes, unfixed: {'; '.join(unfixed) or 'none'}")


jobs = {"kokoro": [kokoro],
        "chatterbox": [lambda: chatterbox("chatterbox_calm", 0.4, 0.5), lambda: chatterbox("chatterbox_lively", 0.8, 0.3)],
        "checked": [lambda: chatterbox_checked("chatterbox_lively_checked", 0.8, 0.3),
                    lambda: chatterbox_checked("chatterbox_lively_tuned", 0.7, 0.5)]}
for job in (jobs.get(WHICH) or jobs["kokoro"] + jobs["chatterbox"]):
    try:
        job()
    except Exception as e:
        log.append(f"FAILED ({WHICH}): {type(e).__name__}: {str(e)[:300]}")
NL = chr(10)
open(os.path.join(OUT, "timings.txt"), "a", encoding="utf-8").write(NL.join(log) + NL)
print(NL.join(log))
