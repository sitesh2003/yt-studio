"""Benchmark audio, measured locally (owner, 19 Nov 2026: "understand the audio also").
Downloads ONLY the sound of each benchmark Short (research/benchmark/media/, never committed),
transcribes it with faster-whisper and measures what can be measured honestly:
speaking speed, pauses, how much the pitch moves (a flat voice moves little), loudness range,
and whether there is speech at all. Our own voices (E2, H14, A1) get the same measurements.

    python tools/benchmark_listen.py   -> research/benchmark/listen.json
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "research/benchmark/media"
OUT = ROOT / "research/benchmark/listen.json"
PLAYLIST = ["WsQnYHIOf-8", "hCl3J0OrQMg", "Z0MKLywH-5g", "jsuoM4dLJ5w", "ItDNA4yv2Ng", "_vcLT_kLGUk",
            "0KiTqL88xdU", "O43PygGEPGY", "ZmBBdQ2tPPU", "uU3NOi-MysE", "kmjELcMJh04", "inz4ouQ6C5k",
            "xd0kO2JcwU0", "vciCGuAMoa0", "Yy6k06pKvxw", "WUMsLAcGpUs", "jNRd1gVaCzk"]
OURS_YT = ["Bxp7r8IzbiY", "80jyJN1A1y8", "syvvVya0Q4g"]           # our public Shorts (old kokoro voice)
OURS_FILES = {"ours_E2_male": "chatterbox_lively_tuned.mp3", "ours_H14_hindi": "opt_H14.mp3",
              "ours_A1_female": "opt_A1.mp3"}


def fetch(vid):
    import yt_dlp
    MEDIA.mkdir(parents=True, exist_ok=True)
    have = list(MEDIA.glob(f"{vid}.*"))
    if have:
        return have[0]
    with yt_dlp.YoutubeDL({"format": "bestaudio[ext=m4a]/bestaudio", "outtmpl": str(MEDIA / "%(id)s.%(ext)s"),
                           "quiet": True, "no_warnings": True, "noplaylist": True, "noprogress": True}) as y:
        y.download([f"https://www.youtube.com/shorts/{vid}"])
    return next(MEDIA.glob(f"{vid}.*"))


def wav16(src):
    out = src.with_suffix(".wav")
    if not out.exists():
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", "16000", str(out)], check=True)
    import soundfile as sf
    a, sr = sf.read(str(out), dtype="float32")
    return out, a, sr


def pitch_stats(a, sr, spans):
    """Median pitch and how much it moves (semitones, 10th-90th percentile) inside speech only."""
    segs = [a[int(s * sr):int(e * sr)] for s, e in spans if e - s > 0.25]
    if not segs:
        return None, None
    x = np.concatenate(segs)
    n, hop = int(0.04 * sr), int(0.01 * sr)
    lo, hi = int(sr / 400), int(sr / 70)
    f0 = []
    for i in range(0, len(x) - n, hop):   # autocorrelation pitch, voiced frames only
        fr = x[i:i + n] - x[i:i + n].mean()
        if np.sqrt(np.mean(fr ** 2)) < 0.01:
            continue
        ac = np.correlate(fr, fr, "full")[n - 1:]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0]
        lag = lo + int(np.argmax(ac[lo:hi]))
        if ac[lag] > 0.45:
            f0.append(sr / lag)
    f0 = np.array(f0)
    if len(f0) < 20:
        return None, None
    st = 12 * np.log2(f0 / np.median(f0))
    return round(float(np.median(f0))), round(float(np.percentile(st, 90) - np.percentile(st, 10)), 1)


def measure(path, model):
    wav, a, sr = wav16(path)
    dur = len(a) / sr
    segs, info = model.transcribe(str(wav), word_timestamps=True, vad_filter=True)
    words = [w for s in segs for w in (s.words or [])]
    text = " ".join(w.word.strip() for w in words)
    if len(words) < 5:
        return {"seconds": round(dur, 1), "speech": False, "language": info.language, "text": text[:200]}
    speak = words[-1].end - words[0].start
    gaps = [b.start - a_.end for a_, b in zip(words, words[1:])]
    pauses = [g for g in gaps if g >= 0.35]
    spans, cur = [], [words[0].start, words[0].end]
    for w in words[1:]:
        if w.start - cur[1] < 0.35:
            cur[1] = w.end
        else:
            spans.append(tuple(cur)); cur = [w.start, w.end]
    spans.append(tuple(cur))
    f0, moves = pitch_stats(a, sr, spans)
    rms = np.array([np.sqrt(np.mean(a[i:i + sr // 10] ** 2)) + 1e-9 for i in range(0, len(a) - sr // 10, sr // 10)])
    db = 20 * np.log10(rms)
    loud = db[db > np.percentile(db, 30)]
    first = [w.word.strip() for w in words if w.start < 3.0]
    return {"seconds": round(dur, 1), "speech": True, "language": info.language,
            "words": len(words), "wpm": round(len(words) / speak * 60), "speech_starts_at": round(words[0].start, 2),
            "pauses_per_min": round(len(pauses) / speak * 60, 1),
            "longest_pause": round(max(gaps), 2) if gaps else 0,
            "pitch_hz": f0, "pitch_range_semitones": moves,
            "loudness_range_db": round(float(np.percentile(loud, 90) - np.percentile(loud, 10)), 1) if len(loud) > 10 else None,
            "first_3s": " ".join(first), "text": text[:600]}


def main():
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    try:   # the playlist as it is now (the owner keeps adding to it)
        sys.path.insert(0, str(ROOT))
        from agents.youtube import yt
        live, tok = [], None
        while True:
            r = yt().playlistItems().list(part="contentDetails", playlistId="PLB4Z8Cz4Yf-s", maxResults=50, pageToken=tok).execute()
            live += [i["contentDetails"]["videoId"] for i in r["items"]]
            tok = r.get("nextPageToken")
            if not tok:
                break
        PLAYLIST[:] = live
    except Exception as e:
        print("playlist read failed, using the saved list:", e)
    print("playlist:", len(PLAYLIST), flush=True)
    for vid in PLAYLIST + OURS_YT:
        if vid in done and "error" not in done[vid]:
            continue
        try:
            done[vid] = measure(fetch(vid), model)
            print("ok", vid, done[vid].get("wpm"), done[vid].get("pitch_range_semitones"), flush=True)
        except Exception as e:
            done[vid] = {"error": f"{type(e).__name__}: {str(e)[:160]}"}
            print("FAIL", vid, done[vid]["error"], flush=True)
        OUT.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
    for key, f in OURS_FILES.items():
        try:
            src = ROOT / "research/voice_lab" / f
            dst = MEDIA / f"{key}.mp3"
            if not dst.exists():
                dst.write_bytes(src.read_bytes())
            done[key] = measure(dst, model)
            print("ok", key, done[key].get("wpm"), done[key].get("pitch_range_semitones"), flush=True)
        except Exception as e:
            done[key] = {"error": f"{type(e).__name__}: {str(e)[:160]}"}
            print("FAIL", key, done[key]["error"], flush=True)
        OUT.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
