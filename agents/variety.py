"""Variety: no two videos should feel like the same template.

Since July 2025 YouTube's "inauthentic content" rule removes monetisation from channels whose videos
are mass-produced or near-identical. Our videos differ in topic, footage and voices, but on 14 Nov 2026
the last 15 hooks mostly opened "Why do / Why is...", most titles opened "Why...", and the zebra-stripes
topic had been made twice. This module catches all three:
  - topic_is_repeat(): a topic too close to one already made (word overlap) is dropped;
  - hook_issue(): the hook opens the same way as most recent hooks -> the writer rewrites it;
  - pick_title(): if most recent titles open the same way, use a title option that does not.
"""
import re

from .core import DATA, read_json

_STOP = {"the", "and", "why", "how", "what", "does", "do", "is", "are", "can", "a", "an", "of", "to", "in",
         "your", "you", "it", "its", "their", "they", "this", "that", "while", "but", "don't", "doesn't"}


def _recent(n=15):
    return [h for h in (read_json(DATA / "history.json", []) or []) if h.get("title") or h.get("topic")][-n:]


def _words(t):
    out = set()
    for w in re.findall(r"[a-z']+", (t or "").lower()):
        if w not in _STOP and len(w) > 2:
            out.add(w[:-1] if w.endswith("s") and len(w) > 3 else w)
    return out


def topic_is_repeat(topic, n=120):
    """True when the topic shares most of its key words with one already made."""
    a = _words(topic)
    if len(a) < 2:
        return False
    for h in (read_json(DATA / "history.json", []) or [])[-n:]:
        if h.get("status") == "withdrawn":      # never published: free to make again, properly
            continue
        b = _words(f"{h.get('topic', '')} {h.get('title', '')}")
        if b and len(a & b) / len(a) >= 0.6:
            return True
    return False


def opener(text):
    """The shape of an opening: 'why', 'how', 'you', 'number', 'most', 'what if', or 'statement'."""
    t = (text or "").strip().lower()
    for key, pat in (("what if", r"^what if\b"), ("why", r"^why\b"), ("how", r"^how\b"),
                     ("you", r"^(you|your)\b"), ("number", r"^[\d$]|^(one|two|three|ten|a hundred|a million)\b"),
                     ("most", r"^(most|many|everyone|people)\b"), ("question", r"^(is|are|can|do|does|did|what|which)\b")):
        if re.search(pat, t):
            return key
    return "statement"


def hook_issue(hook, window=6, limit=3):
    """A rewrite instruction when this hook opens like most of the recent ones, else ''."""
    recent = [opener(h.get("hook", "")) for h in _recent(window) if h.get("hook")]
    mine = opener(hook)
    if recent.count(mine) >= limit:
        others = [o for o in ("statement", "you", "number", "most", "what if") if recent.count(o) == 0]
        return (f"the hook opens like {recent.count(mine)} of the last {len(recent)} videos ('{mine}' opening): "
                f"open differently, e.g. a {' / '.join(others[:3]) or 'bold statement'} opening, keeping it true")
    return ""


def pick_title(options, window=6, limit=4):
    """The first title option, unless most recent titles open the same way and another option does not."""
    options = [o for o in (options or []) if o]
    if not options:
        return options
    recent = [opener(h.get("title", "")) for h in _recent(window) if h.get("title")]
    first = opener(options[0])
    if recent.count(first) >= limit:
        for k, o in enumerate(options[1:], 1):
            if opener(o) != first:
                return [o] + options[:k] + options[k + 1:]
    return options
