"""Agents 2 and 3 - Ideas, script, titles and description.

Learns from three places: what is trending (trends.json), what worked on
YOUR channel (learnings.json, written by the analytics agent), and what you
already made (history.json) so it never repeats a topic.
"""
from .core import DATA, config, llm_json, log, read_json


def _context():
    trends = (read_json(DATA / "trends.json", {}) or {}).get("videos", [])[:25]
    learn = read_json(DATA / "learnings.json", {}) or {}
    history = read_json(DATA / "history.json", []) or []
    return trends, learn, [h["topic"] for h in history][-60:]


def _outliers():
    """Top titles from channels we studied (research/*.json), as format examples only."""
    import glob
    import json as _j
    rows = []
    for f in glob.glob(str(DATA.parent / "research" / "*.json")):
        try:
            rows += _j.load(open(f, encoding="utf-8")).get("videos", [])
        except Exception:
            pass
    rows.sort(key=lambda r: r.get("views", 0), reverse=True)
    return "; ".join(f'"{r["title"]}" ({r["views"] // 1000}k views)' for r in rows[:8]) or "none"


def sequel_topic(title, topic):
    """A follow-up to a video that took off: same hook shape, new true subject (or a deeper Part 2)."""
    out = llm_json(f"""A YouTube Short of ours did about three times better than our average.
Title: "{title}"  Topic: "{topic}"
Suggest ONE follow-up topic that keeps what made it work (the same format: contrast, hidden process,
stakes, or debate) on a closely related subject viewers will also wonder about - or a genuine
"Part 2" that answers the obvious next question. Scientifically TRUE, filmable with real stock
footage, never a repeat. Return JSON: {{"topic": "...", "why": "..."}}""")
    log(f"writer: sequel to {title!r} -> {out.get('topic')}")
    return out


def pick_topics(n=3):
    cfg = config()["channel"]
    trends, learn, done = _context()
    prompt = f"""You plan YouTube Shorts for a channel about: {cfg['niche']}.
Audience: {cfg['audience']}.

Top performing Shorts in this niche for US viewers in the last 30 days (title, views per day):
{chr(10).join(f"- {t['title']} ({t['views_per_day']}/day)" for t in trends) or "- (no trend data)"}

What has worked on THIS channel so far: {learn.get('summary', 'no data yet')}

Topics already made (never repeat these): {done or 'none'}

PROVEN FORMATS (from a study of the biggest explainer Shorts, Nov 2026; a contrast video about two
fish hit 5 million views and 1,800 comments in two days). Use these shapes, never copy a title or idea:
- CONTRAST: "Why X has almost none of Y while Z is full of it" - two familiar things, one surprising
  difference, one clear scientific reason. The strongest format; aim for at least one per batch.
- HIDDEN PROCESS: "How X is really made / what happens to X before it reaches you".
- STAKES + NUMBER: a concrete, true number that sounds impossible (weight, price, speed, age).
- EVERYDAY DEBATE: food, pets, kitchen and body habits people have opinions on (sushi, eggs, coffee,
  dogs, sleep), so viewers want to comment their own experience. Never health advice, never fear.
Proven outlier titles in this space (patterns only): {_outliers()}

Suggest {n} NEW topics. Every topic must be scientifically TRUE, explainable in about a minute, and
FILMABLE WITH REAL STOCK FOOTAGE: the things named must be easy to film (animals, food, cooking,
nature, ocean, people doing everyday things). Avoid topics that would need diagrams of invisible
things (electrons, sound waves, quantum, signals) - those cannot get matching footage.
Return JSON: {{"topics": [{{"topic": "...", "why_it_will_work": "...", "pattern": "..."}}]}}"""
    out = llm_json(prompt)
    topics = out.get("topics", [])
    log("writer: topics -> " + " | ".join(t["topic"] for t in topics))
    return topics


def _fix_rule(fix):
    if not fix:
        return ""
    return f"""- THIS IS A CORRECTED REMAKE. An earlier version of this video was pulled before going public
  because it said: "{fix.get('false_sentence', '')}"
  That is wrong: {fix.get('why', '')}
  What is actually true: {fix.get('correct_version', '')}
  Build the new script around the TRUE version. Never repeat the wrong claim, not even as the hook;
  a hook that exaggerates is what caused this. The truth is surprising enough on its own.
"""


def write_script(topic, recap=None, fix=None):
    c = config()
    ch, fmt = c["channel"], c["format"]
    learn = read_json(DATA / "learnings.json", {}) or {}
    words = int(fmt["target_seconds"] * 2.6)
    prompt = f"""Write a YouTube Short script for US viewers.
Channel: {ch['niche']}. Tone: {ch['voice_tone']}. American English spelling.
Topic: {topic}
What has worked on this channel: {learn.get('summary', 'no data yet')}

Rules:
- About {words} words of narration in total ({fmt['target_seconds']} seconds when spoken).
- The first line is the hook and must land in under 2 seconds: a surprising claim, a question, or a
  pattern interrupt. No "Did you know", no "In this video", no greeting.
- Open a curiosity loop early and close it near the end, so people watch to the end.
- One idea per sentence. Short words. Cut every word that does not earn its place.
- 100% factually correct. If a number is uncertain, round it and say "about". Never state a myth,
  an exaggeration or a disputed claim as fact.
- Numbers must be easy to SAY: never write long decimals or strings of digits (no "99.9999999%").
  Use plain comparisons instead ("almost entirely empty", "a marble in a stadium", "about 100 elephants").
- END WITH AN ENQUIRY QUESTION (the last scene), in the style of a hands-on science centre:
  a small thinking mission the viewer can reason out using ONLY what the video just showed them,
  plus everyday experience. It should make them tinker in their head (or at home, safely), predict,
  or apply the idea to something new. Warm and curious, never a quiz or a test, no trick questions,
  no prior knowledge needed. The channel is called "Ever Thought Why?", so this closing question
  ALWAYS starts with "Ever thought why" or "Ever thought how" (the channel's signature). Example:
  "Ever thought why a cloud that heavy doesn't just fall out of the sky? Drop your guess below."
  The question must have ONE clear, correct answer that a curious 12-year-old can work out from what
  the video showed plus everyday experience. Never ask something whose answer needs advanced theory
  (no quantum mechanics, no equations) that the video did not explain.
- PAUSE AND PREDICT: around the middle, include ONE scene that sets up a prediction about what
  happens next and ends with exactly: "Pause and guess... three, two, one." Mark that scene with
  "predict": true. The very next scene reveals the answer with a satisfying "here's why".
  (This is a different question from the closing enquiry.)
{{recap_rule}}
- RETENTION: every 2-3 sentences, a small turn that keeps people watching ("But here's the weird
  part...", "And that's not even the strangest bit."). Never pad; each turn must lead to a new fact.
- COMMENTS: one moment that invites people to share their own experience (a habit, a food, a pet),
  without asking for comments directly until the closing question.
- NO "subscribe", "like", "share" or "follow" anywhere in the narration. The content earns it.
- SOUND LIKE A CURIOUS HUMAN, not a fact list: talk to one person ("you"), use contractions, let real
  wonder show ("Here's what got me...", "Wait, it gets stranger."), react to the surprising bit,
  vary sentence length. Never robotic lists, never "Fact one, fact two".
- THE ENQUIRY ARC, always in this order: (1) hook; (2) explain; (3) PAUSE AND PREDICT with the
  3-2-1 countdown, first nudging which DIRECTION to think ("think about what the cold does to...");
  (4) reveal the answer with the why; (5) close with the "Ever thought why/how" tinkering question
  that applies the idea to something new.
- Split into 8 to 11 scenes. For each scene give a stock-footage search query of 1-3 plain, concrete
  nouns that stock sites tag clips with, describing exactly what should be ON SCREEN while that line
  is spoken (for example "eye closeup", "tear drop", "elephant herd", "cumulus cloud"), plus 2
  alternative queries that would also show it. Avoid adjectives ("fluffy", "amazing") and abstract
  words ("secret", "hidden", "constantly") that stock sites can't film.

Return JSON exactly in this shape:
{{
 "hook_options": ["...", "...", "..."],
 "scenes": [{{"narration": "...", "visual_query": "...", "alt_queries": ["...", "..."]}}],
 "title_options": ["max 70 characters, true, a curiosity gap that names BOTH sides for a contrast or a concrete number for stakes, Title Case, ending with exactly 2 emojis that fit the subject (e.g. fish+shocked)", "...", "..."],
 "description": "2-3 lines for US viewers that tease the answer without giving it, then 3 relevant hashtags including #shorts",
 "tags": ["...", "..."],
 "thumbnail": {{
   "layout": "split if the fact is a comparison (X = Y, X vs Y, before/after), otherwise single",
   "top_scene": 0, "bottom_scene": 3,
   "top_text": "split only: 1-3 words, e.g. 1 CLOUD",
   "bottom_text": "split only: 1-3 words, e.g. 100 ELEPHANTS",
   "connector": "split only: = or VS or ->",
   "scene": 0,
   "text": "single only: max 4 punchy words, a curiosity gap, never the full answer",
   "highlight": "the one word or number to colour yellow"
 }},
 "thumbnail_text": "max 4 words",
 "series": "exactly one of: Food Whys, Ocean Whys, Animal Whys, Body Whys, Everyday Whys",
 "question": "the enquiry question exactly as spoken in the last scene",
 "answer_comment": "the answer, posted as the channel's first comment once the video is public: start with 'The answer:', explain it in 2-4 friendly sentences a 12-year-old can follow, connect it back to the video, end by inviting a follow-up question. No links.",
 "fact_check": ["each factual claim made, including the answer, so a human can verify it"]
}}
The first scene's narration must be hook_options[0]."""
    s = llm_json(prompt.replace("{recap_rule}", _recap_rule(recap) + _fix_rule(fix)))
    s["topic"] = topic
    if recap:
        s["recap_source"] = recap.get("video_id")
    log(f"writer: script ready, {sum(len(x['narration'].split()) for x in s['scenes'])} words, title {s['title_options'][0]!r}")
    return verify(s)


def _recap_rule(recap):
    if not recap:
        return ""
    names = recap.get("winners") or []
    shout = (f"then give a warm shout-out by name to {' and '.join(names)} who got it right"
             if names else "then say nobody cracked it yet, so today's is their chance")
    return f"""- YESTERDAY'S ANSWER: just before the closing question, add ONE short scene (max 25 words)
  that answers yesterday's question: "{recap['question']}". The correct answer is: "{recap['answer']}".
  Say the answer in one plain sentence, {shout}. Mark that scene with "recap": true.
  Never put this at the start: the first 2 seconds are always today's hook."""


def judge_guesses(question, answer, comments):
    """Which commenters got yesterday's enquiry right? Only first names/handles that are
    appropriate to say out loud on a family-friendly channel."""
    if not comments:
        return []
    out = llm_json(f"""A science Short asked viewers: "{question}"
The correct answer: "{answer}"
Here are viewer comments (author, text). Mark a comment correct only if it contains the key idea of
the answer, even in simple words. Then return up to 2 author names to thank on screen, best answers
first. Skip any name that is offensive, sexual, political, a brand promotion, contains a URL, or
looks like spam. Skip anyone whose comment is rude.
Comments: {comments}
Return JSON: {{"winners": ["name", "..."], "correct_count": 0}}""")
    return [w.lstrip("@").strip()[:30] for w in out.get("winners", []) if w and w.strip()][:2]


def write_weekly(week):
    """Weekly long-form episode (8-10 minutes, widescreen) that goes deeper on the week's Shorts."""
    ch = config()["channel"]
    items = chr(10).join(f"- {w['title']} | question: {w.get('question','')} | answer: {w.get('answer_comment','')}"
                      for w in week)
    s = llm_json(f"""Write a weekly long-form YouTube episode for the channel "Ever Thought Why?" ({ch['niche']}).
Audience: {ch['audience']}. Tone: {ch['voice_tone']}. American English.
This week's Shorts (go DEEPER on each, add the "how we know" and a real-world connection):
{items}

Rules:
- 1300 to 1500 words of narration (8 to 10 minutes). Strong 10-second cold open with the most
  surprising idea of the week, then a one-line promise of what they will understand by the end.
- One chapter per topic. Inside each chapter: the mystery, a "pause and predict" moment ending with
  "Pause and guess... three, two, one." (mark that scene "predict": true), the reveal, why it works,
  how scientists found out, and where you meet it in everyday life.
- 100% accurate, plain spoken numbers, honest simplification only. No jargon without explaining it.
- End with a fresh "Ever thought why...?" question for the comments and a one-line tease of next week.
- Scenes of 2-4 sentences, each with a concrete 1-3 word stock-footage query and 2 alternatives.

Return JSON:
{{"topic": "weekly episode", "title_options": ["max 70 characters", "...", "..."],
 "hook_options": ["the cold open line"],
 "scenes": [{{"narration": "...", "visual_query": "...", "alt_queries": ["...", "..."], "chapter": "chapter title or empty"}}],
 "description": "3-4 lines, then a blank line (chapter timestamps are added automatically), then hashtags",
 "tags": ["..."],
 "thumbnail": {{"layout": "single", "text": "max 4 words", "highlight": "one word"}},
 "question": "the closing Ever thought why question",
 "answer_comment": "The answer: 2-4 friendly sentences",
 "fact_check": ["every factual claim"]}}""")
    s["topic"] = "weekly: " + ", ".join(w["title"] for w in week)[:120]
    log(f"writer: weekly episode, {sum(len(x['narration'].split()) for x in s['scenes'])} words")
    return verify(s)


def verify(script, rounds=2):
    """Fact-checker agent: a second, sceptical pass over every claim and the answer.
    If anything is wrong or doubtful it sends exact fixes back and the script is corrected."""
    for r in range(rounds):
        text = " ".join(sc["narration"] for sc in script["scenes"])
        check = llm_json(f"""You are a strict science fact-checker for a YouTube channel. Be sceptical.
Check every factual claim in this narration, the enquiry question, and the posted answer.
Flag anything false, exaggerated, outdated, a common myth, or stated with more certainty than the
evidence allows. Honest simplification for a general audience is FINE ("almost entirely empty",
rounded numbers with "about"): only flag it if a viewer would come away believing something wrong.
Every fix must keep plain, spoken English: no long digit strings, no jargon. Also flag if the question does not have one clear correct answer, or if the answer
cannot be reasoned out from what the video showed.

Narration: {text}
Question: {script.get('question', '')}
Answer comment: {script.get('answer_comment', '')}

Return JSON: {{"verdict": "pass" or "fix",
 "claims": [{{"claim": "...", "status": "correct|wrong|doubtful", "note": "why, with the correct figure"}}],
 "fixes": ["exact change to make, quoting the sentence"]}}""")
        script["fact_check_result"] = check
        bad = [c for c in check.get("claims", []) if c.get("status") != "correct"]
        if not bad and (check.get("verdict") == "pass" or not check.get("fixes")):
            log(f"checker: passed ({len(check.get('claims', []))} claims verified)")
            return script
        log(f"checker: {len(bad)} problem(s) found, rewriting (round {r + 1})")
        fixed = llm_json(f"""Apply these fact-check corrections to the YouTube Short script below. Change only what
is needed to make it correct; keep the hook strong, the length, scenes, structure and JSON shape the same.
Corrections: {check.get('fixes', [])}
Problems: {bad}
Script JSON: {script}
Return the corrected script as JSON in exactly the same shape.""")
        fixed["topic"] = script["topic"]
        script = fixed
    script.setdefault("fact_check_result", {})["unresolved"] = True
    log("checker: could not fully resolve, flagged for your review")
    return script


def draft_replies(comments):
    """Agent 5 helper: classify comments and draft replies in the channel's voice."""
    ch = config()["channel"]
    prompt = f"""You manage comments for a YouTube channel about {ch['niche']}. Tone: {ch['voice_tone']}.
For each comment decide: "reply" (genuine question or kind comment), "skip" (low value), or "spam".
Replies: max 2 sentences, warm, specific to what they said, factually correct, no links, no emojis spam,
never argue, never promise anything. If a question needs a long answer, say it could be a future Short.
Comments: {comments}
Return JSON: {{"items": [{{"id": "...", "action": "reply|skip|spam", "reply": "..."}}]}}"""
    return llm_json(prompt).get("items", [])
