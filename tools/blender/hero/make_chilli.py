"""Specs for the chilli Short, English + Hindi from ONE render (25 Nov 2026).

    python tools/blender/hero/make_chilli.py          # writes both specs (seconds 0)
    python tools/blender/hero/timings.py chilli_burn  # and chilli_burn_hi: fits seconds to each voice
    python tools/blender/hero/make_chilli.py --both   # render_seconds = the longer language, events in the shorter

Facts: Caterina et al. 1997 Nature 389:816 (TRPV1, ~43 C); Nobel Prize 2021 (Julius); Nolden, Lenart & Hayes
2019 Physiology & Behavior (milk).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHOTS = [
    {"kind": "chilli_macro", "overlay": "label", "label": ["NO REAL HEAT", "your mouth stays about 37 °C"], "fstop": 4.0},
    {"kind": "membrane_dive", "overlay": "label", "label": ["TRPV1", "a heat alarm on your nerves"]},
    {"kind": "heat_open", "overlay": "label", "label": ["OPENS AT ~43 °C", "about 109 °F"],
     "source": "Caterina et al. 1997, Nature 389:816"},
    {"kind": "capsaicin_open", "overlay": "label", "label": ["CAPSAICIN", "opens it with NO heat"]},
    {"kind": "nerve_pulse", "overlay": "label", "label": ["SAME ALARM", "your brain hears HOT"]},
    {"kind": "channel_orbit", "overlay": "label", "label": ["NOBEL PRIZE 2021", "for finding this sensor"],
     "gold": True, "source": "Nobel Prize in Physiology or Medicine 2021"},
    {"kind": "capsaicin_leave", "overlay": "label", "label": ["MILK WORKS BEST", "even skim milk"],
     "source": "Nolden, Lenart & Hayes 2019, Physiology & Behavior"},
    {"kind": "pull_back", "overlay": "label", "label": ["NOT HEAT", "a heat ALARM"]},
    {"kind": "cold_tease", "overlay": "none"},
]
HI = {
    "NO REAL HEAT": "असली गर्मी नहीं",
    "your mouth stays about 37 °C": "मुँह लगभग 37 °C ही रहता है",
    "a heat alarm on your nerves": "नसों पर गर्मी का अलार्म",
    "OPENS AT ~43 °C": "लगभग 43 °C पर खुलता है",
    "about 109 °F": "जलाने वाली गर्मी",
    "CAPSAICIN": "CAPSAICIN",
    "opens it with NO heat": "बिना गर्मी के खोल देता है",
    "SAME ALARM": "वही अलार्म",
    "your brain hears HOT": "दिमाग़ सुनता है: गर्म!",
    "NOBEL PRIZE 2021": "NOBEL PRIZE 2021",
    "for finding this sensor": "इस sensor की खोज के लिए",
    "MILK WORKS BEST": "दूध सबसे अच्छा",
    "even skim milk": "बिना मलाई वाला भी",
    "NOT HEAT": "गर्मी नहीं",
    "a heat ALARM": "गर्मी का अलार्म",
}


def spec(name):
    return ROOT / "research" / "hero" / name / "spec.json"


if "--both" in sys.argv:
    en, hi = (json.loads(spec(n).read_text(encoding="utf-8")) for n in ("chilli_burn", "chilli_burn_hi"))
    for a, b in zip(en["shots"], hi["shots"]):
        r = round(max(a["seconds"], b["seconds"]) + 0.1, 3)
        e = round(min(a["seconds"], b["seconds"]), 3)
        for s in (a, b):
            s["render_seconds"], s["event_seconds"] = r, e
    for n, d in (("chilli_burn", en), ("chilli_burn_hi", hi)):
        spec(n).write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    print("render seconds:", [s["render_seconds"] for s in en["shots"]], "total", sum(s["render_seconds"] for s in en["shots"]))
else:
    for n in ("chilli_burn", "chilli_burn_hi"):
        d = {"assets_dir": "assets/3d", "renderer": "micro", "end_beat_s": 0.6,
             "shots": [dict(s, seconds=0) for s in SHOTS]}
        if n.endswith("_hi"):
            d["hi_labels"] = HI
        spec(n).write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    print("specs written")
