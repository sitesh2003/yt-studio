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


_COUNTDOWN = re.compile(r"(?i)\bthree\.\s*two\.\s*one\.")
_ABBR = re.compile(r"\b(Dr|Mr|Mrs|Ms|Prof|St|vs|etc|e\.g|i\.e|U\.S|approx|No)\.$", re.I)
_TURNS = ("here's why", "here is why", "but ", "and that", "so ", "turns out", "the answer", "now ", "and yet")


def sentences(text):
    """A scene's narration as spoken sentences. 'Three. Two. One.' stays one unit (one held count),
    and abbreviations such as 'Dr.' or 'e.g.' never end a sentence."""
    keep = {}

    def hold(m):
        keep[f"\u2063{len(keep)}\u2063."] = m.group(0)   # ends in "." so the count ends its sentence
        return list(keep)[-1]
    t = _COUNTDOWN.sub(hold, text.strip())
    out, cur = [], ""
    for piece in re.split(r"(?<=[.!?])\s+", t):
        cur = f"{cur} {piece}".strip()
        if not _ABBR.search(cur):
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    for k, v in keep.items():
        out = [o.replace(k, v) for o in out]
    return [o for o in out if re.search(r"\w", o)]


def _gap_after(sent, nxt, scene_end):
    """How long a person pauses after this sentence: no breath sound, just the silence a narrator
    leaves when one thought closes and the next opens. Longer after a question (let it land), after a
    long sentence, before a turn ('But...', 'Here's why...') and at the end of a scene."""
    t, n = sent.strip(), (nxt or "").strip().lower()
    if _COUNTDOWN.search(t):
        g = 0.6                                       # let the count land before the reveal
    elif t.endswith("?"):
        g = 0.55
    elif t.endswith("!"):
        g = 0.38
    else:
        g = 0.34 + (0.08 if len(t.split()) > 14 else 0.0)
    if n.startswith(_TURNS):
        g = max(g, 0.5)                               # a held beat before the turn
    if scene_end:
        g += 0.12
    return g


def _delivery(sent, base):
    """(rate, pitch lift) for one sentence. A question is asked a little slower and its last words
    rise; an exclamation is a touch brighter and quicker; the countdown is slow and even."""
    b = int(re.sub(r"[^-\d]", "", base) or 0)
    t = sent.strip()
    if _COUNTDOWN.search(t) or "pause and guess" in t.lower():
        return f"{b - 8:+d}%", 0.0
    if t.endswith("?"):
        return f"{b - 5:+d}%", 0.045                  # about three quarters of a semitone, on the tail
    if t.endswith("!"):
        return f"{b + 4:+d}%", 0.02
    return f"{b:+d}%", 0.0


def _shape_clip(path, words, lift):
    """Trim the clip to the speech itself, so OUR pause is the only pause: the silence a voice engine
    puts before the first word (about 0.35 s on Kokoro) and after the last one both go. For a question,
    raise the pitch of its last words without changing timing (asetrate up, atempo back: same length,
    so the word timings stay exact); the split is between two words, so there is no warble mid-word.
    Returns (clip, seconds trimmed from the front) - the caller shifts the word timings by that."""
    import subprocess
    out = path.with_name(path.stem + "_s.wav")
    lead = max(0.0, words[0]["start"] - 0.05) if words else 0.0
    head = f"aresample=24000,atrim=start={lead:.3f},asetpts=PTS-STARTPTS"
    trim = "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.04,areverse"
    if lift and len(words) >= 3:
        k = max(1, int(len(words) * 0.6))
        cut = (words[k - 1]["end"] + words[k]["start"]) / 2 - lead
        r = 1 + lift
        fc = (f"[0:a]{head},asplit=2[a][b];"
              f"[a]atrim=0:{cut:.3f},asetpts=PTS-STARTPTS[h];"
              f"[b]atrim={cut:.3f},asetpts=PTS-STARTPTS,asetrate={24000 * r:.0f},aresample=24000,"
              f"atempo={1 / r:.5f}[t];[h][t]concat=n=2:v=0:a=1,{trim}[o]")
    elif lift:
        r = 1 + lift
        fc = f"[0:a]{head},asetrate={24000 * r:.0f},aresample=24000,atempo={1 / r:.5f},{trim}[o]"
    else:
        fc = f"[0:a]{head},{trim}[o]"
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-filter_complex", fc,
                        "-map", "[o]", "-ac", "1", str(out)], check=True)
        path.unlink(missing_ok=True)
        return out, lead
    except Exception as e:
        log(f"voice: shaping skipped ({str(e)[:60]})")
        return path, 0.0


_KOKORO = None
last_engine = ""
last_cast = ""


def _cast_key(script):
    """What picks the voices: the script's first title (scripts carry title_options, not title; an
    empty key gave every video the same pair until 13 Nov), else the topic."""
    return (script.get("title") or (script.get("title_options") or [""])[0] or script.get("topic") or "").strip()


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
    if cast_map.get("host") and cast_map.get("explainer") and             hashlib.sha256(_cast_key(script).encode()).digest()[0] % 2:
        cast_map["host"], cast_map["explainer"] = cast_map["explainer"], cast_map["host"]
        last_cast = "male host, female explainer"
    else:
        last_cast = "female host, male explainer"
    log(f"voice: {last_cast}")
    n_sent = 0
    for k, text in enumerate(scenes):
        who = script["scenes"][k].get("speaker") or ("host" if k == 0 or k == len(scenes) - 1 else "explainer")
        cast = cast_map.get(who, {})
        sv = dict(v, kokoro_voice=cast.get("kokoro") or v.get("kokoro_voice"), edge_voice=cast.get("edge"))
        sents = sentences(text) or [text]
        nxt_scene = scenes[k + 1] if k + 1 < len(scenes) else ""
        for m, sent in enumerate(sents):
            # one sentence at a time, like a narrator: its own pace and tone, then a real pause
            rate, lift = _delivery(sent, v["rate"])
            w, part = _speak_retry(sent, sv, rate, job_dir / f"vo_{k:02d}_{m:02d}.mp3")
            v["engine"] = sv["engine"]   # if Kokoro failed once, stay on Edge for both narrators
            part, lead = _shape_clip(part, w, lift)
            for x in w:
                words.append({"start": x["start"] - lead + t, "end": x["end"] - lead + t, "text": x["text"]})
            last = m == len(sents) - 1
            if last and not nxt_scene:
                gap = 0.0
            else:
                gap = _gap_after(sent, sents[m + 1] if not last else nxt_scene, last)
                if last and (script["scenes"][k + 1].get("speaker") or who) != who:
                    gap += 0.15   # a natural hand-over between the two narrators
            parts.append((part, gap))
            t += _dur(part) + gap   # exactly what is joined, so the captions never drift
            n_sent += 1
    # join: each part followed by its silence, re-encoded to one clean track
    inputs, chain = [], []
    for k, (part, gap) in enumerate(parts):
        inputs += ["-i", str(part)]
        chain.append(f"[{k}:a]aresample=24000,aformat=channel_layouts=mono,apad=pad_dur={gap:.2f}[a{k}]")
    cat = "".join(f"[a{k}]" for k in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[out]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inputs +
                   ["-filter_complex", ";".join(chain) + ";" + cat, "-map", "[out]",
                    "-c:a", "libmp3lame", "-b:a", "128k", str(job_dir / "voice.mp3")], check=True)
    for part, _ in parts:
        part.unlink(missing_ok=True)
    global last_engine
    last_engine = v["engine"]
    log(f"voice: {len(words)} words, {words[-1]['end']:.1f}s, {len(scenes)} scenes, {n_sent} sentences each "
        f"followed by a natural pause; questions rise ({v['engine']})")
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
