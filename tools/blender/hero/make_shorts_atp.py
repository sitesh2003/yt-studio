"""Four vertical chapter Shorts cut from the ATP book (26 Nov 2026): same atp_ kinds, a wider lens for 9:16.

    python tools/blender/hero/make_shorts_atp.py      # writes research/hero/<name>/shots.json for all four
    then per Short: make_pair.py <name> init -> voices -> timings.py -> make_pair.py <name> both -> render_micro.sh
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WATT = "Watt et al. 2010, PNAS 107:16823"
TYM = "Tymoczko, Berg & Stryer, Biochemistry: A Short Course"
LENS = {"atp_mito": 25, "atp_chain": 22, "atp_dam": 28, "atp_muscle": 22, "atp_molecule": 20, "atp_noji": 26,
        "atp_synthase": 35}                                     # 9:16 is narrow: wide subjects need a shorter lens


def S(kind, **k):
    lens = 20 if k.get("dive") else LENS[kind]                # a dive flies in, so it starts wide
    return dict(kind=kind, overlay="label" if "label" in k else "none", lens=lens, **k)


SHORTS = {
    "atp_40kg": [
        S("atp_muscle", label=["ABOUT 40 kg A DAY", "used even at rest"], source=TYM),
        S("atp_molecule", split=True, label=["ABOUT 100 g", "in your body at once"]),
        S("atp_molecule", label=["ATP", "the energy coin cells spend"]),
        S("atp_molecule", split=True, label=["SPENT ATP", "loses a piece, becomes ADP"]),
        S("atp_mito", dive=True, label=["REBUILT AGAIN AND AGAIN", "hundreds of times a day"]),
        S("atp_synthase", mode="orbit", slow=0.4, label=["ATP SYNTHASE", "a spinning turbine"]),
        S("atp_synthase", mode="spin", slow=0.5, label=["100 g HELD, 40 kg USED", "every single day"]),
        S("atp_muscle"),
    ],
    "atp_turbine": [
        S("atp_synthase", mode="spin", slow=0.5, label=["~100 TURNS A SECOND", "shown here slowed down"], source=WATT),
        S("atp_mito", dive=True, label=["MITOCHONDRIA", "the folded inner membrane"]),
        S("atp_dam", label=["A PROTON DAM", "crowded on one side"]),
        S("atp_synthase", mode="protons", slow=0.35, label=["8 PIECES", "the ring, in animals"], source=WATT),
        S("atp_synthase", mode="protons", slow=0.35, label=["8 PROTONS = 1 TURN", "one proton, one step"]),
        S("atp_noji", slow=0.5, fil=24, tgt_x=0, slide_rough=0.6, label=["1997", "the spin, seen directly"], source="Noji et al. 1997, Nature 386:299"),
        S("atp_synthase", mode="orbit", slow=0.4, label=["REAL TURBINES", "spun by protons"]),
        S("atp_muscle"),
    ],
    "atp_three": [
        S("atp_synthase", mode="beta", slow=0.3, label=["3 ATP PER TURN", "one from each part"], source=WATT),
        S("atp_synthase", mode="beta", slow=0.3, label=["THE CROOKED SHAFT", "turns inside the head"]),
        S("atp_synthase", mode="beta", slow=0.3, label=["THREE WORKING PARTS", "each changes shape"]),
        S("atp_synthase", mode="beta", slow=0.3, label=["OPEN - LOOSE", "grab, then hold"],
          source="Boyer 1997, Annual Review of Biochemistry 66:717"),
        S("atp_synthase", mode="beta", slow=0.3, label=["TIGHT", "pressed into ATP"]),
        S("atp_synthase", mode="orbit", slow=0.4, label=["NOBEL PRIZE 1997", "Paul Boyer and John Walker"]),
        S("atp_synthase", mode="spin", slow=0.5, label=["3 ATP EVERY TURN", "~100 turns a second"]),
        S("atp_muscle"),
    ],
    "atp_where": [
        S("atp_molecule", split=True, label=["EVEN SITTING STILL", "about 40 kg a day"], source=TYM),
        S("atp_muscle", label=["MUSCLES", "every pull spends ATP"]),
        S("atp_molecule", label=["NERVES", "pumps keep them ready to fire"]),
        S("atp_molecule", split=True, label=["BUILDING", "every new protein costs ATP"]),
        S("atp_mito", label=["HEART AND BRAIN", "never stop asking"]),
        S("atp_synthase", mode="spin", slow=0.5, label=["REBUILT BY TURBINES", "~100 turns a second"], source=WATT),
        S("atp_synthase", mode="orbit", slow=0.4, label=["40 kg A DAY", "every bit rebuilt"]),
        S("atp_muscle"),
    ],
}

HI = {
    "ABOUT 40 kg A DAY": "रोज़ लगभग 40 kg", "used even at rest": "आराम में भी खर्च",
    "ABOUT 100 g": "लगभग 100 g", "in your body at once": "शरीर में एक समय पर",
    "ATP": "ATP", "the energy coin cells spend": "कोशिकाओं का ऊर्जा-सिक्का",
    "SPENT ATP": "खर्च हुआ ATP", "loses a piece, becomes ADP": "एक टुकड़ा खोकर ADP बनता है",
    "REBUILT AGAIN AND AGAIN": "बार-बार फिर से बनता है", "hundreds of times a day": "दिन में सैकड़ों बार",
    "ATP SYNTHASE": "ATP SYNTHASE", "a spinning turbine": "घूमता turbine",
    "100 g HELD, 40 kg USED": "100 g पास, 40 kg खर्च", "every single day": "हर एक दिन",
    "~100 TURNS A SECOND": "हर second ~100 चक्कर", "shown here slowed down": "यहाँ धीमा दिखाया गया",
    "MITOCHONDRIA": "माइटोकॉन्ड्रिया", "the folded inner membrane": "मुड़ी हुई भीतरी झिल्ली",
    "A PROTON DAM": "प्रोटॉन का बाँध", "crowded on one side": "एक तरफ़ भीड़",
    "8 PIECES": "8 टुकड़े", "the ring, in animals": "जानवरों में यह छल्ला",
    "8 PROTONS = 1 TURN": "8 प्रोटॉन = 1 चक्कर", "one proton, one step": "एक प्रोटॉन, एक कदम",
    "1997": "1997", "the spin, seen directly": "घूमना, सीधे देखा गया",
    "REAL TURBINES": "असली turbine", "spun by protons": "प्रोटॉन से घूमते",
    "3 ATP PER TURN": "हर चक्कर में 3 ATP", "one from each part": "हर हिस्से से एक",
    "THE CROOKED SHAFT": "टेढ़ी धुरी", "turns inside the head": "सिर के अंदर घूमती है",
    "THREE WORKING PARTS": "तीन काम करने वाले हिस्से", "each changes shape": "हर एक आकार बदलता है",
    "OPEN - LOOSE": "खुला - ढीला", "grab, then hold": "पकड़ो, फिर थामो",
    "TIGHT": "कसा हुआ", "pressed into ATP": "दबाकर ATP बनता है",
    "NOBEL PRIZE 1997": "NOBEL PRIZE 1997", "Paul Boyer and John Walker": "Paul Boyer और John Walker",
    "3 ATP EVERY TURN": "हर चक्कर 3 ATP", "~100 turns a second": "हर second ~100 चक्कर",
    "EVEN SITTING STILL": "चुपचाप बैठे हुए भी", "about 40 kg a day": "रोज़ लगभग 40 kg",
    "MUSCLES": "मांसपेशियाँ", "every pull spends ATP": "हर खिंचाव ATP खर्च करता है",
    "NERVES": "नसें", "pumps keep them ready to fire": "pump उन्हें तैयार रखते हैं",
    "BUILDING": "निर्माण", "every new protein costs ATP": "हर नया protein ATP माँगता है",
    "HEART AND BRAIN": "दिल और दिमाग़", "never stop asking": "कभी माँगना बंद नहीं करते",
    "REBUILT BY TURBINES": "turbine फिर से बनाते हैं",
    "40 kg A DAY": "रोज़ 40 kg", "every bit rebuilt": "हर अंश फिर से बनता है",
}

for name, shots in SHORTS.items():
    labels = {t for s in shots for t in s.get("label", [])}
    missing = labels - set(HI)
    assert not missing, (name, missing)
    d = ROOT / "research" / "hero" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "shots.json").write_text(json.dumps({"shots": shots, "hi_labels": {k: HI[k] for k in sorted(labels)}},
                                             indent=2, ensure_ascii=False), encoding="utf-8")
    print(name, len(shots), "shots")
