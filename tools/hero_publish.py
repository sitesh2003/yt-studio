"""Upload a finished, CHECKED 3D hero Short as PRIVATE, scheduled to go public later (20 Nov 2026).

    STUDIO_CHANNEL=<main|hi|wiw> python tools/hero_publish.py <name> [thumbnail_seconds]

Owner: "make a queue... private... then public", "keep it in bank". YouTube's private + scheduled state is
the bank for hero Shorts: nobody can see the video until its slot. At most ONE hero Short goes public per
day per channel (the latest slot of a day with no hero yet), so the daily videos keep their own slots.
Run only after the video was checked frame by frame and listened to."""
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agents import subtitles, youtube   # noqa: E402
from agents.core import CHANNEL, DATA, config, read_json, write_json   # noqa: E402

name = sys.argv[1]
thumb_t = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
d = ROOT / "research" / "hero" / name
script = json.loads((d / "script.json").read_text(encoding="utf-8"))
words = json.loads((d / "words.json").read_text(encoding="utf-8"))
job = ROOT / "jobs" / f"hero_{name}"
job.mkdir(parents=True, exist_ok=True)
shutil.copy(d / f"{name}.mp4", job / "final.mp4")
spec = json.loads((d / "spec.json").read_text(encoding="utf-8")) if (d / "spec.json").exists() else {}
LONG = spec.get("aspect") == "landscape"      # 24 Nov 2026: long films (16:9, chapters), not Shorts
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(thumb_t), "-i", str(job / "final.mp4"),
                "-frames:v", "1", "-vf", "scale=1280:720" if LONG else "scale=720:1280", "-q:v", "3",
                str(job / "thumbnail.jpg")], check=True)

hist = read_json(DATA / "history.json", []) or []
if any(h.get("job") == f"hero_{name}" and h.get("video_id") for h in hist):
    sys.exit(f"hero_{name} is already uploaded")

# the slot: the last slot of the first day (from tomorrow) that has no hero Short yet and a free slot
et = ZoneInfo("America/New_York")
hero_days = {dt.datetime.fromisoformat(h["publish_at"]).astimezone(et).date()
             for h in hist if h.get("hero_3d") and h.get("publish_at")}
p = config()["publish"]
used = set(read_json(DATA / "scheduled.json", []) or [])
try:
    used |= {dt.datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(et).isoformat()
             for t in youtube._scheduled_times()}
except Exception:
    pass
now = dt.datetime.now(et)
slot = None
for day in range(1, 40):
    day_ = (now + dt.timedelta(days=day)).date()
    if day_ in hero_days:
        continue
    for hhmm in reversed(p["slots_et"][:p["videos_per_day"]]):
        h_, m_ = map(int, hhmm.split(":"))
        t = dt.datetime(day_.year, day_.month, day_.day, h_, m_, tzinfo=et)
        if t.isoformat() not in used:
            slot = t
            break
    if slot:
        break

import os   # noqa: E402
if os.environ.get("HERO_AT"):   # a fixed slot (e.g. to place a Short between others), ISO time with offset
    slot = dt.datetime.fromisoformat(os.environ["HERO_AT"])
lines = [s["narration"] for s in script["scenes"]]
chapters = ""
if LONG:   # YouTube chapters: 0:00 first, then each chapter card's cut (voice times = the cuts, gated)
    spans = json.loads((d / "scenes.json").read_text(encoding="utf-8"))
    hindi = CHANNEL == "hi"
    rows = [(0, "शुरुआत" if hindi else "Intro")]
    for i, sh in enumerate(spec["shots"]):
        if sh.get("chapter"):
            nm = sh["chapter"][1]
            rows.append((int(spans[i][0]), nm if hindi else nm.title().replace("T. Rex", "T. rex")))
    chapters = "\n\n" + "\n".join(f"{t // 60}:{t % 60:02d} {nm}" for t, nm in rows)
credits = spec.get("credits") or (
    "3D: every model built from scratch in Blender (procedural; no stock models or footage)."
    if spec.get("renderer") == "micro" else
    "3D models: Quaternius, Animated LowPoly Dinosaurs (CC0); Kenney, Car Kit (CC0). Animated in Blender.")
desc = (script.get("description", "") + chapters + "\n\nSources: " + script.get("sources", "") + "\n" +
        credits + "\n\n"
        "How this was made: the script is researched and fact-checked against published research (sources above), "
        "narrated by an AI voice, and animated and edited with open-source software.")
meta = {"title": script["title_options"][0], "description": desc, "tags": script.get("tags", []),
        "thumbnail": "thumbnail.jpg", "scene_lines": lines}   # captions are burned in: no second track
write_json(job / "meta.json", meta)
vid, when = youtube.upload(job, meta, slot)
print(f"UPLOADED {CHANNEL} {vid} private, goes public {when}; thumbnail: {meta.get('thumbnail_set')}")
hist = read_json(DATA / "history.json", []) or []
hist.append({"job": f"hero_{name}", "topic": script["title_options"][0], "title": meta["title"], "description": desc,
             "tags": meta["tags"], "hook": lines[0], "status": "scheduled", "narration": " ".join(lines),
             "voice_engine": config()["voice"].get("engine"), "countdown": False, "hero_3d": True,
             "question": lines[-1], "video_id": vid, "publish_at": when, "thumbnail_set": meta.get("thumbnail_set")})
write_json(DATA / "history.json", hist)
qf = DATA.parent / "hero_queue.json" if CHANNEL != "main" else DATA / "hero_queue.json"
q = read_json(qf, {}) or {}
for it in q.get("queue", []):
    if it.get("name") == os.environ.get("HERO_QNAME", name):
        it.update(status="uploaded", video_id=vid, public_at=when)
        break
else:
    q.setdefault("queue", []).append({"name": os.environ.get("HERO_QNAME", name), "channel": CHANNEL, "title": meta["title"], "status": "uploaded",
                                      "video_id": vid, "public_at": when})
write_json(qf, q)
