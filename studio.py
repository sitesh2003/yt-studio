"""YT Studio - one command runs the whole team of agents.

  python studio.py make "topic"     make one video (or leave topic out to let the agents pick)
  python studio.py daily            trends -> pick topics -> make videos -> publish or queue -> comments
  python studio.py queue            list videos waiting for your approval
  python studio.py approve JOB      upload a reviewed video to the next US prime-time slot
  python studio.py comments         draft replies to new comments (add --post to send approved ones)
  python studio.py learn            pull analytics and update what the writer learns from
  python studio.py demo             offline test: renders a sample video with no API keys
"""
import datetime as dt
import html
import sys

from agents import editor, trends, visuals, voice, writer
from agents.core import DATA, JOBS, config, log, read_json, slug, write_json


def build(script):
    job = JOBS / (dt.datetime.now().strftime("%Y%m%d-%H%M") + "-" + slug(script["topic"]))
    job.mkdir(parents=True, exist_ok=True)
    write_json(job / "script.json", script)
    words = voice.narrate(script, job)
    times = voice.scene_times(script, words)
    clips, credits = visuals.gather(script, times, job)
    editor.render(clips, times, words, job, editor.predict_overlays(script, times, words))
    spec = match_scenes(script)
    editor.thumbnail(job, spec or script.get("thumbnail_text") or script["title_options"][0])
    thumbs = thumbnail_options(job, spec)
    desc = script["description"]
    chapters = chapter_marks(script, times)
    if chapters:
        desc = desc.rstrip() + "\n\n" + chapters
    desc += ("\n\n" + "\n".join(credits) if credits else "")
    meta = {"topic": script["topic"], "title": script["title_options"][0], "description": desc,
            "tags": script.get("tags", []), "hook": script["scenes"][0]["narration"], "status": "review",
            "question": script.get("question", ""), "answer_comment": script.get("answer_comment", ""),
            "fact_ok": not (script.get("fact_check_result") or {}).get("unresolved", False),
            "weekly": bool(script.get("weekly")), "recap_source": script.get("recap_source")}
    write_json(job / "meta.json", meta)
    write_json(job / "words.json", words)
    from agents import qa
    for attempt in range(3):  # check, then up to 2 self-repairs of flagged scenes
        try:
            meta["qa"] = qa.check(job, script, times, words, visuals.last_scores)
        except Exception as e:
            meta["qa"] = {"pass": False, "error": str(e)[:200]}
            log(f"qa failed to run, holding the video: {e}")
            break
        q = meta["qa"]
        if q.get("pass") or attempt == 2 or q.get("facts") or q.get("technical") or q.get("sync"):
            break  # passed, or a problem footage can't fix
        notes = flagged_scenes(q, len(script["scenes"]))
        if not notes:
            break
        log(f"repair {attempt + 1}: re-picking footage for scene(s) {[i + 1 for i in notes]}")
        credits = visuals.repick(script, times, job, notes)
        editor.render(clips, times, words, job, editor.predict_overlays(script, times, words))
        editor.thumbnail(job, spec or script.get("thumbnail_text") or script["title_options"][0])
        thumbnail_options(job, spec)
        desc = script["description"] + (("\n\n" + chapters) if chapters else "") + \
            ("\n\n" + "\n".join(credits) if credits else "")
        meta["description"] = desc
    meta["repairs"] = attempt
    for raw in job.glob("raw_*.mp4"):
        raw.unlink(missing_ok=True)
    write_json(job / "meta.json", meta)
    review_page(job, script, meta)
    approve_button(job)
    hist = read_json(DATA / "history.json", []) or []
    write_json(DATA / "history.json", hist + [{"job": job.name, **meta}])
    log(f"done: {job}")
    return job, meta


def flagged_scenes(q, n):
    """{scene_index: reason} from the QA result: weak-footage scenes and 'Frame N' review notes."""
    import re
    notes = {}
    for line in q.get("footage", []):
        m = re.search(r"\[([\d,\s]+)\]", line)
        for k in (m.group(1).split(",") if m else []):
            if k.strip().isdigit():
                notes[int(k) - 1] = "no strong footage was found; find a clear literal match"
    for line in q.get("review", []):
        if re.search(r"caption|text|subtitle", line, re.I) and not re.search(r"footage|shows|image|clip|picture", line, re.I):
            continue  # a caption remark is not a footage problem: re-picking clips cannot fix it
        for k in re.findall(r"[Ff]rame\s*(\d+)", line):
            notes[int(k) - 1] = line[:220]
    return {i: r for i, r in notes.items() if 0 <= i < n}


def chapter_marks(script, times):
    """YouTube chapters for the weekly episode: '0:00 Intro' then one line per chapter."""
    marks = [(0.0, "Intro")]
    for sc, (a, _) in zip(script["scenes"], times):
        if sc.get("chapter") and a > 10 and sc["chapter"] != marks[-1][1]:
            marks.append((a, sc["chapter"]))
    if len(marks) < 3:
        return ""
    return "\n".join(f"{int(t // 60)}:{int(t % 60):02d} {name}" for t, name in marks)


def match_scenes(script):
    """Point each thumbnail half at the scene whose footage matches its words (ELEPHANTS ->
    the elephant scene), instead of trusting a scene number the writer may get wrong."""
    spec = dict(script.get("thumbnail") or {})
    if not spec:
        return None
    scenes = script["scenes"]

    def best(text, fallback):
        words = {w.lower().rstrip("s") for w in text.split() if len(w) > 2 and not w.isdigit()}
        scored = []
        for i, s in enumerate(scenes):
            main = s.get("visual_query", "").lower()          # what the clip was found with
            alt = " ".join(s.get("alt_queries", [])).lower()   # backup words count for less
            scored.append((sum(2 * (w in main) + (w in alt) for w in words), -i, i))
        top = max(scored)[0]
        # every matching scene goes to the designer, which keeps the most striking frame
        return [i for sc, _, i in scored if sc == top] if top > 0 else fallback

    if spec.get("layout") == "split":
        spec["top_scene"] = best(spec.get("top_text", ""), spec.get("top_scene"))
        spec["bottom_scene"] = best(spec.get("bottom_text", ""), spec.get("bottom_scene"))
    else:
        spec["scene"] = best(spec.get("text", ""), spec.get("scene"))
    return spec


def thumbnail_options(job, spec):
    """Up to 3 versions, each built on a different matching frame, for you to pick from."""
    if not spec:
        return ["thumbnail.jpg"]
    key = "top_scene" if spec.get("layout") == "split" else "scene"
    cands = spec.get(key) if isinstance(spec.get(key), list) else [spec.get(key)]
    other = [i for i in range(len(list((job / "frames").glob("*.jpg")))) if i not in cands]
    names = []
    for n, k in enumerate((cands + other)[:3]):
        if k is None:
            continue
        name = f"thumbnail_{n + 1}.jpg"
        editor.thumbnail(job, dict(spec, **{key: k}), name)
        names.append(name)
    return names or ["thumbnail.jpg"]


def approve_button(job):
    """Double-click APPROVE.bat in the video's folder: it uploads and schedules for the next US slot."""
    (job / "APPROVE.bat").write_text(
        "@echo off\r\n"
        f'cd /d "{job.parent.parent}"\r\n'
        f'".venv\\Scripts\\python.exe" studio.py approve "{job.name}"\r\n'
        "echo.\r\necho Done. You can close this window.\r\npause\r\n", encoding="utf-8")


def review_page(job, s, meta):
    e = html.escape
    li = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs)
    page = f"""<!doctype html><meta charset="utf-8"><title>Review: {e(meta['title'])}</title>
<style>body{{font:16px/1.5 system-ui;max-width:980px;margin:24px auto;padding:0 16px;display:grid;
grid-template-columns:360px 1fr;gap:28px}}video{{width:360px;border-radius:12px}}h2{{font-size:15px;
text-transform:uppercase;color:#0a7d68;margin:18px 0 6px}}code{{background:#eef;padding:2px 6px}}</style>
<div><video src="final.mp4" controls></video></div>
<div><h1 style="font-size:22px">{e(meta['title'])}</h1>
<h2>Pick a thumbnail</h2><div style="display:flex;gap:10px">{''.join(f'<figure style="margin:0;text-align:center"><img src="{t}" width="170" style="border-radius:8px"><figcaption>{t}</figcaption></figure>' for t in sorted(p.name for p in job.glob('thumbnail_*.jpg')) or ['thumbnail.jpg'])}</div>
<h2>Quality check</h2><p>{'<b style="color:#0a7d68">PASSED: cleared to publish</b>' if (meta.get('qa') or {}).get('pass') else '<b style="color:#b00020">HELD</b>'}</p>
<ul>{''.join(f"<li><b>{e(k)}</b>: {e(str(v))}</li>" for k, vals in (meta.get('qa') or {}).items() if isinstance(vals, list) for v in vals)}</ul>
<h2>Fact-checker</h2><p>{'<b style="color:#0a7d68">Passed</b>' if meta.get('fact_ok', True) else '<b style="color:#b00020">NOT resolved: check before approving</b>'}</p>
<ul>{''.join(f"<li><b>{e(c.get('status',''))}</b>: {e(c.get('claim',''))} <i>{e(c.get('note',''))}</i></li>" for c in (s.get('fact_check_result') or {}).get('claims', []))}</ul>
<h2>Enquiry question (ends the video)</h2><p>{e(meta.get('question',''))}</p>
<h2>Answer (posted as first comment when public)</h2><p>{e(meta.get('answer_comment',''))}</p>
<h2>Check these facts before publishing</h2><ul>{li(s.get('fact_check', []))}</ul>
<h2>Other titles</h2><ul>{li(s['title_options'][1:])}</ul>
<h2>Other hooks</h2><ul>{li(s['hook_options'][1:])}</ul>
<h2>Description</h2><p style="white-space:pre-wrap">{e(meta['description'])}</p>
<h2>Approve</h2><p><code>python studio.py approve {e(job.name)}</code></p></div>"""
    (job / "review.html").write_text(page, encoding="utf-8")


def publish(job):
    from agents import youtube
    meta = read_json(job / "meta.json")
    vid, when = youtube.upload(job, meta)
    meta.update(status="scheduled", video_id=vid, publish_at=when)
    write_json(job / "meta.json", meta)
    try:
        script = read_json(job / "script.json", {}) or {}
        youtube.add_to_series(vid, script.get("series") or meta.get("series"))
    except Exception as e:
        log(f"playlist skipped: {str(e)[:100]}")
    hist = read_json(DATA / "history.json", []) or []
    for h in hist:
        if h.get("job") == job.name:
            h.update(video_id=vid, status="scheduled", publish_at=when)
    write_json(DATA / "history.json", hist)


def comments(post=False):
    from agents import youtube
    drafts_path = DATA / "reply_drafts.json"
    if post:
        drafts = read_json(drafts_path, []) or []
        sent = 0
        for d in drafts:
            if d.get("action") == "reply" and d.get("approved", config()["community"]["mode"] == "auto"):
                youtube.post_reply(d["id"], d["reply"])
                sent += 1
        write_json(drafts_path, [d for d in drafts if d.get("action") != "reply"])
        log(f"comments: {sent} replies posted")
        return
    new = youtube.recent_comments()[:config()["community"]["max_replies_per_run"]]
    if not new:
        log("comments: nothing new")
        return
    items = writer.draft_replies(new)
    texts = {c["id"]: c["text"] for c in new}
    for it in items:
        it["comment"] = texts.get(it["id"], "")
    write_json(drafts_path, items)
    log(f"comments: {sum(i['action'] == 'reply' for i in items)} reply drafts in data/reply_drafts.json")


def _sequel():
    """If a video from the last 10 days has 3x the channel's median views (and 1,000+), make a
    follow-up today - doubling down on what works, like the channels that grow fastest."""
    from agents import youtube
    import statistics
    hist = [h for h in (read_json(DATA / "history.json", []) or []) if h.get("video_id")]
    if len(hist) < 4:
        return None
    v = youtube.views([h["video_id"] for h in hist])
    med = statistics.median(v.values()) if v else 0
    done = set(read_json(DATA / "sequels.json", []) or [])
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=10)).isoformat()
    best = max((h for h in hist if h["video_id"] not in done and (h.get("publish_at") or "") >= since[:10]),
               key=lambda h: v.get(h["video_id"], 0), default=None)
    if not best or v.get(best["video_id"], 0) < max(1000, 3 * med):
        return None
    write_json(DATA / "sequels.json", sorted(done | {best["video_id"]}))
    out = writer.sequel_topic(best.get("title", ""), best.get("topic", ""))
    return {"topic": out["topic"], "pattern": "sequel"} if out.get("topic") else None


def _today_ist():
    from zoneinfo import ZoneInfo
    return dt.datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")


def daily():
    # GitHub drops scheduled runs at busy times, so the workflow has back-up triggers;
    # this guard makes a later trigger a no-op once today's videos are made.
    import os
    mark = DATA / "last_daily.json"
    if not os.environ.get("FORCE_DAILY") and (read_json(mark, {}) or {}).get("date") == _today_ist():
        log("daily: today's videos are already made, nothing to do")
        return
    p = config()["publish"]
    try:
        trends.scan()
    except Exception as e:
        log(f"trends failed, continuing: {e}")
    from agents import youtube
    recap = None
    try:
        recap = youtube.previous_winners()
    except Exception as e:
        log(f"recap skipped: {e}")
    import time
    want = p["videos_per_day"]
    good = 0
    results = []
    # spare topics: a busy AI model or a held-back fact-check no longer means a missing video
    started = time.time()
    budget = float(os.environ.get("DAILY_BUDGET_MIN", "95")) * 60
    topics = writer.pick_topics(want + 2)
    try:
        seq = _sequel()
        if seq:
            topics = [seq] + topics
    except Exception as e:
        log(f"sequel check skipped: {str(e)[:100]}")
    for t in topics:
        if good >= want:
            break
        if time.time() - started > budget:
            log("daily: out of time for more videos today; sending the report")
            break
        use_recap = recap if good == 0 else None
        try:
            job, meta = build(writer.write_script(t["topic"], use_recap))
        except Exception as e:
            log(f"video failed, trying a spare topic: {e}")
            results.append({"topic": t["topic"], "reason": f"could not be made: {str(e)[:120]}"})
            time.sleep(60)  # let the free models cool down
            continue
        if use_recap:
            youtube.mark_recapped(recap["video_id"])
            recap = None
        if not meta.get("fact_ok", True):
            log("not uploading: fact-check unresolved, left for your review; trying a spare topic")
            results.append({"title": meta["title"], "reason": "fact-check could not confirm every claim"})
            continue
        if not (meta.get("qa") or {}).get("pass"):
            log("not uploading: quality check held it back; trying a spare topic")
            q = meta.get("qa") or {}
            why = "; ".join(f"{k}: {v}" for k, vals in q.items() if isinstance(vals, list) for v in vals)
            results.append({"title": meta["title"], "reason": "quality check: " + (why or "not approved")[:300]})
            continue
        good += 1
        if p["mode"] == "auto":
            publish(job)
            meta = read_json(job / "meta.json")
        results.append({"title": meta["title"], "video_id": meta.get("video_id"),
                        "publish_at": meta.get("publish_at"), "question": meta.get("question", "")})
    log(f"daily: {good} of {want} videos ready")
    if good:
        write_json(mark, {"date": _today_ist(), "videos": good})
    hourly()
    try:
        from agents import report
        stats = None
        try:
            stats = youtube.channel_summary()
        except Exception:
            pass
        report.send(*report.build(results, stats))
    except Exception as e:
        log(f"report email failed: {e}")


def weekly():
    """Saturday: an 8-10 minute widescreen episode that goes deeper on the week's Shorts."""
    from zoneinfo import ZoneInfo
    from agents import youtube
    from agents.core import set_override
    since = dt.datetime.now() - dt.timedelta(days=7)
    hist = read_json(DATA / "history.json", []) or []
    week = [h for h in hist if h.get("video_id") and not h.get("weekly")
            and dt.datetime.strptime(h["job"][:13], "%Y%m%d-%H%M") >= since]
    if len(week) < 3:
        log(f"weekly: only {len(week)} uploaded Shorts this week, need 3+; skipping")
        return
    set_override({"format": {"width": 1920, "height": 1080, "type": "long"},
                  "captions": {"size": 64, "position_y": 940, "words_per_line": 4, "outline": 4}})
    try:
        script = writer.write_weekly(week[-7:])
        script["weekly"] = True
        job, meta = build(script)
    finally:
        set_override({})
    if config()["publish"]["mode"] == "auto" and meta.get("fact_ok", True) and (meta.get("qa") or {}).get("pass"):
        et = ZoneInfo("America/New_York")
        now = dt.datetime.now(et)
        when = (now + dt.timedelta(days=(5 - now.weekday()) % 7)).replace(hour=10, minute=0, second=0, microsecond=0)
        if when < now + dt.timedelta(minutes=30):
            when += dt.timedelta(days=7)
        vid, at = youtube.upload(job, meta, when)
        meta.update(status="scheduled", video_id=vid, publish_at=at)
        write_json(job / "meta.json", meta)
        hist = read_json(DATA / "history.json", []) or []
        for h in hist:
            if h.get("job") == job.name:
                h.update(video_id=vid, status="scheduled", publish_at=at)
        write_json(DATA / "history.json", hist)


def hourly():
    """Light jobs that can run often: answer comments on newly public videos, draft replies."""
    from agents import youtube
    try:
        youtube.ensure_public()
    except Exception as e:
        log(f"publish check skipped: {e}")
    try:
        youtube.post_answers()
    except Exception as e:
        log(f"answers skipped: {e}")
    try:
        comments(post=False)                       # draft replies to new comments
        if config()["community"]["mode"] == "auto":
            comments(post=True)                    # and post them (early replies lift reach)
    except Exception as e:
        log(f"comments skipped: {e}")


DEMO = {
    "topic": "your stomach makes a new lining every few days",
    "hook_options": ["Your stomach is full of acid strong enough to dissolve metal."],
    "scenes": [
        {"narration": "Your stomach is full of acid strong enough to dissolve metal.", "visual_query": "stomach"},
        {"narration": "So why doesn't it digest itself?", "visual_query": "question"},
        {"narration": "Because it is always rebuilding.", "visual_query": "cells"},
        {"narration": "A thick layer of mucus coats the wall, and the cells under it are replaced every few days.", "visual_query": "microscope"},
        {"narration": "When that shield fails, you get an ulcer.", "visual_query": "doctor"},
        {"narration": "So right now, your stomach is quietly making a brand new inside, just to survive its own acid.", "visual_query": "body"},
    ],
    "title_options": ["Why Your Stomach Doesn't Digest Itself"],
    "description": "Your stomach acid could eat through metal. Here is why it does not eat you. #shorts #science #humanbody",
    "tags": ["science", "human body", "stomach"],
    "thumbnail_text": "IT DISSOLVES METAL",
    "fact_check": ["Stomach acid pH about 1.5 to 3.5", "Stomach lining cells renew every few days"],
}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "make":
        topic = " ".join(sys.argv[2:]) or writer.pick_topics(1)[0]["topic"]
        build(writer.write_script(topic))
    elif cmd == "daily":
        daily()
    elif cmd == "hourly":
        hourly()
    elif cmd == "weekly":
        weekly()
    elif cmd == "queue":
        for j in sorted(JOBS.iterdir()):
            m = read_json(j / "meta.json", {})
            if m and m.get("status") == "review":
                print(f"{j.name}  |  {m['title']}  |  open {j / 'review.html'}")
    elif cmd == "approve":
        job = JOBS / sys.argv[2]
        if (read_json(job / "meta.json", {}) or {}).get("status") == "scheduled":
            log("already uploaded and scheduled, nothing to do")
        else:
            publish(job)
    elif cmd == "signin":
        from agents import youtube
        ch = youtube.yt().channels().list(part="snippet,statistics", mine=True).execute().get("items", [])
        log(f"signed in. channel: {ch[0]['snippet']['title']}" if ch else "signed in, but this account has NO YouTube channel yet")
    elif cmd == "comments":
        comments(post="--post" in sys.argv)
    elif cmd == "learn":
        from agents import analyst
        analyst.learn()
    elif cmd == "demo":
        build(dict(DEMO))
    else:
        print(__doc__)
