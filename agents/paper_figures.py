"""Agent 4f - Figures from the open-access papers behind a fact (17 Nov 2026, owner: "use open source
publications ... collect those images and use those images in our videos").

Europe PMC indexes millions of open-access papers with their licence. Only papers whose OWN licence
statement (read from the full text, not just the search index) is CC BY or CC0 are used: the channels
are monetised, so non-commercial (NC), no-derivatives (ND) and share-alike (SA) licences are refused,
the same rule as agents/visuals.py uses for photos. Every figure carries its credit line
("Figure: Smith et al., PLOS ONE 2021, CC BY 4.0"), which is burned into the frame and put in the
description. Free, no key."""
import re
import time
from pathlib import Path

import requests

from .core import log

API = "https://www.ebi.ac.uk/europepmc/webservices/rest"
IMG = "https://pmc.ncbi.nlm.nih.gov/articles/instance/{num}/bin/{href}"
UA = {"User-Agent": "yt-studio-research/1.0 (open-access figure reuse, CC BY/CC0 only)"}
STOP = set("a an the of in on to and or for with by from is are was were be as at it its this that these "
           "those your you our we they their why how what when does do did can into than then so not no "
           "but if about more most very much many one two three".split())


def _words(text):
    return {w for w in re.findall(r"[a-z][a-z\-]{2,}", (text or "").lower()) if w not in STOP}


def licence_of(xml):
    """('CC BY 4.0' | 'CC0' | None, reason). Read from the paper's own <license> block."""
    blk = " ".join(re.findall(r"<license\b.*?</license>", xml, re.S)) or " ".join(re.findall(r"<permissions\b.*?</permissions>", xml, re.S))
    low = blk.lower()
    urls = re.findall(r"creativecommons\.org/(licenses|publicdomain)/([a-z\-]+)/?([\d.]*)", low)
    if any(k in ("by-nc", "by-nc-sa", "by-nc-nd", "by-nd", "by-sa") for _, k, _ in urls) or re.search(r"non-?commercial|no derivatives|sharealike|share alike", low):
        return None, "licence forbids commercial use, changes or needs share-alike"
    for kind, k, ver in urls:
        if kind == "publicdomain" and k in ("zero", "mark"):
            return "CC0", "public domain dedication"
        if k == "by":
            return f"CC BY {ver}".strip(), "attribution only"
    if "cc by" in low and "nc" not in low:
        return "CC BY", "attribution only (stated in text)"
    return None, "no open licence found in the paper"


def search(query, n=8):
    q = f'({query}) AND OPEN_ACCESS:y AND (LICENSE:"cc by" OR LICENSE:"cc0") AND HAS_FT:y'
    for attempt in range(4):   # Europe PMC answers 503 now and then
        r = requests.get(f"{API}/search", params={"query": q, "format": "json", "resultType": "core",
                                                   "pageSize": n}, headers=UA, timeout=30)
        if r.status_code < 500:
            break
        time.sleep(3 * (attempt + 1))
    r.raise_for_status()
    return [x for x in r.json().get("resultList", {}).get("result", []) if x.get("pmcid")]


def figures_of(paper):
    """Every figure of one paper, with its credit, if the paper's own licence allows reuse."""
    pmcid = paper["pmcid"]
    r = requests.get(f"{API}/{pmcid}/fullTextXML", headers=UA, timeout=40)
    if r.status_code != 200:
        return [], "no full text"
    xml = r.text
    lic, why = licence_of(xml)
    if not lic:
        return [], why
    first = (paper.get("authorList", {}).get("author") or [{}])[0]
    who = first.get("lastName") or (paper.get("authorString") or "Unknown").split(",")[0].split()[-1]
    many = len(paper.get("authorList", {}).get("author") or []) > 1 or "," in (paper.get("authorString") or "")
    journal = (paper.get("journalInfo", {}).get("journal", {}) or {}).get("medlineAbbreviation") or \
              (paper.get("journalInfo", {}).get("journal", {}) or {}).get("title") or ""
    credit = f"Figure: {who}{' et al.' if many else ''}, {journal} {paper.get('pubYear', '')}, {lic}"
    out = []
    for fig in re.findall(r"<fig\b.*?</fig>", xml, re.S):
        # the figure's own image is its <graphic>; other links in a figure (figshare, DOIs) are not pictures
        hrefs = re.findall(r'<graphic\b[^>]*xlink:href="([^"]+)"', fig) or \
                [h for h in re.findall(r'xlink:href="([^"]+)"', fig) if not h.startswith("http")]
        if not hrefs:
            continue
        href = hrefs[0]
        if not re.search(r"\.(jpe?g|png|gif|webp|tiff?)$", href, re.I):
            href += ".jpg"
        label = re.sub(r"<[^>]+>", "", (re.findall(r"<label>(.*?)</label>", fig, re.S) or [""])[0]).strip()
        cap = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", (re.findall(r"<caption>(.*?)</caption>", fig, re.S) or [""])[0])).strip()
        out.append({"pmcid": pmcid, "doi": paper.get("doi"), "title": paper.get("title"), "label": label,
                    "caption": cap, "url": IMG.format(num=pmcid[3:], href=href), "licence": lic, "credit": credit,
                    "source": f"https://europepmc.org/article/PMC/{pmcid}"})
    return out, f"{lic}: {len(out)} figure(s)"


def find(line, query=None, n_papers=6, top=3):
    """The figures whose captions best match a narration line. A figure must share at least two
    content words with the line to count (a vision check decides the final use)."""
    want = _words(line)
    cands = []
    for paper in search(query or " ".join(sorted(want, key=len, reverse=True)[:4]), n_papers):
        try:
            figs, why = figures_of(paper)
        except Exception as e:
            log(f"paper figures: {paper['pmcid']} skipped ({type(e).__name__})")
            continue
        log(f"paper figures: {paper['pmcid']} {why}")
        for f in figs:
            cap = want & _words(f["caption"])           # the figure's own caption decides
            title = (want & _words(f["title"])) - cap      # the paper's title only breaks ties
            f["score"] = len(cap) + 0.5 * len(title)
            f["matched"] = sorted(cap)
            if len(cap) >= 2:
                cands.append(f)
        time.sleep(0.3)
    cands.sort(key=lambda f: -f["score"])
    return cands[:top]


_BUNDLES = {}


def download(fig, path):
    """The PMC image server refuses scripts (403), so figures come from Europe PMC's official API, which
    returns all of a paper's figures as one zip (cached per paper for this run)."""
    import io
    import zipfile
    pmcid = fig["pmcid"]
    if pmcid not in _BUNDLES:
        r = requests.get(f"{API}/{pmcid}/supplementaryFiles", headers=UA, timeout=90)
        if r.status_code != 200:
            raise RuntimeError(f"figure bundle failed ({r.status_code})")
        _BUNDLES[pmcid] = zipfile.ZipFile(io.BytesIO(r.content))
    z = _BUNDLES[pmcid]
    name = fig["url"].rsplit("/", 1)[-1]
    stem = re.sub(r"(\.(jpe?g|png|gif|webp|tiff?))+$", "", name, flags=re.I)
    pics = [n for n in z.namelist() if n.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
    pick = [n for n in pics if n.rsplit("/", 1)[-1] == name] or \
           [n for n in pics if re.sub(r"(\.(jpe?g|png|gif|webp|tiff?))+$", "", n.rsplit("/", 1)[-1], flags=re.I) == stem]
    pick.sort(key=lambda n: not n.lower().endswith((".jpg", ".jpeg")))   # a JPEG first
    if not pick:
        raise RuntimeError(f"{name} not in the paper's figure bundle")
    Path(path).write_bytes(z.read(pick[0]))
    return path
