"""Fit a hero spec to its narration (20 Nov 2026): python tools/blender/hero/timings.py <name>

Each shot lasts exactly its scene (scenes.json); the last shot keeps a short beat after the question
(end_beat_s, 0.6 s) so the music carries the ending. An x-ray shot's skeleton appears while "bone by bone"
is spoken and its muscles while "muscle by muscle" is spoken (from words.json), so picture and words match."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
name = sys.argv[1]
d = ROOT / "research" / "hero" / name
spec = json.loads((d / "spec.json").read_text(encoding="utf-8"))
scenes = json.loads((d / "scenes.json").read_text(encoding="utf-8"))
words = json.loads((d / "words.json").read_text(encoding="utf-8"))
norm = lambda w: re.sub(r"[^a-z]", "", w.lower())

for i, (shot, (a, b)) in enumerate(zip(spec["shots"], scenes)):
    shot["seconds"] = round(b - a, 3)
    if shot["kind"] == "xray_scan":
        inside = [w for w in words if a <= w["start"] < b]
        first = lambda key: next((w["start"] - a for w in inside if norm(w["text"]).startswith(key)), None)
        tb, tm = first("bone"), first("muscle")
        then = next((w["start"] - a for w in inside if norm(w["text"]) == "then"), b - a - 0.4)
        tb = 0.3   # the skeleton builds from the shot's first words ("rebuilt it in a computer"), so each
        #            bone group is on screen long enough to see; the muscles land on "muscle by muscle"
        tm = (tb + then) / 2 if tm is None else tm - 0.1
        shot["reveal"] = {"bones": [round(tb, 2), round(tm - 0.1, 2)], "muscles": [round(tm, 2), round(then, 2)]}
spec["shots"][-1]["seconds"] = round(spec["shots"][-1]["seconds"] + spec.get("end_beat_s", 0.6), 3)
(d / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
print([(s["kind"], s["seconds"], s.get("reveal")) for s in spec["shots"]])
