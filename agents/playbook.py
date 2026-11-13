"""Agent 7 - The playbook: the channel teaches itself from the whole niche, not only from itself.

Once a week it studies what the biggest English science / curiosity Shorts of the last 30 days have
in common (trends.json, refreshed every day) next to this channel's own numbers (performance.json),
and writes data/playbook.json: the formats, hook and title shapes that are winning NOW, the length
to aim for, and what to stop doing. The writer reads it before every topic list and every script,
so the channel keeps adapting as the market moves - with no person in the loop.

Hard limits the playbook can never change: accuracy first, illustrations or real footage only, no
subscribe/like asks, no copying of anyone's title or idea, US English.
"""
import datetime as dt
import re
import statistics as st

from .core import DATA, llm_json, log, read_json, write_json

PATH = DATA / "playbook.json"
MIN_S, MAX_S = 30, 50          # the length the playbook may choose, in seconds


def _english(title):
    letters = [c for c in title if c.isalpha()]
    return letters and sum(c.isascii() for c in letters) / len(letters) > 0.9


def current():
    return read_json(PATH, {}) or {}


def target_seconds(default):
    t = current().get("target_seconds")
    return max(MIN_S, min(MAX_S, int(t))) if isinstance(t, (int, float)) else default


def study(force=False):
    old = current()
    if not force and old.get("studied"):
        age = dt.datetime.now() - dt.datetime.fromisoformat(old["studied"])
        if age < dt.timedelta(days=6):
            log(f"playbook: studied {age.days} day(s) ago, next study in {6 - age.days} day(s)")
            return old
    rows = [r for r in (read_json(DATA / "trends.json", {}) or {}).get("videos", []) if _english(r["title"])]
    if len(rows) < 20:
        log(f"playbook: only {len(rows)} English trend videos, need 20+; keeping the current playbook")
        return old
    rows.sort(key=lambda r: r["views_per_day"], reverse=True)
    top, rest = rows[:20], rows[20:]
    facts = {}
    secs_top = [r["secs"] for r in top if r.get("secs")]
    secs_rest = [r["secs"] for r in rest if r.get("secs")]
    if secs_top:
        facts["median_seconds_top20"] = st.median(secs_top)
    if secs_rest:
        facts["median_seconds_rest"] = st.median(secs_rest)
    facts["question_titles_top20"] = sum("?" in r["title"] for r in top)
    facts["why_how_what_titles_top20"] = sum(bool(re.match(r"(?i)\W*(why|how|what)", r["title"])) for r in top)
    facts["median_title_chars_top20"] = st.median(len(r["title"]) for r in top)
    ours = read_json(DATA / "performance.json", []) or []
    out = llm_json(f"""You are the strategist for "Ever Thought Why?", a YouTube Shorts channel of accurate,
curious science explainers for US viewers (hook -> explain -> pause and predict -> answer -> closing
"Ever thought why..." question; two narrators; real footage or drawn diagrams).
Study the market and our own numbers, and write the playbook the scriptwriter follows this week.

TOP 20 English science/curiosity Shorts of the last 30 days by views per day:
{[{k: r.get(k) for k in ("title", "views_per_day", "secs", "comments", "channel")} for r in top]}
Counted facts: {facts}
The next {min(len(rest), 30)}, for comparison: {[{k: r.get(k) for k in ("title", "views_per_day", "secs")} for r in rest[:30]]}
OUR channel's videos with real numbers (may be few): {ours[-20:] or 'none yet'}
Last week's playbook (keep what still holds, change what the data now contradicts): {old.get('rules') or 'none'}

ALREADY BUILT IN (fixed - never write rules or experiments about these): the enquiry arc and who
speaks each part (the host gives the hook, the mid-video question, and the closing question; the
explainer explains); the COUNTDOWN EXPERIMENT (half the videos say "Pause and guess... 3-2-1", half
ask the question plainly; the data decides, never suggest changing it); an on-screen hook title in
the first seconds; phrase captions; the loop ending; the small corner logo; illustrated scenes and
maps where footage cannot show a line.
Rules for you: concrete and testable, never generic advice. Patterns only - never copy a title, idea
or anyone's footage. Never suggest anything inaccurate, sensational fear, health advice, photo-real
AI imagery, re-cut TV footage, or asking viewers to subscribe/like. Ignore kids-song, prank, comedy
and dance videos: they are not our genre.
Return JSON: {{
 "rules": ["5-7 short rules the scriptwriter must follow this week"],
 "formats_now": ["3-5 topic formats that are winning now, each with a one-line why"],
 "hook_shapes": ["3-5 opening-line shapes that are working, as templates with X/Y"],
 "title_shapes": ["3 title templates"],
 "topic_areas": ["5 subject areas viewers are hungry for now that are filmable and our genre"],
 "stop_doing": ["things our own numbers or the market say to drop, or empty if unknown"],
 "target_seconds": a whole number between {MIN_S} and {MAX_S}: the length that fits the winners AND
   still leaves room for the enquiry arc,
 "experiment": "one change to try in some videos this week, and how we will know if it worked"}}""")
    if not out.get("rules"):
        log("playbook: the study returned nothing usable; keeping the current playbook")
        return old
    try:
        out["target_seconds"] = max(MIN_S, min(MAX_S, int(out.get("target_seconds") or 40)))
    except (TypeError, ValueError):
        out["target_seconds"] = 40
    out["facts"] = facts
    out["studied"] = dt.datetime.now().isoformat(timespec="seconds")
    out["history"] = ([{"studied": old["studied"], "rules": old.get("rules"), "target_seconds": old.get("target_seconds")}]
                      if old.get("studied") else []) + (old.get("history") or [])[:7]
    write_json(PATH, out)
    log(f"playbook: studied {len(rows)} trend videos; aim for {out['target_seconds']} s; "
        f"rules: {' | '.join(out['rules'][:3])}")
    return out


def brief():
    """The playbook as a block of text for the writer's prompt ('' before the first study)."""
    p = current()
    r = read_json(DATA / "research.json", {}) or {}
    research = ("WHAT THE FASTEST-GROWING CHANNELS IN OUR GENRE DO (studied " + r.get("studied", "") + "):\n- "
                + "\n- ".join(r["lessons"]) + "\n") if r.get("lessons") else ""
    if not p.get("rules"):
        return research
    lines = [research + "THIS WEEK'S PLAYBOOK (learned from the biggest science Shorts right now + our own numbers;",
             "follow it unless it would break accuracy or any rule above):"]
    for key, label in (("rules", "Rules"), ("formats_now", "Winning formats"), ("hook_shapes", "Hook shapes"),
                       ("title_shapes", "Title shapes"), ("stop_doing", "Stop doing")):
        if p.get(key):
            lines.append(f"{label}: " + " | ".join(map(str, p[key])))
    if p.get("experiment"):
        lines.append(f"This week's experiment (use it in some videos): {p['experiment']}")
    return "\n".join(lines)
