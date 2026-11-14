"""Agent 6 - The learning loop. Pulls your real numbers, finds what separates
winners from losers on YOUR channel, and writes learnings.json, which the
writer reads before every new script."""
from .core import DATA, llm_json, log, read_json, write_json
from .youtube import channel_stats


def learn():
    stats = channel_stats()
    history = {h.get("video_id"): h for h in (read_json(DATA / "history.json", []) or [])}
    rows = []
    for s in stats:
        h = history.get(s["video"])
        if h:
            rows.append({"topic": h["topic"], "title": h["title"], "hook": h["hook"],
                         "countdown": h.get("countdown"), "length_arm": h.get("length_arm"),
                         "duration": h.get("duration"), "publish_at": h.get("publish_at"), **s})
    write_json(DATA / "performance.json", rows)
    try:
        experiment(rows)
    except Exception as e:
        log(f"analyst: experiment scoring skipped: {e}")
    try:
        length_experiment(rows)
    except Exception as e:
        log(f"analyst: length experiment skipped: {e}")
    if len(rows) < 5:
        log(f"analyst: {len(rows)} videos with data, need 5+ before drawing conclusions")
        return None
    out = llm_json(f"""These are a YouTube Shorts channel's videos with real performance numbers.
averageViewPercentage above 100 means people rewatch. Compare the top third with the bottom third.
Find concrete, testable patterns in topic, hook wording, title and length. No generic advice.
Data: {rows}
Return JSON: {{"summary": "5 bullet-style sentences the scriptwriter must follow next",
"winning_hooks": ["..."], "avoid": ["..."], "next_experiment": "one A/B idea to test"}}""")
    write_json(DATA / "learnings.json", out)
    log("analyst: learnings updated")
    return out


def experiment(rows, min_each=8, clear_gap=5.0, max_each=15):
    """Scores the countdown experiment (writer.countdown_arm) on average view percentage, the number
    YouTube uses to decide whether to show a Short to more people. Only videos made for the test count
    (they carry a countdown field), and only once they have been public for 2 days and have 100+ views,
    so a fresh video's early numbers can't decide it. A winner is named when both arms have 8+ videos
    and one leads by 5+ points, or at 15+ each, whichever leads. writer.countdown_arm then uses it."""
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc)
    arms = {"countdown": [], "turn": []}
    for r in rows:
        if r.get("countdown") is None or (r.get("views") or 0) < 100 or not r.get("publish_at"):
            continue
        try:
            if now - dt.datetime.fromisoformat(r["publish_at"]).astimezone(dt.timezone.utc) < dt.timedelta(days=2):
                continue
        except ValueError:
            continue
        arms["countdown" if r["countdown"] else "turn"].append(r)
    old = read_json(DATA / "experiments.json", {}) or {}
    exp = dict(old.get("countdown") or {})
    stat = {}
    for k, v in arms.items():
        stat[k] = {"videos": len(v),
                   "avg_view_pct": round(sum(r["averageViewPercentage"] for r in v) / len(v), 1) if v else None,
                   "avg_views": round(sum(r["views"] for r in v) / len(v)) if v else None}
    exp.update(started="2026-11-13", measure="average view percentage", arms=stat)
    a, b = stat["countdown"], stat["turn"]
    if not exp.get("winner") and min(a["videos"], b["videos"]) >= min_each:
        gap = a["avg_view_pct"] - b["avg_view_pct"]
        if abs(gap) >= clear_gap or min(a["videos"], b["videos"]) >= max_each:
            exp["winner"] = "countdown" if gap >= 0 else "turn"
            exp["decided"] = now.date().isoformat()
            log(f"analyst: countdown experiment decided -> {exp['winner']} ({a['avg_view_pct']}% vs {b['avg_view_pct']}% watched)")
    write_json(DATA / "experiments.json", {**old, "countdown": exp})
    return exp


def length_experiment(rows, min_each=8, clear_lead=1.25, max_each=15):
    """Scores the length test on VIEWS per video (reach), not view percentage: a shorter video always
    shows a higher percentage, so that number would favour 'short' by arithmetic alone. Same gates as
    the countdown test: public 2+ days, 100+ views; a winner at 8+ each with a 25% lead, or at 15+ each."""
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc)
    arms = {"short": [], "standard": []}
    for r in rows:
        if r.get("length_arm") not in arms or (r.get("views") or 0) < 100 or not r.get("publish_at"):
            continue
        try:
            if now - dt.datetime.fromisoformat(r["publish_at"]).astimezone(dt.timezone.utc) < dt.timedelta(days=2):
                continue
        except ValueError:
            continue
        arms[r["length_arm"]].append(r)
    old = read_json(DATA / "experiments.json", {}) or {}
    exp = dict(old.get("length") or {})
    stat = {k: {"videos": len(v), "avg_views": round(sum(r["views"] for r in v) / len(v)) if v else None,
                "avg_view_pct": round(sum(r.get("averageViewPercentage", 0) for r in v) / len(v), 1) if v else None,
                "avg_seconds": round(sum(r.get("duration") or 0 for r in v) / len(v), 1) if v else None}
            for k, v in arms.items()}
    exp.update(started="2026-11-14", measure="views per video", arms=stat)
    a, b = stat["short"], stat["standard"]
    if not exp.get("winner") and min(a["videos"], b["videos"]) >= min_each:
        hi, lo = max(a["avg_views"], b["avg_views"]), max(1, min(a["avg_views"], b["avg_views"]))
        if hi / lo >= clear_lead or min(a["videos"], b["videos"]) >= max_each:
            exp["winner"] = "short" if a["avg_views"] >= b["avg_views"] else "standard"
            exp["decided"] = now.date().isoformat()
            log(f"analyst: length experiment decided -> {exp['winner']} ({a['avg_views']} vs {b['avg_views']} views)")
    write_json(DATA / "experiments.json", {**old, "length": exp})
    return exp


def experiment_line():
    """One plain sentence for the daily report."""
    e = (read_json(DATA / "experiments.json", {}) or {}).get("countdown") or {}
    a, b = (e.get("arms") or {}).get("countdown") or {}, (e.get("arms") or {}).get("turn") or {}
    if e.get("winner"):
        return (f"Countdown test decided on {e.get('decided')}: "
                f"{'keeping the countdown' if e['winner'] == 'countdown' else 'no countdown from now on'} "
                f"({a.get('avg_view_pct')}% vs {b.get('avg_view_pct')}% watched).")
    return (f"Countdown test running: {a.get('videos', 0)} with the countdown "
            f"({a.get('avg_view_pct') or '-'}% watched) vs {b.get('videos', 0)} without "
            f"({b.get('avg_view_pct') or '-'}%); needs 8 of each, public 2+ days.")
