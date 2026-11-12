"""The last accuracy check - with a second opinion before anything is called false.

Used twice:
  * before_bank(meta)  BEFORE a finished video enters the bank (the normal path): an overstated
                       title or description is fixed in place; a wrong spoken line means the video
                       is NOT banked and a corrected remake is queued. Nothing reaches YouTube.
  * audit_scheduled()  safety net for anything already scheduled on YouTube that was never
                       audited (older uploads): fix in place, or delete a never-public video.
"""
import datetime as dt

from .core import DATA, add_lesson, llm_json, log, read_json, write_json


def judge(title, description, spoken):
    """Returns {"status": "ok" | "meta" | "false" | "off_topic", ...fixes and the correction}."""
    first = (description or "").split("\n\n")[0]
    out = llm_json(f"""You are the last accuracy check before a science Short goes public. Be strict but fair:
popular simplifications are fine; overstatements, myths and false claims are not.
Only judge FACTS: hashtags, emojis and formatting are fine and never a reason to mark something not ok.
Check the PREMISE first: the question the video is built on, and every contrast between two things
("X sticks while Y slides off", "A has none while B has many"). If either side of a contrast is false
(e.g. an animal said to fail at something it actually does well), that is narration_false.
TITLE: {title}
DESCRIPTION: {first}
NARRATION (spoken, cannot be edited): {spoken}
Return JSON: {{"title_ok": true or false, "description_ok": true or false,
 "fixed_title": "accurate title, same curiosity, max 70 chars, Title Case, ends with 2 fitting emojis",
 "fixed_description": "accurate 1-2 lines, no hashtags",
 "narration_false": true only if the narration states something actually FALSE or clearly misleading,
 "false_sentence": "if narration_false: the exact sentence from the narration that is wrong",
 "correct_version": "if narration_false: what is actually true, in one or two plain sentences",
 "why": "one line"}}""")
    if out.get("narration_false"):
        # SECOND OPINION: an auditor can be wrong too (12 Nov it "corrected" a true line about maple
        # sap). A separate check must agree, and must confirm the correction before it is learned.
        second = llm_json(f"""Independent science check. Video title: "{title}".
A reviewer says this spoken line is false or misleading: "{out.get('false_sentence', '')}"
Reviewer's proposed truth: "{out.get('correct_version', '')}"
Judge carefully and on your own:
- "line_problem": "false" if the line is scientifically false, "off_topic" if it is true but does
  not belong in a video with this title, "fine" if it is true and on topic.
- "correction_accurate": true only if the reviewer's proposed truth is itself accurate.
- "truth": one or two plain sentences that are definitely accurate about this line.
Return JSON: {{"line_problem": "false|off_topic|fine", "correction_accurate": true or false, "truth": "..."}}""")
        verdict = second.get("line_problem", "fine")
        if verdict in ("false", "off_topic"):
            out["correct_version"] = (out.get("correct_version") if second.get("correction_accurate")
                                      else second.get("truth", ""))
            if verdict == "off_topic":
                out["why"] = "the line is true but has nothing to do with this video's subject"
                out["correct_version"] = "Keep every line about this video's own subject. " + (second.get("truth") or "")
            out["status"] = verdict
            return out
        out["overruled"] = True
    out["status"] = "ok" if (out.get("title_ok", True) and out.get("description_ok", True)) else "meta"
    return out


def queue_remake(topic, title, out, ref=""):
    remakes = read_json(DATA / "remakes.json", []) or []
    remakes.append({"topic": topic or title, "pulled": ref, "title": title,
                    "false_sentence": out.get("false_sentence", ""),
                    "correct_version": out.get("correct_version", ""), "why": out.get("why", ""), "tries": 0})
    write_json(DATA / "remakes.json", remakes)
    if out.get("status") == "false":  # only a confirmed falsehood becomes a lesson
        add_lesson("false_line", f"said \"{out.get('false_sentence', '')}\" but {out.get('correct_version', '')}")
    else:
        add_lesson("off_topic", f"a video about '{title}' drifted into an unrelated line: \"{out.get('false_sentence', '')}\"")


def fixed_description(description, out):
    parts = description.split("\n\n", 1)
    tags = " ".join(w for w in parts[0].split() if w.startswith("#"))
    return out["fixed_description"] + (" " + tags if tags else "") + ("\n\n" + parts[1] if len(parts) > 1 else "")


def before_bank(meta):
    """True if the video may enter the bank (title/description fixed in place if needed)."""
    out = judge(meta.get("title", ""), meta.get("description", ""), meta.get("narration") or meta.get("hook", ""))
    if out["status"] in ("false", "off_topic"):
        queue_remake(meta.get("topic"), meta.get("title", ""), out)
        log(f"audit: not banked - wrong line \"{out.get('false_sentence', '')}\"; corrected remake queued")
        return False
    if out["status"] == "meta":
        if not out.get("title_ok", True) and out.get("fixed_title"):
            add_lesson("title", f"title '{meta['title']}' overstated: {out.get('why', '')}")
            meta["title"] = out["fixed_title"][:100]
        if not out.get("description_ok", True) and out.get("fixed_description"):
            meta["description"] = fixed_description(meta["description"], out)
        log(f"audit: corrected before banking -> '{meta['title']}'")
    meta["audited"] = True
    return True


def audit_scheduled():
    """Safety net for videos already scheduled on YouTube that were never audited."""
    from .youtube import yt
    done = set(read_json(DATA / "audited.json", []) or [])
    hist = {h["video_id"]: h for h in (read_json(DATA / "history.json", []) or []) if h.get("video_id")}
    y = yt()
    now = dt.datetime.now(dt.timezone.utc)
    actions, pulled = [], False
    for vid, h in hist.items():
        if vid in done or h.get("audited"):
            continue
        items = y.videos().list(part="snippet,status", id=vid).execute().get("items", [])
        if not items:
            continue
        v = items[0]
        pa = v["status"].get("publishAt")
        if not pa or dt.datetime.fromisoformat(pa.replace("Z", "+00:00")) <= now:
            done.add(vid)  # already public (or not scheduled): nothing left to protect
            continue
        sn = v["snippet"]
        out = judge(sn["title"], sn["description"], h.get("narration") or h.get("hook", ""))
        if out["status"] in ("false", "off_topic"):
            y.videos().delete(id=vid).execute()   # never public, so nothing is lost
            queue_remake(h.get("topic"), sn["title"], out, vid)
            actions.append(f"Deleted before going public: '{sn['title']}'. Wrong line: "
                           f"\"{out.get('false_sentence', '?')}\". Correct: {out.get('correct_version', '')} "
                           "A corrected remake is queued.")
            pulled = True
        elif out["status"] == "meta":
            body = {"title": sn["title"], "description": sn["description"],
                    "categoryId": sn.get("categoryId", "28"), "tags": sn.get("tags", [])}
            if not out.get("title_ok", True) and out.get("fixed_title"):
                body["title"] = out["fixed_title"][:100]
            if not out.get("description_ok", True) and out.get("fixed_description"):
                body["description"] = fixed_description(sn["description"], out)
            y.videos().update(part="snippet", body={"id": vid, "snippet": body}).execute()
            add_lesson("title", f"title '{sn['title']}' overstated: {out.get('why', '')}")
            actions.append(f"Corrected before going public: '{sn['title']}' -> '{body['title']}' ({out.get('why', '')})")
        elif out.get("overruled"):
            actions.append(f"Audit query on '{sn['title']}' overruled by a second check (line is accurate).")
        done.add(vid)
    write_json(DATA / "audited.json", sorted(done))
    for a in actions:
        log("health: " + a)
    audit_scheduled.pulled = pulled
    return actions
