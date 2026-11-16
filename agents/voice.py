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
    text = re.sub(r"(?<!\d):(?!\d)", ",", text)   # "Step one:" -> "Step one," (not 3:30)
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
    for piece in re.split(r"(?<=[.!?\u0964])\s+", t):   # \u0964 = the Hindi full stop (।)
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
    # 15 Nov (user, comparing a 12M-view narrated Short): "only after the sentence is done it takes a
    # very small break". Real gaps come out ~0.1 s above these numbers (clip edges), so a plain
    # sentence ends with ~0.25-0.3 s of silence, a question ~0.4 s.
    if _COUNTDOWN.search(t):
        g = 0.45                                      # let the count land before the reveal
    elif t.endswith("?"):
        g = 0.3
    elif t.endswith("!"):
        g = 0.18
    else:
        g = 0.16 + (0.04 if len(t.split()) > 16 else 0.0)
    if n.startswith(_TURNS):
        g = max(g, 0.26)                              # a short held beat before the turn
    if scene_end:
        g += 0.05
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


def _tighten(wav, keep=0.15, longer_than=0.22, floor_db=-40.0):
    """Shorten silences INSIDE a sentence: Kokoro stops for ~0.4 s at a comma, where a person barely
    pauses. Any inner silence longer than `longer_than` keeps only `keep` seconds. Returns the cuts as
    [(position_in_original_clip, seconds_removed)] so the word timings can follow."""
    import numpy as np
    import soundfile as sf
    a, sr = sf.read(str(wav))
    if a.ndim > 1:
        a = a.mean(axis=1)
    hop = int(sr * 0.01)
    n = len(a) // hop
    if n < 10:
        return []
    rms = np.sqrt(np.mean(a[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    quiet = 20 * np.log10(rms) < floor_db
    runs, k = [], 0
    while k < n:
        if quiet[k]:
            j = k
            while j < n and quiet[j]:
                j += 1
            if k > 0 and j < n and (j - k) * 0.01 > longer_than:   # inner silences only
                runs.append((k * hop, j * hop))
            k = j
        else:
            k += 1
    if not runs:
        return []
    keep_n = int(sr * keep)
    pieces, cuts, last, removed = [], [], 0, 0
    for s0, s1 in runs:
        mid0, mid1 = s0 + keep_n // 2, s1 - keep_n // 2
        pieces.append(a[last:mid0])
        cuts.append((mid0 / sr, (mid1 - mid0) / sr))   # position in the ORIGINAL clip
        removed += mid1 - mid0
        last = mid1
    pieces.append(a[last:])
    sf.write(str(wav), np.concatenate(pieces), sr)
    return cuts


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
        try:
            cuts = _tighten(out)
        except Exception as e:
            log(f"voice: comma tightening skipped ({str(e)[:60]})")
            cuts = []
        return out, lead, cuts
    except Exception as e:
        log(f"voice: shaping skipped ({str(e)[:60]})")
        return path, 0.0, []


_KOKORO = None
last_engine = ""
last_cast = ""


def _cast_key(script):
    """What picks the voices: the script's first title (scripts carry title_options, not title; an
    empty key gave every video the same pair until 13 Nov), else the topic."""
    return (script.get("title") or (script.get("title_options") or [""])[0] or script.get("topic") or "").strip()


_LEX = None


def _lexicon(text):
    """Science words Kokoro gets wrong, given their sound ([word](/phonemes/)); the word itself is kept,
    so the word timings and captions still spell it normally. Kokoro only (assets/lexicon.json)."""
    global _LEX
    if _LEX is None:
        import json
        from .core import ASSETS
        try:
            _LEX = {k: v for k, v in json.loads((ASSETS / "lexicon.json").read_text(encoding="utf-8")).items()
                    if not k.startswith("_")}
        except Exception:
            _LEX = {}
    for word, ph in _LEX.items():
        text = re.sub(rf"(?i)(?<![\[\w])({re.escape(word)})(?![\w\]])", lambda m: f"[{m.group(1)}](/{ph}/)", text)
    return text


def _kokoro_speak(text, v, rate, path):
    """Kokoro (open source, Apache 2.0, runs right here on the CPU): a warmer, more human voice.
    Returns word timings like the Edge voice does."""
    global _KOKORO
    import numpy as np
    import soundfile as sf
    if _KOKORO is None:
        from kokoro import KPipeline
        _KOKORO = KPipeline(lang_code=config()["voice"].get("kokoro_lang", "a"), repo_id="hexgrad/Kokoro-82M")
    speed = 1.0 + int(re.sub(r"[^-\d]", "", rate) or 0) / 100
    audio, words, offset = [], [], 0.0
    for r in _KOKORO(_lexicon(text), voice=v.get("kokoro_voice") or "af_heart", speed=speed):
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


_CB = None
_EAR = None


def _norm_w(w):
    return re.sub(r"[^\w]", "", (w or "").lower())


def _align(text, heard):
    """The script's own words on the times the listener heard them (captions keep the script's spelling).
    Unmatched script words are spread evenly between their matched neighbours."""
    import difflib
    said = re.findall(r"\S+", text)
    a, b = [_norm_w(w) for w in said], [_norm_w(h["text"]) for h in heard]
    times = [None] * len(said)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for i in range(blk.size):
            times[blk.a + i] = (heard[blk.b + i]["start"], heard[blk.b + i]["end"])
    end_all = heard[-1]["end"] if heard else 0.0
    k = 0
    while k < len(said):
        if times[k] is None:
            j = k
            while j < len(said) and times[j] is None:
                j += 1
            lo = times[k - 1][1] if k else (heard[0]["start"] if heard else 0.0)
            hi = times[j][0] if j < len(said) else end_all
            step = max(hi - lo, 0.05 * (j - k)) / (j - k)
            for n in range(k, j):
                times[n] = (lo + step * (n - k), lo + step * (n - k + 1))
            k = j
        k += 1
    return [{"start": s, "end": e, "text": w} for w, (s, e) in zip(said, times)]


def _chatterbox_speak(text, v, rate, path, tries=3):
    """Chatterbox (MIT, open source, CPU): the expressive narrator the owner picked on 16 Nov 2026 (lab option E2:
    emotion 0.7, cfg 0.5). It gives no word timings and can drop a word, so each sentence is listened to
    (faster-whisper, word timings), re-made with a new seed if a word is missing, and the best take kept."""
    global _CB, _EAR
    import soundfile as sf
    import torch
    if _CB is None:
        from chatterbox.tts import ChatterboxTTS
        _CB = ChatterboxTTS.from_pretrained(device="cpu")
    if _EAR is None:
        from faster_whisper import WhisperModel
        _EAR = WhisperModel("base.en", device="cpu", compute_type="int8")
    want = [w for w in (_norm_w(x) for x in re.findall(r"\S+", text)) if w]
    best = None
    for n in range(tries):
        torch.manual_seed(1000 + n)
        wav = _CB.generate(text, exaggeration=float(v.get("cb_exaggeration", 0.7)),
                           cfg_weight=float(v.get("cb_cfg", 0.5))).squeeze(0).cpu().numpy().astype("float32")
        sf.write(str(path), wav, _CB.sr)
        segs, _ = _EAR.transcribe(str(path), language="en", beam_size=5, word_timestamps=True)
        heard = [{"start": w.start, "end": w.end, "text": w.word.strip()} for s in segs for w in (s.words or [])]
        got = {_norm_w(h["text"]) for h in heard}
        # spelling is not a dropped word: "tyre" heard as "tire", "colour" as "color" (the 16 Nov test re-made
        # three good takes for that), so a word counts as said if anything heard is close to it
        import difflib
        miss = [w for w in want if w not in got and not w.isdigit()
                and not difflib.get_close_matches(w, got, n=1, cutoff=0.7)]
        if best is None or len(miss) < len(best[2]):
            best = (wav, heard, miss)
        if not miss:
            break
        log(f"voice: Chatterbox dropped {miss[:4]} in {text[:40]!r}; take {n + 2}")
    wav, heard, miss = best
    if not heard or len(miss) > max(1, len(want) // 8):
        raise RuntimeError(f"Chatterbox kept dropping words ({miss[:4]})")
    sf.write(str(path), wav, _CB.sr)
    return _align(text, heard)


def _speak_retry(text, v, rate, path):
    if v.get("engine") == "chatterbox":
        try:
            return _chatterbox_speak(text, v, rate, path.with_suffix(".wav")), path.with_suffix(".wav")
        except Exception as e:
            # the owner's second choice (lab option A1) for the rest of this video
            log(f"voice: Chatterbox unavailable ({str(e)[:80]}), using Kokoro {v.get('kokoro_voice') or 'af_heart'}")
            v["engine"] = "kokoro"
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


class _SentenceFailed(Exception):
    pass


def _merge_short(sents):
    """A one-word line ("Wait!", "Right.") joins the next one: engines often return nothing for it,
    and a narrator runs it straight on anyway. The held count "Three. Two. One." stays as it is."""
    out = []
    for s in sents:
        if out and len(re.findall(r"\w+", out[-1])) < 2 and not _COUNTDOWN.search(out[-1]):
            out[-1] = f"{out[-1]} {s}"
        else:
            out.append(s)
    if (len(out) > 1 and len(re.findall(r"\w+", out[-1])) < 2 and not _COUNTDOWN.search(out[-1])
            and not _COUNTDOWN.search(out[-2])):
        out[-2:] = [f"{out[-2]} {out[-1]}"]
    return out


def _say_sentence(sent, nxt, nxt_scene, sv, v, who, script, k, m, job_dir, words, parts, t, n_sent, whole=False):
    rate, lift = _delivery(sent, v["rate"])
    trial = dict(sv)
    try:
        w, part = _speak_retry(sent, trial, rate, job_dir / f"vo_{k:02d}_{m:02d}.mp3")
    except Exception as e:
        if not whole:
            raise _SentenceFailed(f"no audio for {sent[:50]!r}") from e
        raise
    for retry in range(2):
        # DROP GUARD (15 Nov: a cloud run lost "one water molecules prefer to stick to each other" -
        # 3 s of audio missing while the word timings still listed every word). If the audio is
        # clearly shorter than the timings, speak it again; still short -> read the scene whole.
        short = w and _dur(part) < w[-1]["end"] - 0.35
        if not short:
            break
        log(f"voice: audio {_dur(part):.1f}s but words run to {w[-1]['end']:.1f}s for {sent[:40]!r}; speaking it again")
        part.unlink(missing_ok=True)
        if retry == 1:
            if not whole:
                raise _SentenceFailed(f"audio shorter than its words for {sent[:50]!r}")
            raise RuntimeError(f"voice: audio keeps dropping words in {sent[:50]!r}")
        w, part = _speak_retry(sent, dict(trial), rate, job_dir / f"vo_{k:02d}_{m:02d}_r.mp3")
    if trial["engine"] != sv["engine"]:
        if not whole:   # Kokoro refused this one line: try the scene whole before changing voice
            part.unlink(missing_ok=True)
            raise _SentenceFailed(f"Kokoro gave no audio for {sent[:50]!r}")
        sv["engine"] = v["engine"] = trial["engine"]   # the whole scene failed on Kokoro: Edge from here
    part, lead, cuts = _shape_clip(part, w, 0.0 if whole else lift)

    def moved(sec):   # a time in the trimmed clip, after the shortened inner silences
        sec -= lead
        return sec - sum(amt for pos, amt in cuts if pos + amt <= sec + 1e-6) + t
    for x in w:
        words.append({"start": moved(x["start"]), "end": moved(x["end"]), "text": x["text"]})
    scenes_n = len(script["scenes"])
    last = whole or nxt is None
    if last and not nxt_scene:
        gap = 0.0
    else:
        gap = _gap_after(sent, nxt if not last else nxt_scene, last)
        if last and k + 1 < scenes_n and (script["scenes"][k + 1].get("speaker") or who) != who:
            gap += 0.08   # a quick hand-over between the two narrators
    parts.append((part, gap))
    return t + _dur(part) + gap, n_sent + 1   # exactly what is joined, so the captions never drift


def narrate(script, job_dir, engine=None):
    """One scene at a time, joined with natural pauses, so it sounds like a person telling a story
    rather than one long breathless read. Word timings are shifted onto the joined timeline."""
    v = dict(config()["voice"])
    if engine:
        v["engine"] = engine
    if v.get("engine") == "chatterbox":
        words = _narrate(script, job_dir, v)
        if v["engine"] == "chatterbox":
            return words
        # Chatterbox failed part-way: one video never mixes two voices, so read it all again with Kokoro
        log("voice: Chatterbox failed part-way; the whole video is read again with Kokoro")
        return narrate(script, job_dir, engine="kokoro")
    return _narrate(script, job_dir, v)


def _narrate(script, job_dir, v):
    import subprocess
    from .writer import tidy_countdown
    tidy_countdown(script)   # "Pause and guess" exactly once, right before the 3-2-1
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
    if cast_map.get("host") == cast_map.get("explainer"):   # one narrator per channel since 16 Nov 2026
        last_cast = f"one narrator ({(cast_map.get('host') or {}).get('kokoro') or (cast_map.get('host') or {}).get('edge') or 'default'})"
    log(f"voice: {last_cast}")
    n_sent = 0
    for k, text in enumerate(scenes):
        who = script["scenes"][k].get("speaker") or ("host" if k == 0 or k == len(scenes) - 1 else "explainer")
        cast = cast_map.get(who, {})
        sv = dict(v, kokoro_voice=cast.get("kokoro") or v.get("kokoro_voice"), edge_voice=cast.get("edge"))
        if cast.get("engine"):   # a narrator can use its own engine (e.g. an Edge voice beside a Kokoro one)
            sv["engine"] = cast["engine"]
        sents = _merge_short(sentences(text)) or [text]
        nxt_scene = scenes[k + 1] if k + 1 < len(scenes) else ""
        mark = (len(words), len(parts), t, n_sent)
        try:
            for m, sent in enumerate(sents):
                # one sentence at a time, like a narrator: its own pace and tone, then a real pause
                t, n_sent = _say_sentence(sent, sents[m + 1] if m + 1 < len(sents) else None, nxt_scene,
                                          sv, v, who, script, k, m, job_dir, words, parts, t, n_sent)
        except _SentenceFailed as e:
            # a line the engine would not say on its own (it happens with very short or odd lines):
            # say this scene in one piece, the way every video was read before 14 Nov, rather than
            # switching voices or losing the video
            log(f"voice: scene {k + 1} read in one piece ({e})")
            for p_, _ in parts[mark[1]:]:
                p_.unlink(missing_ok=True)
            del words[mark[0]:], parts[mark[1]:]
            t, n_sent = mark[2], mark[3]
            t, n_sent = _say_sentence(text, None, nxt_scene, sv, v, who, script, k, 99, job_dir,
                                      words, parts, t, n_sent, whole=True)
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
