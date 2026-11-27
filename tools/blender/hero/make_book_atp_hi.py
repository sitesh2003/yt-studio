"""Hindi ATP book (26 Nov 2026): the English book's 45 shots, Hindi narration, labels and chapter cards.

    python tools/blender/hero/make_book_atp_hi.py     # writes research/hero/book_atp_hi/{script,spec}.json
    then: hero_voice (STUDIO_CHANNEL=hi) -> timings.py book_atp_hi -> render only the shots longer than English
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
H = ROOT / "research" / "hero"
en_script = json.loads((H / "book_atp" / "script.json").read_text(encoding="utf-8"))
en_spec = json.loads((H / "book_atp" / "spec.json").read_text(encoding="utf-8"))

N = [
    "इसी पल, आपके शरीर की लगभग हर कोशिका के अंदर, नन्हे turbine घूम रहे हैं।",
    "हर एक turbine हर सेकंड लगभग सौ बार घूमता है, और हर चक्कर वह ईंधन बनाता है जिससे आप ज़िंदा हैं।",
    "यह उसी turbine की कहानी है। वह कहाँ है, उसे कौन घुमाता है, और वह रुक जाए तो क्या होता है।",
    "अध्याय एक। आपकी मांसपेशियों को ताकत असल में कहाँ से मिलती है?",
    "हर बार जब कोई मांसपेशी खिंचती है, उसके तंतु ATP नाम का अणु खर्च करते हैं। यह कोशिकाओं का ऊर्जा-सिक्का है।",
    "अजीब बात यह है कि आपके पूरे शरीर में किसी भी पल सिर्फ़ लगभग सौ ग्राम ATP होता है।",
    "पर आराम करते हुए भी, आप दिन में लगभग चालीस किलो ATP खर्च करते हैं। इसलिए हर अणु बार-बार फिर से बनता है।",
    "आपके अंदर कोई चीज़ लगातार ATP बना रही है। उसे ढूँढने के लिए हमें और छोटा होना होगा।",
    "अध्याय दो। कोशिका अपना ज़्यादातर ATP कहाँ बनाती है?",
    "मांसपेशी की कोशिका के अंदर माइटोकॉन्ड्रिया हैं: नन्हे कैप्सूल, हर एक दो झिल्लियों में लिपटा।",
    "भीतरी झिल्ली किताब के पन्नों की तरह बार-बार मुड़ी हुई है, ताकि उसमें ज़्यादा से ज़्यादा जगह समा सके।",
    "यही मुड़ी हुई झिल्ली कारखाने का फ़र्श है। और यह एक हैरान करने वाली चीज़ से चलती है: प्रोटॉन।",
    "अध्याय तीन। यह chain प्रोटॉन का अंतर कैसे बनाती है?",
    "आपका खाना टूटते-टूटते उस हालत में पहुँचता है जहाँ उसकी ऊर्जा इलेक्ट्रॉन ढोते हैं।",
    "ये इलेक्ट्रॉन भीतरी झिल्ली में प्रोटीन के एक chain से आगे बढ़ाए जाते हैं, जैसे लोग हाथों-हाथ बाल्टी आगे बढ़ाते हैं।",
    "इनमें से तीन पड़ावों पर, इस ऊर्जा से प्रोटॉन झिल्ली के पार बाहर pump किए जाते हैं।",
    "आख़िर में, कॉम्प्लेक्स चार इलेक्ट्रॉन को आपकी साँस की ऑक्सीजन को सौंप देता है, और पानी बनता है।",
    "इसीलिए आपको ऑक्सीजन चाहिए। इलेक्ट्रॉन का आख़िरी पड़ाव वही है।",
    "अध्याय चार। एक झिल्ली ऊर्जा कैसे जमा कर सकती है?",
    "pump झिल्ली की एक तरफ़ प्रोटॉन की भीड़ लगा देते हैं। सोचिए, जैसे बाँध के पीछे पानी जमा होता है।",
    "प्रोटॉन वापस बहना चाहते हैं। और वापस आने का मुख्य रास्ता एक ही तरह का दरवाज़ा है।",
    "वह दरवाज़ा ही turbine है। उसका नाम है ATP synthase।",
    "अध्याय पाँच। प्रोटॉन का बहाव ATP synthase को कैसे घुमाता है?",
    "झिल्ली में धँसा हिस्सा एक छल्ला है। जानवरों में यह आठ एक जैसे टुकड़ों से बना होता है।",
    "एक प्रोटॉन एक टुकड़े पर बैठता है, छल्ला एक कदम घूमता है, और प्रोटॉन दूसरी तरफ़ निकल जाता है।",
    "आठ प्रोटॉन, एक पूरा चक्कर। और यह हर सेकंड लगभग सौ चक्कर लगाता है।",
    "उन्नीस सौ सत्तानवे तक किसी ने इसे घूमते नहीं देखा था। तब जापान के वैज्ञानिकों ने इस पर एक चमकता धागा जोड़ा और इसे घूमते देखा।",
    "यह अब तक देखी गई सबसे छोटी घूमने वाली मोटर थी। इसकी घूमती धुरी एक मीटर के सिर्फ़ लगभग दो अरबवें हिस्से जितनी चौड़ी है।",
    "अध्याय छह। घूमने से ATP आख़िर बनता कैसे है?",
    "छल्ला एक टेढ़ी धुरी को घुमाता है, और धुरी तीन काम करने वाले हिस्सों के सिर के अंदर घूमती है।",
    "धुरी घूमते हुए हर हिस्से को एक के बाद एक तीन आकारों में दबाती है।",
    "खुला, टुकड़ों को पकड़ने के लिए। ढीला, उन्हें थामने के लिए। और कसा हुआ, उन्हें दबाकर ATP बनाने के लिए।",
    "फिर हिस्सा खुलता है और नया ATP छोड़ देता है। तीन हिस्से, इसलिए हर चक्कर में तीन ATP।",
    "इसी विचार को उन्नीस सौ सत्तानवे में रसायन का Nobel Prize मिला।",
    "अध्याय सात। इतना सारा ATP जाता कहाँ है?",
    "मांसपेशियों में, खिंचाव के लिए। उन pump में, जो हर नस को संदेश के लिए तैयार रखते हैं। और नए protein बनाने में।",
    "आपका दिल और दिमाग़, नींद में भी, इसे माँगना कभी बंद नहीं करते।",
    "बिल्कुल चुपचाप बैठे हुए भी आपकी कोशिकाएँ ATP खर्च करती हैं। यही है दिन का चालीस किलो।",
    "अध्याय आठ। जब cyanide इस chain को रोक दे, तब क्या होता है?",
    "cyanide turbine पर हमला नहीं करता। वह chain का आख़िरी पड़ाव, कॉम्प्लेक्स चार, जाम कर देता है।",
    "इलेक्ट्रॉन को जाने की जगह नहीं मिलती, तो pump रुक जाते हैं। प्रोटॉन का बाँध खाली होता है, और turbine धीमे पड़ जाते हैं।",
    "नया ATP न बनने पर, सबसे ज़्यादा ऊर्जा माँगने वाले अंग, जैसे दिल और दिमाग़, सबसे ज़्यादा प्रभावित होते हैं।",
    "इतना कुछ इन नन्ही मशीनों पर टिका है।",
    "इसी पल, आपकी कोशिकाओं में नन्हे turbine हर सेकंड लगभग सौ बार घूम रहे हैं, और हर चक्कर तीन ATP बनाता है।",
    "तो जब आप दौड़ना शुरू करते हैं, तब इन turbines का क्या होता होगा?",
]
assert len(N) == len(en_script["scenes"]) == len(en_spec["shots"]), (len(N), len(en_script["scenes"]))

CH = {
    "What Powers Your Muscles?": "मांसपेशियों को ताकत कहाँ से?",
    "Where Is ATP Made?": "ATP कहाँ बनता है?",
    "Building The Proton Gradient": "प्रोटॉन का अंतर कैसे बनता है",
    "A Membrane That Stores Energy": "ऊर्जा जमा करने वाली झिल्ली",
    "What Spins The Turbine?": "turbine को कौन घुमाता है?",
    "How Spinning Makes ATP": "घूमने से ATP कैसे बनता है",
    "Where Does The ATP Go?": "ATP जाता कहाँ है?",
    "When Cyanide Blocks The Chain": "जब cyanide chain रोक दे",
}
NUM = {"1": "एक", "2": "दो", "3": "तीन", "4": "चार", "5": "पाँच", "6": "छह", "7": "सात", "8": "आठ"}

HI = {
    "~100 TURNS A SECOND": "हर सेकंड ~100 चक्कर", "shown here slowed down": "यहाँ धीमा दिखाया गया",
    "ATP": "ATP", "the energy coin cells spend": "कोशिकाओं का ऊर्जा-सिक्का",
    "ABOUT 100 g": "लगभग 100 g", "in your whole body at once": "पूरे शरीर में एक समय पर",
    "ABOUT 40 kg A DAY": "रोज़ लगभग 40 kg", "used even at rest": "आराम में भी खर्च",
    "MITOCHONDRION": "माइटोकॉन्ड्रिया", "wrapped in two membranes": "दो झिल्लियों में लिपटा",
    "CRISTAE": "CRISTAE", "the folded inner membrane": "मुड़ी हुई भीतरी झिल्ली",
    "PROTONS": "प्रोटॉन", "the hidden power source": "छिपा हुआ ताकत का स्रोत",
    "ELECTRONS": "इलेक्ट्रॉन", "carry the energy from food": "खाने की ऊर्जा ढोते हैं",
    "A BUCKET BRIGADE": "हाथों-हाथ बाल्टी", "electrons passed along": "इलेक्ट्रॉन आगे बढ़ते हैं",
    "THREE PUMPS": "तीन pump", "Complexes I, III and IV": "कॉम्प्लेक्स I, III और IV",
    "COMPLEX IV": "कॉम्प्लेक्स IV", "electrons + oxygen make water": "इलेक्ट्रॉन + ऑक्सीजन = पानी",
    "WHY YOU BREATHE": "हम साँस क्यों लेते हैं", "oxygen is the last stop": "ऑक्सीजन आख़िरी पड़ाव",
    "A PROTON DAM": "प्रोटॉन का बाँध", "crowded on one side": "एक तरफ़ भीड़",
    "ONE MAIN DOOR": "एक मुख्य दरवाज़ा", "back across the membrane": "झिल्ली के पार वापस",
    "ATP SYNTHASE": "ATP SYNTHASE", "the turbine": "यही turbine",
    "8 PIECES": "8 टुकड़े", "the ring, in animals": "जानवरों में यह छल्ला",
    "ONE PROTON": "एक प्रोटॉन", "one step of the ring": "छल्ले का एक कदम",
    "8 PROTONS = 1 TURN": "8 प्रोटॉन = 1 चक्कर", "about 100 turns a second": "हर सेकंड लगभग 100 चक्कर",
    "1997": "1997", "the spin, seen directly": "घूमना, सीधे देखा गया",
    "ABOUT 2 nm WIDE": "लगभग 2 nm चौड़ी", "the smallest rotary motor seen": "सबसे छोटी घूमती मोटर",
    "THE CROOKED SHAFT": "टेढ़ी धुरी", "turns inside the head": "सिर के अंदर घूमती है",
    "THREE WORKING PARTS": "तीन काम करने वाले हिस्से", "each changes shape": "हर एक आकार बदलता है",
    "OPEN - LOOSE - TIGHT": "खुला - ढीला - कसा", "the binding change": "आकार का बदलना",
    "3 ATP PER TURN": "हर चक्कर में 3 ATP", "one from each part": "हर हिस्से से एक",
    "NOBEL PRIZE 1997": "NOBEL PRIZE 1997", "Paul Boyer and John Walker": "Paul Boyer और John Walker",
    "MUSCLES, NERVES, PROTEINS": "मांसपेशी, नस, protein", "all paid in ATP": "सबका भुगतान ATP से",
    "HEART AND BRAIN": "दिल और दिमाग़", "never stop asking": "कभी माँगना बंद नहीं करते",
    "EVEN SITTING STILL": "चुपचाप बैठे हुए भी", "about 40 kg a day": "रोज़ लगभग 40 kg",
    "CYANIDE": "CYANIDE", "jams Complex IV, not the turbine": "कॉम्प्लेक्स IV जाम, turbine नहीं",
    "THE DAM DRAINS": "बाँध खाली होता है", "the turbines slow down": "turbine धीमे पड़ते हैं",
    "NO NEW ATP": "नया ATP नहीं", "heart and brain hit hardest": "दिल और दिमाग़ पर सबसे ज़्यादा असर",
    "3 ATP every turn": "हर चक्कर 3 ATP",
}

spec = copy.deepcopy(en_spec)
labels = set()
for sh in spec["shots"]:
    sh["seconds"] = 0
    sh.pop("render_seconds", None)
    sh.pop("event_seconds", None)
    labels |= set(sh.get("label", []))
    if sh.get("chapter"):
        small, title = sh["chapter"]
        sh["chapter"] = ["अध्याय " + NUM[small.split()[-1]], CH[title]]
missing = labels - set(HI)
assert not missing, missing
spec["hi_labels"] = {k: HI[k] for k in sorted(labels)}

script = {
    "title_options": ["आपके अंदर का नन्हा turbine: जो आपके शरीर को ऊर्जा देता है"],
    "share": {
        "myth": "खाने की ऊर्जा किसी तरह शरीर की ऊर्जा बन जाती है; इसमें कुछ भी मशीन जैसा नहीं होता।",
        "truth": "आपका ज़्यादातर ATP, ATP synthase बनाता है: माइटोकॉन्ड्रिया की एक घूमने वाली मोटर, जिसे प्रोटॉन हर सेकंड लगभग सौ बार घुमाते हैं, और हर चक्कर में तीन ATP बनते हैं (Noji et al. 1997; Watt et al. 2010)।",
        "line": "इसी पल, आपकी कोशिकाओं में नन्हे turbine हर सेकंड लगभग सौ बार घूम रहे हैं, और हर चक्कर तीन ATP बनाता है।",
    },
    "facts": en_script["facts"],
    "description": ("आपकी कोशिकाओं के अंदर, एक मीटर के लगभग दस अरबवें हिस्से जितनी मोटर हर सेकंड लगभग सौ बार घूमती है, और हर "
                    "चक्कर में ATP के तीन अणु बनाती है, वही ऊर्जा जिस पर आपका शरीर चलता है। यह उसकी कहानी है, "
                    "आपकी मांसपेशियों से turbine तक और वापस, आठ अध्यायों में। #hindi #science #biology"),
    "sources": en_script["sources"],
    "tags": ["ATP hindi", "माइटोकॉन्ड्रिया", "ATP synthase", "biology hindi", "science hindi", "3D animation"],
    "scenes": [{"narration": t} for t in N],
}
d = H / "book_atp_hi"
d.mkdir(exist_ok=True)
(d / "script.json").write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")
(d / "spec.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
print("book_atp_hi:", len(N), "scenes,", len(labels), "labels")
