"""Agent 5 - The comment replier: read, understand, check, then reply.

The old replier saw bare comment text in a batch, with no idea what the video said. This one, for each
comment:
  1. knows the video: title, the full narration, the closing question and its answer, verified sources;
  2. reads the whole thread, so a viewer replying to OUR comment gets an answer too (follow-ups);
  3. works out what the person means (question, guess at the closing question, correction, story,
     topic idea, praise, joke, confusion, hostility, spam, a personal medical worry) and what to do;
  4. checks before it speaks: a viewer's correction gets its own fact-check, and a reply that states
     anything beyond the video's facts gets a second accuracy pass that may fix or drop it;
  5. answers in the commenter's language (auto-dubbing brings viewers who are not English speakers);
  6. learns: a correction that proves right becomes a lesson the writer never repeats, and topic ideas
     go to data/viewer_requests.json, which the topic picker reads.
It never argues, never asks for likes or subscriptions, never posts links, never gives personal
medical advice, and skips spam, hate, sexual, political and baiting comments.
"""
import datetime as dt

from .core import DATA, add_lesson, config, llm_json, log, read_json, write_json

REPLIED = DATA / "replied.json"


def _me(y):
    return y.channels().list(part="id", mine=True).execute()["items"][0]["id"]


def fetch(limit=100):
    """Comments that need us: new top-level comments we have not answered, and viewer replies that
    came after our last word in a thread (a follow-up)."""
    from .youtube import yt
    y = yt()
    me = _me(y)
    res = y.commentThreads().list(part="snippet,replies", allThreadsRelatedToChannelId=me, order="time",
                                  maxResults=min(limit, 100), textFormat="plainText").execute()
    done = set(read_json(REPLIED, []) or [])
    out = []
    for t in res.get("items", []):
        top = t["snippet"]["topLevelComment"]
        ts = top["snippet"]
        thread = [{"id": top["id"], "who": "us" if (ts.get("authorChannelId") or {}).get("value") == me
                   else ts.get("authorDisplayName", "viewer"), "text": ts.get("textDisplay", "")[:600],
                   "at": ts.get("publishedAt", "")}]
        for r in sorted((t.get("replies") or {}).get("comments", []), key=lambda c: c["snippet"]["publishedAt"]):
            rs = r["snippet"]
            thread.append({"id": r["id"], "who": "us" if (rs.get("authorChannelId") or {}).get("value") == me
                           else rs.get("authorDisplayName", "viewer"), "text": rs.get("textDisplay", "")[:600],
                           "at": rs.get("publishedAt", "")})
        last = thread[-1]
        if last["who"] == "us" or last["id"] in done:
            continue                        # we spoke last, or already answered this exact comment
        if len(thread) == 1 and top["id"] in done:
            continue
        we_spoke = any(m["who"] == "us" for m in thread)
        if len(thread) > 1 and not we_spoke:
            continue                        # viewers talking among themselves: let them
        out.append({"key": last["id"], "parent": top["id"], "video_id": ts.get("videoId"),
                    "author": last["who"], "text": last["text"], "thread": thread,
                    "kind": "followup" if we_spoke else "new"})
    return out


def _context(video_id, cache={}):
    if video_id not in cache:
        h = next((h for h in (read_json(DATA / "history.json", []) or []) if h.get("video_id") == video_id), {})
        cache[video_id] = {k: h.get(k) for k in ("title", "narration", "question", "answer_comment",
                                                 "sources", "fact_check", "description")}
    return cache[video_id]


def _understand(item, ctx):
    ch = config()["channel"]
    convo = "\n".join(f"{'CHANNEL' if m['who'] == 'us' else m['who']}: {m['text']}" for m in item["thread"])
    return llm_json(f"""You run the comments for "{ch['name']}", an accurate science Shorts channel. Tone: {ch['voice_tone']}.
THE VIDEO this comment is on:
Title: {ctx.get('title') or 'unknown'}
What the video says (full narration): {ctx.get('narration') or 'unknown'}
Its closing question: {ctx.get('question') or 'none'}
The correct answer: {ctx.get('answer_comment') or 'not available'}
Verified sources: {[s.get('cite') for s in (ctx.get('sources') or [])] or 'none'}

THE CONVERSATION (oldest first; reply to the LAST message, from {item['author']}):
{convo}

First UNDERSTAND, then decide. Rules for a reply:
- Reply in the SAME LANGUAGE as their message. 1-3 short sentences, warm, specific to what THEY said
  (quote or name their point), like a curious friend, never a bot ("Great question!" alone is not a reply).
- Questions: answer from the video's facts and well-established science only. If you are not sure, say
  so honestly and say it might make a good future video. Never invent a study, number or source; you may
  name one of the verified sources above if it is relevant (author and year, no link).
- A guess at the closing question: judge it against the correct answer. Right: say so warmly and add
  one extra detail. Partly right: credit what is right and give a nudge. Wrong: be kind, give a hint.
- A correction ("that's wrong", "actually..."): do NOT agree or disagree yet; set intent "correction"
  and write their claim in "claim" (it is checked separately).
- A personal medical worry: give the general fact only and say to see a doctor; no diagnosis or dose.
- Topic ideas ("do a video on X"): thank them, and put X in "topic_idea".
- Praise or a story: respond to the specific thing they shared.
- SKIP (no reply): spam, self-promotion, links, hate, sexual or political content, baiting or trolling,
  emoji-only or one-word comments with nothing to answer, and anything you cannot answer helpfully.
- Never: argue, mock, ask for likes/subscriptions, post links, share personal data, promise anything.
Return JSON: {{"understood": "one line: what they actually mean",
 "intent": "question|guess|correction|praise|story|topic_idea|joke|confused|medical|hostile|spam|other",
 "language": "the language of their message", "action": "reply|skip",
 "reply": "the reply text, or empty", "claim": "their factual claim if a correction, else empty",
 "topic_idea": "the topic if they suggested one, else empty",
 "beyond_video": true if the reply states any fact NOT in the video narration or answer}}""")


def _check_correction(claim, ctx):
    return llm_json(f"""A viewer says a science video got something wrong. Fact-check strictly, using only settled,
mainstream science (what textbooks, NASA/NIH/CDC or peer-reviewed reviews say).
What the video said: {ctx.get('narration')}
The viewer's claim: "{claim}"
Return JSON: {{"viewer_right": true or false, "partly": true or false,
 "truth": "the correct statement in one sentence", "video_line_wrong": "the exact wrong line from the video, or empty"}}""")


def _check_reply(reply, ctx, language, comment=""):
    """Second pass before posting. Tested 14 Nov 2026 on six sample comments: without it a reply told a
    viewer the grip benefit of pruned fingers is fact (the video says scientists still debate it), one
    made a shaky claim about dead skin cells, and one promised a video."""
    out = llm_json(f"""Check this reply to a viewer before an accurate science channel posts it.
What the video said: {ctx.get('narration')}
The video's closing question: {ctx.get('question') or 'none'}
Its answer: {ctx.get('answer_comment') or 'none'}
The viewer wrote: "{comment}"
Reply ({language}): "{reply}"
Check strictly:
1. Is EVERY factual statement correct by settled mainstream science? A shaky or half-true claim counts as wrong.
2. Where the video (or science) says something is debated, uncertain or a hypothesis, does the reply
   keep that uncertainty? Stating a debated idea as fact is wrong.
3. No promises (no "I'll make a video", "stay tuned", "added to my list"), no links, no personal data,
   no medical advice, kind and not lecturing.
If anything fails, rewrite the reply so it passes, same language, 1-3 sentences, still answering exactly what the
viewer wrote; if it cannot be fixed, set ok false.
Return JSON: {{"ok": true or false, "reply": "the reply, corrected if needed", "problem": "what was wrong, or empty"}}""")
    if out.get("problem"):
        log(f"comments: reply fixed before posting ({str(out['problem'])[:80]})")
    return (out.get("reply") or reply) if out.get("ok") else None


def draft(limit=None):
    """Read, understand, check and draft replies. Returns the drafts (also saved)."""
    limit = limit or config()["community"]["max_replies_per_run"]
    items = fetch()[:limit]
    if not items:
        log("comments: nothing new")
        return []
    drafts = []
    for it in items:
        ctx = _context(it["video_id"])
        try:
            u = _understand(it, ctx)
        except Exception as e:
            log(f"comments: could not read a comment ({str(e)[:60]})")
            continue
        d = {"id": it["parent"], "key": it["key"], "comment": it["text"], "author": it["author"],
             "video_id": it["video_id"], "kind": it["kind"], "understood": u.get("understood"),
             "intent": u.get("intent"), "action": "skip", "reply": ""}
        if u.get("topic_idea"):
            req = read_json(DATA / "viewer_requests.json", []) or []
            req.append({"topic": str(u["topic_idea"])[:200], "video_id": it["video_id"],
                        "at": dt.date.today().isoformat()})
            write_json(DATA / "viewer_requests.json", req[-100:])
        reply = (u.get("reply") or "").strip() if u.get("action") == "reply" else ""
        if u.get("intent") == "correction" and u.get("claim"):
            v = _check_correction(u["claim"], ctx)
            lang = u.get("language", "English")
            d["correction"] = v
            if v.get("viewer_right") and not v.get("partly"):
                add_lesson("viewer correction", f"A viewer was right: {v.get('truth')} (video: {ctx.get('title')})")
                corr = read_json(DATA / "corrections.json", []) or []
                write_json(DATA / "corrections.json", corr + [{"video_id": it["video_id"], "title": ctx.get("title"),
                                                               "claim": u["claim"], **v}])
            reply = llm_json(f"""Write a 1-2 sentence reply in {lang} to a viewer who said: "{it['text']}".
Fact-check result: {v}. If they are right, thank them sincerely and state the correct fact. If partly right,
credit the right part and clarify. If wrong, kindly explain the real fact in plain words, no lecturing.
Never argue, no links. Return JSON: {{"reply": "..."}}""").get("reply", "")
        if reply:   # every reply is checked: facts, kept uncertainty, no promises
            reply = _check_reply(reply, ctx, u.get("language", "English"), it["text"]) or ""
        if reply:
            d.update(action="reply", reply=reply[:600])
        drafts.append(d)
    write_json(DATA / "reply_drafts.json", drafts)
    log(f"comments: read {len(drafts)}; {sum(d['action'] == 'reply' for d in drafts)} replies drafted, "
        f"{sum(d['action'] == 'skip' for d in drafts)} skipped")
    return drafts


def post(drafts=None):
    """Post approved replies; every answered comment is remembered so it is never answered twice."""
    from .youtube import yt
    drafts = read_json(DATA / "reply_drafts.json", []) if drafts is None else drafts
    auto = config()["community"]["mode"] == "auto"
    done = read_json(REPLIED, []) or []
    sent = 0
    for d in drafts or []:
        if d.get("action") == "reply" and d.get("approved", auto) and d.get("reply"):
            text = d["reply"] if d.get("kind") != "followup" else f"@{d.get('author', '').lstrip('@')} {d['reply']}"
            yt().comments().insert(part="snippet", body={"snippet": {"parentId": d["id"], "textOriginal": text}}).execute()
            sent += 1
            d["posted"] = True
        if d.get("posted") or d.get("action") == "skip":
            done.append(d.get("key") or d["id"])   # skipped ones too: never re-read the same spam
    write_json(REPLIED, done[-5000:])
    write_json(DATA / "reply_drafts.json", [d for d in drafts or [] if not d.get("posted") and d.get("action") != "skip"])
    log(f"comments: {sent} replies posted")
    return sent
