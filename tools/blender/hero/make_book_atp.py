"""Spec for the ATP book (26 Nov 2026), landscape long film, one shot per script scene.

    python tools/blender/hero/make_book_atp.py        # writes research/hero/book_atp/spec.json (seconds 0)
    python tools/blender/hero/timings.py book_atp     # fits seconds to the voice
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
S = lambda kind, **k: dict(kind=kind, overlay="label" if "label" in k else "none", **k)
WATT = "Watt et al. 2010, PNAS 107:16823"
SH = [
    S("atp_synthase", mode="orbit", slow=0.4),
    S("atp_synthase", mode="spin", slow=0.5, label=["~100 TURNS A SECOND", "shown here slowed down"]),
    S("atp_mito", dive=True),
    S("atp_muscle", chapter=["CHAPTER 1", "What Powers Your Muscles?"]),
    S("atp_molecule", label=["ATP", "the energy coin cells spend"]),
    S("atp_molecule", split=True, label=["ABOUT 100 g", "in your whole body at once"]),
    S("atp_muscle", label=["ABOUT 40 kg A DAY", "used even at rest"], source="Tymoczko, Berg & Stryer, Biochemistry: A Short Course"),
    S("atp_mito"),
    S("atp_mito", dive=True, chapter=["CHAPTER 2", "Where Is ATP Made?"]),
    S("atp_mito", label=["MITOCHONDRION", "wrapped in two membranes"]),
    S("atp_mito", dive=True, label=["CRISTAE", "the folded inner membrane"]),
    S("atp_dam", label=["PROTONS", "the hidden power source"]),
    S("atp_chain", chapter=["CHAPTER 3", "Building The Proton Gradient"]),
    S("atp_chain", label=["ELECTRONS", "carry the energy from food"]),
    S("atp_chain", focus="pumps", label=["A BUCKET BRIGADE", "electrons passed along"]),
    S("atp_chain", focus="pumps", label=["THREE PUMPS", "Complexes I, III and IV"]),
    S("atp_chain", focus="iv", label=["COMPLEX IV", "electrons + oxygen make water"]),
    S("atp_chain", focus="iv", label=["WHY YOU BREATHE", "oxygen is the last stop"]),
    S("atp_dam", chapter=["CHAPTER 4", "A Membrane That Stores Energy"]),
    S("atp_dam", label=["A PROTON DAM", "crowded on one side"]),
    S("atp_dam", label=["ONE MAIN DOOR", "back across the membrane"]),
    S("atp_synthase", mode="orbit", slow=0.4, label=["ATP SYNTHASE", "the turbine"]),
    S("atp_synthase", mode="spin", slow=0.4, chapter=["CHAPTER 5", "What Spins The Turbine?"]),
    S("atp_synthase", mode="protons", slow=0.35, label=["8 PIECES", "the ring, in animals"], source=WATT),
    S("atp_synthase", mode="protons", slow=0.35, label=["ONE PROTON", "one step of the ring"]),
    S("atp_synthase", mode="spin", slow=0.5, label=["8 PROTONS = 1 TURN", "about 100 turns a second"], source=WATT),
    S("atp_noji", slow=0.5, label=["1997", "the spin, seen directly"], source="Noji et al. 1997, Nature 386:299"),
    S("atp_noji", slow=0.5, label=["ABOUT 2 nm WIDE", "the smallest rotary motor seen"]),
    S("atp_synthase", mode="beta", slow=0.3, chapter=["CHAPTER 6", "How Spinning Makes ATP"]),
    S("atp_synthase", mode="beta", slow=0.3, label=["THE CROOKED SHAFT", "turns inside the head"]),
    S("atp_synthase", mode="beta", slow=0.3, label=["THREE WORKING PARTS", "each changes shape"]),
    S("atp_synthase", mode="beta", slow=0.3, label=["OPEN - LOOSE - TIGHT", "the binding change"], source="Boyer 1997, Annual Review of Biochemistry 66:717"),
    S("atp_synthase", mode="beta", slow=0.3, label=["3 ATP PER TURN", "one from each part"], source=WATT),
    S("atp_synthase", mode="orbit", slow=0.4, label=["NOBEL PRIZE 1997", "Paul Boyer and John Walker"]),
    S("atp_muscle", chapter=["CHAPTER 7", "Where Does The ATP Go?"]),
    S("atp_muscle", label=["MUSCLES, NERVES, PROTEINS", "all paid in ATP"]),
    S("atp_mito", label=["HEART AND BRAIN", "never stop asking"]),
    S("atp_molecule", split=True, label=["EVEN SITTING STILL", "about 40 kg a day"]),
    S("atp_chain", cyanide=True, focus="iv", chapter=["CHAPTER 8", "When Cyanide Blocks The Chain"]),
    S("atp_chain", cyanide=True, focus="iv", label=["CYANIDE", "jams Complex IV, not the turbine"], source="Zuhra & Szabo 2022, FEBS Journal 289:2481"),
    S("atp_chain", cyanide=True, label=["THE DAM DRAINS", "the turbines slow down"]),
    S("atp_chain", cyanide=True, label=["NO NEW ATP", "heart and brain hit hardest"]),
    S("atp_mito"),
    S("atp_synthase", mode="orbit", slow=0.4, label=["~100 TURNS A SECOND", "3 ATP every turn"]),
    S("atp_muscle"),
]
spec = {"assets_dir": "assets/3d", "renderer": "micro", "aspect": "landscape", "long": True, "caption_scale": 1.0,
        "end_beat_s": 0.8, "shots": [dict(s, seconds=0) for s in SH]}
script = json.loads((ROOT / "research/hero/book_atp/script.json").read_text(encoding="utf-8"))
assert len(script["scenes"]) == len(SH), (len(script["scenes"]), len(SH))
(ROOT / "research/hero/book_atp/spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
print("book spec:", len(SH), "shots")
