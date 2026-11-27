"""The ATP book grows to ~10 minutes (owner, 27 Nov 2026: "proper long ... 10 mins type").

Chapters 1-8 (scenes 0-41) keep their recorded voices and rendered frames; the old 3-scene ending is replaced by
chapters 9-13 and a new ending. Facts checked 27 Nov 2026 against the sources named on each shot (fact-check notes:
research/hero/book_atp_ext/facts_checked.md).

    python tools/blender/hero/make_book_atp_long.py ext      # writes book_atp_ext(+_hi)/script.json + shots.json
    (voice both: hero_voice book_atp_ext main, book_atp_ext_hi hi)
    python tools/blender/hero/make_book_atp_long.py merge    # builds book_atp_long(+_hi): voice, words, scenes, script, spec
    python tools/blender/hero/timings.py book_atp_long ; timings.py book_atp_long_hi
    python tools/blender/hero/make_book_atp_long.py seconds  # render/event seconds for the new shots (one render, two voices)
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
H = ROOT / "research" / "hero"
KEEP = 42                                            # scenes 0..41 of the old book are kept as they are

BAKER = "Baker, McCormick & Robergs 2010, J Nutr Metab 905612"
BRAND = "Brand & Nicholls 2011, Biochem J 435:297"
KAM = "Kaminsky, Arena & Myers 2015, Mayo Clin Proc 90:1515"
SULKIN = "Sulkin et al. 2014, J Struct Biol 188:55"
NOJI = "Noji et al. 1997, Nature 386:299"
NAKA = "Nakamoto et al. 2008, Arch Biochem Biophys 476:43"
CAMP = "Campanella et al. 2008, Cell Metab 8:13"
LIDELL = "Lidell et al. 2013, Nat Med 19:631"
FED = "Fedorenko, Lishko & Kirichok 2012, Cell 151:400"
CYPESS = "Cypess et al. 2009, NEJM 360:1509"
PARFREY = "Parfrey et al. 2011, PNAS 108:13624"
ROGER = "Roger, Munoz-Gomez & Kamikawa 2017, Curr Biol 27:R1177"
ANDERSON = "Anderson et al. 1981, Nature 290:457"
ROBIN = "Robin & Wong 1988, J Cell Physiol 136:507"
REYNIER = "Reynier et al. 2001, Mol Hum Reprod 7:425"
SUTOVSKY = "Sutovsky et al. 1999, Nature 402:371"
LUO = "Luo et al. 2018, PNAS 115:13039"
WATT = "Watt et al. 2010, PNAS 107:16823"


def S(kind, en, hi, **k):
    return dict(kind=kind, overlay="label" if "label" in k else "none", **k), en, hi


EXT = [
    # ---- chapter 9: running (answers the old closing question)
    S("atp_muscle", "Chapter nine. So what happens to all those turbines when you start to run?",
      "अध्याय नौ। तो जब आप दौड़ना शुरू करते हैं, तब इन सारे turbines का क्या होता है?",
      pace=2.2, chapter=["CHAPTER 9", "What Happens When You Run?"]),
    S("atp_muscle", "In the first few seconds of a flat-out sprint, your muscles run mostly on the ATP they already hold.",
      "पूरी ताकत की दौड़ के पहले कुछ सेकंड, आपकी मांसपेशियाँ ज़्यादातर उसी ATP से चलती हैं जो उनके पास पहले से है।",
      pace=2.2, label=["THE FIRST SECONDS", "the ATP already there"], source=BAKER),
    S("atp_molecule", "A backup called phosphocreatine rebuilds that ATP almost instantly, but its store is small.",
      "फ़ॉस्फ़ोक्रिएटिन नाम का एक बैकअप उस ATP को लगभग तुरंत फिर से बना देता है, पर उसका भंडार छोटा है।",
      label=["PHOSPHOCREATINE", "an instant backup"]),
    S("atp_molecule", "Within about ten seconds of all-out effort, most of that phosphocreatine is used up.",
      "पूरी ताकत की कोशिश के लगभग दस सेकंड में, ज़्यादातर फ़ॉस्फ़ोक्रिएटिन ख़त्म हो जाता है।",
      split=True, label=["ABOUT 10 SECONDS", "then the backup runs low"], source=BAKER),
    S("atp_molecule", "Within seconds, glycolysis joins in. It splits sugar fast, without needing oxygen.",
      "कुछ ही सेकंड में ग्लाइकोलिसिस भी जुड़ जाता है। यह बिना ऑक्सीजन के, तेज़ी से शक्कर को तोड़ता है।",
      split=True, label=["GLYCOLYSIS", "sugar split, no oxygen"]),
    S("atp_mito", "In a ten second sprint, only a few percent of the energy comes from your mitochondria.",
      "दस सेकंड की दौड़ में, ऊर्जा का सिर्फ़ कुछ प्रतिशत आपके माइटोकॉन्ड्रिया से आता है।",
      label=["10 SECOND SPRINT", "~3% from mitochondria"], source=BAKER),
    S("atp_mito", "Stretch it to thirty seconds, and they already supply more than a quarter.",
      "इसे तीस सेकंड तक खींचिए, और वे पहले ही एक चौथाई से ज़्यादा देने लगते हैं।",
      dive=True, label=["30 SECOND SPRINT", "over a quarter"]),
    S("atp_mito", "By about a minute and a quarter of hard effort, the oxygen-using supply roughly matches all the rest.",
      "लगभग सवा मिनट की कड़ी मेहनत तक, ऑक्सीजन वाली सप्लाई बाकी सब के लगभग बराबर हो जाती है।",
      label=["ABOUT 75 SECONDS", "half from mitochondria"], source=BAKER),
    S("atp_mito", "The longer you keep going, the more of the work passes to them. All three systems overlap.",
      "आप जितनी देर चलते रहें, उतना ज़्यादा काम उनके पास जाता है। तीनों तरीके साथ-साथ चलते हैं।",
      label=["THE LONG RUN", "mitochondria take over"]),
    S("atp_molecule", "And here's the clever part. Every ATP you spend leaves behind ADP and phosphate.",
      "और यहाँ एक कमाल की बात है। आपका खर्च किया हर ATP पीछे ADP और फ़ॉस्फ़ेट छोड़ता है।",
      split=True, label=["ADP + PHOSPHATE", "what spent ATP leaves"]),
    S("atp_synthase", "Those are exactly what the turbine needs. So as they build up, the turbines and the whole chain run faster.",
      "turbine को ठीक इन्हीं की ज़रूरत है। तो जैसे-जैसे ये जमा होते हैं, turbine और पूरी chain तेज़ चलने लगते हैं।",
      mode="spin", slow=0.8, label=["MORE ADP = FASTER", "respiratory control"], source=BRAND),
    S("atp_synthase", "Nobody has to flip a switch. Spending energy is itself the signal to make more.",
      "किसी को कोई बटन नहीं दबाना पड़ता। ऊर्जा खर्च करना ही और बनाने का संकेत है।",
      mode="orbit", slow=0.6),
    S("atp_chain", "That's why you breathe hard. Oxygen is the last stop for the electrons, and the chain needs far more of it.",
      "इसीलिए आप तेज़ साँस लेते हैं। ऑक्सीजन इलेक्ट्रॉन का आख़िरी पड़ाव है, और chain को इसकी कहीं ज़्यादा ज़रूरत होती है।",
      focus="iv", label=["BREATHING HARD", "more oxygen for the chain"]),
    S("atp_muscle", "At full effort, a healthy young adult can use roughly ten times as much oxygen as at rest, or more.",
      "पूरी ताकत लगाने पर, एक स्वस्थ युवा आराम की तुलना में लगभग दस गुना या उससे भी ज़्यादा ऑक्सीजन इस्तेमाल कर सकता है।",
      pace=2.2, label=["ABOUT 10x THE OXYGEN", "at full effort"], source=KAM),
    S("atp_cell", "And your heart never gets a rest. In heart muscle, mitochondria fill more than a quarter of each cell.",
      "और आपके दिल को कभी आराम नहीं मिलता। दिल की मांसपेशी में, माइटोकॉन्ड्रिया हर कोशिका का एक चौथाई से ज़्यादा हिस्सा भरते हैं।",
      count=330, label=["HEART MUSCLE", "over a quarter is mitochondria"], source=SULKIN),
    # ---- chapter 10: backwards
    S("atp_synthase", "Chapter ten. Can the turbine run backwards?",
      "अध्याय दस। क्या यह turbine उल्टा चल सकता है?",
      mode="reverse", slow=0.4, chapter=["CHAPTER 10", "Can The Turbine Run Backwards?"]),
    S("atp_synthase", "It can. Feed ATP synthase a supply of ATP, and it spins the other way.",
      "चल सकता है। ATP synthase को ATP खिलाइए, और यह दूसरी दिशा में घूमने लगता है।",
      mode="reverse", slow=0.4, label=["RUNNING BACKWARDS", "fed ATP, it splits it"]),
    S("atp_synthase", "Now splitting ATP turns the rotor, and the whole machine pumps protons back across the membrane.",
      "अब ATP का टूटना रोटर को घुमाता है, और पूरी मशीन प्रोटॉन को झिल्ली के पार वापस pump करती है।",
      mode="reverse", slow=0.4, label=["PUMP MODE", "ATP in, protons out"]),
    S("atp_noji", "Remember the glowing filament from nineteen ninety-seven? That spin was driven this way.",
      "उन्नीस सौ सत्तानवे का वह चमकता धागा याद है? वह घूमना इसी तरह चलाया गया था।",
      slow=0.5),
    S("atp_noji", "The scientists fed the turbine's head ATP, and as it split the ATP, it turned.",
      "वैज्ञानिकों ने turbine के सिर को ATP खिलाया, और जैसे-जैसे वह ATP तोड़ता गया, वह घूमता गया।",
      slow=0.5, label=["FED ATP", "the head turned"], source=NOJI),
    S("atp_noji", "They used only the head and shaft, from a heat-loving bacterium. It spun, but on its own it couldn't pump.",
      "उन्होंने गर्मी पसंद बैक्टीरिया से सिर्फ़ सिर और धुरी ली थी। वह घूमा, पर अकेले वह pump नहीं कर सकता था।",
      slow=0.5, label=["HEAD AND SHAFT ONLY", "from a heat-loving bacterium"]),
    S("atp_synthase", "Some bacteria do this on purpose. Without oxygen, E. coli spends ATP to run its turbines backwards and keep its membrane charged.",
      "कुछ बैक्टीरिया ऐसा जानबूझकर करते हैं। ऑक्सीजन न होने पर, E. coli अपनी झिल्ली को चार्ज रखने के लिए ATP खर्च करके turbine उल्टे चलाता है।",
      mode="reverse", slow=0.3, label=["E. COLI", "without oxygen"], source=NAKA),
    S("atp_chain", "In your cells, that could be a disaster. If the dam ever drained, the turbines could burn through your ATP.",
      "आपकी कोशिकाओं में यह मुसीबत बन सकता है। अगर बाँध कभी खाली हो जाए, तो turbine आपका ATP जला सकते हैं।",
      cyanide=True, label=["A DRAINED DAM", "turbines could burn ATP"]),
    S("atp_synthase", "So your mitochondria carry a brake, a small protein called IF1.",
      "इसलिए आपके माइटोकॉन्ड्रिया में एक ब्रेक होता है, IF1 नाम का एक छोटा protein।",
      mode="orbit", slow=0.2, label=["IF1", "the brake"]),
    S("atp_synthase", "If the proton gradient collapses, IF1 largely stops the turbines running backwards and draining the cell.",
      "अगर प्रोटॉन का अंतर ख़त्म हो जाए, तो IF1 turbines को उल्टा चलकर कोशिका को खाली करने से काफ़ी हद तक रोक देता है।",
      mode="spin", slow=0.12, label=["ATP SAVED", "when the dam drains"], source=CAMP),
    # ---- chapter 11: brown fat
    S("atp_dam", "Chapter eleven. How does brown fat make heat?",
      "अध्याय ग्यारह। ब्राउन फ़ैट गर्मी कैसे बनाता है?",
      leak=True, chapter=["CHAPTER 11", "How Does Brown Fat Make Heat?"]),
    S("atp_cell", "A newborn baby carries a pad of brown fat, including between its shoulder blades, to keep warm.",
      "नवजात बच्चे के शरीर में गर्म रहने के लिए ब्राउन फ़ैट की एक परत होती है, कंधों के बीच भी।",
      count=300, label=["BROWN FAT", "packed with mitochondria"], source=LIDELL),
    S("atp_dam", "Brown fat cells are packed with mitochondria. And their inner membranes have a gap in the dam.",
      "ब्राउन फ़ैट की कोशिकाएँ माइटोकॉन्ड्रिया से भरी होती हैं। और उनकी भीतरी झिल्ली के बाँध में एक दरार होती है।",
      leak=True, label=["UCP1", "a gap in the dam"]),
    S("atp_dam", "A protein called UCP1 lets protons leak straight back, without passing through the turbine.",
      "UCP1 नाम का एक protein प्रोटॉन को turbine से गुज़रे बिना, सीधे वापस रिसने देता है।",
      leak=True, label=["NO TURBINE", "protons leak back"], source=FED),
    S("atp_dam", "So the energy stored in the dam doesn't make ATP. It comes out as heat.",
      "तो बाँध में जमा ऊर्जा ATP नहीं बनाती। वह गर्मी बनकर निकलती है।",
      leak=True, label=["HEAT", "instead of ATP"]),
    S("atp_dam", "It's a power station that burns its fuel just to keep you warm.",
      "यह एक ऐसा बिजलीघर है जो अपना ईंधन सिर्फ़ आपको गर्म रखने के लिए जलाता है।",
      leak=True),
    S("atp_cell", "Adults keep smaller amounts, mainly around the neck and collarbones, and it switches on in the cold.",
      "बड़ों में यह कम होता है, ज़्यादातर गर्दन और कॉलरबोन के आसपास, और ठंड में यह चालू हो जाता है।",
      count=220, label=["ADULTS TOO", "neck and collarbones"], source=CYPESS),
    # ---- chapter 12: where mitochondria came from
    S("atp_cell", "Chapter twelve. Where did mitochondria come from?",
      "अध्याय बारह। माइटोकॉन्ड्रिया आए कहाँ से?",
      mode="engulf", chapter=["CHAPTER 12", "Where Did Mitochondria Come From?"]),
    S("atp_cell", "Here's the strangest part of the whole story. Mitochondria were once bacteria.",
      "पूरी कहानी का सबसे अजीब हिस्सा यह है। माइटोकॉन्ड्रिया कभी बैक्टीरिया थे।",
      mode="engulf", label=["ONCE BACTERIA", "free-living cells"]),
    S("atp_cell", "More than one and a half billion years ago, a free-living bacterium ended up living inside another cell.",
      "डेढ़ अरब साल से भी पहले, एक आज़ाद बैक्टीरिया किसी दूसरी कोशिका के अंदर रहने लगा।",
      mode="engulf", label=["OVER 1.5 BILLION YEARS AGO", "one cell inside another"], source=PARFREY),
    S("atp_cell", "Instead of being digested, it stayed. The host gave it shelter and food, and it gave the host energy.",
      "वह पचाया नहीं गया, वहीं रह गया। मेज़बान ने उसे घर और खाना दिया, और उसने मेज़बान को ऊर्जा दी।",
      mode="engulf", label=["A PARTNERSHIP", "shelter for energy"]),
    S("atp_cell", "The host was related to a group of microbes called Asgard archaea. Together they became the first complex cell.",
      "वह मेज़बान Asgard archaea नाम के सूक्ष्मजीवों से जुड़ा था। दोनों मिलकर पहली जटिल कोशिका बने।",
      mode="engulf", label=["ASGARD ARCHAEA", "the host's relatives"], source=ROGER),
    S("atp_cell", "The mitochondria in every plant, animal and fungus trace back to that one partnership.",
      "हर पौधे, जानवर और फफूँद के माइटोकॉन्ड्रिया उसी एक साझेदारी से निकले हैं।",
      label=["ONE ANCESTOR", "for all mitochondria"], source=ROGER),
    S("atp_mito", "And they still carry a trace of their past: their own DNA.",
      "और उनमें आज भी अपने अतीत की निशानी है: उनका अपना DNA।",
      label=["THEIR OWN DNA", "left from the bacterium"]),
    S("atp_mito", "Human mitochondrial DNA is a tiny loop of sixteen thousand, five hundred and sixty-nine base pairs, carrying just thirty-seven genes.",
      "इंसान का माइटोकॉन्ड्रियल DNA सोलह हज़ार पाँच सौ उनहत्तर base pairs का एक छोटा सा छल्ला है, जिसमें सिर्फ़ सैंतीस genes हैं।",
      dive=True, label=["16,569 BASE PAIRS", "37 genes"], source=ANDERSON),
    S("atp_synthase", "Two pieces of the turbine itself are written in that little loop.",
      "turbine के खुद के दो टुकड़े उसी छोटे छल्ले में लिखे हैं।",
      mode="protons", slow=0.35, label=["TWO TURBINE PARTS", "written in mitochondrial DNA"], source=ANDERSON),
    S("atp_cell", "A typical cell holds hundreds of mitochondria, and each one keeps its own copies.",
      "एक आम कोशिका में सैकड़ों माइटोकॉन्ड्रिया होते हैं, और हर एक अपनी प्रतियाँ रखता है।",
      label=["HUNDREDS PER CELL", "each with its own DNA"], source=ROBIN),
    # ---- chapter 13: from your mother
    S("atp_cell", "Chapter thirteen. Why do your mitochondria come from your mother?",
      "अध्याय तेरह। आपके माइटोकॉन्ड्रिया आपकी माँ से ही क्यों आते हैं?",
      mode="egg", chapter=["CHAPTER 13", "Why Only From Your Mother?"]),
    S("atp_cell", "A human egg is huge for a cell. It carries a huge stock of mitochondrial DNA, on average around two hundred thousand copies.",
      "इंसान का अंडाणु एक कोशिका के हिसाब से बहुत बड़ा है। इसमें माइटोकॉन्ड्रियल DNA का बड़ा भंडार होता है, औसतन लगभग दो लाख प्रतियाँ।",
      mode="egg", label=["ABOUT 200,000 COPIES", "of mitochondrial DNA"], source=REYNIER),
    S("atp_cell", "It varies a lot from egg to egg, from about twenty thousand to about six hundred thousand.",
      "यह हर अंडाणु में बहुत अलग होता है, लगभग बीस हज़ार से लगभग छह लाख तक।",
      mode="egg", label=["20,000 TO 600,000", "it varies a lot"], source=REYNIER),
    S("atp_cell", "A sperm brings only a few mitochondria, packed in its middle to power its tail.",
      "शुक्राणु सिर्फ़ कुछ माइटोकॉन्ड्रिया लाता है, जो उसकी पूँछ को चलाने के लिए बीच में भरे होते हैं।",
      mode="egg", label=["A FEW IN THE SPERM", "to power the tail"]),
    S("atp_cell", "After fertilisation, the sperm's mitochondria are tagged and destroyed.",
      "निषेचन के बाद, शुक्राणु के माइटोकॉन्ड्रिया पर निशान लगाकर उन्हें नष्ट कर दिया जाता है।",
      mode="egg", label=["TAGGED AND DESTROYED", "soon after fertilisation"], source=SUTOVSKY),
    S("atp_cell", "So you get your mitochondria almost entirely from your mother. Very rare exceptions have been reported.",
      "तो आपके माइटोकॉन्ड्रिया लगभग पूरी तरह आपकी माँ से आते हैं। बहुत ही कम अपवाद दर्ज हुए हैं।",
      label=["FROM YOUR MOTHER", "almost always"], source=LUO),
    S("atp_cell", "She got hers from her mother, and she from hers, in a line running back through every generation.",
      "उन्हें अपने माइटोकॉन्ड्रिया अपनी माँ से मिले, और उन्हें अपनी माँ से, हर पीढ़ी से पीछे जाती एक कतार में।",
      mode="egg"),
    # ---- ending
    S("atp_synthase", "So that's the turbine's story. Protons spin it. Spending speeds it up. It can run backwards, it can become a heater, and it came from a bacterium your mother passed down.",
      "तो यह है turbine की कहानी। प्रोटॉन इसे घुमाते हैं। खर्च करने से यह तेज़ होता है। यह उल्टा चल सकता है, हीटर बन सकता है, और यह एक बैक्टीरिया से आया जिसे आपकी माँ ने आगे बढ़ाया।",
      mode="orbit", slow=0.4),
    S("atp_mito", "That's how much depends on these tiny machines.",
      "इतना कुछ इन नन्ही मशीनों पर टिका है।"),
    S("atp_synthase", "Right now, tiny turbines inside your cells are spinning about a hundred times a second, and every turn makes three ATP.",
      "इसी पल, आपकी कोशिकाओं में नन्हे turbine हर सेकंड लगभग सौ बार घूम रहे हैं, और हर चक्कर तीन ATP बनाता है।",
      mode="orbit", slow=0.4, label=["~100 TURNS A SECOND", "3 ATP every turn"], source=WATT),
    S("atp_muscle", "So if your mitochondria came from your mother, and hers from her mother, how far back do you think that line goes?",
      "तो अगर आपके माइटोकॉन्ड्रिया आपकी माँ से आए, और उनके उनकी माँ से, तो आपको क्या लगता है यह कतार कितनी पीछे तक जाती है?"),
]

HI = {
    "CHAPTER 9": "अध्याय नौ", "CHAPTER 10": "अध्याय दस", "CHAPTER 11": "अध्याय ग्यारह",
    "CHAPTER 12": "अध्याय बारह", "CHAPTER 13": "अध्याय तेरह",
    "What Happens When You Run?": "दौड़ने पर क्या होता है?",
    "Can The Turbine Run Backwards?": "क्या turbine उल्टा चल सकता है?",
    "How Does Brown Fat Make Heat?": "ब्राउन फ़ैट गर्मी कैसे बनाता है?",
    "Where Did Mitochondria Come From?": "माइटोकॉन्ड्रिया कहाँ से आए?",
    "Why Only From Your Mother?": "सिर्फ़ माँ से ही क्यों?",
    "THE FIRST SECONDS": "पहले कुछ सेकंड", "the ATP already there": "पहले से मौजूद ATP",
    "PHOSPHOCREATINE": "फ़ॉस्फ़ोक्रिएटिन", "an instant backup": "तुरंत बैकअप",
    "GLYCOLYSIS": "ग्लाइकोलिसिस", "sugar split, no oxygen": "बिना ऑक्सीजन शक्कर टूटती है",
    "10 SECOND SPRINT": "10 सेकंड की दौड़", "~3% from mitochondria": "~3% माइटोकॉन्ड्रिया से",
    "30 SECOND SPRINT": "30 सेकंड की दौड़", "over a quarter": "एक चौथाई से ज़्यादा",
    "THE LONG RUN": "लंबी दौड़", "mitochondria take over": "माइटोकॉन्ड्रिया संभालते हैं",
    "ADP + PHOSPHATE": "ADP + फ़ॉस्फ़ेट", "what spent ATP leaves": "खर्च हुए ATP का बचा",
    "MORE ADP = FASTER": "ज़्यादा ADP = तेज़", "respiratory control": "रेस्पिरेटरी कंट्रोल",
    "BREATHING HARD": "तेज़ साँस", "more oxygen for the chain": "chain के लिए ज़्यादा ऑक्सीजन",
    "ABOUT 10x THE OXYGEN": "लगभग 10 गुना ऑक्सीजन", "at full effort": "पूरी ताकत पर",
    "HEART MUSCLE": "दिल की मांसपेशी", "over a quarter is mitochondria": "एक चौथाई से ज़्यादा माइटोकॉन्ड्रिया",
    "RUNNING BACKWARDS": "उल्टा चलना", "fed ATP, it splits it": "ATP खिलाओ, वह तोड़ता है",
    "PUMP MODE": "pump मोड", "ATP in, protons out": "ATP अंदर, प्रोटॉन बाहर",
    "FED ATP": "ATP खिलाया", "the head turned": "सिर घूमा",
    "E. COLI": "E. COLI", "without oxygen": "बिना ऑक्सीजन",
    "A DRAINED DAM": "खाली बाँध", "turbines could burn ATP": "turbine ATP जला सकते हैं",
    "IF1": "IF1", "the brake": "ब्रेक",
    "ATP SAVED": "ATP बचा", "when the dam drains": "जब बाँध खाली हो",
    "BROWN FAT": "ब्राउन फ़ैट", "packed with mitochondria": "माइटोकॉन्ड्रिया से भरा",
    "UCP1": "UCP1", "a gap in the dam": "बाँध में दरार",
    "NO TURBINE": "turbine नहीं", "protons leak back": "प्रोटॉन वापस रिसते हैं",
    "HEAT": "गर्मी", "instead of ATP": "ATP की जगह",
    "ADULTS TOO": "बड़ों में भी", "neck and collarbones": "गर्दन और कॉलरबोन",
    "ONCE BACTERIA": "कभी बैक्टीरिया थे", "free-living cells": "आज़ाद कोशिकाएँ",
    "OVER 1.5 BILLION YEARS AGO": "डेढ़ अरब साल से भी पहले", "one cell inside another": "एक कोशिका दूसरी के अंदर",
    "A PARTNERSHIP": "एक साझेदारी", "shelter for energy": "घर के बदले ऊर्जा",
    "ONE ANCESTOR": "एक ही पूर्वज", "for all mitochondria": "सारे माइटोकॉन्ड्रिया का",
    "THEIR OWN DNA": "उनका अपना DNA", "left from the bacterium": "बैक्टीरिया की निशानी",
    "16,569 BASE PAIRS": "16,569 base pairs", "37 genes": "37 genes",
    "TWO TURBINE PARTS": "turbine के दो टुकड़े", "written in mitochondrial DNA": "माइटोकॉन्ड्रियल DNA में लिखे",
    "HUNDREDS PER CELL": "हर कोशिका में सैकड़ों", "each with its own DNA": "हर एक का अपना DNA",
    "ABOUT 200,000 COPIES": "लगभग 2 लाख प्रतियाँ", "of mitochondrial DNA": "माइटोकॉन्ड्रियल DNA की",
    "A FEW IN THE SPERM": "शुक्राणु में कुछ ही", "to power the tail": "पूँछ चलाने के लिए",
    "TAGGED AND DESTROYED": "निशान लगाकर नष्ट", "soon after fertilisation": "निषेचन के जल्दी बाद",
    "FROM YOUR MOTHER": "आपकी माँ से",
    "ABOUT 10 SECONDS": "लगभग 10 सेकंड", "then the backup runs low": "फिर बैकअप घटता है",
    "ABOUT 75 SECONDS": "लगभग 75 सेकंड", "half from mitochondria": "आधा माइटोकॉन्ड्रिया से",
    "HEAD AND SHAFT ONLY": "सिर्फ़ सिर और धुरी", "from a heat-loving bacterium": "गर्मी पसंद बैक्टीरिया से",
    "ASGARD ARCHAEA": "ASGARD ARCHAEA", "the host's relatives": "मेज़बान के रिश्तेदार",
    "20,000 TO 600,000": "20,000 से 6 लाख", "it varies a lot": "बहुत अलग-अलग", "almost always": "लगभग हमेशा",
    "~100 TURNS A SECOND": "हर सेकंड ~100 चक्कर", "3 ATP every turn": "हर चक्कर 3 ATP",
}

SOURCES_EXTRA = ("; Baker, McCormick & Robergs 2010, J Nutr Metab 905612 (sprint energy systems); Brand & Nicholls 2011, "
                 "Biochem J 435:297 (respiratory control); Kaminsky et al. 2015, Mayo Clin Proc 90:1515 (VO2max); Sulkin et al. "
                 "2014, J Struct Biol 188:55 (heart mitochondria); Nakamoto et al. 2008, Arch Biochem Biophys 476:43 (reverse "
                 "running in bacteria); Campanella et al. 2008, Cell Metab 8:13 (IF1); Fedorenko et al. 2012, Cell 151:400 (UCP1); "
                 "Lidell et al. 2013, Nat Med 19:631 and Cypess et al. 2009, NEJM 360:1509 (brown fat); Parfrey et al. 2011, PNAS "
                 "108:13624 and Roger et al. 2017, Curr Biol 27:R1177 (origin of mitochondria); Anderson et al. 1981, Nature 290:457 "
                 "(human mtDNA); Robin & Wong 1988, J Cell Physiol 136:507; Reynier et al. 2001, Mol Hum Reprod 7:425 (egg mtDNA); "
                 "Sutovsky et al. 1999, Nature 402:371 and Luo et al. 2018, PNAS 115:13039 (maternal inheritance).")


def w(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def ext():
    for lang in ("", "_hi"):
        base = json.loads((H / f"book_atp{lang}" / "script.json").read_text(encoding="utf-8"))
        sc = {k: base[k] for k in ("title_options", "share", "facts", "description", "sources", "tags")}
        sc["scenes"] = [{"narration": (en if not lang else hi)} for _, en, hi in EXT]
        w(H / f"book_atp_ext{lang}" / "script.json", sc)
    labels = {t for sh, _, _ in EXT for t in sh.get("label", []) + sh.get("chapter", [])}
    missing = labels - set(HI)
    assert not missing, missing
    w(H / "book_atp_ext" / "shots.json", {"shots": [sh for sh, _, _ in EXT], "hi_labels": {k: HI[k] for k in sorted(labels)}})
    print("ext:", len(EXT), "scenes;", sum(len(en.split()) for _, en, _ in EXT), "EN words")


def _probe(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, check=True).stdout)


def merge():
    for lang in ("", "_hi"):
        old, new, out = H / f"book_atp{lang}", H / f"book_atp_ext{lang}", H / f"book_atp_long{lang}"
        out.mkdir(exist_ok=True)
        scenes_o = json.loads((old / "scenes.json").read_text())
        cut = scenes_o[KEEP][0]                                  # where the old ending began
        words_o = [x for x in json.loads((old / "words.json").read_text(encoding="utf-8")) if x["start"] < cut]
        words_n = json.loads((new / "words.json").read_text(encoding="utf-8"))
        scenes_n = json.loads((new / "scenes.json").read_text())
        lead = scenes_n[0][0]                                    # leading silence of the new recording
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(old / "voice.mp3"), "-i", str(new / "voice.mp3"),
                        "-filter_complex", f"[0]atrim=0:{cut},asetpts=N/SR/TB[a];[1]atrim={lead},asetpts=N/SR/TB[b];[a][b]concat=n=2:v=0:a=1",
                        "-c:a", "libmp3lame", "-b:a", "192k", str(out / "voice.mp3")], check=True)
        off = cut - lead
        words = words_o + [dict(x, start=round(x["start"] + off, 3), end=round(x["end"] + off, 3)) for x in words_n]
        scenes = scenes_o[:KEEP] + [[round(a + off, 3), round(b + off, 3)] for a, b in scenes_n]
        scenes[KEEP - 1][1] = scenes[KEEP][0]
        w(out / "words.json", words)
        w(out / "scenes.json", scenes)
        so = json.loads((old / "script.json").read_text(encoding="utf-8"))
        sn = json.loads((new / "script.json").read_text(encoding="utf-8"))
        so["scenes"] = so["scenes"][:KEEP] + sn["scenes"]
        so["sources"] = so["sources"].rstrip(".") + SOURCES_EXTRA
        if lang:
            so["title_options"] = ["आपके अंदर का नन्हा turbine: आपकी ऊर्जा की पूरी कहानी"]
            so["description"] = ("आपकी कोशिकाओं के अंदर एक नन्हा turbine हर सेकंड लगभग सौ बार घूमता है और हर चक्कर में तीन ATP "
                                 "बनाता है। तेरह अध्यायों में उसकी पूरी कहानी: वह कैसे चलता है, दौड़ते समय क्या होता है, वह उल्टा कैसे "
                                 "चलता है, ब्राउन फ़ैट गर्मी कैसे बनाता है, और माइटोकॉन्ड्रिया कभी बैक्टीरिया थे और माँ से ही क्यों "
                                 "आते हैं। #hindi #science #biology")
        else:
            so["description"] = ("Inside your cells, a motor about ten billionths of a metre across spins around a hundred times a "
                                 "second, and every turn makes three molecules of ATP. Its whole story in thirteen chapters: how it "
                                 "works, what happens when you run, how it can run backwards, how brown fat turns it into heat, and "
                                 "why your mitochondria were once bacteria and come from your mother.")
        w(out / "script.json", so)
        sp = json.loads((old / "spec.json").read_text(encoding="utf-8"))
        shots_n = json.loads((H / "book_atp_ext" / "shots.json").read_text(encoding="utf-8"))
        sp["shots"] = sp["shots"][:KEEP] + [dict(s, seconds=0) for s in shots_n["shots"]]
        if lang:
            sp["hi_labels"] = dict(sp.get("hi_labels", {}), **shots_n["hi_labels"])
            for s in sp["shots"][KEEP:]:
                if s.get("chapter"):
                    s["chapter"] = [HI[s["chapter"][0]], HI[s["chapter"][1]]]
        w(out / "spec.json", sp)
        meta = json.loads((new / "voice_meta.json").read_text())
        w(out / "voice_meta.json", dict(meta, merged_from=[str(old.name), str(new.name)], cut_s=cut))
        print(lang or "en", "merged:", len(so["scenes"]), "scenes,", round(_probe(out / "voice.mp3"), 1), "s")


def seconds():
    """One render serves both: new shots render at the longer voice, timed events at the shorter (as make_pair)."""
    en = json.loads((H / "book_atp_long" / "spec.json").read_text(encoding="utf-8"))
    hi = json.loads((H / "book_atp_long_hi" / "spec.json").read_text(encoding="utf-8"))
    for a, b in zip(en["shots"][KEEP:], hi["shots"][KEEP:]):
        r = round(max(a["seconds"], b["seconds"]) + 0.1, 3)
        e = round(min(a["seconds"], b["seconds"]), 3)
        for s in (a, b):
            s["render_seconds"], s["event_seconds"] = r, e
    w(H / "book_atp_long" / "spec.json", en)
    w(H / "book_atp_long_hi" / "spec.json", hi)
    print("new render seconds total", round(sum(s["render_seconds"] for s in en["shots"][KEEP:]), 1))


{"ext": ext, "merge": merge, "seconds": seconds}[sys.argv[1]]()
