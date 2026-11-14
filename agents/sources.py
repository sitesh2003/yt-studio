"""Agent 3b - Real, open research behind every video, shown to viewers.

For the video's key claims it searches OpenAlex (a free, open index of 250M+ scholarly works; no key)
for OPEN-ACCESS papers that have an abstract, then the AI reads each abstract and keeps a paper only
if the abstract itself directly supports the claim. A citation that does not support the claim is
worse than none, so when nothing passes, the video simply carries no citation.

The verified sources go into the description and under the answer comment ("Sources: ..."), and the
comment replier can point to them. Shorts do not make links clickable, so each one is written as
"Authors (year), Journal. doi:..." which anyone can paste into a search.
"""
import requests

from .core import llm_json, log

API = "https://api.openalex.org/works"
UA = {"User-Agent": "yt-studio-sources/1.0"}


def _abstract(inv):
    """OpenAlex stores abstracts as {word: [positions]}; rebuild the text."""
    if not inv:
        return ""
    pos = sorted((p, w) for w, ps in inv.items() for p in ps)
    return " ".join(w for _, w in pos)


def _search(query, n=6):
    r = requests.get(API, params={"search": query[:200], "per-page": n,
                                  "filter": "is_oa:true,has_abstract:true,type:article,is_retracted:false"},
                     headers=UA, timeout=30)
    r.raise_for_status()
    out = []
    for w in r.json().get("results", []):
        src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
        authors = [a["author"]["display_name"] for a in w.get("authorships", [])[:3] if a.get("author")]
        out.append({"title": w.get("display_name") or "", "year": w.get("publication_year"),
                    "doi": (w.get("doi") or "").replace("https://doi.org/", ""), "journal": src,
                    "authors": authors, "cited": w.get("cited_by_count", 0),
                    "abstract": _abstract(w.get("abstract_inverted_index"))[:1500]})
    return [p for p in out if p["doi"] and p["abstract"]]


def cite(p):
    who = p["authors"][0].split()[-1] + (" et al." if len(p["authors"]) > 1 else "") if p["authors"] else "Authors"
    return f"{who} ({p['year']}), {p['journal'] or 'journal'}. doi:{p['doi']}"


def find(script, max_sources=3):
    """Verified open-access sources for the script's key claims: [{claim, cite, doi, ...}]."""
    claims = [c for c in (script.get("fact_check") or []) if isinstance(c, str)][:6]
    if not claims:
        return []
    plan = llm_json(f"""These are the factual claims in a short science video titled "{(script.get('title_options') or [''])[0]}":
{claims}
Pick the 3 claims that most need a scientific source (the core explanation and any surprising number),
and for each write ONE search query of 3-7 plain scientific keywords that a research-paper index would
match (no question words). Return JSON: {{"items": [{{"claim": "...", "query": "..."}}]}}""")
    found, seen = [], set()
    for it in (plan.get("items") or [])[:3]:
        try:
            papers = [p for p in _search(it.get("query", "")) if p["doi"] not in seen]
        except Exception as e:
            log(f"sources: search failed ({str(e)[:60]})")
            continue
        if not papers:
            continue
        verdict = llm_json(f"""Claim from a science video: "{it.get('claim')}"
Below are open-access papers with their abstracts. Pick the ONE paper whose ABSTRACT directly supports
the claim (it states or clearly shows the same thing). Be strict: same general topic is NOT enough,
and do not use anything you know beyond the abstract. If none directly supports it, answer 0.
{[{"n": k + 1, "title": p["title"], "year": p["year"], "abstract": p["abstract"]} for k, p in enumerate(papers)]}
Return JSON: {{"best": number (0 if none), "why": "the sentence in the abstract that supports the claim"}}""")
        try:
            b = int(verdict.get("best") or 0)
        except (TypeError, ValueError):
            b = 0
        if 1 <= b <= len(papers):
            p = papers[b - 1]
            seen.add(p["doi"])
            found.append({"claim": it.get("claim"), "cite": cite(p), "doi": p["doi"], "title": p["title"],
                          "why": str(verdict.get("why", ""))[:300]})
            log(f"sources: {cite(p)} supports \"{str(it.get('claim'))[:60]}\"")
        if len(found) >= max_sources:
            break
    if not found:
        log("sources: no open paper directly supports the claims; the video carries no citation")
    return found


def block(sources):
    """The 'Sources:' text for a description or comment, or '' when there are none."""
    return ("Sources (open-access research):\n" + "\n".join(f"- {s['cite']}" for s in sources)) if sources else ""
