"""Why It Works long film (23 Nov 2026): "Why Just 10 km/h Can Turn a Stop Into a Crash".
Council rounds 8: a five-second crash investigation (impact first, freeze, rewind, replay); every number computed
here or taken from a named source; idealised-simulation labels where the physics is simplified.

Worked physics (equal braking a = 7 m/s^2 on a dry road, from the same instant):
  50 km/h = 13.89 m/s stops in v^2/2a = 13.8 m.  60 km/h = 16.67 m/s at that point: sqrt(60^2 - 50^2) = 33.2 km/h.
  Energy ratio (60/50)^2 = 1.44 -> 44% more.  Double speed -> 4x energy and 4x braking distance.
  Reaction 1.5 s: 50 km/h -> 20.8 m, 60 km/h -> 25.0 m (FHWA: typical perception-reaction 0.75-1.5 s).
  With 1.5 s reaction at both: 50 car stops at 34.6 m; 60 car has braked 9.6 m there -> 43 km/h.
  Wet: UK Highway Code rule 227 - allow at least double. Half the grip (3.5 m/s^2) -> 2x braking distance.
  Impulse: 1,500 kg at 33 km/h (9.2 m/s): change in momentum 13,800 kg m/s; stopped in 0.1 s -> ~138 kN average,
  in 0.02 s -> ~690 kN (illustrative stopping times).
"""
import copy, json, os, sys
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(R); sys.path.insert(0, R)

L50_60 = {"speeds": [50, 60], "decels": [7.0, 7.0], "lane_names": ["50 km/h", "60 km/h"]}
DRYWET = {"speeds": [50, 50], "decels": [7.0, 3.5], "wet_lane": 1, "lane_names": ["DRY", "WET"]}
S_PHYS = "Kinematics v² = u² - 2as (idealised: same car, same braking from the same instant)"
S_KE = "OpenStax University Physics, Ch. 7 (kinetic energy)"
S_FHWA = "US Federal Highway Administration: perception-reaction time 0.75-1.5 s"
S_HC = "UK Highway Code, rule 227"
S_NEW = "Newton's second law: average force = change in momentum / time"
S_BAR = "Barenyi patent DBP 854 157 (filed 1951, granted 1952); Mercedes-Benz W 111 (1959)"
S_NHTSA = "NHTSA: seat belts cut the risk of fatal injury to front-seat car occupants by 45%"

SC = [
 # cold open: the impact first
 ("Two identical cars. Same brakes, same road, same driver reaction. One is doing fifty kilometres an hour. The other, sixty.",
  dict({"kind": "brake_compare", "overlay": "brake_speeds", "brake_at": 0.55, "seconds": 7}, **L50_60)),
 ("Both brake at exactly the same moment. The slower car stops. The faster one is still doing more than thirty kilometres an hour, at the very same spot.",
  dict({"kind": "brake_compare", "overlay": "brake_result", "result_text": "STILL AT 33 km/h", "brake_at": 0.1, "seconds": 9,
        "source": S_PHYS}, **L50_60)),
 ("If there's a wall there, one car is fine. The other crashes. Ten kilometres an hour, about six miles an hour, made all the difference.",
  {"kind": "crash_compare", "overlay": "none", "hit_at": 0.45, "seconds": 8}),
 ("So let's investigate. We'll freeze this crash, rewind the last five seconds, and find out exactly where that extra speed did its damage.",
  dict({"kind": "brake_compare", "overlay": "none", "brake_at": 0.9, "seconds": 8, "cam_h": 34}, **L50_60)),

 # 1 the energy you carry
 ("Rewind one. The energy you carry.", dict({"kind": "brake_compare", "overlay": "chapter", "chapter": ["REWIND 1", "THE ENERGY YOU CARRY"],
   "brake_at": 0.95, "seconds": 3.5}, **L50_60)),
 ("A moving car carries kinetic energy: half its mass times its speed squared. That squared is the whole story.",
  dict({"kind": "brake_compare", "overlay": "energy", "brake_at": 0.95, "seconds": 8, "source": S_KE}, **L50_60)),
 ("Go from fifty to sixty, just twenty percent faster, and the energy goes up by forty-four percent.",
  dict({"kind": "brake_compare", "overlay": "bars", "title": "MOVING ENERGY", "bars": [["50 km/h", 100, "cyan"], ["60 km/h", 144, "red"]],
        "unit": "%", "brake_at": 0.95, "seconds": 8, "source": S_KE}, **L50_60)),
 ("Double your speed, and you carry four times the energy. And every bit of it has to go somewhere before the car can stop.",
  {"kind": "brake_compare", "overlay": "four", "brake_at": 0.95, "seconds": 9, "source": S_KE}),

 # 2 thinking time
 ("Here's a way to feel it. Hitting a wall at fifty takes the same energy as the car falling about ten metres, roughly from a third-floor window. At sixty, it's about fourteen metres, nearly the fifth floor.",
  dict({"kind": "brake_compare", "overlay": "bars", "title": "SAME ENERGY AS FALLING", "bars": [["50 km/h", 9.8, "cyan"], ["60 km/h", 14.2, "red"]],
        "unit": "m", "brake_at": 0.95, "seconds": 11, "source": "Energy: height = v² / 2g"}, **L50_60)),
 ("Rewind two. The thinking gap.", dict({"kind": "brake_compare", "overlay": "chapter", "chapter": ["REWIND 2", "THE THINKING GAP"],
   "brake_at": 0.95, "seconds": 3.5}, **L50_60)),
 ("Before the brakes do anything, a driver has to see the danger, decide, and move a foot. That usually takes somewhere between three quarters of a second and one and a half seconds.",
  dict({"kind": "brake_compare", "overlay": "react", "brake_at": 0.25, "react_s": 1.5, "seconds": 11, "source": S_FHWA}, **L50_60)),
 ("At fifty, a second and a half of thinking covers about twenty-one metres. At sixty, twenty-five. The faster car reaches the brakes later, and further down the road.",
  dict({"kind": "brake_compare", "overlay": "bars", "title": "THINKING DISTANCE (1.5 s)", "bars": [["50 km/h", 20.8, "cyan"], ["60 km/h", 25.0, "red"]],
        "unit": "m", "brake_at": 0.75, "seconds": 11, "source": S_FHWA}, **L50_60)),
 ("That's nearly five car lengths, travelled at full speed, before your foot even touches the pedal. Anything that slows your reaction, like a phone or tiredness, stretches it further.",
  dict({"kind": "brake_compare", "overlay": "react", "brake_at": 0.6, "react_s": 1.5, "seconds": 10, "source": S_FHWA}, **L50_60)),
 ("Add that thinking gap to our test, and where the slower car stops, the faster one is now doing around forty-three kilometres an hour.",
  dict({"kind": "brake_compare", "overlay": "brake_result", "result_text": "NOW 43 km/h", "brake_at": 0.2, "react_s": 1.5, "seconds": 11,
        "source": "Same model with a 1.5 s reaction and 7 m/s² braking (idealised)"}, **L50_60)),

 # 3 braking
 ("Rewind three. Turning speed into heat.", dict({"kind": "brake_compare", "overlay": "chapter", "chapter": ["REWIND 3", "TURNING SPEED INTO HEAT"],
   "brake_at": 0.2, "seconds": 3.5}, **L50_60)),
 ("Brakes don't destroy energy. Friction turns the car's motion into heat, in the brakes and the tyres.",
  dict({"kind": "brake_compare", "overlay": "label", "label": ["FRICTION", "motion becomes heat"], "brake_at": 0.15, "seconds": 8}, **L50_60)),
 ("With the same grip, the braking distance grows with the square of speed. Twice as fast means four times as far.",
  {"kind": "brake_compare", "overlay": "brake_result", "result_text": "4x THE DISTANCE", "brake_at": 0.12, "seconds": 9,
   "source": "Braking distance = v² / 2a"}),
 ("On a dry road with good brakes, a car at fifty needs about fourteen metres to brake to a stop. At sixty, about twenty. Six extra metres, from ten extra kilometres an hour.",
  dict({"kind": "brake_compare", "overlay": "bars", "title": "BRAKING DISTANCE (DRY)", "bars": [["50 km/h", 13.8, "cyan"], ["60 km/h", 19.8, "red"]],
        "unit": "m", "brake_at": 0.15, "seconds": 11, "source": "v² / 2a with a = 7 m/s² (idealised dry road)"}, **L50_60)),
 ("That's why a small bump in speed hurts so much more than it feels like it should.",
  dict({"kind": "brake_compare", "overlay": "none", "brake_at": 0.15, "seconds": 7, "cam_h": 30}, **L50_60)),

 # 4 grip
 ("Rewind four. The road itself.", dict({"kind": "brake_compare", "overlay": "chapter", "chapter": ["REWIND 4", "THE ROAD ITSELF"],
   "brake_at": 0.2, "seconds": 3.5}, **DRYWET)),
 ("All of this assumed a dry road. Water gets between the tyre and the road, and grip drops.",
  dict({"kind": "brake_compare", "overlay": "label", "label": ["LESS GRIP", "water gets between tyre and road"], "brake_at": 0.12, "seconds": 8}, **DRYWET)),
 ("The UK Highway Code tells drivers to allow at least double the stopping distance in the wet. In our model, half the grip means twice the braking distance.",
  dict({"kind": "brake_compare", "overlay": "brake_result", "result_text": "2x THE DISTANCE", "brake_at": 0.12, "seconds": 10, "source": S_HC}, **DRYWET)),
 ("Tyre grooves exist to pump that water out of the way. Worn tyres can't clear as much, and at higher speeds a tyre can ride up on the water and lose contact. That's hydroplaning.",
  dict({"kind": "brake_compare", "overlay": "label", "label": ["WORN TYRES", "can't push the water away"], "brake_at": 0.15, "seconds": 11}, **DRYWET)),

 # 5 impact
 ("That's why tyres have a legal minimum tread depth. In the UK, it's one point six millimetres, about the thickness of a one-penny coin.",
  dict({"kind": "brake_compare", "overlay": "label", "label": ["1.6 mm", "UK legal minimum tread"], "brake_at": 0.15, "seconds": 9,
        "source": "UK government: tyre tread depth rules"}, **DRYWET)),
 ("Rewind five. The impact.", {"kind": "crash_compare", "overlay": "chapter", "chapter": ["REWIND 5", "THE IMPACT"], "hit_at": 0.85, "seconds": 3.5}),
 ("Now the crash itself. Whatever happens, the car has to go from thirty-three kilometres an hour to zero. What matters is how quickly.",
  {"kind": "crash_compare", "overlay": "same_speed", "hit_at": 0.55, "seconds": 9, "frame_lift": 4.0}),
 ("Newton's second law: the average force equals the change in momentum, divided by the time it takes. Stretch the time, and the force falls.",
  {"kind": "crash_compare", "overlay": "newton", "hit_at": 0.25, "seconds": 10, "frame_lift": 4.0, "source": S_NEW}),
 ("A stiff car stops in a blink, and the force spikes. A car that folds takes longer to stop, so the peak force is much lower.",
  {"kind": "crash_compare", "overlay": "force_graph_both", "hit_at": 0.25, "seconds": 9, "frame_lift": 4.0, "source": S_NEW}),
 ("Some rough numbers. Stop a family car from thirty-three kilometres an hour in a tenth of a second, and the average force is about one hundred and forty thousand newtons. Stop it five times faster, and the force is five times bigger.",
  {"kind": "crash_compare", "overlay": "bars", "title": "AVERAGE FORCE (illustrative)", "bars": [["STOPS IN 0.1 s", 138, "green"], ["STOPS IN 0.02 s", 690, "red"]],
   "unit": "kN", "hit_at": 0.3, "seconds": 12, "frame_lift": 4.0, "source": S_NEW}),
 ("That's the crumple zone, patented by engineer Béla Barényi more than seventy years ago: soft ends that fold, around a strong cabin that doesn't.",
  {"kind": "crash_compare", "overlay": "history", "hit_at": 0.3, "seconds": 10, "frame_lift": 4.0, "source": S_BAR}),

 # 6 the second collision
 ("Rewind six. The second collision.", {"kind": "cabin", "belt": True, "ghost": True, "hit_s": 9.0, "overlay": "chapter",
   "chapter": ["REWIND 6", "THE SECOND COLLISION"], "seconds": 3.5}),
 ("When the car stops, you don't. Your body keeps moving at the speed the car was doing. That's Newton's first law.",
  {"kind": "cabin", "belt": False, "ghost": True, "hit_s": 1.4, "slowmo": 12, "overlay": "label", "label": ["NEWTON'S FIRST LAW", "you keep moving"], "seconds": 9}),
 ("Without a belt, you fly forward at the car's old speed until something stops you: the steering wheel, the dashboard, the windscreen. Engineers call it the second collision.",
  {"kind": "cabin", "belt": False, "ghost": True, "hit_s": 1.2, "slowmo": 12, "overlay": "label", "label": ["SECOND COLLISION", "you hit the inside of the car"], "seconds": 10}),
 ("A seat belt holds you to the car, so you slow down with the cabin, spreading the force across your hips and chest, the strongest parts of your body.",
  {"kind": "cabin", "belt": True, "ghost": True, "hit_s": 1.4, "slowmo": 12, "overlay": "label", "label": ["SEAT BELT", "slow down with the car"], "seconds": 10}),
 ("An airbag adds a cushion that gives you a little more time, and a little more area, to stop. It works with the belt, not instead of it.",
  {"kind": "cabin", "belt": True, "ghost": False, "airbag": True, "hit_s": 1.2, "slowmo": 12, "overlay": "label",
   "label": ["AIRBAG", "works WITH the belt"], "seconds": 10}),
 ("In the United States, safety officials estimate that seat belts cut the risk of death for people in the front seats of cars by forty-five percent.",
  {"kind": "cabin", "belt": True, "ghost": False, "airbag": True, "hit_s": 2.0, "slowmo": 12, "overlay": "bars", "title": "RISK OF DEATH, FRONT SEAT",
   "bars": [["NO BELT", 100, "red"], ["BELT", 55, "green"]], "unit": "%", "seconds": 10, "source": S_NHTSA}),

 # 7 replay
 ("Replay. Everything at once.", dict({"kind": "brake_compare", "overlay": "chapter", "chapter": ["REPLAY", "EVERYTHING AT ONCE"],
   "brake_at": 0.6, "seconds": 3.5}, **L50_60)),
 ("Same two cars. The faster one carries almost half as much energy again, reacts further down the road, and needs more room to brake.",
  dict({"kind": "brake_compare", "overlay": "brake_speeds", "brake_at": 0.45, "seconds": 10}, **L50_60)),
 ("Go back through the evidence: almost half as much energy again, about four more metres of thinking, about six more metres of braking. Every piece pushes the same way.",
  dict({"kind": "brake_compare", "overlay": "react", "brake_at": 0.4, "react_s": 1.5, "seconds": 10}, **L50_60)),
 ("Where the slower car stops, the faster one arrives with real speed left over. Add rain, and the gap gets wider still.",
  dict({"kind": "brake_compare", "overlay": "brake_result", "result_text": "STILL AT 33 km/h", "brake_at": 0.1, "seconds": 9, "source": S_PHYS}, **L50_60)),
 ("That's why ten kilometres an hour is never just ten. Which part of the physics surprised you most?",
  {"kind": "crash_compare", "overlay": "none", "hit_at": 0.4, "seconds": 9}),
]

base = json.load(open("research/hero/braking/spec.json"))
spec = {k: v for k, v in base.items() if k != "shots"}
spec.update(aspect="landscape", long=True, caption_scale=1.0)
os.makedirs("research/hero/wiw_long", exist_ok=True)
json.dump(dict(spec, shots=[copy.deepcopy(r[1]) for r in SC]), open("research/hero/wiw_long/spec.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
srcs = "; ".join([S_KE, S_FHWA, S_HC, S_NEW, S_BAR, S_NHTSA, "UK Highway Code stopping distances", "IIHS, NHTSA (airbags supplement belts)"])
script = {"title_options": ["Why Just 10 km/h Can Turn a Stop Into a Crash"],
          "facts": [__doc__], "sources": srcs,
          "description": "Two identical cars brake at the same moment: one at 50 km/h, one at 60. One stops; the other is still doing 33 km/h at the same spot. "
                         "We freeze the crash and rewind five seconds to find out why, in 3D: energy, reaction time, braking, grip, crumple zones, belts and airbags.",
          "share": {"myth": "Going ten km/h faster is only a little more dangerous.", "truth": "Moving energy grows with the square of speed, so 50 to 60 km/h carries 44% more energy and needs far more road to stop.", "line": "Fifty to sixty is just twenty percent faster, but the energy goes up by forty-four percent."},
          "tags": ["physics", "braking distance", "kinetic energy", "crumple zone", "seat belt", "car safety", "3D animation", "STEM"],
          "scenes": [{"narration": r[0]} for r in SC]}
json.dump(script, open("research/hero/wiw_long/script.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("scenes", len(SC), "words", sum(len(r[0].split()) for r in SC))
