"""The student channel's writer (Why It Works, STUDIO_CHANNEL=wiw).

Same engine and the same checks as Ever Thought Why? (fact-check rounds, sources, listening check,
QA), but a different promise: ONE concept a student meets in physics, chemistry, biology, maths,
electronics or technology - or one new piece of open-access research - shown step by step, then WHY it
works in one line of school science, then a "try this" for the comments.

The script comes back in exactly the shape writer.write_script returns, so voice, visuals, editor, QA,
bank and publisher need no changes.
"""
import datetime as dt
import random

import requests

from . import playbook
from .core import DATA, config, llm_json, log, read_json

SUBJECTS = ["physics", "chemistry", "biology", "maths", "electronics", "technology", "earth and space"]

FORMATS = """FORMATS for this channel (one concept per video):
- WHY IT WORKS: a rule students memorise without the reason (why ice floats, why a negative times a
  negative is positive, why the sky is blue, why a transformer needs AC), then the reason, drawn.
- VISUAL PROOF: a maths or physics result shown so it is obvious (Pythagoras by rearranging squares,
  the area of a circle by unrolling it, why the angles of a triangle add to 180).
- HOW IT WORKS INSIDE: the working of a device or a body system, step by step (a diode, a battery,
  a solar cell, a neuron firing, how a vaccine trains the immune system, how GPS finds you).
- THE TRICK, HONESTLY: a viral maths or science trick, worked through once, then WHY it works - and
  if it only works for special numbers, say so clearly.
- NEW RESEARCH: one recent open-access paper (from the list below) explained at school level: what
  they found, how they know, why it matters. Never overstate it: "a new study suggests", not "proved".
- COMMON MISTAKE: a misconception students and textbooks often repeat (heavier things fall faster,
  the tongue taste map, electrons flow from + to -), settled with the reason.
"""


def _recent_papers(subject, n=6):
    """Recent open-access papers with abstracts, a candidate pool for NEW RESEARCH videos."""
    since = (dt.date.today() - dt.timedelta(days=75)).isoformat()
    try:
        r = requests.get("https://api.openalex.org/works", timeout=30,
                         headers={"User-Agent": "yt-studio-student/1.0"},
                         params={"search": subject, "per-page": n, "sort": "cited_by_count:desc",
                                 "filter": f"is_oa:true,has_abstract:true,type:article,is_retracted:false,"
                                           f"from_publication_date:{since}"})
        r.raise_for_status()
        return [f"{w.get('display_name')} ({w.get('publication_year')}, doi:{(w.get('doi') or '').replace('https://doi.org/', '')})"
                for w in r.json().get("results", []) if w.get("display_name")]
    except Exception as e:
        log(f"student: no recent papers for {subject} ({str(e)[:60]})")
        return []


def _syllabus(subjects, per=6):
    """Concepts from channels/wiw_concepts.json for today's subjects that the channel has not made yet."""
    import json
    from .core import ROOT
    from .variety import topic_is_repeat
    try:
        cmap = json.loads((ROOT / "channels" / "wiw_concepts.json").read_text(encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for sub in subjects:
        todo = [c for c in cmap.get(sub, []) if not topic_is_repeat(c)]
        random.shuffle(todo)
        out[sub] = todo[:per]
    return out


def pick_topics(n=3):
    cfg = config()["channel"]
    done = [h.get("topic") for h in (read_json(DATA / "history.json", []) or []) if h.get("topic")][-80:]
    day = dt.date.today().toordinal()
    subjects = [SUBJECTS[(day * n + k) % len(SUBJECTS)] for k in range(n)]   # rotate every subject
    papers = _recent_papers(random.choice(SUBJECTS))
    out = llm_json(f"""You plan YouTube Shorts for the channel "Why It Works": {cfg['niche']}.
Audience: {cfg['audience']}.
{playbook.brief()}
{FORMATS}
Recent open-access papers you MAY use for one NEW RESEARCH topic (only if it can be explained truly and
simply; otherwise ignore the list): {papers or 'none today'}
CONCEPTS STUDENTS STUDY that this channel has not covered yet, by subject (prefer one of these; phrase it
as the question a student would ask): {_syllabus(subjects)}
Topics already made (never repeat): {done or 'none'}
Topics viewers asked for: {[r['topic'] for r in (read_json(DATA / 'viewer_requests.json', []) or [])][-10:] or 'none yet'}

Suggest {n} NEW topics, one for each of these subjects in order: {subjects}.
Every topic must be scientifically TRUE (textbook or peer-reviewed), explainable in about 35 seconds,
and SHOWABLE with a diagram, a computed animation, or real footage. Prefer the concepts students meet
in school and early college, phrased as the question a student would actually ask.
Return JSON: {{"topics": [{{"topic": "...", "subject": "...", "format": "...", "why_it_will_work": "..."}}]}}""")
    topics = out.get("topics", [])
    log("student: topics -> " + " | ".join(t.get("topic", "") for t in topics))
    return topics


def write_script(topic, recap=None, fix=None):
    from .writer import _fix_rule, lint, verify
    c = config()
    ch, fmt = c["channel"], c["format"]
    secs = playbook.target_seconds(fmt["target_seconds"])
    words = int(secs * 2.4)
    lessons = [l["text"] for l in (read_json(DATA / "lessons.json", []) or [])][-15:]
    s = llm_json(f"""Write a YouTube Short script for the channel "Why It Works".
Channel: {ch['niche']}. Audience: {ch['audience']}. Tone: {ch['voice_tone']}. American English spelling.
Topic: {topic}
Mistakes this channel's checkers already caught (never repeat): {lessons or 'none yet'}
{playbook.brief()}
{_fix_rule(fix)}
Rules:
- About {words} words in total ({secs} seconds spoken). One concept only.
- THE ARC, always in this order:
  (1) HOOK in under 2 seconds: the question a student actually asks, or the surprising fact
      ("Ice is a solid. So why doesn't it sink?"). No greeting, no "Did you know", no "In this video".
  (2) SHOW IT step by step: what happens, one step per scene, each step something that can be DRAWN.
  (3) WHY IT WORKS: the reason in one plain sentence of school-level science, said clearly and slowly.
      Mark that scene "why": true.
  (4) WHERE YOU SEE IT: one real-world use or, for research, how they know and why it matters.
  (5) TRY THIS: a short question the viewer can work out from the video, for the comments, starting
      with "Try this:" (e.g. "Try this: why does a lake freeze from the top down?"). It must have one
      clear answer.
- 100% correct. Simplify honestly ("roughly", "in most cases"); never state a myth or an overclaim.
  If a trick only works for special cases, SAY so.
- Numbers easy to say; any number you use must be exactly right.
- One idea per sentence. Short words. Talk to one student ("you"), warm and clear, like the best
  teacher they ever had. Contractions are fine. No "subscribe", "like", "share" or "follow".
- TWO NARRATORS: the HOST asks the hook and the Try-this question and reacts like a curious student;
  the EXPLAINER shows and explains. Mark every scene "speaker": "host" or "explainer".
- 7 to 10 scenes. For each scene: "visual_query" = 1-3 plain concrete nouns for real footage of what is
  on screen, plus 2 "alt_queries". Most scenes here will be DRAWN as diagrams or animations from the
  narration, so make each line say exactly what should be drawn (the objects, the numbers, the arrows).

Return JSON exactly in this shape:
{{
 "hook_options": ["...", "...", "..."],
 "scenes": [{{"speaker": "host or explainer", "narration": "...", "visual_query": "...", "alt_queries": ["...", "..."]}}],
 "title_options": ["4 to 8 words, max 60 characters, Title Case, NO hashtags, the student's question or the surprising fact, ending with ONE emoji (🤔 😮 🤯 💡 ⚡ 🧪); true, never the answer", "...", "..."],
 "description": "2-3 lines: the question, a tease of the reason, then 3 hashtags including #shorts and the subject (e.g. #physics)",
 "tags": ["...", "..."],
 "thumbnail": {{"layout": "single", "scene": 0, "text": "max 4 words", "highlight": "one word"}},
 "thumbnail_text": "max 4 words",
 "series": "exactly one of: Physics, Chemistry, Biology, Maths, Electronics, Technology, Earth and Space, New Research",
 "question": "the Try-this question exactly as spoken",
 "answer_comment": "Start with 'The answer:', explain in 2-4 sentences a 14-year-old can follow, link it back to the video, invite a follow-up question. No links.",
 "fact_check": ["each factual claim, including the answer to Try this"]
}}
The first scene's narration must be hook_options[0].""")
    issues = [i for i in lint(s, words) if "countdown" not in i]
    if issues:
        log(f"student: script lint - {' | '.join(issues)}; rewriting once")
        again = llm_json(f"""Rewrite this YouTube Short script to fix ONLY these problems, keeping every true fact,
the speakers, the scene count and the JSON shape exactly:
{issues}
Script: {s}
Return the whole script JSON.""")
        if again.get("scenes"):
            s = again
    s["topic"] = topic
    s["countdown"] = False
    log(f"student: script ready, {sum(len(x['narration'].split()) for x in s.get('scenes', []))} words, "
        f"title {(s.get('title_options') or [''])[0]!r}")
    return verify(s)


def is_student():
    return config()["channel"].get("style") == "student"

