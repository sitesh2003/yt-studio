"""Agents 2 and 3 - Ideas, script, titles and description.

Learns from three places: what is trending (trends.json), what worked on
YOUR channel (learnings.json, written by the analytics agent), and what you
already made (history.json) so it never repeats a topic.
"""
import re

from .core import DATA, add_lesson, config, llm_json, log, read_json
from . import playbook


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
"Part 2" that answers the obvious next question. Scientifically TRUE, showable with real stock
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

Topics VIEWERS asked for in the comments (use one when it is true, showable and fits the channel):
{[r['topic'] for r in (read_json(DATA / 'viewer_requests.json', []) or [])][-15:] or 'none yet'}

{playbook.brief()}

PROVEN FORMATS (from a study of the biggest explainer Shorts, Nov 2026; a contrast video about two
fish hit 5 million views and 1,800 comments in two days). Use these shapes, never copy a title or idea:
- CONTRAST: "Why X has almost none of Y while Z is full of it" - two familiar things, one surprising
  difference, one clear scientific reason. The strongest format; aim for at least one per batch.
- HIDDEN PROCESS: "How X is really made / what happens to X before it reaches you".
- STAKES + NUMBER: a concrete, true number that sounds impossible (weight, price, speed, age).
- HIDDEN ENGINEERING: the clever design inside an everyday object or place people never notice
  (why a road has a groove, what the yellow box on a guardrail does, why a plane window is round).
  In the Nov 2026 study this was the fastest-growing format in our genre.
- HOW A MACHINE WORKS: what really happens inside something people use every day (a fridge, a lock,
  a microwave, an elevator), shown step by step.
- WHAT IF: a vivid, TRUE hypothetical worked out with real science ("What if humans had a
  hummingbird's heart rate"); the answer must follow from real numbers, never fantasy.
- HOW IT GETS YOU: what really happens, step by step, when something everyday acts on your body
  ("How a horsefly bite works"), told close up. Never gore, never fear for its own sake.
- EVERYDAY DEBATE: food, pets, kitchen and body habits people have opinions on (sushi, eggs, coffee,
  dogs, sleep), so viewers want to comment their own experience.
- BODY MYTH OR FEAR, SETTLED: a fear or myth people really have about their body or a danger
  (the rusty-nail tetanus myth, sucking out snake venom, bats and rabies, "you swallow spiders in your
  sleep"), settled with ONE surprising true number or mechanism. In the Nov 2026 study a channel grew
  to 65K subscribers in 4 weeks this way. Facts ONLY from established medicine (CDC, WHO, NIH level or
  peer-reviewed research); never personal treatment advice beyond "get medical help"; calm, never scary.
- TRUE SCIENCE STORY: a real, well-documented person or moment behind a discovery, told as a story
  with stakes (the doctor who drank bacteria to prove what causes ulcers; the man whose head was hit by
  a particle-accelerator beam). In the Nov 2026 study, story Shorts about real people reached 850K views
  in a day on a 7-video channel. Only events confirmed by reliable history; no gossip, rumours or
  private lives of living people.
- ANY OTHER SCIENCE (space, physics, chemistry, earth, history of science, technology): welcome, as
  long as it is true, surprising, and can be SHOWN (see below).
Proven outlier titles in this space (patterns only): {_outliers()}

Suggest {n} NEW topics. Every topic must be scientifically TRUE (settled science, the kind a
peer-reviewed paper or CDC/NASA/NIH page states), explainable in about a minute, and SHOWABLE: the
things named can be filmed (animals, food, nature, ocean, people, machines, roads, vehicles, buildings,
everyday objects, space from NASA footage), drawn as one clear object, or shown on a map. Avoid
topics that need diagrams of invisible things (electrons, sound waves, quantum, signals) as the
main picture. Prefer topics with a good chance of an open-access research paper behind them.
Return JSON: {{"topics": [{{"topic": "...", "why_it_will_work": "...", "pattern": "..."}}]}}"""
    out = llm_json(prompt)
    topics = out.get("topics", [])
    log("writer: topics -> " + " | ".join(t["topic"] for t in topics))
    return topics


def tidy_countdown(script):
    """"Pause and guess" is said ONCE, straight before "three, two, one" (the maple-syrup Short said
    it twice: once before the question and again before the count). Any extra "Pause and guess" and
    any extra countdown are removed from the spoken lines, whatever the writer produced."""
    import re
    pg = re.compile(r"\s*pause and guess[.…!,:]*\s*", re.I)
    count = re.compile(r"three[,.…]*\s*two[,.…]*\s*one[.…!]*", re.I)
    scenes = script.get("scenes", [])
    if script.get("countdown") is False:          # the no-countdown arm: no count, no "pause and guess"
        for k, sc in enumerate(scenes):
            t = re.sub(r"\s{2,}", " ", count.sub("", pg.sub(" ", sc.get("narration", "")))).strip()
            if t != sc.get("narration", ""):
                log(f"writer: removed a countdown from scene {k + 1} (no-countdown video)")
                sc["narration"] = t
        return script
    hits = [(k, m) for k, sc in enumerate(scenes) for m in count.finditer(sc.get("narration", ""))]
    keep_scene = hits[-1][0] if hits else None
    for k, sc in enumerate(scenes):
        text = sc.get("narration", "")
        if k == keep_scene:
            spans = list(count.finditer(text))
            last = spans[-1]
            before, after = text[:last.start()], text[last.end():]
            before = count.sub("", before)            # a second countdown earlier in the scene
            before = pg.sub(" ", before).rstrip()      # every "pause and guess" ...
            text = f"{before} Pause and guess... three, two, one.{after}".strip()   # ... once, here
        elif keep_scene is not None:
            text = count.sub("", pg.sub(" ", text))
        text = re.sub(r"\s{2,}", " ", text).strip()
        if text != sc.get("narration", ""):   # a removed phrase can leave a sentence starting small
            text = re.sub(r"(^|(?<!\.\.)[.?!]\s+)([a-z])", lambda m: m[1] + m[2].upper(), text)
            log(f"writer: tidied the countdown in scene {k + 1}")
        sc["narration"] = text
    return script


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


def _content_words(sentence):
    return {w for w in re.findall(r"[a-z']+", sentence.lower()) if len(w) > 3}


def lint(s, words):
    """Problems a reader would notice that the fact-checker does not look for."""
    issues = []
    scenes = s.get("scenes") or []
    text = " ".join(x.get("narration", "") for x in scenes)
    sents = [x for x in re.split(r"(?<=[.?!])\s+", text) if len(_content_words(x)) >= 3]
    for i, a in enumerate(sents):
        for b in sents[i + 1:]:
            A, B = _content_words(a), _content_words(b)
            if len(A & B) / max(1, min(len(A), len(B))) >= 0.7:
                issues.append(f"says the same thing twice: \"{a}\" / \"{b}\"")
    n = len(text.split())
    if n > words * 1.2:
        issues.append(f"{n} words, aim for about {words}: cut the weakest lines")
    pre = [x.get("narration", "") for x in scenes]
    k = next((i for i, x in enumerate(scenes) if x.get("predict") or x.get("turn") or "three, two, one" in x.get("narration", "").lower()), None)
    if k:
        after = " ".join(pre[k + 1:k + 2])
        leak = llm_json(f"""A science Short builds to a reveal. Lines BEFORE the "pause and guess" countdown:
{pre[:k + 1]}
The reveal line AFTER the countdown: "{after}"
Does any line before the countdown already give the same explanation as the reveal, in any words
(so a viewer who heard it learns nothing new after the countdown)? Naming the mechanism counts as giving
it away; a hint that leaves the viewer still guessing does not. Return JSON: {{"leaks": true or false, "line": "the leaking line or empty"}}""")
        if leak.get("leaks"):
            issues.append(f"gives the answer away before the countdown: \"{leak.get('line', '')}\" - keep it as a clue only")
    return issues[:5]


def countdown_arm(topic):
    """THE COUNTDOWN EXPERIMENT (approved 13 Nov 2026). None of the fastest-growing channels in our
    genre uses a countdown, so half the Shorts keep "Pause and guess... three, two, one" and half ask
    the same question plainly with no count (a "turn"). The topic decides the arm, so a remake keeps
    its arm. Once analyst.experiment() names a winner (data/experiments.json), every video uses it."""
    import hashlib
    win = ((read_json(DATA / "experiments.json", {}) or {}).get("countdown") or {}).get("winner")
    if win in ("countdown", "turn"):
        return win == "countdown"
    return int(hashlib.md5(topic.lower().strip().encode()).hexdigest(), 16) % 2 == 0


ARM = {
    True: {
        "giveaway": """- NEVER GIVE THE ANSWER AWAY BEFORE THE COUNTDOWN. The hook only asks or surprises; the middle gives
  clues; the actual answer is said for the first time right after "three, two, one".""",
        "middle": """- PAUSE AND PREDICT: around the middle, include ONE scene that sets up a prediction about what
  happens next and ends with exactly: "Pause and guess... three, two, one." Say "Pause and
  guess" only ONCE in the whole video, right before the count - never before the question as well. Mark that scene with
  "predict": true. The very next scene reveals the answer with a satisfying "here's why".
  (This is a different question from the closing enquiry.)""",
        "host": "runs the PAUSE AND PREDICT with the 3-2-1",
        "arc": """(3) PAUSE AND PREDICT with the
  3-2-1 countdown, first nudging which DIRECTION to think ("think about what the cold does to...");""",
    },
    False: {
        "giveaway": """- NEVER GIVE THE ANSWER AWAY BEFORE THE TURN. The hook only asks or surprises; the middle gives
  clues; the actual answer is said for the first time right after the turn question.""",
        "middle": """- THE TURN: around the middle, include ONE scene where the host asks, plainly and briefly, the
  question the whole video has been building to (e.g. "So what is the shell actually doing?"). NO
  countdown: never say "pause and guess", "guess", "three, two, one" or ask the viewer to stop the video.
  Mark that scene with "turn": true. The very next scene reveals the answer with a satisfying "here's why".
  (This is a different question from the closing enquiry.)""",
        "host": "asks the turn question in the middle",
        "arc": """(3) THE TURN: the plain question
  that everything so far has built to, first nudging which DIRECTION to think, with no countdown;""",
    },
}


def write_script(topic, recap=None, fix=None):
    c = config()
    cd = countdown_arm(topic)
    arm = ARM[cd]
    ch, fmt = c["channel"], c["format"]
    learn = read_json(DATA / "learnings.json", {}) or {}
    secs = playbook.target_seconds(fmt["target_seconds"])
    words = int(secs * 2.3)          # measured: Kokoro + the countdown pauses run ~2.3 words a second
    prompt = f"""Write a YouTube Short script for US viewers.
Channel: {ch['niche']}. Tone: {ch['voice_tone']}. American English spelling.
Topic: {topic}
What has worked on this channel: {learn.get('summary', 'no data yet')}
Mistakes this channel's checkers already caught (never repeat these): {[l['text'] for l in (read_json(DATA / 'lessons.json', []) or [])][-15:] or 'none yet'}
{playbook.brief()}

Rules:
- About {words} words of narration in total ({secs} seconds when spoken). Short is strong:
  the biggest science Shorts run about 40 seconds, and a Short people finish gets shown to more people.
- The first line is the hook and must land in under 2 seconds: a surprising claim, a question, or a
  pattern interrupt. No "Did you know", no "In this video", no greeting.
- Open a curiosity loop early and close it near the end, so people watch to the end.
{{giveaway_rule}}
- Never say the same thing twice, even in different words.
- Any contrast between two things ("X sticks while Y slides off") must be TRUE for BOTH sides. If one
  side is a myth, pick a different contrast or drop it.
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
{{middle_rule}}
{{recap_rule}}
- RETENTION: every 2-3 sentences, a small turn that keeps people watching ("But here's the weird
  part...", "And that's not even the strangest bit."). Never pad; each turn must lead to a new fact.
- COMMENTS: one moment that invites people to share their own experience (a habit, a food, a pet),
  without asking for comments directly until the closing question.
- TWO NARRATORS, a natural conversation between friends: the HOST is curious - opens with the
  hook, wonders aloud, reacts ("Wait, really?"), {{host_rule}}, and asks
  the closing "Ever thought why" question; the EXPLAINER answers warmly and clearly. Mark every scene
  "speaker": "host" or "explainer". Never have them introduce themselves or use names.
- LOOP: Shorts replay automatically, and a replay counts. Make the very last words of the closing
  question lead naturally back into the first line, so the video feels like one circle (e.g. the
  question ends on the same object the hook opens with). End right after the question - no outro.
- NO "subscribe", "like", "share" or "follow" anywhere in the narration. The content earns it.
- SOUND LIKE A CURIOUS HUMAN, not a fact list: talk to one person ("you"), use contractions, let real
  wonder show ("Here's what got me...", "Wait, it gets stranger."), react to the surprising bit,
  vary sentence length. Never robotic lists, never "Fact one, fact two".
- THE ENQUIRY ARC, always in this order: (1) hook; (2) explain; {{arc_rule}}
  (4) reveal the answer with the why; (5) close with the "Ever thought why/how" tinkering question
  that applies the idea to something new.
- Split into 8 to 11 scenes. For each scene give a stock-footage search query of 1-3 plain, concrete
  nouns that stock sites tag clips with, describing exactly what should be ON SCREEN while that line
  is spoken (for example "eye closeup", "tear drop", "elephant herd", "cumulus cloud"), plus 2
  alternative queries that would also show it. Avoid adjectives ("fluffy", "amazing") and abstract
  words ("secret", "hidden", "constantly") that stock sites can't film.
- MAPS: if a line is about WHERE something is on Earth, add "map": ["Country or continent name as
  written on a world map", ...] to that scene (e.g. "map": ["Japan"]); it is drawn from real map
  data. Only countries and continents, at most 2 map scenes, and only where the place truly matters.

Return JSON exactly in this shape:
{{
 "hook_options": ["...", "...", "..."],
 "scenes": [{{"speaker": "host or explainer", "narration": "...", "visual_query": "...", "alt_queries": ["...", "..."]}}],
 "title_options": ["4 to 8 words, max 60 characters, Title Case, NO hashtags, ending with exactly ONE face emoji that shows the feeling (one of: 🤔 😮 😨 😱 🤯 😳), like the biggest channel in the genre: one concrete object, place or moment and a curiosity gap that is TRUE (e.g. 'Why Plane Windows Are Never Square 🤔', 'How Horseflies Bite You 😨'); never the answer", "...", "..."],
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
 "series": "exactly one of: Food Whys, Ocean Whys, Animal Whys, Body Whys, Everyday Whys, How Things Work",
 "question": "the enquiry question exactly as spoken in the last scene",
 "answer_comment": "the answer, posted as the channel's first comment once the video is public: start with 'The answer:', explain it in 2-4 friendly sentences a 12-year-old can follow, connect it back to the video, end by inviting a follow-up question. No links.",
 "fact_check": ["each factual claim made, including the answer, so a human can verify it"]
}}
The first scene's narration must be hook_options[0]."""
    for k, v in (("{giveaway_rule}", arm["giveaway"]), ("{middle_rule}", arm["middle"]),
                 ("{host_rule}", arm["host"]), ("{arc_rule}", arm["arc"]),
                 ("{recap_rule}", _recap_rule(recap) + _fix_rule(fix))):
        prompt = prompt.replace(k, v)
    s = llm_json(prompt)
    issues = lint(s, words)
    if issues:
        log(f"writer: script lint - {' | '.join(issues)}; rewriting once")
        again = llm_json(f"""Rewrite this YouTube Short script to fix ONLY these problems, keeping every true fact,
the speakers, the scene count and the JSON shape exactly:
{issues}
Script: {s}
Return the whole script JSON.""")
        if again.get("scenes") and len(lint(again, words)) < len(issues):
            s = again
    s["topic"] = topic
    s["countdown"] = cd
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
    from . import library
    known = library.find(" ".join(w["title"] for w in week), n=10)
    verified = chr(10).join(f"- {e['title']}: claims {e.get('claims', [])[:5]}; sources {[s['cite'] for s in e.get('sources', [])]}"
                            for e in known) or "- (none yet)"
    s = llm_json(f"""Write a weekly long-form YouTube episode for the channel "Ever Thought Why?" ({ch['niche']}).
Audience: {ch['audience']}. Tone: {ch['voice_tone']}. American English.
This week's Shorts (go DEEPER on each, add the "how we know" and a real-world connection):
{items}

ALREADY VERIFIED by this channel (claims that passed our fact check, and open-access papers whose abstracts
support them). Build on these first; when a chapter uses one of these papers, name it in the narration as
"a study by <author> in <year>" so viewers know how we know:
{verified}

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
{{"topic": "weekly episode", "title_options": ["max 70 characters, Title Case, no emojis, concrete and true", "...", "..."],
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
    last_bad = []
    for r in range(rounds + 1):  # check, fix, ... and always re-check the final fix
        text = " ".join(sc["narration"] for sc in script["scenes"])
        check = llm_json(f"""You are a strict science fact-checker for a YouTube channel. Be sceptical.
Check every factual claim in this narration, the enquiry question, and the posted answer.
Flag anything false, exaggerated, outdated, a common myth, or stated with more certainty than the
evidence allows. Honest simplification for a general audience is FINE ("almost entirely empty",
rounded numbers with "about"): only flag it if a viewer would come away believing something wrong.
Check the TITLE and the first line (the hook) hardest: a hook or title that overstates ("makes it
worse" when it only fails to help, "always", "never", "100%") is WRONG, even if the rest is right.
Every fix must keep plain, spoken English: no long digit strings, no jargon. Also flag if the question does not have one clear correct answer, or if the answer
cannot be reasoned out from what the video showed.

Title: {(script.get('title_options') or [''])[0]}
Narration: {text}
Question: {script.get('question', '')}
Answer comment: {script.get('answer_comment', '')}

Return JSON: {{"verdict": "pass" or "fix",
 "claims": [{{"claim": "...", "status": "correct|wrong|doubtful", "note": "why, with the correct figure"}}],
 "fixes": ["exact change to make, quoting the sentence"]}}""")
        script["fact_check_result"] = check
        bad = [c for c in check.get("claims", []) if c.get("status") != "correct"]
        if not bad:  # every claim correct: remaining "fixes" are only style, not facts
            log(f"checker: passed ({len(check.get('claims', []))} claims verified)")
            return script
        last_bad = bad
        if r == rounds:
            break
        log(f"checker: {len(bad)} problem(s) found, rewriting (round {r + 1})")
        fixed = llm_json(f"""Apply these fact-check corrections to the YouTube Short script below. Change only what
is needed to make it correct; keep the hook strong, the length, scenes, structure and JSON shape the same.
Corrections: {check.get('fixes', [])}
Problems: {bad}
Script JSON: {script}
Return the corrected script as JSON in exactly the same shape.""")
        fixed["topic"] = script["topic"]
        script = fixed
    # last resort before giving up the topic: CUT whatever cannot be confirmed (a shorter true video
    # beats no video), then one final check
    bad = last_bad
    if bad:
        log("checker: removing the claims that could not be confirmed")
        cut = llm_json(f"""These claims in a YouTube Short script could not be confirmed: {bad}
Rewrite the script so it no longer makes them: replace each with something that is definitely true
and well established, or drop that sentence. If the title or hook relied on one, write a new true
hook and title. Keep the enquiry arc (hook, explain, pause-and-predict with 3-2-1, answer,
Ever-thought-why question), the JSON shape and roughly the length.
Script JSON: {script}
Return the corrected script as JSON in exactly the same shape.""")
        cut["topic"] = script["topic"]
        final = llm_json(f"""Strict science fact-check. Title: {(cut.get('title_options') or [''])[0]}
Narration: {" ".join(sc["narration"] for sc in cut.get("scenes", []))}
Question: {cut.get('question', '')}  Answer: {cut.get('answer_comment', '')}
Return JSON: {{"claims": [{{"claim": "...", "status": "correct|wrong|doubtful"}}]}}""")
        if cut.get("scenes") and final.get("claims") and all(c.get("status") == "correct" for c in final["claims"]):
            cut["fact_check_result"] = {"verdict": "pass", "claims": final.get("claims", []), "cut": True}
            log(f"checker: passed after cutting ({len(final.get('claims', []))} claims verified)")
            return cut
    for c in bad:
        add_lesson("unconfirmed", f"{c.get('claim', '')} -> {c.get('note', 'could not be confirmed')}")
    script.setdefault("fact_check_result", {})["unresolved"] = True
    log("checker: could not fully resolve; this topic is skipped")
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
