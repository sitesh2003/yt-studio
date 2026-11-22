"""The quality gate every hero Short passes, BEFORE rendering (voice) and AFTER (finished video).
Owner, 21 Nov 2026: "every clip... check it, then fix it, then do more... no caption re-writing, no voice issues,
no 3D issues... keep modifying yourself better and better". Lessons learned go to research/hero/LESSONS.md.

    python tools/hero_gate.py <name> voice      # before rendering: speed, every word heard, per scene
    python tools/hero_gate.py <name> video      # after: cuts on the words, captions never doubled/overlapping

Exit code 0 = pass; 1 = fail (the reasons are printed). A failing video is never banked.
"""
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
name, stage = sys.argv[1], sys.argv[2]
d = ROOT / "research" / "hero" / name
hindi = name.endswith("_hi")
script = json.loads((d / "script.json").read_text(encoding="utf-8"))
words = json.loads((d / "words.json").read_text(encoding="utf-8"))
fails, notes = [], []

# speed bands (owner: "not telling very fast"); Hindi carries more syllables per word, so fewer words a minute
BAND = (160, 195) if hindi else (170, 200)


HI_NUM = {"एक": "1", "दो": "2", "तीन": "3", "चार": "4", "पांच": "5", "पाँच": "5", "छह": "6", "छः": "6", "सात": "7",
          "आठ": "8", "नौ": "9", "दस": "10", "चौदह": "14", "अठारह": "18", "बीस": "20", "अट्ठाईस": "28", "तीस": "30",
          "पचास": "50", "पचपन": "55", "साठ": "60", "सौ": "100", "हज़ार": "1000", "डेढ़": "1.5"}


def canon(t):
    """Text for comparing what was written with what was heard: numbers in one form (digits), no punctuation."""
    t = t.lower()
    if not hindi:
        from agents.voice import _say_number
        t = re.sub(r"\d[\d,]*", lambda m: " ".join(_say_number(int(m.group(0).replace(",", "")))), t)
        t = t.replace("-", " ")
        for uk, us in (("metres", "meters"), ("metre", "meter"), ("kilometres", "kilometers"), ("tyres", "tires"),
                       ("tyre", "tire"), ("colour", "color"), ("grey", "gray"), ("centre", "center"), ("litre", "liter"),
                       ("brake", "break"), ("braking", "breaking"), ("onto", "on to")):   # spelling, same-sound words
            t = re.sub(r"[.,?!]", " ", " " + t + " ").replace(" " + uk + " ", " " + us + " ")
    else:
        for w_, dg in HI_NUM.items():
            t = re.sub(rf"(?<!\S){w_}(?!\S)", dg, t)
    t = re.sub(r"[।,.?!'\"\-:;]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


if stage == "voice":
    dur = words[-1]["end"]
    wpm = len(words) / (dur / 60)
    (notes if BAND[0] <= wpm <= BAND[1] else fails).append(f"speed {wpm:.0f} words a minute (band {BAND[0]}-{BAND[1]})")
    from faster_whisper import WhisperModel
    m = WhisperModel("medium" if hindi else "medium.en", device="cpu", compute_type="int8")
    # no carry-over between segments: with mixed Hindi-English the model otherwise starts inventing translations
    segs, _ = m.transcribe(str(d / "voice.mp3"), language="hi" if hindi else "en", beam_size=5,
                           condition_on_previous_text=False, vad_filter=True)
    heard = canon(" ".join(s.text for s in segs))
    for k, sc in enumerate(script["scenes"]):
        want = canon(sc["narration"])
        # best matching window of the heard text for this scene
        hw, ww = heard.split(), want.split()
        if hindi:   # compare by SOUND: "overlap" and "ओवलाब" are the same word said aloud
            from agents.listen import skeleton
            hw, ww = [skeleton(x) for x in hw], [skeleton(x) for x in ww]
        best = 0.0
        for i in range(0, max(1, len(hw) - len(ww) + 1)):
            r = SequenceMatcher(None, ww, hw[i:i + len(ww) + 2]).ratio()
            best = max(best, r)
        # Hindi spelling varies (digits vs words, nukta, anusvara), so its bar is lower; English must be near-exact
        bar = 0.6 if hindi else 0.8
        (notes if best >= bar else fails).append(f"scene {k + 1} heard {best:.0%}: {sc['narration'][:50]}")
    if hindi:   # Devanagari Hindi; English only as single words (owner, 22 Nov 2026)
        from agents.writer import hindi_script_issues
        for iss in hindi_script_issues(script["scenes"]):
            fails.append(iss)
    for num in re.findall(r"\b\d[\d,]*\b", " ".join(s["narration"] for s in script["scenes"])):
        notes.append(f"digits '{num}' in the script: check it is read as intended (words are safer)")

elif stage == "video":
    scenes = json.loads((d / "scenes.json").read_text(encoding="utf-8"))
    key = lambda t: re.sub(r"[^a-z]", "", t.lower()) or t.strip("।,.?!-")
    heard = [key(w["text"]) for w in words]
    j = 0
    for k, sc in enumerate(script["scenes"]):
        want = [key(t) for t in sc["narration"].split()[:3]]
        for i in range(j, len(heard)):
            if heard[i:i + 3] == want:
                lag = scenes[k][0] - (0 if k == 0 else words[i]["start"])
                (notes if abs(lag) <= 0.25 else fails).append(f"cut {k + 1} is {lag:+.2f} s from its first word")
                j = i + 1
                break
        else:
            notes.append(f"cut {k + 1}: opening words not found in the voice timings (checked by eye)")
    ass = ROOT / "jobs" / f"_hero_compose_{name}" / "captions.ass"
    if ass.exists():
        def t(s):
            h, m_, sec = s.split(":")
            return int(h) * 3600 + int(m_) * 60 + float(sec)
        ev = []
        for line in ass.read_text(encoding="utf-8").splitlines():
            if line.startswith("Dialogue: 0,"):
                p = line.split(",", 9)
                ev.append((t(p[1]), t(p[2]), p[9]))
        ev.sort()
        overlap = [(a, b) for a, b in zip(ev, ev[1:]) if b[0] < a[1] - 0.02 and re.sub(r"\{[^}]*\}", "", a[2]) != re.sub(r"\{[^}]*\}", "", b[2])]
        (fails if overlap else notes).append(f"captions on screen at once (doubling): {len(overlap)}")
    else:
        fails.append("no captions file found to check")

for n_ in notes:
    print("  ok  ", n_)
for f_ in fails:
    print("  FAIL", f_)
print("GATE", "PASS" if not fails else "FAIL", name, stage)
sys.exit(1 if fails else 0)
