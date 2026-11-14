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


def lead(title, chars=2500):
    """The plain-text opening section of a Wikipedia article (reference for the fact-checker only;
    never read out or shown, so its CC BY-SA licence does not reach the video)."""
    r = requests.get("https://en.wikipedia.org/w/api.php", headers=UA, timeout=15, params={
        "action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1, "redirects": 1,
        "titles": title, "format": "json"})
    pages = r.json().get("query", {}).get("pages", {})
    return next((p.get("extract", "") for p in pages.values()), "")[:chars]


def _canonical(title):
    """Follow a redirect ("Flicker fusion rate" -> "Flicker fusion threshold"): readers land on the
    target, so a redirect's own count is near zero."""
    r = requests.get("https://en.wikipedia.org/w/api.php", headers=UA, timeout=15, params={
        "action": "query", "titles": title, "redirects": 1, "format": "json"})
    pages = r.json().get("query", {}).get("pages", {})
    p = next(iter(pages.values()), {})
    return None if "missing" in p else p.get("title", title)


def views(title, days=60):
    title = _canonical(title) or title
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
        import re
        key = {w.lower()[:5] for w in re.findall(r"[A-Za-z]{4,}", f"{topic} {article or ''}") if w.lower() not in _Q}
        for q in ([article] if article else []) + [topic]:
            title = _article(q)
            # a search hit must share a key word with the topic ("brain energy" once matched "Israel")
            if title and key & {w.lower()[:5] for w in re.findall(r"[A-Za-z]{4,}", title)}:
                return views(title), title
        return 0, None
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


# Numeric facts from Wikidata (CC0) for the fact-checker. Property -> plain name.
FACT_PROPS = {"P2250": "life expectancy", "P4214": "highest observed lifespan", "P2067": "mass",
              "P2052": "speed", "P2048": "height", "P2043": "length", "P2049": "width", "P2386": "diameter",
              "P2120": "radius", "P2583": "distance from Earth", "P2102": "boiling point",
              "P2101": "melting point", "P2054": "density", "P2046": "area", "P2044": "elevation",
              "P1082": "population", "P2146": "orbital period", "P2147": "rotation period",
              "P2076": "temperature", "P1086": "atomic number", "P2665": "alcohol by volume"}
_UNITS = {}


def _unit(qid):
    if not qid or qid == "1":
        return ""
    if qid not in _UNITS:
        try:
            e = requests.get(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json", headers=UA, timeout=15).json()
            _UNITS[qid] = list(e["entities"].values())[0]["labels"].get("en", {}).get("value", qid)
        except Exception:
            _UNITS[qid] = qid
    return _UNITS[qid]


def facts(title, limit=12):
    """['highest observed lifespan: 500 year', ...] for the Wikipedia article's Wikidata item."""
    r = requests.get("https://en.wikipedia.org/w/api.php", headers=UA, timeout=15, params={
        "action": "query", "prop": "pageprops", "ppprop": "wikibase_item", "redirects": 1,
        "titles": title, "format": "json"})
    page = next(iter(r.json().get("query", {}).get("pages", {}).values()), {})
    qid = page.get("pageprops", {}).get("wikibase_item")
    if not qid:
        return []
    e = requests.get(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json", headers=UA, timeout=20).json()
    claims = list(e["entities"].values())[0].get("claims", {})
    out = []
    for p, name in FACT_PROPS.items():
        for st in claims.get(p, [])[:2]:
            v = (st.get("mainsnak", {}).get("datavalue") or {}).get("value")
            if isinstance(v, dict) and "amount" in v:
                out.append(f"{name}: {v['amount'].lstrip('+')} {_unit(v.get('unit', '').rsplit('/', 1)[-1])}".strip())
    return out[:limit]
