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


# ---- 16 Nov 2026, owner: "I don't feel the male and female voice pace is great ... share all the options" ----
# The same Short-style lines, read sentence by sentence with the pauses a real video uses (agents/voice.py
# _gap_after), so each option sounds as it would in a video. Files: opt_<id>.wav.
OPT_EN = [["Your fingers wrinkle in the bath. But your elbows don't. Why?"],
          ["For years, we thought skin just soaked up water like a sponge.",
           "But here's the twist. If the nerves in a finger are cut, it never wrinkles at all!"],
          ["So wrinkling is your body's choice. Tiny blood vessels squeeze, and the skin folds into grooves."],
          ["Those grooves push water away, like the tread on a tyre. Wet things are easier to grip."],
          ["So next time you're in the bath, try picking up a wet marble. Which hand wins?"]]
OPT_HI = [["नहाने के बाद उंगलियों पर झुर्रियां पड़ जाती हैं। लेकिन कोहनी पर नहीं। क्यों?"],
          ["सालों तक हमें लगा कि त्वचा बस स्पंज की तरह पानी सोख लेती है।",
           "लेकिन असली बात कुछ और है! अगर उंगली की नसें कट जाएं, तो झुर्रियां पड़ती ही नहीं।"],
          ["यानी यह आपके शरीर का फैसला है। छोटी रक्त नलिकाएं सिकुड़ती हैं, और त्वचा में खांचे बन जाते हैं।"],
          ["ये खांचे पानी को हटाते हैं, बिल्कुल टायर की तरह। गीली चीज़ें पकड़ना आसान हो जाता है।"],
          ["तो अगली बार गीला कंचा उठाकर देखिए। कौन सा हाथ जीतेगा?"]]
# id, engine, voice, speed (Kokoro) or rate (Edge), pause scale, language
OPTIONS = [
    ("A1", "kokoro", "af_heart", 1.06, 1.0, "en"),      # main channel today
    ("A2", "kokoro", "af_heart", 0.96, 1.6, "en"),      # same voice, calmer pace, longer pauses
    ("A3", "kokoro", "af_heart", 1.14, 0.7, "en"),      # same voice, quicker
    ("A4", "kokoro", "af_bella", 1.06, 1.0, "en"),      # Why It Works today
    ("A5", "kokoro", "af_nicole", 1.0, 1.0, "en"),
    ("A6", "kokoro", "af_sarah", 1.06, 1.0, "en"),
    ("B1", "kokoro", "am_michael", 1.04, 1.0, "en"),
    ("B2", "kokoro", "am_fenrir", 1.04, 1.0, "en"),
    ("B3", "kokoro", "am_puck", 1.06, 1.0, "en"),
    ("B4", "kokoro", "bm_george", 1.02, 1.0, "en-gb"),
    ("B5", "kokoro", "bf_emma", 1.04, 1.0, "en-gb"),
    ("C1", "edge", "en-US-AvaMultilingualNeural", "+4%", 1.0, "en"),
    ("C2", "edge", "en-US-EmmaMultilingualNeural", "+4%", 1.0, "en"),
    ("C3", "edge", "en-US-AndrewMultilingualNeural", "+4%", 1.0, "en"),
    ("C4", "edge", "en-US-BrianMultilingualNeural", "+4%", 1.0, "en"),
    ("C5", "edge", "en-GB-RyanNeural", "+2%", 1.0, "en"),
    ("C6", "edge", "en-IN-NeerjaNeural", "+2%", 1.0, "en"),
    ("C7", "edge", "en-IN-PrabhatNeural", "+2%", 1.0, "en"),
    ("D1", "two", ("am_michael", "af_heart"), 1.06, 1.0, "en"),   # the OLD style: male host, female explainer
    ("H1", "edge", "hi-IN-SwaraNeural", "+0%", 1.0, "hi"),        # Aakhir Kyun? today
    ("H2", "edge", "hi-IN-MadhurNeural", "+0%", 1.0, "hi"),
    ("H3", "edge", "hi-IN-SwaraNeural", "-6%", 1.6, "hi"),         # calmer
    ("H4", "kokoro", "hf_alpha", 1.0, 1.0, "hi"),
    ("H5", "kokoro", "hm_omega", 1.0, 1.0, "hi"),
]


def _gap(sent, last_in_scene):
    s = sent.strip()
    g = 0.3 if s.endswith("?") else 0.18 if s.endswith("!") else 0.2
    return g + (0.05 if last_in_scene else 0.0)


def _trim(wav, sr):
    import numpy as np
    loud = np.where(np.abs(wav) > 0.01)[0]
    if not len(loud):
        return wav
    a, b = max(0, loud[0] - int(0.03 * sr)), min(len(wav), loud[-1] + int(0.05 * sr))
    return wav[a:b]


_PIPES = {}


def _kokoro_say(text, voice, speed, lang):
    import numpy as np
    from kokoro import KPipeline
    code = {"en": "a", "en-gb": "b", "hi": "h"}[lang]
    if code not in _PIPES:
        _PIPES[code] = KPipeline(lang_code=code, repo_id="hexgrad/Kokoro-82M")
    return np.concatenate([r.audio.numpy() for r in _PIPES[code](text, voice=voice, speed=speed)]), 24000


def _edge_say(text, voice, rate):
    import asyncio
    import subprocess
    import tempfile
    import edge_tts
    import soundfile as sf
    d = tempfile.mkdtemp()
    asyncio.run(edge_tts.Communicate(text, voice, rate=rate).save(f"{d}/s.mp3"))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{d}/s.mp3", "-ac", "1", "-ar", "24000", f"{d}/s.wav"],
                   check=True)
    return sf.read(f"{d}/s.wav", dtype="float32")


def options():
    import re
    import numpy as np
    for oid, engine, voice, pace, pscale, lang in OPTIONS:
        t = time.time()
        try:
            parts, sr = [], 24000
            script = OPT_HI if lang == "hi" else OPT_EN
            for k, scene in enumerate(script):
                sents = [s for line in scene for s in re.split(r"(?<=[.?!।])\s+", line.strip()) if s]
                for m, sent in enumerate(sents):
                    if engine == "edge":
                        w, sr = _edge_say(sent, voice, pace)
                    else:
                        v = voice if engine == "kokoro" else voice[0 if k in (0, len(script) - 1) else 1]
                        w, sr = _kokoro_say(sent, v, pace, lang)
                    gap = _gap(sent, m == len(sents) - 1) * pscale
                    parts += [_trim(w, sr), np.zeros(int(sr * gap), dtype="float32")]
            wav = np.concatenate(parts)
            save(f"opt_{oid}.wav", wav, sr)
            log.append(f"opt_{oid} {engine} {voice} {pace} pauses x{pscale}: {time.time() - t:.0f}s to make, "
                       f"{len(wav) / sr:.1f}s long")
        except Exception as e:
            log.append(f"opt_{oid} {engine} {voice}: FAILED {type(e).__name__}: {str(e)[:200]}")


# ---- Hindi round 2 (16 Nov 2026, owner: liked none of H1-H5, "hindi is very slow") ----
HINDI2 = [("H6", "edge", "hi-IN-SwaraNeural", "+15%", 0.7),
          ("H7", "edge", "hi-IN-SwaraNeural", "+25%", 0.6),
          ("H8", "edge", "hi-IN-MadhurNeural", "+15%", 0.7),
          ("H9", "edge", "hi-IN-MadhurNeural", "+25%", 0.6)]


def hindi2():
    import re
    import numpy as np
    for oid, engine, voice, rate, pscale in HINDI2:
        t = time.time()
        try:
            parts, sr = [], 24000
            for scene in OPT_HI:
                sents = [s for line in scene for s in re.split(r"(?<=[.?!।])\s+", line.strip()) if s]
                for m, sent in enumerate(sents):
                    w, sr = _edge_say(sent, voice, rate)
                    parts += [_trim(w, sr), np.zeros(int(sr * _gap(sent, m == len(sents) - 1) * pscale), dtype="float32")]
            wav = np.concatenate(parts)
            save(f"opt_{oid}.wav", wav, sr)
            log.append(f"opt_{oid} {voice} {rate} pauses x{pscale}: {len(wav) / sr:.1f}s long")
        except Exception as e:
            log.append(f"opt_{oid} {voice}: FAILED {type(e).__name__}: {str(e)[:200]}")
    # the owner's English pick (E2) speaking Hindi: Chatterbox's multilingual model, same voice, quicker pauses
    try:
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
        for oid, ex, cfg in (("H10", 0.7, 0.5), ("H11", 0.5, 0.3)):
            t = time.time()
            parts = []
            for scene in OPT_HI:
                sents = [s for line in scene for s in re.split(r"(?<=[.?!।])\s+", line.strip()) if s]
                for m, sent in enumerate(sents):
                    torch.manual_seed(1000)
                    w = model.generate(sent, language_id="hi", exaggeration=ex, cfg_weight=cfg).squeeze(0).cpu().numpy()
                    parts += [_trim(w, model.sr), np.zeros(int(model.sr * _gap(sent, m == len(sents) - 1) * 0.7),
                                                          dtype="float32")]
            wav = np.concatenate(parts)
            save(f"opt_{oid}.wav", wav, model.sr)
            log.append(f"opt_{oid} chatterbox multilingual hi (emotion {ex}, cfg {cfg}): {time.time() - t:.0f}s to make, "
                       f"{len(wav) / model.sr:.1f}s long")
    except Exception as e:
        log.append(f"opt_H10/H11 chatterbox hindi: FAILED {type(e).__name__}: {str(e)[:200]}")


# 17 Nov 2026, owner: "show me my voice speaking all the versions". His 22 s sample (unlocked from
# assets/voice/owner.wav.enc with VOICE_KEY) read by Chatterbox in English, Hinglish and romanised Hinglish,
# plus H14 = the new Hindi pick (H6, Swara) at +18% reading the same Hinglish lines.
OPT_HING = [["नहाने के बाद fingers पर wrinkles आ जाते हैं। लेकिन elbow पर नहीं। क्यों?"],
            ["सालों तक हमें लगा कि skin बस sponge की तरह पानी सोख लेती है।",
             "लेकिन असली बात कुछ और है! अगर finger की nerves कट जाएं, तो wrinkles आते ही नहीं।"],
            ["मतलब ये आपकी body का decision है। छोटी blood vessels सिकुड़ती हैं, और skin में grooves बन जाते हैं।"],
            ["ये grooves पानी को हटाते हैं, बिल्कुल tyre की तरह। गीली चीज़ें पकड़ना easy हो जाता है।"],
            ["तो next time गीला कंचा उठाकर देखिए। कौन सा हाथ जीतेगा?"]]
OPT_HING_ROMAN = [["Nahaane ke baad fingers pe wrinkles aa jaate hain. Lekin elbow pe nahi. Kyun?"],
                  ["Saalon tak humein laga ki skin bas sponge ki tarah paani sokh leti hai.",
                   "Lekin asli baat kuch aur hai! Agar finger ki nerves kat jaayein, toh wrinkles aate hi nahi."],
                  ["Matlab ye aapki body ka decision hai. Chhoti blood vessels sikudti hain, aur skin mein grooves ban jaate hain."],
                  ["Ye grooves paani ko hataate hain, bilkul tyre ki tarah. Geeli cheezein pakadna easy ho jaata hai."],
                  ["Toh next time geela kancha utha ke dekhiye. Kaunsa haath jeetega?"]]


def _tempo(wav, sr, f):
    import subprocess
    import tempfile
    import numpy as np
    import soundfile as sf
    d = tempfile.mkdtemp()
    sf.write(f"{d}/a.wav", wav, sr)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{d}/a.wav", "-af",
                    "silenceremove=stop_periods=-1:stop_duration=0.2:stop_threshold=-40dB:stop_silence=0.1,"
                    f"atempo={f:.3f}", f"{d}/b.wav"], check=True)
    return np.asarray(sf.read(f"{d}/b.wav", dtype="float32")[0])


def _read(lines, say, sr, pscale=0.7):
    import re
    import numpy as np
    parts = []
    for scene in lines:
        sents = [s for line in scene for s in re.split(r"(?<=[.?!।])\s+", line.strip()) if s]
        for m, sent in enumerate(sents):
            parts += [_trim(say(sent), sr), np.zeros(int(sr * _gap(sent, m == len(sents) - 1) * pscale), dtype="float32")]
    return np.concatenate(parts)


def owner():
    # the new Hindi pick first (no key needed): H6 Swara at +18%, Hinglish
    try:
        w = _read(OPT_HING, lambda t: _edge_say(t, "hi-IN-SwaraNeural", "+18%")[0], 24000)
        save("opt_H14.wav", w, 24000)
        log.append(f"opt_H14 Swara +18% Hinglish: {len(w) / 24000:.1f}s long")
    except Exception as e:
        log.append(f"opt_H14: FAILED {type(e).__name__}: {str(e)[:200]}")
    ref = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "voice", "owner.wav")
    if not os.path.exists(ref):
        log.append("owner voice: NOT UNLOCKED (add the VOICE_KEY secret), no samples in his voice made")
        return
    import torch
    from chatterbox.tts import ChatterboxTTS
    en = ChatterboxTTS.from_pretrained(device="cpu")
    for oid, lines, ex, cfg, f, what in (("O1", OPT_EN, 0.7, 0.5, 1.0, "English, E2 settings"),
                                         ("O2", OPT_EN, 0.5, 0.3, 1.0, "English, calmer"),
                                         ("O3", OPT_EN, 0.7, 0.5, 1.12, "English, E2 settings, quicker"),
                                         ("O4", OPT_HING_ROMAN, 0.5, 0.3, 1.0, "Hinglish in English letters, English model")):
        t = time.time()
        try:
            def say(s, ex=ex, cfg=cfg):
                torch.manual_seed(1000)
                return en.generate(s, audio_prompt_path=ref, exaggeration=ex, cfg_weight=cfg).squeeze(0).cpu().numpy()
            w = _read(lines, say, en.sr)
            if f > 1.001:
                w = _tempo(w, en.sr, f)
            save(f"owner_{oid}.wav", w, en.sr)
            log.append(f"owner_{oid} {what}: {time.time() - t:.0f}s to make, {len(w) / en.sr:.1f}s long")
        except Exception as e:
            log.append(f"owner_{oid}: FAILED {type(e).__name__}: {str(e)[:200]}")
    del en
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    hi = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    for oid, ex, cfg, what in (("O5", 0.5, 0.3, "Hinglish, Hindi model, +18%"),
                               ("O6", 0.7, 0.5, "Hinglish, Hindi model, livelier, +18%")):
        t = time.time()
        try:
            def say(s, ex=ex, cfg=cfg):
                torch.manual_seed(1000)
                return hi.generate(s, language_id="hi", audio_prompt_path=ref, exaggeration=ex,
                                   cfg_weight=cfg).squeeze(0).cpu().numpy()
            w = _tempo(_read(OPT_HING, say, hi.sr), hi.sr, 1.18)
            save(f"owner_{oid}.wav", w, hi.sr)
            log.append(f"owner_{oid} {what}: {time.time() - t:.0f}s to make, {len(w) / hi.sr:.1f}s long")
        except Exception as e:
            log.append(f"owner_{oid}: FAILED {type(e).__name__}: {str(e)[:200]}")


jobs = {"kokoro": [kokoro], "options": [options], "hindi2": [hindi2], "owner": [owner],
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
