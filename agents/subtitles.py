"""Exact English captions for YouTube, from the narrator's own word timings.

YouTube writes automatic captions by guessing from the audio, and its auto-dubbing translates from
that guess. We already know every word and when it is said, so we upload the real thing: a caption
file (SRT) whose words are the SCRIPT's words (with its punctuation and spelling of science terms) and
whose times are the voice engine's. A new cue starts at every pause (the end of a sentence) or after
about 7 words, so each line reads like a subtitle a person made.
"""
import difflib
import re

from .core import log


def _norm(w):
    return re.sub(r"[^a-z0-9']", "", (w or "").lower())


def _ts(sec):
    ms = int(round(max(0.0, sec) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def build(words, script, max_words=7, pause=0.3):
    """SRT text. words = [{start, end, text}] from voice.narrate; script = the scenes it read."""
    if not words:
        return ""
    tokens = " ".join(s.get("narration", "") for s in script.get("scenes", [])).split()
    a, b = [_norm(t) for t in tokens], [_norm(w["text"]) for w in words]
    shown = [w["text"] for w in words]
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):          # matched word: show it as the script wrote it
            shown[blk.b + k] = tokens[blk.a + k]
    def left_in_sentence(j):   # words from j up to the end of the script sentence (or a real pause)
        n = 1
        while (j + n < len(words) and not re.search(r"[.?!][\"')]*$", shown[j + n - 1])
               and words[j + n]["start"] - words[j + n - 1]["end"] <= pause):
            n += 1
        return n

    cues, cur = [], []
    for j, w in enumerate(words):
        # a new line after every sentence end in the SCRIPT (voice-engine timings can run past trimmed
        # audio and hide the pause), and at any real pause
        gap = cur and (w["start"] - words[cur[-1]]["end"] > pause or re.search(r"[.?!][\"')]*$", shown[cur[-1]]))
        # a long line breaks after max_words, unless only 1-3 words of the sentence are left
        full = cur and len(cur) >= max_words and left_in_sentence(j) > 3
        if gap or full:
            cues.append(cur)
            cur = []
        cur.append(j)
    if cur:
        cues.append(cur)
    out = []
    for n, c in enumerate(cues, 1):
        start, end = words[c[0]]["start"], words[c[-1]]["end"]
        if n < len(cues):
            end = min(end + 0.25, words[cues[n][0]]["start"])
        out.append(f"{n}\n{_ts(start)} --> {_ts(end)}\n{' '.join(shown[j] for j in c)}\n")
    return "\n".join(out)


def upload(yt, video_id, srt):
    """captions.insert (400 quota units). A failure never stops a publish."""
    if not srt:
        return False
    try:
        from googleapiclient.http import MediaInMemoryUpload
        yt.captions().insert(part="snippet", body={"snippet": {
            "videoId": video_id, "language": "en", "name": "English", "isDraft": False}},
            media_body=MediaInMemoryUpload(srt.encode("utf-8"), mimetype="application/octet-stream")).execute()
        log("youtube: exact English captions uploaded")
        return True
    except Exception as e:
        log(f"youtube: captions not uploaded ({str(e)[:100]})")
        return False
