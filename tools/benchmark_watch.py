"""Benchmark: Gemini watches each Short (picture AND sound, straight from the public YouTube URL)
and describes how it is made, so ours can be compared with what gets views (owner, 19 Nov 2026).
Then it listens to our own voices (E2 male, H14 Hindi) against the benchmark voices.

    python tools/benchmark_watch.py            -> research/benchmark/watch.json
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
import os  # noqa: E402

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

OUT = ROOT / "research/benchmark/watch.json"
MODELS = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash"]
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

ASK = """You are studying this YouTube Short to learn how it is made. Watch AND listen to all of it.
Return JSON only:
{
 "first_3_seconds": "exactly what is seen and heard in the first 3 seconds",
 "hook_line": "the first spoken or on-screen sentence, word for word",
 "spoken_language": "e.g. English, Hindi, Hinglish, none",
 "voice": {"kind": "human / AI text-to-speech / none", "gender": "", "accent": "",
           "pace_words_per_minute": 0, "energy": "flat / calm / lively / very energetic",
           "pauses": "how it uses pauses", "sounds_natural_1_to_10": 0, "why": ""},
 "music_and_sfx": "background music? sound effects? when?",
 "visual_technique": "one of: real filmed footage of a person / real stock or process footage / 3D animation / 2D vector animation / stick-figure line animation / AI-generated video / slides or photos with zoom / screen recording / mixed - then one sentence",
 "visual_detail": "how the frame is laid out (full screen? clip in a band with blur?), how often the shot changes (cuts per 10 seconds), does each picture show exactly what is said",
 "captions": "style of on-screen text (one big word? full sentences? colours?)",
 "structure": "the beats in order, e.g. hook -> twist -> explanation -> payoff",
 "ending": "how it ends; does it loop back to the start; any question or call to action",
 "why_it_works_or_not": "2-3 sentences, honest",
 "how_a_free_automated_pipeline_could_match_it": "concrete: which free tools/footage/libraries, or 'cannot without filming/hand animation'"
}"""

TARGETS = [
    # the owner's EVER THOUGHT WHY playlist (17), in playlist order
    "WsQnYHIOf-8", "hCl3J0OrQMg", "Z0MKLywH-5g", "jsuoM4dLJ5w", "ItDNA4yv2Ng", "_vcLT_kLGUk", "0KiTqL88xdU",
    "O43PygGEPGY", "ZmBBdQ2tPPU", "uU3NOi-MysE", "kmjELcMJh04", "inz4ouQ6C5k", "xd0kO2JcwU0", "vciCGuAMoa0",
    "Yy6k06pKvxw", "WUMsLAcGpUs", "jNRd1gVaCzk",
    # ours, for comparison: two of the best and one of the weakest
    "Bxp7r8IzbiY", "80jyJN1A1y8", "syvvVya0Q4g",
]


def ask(parts):
    last = None
    for _ in range(3):
        for m in MODELS:
            try:
                r = client.models.generate_content(model=m, contents=types.Content(parts=parts),
                                                   config=types.GenerateContentConfig(response_mime_type="application/json"))
                return json.loads(r.text), m
            except Exception as e:  # busy / quota: next model
                last = e
                time.sleep(8)
    raise RuntimeError(str(last)[:200])


def main():
    done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for vid in TARGETS:
        if vid in done and "error" not in done[vid]:
            continue
        try:
            res, m = ask([types.Part(file_data=types.FileData(file_uri=f"https://www.youtube.com/watch?v={vid}")),
                          types.Part(text=ASK)])
            res["_model"] = m
            done[vid] = res
            print("ok", vid, (res.get("visual_technique") or "")[:60], flush=True)
        except Exception as e:
            done[vid] = {"error": str(e)[:200]}
            print("FAIL", vid, str(e)[:120], flush=True)
        OUT.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")

    # our voices against the benchmark voices
    vl = ROOT / "research/voice_lab"
    for key, f, note in [("_ours_E2_male", "chatterbox_lively_tuned.mp3", "our English male voice"),
                         ("_ours_H14_hindi", "opt_H14.mp3", "our Hindi voice (Hinglish script)")]:
        if key in done and "error" not in done[key]:
            continue
        try:
            res, m = ask([types.Part(inline_data=types.Blob(mime_type="audio/mpeg", data=(vl / f).read_bytes())),
                          types.Part(text=f"""This is {note} for a science YouTube Shorts channel. Listen closely.
Return JSON only: {{"kind": "human or AI", "gender": "", "accent": "", "pace_words_per_minute": 0,
"energy": "flat / calm / lively / very energetic", "sounds_natural_1_to_10": 0,
"problems": ["every audible problem: robotic words, wrong stress, mumbling, odd pauses, mispronounced words, Hindi words read badly ..."],
"compared_to_top_shorts_narrators": "honest comparison with narrators of viral Shorts",
"what_to_change": ["concrete settings or script changes"]}}"""),
                          ])
            res["_model"] = m
            done[key] = res
            print("ok", key, flush=True)
        except Exception as e:
            done[key] = {"error": str(e)[:200]}
            print("FAIL", key, str(e)[:120], flush=True)
        OUT.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
