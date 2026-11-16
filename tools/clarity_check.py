"""Scene-by-scene clarity of uploaded videos (16 Nov 2026, owner: the baking soda and vaccines videos on Why It
Works have the voice 'inaudible'). For each scene of each video: how loud it is, how much of its script the
listener (faster-whisper) hears, and which words are lost. Run in GitHub (needs the run artifacts):
    python tools/clarity_check.py <job-prefix> [<job-prefix> ...]
Writes research/clarity_check.md."""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audio_audit as A   # noqa: E402

ROOT = A.ROOT


def loudness(path, a, b):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{a:.2f}", "-t", f"{max(b - a, 0.5):.2f}", "-i", str(path),
                        "-vn", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    m = re.findall(r"I:\s*(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None


def words_norm(s, lang="en"):
    if lang != "en":   # Hindi: compared by sound (agents/listen.py skeletons), so spelling and script do not count
        from agents.listen import skeleton
        return [k for k in (skeleton(w) for w in re.findall(r"[\wऀ-ॿ']+", (s or "").lower())) if k]
    return re.findall(r"[a-z0-9']+", (s or "").lower())


def main(prefixes):
    vids = [v for v in A.videos() if any(v["job"].startswith(p) for p in prefixes)]
    hist = {}
    for _, _, path, _ in A.CHANNELS:
        if path.exists():
            hist.update({h["job"]: h for h in json.load(open(path, encoding="utf-8"))})
    # finished but not yet uploaded (banked / review) videos can be checked too, when named
    seen = {v["job"] for v in vids}
    for key, name, path, lang in A.CHANNELS:
        for h in json.load(open(path, encoding="utf-8")) if path.exists() else []:
            if h["job"] not in seen and not h.get("video_id") and any(h["job"].startswith(p) for p in prefixes):
                vids.append({"channel": key, "channel_name": name, "lang": lang, "job": h["job"],
                             "title": h.get("title", ""), "status": h.get("status"), "video_id": "(not uploaded yet)"})
    files = A.artifact_files({v["job"] for v in vids})
    from faster_whisper import WhisperModel
    sys.path.insert(0, str(ROOT))
    ears = {}
    md = ["# Clarity check, scene by scene", ""]
    for v in vids:
        try:
            md += one(v, hist, files, ears)
        except Exception as e:   # one bad video must not lose the whole report
            import traceback
            md += [f"## {v.get('title')}", "Check crashed: " + repr(e), "", "```", traceback.format_exc()[-1500:], "```", ""]
            print(traceback.format_exc())
    (ROOT / "research" / "clarity_check.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


def one(v, hist, files, ears):
    from faster_whisper import WhisperModel
    md = []
    if True:
        h, path = hist[v["job"]], files.get(v["job"])
        md += [f"## {v['title']}", f"{v['channel_name']} · https://youtu.be/{v['video_id']} · voices: {h.get('voices')}", ""]
        if not path:
            return md + ["Could not get the uploaded file.", ""]
        lang = v["lang"]
        if lang not in ears:
            ears[lang] = WhisperModel("small.en" if lang == "en" else "small", device="cpu", compute_type="int8")
        segs, _ = ears[lang].transcribe(str(path), language=lang, word_timestamps=True, beam_size=5)
        heard = [(w.start, w.end, w.word) for s in segs for w in (s.words or [])]
        overall = loudness(path, 0, A._duration(path))
        md += [f"Whole video: {overall} LUFS.", "", "| Scene | Time | Loudness | Heard | Words lost |", "|---|---|---|---|---|"]
        for k, ((a, b), line) in enumerate(zip(h.get("scene_times") or [], h.get("scene_lines") or [])):
            said = words_norm(line, lang)
            got = words_norm(" ".join(w for s, e, w in heard if s >= a - 0.2 and e <= b + 0.2), lang)
            import difflib
            sm = difflib.SequenceMatcher(None, said, got, autojunk=False)
            match = sum(blk.size for blk in sm.get_matching_blocks())
            lost = [" ".join(said[i1:i2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op in ("delete", "replace")]
            lu = loudness(path, a, b)
            pct = match / max(len(said), 1)
            md.append(f"| {k + 1} | {A.mmss(a)} to {A.mmss(b)} | {lu} LUFS | {pct:.0%} | {'; '.join(lost)[:120]} |")
            print(v["job"][:13], k + 1, lu, f"{pct:.0%}", lost[:3])
        md.append("")
    return md


if __name__ == "__main__":
    main(sys.argv[1:])
