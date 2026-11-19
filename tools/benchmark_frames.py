"""Contact sheets of each benchmark Short (one frame every 3 s), from a 360p copy kept only in
research/benchmark/media/ (never committed). For studying how each one is animated or filmed.

    python tools/benchmark_frames.py VIDEO_ID [VIDEO_ID ...]   -> research/benchmark/media/<id>_sheet.jpg
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "research/benchmark/media"


def sheet(vid):
    import yt_dlp
    MEDIA.mkdir(parents=True, exist_ok=True)
    mp4 = MEDIA / f"{vid}_360.mp4"
    if not mp4.exists():
        with yt_dlp.YoutubeDL({"format": "bv*[height<=360][ext=mp4]/b[height<=360]", "outtmpl": str(mp4),
                               "quiet": True, "no_warnings": True, "noprogress": True, "noplaylist": True}) as y:
            y.download([f"https://www.youtube.com/shorts/{vid}"])
    out = MEDIA / f"{vid}_sheet.jpg"
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                               capture_output=True, text=True).stdout.strip() or 30)
    step = max(2.0, dur / 16)          # at most 16 frames, so long videos are sampled evenly
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-vf",
                    f"fps=1/{step:.2f},scale=180:-2,pad=iw+4:ih+4:2:2:white,tile=8x2",
                    "-frames:v", "1", "-q:v", "4", str(out)], check=True)
    return out


if __name__ == "__main__":
    for v in sys.argv[1:]:
        try:
            print("ok", sheet(v))
        except Exception as e:
            print("FAIL", v, str(e)[:150])
