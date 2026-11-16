"""Listen to every video that went to YouTube and find stretches with NO VOICE in the middle.

16 Nov 2026, owner: "I felt 1 or 2 videos have no voice in the middle". Runs in GitHub Actions
(.github/workflows/audio-audit.yml), because the files are there:
  - the exact final.mp4 that was uploaded, from the runs' stored artifacts (kept 7 days);
  - for older public videos no longer in an artifact, the audio YouTube serves (yt-dlp), when it allows it.
Each file is checked two ways:
  1. silence  - ffmpeg silencedetect: the sound drops out completely (the old one-pass render fault);
  2. no voice - faster-whisper word timings: a gap between two spoken words, which also catches a voice
                that stops while background music carries on.
Writes research/audio_audit.md (plain words, for the owner) and research/audio_audit.json."""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
REPO = os.environ.get("GITHUB_REPOSITORY", "sitesh2003/yt-studio")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
CHANNELS = (("main", "Ever Thought Why?", ROOT / "data" / "history.json", "en"),
            ("wiw", "Why It Works", ROOT / "data" / "wiw" / "history.json", "en"),
            ("hi", "Aakhir Kyun?", ROOT / "data" / "hi" / "history.json", "hi"))
GAP = 2.0          # seconds without a spoken word in the middle = a problem
SILENT = 1.0       # seconds of real silence in the middle = a problem
EDGE = 1.5         # the first and last 1.5 s are allowed to be quiet
TMP = Path(tempfile.gettempdir()) / "audit"
TMP.mkdir(exist_ok=True)


def _h():
    return {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"} if TOKEN else {}


def videos():
    out = []
    for key, name, path, lang in CHANNELS:
        for h in json.load(open(path, encoding="utf-8")) if path.exists() else []:
            if h.get("video_id") and h.get("status") not in ("deleted", "missing", "withdrawn"):
                out.append({"channel": key, "channel_name": name, "lang": lang, "job": h["job"],
                            "title": h.get("title", ""), "status": h.get("status"), "video_id": h["video_id"],
                            "publish_at": h.get("publish_at", "")})
    return out


def _duration(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path)], capture_output=True, text=True, errors="replace")
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", r.stderr)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0


def silences(path, dur):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-vn", "-af",
                        f"silencedetect=noise=-45dB:d={SILENT}", "-f", "null", "-"],
                       capture_output=True, text=True, errors="replace")
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)] + [dur]
    return [(round(a, 1), round(b, 1)) for a, b in zip(starts, ends) if a > EDGE and b < dur - EDGE]


_MODELS = {}


def voice_gaps(path, lang, dur):
    from faster_whisper import WhisperModel
    name = "base.en" if lang == "en" else "small"
    if name not in _MODELS:
        _MODELS[name] = WhisperModel(name, device="cpu", compute_type="int8")
    segs, _ = _MODELS[name].transcribe(str(path), language=lang, word_timestamps=True, vad_filter=False,
                                       beam_size=1)
    words = [w for s in segs for w in (s.words or [])]
    gaps = []
    for a, b in zip(words, words[1:]):
        if b.start - a.end >= GAP:
            gaps.append((round(a.end, 1), round(b.start, 1), a.word.strip(), b.word.strip()))
    tail = round(dur - words[-1].end, 1) if words else round(dur, 1)
    return gaps, len(words), tail


def artifact_files(wanted):
    """{job: local final.mp4} for the wanted jobs, from the runs' stored artifacts (newest first)."""
    found = {}
    if not TOKEN:
        return found
    arts, page = [], 1
    while True:
        r = requests.get(f"https://api.github.com/repos/{REPO}/actions/artifacts", headers=_h(),
                         params={"per_page": 100, "page": page}, timeout=60).json()
        arts += r.get("artifacts", [])
        if len(r.get("artifacts", [])) < 100:
            break
        page += 1
    for a in sorted(arts, key=lambda a: a["created_at"], reverse=True):
        if a["expired"] or not (a["name"].startswith("videos") or a["name"].startswith("weekly")):
            continue
        if not (wanted - set(found)):
            break
        zpath = TMP / "a.zip"
        with requests.get(a["archive_download_url"], headers=_h(), stream=True, timeout=600) as r:
            if r.status_code != 200:
                print(f"artifact {a['id']}: HTTP {r.status_code}")
                continue
            with open(zpath, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
        try:
            with zipfile.ZipFile(zpath) as z:
                for n in z.namelist():
                    parts = n.split("/")
                    if not n.endswith("final.mp4"):
                        continue
                    job = next((p for p in parts if p in wanted), None)
                    if job and job not in found:
                        dest = TMP / f"{job}.m4a"
                        with z.open(n) as src, open(TMP / "v.mp4", "wb") as out:
                            out.write(src.read())
                        # keep only the sound: small, and exactly what viewers hear
                        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(TMP / "v.mp4"), "-vn", "-c:a",
                                        "copy", str(dest)], check=False)
                        found[job] = dest if dest.exists() and dest.stat().st_size else None
                        print(f"artifact {a['name']} {a['id']}: {job}")
        except zipfile.BadZipFile:
            print(f"artifact {a['id']}: not a zip")
        zpath.unlink(missing_ok=True)
    return {k: v for k, v in found.items() if v}


def youtube_audio(vid):
    dest = TMP / f"yt-{vid}.m4a"
    r = subprocess.run([sys.executable, "-m", "yt_dlp", "-q", "-f", "bestaudio[ext=m4a]/bestaudio", "-o", str(dest),
                        f"https://www.youtube.com/watch?v={vid}"], capture_output=True, text=True, errors="replace")
    return (dest, "") if dest.exists() else (None, (r.stderr or r.stdout).strip().splitlines()[-1:] or ["?"])


def mmss(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def main():
    vids = videos()
    files = artifact_files({v["job"] for v in vids})
    rows = []
    for v in vids:
        path, source, why = files.get(v["job"]), "the uploaded file (run artifact)", ""
        if not path:
            path, err = youtube_audio(v["video_id"])
            source, why = "YouTube's audio", (err[0] if err else "")
        if not path:
            rows.append({**v, "checked": False, "why": why[:160]})
            print(f"NOT CHECKED {v['job']}: {why[:120]}")
            continue
        dur = _duration(path)
        sil = silences(path, dur)
        try:
            gaps, n, tail = voice_gaps(path, v["lang"], dur)
        except Exception as e:
            gaps, n, tail = [], 0, 0
            why = f"listening failed: {str(e)[:100]}"
        rows.append({**v, "checked": True, "source": source, "duration": round(dur, 1), "silences": sil,
                     "gaps": gaps, "words": n, "quiet_end": tail, "why": why})
        print(f"{v['job']}: {dur:.0f}s, {len(sil)} silence(s), {len(gaps)} voice gap(s), {n} words")
    (ROOT / "research").mkdir(exist_ok=True)
    json.dump(rows, open(ROOT / "research" / "audio_audit.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    bad = [r for r in rows if r.get("checked") and (r["silences"] or r["gaps"] or r["quiet_end"] > 4)]
    ok = [r for r in rows if r.get("checked") and r not in bad]
    skipped = [r for r in rows if not r.get("checked")]
    md = ["# Audio audit: is the voice there all the way through?", "",
          f"{len(rows)} videos on YouTube. Checked {len(rows) - len(skipped)}: "
          f"**{len(bad)} with a problem**, {len(ok)} fine, {len(skipped)} could not be fetched.", "",
          f"A problem is: the sound drops out for {SILENT:.0f} s or more, or no word is spoken for {GAP:.0f} s or more, "
          "anywhere except the first and last moments, or the voice ends more than 4 s before the video does.", ""]
    if bad:
        md += ["## Videos with a problem", ""]
        for r in bad:
            md.append(f"### {r['title']}")
            md.append(f"{r['channel_name']} · {r['status']} · https://youtu.be/{r['video_id']} · {mmss(r['duration'])} long "
                      f"· checked from {r['source']}")
            for a, b in r["silences"]:
                md.append(f"- silent from {mmss(a)} to {mmss(b)} ({b - a:.1f} s)")
            for a, b, w1, w2 in r["gaps"]:
                md.append(f"- no voice from {mmss(a)} to {mmss(b)} ({b - a:.1f} s), after \"{w1}\" and before \"{w2}\"")
            if r["quiet_end"] > 4:
                md.append(f"- the voice stops {r['quiet_end']:.0f} s before the end")
            md.append("")
    md += ["## Fine", ""] + [f"- {r['title']} ({r['channel_name']}, {r['status']}, {mmss(r['duration'])})" for r in ok]
    if skipped:
        md += ["", "## Could not be fetched", ""] + [f"- {r['title']} ({r['channel_name']}, https://youtu.be/{r['video_id']}): "
                                                     f"{r['why']}" for r in skipped]
    open(ROOT / "research" / "audio_audit.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
