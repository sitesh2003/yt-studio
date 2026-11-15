"""Voice lab (16 Nov 2026, owner: "can we modulate the voice and add some emotion to the narrator").

Renders the same short spoken-style script with:
  kokoro_af_heart.wav          - today's narrator (Kokoro, one voice)
  chatterbox_calm.wav          - Chatterbox (MIT, open source) with low emotion exaggeration
  chatterbox_lively.wav        - Chatterbox with stronger emotion exaggeration
and writes timings.txt (seconds to make each, length), so speed on the free cloud CPU is known too.
Run by .github/workflows/voice-lab.yml; listen to the files in the run's artifact."""
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


jobs = {"kokoro": [kokoro],
        "chatterbox": [lambda: chatterbox("chatterbox_calm", 0.4, 0.5), lambda: chatterbox("chatterbox_lively", 0.8, 0.3)]}
for job in (jobs.get(WHICH) or jobs["kokoro"] + jobs["chatterbox"]):
    try:
        job()
    except Exception as e:
        log.append(f"FAILED ({WHICH}): {type(e).__name__}: {str(e)[:300]}")
NL = chr(10)
open(os.path.join(OUT, "timings.txt"), "a", encoding="utf-8").write(NL.join(log) + NL)
print(NL.join(log))
