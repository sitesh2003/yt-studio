"""Where do we stand? (25 Nov 2026) The first thing every work session prints.

    python tools/plan_status.py

1. Days covered per channel: the scheduled 3D videos in data/hero_queue.json that are still to go public.
   The owner's rule: Shorts are planned and scheduled at least THREE days ahead; a long "book" film every two weeks.
2. The next free slot per channel (main 19:00 ET, Hindi 02:30 ET, Why It Works weekly 16:30 ET).
3. The topic library (research/topics/library.json): how many topics at each stage, and the best ready ones.
4. What people shared (data/performance.json if present): shares per 1,000 views, best first.
Prints only; changes nothing.
"""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")
ET = dt.timezone(dt.timedelta(hours=-5))
NOW = dt.datetime.now(dt.timezone.utc)
AHEAD_DAYS = 3
SLOT = {"main": (19, 0), "hi": (2, 30), "wiw": (16, 30)}


def load(p, default):
    try:
        return json.loads((ROOT / p).read_text(encoding="utf-8"))
    except Exception:
        return default


def main():
    q = load("data/hero_queue.json", {}).get("queue", [])
    print(f"Now: {NOW.astimezone(ET):%a %d %b %H:%M} ET\n")
    print("1. SCHEDULED, still to go public")
    for ch in ("main", "hi", "wiw"):
        fut = sorted((dt.datetime.fromisoformat(x["public_at"]), x) for x in q
                     if x.get("channel") == ch and x.get("public_at") and x.get("status") == "uploaded"
                     and dt.datetime.fromisoformat(x["public_at"]) > NOW)
        last = fut[-1][0] if fut else NOW
        days = (last - NOW).total_seconds() / 86400
        flag = "OK" if days >= AHEAD_DAYS or ch == "wiw" else f"NEED {AHEAD_DAYS - days:.1f} more day(s)"
        print(f"   {ch:4} {len(fut):2} video(s), covered to {last.astimezone(ET):%a %d %b %H:%M} ET "
              f"({days:.1f} days)  {flag}")
        for t, x in fut:
            print(f"        {t.astimezone(ET):%a %d %b %H:%M}  {x.get('name')}  {x.get('title', '')[:60]}")
        h, m = SLOT[ch]
        nxt = last.astimezone(ET) + dt.timedelta(days=7 if ch == "wiw" else 1)
        print(f"        next free slot: {nxt.replace(hour=h, minute=m):%a %d %b %H:%M} ET")
    lib = load("research/topics/library.json", {}).get("topics", [])
    print(f"\n2. TOPIC LIBRARY: {len(lib)} topics")
    stages = {}
    for t in lib:
        stages[t.get("status", "idea")] = stages.get(t.get("status", "idea"), 0) + 1
    print("   " + ", ".join(f"{k}: {v}" for k, v in sorted(stages.items())))
    ready = sorted((t for t in lib if t.get("status") in ("picked", "facts_checked")),
                   key=lambda t: -float(t.get("score", 0)))
    for t in ready[:8]:
        print(f"   [{t.get('status')}] {t.get('score', '?')}  {t.get('id')}  {t.get('title', '')[:70]}")
    books = [t for t in lib if t.get("format") == "book" and t.get("status") not in ("published", "rejected")]
    if books:
        print("   long-film books waiting: " + "; ".join(b.get("title", b.get("id")) for b in books[:4]))
    perf = load("data/performance.json", {})
    rows = perf.get("videos", perf) if isinstance(perf, dict) else perf
    rows = [r for r in rows if isinstance(r, dict) and r.get("views")] if isinstance(rows, list) else []
    if rows:
        for r in rows:
            r["_s"] = 1000 * float(r.get("shares", 0)) / max(1, float(r["views"]))
        print("\n3. SHARES PER 1,000 VIEWS (best first)")
        for r in sorted(rows, key=lambda r: -r["_s"])[:8]:
            print(f"   {r['_s']:5.1f}  {int(r['views']):>6} views  {str(r.get('title', ''))[:60]}")


if __name__ == "__main__":
    main()
