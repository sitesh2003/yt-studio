"""Take a scheduled hero video OFF its schedule, keeping it private, so a fixed version can take its slot (27 Nov 2026).

    STUDIO_CHANNEL=<main|hi|wiw> python tools/hero_unschedule.py <name> <video_id> "<reason>"

Nothing is deleted: the old upload stays private with no publish time, "[replaced]" goes in front of its title, and
its history entry becomes status "replaced" (so ensure_public never makes it public) with the job renamed, so
hero_publish.py can upload the fixed version under the same name. Prints the old slot for HERO_AT.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agents import youtube   # noqa: E402
from agents.core import CHANNEL, DATA, read_json, write_json   # noqa: E402

name, vid, reason = sys.argv[1], sys.argv[2], sys.argv[3]
y = youtube.yt()
items = y.videos().list(part="status,snippet", id=vid).execute().get("items", [])
if not items:
    sys.exit(f"{vid} not found on the {CHANNEL} channel")
v = items[0]
st, sn = v["status"], v["snippet"]
if st["privacyStatus"] == "public":
    sys.exit(f"{vid} is already PUBLIC: not touched (public changes need the owner's OK)")
slot = st.get("publishAt")
st["privacyStatus"] = "private"
st.pop("publishAt", None)
y.videos().update(part="status", body={"id": vid, "status": st}).execute()
if not sn["title"].startswith("[replaced]"):
    body = {"id": vid, "snippet": {"title": ("[replaced] " + sn["title"])[:100], "categoryId": sn["categoryId"],
                                   "description": sn.get("description", ""), "tags": sn.get("tags", [])}}
    y.videos().update(part="snippet", body=body).execute()
hist = read_json(DATA / "history.json", []) or []
for h in hist:
    if h.get("video_id") == vid:
        h.update(status="replaced", replaced_reason=reason, job=h.get("job", "") + "_replaced", old_publish_at=slot)
write_json(DATA / "history.json", hist)
print(f"UNSCHEDULED {CHANNEL} {vid} (was {slot}); private, history marked replaced")
print(f"HERO_AT={slot}")
