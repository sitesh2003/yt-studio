"""Agents 5 and 6 - Publishing, comments and analytics through the official
YouTube APIs (free). First run opens a browser once for you to sign in to
YOUR channel; the token is kept in token.json on this PC only."""
import datetime as dt
from zoneinfo import ZoneInfo

from .core import DATA, ROOT, config, log, read_json, write_json

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/yt-analytics.readonly",
          "https://www.googleapis.com/auth/gmail.send"]       # daily report to your own inbox only


def _creds():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    tok = ROOT / "token.json"
    creds = Credentials.from_authorized_user_file(str(tok), SCOPES) if tok.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        secret = ROOT / "client_secret.json"
        if not secret.exists():
            raise RuntimeError("client_secret.json missing: see README step 3")
        creds = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES).run_local_server(
            port=0, open_browser=False, authorization_prompt_message="SIGN-IN URL: {url}")
    tok.write_text(creds.to_json(), encoding="utf-8")
    return creds


def yt():
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=_creds(), cache_discovery=False)


def next_slot():
    """Next free US Eastern slot from config, avoiding slots already used."""
    p = config()["publish"]
    used = set(read_json(DATA / "scheduled.json", []) or [])
    et = ZoneInfo("America/New_York")
    try:  # slots already taken on YouTube, whichever machine uploaded them
        used |= {dt.datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(et).isoformat()
                 for t in _scheduled_times()}
    except Exception:
        pass
    now = dt.datetime.now(et)
    for day in range(0, 30):
        d = (now + dt.timedelta(days=day)).date()
        for hhmm in p["slots_et"][:p["videos_per_day"]]:
            h, m = map(int, hhmm.split(":"))
            t = dt.datetime(d.year, d.month, d.day, h, m, tzinfo=et)
            if t > now + dt.timedelta(minutes=30) and t.isoformat() not in used:
                return t
    return now + dt.timedelta(hours=1)


def upload(job_dir, meta, when=None):
    from googleapiclient.http import MediaFileUpload
    p = config()["publish"]
    when = when or next_slot()
    if isinstance(when, str):
        when = dt.datetime.fromisoformat(when)
    body = {
        "snippet": {"title": meta["title"][:100], "description": meta["description"][:4900],
                    "tags": meta.get("tags", [])[:30], "categoryId": p["category_id"],
                    "defaultLanguage": "en", "defaultAudioLanguage": "en-US"},
        "status": {"privacyStatus": "private", "publishAt": when.astimezone(dt.timezone.utc).isoformat(),
                   "selfDeclaredMadeForKids": p["made_for_kids"],
                   "containsSyntheticMedia": p["contains_synthetic_media"]},
    }
    req = yt().videos().insert(part="snippet,status", body=body,
                               media_body=MediaFileUpload(str(job_dir / "final.mp4"), resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    vid = resp["id"]
    thumb = job_dir / meta.get("thumbnail", "thumbnail.jpg")
    if thumb.exists():
        try:  # needs a verified channel (youtube.com/verify); skipped quietly otherwise
            yt().thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb))).execute()
        except Exception as e:
            log(f"youtube: thumbnail not set ({str(e)[:80]})")
    sched =read_json(DATA / "scheduled.json", []) or []
    write_json(DATA / "scheduled.json", sched + [when.isoformat()])
    log(f"youtube: uploaded {vid}, goes public {when:%a %d %b %H:%M} ET")
    return vid, when.isoformat()


def recent_comments(limit=50):
    y = yt()
    me = y.channels().list(part="id", mine=True).execute()["items"][0]["id"]
    res = y.commentThreads().list(part="snippet", allThreadsRelatedToChannelId=me, maxResults=min(limit, 100),
                                  order="time", textFormat="plainText").execute()
    replied = set(read_json(DATA / "replied.json", []) or [])
    out = []
    for t in res.get("items", []):
        top = t["snippet"]["topLevelComment"]
        author = (top["snippet"].get("authorChannelId") or {}).get("value")
        if author == me:
            continue  # our own answer comments
        if t["snippet"].get("totalReplyCount", 0) == 0 and top["id"] not in replied:
            out.append({"id": top["id"], "text": top["snippet"]["textDisplay"][:500]})
    return out


def post_reply(parent_id, text):
    yt().comments().insert(part="snippet", body={"snippet": {"parentId": parent_id, "textOriginal": text}}).execute()
    replied = read_json(DATA / "replied.json", []) or []
    write_json(DATA / "replied.json", replied + [parent_id])


def previous_winners():
    """The latest PUBLIC video with an enquiry we haven't recapped yet, plus who answered it right.
    Returns None when there's nothing to recap (the first days, or still private)."""
    from .writer import judge_guesses
    hist = read_json(DATA / "history.json", []) or []
    cands = [h for h in hist if h.get("video_id") and h.get("question") and not h.get("recapped")
             and not h.get("weekly")]
    if not cands:
        return None
    y = yt()
    ids = ",".join(h["video_id"] for h in cands[-10:])
    status = {v["id"]: v["status"]["privacyStatus"] for v in y.videos().list(part="status", id=ids).execute().get("items", [])}
    public = [h for h in cands[-10:] if status.get(h["video_id"]) == "public"]
    if not public:
        return None
    h = public[-1]
    me = y.channels().list(part="id", mine=True).execute()["items"][0]["id"]
    res = y.commentThreads().list(part="snippet", videoId=h["video_id"], maxResults=100,
                                  order="relevance", textFormat="plainText").execute()
    comments = []
    for t in res.get("items", []):
        c = t["snippet"]["topLevelComment"]["snippet"]
        if c.get("authorChannelId", {}).get("value") != me:
            comments.append((c.get("authorDisplayName", ""), c.get("textDisplay", "")[:300]))
    winners = judge_guesses(h["question"], h.get("answer_comment", ""), comments[:80])
    log(f"youtube: recap of {h['video_id']}: {len(comments)} comments, winners {winners}")
    return {"video_id": h["video_id"], "question": h["question"],
            "answer": h.get("answer_comment", "").replace("The answer:", "").strip(), "winners": winners}


def mark_recapped(video_id):
    hist = read_json(DATA / "history.json", []) or []
    for h in hist:
        if h.get("video_id") == video_id:
            h["recapped"] = True
    write_json(DATA / "history.json", hist)


def ensure_public():
    """A video past its publish time that is still private gets switched to public.
    If YouTube refuses (new API projects can be locked to private until the audit), log it once."""
    import datetime as _dt
    hist = read_json(DATA / "history.json", []) or []
    due = [h for h in hist if h.get("video_id") and h.get("status") == "scheduled" and h.get("publish_at")
           and _dt.datetime.fromisoformat(h["publish_at"]) <= _dt.datetime.now(_dt.timezone.utc)]
    if not due:
        return
    y = yt()
    info = {v["id"]: v for v in y.videos().list(part="status", id=",".join(h["video_id"] for h in due[:50])).execute().get("items", [])}
    for h in due:
        v = info.get(h["video_id"])
        if not v:
            h["status"] = "missing"
            continue
        if v["status"]["privacyStatus"] == "public":
            h["status"] = "public"
            continue
        try:
            st = v["status"]
            st["privacyStatus"] = "public"
            st.pop("publishAt", None)
            y.videos().update(part="status", body={"id": h["video_id"], "status": st}).execute()
            h["status"] = "public"
            log(f"youtube: {h['video_id']} made public")
        except Exception as e:
            h["status"] = "locked"
            log(f"youtube: could not make {h['video_id']} public ({str(e)[:100]}) - needs the API audit")
    write_json(DATA / "history.json", hist)


def channel_summary():
    ch = yt().channels().list(part="statistics", mine=True).execute()["items"][0]["statistics"]
    return {"subscribers": ch.get("subscriberCount"), "views": ch.get("viewCount"), "videos": ch.get("videoCount")}


def post_answers():
    """Once a video is PUBLIC, post its enquiry answer as the channel's first comment (once).
    YouTube cannot comment on private videos, and apps cannot pin comments; pin it in the app."""
    hist = read_json(DATA / "history.json", []) or []
    waiting = [h for h in hist if h.get("video_id") and h.get("answer_comment") and not h.get("answered")]
    if not waiting:
        return 0
    y = yt()
    ids = ",".join(h["video_id"] for h in waiting[:50])
    status = {v["id"]: v["status"]["privacyStatus"] for v in y.videos().list(part="status", id=ids).execute().get("items", [])}
    me = y.channels().list(part="id", mine=True).execute()["items"][0]["id"]
    posted = 0
    for h in waiting:
        if status.get(h["video_id"]) != "public":
            continue
        y.commentThreads().insert(part="snippet", body={"snippet": {
            "channelId": me, "videoId": h["video_id"],
            "topLevelComment": {"snippet": {"textOriginal": h["answer_comment"]}}}}).execute()
        h["answered"] = True
        posted += 1
        log(f"youtube: answer posted on {h['video_id']} ({h['title'][:40]})")
    write_json(DATA / "history.json", hist)
    return posted


def channel_stats():
    """Per-video performance for the learning loop: views, avg % viewed, likes."""
    from googleapiclient.discovery import build
    creds = _creds()
    an = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    end = dt.date.today().isoformat()
    start = (dt.date.today() - dt.timedelta(days=90)).isoformat()
    r = an.reports().query(ids="channel==MINE", startDate=start, endDate=end, dimensions="video",
                           metrics="views,averageViewPercentage,averageViewDuration,likes,subscribersGained",
                           sort="-views", maxResults=200).execute()
    cols = [c["name"] for c in r.get("columnHeaders", [])]
    return [dict(zip(cols, row)) for row in r.get("rows", [])]


SERIES = ["Food Whys", "Ocean Whys", "Animal Whys", "Body Whys", "Everyday Whys"]


def add_to_series(video_id, series):
    """Every video joins a themed playlist, so a viewer who finishes one is offered the next."""
    series = series if series in SERIES else "Everyday Whys"
    path = DATA / "playlists.json"
    ids = read_json(path, {}) or {}
    y = yt()
    if series not in ids:
        found = None
        for pl in y.playlists().list(part="snippet", mine=True, maxResults=50).execute().get("items", []):
            if pl["snippet"]["title"] == series:
                found = pl["id"]
        if not found:
            found = y.playlists().insert(part="snippet,status", body={
                "snippet": {"title": series, "description": f"Ever Thought Why? - {series}: the surprising science, one short why at a time."},
                "status": {"privacyStatus": "public"}}).execute()["id"]
        ids[series] = found
        write_json(path, ids)
    import time
    for attempt in range(4):  # a just-created playlist can refuse items for a few seconds
        try:
            y.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": ids[series], "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()
            break
        except Exception:
            if attempt == 3:
                raise
            time.sleep(8 * (attempt + 1))
    log(f"youtube: added to playlist {series}")


def views(video_ids):
    out = {}
    ids = [v for v in video_ids if v]
    for i in range(0, len(ids), 50):
        for v in yt().videos().list(part="statistics", id=",".join(ids[i:i + 50])).execute().get("items", []):
            out[v["id"]] = int(v["statistics"].get("viewCount", 0))
    return out


def _scheduled_times():
    y = yt()
    up = y.channels().list(part="contentDetails", mine=True).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids = [i["contentDetails"]["videoId"] for i in
           y.playlistItems().list(part="contentDetails", playlistId=up, maxResults=50).execute().get("items", [])]
    return [v["status"]["publishAt"] for v in
            (y.videos().list(part="status", id=",".join(ids)).execute().get("items", []) if ids else [])
            if v["status"].get("publishAt")]


def bank():
    """The video bank, read from YouTube itself (the truth, whichever machine uploaded):
    how many uploads are still private and scheduled to go public, and how many uploads today's
    free quota still allows (resets midnight Pacific; an upload costs 1,600 of 10,000 units)."""
    y = yt()
    up = y.channels().list(part="contentDetails", mine=True).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids = [i["contentDetails"]["videoId"] for i in
           y.playlistItems().list(part="contentDetails", playlistId=up, maxResults=50).execute().get("items", [])]
    now = dt.datetime.now(dt.timezone.utc)
    pt = ZoneInfo("America/Los_Angeles")
    waiting = done = 0
    for i in range(0, len(ids), 50):
        for v in y.videos().list(part="status,snippet", id=",".join(ids[i:i + 50])).execute().get("items", []):
            pa = v["status"].get("publishAt")
            if pa and dt.datetime.fromisoformat(pa.replace("Z", "+00:00")) > now:
                waiting += 1
            pub = dt.datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
            if pub.astimezone(pt).date() == now.astimezone(pt).date():
                done += 1
    cap = config()["publish"].get("max_uploads_per_day", 5)
    return waiting, max(0, cap - done)
