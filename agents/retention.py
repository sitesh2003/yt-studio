"""Agent 6b - Where exactly do viewers leave? (YouTube's own audience-retention curve, per video.)

For every public video at least 2 days old with 100+ views it reads the 100-point retention curve
(audienceWatchRatio, and relativeRetentionPerformance: how it holds against similar videos on YouTube),
finds the moments with the steepest drops, and maps each moment to the sentence spoken there (exact
scene times for videos made from 14 Nov 2026, proportional word position before that). Then it learns
across videos what loses people and what keeps them, and writes data/retention_lessons.json, which
the writer reads before every script. This is the most direct feedback a Short can get: not "this
video did badly" but "people left at THIS line".
"""
import datetime as dt
import re

from .core import DATA, llm_json, log, read_json, write_json

PATH = DATA / "retention.json"
LESSONS = DATA / "retention_lessons.json"


def _curve(an, video_id, start):
    r = an.reports().query(ids="channel==MINE", startDate=start, endDate=dt.date.today().isoformat(),
                           dimensions="elapsedVideoTimeRatio",
                           metrics="audienceWatchRatio,relativeRetentionPerformance",
                           filters=f"video=={video_id}").execute()
    return [(float(a), float(b), float(c)) for a, b, c in r.get("rows", [])]


def _line_at(h, ratio):
    """The sentence being spoken at this fraction of the video."""
    sents = [s for s in re.split(r"(?<=[.?!])\s+", h.get("narration") or "") if s.strip()]
    if not sents:
        return ""
    times, dur = h.get("scene_times"), h.get("duration")
    if times and dur:      # exact: the scene playing at that moment
        t = ratio * dur
        k = next((i for i, (a, b) in enumerate(times) if a <= t <= b), len(times) - 1)
        scenes = h.get("scene_lines") or []
        if k < len(scenes):
            return scenes[k]
    words = " ".join(sents).split()
    pos, n = int(ratio * len(words)), 0
    for s in sents:
        n += len(s.split())
        if n >= pos:
            return s
    return sents[-1]


def analyse(video_id, h, curve):
    if len(curve) < 20:
        return None
    by = {round(x, 2): (w, rel) for x, w, rel in curve}
    get = lambda x: by.get(round(x, 2), (None, None))
    drops = []
    for k in range(len(curve) - 5):
        x0, w0, _ = curve[k]
        x1, w1, _ = curve[k + 5]
        if x0 >= 0.03:                       # the first swipe-away is the hook, measured separately
            drops.append((w0 - w1, x0, x1))
    drops.sort(reverse=True)
    picked = []
    for d, x0, x1 in drops:
        if all(abs(x0 - p["at"]) > 0.12 for p in picked):
            picked.append({"at": round(x0, 2), "lost": round(d, 3), "line": _line_at(h, (x0 + x1) / 2)})
        if len(picked) == 2:
            break
    early = [rel for x, w, rel in curve if x <= 0.10]
    late = [rel for x, w, rel in curve if x >= 0.70]
    return {"title": h.get("title"), "hook_line": _line_at(h, 0.01),
            "kept_at_10pct": get(0.10)[0], "kept_at_50pct": get(0.5)[0], "kept_at_end": curve[-1][1],
            "vs_similar_start": round(sum(early) / len(early), 2) if early else None,
            "vs_similar_end": round(sum(late) / len(late), 2) if late else None,
            "biggest_drops": picked, "countdown": h.get("countdown"),
            "checked": dt.date.today().isoformat()}


def study():
    """Read the curves of eligible videos, then learn what loses and keeps viewers."""
    from googleapiclient.discovery import build
    from .youtube import _creds
    an = build("youtubeAnalytics", "v2", credentials=_creds(), cache_discovery=False)
    hist = {h["video_id"]: h for h in (read_json(DATA / "history.json", []) or []) if h.get("video_id")}
    perf = {p.get("video"): p for p in (read_json(DATA / "performance.json", []) or [])}
    out = read_json(PATH, {}) or {}
    now = dt.datetime.now(dt.timezone.utc)
    for vid, h in hist.items():
        try:
            pub = dt.datetime.fromisoformat(h.get("publish_at") or "").astimezone(dt.timezone.utc)
        except ValueError:     # the first videos were published by hand: use the day they were made
            try:
                pub = dt.datetime.strptime(h["job"][:8], "%Y%m%d").replace(tzinfo=dt.timezone.utc)
            except (KeyError, ValueError):
                continue
        if now - pub < dt.timedelta(days=2) or (perf.get(vid, {}).get("views") or 0) < 100:
            continue
        try:
            a = analyse(vid, h, _curve(an, vid, pub.date().isoformat()))
        except Exception as e:
            log(f"retention: {vid} skipped ({str(e)[:60]})")
            continue
        if a:
            out[vid] = a
    write_json(PATH, out)
    log(f"retention: {len(out)} videos with a retention curve")
    if len(out) < 3:
        return out
    res = llm_json(f"""These are retention results for a science Shorts channel. For each video: how many viewers were
still watching at 10%, 50% and the end (above 1.0 means rewatches), how it held against similar videos on
YouTube at the start and the end (0.5 = typical, higher = better), and the two lines where most viewers left.
{list(out.values())}
Find concrete, testable patterns: which kinds of hook lines keep people past the first seconds, which kinds of
lines make people leave (a slow explanation? a repeated idea? a countdown? a pause?), what the best-holding
videos do differently. Only patterns the numbers support; say "not enough data" rather than guess.
Return JSON: {{"lessons": ["4-6 short rules for the scriptwriter, each tied to the evidence"],
 "worst_moment_types": ["..."], "best_hook_types": ["..."]}}""")
    if res.get("lessons"):
        res["studied"] = dt.date.today().isoformat()
        res["videos"] = len(out)
        write_json(LESSONS, res)
        log("retention: lessons -> " + " | ".join(res["lessons"][:3]))
    return out


def brief():
    r = read_json(LESSONS, {}) or {}
    return ("WHERE OUR VIEWERS LEAVE (from YouTube's retention curves of our own videos, " + r.get("studied", "")
            + "):\n- " + "\n- ".join(r["lessons"]) + "\n") if r.get("lessons") else ""
