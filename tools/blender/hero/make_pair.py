"""Specs for an English + Hindi pair of hero Shorts rendered ONCE (25 Nov 2026).

research/hero/<name>/shots.json holds {"shots": [...], "hi_labels": {...}} (one shot per script scene).

    python tools/blender/hero/make_pair.py <name> init     # write <name>/spec.json and <name>_hi/spec.json
    python tools/blender/hero/timings.py <name>            # (and <name>_hi) fit seconds to each voice
    python tools/blender/hero/make_pair.py <name> both     # render_seconds = the longer, event_seconds = the shorter
    bash tools/blender/hero/render_micro.sh <name>         # one render, frames serve both languages
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
name, mode = sys.argv[1], sys.argv[2]
H = ROOT / "research" / "hero"
src = json.loads((H / name / "shots.json").read_text(encoding="utf-8"))
pair = (name, name + "_hi") + tuple(sys.argv[3:])      # extra variants sharing the render, e.g. popcorn_wiw
if mode == "init":
    for n in pair:
        d = {"assets_dir": "assets/3d", "renderer": "micro", "end_beat_s": 0.6,
             "shots": [dict(s, seconds=0) for s in src["shots"]]}
        if n.endswith("_hi"):
            d["hi_labels"] = src.get("hi_labels", {})
        if n.endswith("_wiw") and src.get("wiw_labels"):      # a variant can relabel its shots
            for sh, lab in zip(d["shots"], src["wiw_labels"]):
                if lab is not None:
                    sh["label"] = lab
        (H / n).mkdir(exist_ok=True)
        (H / n / "spec.json").write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    print("specs written", pair)
elif mode == "both":
    specs = [json.loads((H / n / "spec.json").read_text(encoding="utf-8")) for n in pair]
    assert len({len(d["shots"]) for d in specs}) == 1, "all variants must have the same scenes"
    for shots in zip(*(d["shots"] for d in specs)):
        r = round(max(s["seconds"] for s in shots) + 0.1, 3)
        e = round(min(s["seconds"] for s in shots), 3)
        for s in shots:
            s["render_seconds"], s["event_seconds"] = r, e
    en = specs[0]
    for n, d in zip(pair, specs):
        (H / n / "spec.json").write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    print("render seconds:", [s["render_seconds"] for s in en["shots"]],
          "total", round(sum(s["render_seconds"] for s in en["shots"]), 1))
