"""Why It Works long film (27 Nov 2026): "The Physics Of The Smallest Motor Inside You".
Re-tells ATP synthase as PHYSICS (power, voltage and field, stored energy, rotor, torque and efficiency, thermal
noise, motor/generator, short circuit, feedback) over the ATP book's shots ("src" = index in book_atp_long).

Checked numbers:
  Membrane potential ~150-180 mV (Perry et al. 2011, BioTechniques 50:98; total proton-motive force 180-220 mV).
  Field ~0.15 V / 5 nm = 3e7 V/m, "comparable to a lightning bolt" (Lane & Martin 2010, Nature 467:929).
  F1 turns in 120-degree steps, one ATP each; torque ~40 pN nm; work per step ~80-90 pN nm ~ free energy of ATP
  in the cell (~90 pN nm) -> near 100% efficiency (Yasuda, Noji, Kinosita & Yoshida 1998, Cell 93:1117).
  Later methods give 56-74 pN nm, so "about forty" is said as the 1998 measurement.
  kT at 37 C = 1.38e-23 * 310 = 4.3e-21 J = 4.3 pN nm; 90 / 4.3 ~ 21 ("about twenty times").
  One motor: 4e-20 N m x 2 pi x 100 /s = 2.5e-17 W; 100 W / 2.5e-17 W = 4e18 ("four billion billion").
  Resting power: ~1,700 kcal/day = 82 W ("roughly eighty to a hundred watts"). Car engines ~25-35% efficient.
  8-piece ring, ~100 turns/s, 3 ATP/turn (Watt et al. 2010, PNAS 107:16823). F1 head ~10 nm.
"""
import copy, json, os, sys
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(R); sys.path.insert(0, R)

S_Y = "Yasuda, Noji, Kinosita & Yoshida 1998, Cell 93:1117"
S_LM = "Lane & Martin 2010, Nature 467:929"
S_MP = "Perry et al. 2011, BioTechniques 50:98"
S_W = "Watt et al. 2010, PNAS 107:16823"
S_KT = "Thermal energy kT = Boltzmann constant x temperature"
S_PW = "Power = torque x angular speed (from Yasuda et al. 1998 and Watt et al. 2010)"
S_BMR = "Typical resting metabolic rate ~1,700 kcal/day = ~80 W"

def L(a, b, src=None):
    d = {"overlay": "label", "label": [a, b]}
    if src:
        d["source"] = src
    return d

def C(n, t):
    return {"overlay": "chapter", "chapter": [f"CHAPTER {n}", t]}

NONE = {"overlay": "none"}

SC = [
 ("Inside you right now are motors so small that tens of thousands, side by side, would fit across the full stop at the end of a sentence.", 0, NONE),
 ("Each one spins about a hundred times a second. And it's a real rotary motor, with a rotor, a shaft and a stator, like the motor in a drill.", 1, {}),
 ("It runs on electricity. Not from a socket, but from protons, pushed across a membrane.", 2, NONE),
 ("Its name is ATP synthase. And this is the physics of how it works.", 21, L("ATP SYNTHASE", "a rotary motor")),

 ("Chapter one. How much power do you need?", 3, C(1, "HOW MUCH POWER?")),
 ("Even resting, your body uses energy at roughly eighty to a hundred watts. About as much as an old, bright light bulb.", 4, L("80 TO 100 WATTS", "your body at rest", S_BMR)),
 ("Almost all of that is paid out in one molecule, ATP, the energy currency of your cells.", 5, L("ATP", "the energy currency")),
 ("You hold only about a hundred grams of it at once. Yet you use about forty kilograms a day.", 6, {}),
 ("So every molecule is rebuilt about four hundred times a day.", 37, L("ABOUT 400 TIMES", "every molecule, every day")),
 ("The machine that rebuilds it is the motor. But first, it needs a power supply.", 7, NONE),

 ("Chapter two. A battery in a membrane.", 8, C(2, "A BATTERY IN A MEMBRANE")),
 ("The motors sit in the inner membrane of mitochondria, the power stations of the cell.", 9, {}),
 ("That membrane is folded again and again, to pack in as many motors as possible.", 10, {}),
 ("Food is broken down until its energy is carried by electrons.", 13, {}),
 ("Those electrons flow down a chain of proteins, a little like a current through a circuit.", 14, L("A CURRENT", "electrons down a chain")),
 ("Their energy drives pumps that push protons, which are positive charges, to one side of the membrane.", 15, {}),
 ("At the end of the chain, the electrons are handed to oxygen, and make water.", 16, {}),
 ("Pile up positive charge on one side, and you get a voltage. Across this membrane, it's about a hundred and fifty to a hundred and eighty millivolts.", 19, L("150 TO 180 mV", "across the membrane", S_MP)),
 ("That sounds tiny. But the membrane is only about five billionths of a metre thick. Divide the voltage by that distance, and the electric field is about thirty million volts per metre.", 20, L("30 MILLION V/m", "voltage / thickness", S_LM)),
 ("Scientists have compared that to the field in a lightning bolt, across every one of your mitochondria.", 36, L("LIKE LIGHTNING", "the field strength", S_LM)),

 ("Chapter three. Energy stored uphill.", 18, C(3, "ENERGY STORED UPHILL")),
 ("The protons are pushed back by two things at once: the voltage, and the crowding, because there are far more of them on one side.", 11, L("TWO PUSHES", "charge and crowding")),
 ("Together, they're called the proton-motive force. Like water held behind a dam, it's stored energy, waiting to flow downhill.", 72, L("PROTON-MOTIVE FORCE", "stored energy")),
 ("And the main way back through the membrane is through the motor.", 64, L("ONE WAY BACK", "through the motor")),

 ("Chapter four. The rotor.", 22, C(4, "THE ROTOR")),
 ("In the membrane sits a ring. In animals, it's made of eight identical pieces.", 23, {"source": S_W}),
 ("A proton drops onto one piece, rides the ring around, and is let out on the other side.", 24, {}),
 ("Eight protons, one full turn. About a hundred turns every second.", 25, {}),
 ("In 1997, scientists in Japan attached a glowing filament to the shaft, and filmed it turning.", 26, {}),
 ("The shaft is only about two billionths of a metre across. The smallest rotary motor anyone had ever seen.", 27, {}),

 ("Chapter five. Torque and efficiency.", 28, C(5, "TORQUE AND EFFICIENCY")),
 ("The spinning shaft turns inside a head with three working parts.", 29, {}),
 ("Each turn squeezes every part through three shapes, and each squeeze presses together one ATP.", 30, {}),
 ("Three parts, three ATP a turn. That's one every hundred and twenty degrees.", 32, {}),
 ("In 1998, the same team filmed the shaft clicking round in steps of exactly that size: a hundred and twenty degrees, one ATP each.", 61, L("120 DEGREE STEPS", "one ATP each", S_Y)),
 ("From how hard the filament was dragged through the water, they worked out the motor's torque, its turning force: about forty piconewton-nanometres.", 62, L("TORQUE ~40 pN nm", "measured in 1998", S_Y)),
 ("Multiply that torque by the angle of one step, and you get the work the motor does for every ATP.", 60, L("WORK = TORQUE x ANGLE", "for each step", S_Y)),
 ("And that work almost exactly matches the energy one ATP carries inside a cell. The motor inside your cells is close to one hundred percent efficient. A car engine manages about a quarter to a third.", 33, L("CLOSE TO 100%", "a car engine: 25 to 35%", S_Y)),
 ("How can anything work that well? Part of the answer: it's tiny. At this size, water molecules are constantly battering it from every side.", 93, NONE),
 ("The energy of that random jostling, at body temperature, is about four piconewton-nanometres. One ATP carries about twenty times more. Enough to beat the noise.", 91, L("THERMAL NOISE", "one ATP = ~20 x kT", S_KT)),

 ("Chapter six. The power of one motor.", 34, C(6, "THE POWER OF ONE MOTOR")),
 ("Power is torque times how fast something turns. Put in forty piconewton-nanometres, and a hundred turns a second.", 52, L("POWER = TORQUE x SPEED", "one motor", S_PW)),
 ("One motor makes about twenty-five billion-billionths of a watt.", 0, L("~2.5 x 10^-17 W", "one motor", S_PW)),
 ("To run a hundred-watt light bulb, you'd need about four billion billion of them, all spinning flat out.", 50, L("4 BILLION BILLION", "to light one bulb", S_PW)),
 ("That's roughly the job your mitochondria do for you, every moment, without a sound.", 35, NONE),

 ("Chapter seven. Motor, or generator?", 57, C(7, "MOTOR OR GENERATOR?")),
 ("Run an electric motor backwards and it becomes a generator. ATP synthase works both ways too.", 58, {}),
 ("Feed it ATP, and it spins the other way, splitting ATP and pumping protons back uphill.", 59, {}),
 ("Without oxygen, the bacterium E. coli does exactly this, spending ATP to keep its membrane charged.", 63, {}),
 ("Your mitochondria carry a brake, a small protein called IF1.", 65, {}),
 ("If the voltage collapses, IF1 largely stops the motors running backwards and wasting ATP.", 66, {}),

 ("Chapter eight. A short circuit.", 67, C(8, "A SHORT CIRCUIT")),
 ("Brown fat cells are packed with mitochondria.", 68, {}),
 ("Their membranes hold a protein called UCP1, a gap in the dam. Protons rush straight back through it, without passing through the motor.", 69, {}),
 ("In electrical terms, it's a short circuit. Current flows, but no useful work gets done.", 70, L("A SHORT CIRCUIT", "current, but no work")),
 ("So the energy comes out as heat, just as a short-circuited wire gets hot.", 71, {}),
 ("Newborn babies rely on it to keep warm. Adults keep smaller amounts, switched on by cold.", 73, {}),

 ("Chapter nine. Speed control.", 42, C(9, "SPEED CONTROL")),
 ("Start to sprint, and your muscles burn through ATP far faster.", 43, L("START TO SPRINT", "demand jumps")),
 ("Every ATP spent leaves behind ADP and phosphate.", 51, {}),
 ("Those are exactly what the motor needs. As they build up, it spins faster, and the chain pumps harder.", 52, {}),
 ("Nobody flips a switch. Spending energy is itself the signal to make more.", 53, NONE),
 ("Engineers call that negative feedback. And it's why you breathe harder: the chain needs more oxygen.", 54, L("NEGATIVE FEEDBACK", "demand sets the speed")),
 ("At full effort, a fit young adult can use roughly ten times as much oxygen as at rest.", 55, {}),

 ("So that's the physics of the motor inside you. A membrane charged like a battery. A field like lightning. A rotor turned by protons, stepping a hundred and twenty degrees at a time, close to perfectly efficient.", 91, NONE),
 ("All of it, smaller than a virus.", 92, NONE),
 ("Run an electric motor backwards and it becomes a generator, and this one does the same. So if a motor this small can be this efficient, what would you build if you could copy it?", 94, NONE),
]

base = json.load(open("research/hero/book_atp_long/spec.json", encoding="utf-8"))
spec = {k: v for k, v in base.items() if k != "shots"}
shots = []
for nar, src, ov in SC:
    sh = copy.deepcopy(base["shots"][src])
    for k in ("render_seconds", "event_seconds", "hi_labels", "hi_label"):
        sh.pop(k, None)
    sh.update(ov)
    if sh.get("overlay") == "none":
        sh.pop("label", None)
    sh["src"] = src
    shots.append(sh)
os.makedirs("research/hero/wiw_atp", exist_ok=True)
json.dump(dict(spec, shots=shots), open("research/hero/wiw_atp/spec.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

script = {
    "title_options": ["The Physics Of The Smallest Motor Inside You ⚡"],
    "facts": ["Numbers and sources in tools/blender/hero/make_wiw_atp.py docstring; biology as fact-checked in the ATP book "
              "(research/hero/book_atp_ext/facts_checked.md)."],
    "sources": "; ".join([S_Y, S_LM, S_MP, S_W, "Noji et al. 1997, Nature 386:299", "Campanella et al. 2008, Cell Metab 8:13",
                          "Fedorenko, Lishko & Kirichok 2012, Cell 151:400", "Brand & Nicholls 2011, Biochem J 435:297",
                          "Kaminsky, Arena & Myers 2015, Mayo Clin Proc 90:1515"]),
    "description": "Inside your cells, a rotary motor about ten billionths of a metre across turns about a hundred times a second, "
                   "powered by a membrane charged like a battery. We work through its physics: voltage and field strength, "
                   "torque, efficiency, thermal noise, power, generators, short circuits and feedback. In 3D, from published measurements.",
    "share": {"myth": "Machines inside living cells are sloppy compared with human-made engines.",
              "truth": "ATP synthase turns in 120-degree steps with a torque of about 40 pN nm, and its work per step nearly matches the energy in one ATP, close to 100% efficient (Yasuda et al. 1998, Cell).",
              "line": "The motor inside your cells is close to one hundred percent efficient. A car engine manages about a quarter to a third."},
    "tags": ["physics", "ATP synthase", "molecular motor", "biophysics", "why it works", "science explained", "3D animation"],
    "scenes": [{"narration": r[0]} for r in SC],
}
json.dump(script, open("research/hero/wiw_atp/script.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
w = sum(len(r[0].split()) for r in SC)
print("scenes", len(SC), "words", w, "est minutes at 160 wpm", round(w / 160, 1))
