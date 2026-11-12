"""The video bank: finished, checked videos wait HERE - not on YouTube.

A video reaches the bank only after every check (facts, footage, quality review, last accuracy
audit). It is kept as files on the repo's "video-bank" GitHub Release (free storage). The publisher
uploads from the bank to YouTube only close to each public slot - three a day - so a wrong video
never touches the channel and nothing ever has to be deleted there.

data/bank.json lists what is waiting, oldest first.
"""
import datetime as dt
import os

import requests

from .core import DATA, log, read_json, write_json

REPO = os.environ.get("GITHUB_REPOSITORY", "sitesh2003/yt-studio")
TAG = "video-bank"
PATH = DATA / "bank.json"


def available():
    return bool(os.environ.get("GITHUB_TOKEN"))


def _h(extra=None):
    h = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
    h.update(extra or {})
    return h


def _release():
    r = requests.get(f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}", headers=_h(), timeout=30)
    if r.status_code == 404:
        r = requests.post(f"https://api.github.com/repos/{REPO}/releases", headers=_h(), timeout=30, json={
            "tag_name": TAG, "name": "Video bank",
            "body": "Finished, checked videos waiting for their public slot. Managed automatically."})
    r.raise_for_status()
    return r.json()


def items():
    return read_json(PATH, []) or []


def store(job, meta):
    """Upload final.mp4, the thumbnail and meta.json of a finished video to the bank."""
    rel = _release()
    up = rel["upload_url"].split("{")[0]
    assets = {}
    files = [("mp4", job / "final.mp4", "video/mp4"),
             ("jpg", job / meta.get("thumbnail", "thumbnail.jpg"), "image/jpeg"),
             ("json", job / "meta.json", "application/json")]
    for ext, path, ctype in files:
        if not path.exists():
            continue
        with open(path, "rb") as fh:
            r = requests.post(up, params={"name": f"{job.name}.{ext}"}, data=fh,
                              headers=_h({"Content-Type": ctype}), timeout=300)
        r.raise_for_status()
        assets[ext] = r.json()["id"]
    bank = items()
    bank.append({"job": job.name, "title": meta.get("title", ""), "assets": assets,
                 "series": meta.get("series", ""), "stored": dt.datetime.now(dt.timezone.utc).isoformat()})
    write_json(PATH, bank)
    log(f"bank: stored '{meta.get('title', job.name)}' ({len(bank)} waiting)")


def fetch(item, into):
    """Download a banked video's files into a folder, ready for youtube.upload()."""
    into.mkdir(parents=True, exist_ok=True)
    names = {"mp4": "final.mp4", "jpg": "thumbnail.jpg", "json": "meta.json"}
    for ext, aid in item["assets"].items():
        r = requests.get(f"https://api.github.com/repos/{REPO}/releases/assets/{aid}", timeout=300,
                         headers=_h({"Accept": "application/octet-stream"}), stream=True)
        r.raise_for_status()
        with open(into / names[ext], "wb") as fh:
            for chunk in r.iter_content(1 << 16):
                fh.write(chunk)
    return into


def remove(item):
    """After the video is safely on YouTube, drop it from the bank."""
    for aid in item["assets"].values():
        try:
            requests.delete(f"https://api.github.com/repos/{REPO}/releases/assets/{aid}", headers=_h(), timeout=30)
        except Exception:
            pass
    write_json(PATH, [b for b in items() if b["job"] != item["job"]])
