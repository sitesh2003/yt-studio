"""Agent 8 - Health: the channel looks after itself, no person needed.

Runs every 2 hours (with the answers job) and at the end of every production run:
  1. ROLL CALL   reads GitHub's own record of production runs. A planned run that never started
                 (GitHub skipped it) or that failed is noted, and if the video bank is short a
                 catch-up production run is started straight away.
  2. AUDIT       every video waiting in the bank gets a last accuracy check BEFORE it goes public:
                 title, description and narration against the facts. An overstated title or
                 description is rewritten in place; a false spoken claim (audio cannot be edited)
                 takes the video off the schedule, kept private, and the bank refills.
  3. STATUS      writes STATUS.md (in the repo, readable any time) and the block for the daily
                 email: what ran, what was skipped, what was done about it, how far ahead the bank
                 covers, and when the next production run is due.
"""
import datetime as dt
import os
import re
from zoneinfo import ZoneInfo

import requests

from .core import DATA, ROOT, config, llm_json, log, read_json, write_json

IST, ET = ZoneInfo("Asia/Kolkata"), ZoneInfo("America/New_York")
REPO = os.environ.get("GITHUB_REPOSITORY", "sitesh2003/yt-studio")
GRACE = dt.timedelta(hours=2)   # GitHub may start a scheduled run late; after this it was skipped


def _gh(path, method="GET", **kw):
    h = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    r = requests.request(method, f"https://api.github.com/repos/{REPO}/{path}", headers=h, timeout=30, **kw)
    r.raise_for_status()
    return r.json() if r.content else {}


def planned_times():
    """The production times, read from the workflow file itself (one source of truth)."""
    yml = (ROOT / ".github" / "workflows" / "daily.yml").read_text(encoding="utf-8")
    return [(int(h), int(m)) for m, h in re.findall(r'cron:\s*"(\d+)\s+(\d+)\s+\*\s+\*\s+\*"', yml)]


def _expected(now):
    out = []
    for d in range(-2, 3):
        day = (now + dt.timedelta(days=d)).date()
        for h, m in planned_times():
            out.append(dt.datetime(day.year, day.month, day.day, h, m, tzinfo=dt.timezone.utc))
    return sorted(out)


def roll_call(now=None, watch_from=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    runs = _gh("actions/workflows/daily.yml/runs?per_page=30").get("workflow_runs", [])
    runs = [{"at": dt.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")), "event": r["event"],
             "status": r["status"], "result": r.get("conclusion"), "url": r["html_url"]} for r in runs]
    since = max(now - dt.timedelta(hours=26), watch_from or now - dt.timedelta(hours=26))
    planned = [t for t in _expected(now) if since <= t <= now - GRACE]
    sched = [r for r in runs if r["event"] == "schedule"]
    skipped = [t for t in planned
               if not any(t - dt.timedelta(minutes=5) <= r["at"] <= t + GRACE for r in sched)]
    failed = [r for r in runs if r["at"] >= since and r["status"] == "completed"
              and r["result"] in ("failure", "timed_out", "cancelled")]
    running = any(r["status"] in ("queued", "in_progress", "waiting", "pending") for r in runs)
    nxt = next((t for t in _expected(now) if t > now), None)
    return {"skipped": skipped, "failed": failed, "running": running, "next": nxt}


def start_catch_up():
    _gh("actions/workflows/daily.yml/dispatches", method="POST", json={"ref": "main"})
    log("health: catch-up production run started")


def coverage():
    """Scheduled publish times still ahead, read from YouTube (whichever machine uploaded)."""
    from .youtube import _scheduled_times
    now = dt.datetime.now(dt.timezone.utc)
    return sorted(t for t in (dt.datetime.fromisoformat(x.replace("Z", "+00:00")) for x in _scheduled_times())
                  if t > now)


def audit_bank():
    """Last accuracy check on every waiting video, before the public sees it."""
    from .youtube import yt
    done = set(read_json(DATA / "audited.json", []) or [])
    hist = {h["video_id"]: h for h in (read_json(DATA / "history.json", []) or []) if h.get("video_id")}
    y = yt()
    now = dt.datetime.now(dt.timezone.utc)
    actions = []
    pulled = False
    for vid, h in hist.items():
        if vid in done:
            continue
        items = y.videos().list(part="snippet,status", id=vid).execute().get("items", [])
        if not items:
            continue
        v = items[0]
        pa = v["status"].get("publishAt")
        if not pa or dt.datetime.fromisoformat(pa.replace("Z", "+00:00")) <= now:
            done.add(vid)  # already public (or not scheduled): nothing left to protect
            continue
        sn = v["snippet"]
        spoken = h.get("narration") or h.get("hook", "")
        first = sn["description"].split("\n\n")[0]
        out = llm_json(f"""You are the last accuracy check before a science Short goes public. Be strict but fair:
popular simplifications are fine; overstatements, myths and false claims are not.
TITLE: {sn['title']}
DESCRIPTION: {first}
NARRATION (spoken, cannot be edited): {spoken}
Return JSON: {{"title_ok": true or false, "description_ok": true or false,
 "fixed_title": "accurate title, same curiosity, max 70 chars, Title Case, ends with 2 fitting emojis",
 "fixed_description": "accurate 1-2 lines, no hashtags",
 "narration_false": true only if the narration states something actually FALSE or clearly misleading,
 "false_sentence": "if narration_false: the exact sentence from the narration that is wrong",
 "correct_version": "if narration_false: what is actually true, in one or two plain sentences",
 "why": "one line"}}""")
        if out.get("narration_false"):
            st = {"privacyStatus": "private",
                  "selfDeclaredMadeForKids": v["status"].get("selfDeclaredMadeForKids", False)}
            y.videos().update(part="status", body={"id": vid, "status": st}).execute()
            actions.append(f"Taken off the schedule before going public: '{sn['title']}'. Wrong line: "
                           f"\"{out.get('false_sentence', '?')}\". Correct: {out.get('correct_version', out.get('why', ''))} "
                           "A corrected remake is queued for the next production run.")
            remakes = read_json(DATA / "remakes.json", []) or []
            remakes.append({"topic": h.get("topic") or sn["title"], "pulled": vid, "title": sn["title"],
                            "false_sentence": out.get("false_sentence", ""),
                            "correct_version": out.get("correct_version", ""), "why": out.get("why", ""),
                            "tries": 0})
            write_json(DATA / "remakes.json", remakes)
            pulled = True
        elif not (out.get("title_ok", True) and out.get("description_ok", True)):
            body = {"title": sn["title"], "description": sn["description"],
                    "categoryId": sn.get("categoryId", "28"), "tags": sn.get("tags", [])}
            if not out.get("title_ok", True) and out.get("fixed_title"):
                body["title"] = out["fixed_title"][:100]
            if not out.get("description_ok", True) and out.get("fixed_description"):
                parts = sn["description"].split("\n\n", 1)
                tags = " ".join(w for w in parts[0].split() if w.startswith("#"))
                body["description"] = (out["fixed_description"] + (" " + tags if tags else "")
                                       + ("\n\n" + parts[1] if len(parts) > 1 else ""))
            y.videos().update(part="snippet", body={"id": vid, "snippet": body}).execute()
            actions.append(f"Corrected before going public: '{sn['title']}' -> '{body['title']}' ({out.get('why', '')})")
        done.add(vid)
    write_json(DATA / "audited.json", sorted(done))
    for a in actions:
        log("health: " + a)
    audit_bank.pulled = pulled
    return actions


def _fmt(t):
    return t.astimezone(IST).strftime("%a %d %b, %I:%M %p IST")


def check(heal=True):
    """Roll call + catch-up + audit + STATUS.md. Returns the lines for the daily email."""
    lines, notes = [], read_json(DATA / "health.json", {}) or {}
    reported = notes.get("reported", [])
    notes.setdefault("watch_from", dt.datetime.now(dt.timezone.utc).isoformat())  # only judge runs planned after the first check
    try:
        rc = roll_call(watch_from=dt.datetime.fromisoformat(notes["watch_from"]))
    except Exception as e:
        rc = None
        lines.append(f"Could not read GitHub's run list ({str(e)[:80]}).")
    try:
        lines += audit_bank()
    except Exception as e:
        log(f"health: audit skipped ({str(e)[:80]})")
    try:
        bank = coverage()
    except Exception as e:
        bank = []
        lines.append(f"Could not read the YouTube schedule ({str(e)[:80]}).")
    p = config()["publish"]
    target = p.get("bank_days", 2) * p["videos_per_day"]
    if rc:
        for t in rc["skipped"]:
            if t.isoformat() not in reported:
                lines.append(f"GitHub skipped the production run planned for {_fmt(t)}.")
                reported.append(t.isoformat())
        for r in rc["failed"]:
            if r["url"] not in reported:
                lines.append(f"The production run at {_fmt(r['at'])} ended as '{r['result']}'.")
                reported.append(r["url"])
        problem = rc["skipped"] or rc["failed"] or getattr(audit_bank, "pulled", False)
        if heal and problem and len(bank) < target and not rc["running"] and os.environ.get("GITHUB_TOKEN"):
            last = notes.get("catch_up")
            if not last or dt.datetime.fromisoformat(last) < dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=3):
                try:
                    start_catch_up()
                    notes["catch_up"] = dt.datetime.now(dt.timezone.utc).isoformat()
                    lines.append("A catch-up production run was started automatically.")
                except Exception as e:
                    lines.append(f"Could not start a catch-up run ({str(e)[:80]}).")
    notes["reported"] = reported[-60:]
    write_json(DATA / "health.json", notes)
    cover = f"covers until {_fmt(bank[-1])}" if bank else "is EMPTY: nothing scheduled"
    summary = [f"Video bank: {len(bank)} of {target} videos ready, {cover}."]
    if rc and rc["next"]:
        summary.append(f"Next production run: {_fmt(rc['next'])}"
                       + (" (one is running now)" if rc["running"] else "") + ".")
    out = summary + lines
    _status(out, bank)
    for l in out:
        log("health: " + l)
    return out


def _status(lines, bank):
    now = dt.datetime.now(dt.timezone.utc)
    rows = "\n".join(f"| {_fmt(t)} | {t.astimezone(ET).strftime('%a %I:%M %p ET')} |" for t in bank) or "| (none) | |"
    plan = ", ".join(dt.datetime(2000, 1, 1, h, m, tzinfo=dt.timezone.utc).astimezone(IST).strftime("%I:%M %p")
                     for h, m in planned_times())
    body = "\n".join(f"- {l}" for l in lines)
    (ROOT / "STATUS.md").write_text(
        "# Ever Thought Why? - status\n\n"
        f"Updated {_fmt(now)} by the health agent (every 2 hours, and after every production run).\n\n"
        f"{body}\n\n## Videos waiting to go public\n\n| Goes public (India) | US time |\n|---|---|\n{rows}\n\n"
        f"Production runs every day at {plan} IST (GitHub's quiet hours). Each run tops the bank up to two\n"
        "days of videos; a skipped or failed run is caught here and a catch-up run starts automatically.\n",
        encoding="utf-8")
