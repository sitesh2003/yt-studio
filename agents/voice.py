"""Agent 4a - Voiceover with word-level timings (free, no key: Microsoft Edge neural voices).

Word timings come straight from the voice engine, so captions are exact
without running a speech-to-text model.
"""
import asyncio
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


def narrate(script, job_dir):
    v = config()["voice"]
    text = clean(" ".join(s["narration"].strip() for s in script["scenes"]))
    words, last = None, None
    # keep the channel's voice: retry it patiently, only switch voice as a last resort
    for attempt, name in enumerate([v["name"]] * 5 + ["en-US-AndrewNeural", "en-US-BrianNeural"]):
        try:
            words = asyncio.run(_speak(text, name, v["rate"], str(job_dir / "voice.mp3")))
            if words:
                break
        except Exception as e:  # the free voice service drops a request now and then
            last = e
            log(f"voice: attempt {attempt + 1} failed ({type(e).__name__}), retrying")
            time.sleep(4 * (attempt + 1))
    if not words:
        raise RuntimeError(f"voice: no audio after retries: {last}")
    if not words:
        raise RuntimeError("voice: no word timings returned")
    log(f"voice: {len(words)} words, {words[-1]['end']:.1f}s")
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
