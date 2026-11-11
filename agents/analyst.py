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
            rows.append({"topic": h["topic"], "title": h["title"], "hook": h["hook"], **s})
    write_json(DATA / "performance.json", rows)
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
