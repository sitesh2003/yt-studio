"""Why It Works long film (27 Nov 2026): "The Physics Of T. rex: Why Giants Can't Sprint".
Owner rule 27 Nov: every channel gets two ~10-min films a week. This one re-tells the T. rex film as PHYSICS
(square-cube law, torque, triangulation, pressure, levers, kinetic energy) over the SAME 3D shots
(render once, publish many: each shot carries "src", its index in trex_long, so its frames can be reused).

Worked physics:
  Hatchling ~0.9 m (Funston 2021) -> Sue ~12 m: 13.3x longer. Same shape: weight x 13^3 ~ 2,200 (">2,000");
  bone cross-section x 13^2 ~ 170. Double size: weight x8, bone area x4 -> stress x2 (Galileo 1638).
  Growth ~2 kg/day for ~4 years = 2,920 kg ("nearly three tonnes") (Erickson et al. 2004).
  Bite 34,522 N (Gignac & Erickson 2017) / 9.81 = 3,519 kg-weight ("about three and a half tonnes").
  Impact (rough, labelled): 10 km rock, density ~2,600 kg/m3 -> 1.36e15 kg; at 20 km/s KE = 2.7e23 J;
  Hiroshima ~15 kt = 6.3e13 J -> ~4e9 ("billions"); even at 12 km/s still >1e9.
"""
import copy, json, os, sys
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(R); sys.path.insert(0, R)

S_SQ = "Square-cube law: Galileo, Two New Sciences (1638); Haldane 1926, 'On Being the Right Size'"
S_COM = "Hutchinson et al. 2011, PLoS ONE (mass and centre of mass)"
S_KE = "Kinetic energy = 1/2 m v^2. Rough estimate: 10 km rock, ~2.6 t/m3, ~20 km/s; Schulte et al. 2010, Science"
S_P = "Pressure = force / area"

# (narration, src index in trex_long, overrides)
SC = [
 ("A Tyrannosaurus rex weighed about as much as six small cars. So why couldn't something that powerful run? The answer isn't about muscle. It's about a simple rule of geometry.", 0, {}),
 ("Make any animal bigger, and its weight grows much faster than the strength of its bones. At T. rex size, a full sprint would likely have put more stress on its legs than they could take.", 1, {}),
 ("That's why, in the best computer model we have, a car at city speed simply drives away from it.", 2, {}),
 ("In this film we'll take the movie monster apart with physics: geometry, balance, pressure, levers and energy. One question at a time. And we'll start with the rule that shaped everything.", 3, {}),

 ("Chapter one. The cube rule.", 4, {"chapter": ["CHAPTER 1", "THE CUBE RULE"]}),
 ("Tyrannosaurs began small. Fossil embryos from close relatives suggest a hatchling about ninety centimetres long, roughly the size of a small dog.", 5, {}),
 ("An adult like Sue was about twelve metres long. That's about thirteen times longer. But its weight didn't grow thirteen times.", 6,
  {"label": ["13 TIMES LONGER", "hatchling to adult"], "source": "Funston et al. 2021; Field Museum (FMNH PR 2081)"}),
 ("Weight depends on volume: length, times width, times height. Make an animal thirteen times bigger in every direction, and it becomes thirteen, times thirteen, times thirteen. That's more than two thousand times heavier, if it kept the same shape.", 7,
  {"overlay": "label", "label": ["13 x 13 x 13", "more than 2,000 times heavier"], "source": S_SQ}),
 ("But the strength of a bone depends on its cross-section, the area you'd see if you cut straight across it. That only grows with the square: about a hundred and seventy times. Weight wins, by a long way. It's called the square-cube law, and Galileo worked it out almost four hundred years ago.", 8,
  {"overlay": "label", "label": ["SQUARE-CUBE LAW", "weight x 2,000, bone x 170"], "source": S_SQ}),

 ("Chapter two. Growing fast.", 9, {"chapter": ["CHAPTER 2", "GROWING FAST"]}),
 ("Young T. rex were small enough to beat the rule. Long, slender legs and a light body made them quick on their feet.", 10,
  {"label": ["LONG, SLIM LEGS", "light and quick"]}),
 ("Scientists think they hunted smaller, faster animals that the giant adults couldn't catch.", 11, {}),
 ("Then came the growth spurt. Growth rings inside the bones, a little like the rings in a tree trunk, show how fast each animal grew.", 12, {}),
 ("Thin slices cut from the leg bones of two young T. rex, nicknamed Jane and Petey, showed they were about thirteen and fifteen years old, and still growing fast.", 13, {}),
 ("At its peak, a teenage T. rex added roughly two kilograms of body every single day, for about four years. That's nearly three tonnes of new animal.", 14, {}),
 ("And every kilogram it added made the cube rule bite harder. The bigger it got, the more carefully it had to move.", 15, {}),

 ("Chapter three. A balancing act.", 16, {"chapter": ["CHAPTER 3", "A BALANCING ACT"]}),
 ("Sue, the most complete T. rex skeleton ever found, measured about twelve metres from nose to tail.", 17, {}),
 ("Estimates vary, but an adult like Sue weighed roughly eight tonnes. On a giant see-saw, you'd need about six small cars to balance it.", 18, {}),
 ("Its skull alone was about one point four metres long. And all of that weight sat far out in front of the hips.", 19, {}),
 ("Think of the hips as the pivot of a see-saw. A heavy head out in front tries to tip the whole body forward. Physicists call that turning effect torque: the weight, times its distance from the pivot.", 18,
  {"overlay": "label", "label": ["TORQUE", "weight x distance from the pivot"], "source": "Torque = force x lever arm"}),
 ("The answer was the tail. A long, heavy tail stretched out behind, pulling the other way. Head and tail balanced, and the centre of mass ended up close to the hips, over the feet.", 21,
  {"label": ["THE TAIL", "a counterweight"], "source": S_COM}),
 ("Balanced, yes. But could all eight tonnes of it actually run?", 22, {}),

 ("Chapter four. Why it couldn't run.", 23, {"chapter": ["CHAPTER 4", "WHY IT COULDN'T RUN"]}),
 ("In 2017, a team in Britain built a T. rex inside a computer, with every bone, and every muscle that pulled on them.", 24, {}),
 ("Then they let the computer try thousands of ways to fire those muscles, searching for the fastest way to move.", 25, {}),
 ("Running means landing hard on one leg at a time, and each landing pushes on the bone far harder than standing still. At every running speed, the stress in its leg bones climbed so high that they would likely have broken. That's the cube rule again. Make an animal twice as big and it gets eight times heavier, but its bones get only four times stronger. Double the stress.", 26, {}),
 ("An earlier study reached the same wall from another side. To sprint fast, an animal this heavy would need about forty percent of its whole body in the muscles of each leg. Nothing alive carries that much.", 27, {}),
 ("So its top speed was probably a brisk walk. In the 2017 model, that was about twenty kilometres an hour, or twelve miles an hour.", 28, {}),
 ("Elephants follow the same physics. Even at top speed, they never get all four feet off the ground at once.", 29, {}),
 ("A car on a city street would leave it behind. So would a fit cyclist.", 30, {}),
 ("So how did a slow giant become a top predator? Part of the answer is in how it saw the world.", 31, {}),

 ("Chapter five. Eyes that measure distance.", 32, {"chapter": ["CHAPTER 5", "EYES THAT MEASURE"]}),
 ("In 2006, a scientist rebuilt the heads of meat-eating dinosaurs and traced where each eye could look.", 33, {}),
 ("T. rex's eyes faced forward, and their views overlapped across about fifty-five degrees. That's wider than in a modern hawk.", 34,
  {"label": ["55 DEGREES OF OVERLAP", "wider than a hawk's"]}),
 ("Overlap means each eye sees the same object from a slightly different place. The brain uses that difference to work out distance. It's the same geometry surveyors use to measure a far-off mountain. It's called triangulation.", 35,
  {"label": ["TRIANGULATION", "two views give distance"], "source": "Stevens 2006, Journal of Vertebrate Paleontology"}),
 ("Based on living birds and reptiles, its sharpest vision may have picked out objects several kilometres away. It's only an estimate. But it means a slow hunter could still see you coming.", 36, {}),
 ("Its brain also had huge smell lobes, among the biggest of any meat-eating dinosaur.", 37, {}),
 ("And its inner ear was tuned to low, deep sounds. Low sounds have long wavelengths, and they travel further across open ground before they fade.", 38, {}),

 ("Chapter six. Force and pressure.", 39, {"chapter": ["CHAPTER 6", "FORCE AND PRESSURE"]}),
 ("To estimate its bite, scientists rebuilt the jaw muscles using its closest living relatives, crocodiles and birds.", 40, {}),
 ("Their estimate: up to about thirty-five thousand newtons at the back teeth. That's like the weight of three and a half tonnes pressing down, more than twice the strongest bite ever measured in a living animal, the saltwater crocodile.", 41, {}),
 ("But force is only half the story. Pressure is force divided by area. Squeeze that force onto the small tip of a tooth, and the pressure becomes enormous, enough to crack bone.", 42,
  {"source": S_P + "; Gignac & Erickson 2017, Scientific Reports"}),
 ("Its biggest teeth, root and all, were about thirty centimetres long. And they were thick, so they wouldn't snap under that load.", 43, {}),
 ("Fossil bones of its prey, like a Triceratops hip, carry deep T. rex bite marks, some punched right into the bone.", 44, {}),
 ("And a giant fossil dropping, most likely from a T. rex, is up to half crushed bone.", 45, {}),
 ("A slow walker that can judge distance and bite through bone doesn't need to be fast. But then, what were those tiny arms for?", 46, {}),

 ("Chapter seven. Short levers.", 47, {"chapter": ["CHAPTER 7", "SHORT LEVERS"]}),
 ("In 2001, two scientists measured the arm bones and the scars where the muscles attached.", 48, {}),
 ("Each arm was about a metre long, ending in just two clawed fingers. Short, but built from thick bone.", 49, {}),
 ("Their calculation: the biceps alone could curl about two hundred kilograms. Small arms, but not weak ones.", 50, {}),
 ("So why so short? One idea, from 2022: when several adults fed on the same carcass, long arms would have been in the way of all those jaws. It's still debated. Nobody knows for sure.", 51, {}),

 ("Chapter eight. Energy from the sky.", 52, {"chapter": ["CHAPTER 8", "ENERGY FROM THE SKY"]}),
 ("Sixty-six million years ago, T. rex was still at the top of its world.", 53, {}),
 ("Then a rock about ten kilometres across came out of the sky. And the cube rule works here too. A rock that big holds an enormous mass.", 54, {}),
 ("Moving energy is half the mass, times the speed squared. At the kind of speed asteroids hit the Earth, around twenty kilometres a second, a rough estimate gives billions of times the energy of the Hiroshima bomb.", 55,
  {"overlay": "label", "label": ["1/2 m v SQUARED", "rough estimate: billions of Hiroshimas"], "source": S_KE}),
 ("It blasted a crater about one hundred and eighty kilometres wide, in what is now Mexico. Within hours, shock waves, wildfires and giant waves spread out from the impact.", 56, {}),
 ("Dust and soot spread around the planet. Sunlight dimmed, plants struggled, and food chains collapsed.", 57, {}),
 ("About three quarters of all species died out. Every T. rex was gone. But one group of dinosaurs survived: the birds.", 58, {}),
 ("So that's the physics of T. rex. The cube rule made it heavy and slow. Torque explains its tail. Triangulation helped it judge distance. Pressure made its bite crack bone. And energy, half m v squared, ended its world.", 59, {}),
 ("The same rule explains why an ant can fall off a table and walk away, while an elephant can't even jump. So if you were scaled up to the size of a T. rex, what do you think would break first?", 60, {}),
]

base = json.load(open("research/hero/trex_long/spec.json", encoding="utf-8"))
spec = {k: v for k, v in base.items() if k != "shots"}
shots = []
for nar, src, ov in SC:
    sh = copy.deepcopy(base["shots"][src])
    sh.update(ov)
    sh["src"] = src
    shots.append(sh)
os.makedirs("research/hero/wiw_trex", exist_ok=True)
json.dump(dict(spec, shots=shots), open("research/hero/wiw_trex/spec.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

tl = json.load(open("research/hero/trex_long/script.json", encoding="utf-8"))
facts = tl["facts"] + [
    "Physics added 27 Nov 2026: square-cube law (Galileo 1638; Haldane 1926): 13x length -> ~2,200x weight, ~170x bone area; "
    "growth 2 kg/day x 4 yr = 2,920 kg (Erickson 2004); bite 34,522 N = weight of ~3.5 t (Gignac & Erickson 2017); "
    "impact energy a labelled rough estimate (10 km, ~2.6 t/m3, ~20 km/s -> ~2.7e23 J, ~4e9 x Hiroshima 6.3e13 J); "
    "low-frequency sound attenuates less in air; centre of mass near the hips (Hutchinson et al. 2011)."]
script = {
    "title_options": ["The Physics Of T. rex: Why Giants Can't Sprint"],
    "facts": facts,
    "sources": tl["sources"] + "; Galileo 1638, Two New Sciences; Haldane 1926, On Being the Right Size",
    "description": "Why couldn't an eight-tonne T. rex run? Not because of weak muscles, but because of geometry. "
                   "We take the movie monster apart with physics: the square-cube law, torque, triangulation, pressure, levers "
                   "and the energy of the asteroid that ended its world. In 3D, with every claim from published science.",
    "share": {"myth": "A bigger, stronger animal is always a faster one.",
              "truth": "Weight grows with the cube of size but bone strength only with the square, so at about eight tonnes a T. rex sprint would likely have broken its legs (Galileo 1638; Sellers et al. 2017, PeerJ).",
              "line": "Make an animal twice as big and it gets eight times heavier, but its bones get only four times stronger."},
    "tags": ["physics", "square-cube law", "T. rex", "dinosaurs", "why it works", "science explained", "3D animation"],
    "scenes": [{"narration": r[0]} for r in SC],
}
json.dump(script, open("research/hero/wiw_trex/script.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
w = sum(len(r[0].split()) for r in SC)
print("scenes", len(SC), "words", w, "est minutes at 160 wpm", round(w / 160, 1))
