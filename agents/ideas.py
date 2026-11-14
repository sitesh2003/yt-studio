"""Where topic ideas come from, beyond brainstorming: questions real people asked, and new research
written for young readers. All free, no keys, and every idea is only a STARTING POINT - the writer
always explains it in its own words and the fact-checker checks it.

- Stack Exchange (api.stackexchange.com, no key, ~300 calls a day per address): the all-time
  top-voted questions on the science, cooking and engineering sites are proven curiosity ("Why are so
  few foods blue?", "Why doesn't water burn?"). Only the question is used, as an idea; nothing is copied.
- Frontiers for Young Minds (via Crossref + OpenAlex): peer-reviewed research written for ages 8-15,
  CC BY 4.0, new articles every week - ideal for "new research, explained" on the student channel.
(Semantic Scholar's TLDR summaries were tested and left out: their licence is non-commercial.)

Results are cached for a day (data/ideas_cache.json) so a run never spends the shared quota twice.
"""
import datetime as dt
import html
import random

import requests

from .core import DATA, log, openalex_params, read_json, write_json

UA = {"User-Agent": "yt-studio-ideas/1.0 (science education channel)"}
CACHE = DATA / "ideas_cache.json"

# everyday-science sites for the main channel; school-science sites for the student channel
SITES_MAIN = ["biology", "chemistry", "physics", "cooking", "earthscience", "engineering", "astronomy", "outdoors"]
SITES_STUDENT = ["physics", "chemistry", "biology", "electronics", "earthscience", "astronomy", "matheducators", "engineering"]


def _cached(key, fetch):
    cache = read_json(CACHE, {}) or {}
    today = dt.date.today().isoformat()
    if cache.get(key, {}).get("date") == today:
        return cache[key]["items"]
    try:
        items = fetch()
    except Exception as e:
        log(f"ideas: {key} unavailable ({str(e)[:60]})")
        return (cache.get(key) or {}).get("items", [])     # yesterday's list beats nothing
    cache[key] = {"date": today, "items": items}
    write_json(CACHE, cache)
    return items


def _se(site, pages=(1, 2, 3, 4, 5, 6, 7, 8)):
    """Top-voted questions from a random page of one site (so the list changes from day to day)."""
    page = random.choice(pages)
    r = requests.get("https://api.stackexchange.com/2.3/questions", headers=UA, timeout=20, params={
        "order": "desc", "sort": "votes", "site": site, "pagesize": 30, "page": page})
    r.raise_for_status()
    return [{"q": html.unescape(q["title"]), "site": site, "votes": q.get("score", 0)}
            for q in r.json().get("items", [])
            if "$" not in q["title"]                                   # skip formula-heavy titles
            and (q["title"].strip().endswith("?") or q["title"].lower().startswith(("why", "how", "what", "is ", "can ", "does ", "do ")))]


def questions(student=False, n=14):
    """Real questions people asked, a few from each site, shuffled."""
    sites = SITES_STUDENT if student else SITES_MAIN
    pool = []
    for s in sites:
        pool += _cached(f"se:{s}", lambda s=s: _se(s))[:12]
    random.shuffle(pool)
    return pool[:n]


def _abstract(inv):
    pos = sorted((p, w) for w, ps in (inv or {}).items() for p in ps)
    return " ".join(w for _, w in pos)


def young_minds(n=8):
    """The newest Frontiers for Young Minds articles: title, DOI, a short abstract (CC BY 4.0)."""
    def fetch():
        r = requests.get("https://api.crossref.org/journals/2296-6846/works", headers=UA, timeout=30,
                         params={"sort": "published", "order": "desc", "rows": 25, "select": "title,DOI"})
        r.raise_for_status()
        out = []
        for w in r.json()["message"]["items"]:
            doi = w.get("DOI")
            ab = ""
            try:
                a = requests.get(f"https://api.openalex.org/works/doi:{doi}", headers=UA, timeout=20,
                                 params=openalex_params({"select": "abstract_inverted_index"})).json()
                ab = _abstract(a.get("abstract_inverted_index"))[:400]
            except Exception:
                pass
            out.append({"title": (w.get("title") or [""])[0], "doi": doi, "abstract": ab})
        return out
    items = _cached("fym", fetch)
    return random.sample(items, min(n, len(items))) if items else []


FEEDS = {"ScienceDaily": "https://www.sciencedaily.com/rss/top/science.xml",
         "Phys.org": "https://phys.org/rss-feed/"}


def news(n=8):
    """This week's science headlines (ScienceDaily allows headline use with credit; Phys.org asks for
    credit). Only the headline is used, as an idea; the video always cites the original paper."""
    import xml.etree.ElementTree as ET

    def fetch():
        out = []
        for name, url in FEEDS.items():
            try:
                r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (yt-studio ideas)"}, timeout=20)
                for it in ET.fromstring(r.content).iter("item"):
                    t = html.unescape((it.findtext("title") or "").strip())
                    if t:
                        out.append({"title": t, "via": name})
            except Exception as e:
                log(f"ideas: {name} feed unavailable ({str(e)[:50]})")
        return out
    items = _cached("news", fetch)
    return random.sample(items, min(n, len(items))) if items else []


def brief(student=False):
    """The block the topic planner reads."""
    qs = questions(student)
    lines = ["REAL QUESTIONS people asked online (proven curiosity). Use one when it fits the channel and can",
             "be answered truly and simply; rephrase it in your own words, never copy:"]
    lines += [f"- {q['q']}" for q in qs] or ["- (none today)"]
    lines += ["", "THIS WEEK'S SCIENCE HEADLINES (ideas only: a video built on one must explain the underlying",
              "science truly, and the fact-checker and sources check the claim itself, never the headline):"]
    lines += [f"- {x['title']} (via {x['via']})" for x in news()] or ["- (none today)"]
    if student:
        lines += ["", "NEW RESEARCH written for young readers (Frontiers for Young Minds, peer-reviewed, CC BY 4.0).",
                  "A good NEW RESEARCH topic; the paper itself becomes the cited source:"]
        lines += [f"- {a['title']} (doi:{a['doi']}): {a['abstract'][:200]}" for a in young_minds()] or ["- (none today)"]
    return "\n".join(lines)
