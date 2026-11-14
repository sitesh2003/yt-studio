"""How many people care about a topic, measured for free: the median daily readers of the matching
Wikipedia article over the last 60 days (Wikimedia pageviews API, open data, no key; a User-Agent with
a contact link is required for the higher rate limit).

The daily planner suggests a few more topics than it needs; ranking them by this number means the
videos made first are the ones on subjects more people are already curious about. It is a tie-breaker,
never a reason to make something untrue or off-niche.
"""
import datetime as dt
import statistics
from urllib.parse import quote

import requests

from .core import log

UA = {"User-Agent": "yt-studio-demand/1.0 (https://github.com/sitesh2003/yt-studio)"}


_Q = {"why", "how", "what", "does", "do", "is", "are", "can", "the", "a", "an", "our", "your", "you", "we",
      "on", "in", "of", "to", "so", "when", "it", "its", "they", "their", "really", "actually"}


def _article(topic):
    """Best-matching English Wikipedia article for a topic's key words (question words removed: a whole
    question as a search once matched a rapper), or None."""
    import re
    q = " ".join(w for w in re.findall(r"[A-Za-z0-9'-]+", topic) if w.lower() not in _Q)
    r = requests.get("https://en.wikipedia.org/w/api.php", headers=UA, timeout=15, params={
        "action": "query", "list": "search", "srsearch": q[:200], "srlimit": 1, "format": "json"})
    hits = r.json().get("query", {}).get("search", [])
    return hits[0]["title"] if hits else None


def views(title, days=60):
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days)
    url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/"
           f"{quote(title.replace(' ', '_'), safe='')}/daily/{start:%Y%m%d}/{end:%Y%m%d}")
    r = requests.get(url, headers=UA, timeout=15)
    items = r.json().get("items", []) if r.ok else []
    return int(statistics.median([i["views"] for i in items])) if items else 0


def score(topic, article=None):
    """(median daily readers, article title) for a topic; (0, None) when unknown. The planner's own
    article name is used first; a search on the topic's key words is the fallback."""
    try:
        if article:
            v = views(article)
            if v:
                return v, article
        title = _article(topic)
        return (views(title), title) if title else (0, None)
    except Exception as e:
        log(f"demand: {str(e)[:60]}")
        return 0, None


def rank(topics):
    """Topics sorted by demand, highest first; each gets t['demand'] = (views, article)."""
    for t in topics:
        t["demand"] = score(t.get("topic", ""), t.get("wikipedia"))
    out = sorted(topics, key=lambda t: -t["demand"][0])
    log("demand: " + " | ".join(f"{t['demand'][0]}/day {t['demand'][1]}" for t in out))
    return out
