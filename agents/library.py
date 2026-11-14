"""Agent 8 - The library: everything the channel has verified, kept and reusable.

Every finished video adds its verified claims and its open-access sources to data/library.json, and
research/LIBRARY.md is rebuilt as a readable index (title, the claims it makes, the papers behind them).
It is the channel's memory of what it knows and how it knows it:
- the weekly long video researches FROM it first (find() returns what we already verified on a topic);
- the comment replier and future videos can reuse a checked source instead of searching again;
- the index is a public, honest record of our sources (a website can be built from it later).
"""
import datetime as dt
import re

from .core import CHANNEL, DATA, ROOT, read_json, write_json

PATH = DATA / "library.json"
INDEX = ROOT / "research" / ("LIBRARY.md" if CHANNEL == "main" else f"LIBRARY_{CHANNEL}.md")


def _words(t):
    """Word stems (first 5 letters, plural s dropped), so 'owl' meets 'owls' and 'silent' meets 'silence'."""
    out = set()
    for w in re.findall(r"[a-z]{3,}", (t or "").lower()):
        w = w[:-1] if len(w) > 3 and w.endswith("s") else w
        out.add(w[:5])
    return out - {"the", "and", "why", "how", "what", "with", "that", "this", "from", "your", "their"}


def add(job, meta):
    lib = read_json(PATH, []) or []
    if any(e.get("job") == job for e in lib):
        return
    lib.append({"job": job, "date": dt.date.today().isoformat(), "title": meta.get("title"),
                "topic": meta.get("topic"), "series": meta.get("series"), "weekly": bool(meta.get("weekly")),
                "claims": [c for c in (meta.get("fact_check") or []) if isinstance(c, str)][:12],
                "sources": [{"cite": s.get("cite"), "doi": s.get("doi"), "claim": s.get("claim")}
                            for s in (meta.get("sources") or [])]})
    write_json(PATH, lib)
    write_index(lib)


def find(query, n=8):
    """Library entries most related to a query (shared words in title, topic, claims, sources)."""
    q = _words(query)
    scored = []
    for e in read_json(PATH, []) or []:
        text = " ".join([e.get("title") or "", e.get("topic") or ""] + e.get("claims", []) +
                        [s.get("claim") or "" for s in e.get("sources", [])])
        s = len(q & _words(text))
        if s:
            scored.append((s, e))
    return [e for _, e in sorted(scored, key=lambda x: -x[0])[:n]]


def write_index(lib=None):
    lib = lib if lib is not None else (read_json(PATH, []) or [])
    lines = ["# Ever Thought Why? - the library",
             "",
             "Every video, the claims it makes, and the open-access research behind them. Built automatically by",
             "agents/library.py; a source is listed only if its abstract was checked to support the claim.",
             ""]
    for e in sorted(lib, key=lambda e: e.get("date", ""), reverse=True):
        lines.append(f"## {e.get('title') or e.get('topic')}")
        lines.append(f"*{e.get('date')} · {e.get('series') or ''}{' · weekly episode' if e.get('weekly') else ''}*")
        lines.append("")
        for c in e.get("claims", [])[:8]:
            lines.append(f"- {c}")
        if e.get("sources"):
            lines.append("")
            lines.append("Sources:")
            for s in e["sources"]:
                lines.append(f"- {s.get('cite')} — supports: {s.get('claim')}")
        lines.append("")
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text("\n".join(lines), encoding="utf-8")
