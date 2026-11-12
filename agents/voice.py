"""Agent 4a - Voiceover with word-level timings (free, no key: Microsoft Edge neural voices).

Word timings come straight from the voice engine, so captions are exact
without running a speech-to-text model.
"""
import asyncio
import re
import time

import edge_tts

from .core import config, log


async def _speak(text, voice, rate, out_mp3):
    words = []
    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    with open(out_mp3, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({"start": chunk["offset"] / 1e7,
                              "end": (chunk["offset"] + chunk["duration"]) / 1e7,
                              "text": chunk["text"]})
    return words


def clean(text):
    """Text the free voice service reads well. Repeated '...' makes it return no audio at all,
    and 'three, two, one' gets rushed, so the countdown becomes 'Three. Two. One.'"""
    import re
    text = re.sub(r"\s*(\.\s*){2,}|…", ". ", text)                       # ellipses -> one full stop
    text = re.sub(r"(?i)\bthree[,.\s]+two[,.\s]+one\b[.,!]?", "Three. Two. One.", text)
    text = re.sub(r"\s+([.,!?])", r"\1", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def _pause_after(text, nxt):
    """A human narrator breathes: a beat between scenes, longer after a question or before an answer."""
    t, n = text.strip(), (nxt or "").strip().lower()
    if re.search(r"(?i)three\.?\s*two\.?\s*one\.?$", t):
        return 0.55                                  # let the countdown land before the reveal
    if t.endswith("?"):
        return 0.4
    if n.startswith(("here's why", "here is why", "but ", "and that", "so ", "turns out", "the answer")):
        return 0.3                                   # a held beat before the turn
    return 0.1   # the voice engine already ends each part with ~0.5 s of natural silence


def _rate_for(text, base):
    """Small changes of pace so it doesn't drone: slower for the countdown and the closing question."""
    b = int(re.sub(r"[^-\d]", "", base) or 0)
    if "pause and guess" in text.lower() or text.strip().endswith("?"):
        b -= 6
    return f"{b:+d}%"


_KOKORO = None
last_engine = ""
last_cast = ""


def _kokoro_speak(text, v, rate, path):
    """Kokoro (open source, Apache 2.0, runs right here on the CPU): a warmer, more human voice.
    Returns word timings like the Edge voice does."""
    global _KOKORO
    import numpy as np
    import soundfile as sf
    if _KOKORO is None:
        from kokoro import KPipeline
        _KOKORO = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    speed = 1.0 + int(re.sub(r"[^-\d]", "", rate) or 0) / 100
    audio, words, offset = [], [], 0.0
    for r in _KOKORO(text, voice=v.get("kokoro_voice") or "af_heart", speed=speed):
        a = r.audio.numpy() if hasattr(r.audio, "numpy") else np.asarray(r.audio)
        for tk in (r.tokens or []):
            if tk.start_ts is not None and tk.end_ts is not None and re.search(r"\w", tk.text):
                words.append({"start": tk.start_ts + offset, "end": tk.end_ts + offset, "text": tk.text})
        audio.append(a)
        offset += len(a) / 24000
    if not audio or not words:
        raise RuntimeError("kokoro returned no audio")
    sf.write(str(path), np.concatenate(audio), 24000)
    return words


def _speak_retry(text, v, rate, path):
    if v.get("engine") == "kokoro":
        try:
            return _kokoro_speak(text, v, rate, path.with_suffix(".wav")), path.with_suffix(".wav")
        except Exception as e:
            log(f"voice: Kokoro unavailable ({str(e)[:80]}), using the Edge voice")
            v["engine"] = "edge-tts"   # stay on one voice for the rest of this video
    last = None
    for attempt, name in enumerate([v.get("edge_voice") or v["name"]] * 5 + ["en-US-AndrewNeural", "en-US-BrianNeural"]):
        try:
            words = asyncio.run(_speak(text, name, rate, str(path)))
            if words:
                return words, path
        except Exception as e:  # the free voice service drops a request now and then
            last = e
            log(f"voice: attempt {attempt + 1} failed ({type(e).__name__}), retrying")
            time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"voice: no audio after retries: {last}")


def _dur(path):
    import subprocess
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path)], capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", err)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0


def narrate(script, job_dir):
    """One scene at a time, joined with natural pauses, so it sounds like a person telling a story
    rather than one long breathless read. Word timings are shifted onto the joined timeline."""
    import subprocess
    from .writer import tidy_countdown
    tidy_countdown(script)   # "Pause and guess" exactly once, right before the 3-2-1
    v = dict(config()["voice"])
    scenes = [clean(s["narration"].strip()) for s in script["scenes"]]
    words, parts, t = [], [], 0.0
    # Change the voices from video to video: in about half the videos the host is male and the
    # explainer female. Picked from the title, so a re-narration of the same video keeps its voices.
    global last_cast
    import hashlib
    cast_map = dict(v.get("narrators") or {})
    if cast_map.get("host") and cast_map.get("explainer") and             hashlib.sha256(script.get("title", "").encode()).digest()[0] % 2:
        cast_map["host"], cast_map["explainer"] = cast_map["explainer"], cast_map["host"]
        last_cast = "male host, female explainer"
    else:
        last_cast = "female host, male explainer"
    log(f"voice: {last_cast}")
    for k, text in enumerate(scenes):
        who = script["scenes"][k].get("speaker") or ("host" if k == 0 or k == len(scenes) - 1 else "explainer")
        cast = cast_map.get(who, {})
        sv = dict(v, kokoro_voice=cast.get("kokoro") or v.get("kokoro_voice"), edge_voice=cast.get("edge"))
        w, part = _speak_retry(text, sv, _rate_for(text, v["rate"]), job_dir / f"vo_{k:02d}.mp3")
        v["engine"] = sv["engine"]   # if Kokoro failed for one scene, stay on Edge for both narrators
        for x in w:
            words.append({"start": x["start"] + t, "end": x["end"] + t, "text": x["text"]})
        gap = _pause_after(text, scenes[k + 1] if k + 1 < len(scenes) else "") if k + 1 < len(scenes) else 0.0
        if k + 1 < len(scenes) and (script["scenes"][k + 1].get("speaker") or who) != who:
            gap += 0.15   # a natural hand-over between the two narrators
        parts.append((part, gap))
        t += _dur(part) + gap
    # join: each part followed by its silence, re-encoded to one clean track
    inputs, chain = [], []
    for k, (part, gap) in enumerate(parts):
        inputs += ["-i", str(part)]
        chain.append(f"[{k}:a]aresample=24000,apad=pad_dur={gap:.2f}[a{k}]")
    cat = "".join(f"[a{k}]" for k in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[out]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inputs +
                   ["-filter_complex", ";".join(chain) + ";" + cat, "-map", "[out]",
                    "-c:a", "libmp3lame", "-b:a", "128k", str(job_dir / "voice.mp3")], check=True)
    for part, _ in parts:
        part.unlink(missing_ok=True)
    global last_engine
    last_engine = v["engine"]
    log(f"voice: {len(words)} words, {words[-1]['end']:.1f}s, {len(parts)} scenes with natural pauses ({v['engine']})")
    return words


def scene_times(script, words):
    """Map each scene to start/end seconds by counting its words through the timeline."""
    times, i = [], 0
    total = len(words)
    for s in script["scenes"]:
        n = max(1, len(s["narration"].split()))
        start = words[min(i, total - 1)]["start"]
        i = min(i + n, total)
        times.append(start)
    ends = times[1:] + [words[-1]["end"] + 0.6]
    times[0] = 0.0
    return [(a, b) for a, b in zip(times, ends)]
