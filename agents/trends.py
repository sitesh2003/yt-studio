"""Agent 1 - Trends: what is working in the niche for US viewers right now.

Uses the free YouTube Data API key. search.list costs 100 quota units of the
10,000 free per day, so this runs a handful of searches, not hundreds.
"""
import datetime as dt
import re

import requests

from .core import DATA, config, key, log, write_json

API = "https://www.googleapis.com/youtube/v3"


def _get(path, **params):
    params["key"] = key("YOUTUBE_API_KEY")
    r = requests.get(f"{API}/{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def scan(days=30, per_keyword=15):
    if not key("YOUTUBE_API_KEY"):
        log("trends: no YOUTUBE_API_KEY, skipping (scripts will still work)")
        return []
    cfg = config()["channel"]
    since = (dt.datetime.utcnow() - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids = {}
    for kw in cfg["seed_keywords"]:
        res = _get("search", part="snippet", q=kw + " #shorts", type="video", order="viewCount",
                   regionCode="US", relevanceLanguage="en", videoDuration="short",
                   publishedAfter=since, maxResults=per_keyword)
        for it in res.get("items", []):
            ids[it["id"]["videoId"]] = kw
    if not ids:
        return []
    rows = []
    id_list = list(ids)
    for i in range(0, len(id_list), 50):
        res = _get("videos", part="snippet,statistics,contentDetails", id=",".join(id_list[i:i + 50]))
        for v in res.get("items", []):
            st = v.get("statistics", {})
            pub = dt.datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
            age = max((dt.datetime.now(dt.timezone.utc) - pub).days, 1)
            views = int(st.get("viewCount", 0))
            m = re.match(r"PT(?:(\d+)M)?(?:(\d+)S)?", v.get("contentDetails", {}).get("duration", ""))
            secs = int(m[1] or 0) * 60 + int(m[2] or 0) if m else 0
            rows.append({
                "id": v["id"], "title": v["snippet"]["title"], "channel": v["snippet"]["channelTitle"],
                "views": views, "likes": int(st.get("likeCount", 0)), "comments": int(st.get("commentCount", 0)),
                "views_per_day": round(views / age), "age_days": age, "secs": secs, "keyword": ids[v["id"]],
            })
    rows.sort(key=lambda r: r["views_per_day"], reverse=True)
    write_json(DATA / "trends.json", {"scanned": dt.datetime.now().isoformat(), "videos": rows})
    log(f"trends: {len(rows)} videos scanned, top: {rows[0]['title'][:60]!r}" if rows else "trends: none found")
    return rows
