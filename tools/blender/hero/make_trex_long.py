import copy, json, os, sys
R = r"C:\Users\Sitesh Kumar Dash\Projects\yt-studio"
os.chdir(R); sys.path.insert(0, R)

P = {"ground": "plain"}
JAW = {"cam": [[9.5, -15.5, 6.6], [8.0, -13.5, 6.3]], "tgt": [[0, -4.6, 5.4], [0, -4.6, 5.4]], "lens": 32}
ARM = {"cam": [[4.6, -2.6, 3.3], [4.0, -2.4, 3.2]], "tgt": [[0, -2.3, 3.1], [0, -2.3, 3.1]], "lens": 36, "xr_start": True,
       "anim": "idle", "muscle_groups": ["ARM"], "bone_groups": ["ARMS", "NECK", "SKULL"]}
S_SELL = "Sellers et al. 2017, PeerJ"
S_HG = "Hutchinson & Garcia 2002, Nature"
S_FUN = "Funston et al. 2021, Canadian Journal of Earth Sciences"
S_WOOD = "Woodward et al. 2020, Science Advances; Schroeder et al. 2021, Science"
S_ERI = "Erickson et al. 2004, Nature"
S_SUE = "Field Museum (FMNH PR 2081); Hutchinson et al. 2011, PLoS ONE"
S_STE = "Stevens 2006, Journal of Vertebrate Paleontology"
S_GIG = "Gignac & Erickson 2017, Scientific Reports; Erickson et al. 2012, PLoS ONE"
S_CHIN = "Chin et al. 1998, Nature"
S_CAR = "Carpenter & Smith 2001, Mesozoic Vertebrate Life"
S_PAD = "Padian 2022, Acta Palaeontologica Polonica"
S_SCH = "Schulte et al. 2010, Science; Renne et al. 2013, Science"

# (english, hindi, shot, hindi-only shot changes)
SC = [
 # ---- opening: the puzzle, the full animal on screen from frame 1
 ("If you raced a Tyrannosaurus rex, you wouldn't need a sports car to escape. A good bicycle might do it.",
  "अगर तुम्हारी रेस एक Tyrannosaurus rex से हो, तो बचने के लिए sports car की ज़रूरत नहीं। एक अच्छी साइकिल शायद काफ़ी होती।",
  dict({"kind": "closeup_roar", "overlay": "none", "seconds": 6}, **P)),
 ("At around eight tonnes, a true sprint would likely have put more strain on its leg bones than they could take.",
  "करीब आठ टन के इस शरीर के लिए, तेज़ दौड़ इसकी टांगों की हड्डियों पर इतना ज़ोर डालती, जितना वो शायद सह नहीं पातीं।",
  {"kind": "stress_run", "overlay": "none", "seconds": 6, "lens": 32, "source": S_SELL}),
 ("So here's the puzzle. How does a hunter that cannot run become the most famous predator that ever lived?",
  "तो पहेली ये है। जो शिकारी दौड़ ही नहीं सकता था, वो दुनिया का सबसे मशहूर शिकारी कैसे बना?",
  {"kind": "race_pass", "kmh": 20, "car_kmh": 50, "lens": 22, "car_behind_m": 9, "overlay": "none", "seconds": 6}),
 ("To find out, we'll follow one T. rex through its whole life, from the egg to the day its world ended. And at every stage, we'll test the legend against the science.",
  "ये जानने के लिए, हम एक T. rex की पूरी ज़िंदगी देखेंगे, अंडे से लेकर उस दिन तक, जब उसकी दुनिया ख़त्म हुई। और हर मोड़ पर, कहानी को विज्ञान की कसौटी पर परखेंगे।",
  dict({"kind": "run_at_camera", "overlay": "none", "freeze_s": 0.0, "seconds": 8}, **P)),

 # ---- chapter 1
 ("Chapter one. Born dangerous.", "पहला अध्याय। ख़तरनाक जन्म।",
  {"kind": "hatch", "length_m": 0.9, "crack_s": 5.0, "overlay": "chapter", "chapter": ["CHAPTER 1", "BORN DANGEROUS"],
   "seconds": 3.5}, {"chapter": ["अध्याय 1", "ख़तरनाक जन्म"]}),
 ("Every tyrannosaur started inside an egg. In 2021, scientists described the first known tyrannosaur embryo fossils: a tiny jaw bone and a claw, from close relatives of T. rex.",
  "हर tyrannosaur की शुरुआत एक अंडे से हुई। दो हज़ार इक्कीस में scientists ने tyrannosaur के भ्रूण के पहले fossil बताए: एक छोटी सी जबड़े की हड्डी और एक पंजा, जो T. rex के क़रीबी रिश्तेदारों के थे।",
  {"kind": "hatch", "length_m": 0.9, "crack_s": 5.5, "overlay": "none", "seconds": 9, "source": S_FUN}),
 ("From those bones, they estimated a hatchling about the size of a small dog, roughly ninety centimetres, or three feet, long.",
  "उन हड्डियों से अंदाज़ा लगाया गया कि अंडे से निकला बच्चा एक छोटे कुत्ते जितना था, करीब नब्बे सेंटीमीटर लंबा।",
  {"kind": "hatch", "length_m": 0.9, "crack_s": 0.8, "overlay": "label", "label": ["SMALL DOG SIZE", "a baby tyrannosaur"],
   "seconds": 7, "source": S_FUN}),
 ("Small enough to be eaten by almost anything. For its first years, a young tyrannosaur was probably prey, not predator.",
  "इतना छोटा, कि लगभग कोई भी इसे खा जाए। शुरुआती सालों में, ये शायद शिकारी नहीं, ख़ुद शिकार था।",
  {"kind": "speed_track", "length_m": 1.0, "kmh": 7, "overlay": "none", "seconds": 7,
   "scale_prop": {"file": "cars/sedan.glb", "length_m": 4.5, "at": [-5.2, 0.0, 0]},
   "cam": [[2.8, 2.5, 1.6], [2.8, -2.0, 1.6]], "tgt": [[-2.6, 1.5, 0.5], [-2.6, -3.0, 0.5]], "lens": 32}),
 ("But the real T. rex was stranger than the legend. Because the next stage of its life looked like a different animal altogether.",
  "पर असली T. rex, कहानियों से कहीं ज़्यादा अजीब था। क्योंकि ज़िंदगी का अगला दौर, बिल्कुल अलग जानवर जैसा दिखता था।",
  dict({"kind": "speed_track", "length_m": 5.0, "kmh": 30, "overlay": "none", "seconds": 7, "cam_dist": 7.5, "cam_h": 1.5}, **P)),

 # ---- chapter 2
 ("Chapter two. The teenage years.", "दूसरा अध्याय। जवानी के साल।",
  dict({"kind": "speed_track", "length_m": 5.0, "kmh": 30, "overlay": "chapter", "chapter": ["CHAPTER 2", "THE TEENAGE YEARS"],
        "seconds": 3.5, "cam_dist": 7.5, "cam_h": 1.5}, **P), {"chapter": ["अध्याय 2", "जवानी के साल"]}),
 ("Young T. rex were built differently from the adults: long, slender legs, a lighter body, and a narrower skull.",
  "जवान T. rex की बनावट बड़ों से अलग थी: लंबी, पतली टांगें, हल्का शरीर, और पतली खोपड़ी।",
  dict({"kind": "speed_track", "length_m": 5.0, "kmh": 30, "overlay": "label", "label": ["LONG, SLIM LEGS", "built for speed"],
        "seconds": 7, "cam_dist": 7.5, "cam_h": 1.5, "source": S_WOOD}, **P)),
 ("Their bites couldn't crush bone yet. So instead of competing with the giants, they likely hunted smaller, quicker animals.",
  "इनका bite अभी हड्डी नहीं तोड़ सकता था। इसलिए बड़ों से मुक़ाबला करने के बजाय, ये शायद छोटे और तेज़ जानवरों का शिकार करते थे।",
  dict({"kind": "speed_track", "length_m": 5.0, "kmh": 25, "overlay": "label", "label": ["SMALLER, QUICKER PREY", "the giants ignored"],
        "seconds": 8, "cam_dist": 7.5, "cam_h": 1.5, "source": S_WOOD}, **P)),
 ("In 2020, scientists cut thin slices from the leg bones of two young T. rex, nicknamed Jane and Petey, and counted the rings. They were about thirteen and fifteen years old, and still growing fast.",
  "दो हज़ार बीस में, scientists ने दो जवान T. rex, जिनके नाम Jane और Petey रखे गए, उनकी टांग की हड्डियों के पतले टुकड़े काटे, और छल्ले गिने। वो करीब तेरह और पंद्रह साल के थे, और अब भी तेज़ी से बढ़ रहे थे।",
  dict({"kind": "speed_track", "length_m": 7.0, "kmh": 18, "overlay": "label", "label": ["JANE AND PETEY", "about 13 and 15 years old"],
        "seconds": 10, "cam_dist": 10.0, "cam_h": 2.0, "source": "Woodward et al. 2020, Science Advances"}, **P)),
 ("Then came the growth spurt. Inside the bones are growth rings, a little like the rings in a tree trunk. Counting them shows how fast each animal grew.",
  "फिर आया तेज़ी से बढ़ने का दौर। हड्डियों के अंदर बढ़त के छल्ले होते हैं, कुछ-कुछ पेड़ के तने के छल्लों जैसे। उन्हें गिनकर पता चलता है कि जानवर कितनी तेज़ी से बढ़ा।",
  dict({"kind": "grow", "from_m": 5.0, "ages": [12, 14], "overlay": "none", "seconds": 9, "source": S_ERI}, **P)),
 ("Around age fourteen, growth exploded. At its peak, a young T. rex added roughly two kilograms a day, nearly five pounds, for about four years.",
  "करीब चौदह साल की उम्र में, बढ़त अचानक तेज़ हो गई। सबसे तेज़ दौर में, जवान T. rex हर दिन करीब दो किलो बढ़ता था, और ये लगभग चार साल चलता रहा।",
  dict({"kind": "grow", "from_m": 5.0, "ages": [14, 18], "overlay": "grow", "seconds": 9, "source": S_ERI}, **P)),
 ("By its late teens, it weighed several tonnes. Nothing in its world could hunt it anymore.",
  "उन्नीस साल से पहले ही, इसका वज़न कई टन हो चुका था। अब इसकी दुनिया में कोई इसका शिकार नहीं कर सकता था।",
  dict({"kind": "closeup_roar", "overlay": "none", "seconds": 6}, **P)),

 # ---- chapter 3
 ("Chapter three. A living bulldozer.", "तीसरा अध्याय। जीता-जागता bulldozer।",
  {"kind": "balance", "tonnes": 8.4, "car_t": 1.4, "cars": 6, "start_cars": 0, "drop_s": [5.0, 6.0], "cam_scale": 0.8,
   "overlay": "chapter", "chapter": ["CHAPTER 3", "A LIVING BULLDOZER"], "seconds": 3.5},
  {"chapter": ["अध्याय 3", "जीता-जागता bulldozer"]}),
 ("The most famous T. rex skeleton is called Sue, found in South Dakota in 1990. Sue was about twelve metres long, around forty feet.",
  "सबसे मशहूर T. rex कंकाल का नाम है Sue, जो उन्नीस सौ नब्बे में अमेरिका के South Dakota में मिला। Sue करीब बारह मीटर लंबा था।",
  dict({"kind": "xray_scan", "lens": 28, "reveal": {"bones": [0.3, 5.0], "muscles": [5.2, 7.5]}, "overlay": "label",
        "label": ["SUE", "about 12 m long"], "seconds": 9, "source": S_SUE})),
 ("Studies put an adult like Sue at roughly eight tonnes, though estimates vary. On a giant see-saw, you'd need about six small cars to balance it.",
  "Studies के हिसाब से Sue जैसे बड़े T. rex का वज़न करीब आठ टन था, हालांकि अंदाज़े अलग-अलग हैं। एक बड़े तराज़ू पर, इसे बराबर करने के लिए करीब छह छोटी कारें चाहिए।",
  {"kind": "balance", "tonnes": 8.4, "car_t": 1.4, "cars": 6, "start_cars": 0, "drop_s": [2.5, 6.5], "cam_scale": 0.8,
   "overlay": "label", "label": ["~8 TONNES", "= about 6 small cars"], "seconds": 9, "source": S_SUE},
  {"label": ["~8 TONNES", "= about 6 small cars"]}),
 ("Sue's skull alone is about one point four metres long, and about ninety percent of its skeleton was found.",
  "अकेली Sue की खोपड़ी करीब डेढ़ मीटर लंबी है, और उसका करीब नब्बे प्रतिशत कंकाल मिला।",
  dict({"kind": "xray_jaw", "reveal": {"bones": [0.2, 2.5], "muscles": [30.0, 31.0]}, "overlay": "label", "label": ["SUE'S SKULL", "~1.4 m long"],
        "anim": "idle", "seconds": 8, "source": "Field Museum, Chicago", "xr_start": True,
        "bone_groups": ["SKULL", "NECK"], "muscle_groups": ["JAW"]}, **dict(JAW, cam=[[4.8, -10.5, 6.4], [4.0, -9.4, 6.2]],
        tgt=[[0, -4.8, 5.0], [0, -4.8, 5.0]], lens=35))),
 ("And all of that weight rested on just two legs, with a long, heavy tail balancing the head and body over the hips.",
  "और ये सारा वज़न सिर्फ़ दो टांगों पर टिका था, और लंबी, भारी पूंछ सिर और शरीर को कूल्हों के ऊपर संतुलित रखती थी।",
  {"kind": "size_tower", "cars": 6, "lens": 24, "overlay": "none", "seconds": 8}),
 ("Which brings us back to the big question. Could something this heavy actually run?",
  "और यहीं से हम लौटते हैं बड़े सवाल पर। क्या इतना भारी जानवर सच में दौड़ सकता था?",
  dict({"kind": "closeup_roar", "overlay": "none", "seconds": 6}, **P)),

 # ---- chapter 4
 ("Chapter four. The running myth.", "चौथा अध्याय। दौड़ने का भ्रम।",
  {"kind": "stress_run", "lens": 32, "overlay": "chapter", "chapter": ["CHAPTER 4", "THE RUNNING MYTH"], "seconds": 3.5},
  {"chapter": ["अध्याय 4", "दौड़ने का भ्रम"]}),
 ("In 2017, a team in Britain built a T. rex inside a computer, with every bone and the muscles that pulled on them, and asked it to run.",
  "दो हज़ार सत्रह में, ब्रिटेन की एक टीम ने computer के अंदर एक T. rex बनाया, हर हड्डी और उन्हें खींचने वाली muscles के साथ, और फिर उसे दौड़ाकर देखा।",
  {"kind": "xray_scan", "lens": 28, "reveal": {"bones": [0.3, 4.5], "muscles": [4.7, 7.5]}, "overlay": "xray_scan",
   "seconds": 9, "source": S_SELL}),
 ("The computer tried thousands of ways to fire the muscles, searching for the fastest way to move.",
  "Computer ने muscles को चलाने के हज़ारों तरीके आज़माए, सबसे तेज़ चाल ढूंढने के लिए।",
  {"kind": "xray_scan", "lens": 28, "reveal": {"bones": [0.1, 0.5], "muscles": [0.6, 2.0]}, "overlay": "none", "seconds": 6, "source": S_SELL}),
 ("At every running speed, the stress in its leg bones climbed so high that the bones would likely have broken. The model could walk. It couldn't run.",
  "हर दौड़ने वाली speed पर, टांगों की हड्डियों पर दबाव इतना बढ़ गया कि हड्डियां शायद टूट जातीं। Model चल सकता था। दौड़ नहीं सकता था।",
  {"kind": "stress_run", "lens": 32, "overlay": "stress", "seconds": 9, "source": S_SELL}),
 ("An earlier study reached the same wall from another side. To sprint fast, an animal this heavy would need about forty percent of its whole body in the muscles of each leg. Nothing alive carries that much.",
  "एक पुरानी study भी दूसरे रास्ते से यहीं पहुंची थी। इतने भारी जानवर को तेज़ दौड़ने के लिए, हर टांग की muscles में अपने पूरे शरीर का करीब चालीस प्रतिशत चाहिए। कोई ज़िंदा जानवर इतना नहीं ढोता।",
  {"kind": "muscle_needed", "muscle_scale": 2.6, "lens": 28, "overlay": "muscle_needed", "seconds": 11, "source": S_HG}),
 ("That isn't as strange as it sounds. Elephants, the heaviest land animals alive today, never get all four feet off the ground at once, even at top speed.",
  "ये उतना अजीब नहीं जितना लगता है। हाथी, जो आज ज़मीन के सबसे भारी जानवर हैं, सबसे तेज़ चलते हुए भी कभी चारों पैर एक साथ ज़मीन से नहीं उठाते।",
  dict({"kind": "speed_track", "kmh": 15, "lens": 24, "overlay": "label", "label": ["LIKE AN ELEPHANT", "fast, but never airborne"],
        "seconds": 9, "source": "Hutchinson et al. 2003, Nature"}, **P)),
 ("So the real T. rex probably topped out at a brisk walk. In the 2017 model, that was around twenty kilometres an hour, about twelve miles an hour.",
  "तो असली T. rex की सबसे तेज़ चाल शायद तेज़ क़दमों वाली चाल थी। दो हज़ार सत्रह के model में, ये करीब बीस किलोमीटर प्रति घंटा थी।",
  {"kind": "speed_track", "kmh": 20, "lens": 22, "overlay": "speed_track", "seconds": 9, "source": S_SELL}),
 ("A car on a city street would leave it behind. So would a fit cyclist.",
  "शहर की सड़क पर चलती car इसे पीछे छोड़ देती। एक फ़िट साइकिल वाला भी।",
  {"kind": "race_pass", "kmh": 20, "car_kmh": 50, "lens": 22, "car_behind_m": 9, "overlay": "race_pass", "seconds": 6}),
 ("But the real T. rex was stranger than the legend. It didn't need to chase you. It needed to find you first.",
  "पर असली T. rex, कहानियों से कहीं ज़्यादा अजीब था। इसे तुम्हारा पीछा करने की ज़रूरत नहीं थी। पहले, इसे तुम्हें ढूंढना था।",
  dict({"kind": "closeup_roar", "overlay": "none", "seconds": 7}, **P)),

 # ---- chapter 5
 ("Chapter five. Eyes forward.", "पांचवां अध्याय। सामने देखती आंखें।",
  {"kind": "vision_cone", "lens": 24, "overlay": "chapter", "chapter": ["CHAPTER 5", "EYES FORWARD"], "seconds": 3.5},
  {"chapter": ["अध्याय 5", "सामने देखती आंखें"]}),
 ("In 2006, a scientist rebuilt the heads of meat-eating dinosaurs and traced where each eye could look.",
  "दो हज़ार छह में, एक scientist ने मांसाहारी dinosaurs के सिर दोबारा बनाए, और देखा कि हर आंख कहां तक देख सकती थी।",
  dict({"kind": "xray_jaw", "overlay": "label", "label": ["REBUILT HEAD", "where each eye can look"], "anim": "idle",
        "seconds": 7, "source": S_STE}, **JAW)),
 ("T. rex had forward-facing eyes. Their views overlapped across about fifty-five degrees, wider than in a modern hawk.",
  "इस T. rex की आंखें सामने की ओर थीं। दोनों आंखों का नज़ारा करीब पचपन डिग्री तक एक-दूसरे पर चढ़ता था, आज के बाज़ से भी ज़्यादा।",
  {"kind": "vision_cone", "lens": 24, "overlay": "label", "label": ["55\u00b0 OVERLAP", "wider than a hawk's"], "seconds": 8, "source": S_STE}),
 ("That overlap gives depth vision, the same trick your own eyes use to judge exactly how far away something is.",
  "इसी से मिलती है depth vision, वही तरीका जिससे तुम्हारी आंखें बताती हैं कि कोई चीज़ ठीक कितनी दूर है।",
  {"kind": "vision_cone", "view": "behind", "overlay": "label", "label": ["DEPTH VISION", "how far away you are"], "seconds": 7}),
 ("Based on living birds and reptiles, its sharpest vision may have picked out objects several kilometres away, far beyond what we manage. So standing still probably wouldn't have saved you.",
  "आज के पक्षियों और reptiles के आधार पर, इसकी नज़र शायद कई किलोमीटर दूर की चीज़ें भी पहचान लेती, हमसे कहीं ज़्यादा। तो खड़े रहने से भी तुम शायद नहीं बचते।",
  {"kind": "speed_track", "kmh": 12, "overlay": "bars", "title": "HOW FAR IT MAY HAVE SEEN",
   "bars": [["T. REX (estimate)", 6, "yellow"], ["PEOPLE", 1.6, "cyan"]], "unit": "km", "seconds": 11, "source": S_STE}),

 # ---- chapter 6
 ("Chapter six. The bone crusher.", "छठा अध्याय। हड्डियां चबाने वाला।",
  dict({"kind": "xray_jaw", "anim": "idle", "overlay": "chapter", "chapter": ["CHAPTER 6", "THE BONE CRUSHER"], "seconds": 3.5}, **JAW),
  {"chapter": ["अध्याय 6", "हड्डियां चबाने वाला"]}),
 ("To estimate its bite, scientists rebuilt the jaw muscles using its closest living relatives, crocodiles and birds.",
  "इसके bite का अंदाज़ा लगाने के लिए, scientists ने इसके सबसे क़रीबी ज़िंदा रिश्तेदारों, मगरमच्छ और पक्षियों, की मदद से जबड़े की muscles दोबारा बनाईं।",
  dict({"kind": "xray_jaw", "reveal": {"bones": [0.3, 1.5], "muscles": [1.7, 6.0]}, "overlay": "xray_scan", "anim": "idle",
        "muscle_groups": ["JAW"], "bone_groups": ["SKULL", "NECK", "SPINE", "RIBS", "HIPS", "THIGHS", "SHINS", "FEET", "TAIL", "ARMS"],
        "seconds": 8, "source": S_GIG}, **JAW)),
 ("Their estimate: up to about thirty-five thousand newtons at the back teeth. More than twice the strongest bite ever measured in a living animal, the saltwater crocodile.",
  "उनका अंदाज़ा: पीछे के दांतों पर करीब साढ़े चौंतीस हज़ार newton तक। ये किसी भी ज़िंदा जानवर में नापे गए सबसे ताकतवर bite, खारे पानी के मगरमच्छ, से दोगुने से भी ज़्यादा है।",
  {"kind": "closeup_roar", "overlay": "bite_compare", "bars": [["SALTWATER CROC (measured)", 16414, "cyan"], ["T. REX (estimate)", 34522, "red"]],
   "seconds": 11, "source": S_GIG}),
 ("Its thick teeth focused that force onto small tips, with enough pressure to crack bone.",
  "इसके मोटे दांत उस ताकत को छोटी नोकों पर इकट्ठा कर देते थे, इतने दबाव से, कि हड्डी चटक जाए।",
  dict({"kind": "xray_jaw", "teeth_stress": True, "overlay": "tooth_pressure", "seconds": 7, "source": S_GIG}, **JAW)),
 ("Its biggest teeth, root and all, were about thirty centimetres long. That's about the length of a banana.",
  "इसके सबसे बड़े दांत, जड़ समेत, करीब तीस सेंटीमीटर लंबे थे। लगभग एक केले जितने।",
  dict({"kind": "closeup_roar", "overlay": "label", "label": ["~30 cm TEETH", "root and all"], "seconds": 7,
        "source": "Field Museum (Sue)"}, **P)),
 ("And fossil bones of its prey, like a Triceratops hip, carry deep T. rex bite marks, some punched deep into the bone.",
  "और इसके शिकार की fossil हड्डियों पर, जैसे एक Triceratops के कूल्हे पर, T. rex के गहरे दांतों के निशान हैं, कुछ तो हड्डी में गहरे धंसे हुए।",
  dict({"kind": "xray_jaw", "teeth_stress": True, "overlay": "label", "label": ["BITE MARKS", "on a Triceratops hip"], "seconds": 8,
        "source": "Erickson & Olson 1996, Journal of Vertebrate Paleontology"}, **JAW)),
 ("We even have the evidence. A giant fossil dropping, most likely from a T. rex, is up to half crushed bone.",
  "और इसका सबूत भी है। एक विशाल fossil potty, जो शायद T. rex की है, उसमें आधी तक कुचली हुई हड्डियां हैं।",
  {"kind": "coprolite", "overlay": "coprolite", "seconds": 8, "source": S_CHIN}),
 ("So our puzzle starts to make sense. Eyes that judge distance. A bite that breaks bone. Maybe it never needed to be fast.",
  "तो अब पहेली समझ आने लगती है। दूरी नापने वाली आंखें। हड्डी तोड़ने वाला bite। शायद इसे तेज़ होने की ज़रूरत ही नहीं थी।",
  dict({"kind": "closeup_roar", "overlay": "none", "seconds": 8}, **P)),

 # ---- chapter 7
 ("Chapter seven. The tiny arms mystery.", "सातवां अध्याय। छोटे हाथों का रहस्य।",
  dict({"kind": "xray_jaw", "reveal": {"bones": [0.3, 1.5], "muscles": [1.7, 3.0]}, "overlay": "chapter",
        "chapter": ["CHAPTER 7", "THE TINY ARMS MYSTERY"], "seconds": 3.5}, **ARM),
  {"chapter": ["अध्याय 7", "छोटे हाथों का रहस्य"]}),
 ("Then there are the arms everyone jokes about. In 2001, two scientists measured the arm bones and the scars where the muscles attached.",
  "और फिर आते हैं वो हाथ, जिनका सब मज़ाक उड़ाते हैं। दो हज़ार एक में, दो scientists ने हाथ की हड्डियां नापीं, और वो निशान भी जहां muscles जुड़ी थीं।",
  dict({"kind": "xray_jaw", "reveal": {"bones": [0.3, 3.0], "muscles": [3.2, 6.5]}, "overlay": "label",
        "label": ["BICEPS", "worked out from the bones"], "seconds": 9, "source": S_CAR}, **ARM)),
 ("Each arm was about a metre long, around three feet, ending in just two clawed fingers.",
  "हर हाथ करीब एक मीटर लंबा था, और उसके सिरे पर बस दो नुकीली उंगलियां।",
  dict({"kind": "xray_jaw", "reveal": {"bones": [0.2, 1.0], "muscles": [6.0, 6.5]}, "overlay": "label", "label": ["ABOUT 1 m", "two clawed fingers"],
        "seconds": 8, "source": "Carpenter & Smith 2001"}, **ARM)),
 ("Their calculation: the biceps alone could curl about two hundred kilograms, more than four hundred pounds. Small, but not weak.",
  "उनका हिसाब: अकेली biceps करीब दो सौ किलो उठा सकती थी। छोटे, पर कमज़ोर नहीं।",
  {"kind": "closeup_roar", "overlay": "bars", "title": "WHAT ONE ARM MAY CURL",
   "bars": [["T. REX ARM (estimate)", 200, "yellow"], ["ONE ADULT", 70, "cyan"]], "unit": "kg", "seconds": 9, "source": S_CAR}),
 ("So why so short? One idea, from 2022: when several adults tore into the same carcass, long arms would have been in the way of all those jaws. It's still debated. Nobody knows for sure.",
  "तो इतने छोटे क्यों? दो हज़ार बाईस का एक idea: जब कई बड़े T. rex एक ही शिकार पर टूटते, तो लंबे हाथ उन सारे जबड़ों के रास्ते में आते। इस पर अब भी बहस है। पक्का कोई नहीं जानता।",
  {"kind": "closeup_roar", "overlay": "label", "label": ["ONE IDEA", "long arms get bitten"], "seconds": 12, "source": S_PAD}),

 # ---- chapter 8: the climax
 ("Chapter eight. The last world.", "आठवां अध्याय। आख़िरी दुनिया।",
  {"kind": "asteroid", "phase": "calm", "overlay": "chapter", "chapter": ["CHAPTER 8", "THE LAST WORLD"], "seconds": 3.5},
  {"chapter": ["अध्याय 8", "आख़िरी दुनिया"]}),
 ("Sixty-six million years ago, T. rex was still here, at the top of its world.",
  "छह करोड़ साठ लाख साल पहले, T. rex अब भी यहीं था, अपनी दुनिया में सबसे ऊपर।",
  {"kind": "asteroid", "phase": "calm", "overlay": "none", "seconds": 7}),
 ("Then a rock about ten kilometres across, around six miles wide, came out of the sky.",
  "फिर आसमान से करीब दस किलोमीटर चौड़ी एक चट्टान आई।",
  {"kind": "asteroid", "phase": "streak", "overlay": "none", "seconds": 7, "source": S_SCH}),
 ("It struck what is now the Yucatán Peninsula in Mexico, and blasted a crater roughly one hundred and eighty kilometres wide.",
  "वो आज के Mexico के युकाटन इलाक़े में गिरी, और करीब एक सौ अस्सी किलोमीटर चौड़ा गड्ढा बना दिया।",
  {"kind": "asteroid", "phase": "flash", "flash_s": 0.6, "overlay": "none", "seconds": 8, "source": S_SCH}),
 ("Within hours, shock waves, wildfires and giant waves spread out from the impact.",
  "कुछ ही घंटों में, उस टक्कर से झटके, जंगल की आग और विशाल लहरें चारों ओर फैल गईं।",
  {"kind": "asteroid", "phase": "flash", "flash_s": 0.1, "overlay": "none", "seconds": 7, "source": S_SCH}),
 ("Dust and soot spread around the planet. Sunlight dimmed, plants struggled, and food chains collapsed.",
  "धूल और कालिख पूरी धरती पर फैल गई। धूप धुंधली हो गई, पौधे मुरझाने लगे, और खाने की पूरी कड़ी टूट गई।",
  {"kind": "asteroid", "phase": "dark", "overlay": "none", "seconds": 9, "source": S_SCH}),
 ("About three quarters of all species died out. Every T. rex was gone.",
  "धरती की करीब तीन-चौथाई प्रजातियां ख़त्म हो गईं। एक भी T. rex नहीं बचा।",
  {"kind": "asteroid", "phase": "dark", "overlay": "none", "seconds": 8, "source": S_SCH}),
 ("But not every dinosaur vanished. One group survived: the birds. Birds are dinosaurs too, and among the closest living relatives of T. rex.",
  "पर हर dinosaur ख़त्म नहीं हुआ। एक समूह बच गया: पक्षी। पक्षी भी dinosaur हैं, और T. rex के सबसे क़रीबी ज़िंदा रिश्तेदारों में से।",
  dict({"kind": "closeup_roar", "overlay": "none", "seconds": 10}, **P)),
 ("So the real T. rex could not outrun your car. But it could judge exactly where you stood, and bite through bone. The movie monster, or the real animal: which one sounds more frightening to you?",
  "तो असली T. rex तुम्हारी car से तेज़ नहीं दौड़ सकता था। पर वो ठीक-ठीक देख लेता कि तुम कहां खड़े हो, और हड्डी तक काट डालता। फ़िल्मों वाला राक्षस, या असली जानवर: तुम्हें कौन ज़्यादा डरावना लगता है?",
  dict({"kind": "closeup_roar", "overlay": "none", "seconds": 12}, **P)),
]


SENSES = [
 ("Its other senses were sharp too. Casts of its brain cavity show huge smell lobes, among the biggest of any meat-eating dinosaur.",
  "इसकी बाक़ी इंद्रियां भी तेज़ थीं। इसके दिमाग़ के खोल के सांचे दिखाते हैं कि सूंघने वाला हिस्सा बहुत बड़ा था, मांसाहारी dinosaurs में सबसे बड़े हिस्सों में से।",
  dict({"kind": "closeup_roar", "overlay": "label", "label": ["BIG SMELL LOBES", "a nose for food"], "seconds": 8,
        "cam": [[2.6, -9.0, 4.6], [2.0, -7.6, 4.8]], "tgt": [[0, -4.6, 4.6], [0, -4.6, 4.7]],
        "source": "Zelenitsky et al. 2009, Proceedings of the Royal Society B"}, **P)),
 ("And its inner ear was tuned to low, deep sounds, the kind that travel far across open ground.",
  "और इसके अंदरूनी कान धीमी, गहरी आवाज़ों के लिए बने थे, वो आवाज़ें जो खुले मैदान में दूर तक जाती हैं।",
  dict({"kind": "closeup_roar", "overlay": "label", "label": ["LOW SOUNDS", "heard from far away"], "seconds": 7,
        "cam": [[-6.5, -9.0, 5.2], [-5.6, -8.2, 5.0]], "tgt": [[0, -3.8, 4.8], [0, -3.8, 4.8]],
        "source": "Witmer & Ridgely 2009, The Anatomical Record"}, **P)),
]
SKIN = ("And forget a coat of feathers on the adults. Fossil skin found with T. rex bones shows small scales, at least on its neck, hips and tail.",
  "और बड़े T. rex पर पंखों का कोट भूल जाओ। इसकी हड्डियों के साथ मिली fossil चमड़ी पर छोटे-छोटे scales दिखते हैं, कम से कम गर्दन, कूल्हों और पूंछ पर।",
  dict({"kind": "closeup_roar", "overlay": "label", "label": ["SCALY SKIN", "neck, hips and tail"], "seconds": 9,
        "cam": [[8.5, -1.0, 3.0], [7.8, 0.5, 3.2]], "tgt": [[0, 0.5, 3.0], [0, 1.5, 3.0]],
        "source": "Bell et al. 2017, Biology Letters"}, **P))
i = next(k for k, r in enumerate(SC) if r[0].startswith("Based on living birds and reptiles"))
SC[i + 1:i + 1] = SENSES
i = next(k for k, r in enumerate(SC) if r[0].startswith("And all of that weight rested"))
SC.insert(i + 1, SKIN)
# every close-up from its own angle, so no two look alike
ANG = [((4.5, -12.5, 1.4), (2.6, -9.0, 1.6), (0, -3.5, 4.6), (0, -3.5, 4.9)),      # low hero
       ((10.0, -6.0, 3.0), (9.0, -4.8, 3.2), (0, -3.0, 4.0), (0, -3.0, 4.2)),      # profile
       ((5.0, -14.0, 8.5), (3.8, -11.0, 7.5), (0, -3.5, 4.0), (0, -3.5, 4.4)),     # high
       ((-8.0, -10.0, 2.6), (-3.0, -12.5, 2.8), (0, -3.5, 4.6), (0, -3.5, 4.8)),   # slow arc
       ((2.0, -8.0, 4.4), (1.4, -6.6, 4.6), (0, -4.0, 4.6), (0, -4.0, 4.8))]       # close face
k_ = 0
for r in SC:
    sh = r[2]
    if sh["kind"] == "closeup_roar" and "cam" not in sh:
        a0, a1, t0, t1 = ANG[k_ % len(ANG)]
        sh["cam"], sh["tgt"] = [list(a0), list(a1)], [list(t0), list(t1)]
        k_ += 1

def _move_after(first_words, anchor_words):
    i = next(k for k, r in enumerate(SC) if r[0].startswith(first_words))
    row = SC.pop(i)
    j = next(k for k, r in enumerate(SC) if r[0].startswith(anchor_words))
    SC.insert(j + 1, row)
_move_after("In 2020, scientists cut thin slices", "Then came the growth spurt.")
_move_after("That isn't as strange as it sounds.", "So the real T. rex probably topped out")

base = json.load(open("research/hero/trex/spec.json"))
spec = {k: v for k, v in base.items() if k != "shots"}
spec["aspect"] = "landscape"
spec["long"] = True
spec["caption_scale"] = 1.0
for name in ("trex_long", "trex_long_hi"):
    os.makedirs(f"research/hero/{name}", exist_ok=True)
    shots = []
    for row in SC:
        sh = copy.deepcopy(row[2])
        if name.endswith("_hi") and len(row) > 3:
            sh.update(row[3])
        shots.append(sh)
    json.dump(dict(spec, shots=shots), open(f"research/hero/{name}/spec.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

facts = ["All figures as in the five fact-checked T. rex Shorts (trex, trex_bite, trex_baby, trex_vision, trex_arms) plus: "
         "Sue (FMNH PR 2081) found 1990 in South Dakota, about 12.3 m; Chicxulub impactor ~10 km, crater ~180 km, "
         "about three quarters of species lost (Schulte et al. 2010, Science; Renne et al. 2013, Science, 66 Ma).",
         "Wording rules from council round 7: 20 km/h = fastest gait in the Sellers 2017 model; eyesight = model estimate; "
         "200 kg = Carpenter & Smith's calculation; hatchling size from tyrannosaur relatives (Funston 2021); mass 'estimates vary'; "
         "birds are T. rex's relatives, not its descendants."]
srcs = "; ".join(sorted({S_SELL, S_HG, S_FUN, S_WOOD, S_ERI, S_SUE, S_STE, S_GIG, S_CHIN, S_CAR, S_PAD, S_SCH}))
en = {"title_options": ["Was The Real T. rex As Terrifying As The Movies?"], "facts": facts, "sources": srcs,
      "description": "The real T. rex probably couldn't run. So how did it become the most famous predator that ever lived? "
                     "We follow one T. rex from the egg to the asteroid, in 3D, and test every part of the legend against published science.",
      "share": {"myth": "T. rex could chase down a car, like in the movies.", "truth": "Computer models of its bones and muscles say running would have broken its legs; it walked fast, around 20 km/h.", "line": "The real T. rex could not outrun your car."},
      "tags": ["T. rex", "Tyrannosaurus rex", "dinosaurs", "paleontology", "science documentary", "3D animation", "Chicxulub"],
      "scenes": [{"narration": r[0]} for r in SC]}
hi = dict(en, title_options=["क्या असली T. rex फ़िल्मों जितना ख़तरनाक था?"],
          description="असली T. rex शायद दौड़ नहीं सकता था। तो फिर ये दुनिया का सबसे मशहूर शिकारी कैसे बना? अंडे से लेकर asteroid तक, एक T. rex की पूरी ज़िंदगी, 3D में, और हर बात विज्ञान की कसौटी पर।",
          tags=["T. rex", "dinosaur hindi", "science hindi", "डायनासोर", "3D animation"],
          scenes=[{"narration": r[1]} for r in SC])
json.dump(en, open("research/hero/trex_long/script.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump(hi, open("research/hero/trex_long_hi/script.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
from agents import writer
print("scenes", len(SC), "EN words", sum(len(r[0].split()) for r in SC), "HI words", sum(len(r[1].split()) for r in SC))
print("hindi issues:", writer.hindi_script_issues(hi["scenes"]))
print("est EN minutes at 175 wpm:", round(sum(len(r[0].split()) for r in SC) / 175, 1))
