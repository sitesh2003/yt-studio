"""QA check 6 - listen to the finished video and compare what is SAID with the script.

A voice engine can drop a word, garble a science term, or read "1.5" as "fifteen". The captions come
from the script, so they would still look right while the audio is wrong. This check transcribes the
final audio with faster-whisper (MIT licence, runs on the CPU, the model downloads once) and compares
it word by word with the narration:
  - any NUMBER that is missing or different in the audio holds the video;
  - if under 85% of the script is heard as written, the video is held;
  - smaller differences are kept as notes on the review page.
If faster-whisper is not installed, the check is skipped (and says so) rather than blocking.
"""
import difflib
import re

from .core import log

_MODEL = None
_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen " \
        "sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
NEGATIONS = {"not", "no", "never", "none", "nothing", "nobody", "neither", "nor", "cannot"}
NUMBER_WORDS = set(_ONES + _TENS[2:] + ["hundred", "thousand", "million", "billion", "point", "half"])


def available():
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


def _say(n):
    """An integer as words, the way a narrator reads it (no 'and')."""
    n = int(n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    for size, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand"), (100, "hundred")):
        if n >= size:
            rest = n % size
            return f"{_say(n // size)} {name}" + (f" {_say(rest)}" if rest else "")
    return str(n)


def norm(text):
    """Lower-case word tokens with every number spelled out, so '40' and 'forty' compare equal."""
    t = (text or "").lower().replace("%", " percent").replace("&", " and ")
    t = re.sub(r"(\d),(\d{3})", r"\1\2", t)

    def num(m):
        whole, _, frac = m.group(0).partition(".")
        out = _say(whole) if len(whole) < 13 else whole
        if frac:
            out += " point " + " ".join(_ONES[int(d)] for d in frac)
        return f" {out} "
    t = re.sub(r"\d+(?:\.\d+)?", num, t)
    t = t.replace("-", " ")
    return re.findall(r"[a-z']+", t)


def transcribe(audio_path):
    global _MODEL
    from faster_whisper import WhisperModel
    if _MODEL is None:
        _MODEL = WhisperModel("base.en", device="cpu", compute_type="int8")
    segs, _ = _MODEL.transcribe(str(audio_path), language="en", beam_size=5, vad_filter=False)
    return " ".join(s.text for s in segs)


def compare(script_text, heard_text):
    """(issues, notes, ratio) for the script versus what was heard."""
    a, b = norm(script_text), norm(heard_text)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ratio = sm.ratio()
    issues, notes = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        said, heard = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        # "one" is also a pronoun ("no one", "this one"), so on its own it is not treated as a number
        n_said = [w for w in a[i1:i2] if w in NUMBER_WORDS and w != "one"]
        n_heard = [w for w in b[j1:j2] if w in NUMBER_WORDS and w != "one"]
        neg_said = [w for w in a[i1:i2] if w in NEGATIONS or w.endswith("n't")]
        neg_heard = [w for w in b[j1:j2] if w in NEGATIONS or w.endswith("n't")]
        if neg_said != neg_heard:   # "can't" heard as "can" flips the meaning of the sentence
            issues.append(f'meaning flips: script "{said}" but the audio says "{heard or "(nothing)"}"')
        elif n_said != n_heard:
            issues.append(f'number differs: script "{said}" but the audio says "{heard or "(nothing)"}"')
        else:
            notes.append(f'"{said}" heard as "{heard}"' if said and heard else
                         f'"{said}" not heard' if said else f'extra "{heard}"')
    if ratio < 0.85:
        issues.append(f"only {ratio:.0%} of the script is heard as written")
    return issues, notes, ratio


def check(job, script):
    """Returns (issues, notes). Empty issues = the audio says what the script says."""
    if not available():
        return [], ["listening check skipped (faster-whisper not installed)"]
    try:
        heard = transcribe(job / "voice.mp3")
    except Exception as e:
        return [], [f"listening check unavailable: {str(e)[:80]}"]
    text = " ".join(s["narration"] for s in script["scenes"])
    issues, notes, ratio = compare(text, heard)
    log(f"listen: {ratio:.0%} of the script heard as written; {len(issues)} problem(s), {len(notes)} note(s)")
    return issues, notes[:8]
