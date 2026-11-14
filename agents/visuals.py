"""Agent 4b - Footage that actually shows what the narrator is saying.

For every scene: search Pixabay videos and photos with several queries, drop junk (green
screen, AI-generated, low quality, already used), then SHOW the AI the preview frames of the
best candidates next to the narration and let it pick the one that fits. If nothing fits, it
falls back to a matching photo with a slow zoom, and only then to a plain moving gradient.
"""
import io
import re

import requests
from PIL import Image

from .core import config, key, llm_json, log, run

BANNED = {"green screen", "greenscreen", "chroma", "chroma key", "watermark", "text", "logo",
          "template", "mockup", "screensaver", "intro", "countdown", "glitch"}


def _vertical():
    f = config()["format"]
    return f["height"] > f["width"]


def _tags(h):
    return {t.strip().lower() for t in h.get("tags", "").split(",") if t.strip()}


def _ok(h):
    tags = _tags(h)
    blob = " ".join(tags) + " " + (h.get("description") or "").lower()
    return (not h.get("isLowQuality") and not h.get("isAiGenerated")
            and not any(b in blob for b in BANNED))


def _video_candidates(query):
    r = _get("https://pixabay.com/api/videos/",
                     params={"key": key("PIXABAY_API_KEY"), "q": query[:100], "per_page": 20,
                             "safesearch": "true", "video_type": "film"}, timeout=30)
    r.raise_for_status()
    out = []
    for h in r.json().get("hits", []):
        if not _ok(h):
            continue
        f = next((h["videos"].get(s) for s in ("large", "medium")
                  if (h["videos"].get(s) or {}).get("url") and h["videos"][s].get("height", 0) >= 720), None)
        thumb = (h["videos"].get("tiny") or h["videos"].get("small") or {}).get("thumbnail")
        if f and thumb:
            portrait = f.get("height", 0) > f.get("width", 1)
            out.append({"kind": "video", "id": ("v", h["id"]), "url": f["url"], "thumb": thumb,
                        "user": h.get("user", "Pixabay"), "tags": h.get("tags", ""),
                        "fit": True})  # landscape is blur-filled now, not cropped
    return out


def _photo_candidates(query):
    r = _get("https://pixabay.com/api/",
                     params={"key": key("PIXABAY_API_KEY"), "q": query[:100], "image_type": "photo",
                             "orientation": "vertical" if _vertical() else "horizontal",
                             "min_height": 1600 if _vertical() else 1000, "safesearch": "true",
                             "per_page": 12}, timeout=30)
    r.raise_for_status()
    return [{"kind": "photo", "id": ("p", h["id"]), "url": h["largeImageURL"], "thumb": h["webformatURL"],
             "user": h.get("user", "Pixabay"), "tags": h.get("tags", ""), "fit": True}
            for h in r.json().get("hits", []) if _ok(h) and h.get("largeImageURL")]


UA = {"User-Agent": "yt-studio/1.0 (https://github.com/sitesh2003/yt-studio)"}
# Only licences that allow commercial use with at most a credit. Never share-alike (SA),
# non-commercial (NC) or no-derivatives (ND): a video is a derivative work.
_OK_LICENCES = ("public domain", "cc0", "cc by 2.0", "cc by 2.5", "cc by 3.0", "cc by 4.0", "pdm")


def _commons_candidates(query):
    """Wikimedia Commons photos: the specific plants, animals and foods stock sites lack."""
    import re
    r = _get("https://commons.wikimedia.org/w/api.php", params={
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": f"{query[:80]} filetype:bitmap", "gsrlimit": 15, "prop": "imageinfo",
        "iiprop": "url|extmetadata|size", "iiurlwidth": 1280})
    out = []
    for p in (r.json().get("query") or {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        m = ii.get("extmetadata", {})
        lic = (m.get("LicenseShortName", {}).get("value") or "").strip()
        if not lic.lower().startswith(_OK_LICENCES) or ii.get("width", 0) < 1000 or not ii.get("thumburl"):
            continue
        artist = re.sub(r"<[^>]+>|\s+", " ", m.get("Artist", {}).get("value", "")).strip()[:60] or "unknown"
        out.append({"kind": "photo", "id": ("c", p.get("pageid")), "url": ii["thumburl"], "thumb": ii["thumburl"],
                    "user": artist, "tags": p.get("title", "").lower(), "fit": True,
                    "credit": f"Photo: {artist}, {lic}, via Wikimedia Commons"})
    return out


def _openverse_candidates(query):
    """Openverse: millions of openly licensed photos (Flickr, museums, Wikimedia) - free, no key.
    Only CC BY, CC0 and public-domain-mark: never share-alike, non-commercial or no-derivatives."""
    r = _get("https://api.openverse.org/v1/images/", params={
        "q": query[:80], "license": "by,cc0,pdm", "page_size": 12, "mature": "false"})
    out = []
    for x in r.json().get("results", []):
        if (x.get("width") or 0) < 1000 or not x.get("url"):
            continue
        lic = f"{(x.get('license') or '').upper()} {x.get('license_version') or ''}".strip()
        who = (x.get("creator") or "unknown")[:60]
        out.append({"kind": "photo", "id": ("o", x.get("id")), "url": x["url"],
                    "thumb": x.get("thumbnail") or x["url"], "user": who,
                    "tags": " ".join(t.get("name", "") for t in (x.get("tags") or [])[:12]) + " " + (x.get("title") or ""),
                    "fit": True, "credit": f"Photo: {who}, {lic}, via Openverse ({x.get('source', '')})"})
    return out


def _inat_candidates(query):
    """iNaturalist: research-grade photos of the EXACT species a line names (a monarch, not "a
    butterfly"), CC0 or CC BY only, credited to the observer. Used only when the query resolves to a
    real taxon whose name or common name appears in the query."""
    t = _get("https://api.inaturalist.org/v1/taxa/autocomplete", params={"q": query[:60], "per_page": 1}).json()
    tx = (t.get("results") or [None])[0]
    if not tx:
        return []
    names = {(tx.get("name") or "").lower(), (tx.get("preferred_common_name") or "").lower(),
             (tx.get("matched_term") or "").lower()} - {""}
    if not any(n in query.lower() or query.lower() in n for n in names):
        return []                                  # a loose match ("bark" -> a beetle) is not the subject
    r = _get("https://api.inaturalist.org/v1/observations", params={
        "taxon_id": tx["id"], "photo_license": "cc0,cc-by", "quality_grade": "research",
        "order_by": "votes", "per_page": 10})
    out = []
    for o in r.json().get("results", []):
        ph = (o.get("photos") or [{}])[0]
        lic = (ph.get("license_code") or "").lower()
        if lic not in ("cc0", "cc-by") or not ph.get("url"):
            continue
        who = re.sub(r"^\(c\)\s*|,.*$", "", ph.get("attribution") or "").strip()[:50] or "iNaturalist observer"
        out.append({"kind": "photo", "id": ("in", ph.get("id")), "url": ph["url"].replace("square", "original"),
                    "thumb": ph["url"].replace("square", "medium"), "user": who,
                    "tags": f"{tx.get('preferred_common_name', '')} {tx.get('name', '')}".lower(), "fit": True,
                    "credit": f"Photo: {who}, {'CC0' if lic == 'cc0' else 'CC BY'}, via iNaturalist"})
    return out


def _wellcome_candidates(query):
    """Wellcome Collection: anatomy, medicine and microscopy images (old plates and modern
    photographs). Public-domain mark or CC BY only - CC BY-NC is common there and always skipped."""
    r = _get("https://api.wellcomecollection.org/catalogue/v2/images", params={"query": query[:80], "pageSize": 12})
    out = []
    for x in r.json().get("results", []):
        loc = (x.get("locations") or [{}])[0]
        lic = (loc.get("license") or {}).get("id", "")
        if lic not in ("pdm", "cc-0", "cc-by") or not loc.get("url"):
            continue
        base = loc["url"].rsplit("/info.json", 1)[0]
        title = ((x.get("source") or {}).get("title") or "")[:80]
        out.append({"kind": "photo", "id": ("wc", x.get("id")), "url": f"{base}/full/1600,/0/default.jpg",
                    "thumb": f"{base}/full/400,/0/default.jpg", "user": "Wellcome Collection", "tags": title.lower(),
                    "fit": True, "credit": f"Image: Wellcome Collection ({'public domain' if lic != 'cc-by' else 'CC BY 4.0'})"})
    return out


def _met_candidates(query, n=6):
    """The Met's Open Access collection (CC0): historic scientific instruments, anatomy prints and
    portraits, for science-history moments. Only objects marked public domain. (The old /v1/search
    was retired on 01 Oct 2026; /v1.1/search is the paginated replacement.)"""
    hdr = {"User-Agent": "Mozilla/5.0 (yt-studio)"}
    r = requests.get("https://collectionapi.metmuseum.org/public/collection/v1.1/search", headers=hdr, timeout=20,
                     params={"q": query[:60], "hasImages": "true", "limit": n})
    out = []
    for oid in (r.json().get("objectIDs") or [])[:n]:
        try:
            o = requests.get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}",
                             headers=hdr, timeout=15).json()
        except Exception:
            continue
        if not o.get("isPublicDomain") or not o.get("primaryImage"):
            continue
        out.append({"kind": "photo", "id": ("met", oid), "url": o["primaryImage"],
                    "thumb": o.get("primaryImageSmall") or o["primaryImage"], "user": "The Met",
                    "tags": f"{o.get('title', '')} {o.get('objectName', '')} {o.get('classification', '')}".lower(),
                    "fit": True, "credit": "Image: The Metropolitan Museum of Art (CC0)"})
    return out


def _nasa_candidates(query):
    """NASA Image Library: public-domain photos of space, Earth and oceans - free, no key."""
    r = _get("https://images-api.nasa.gov/search", params={"q": query[:80], "media_type": "image"})
    out = []
    for it in r.json().get("collection", {}).get("items", [])[:10]:
        d, href = it["data"][0], (it.get("links") or [{}])[0].get("href", "")
        if not href:
            continue
        out.append({"kind": "photo", "id": ("n", d.get("nasa_id")), "url": href.replace("~thumb", "~large"),
                    "thumb": href, "user": "NASA", "tags": (d.get("title") or "") + " " + " ".join(d.get("keywords") or []),
                    "fit": True, "credit": "Image: NASA (public domain)"})
    return out


def _nasa_video_candidates(query):
    """NASA video: real public-domain footage of space, Earth, oceans, weather, flight - no key."""
    r = _get("https://images-api.nasa.gov/search", params={"q": query[:80], "media_type": "video"})
    out = []
    for it in r.json().get("collection", {}).get("items", [])[:6]:
        d, thumb = it["data"][0], (it.get("links") or [{}])[0].get("href", "")
        if thumb and it.get("href"):
            out.append({"kind": "video", "id": ("nv", d.get("nasa_id")), "url": None, "manifest": it["href"],
                        "thumb": thumb, "user": "NASA", "fit": True,
                        "tags": (d.get("title") or "") + " " + " ".join(d.get("keywords") or []),
                        "credit": "Video: NASA (public domain)"})
    return out


def _nasa_video_url(manifest):
    files = _get(manifest).json()
    for pref in ("~large.mp4", "~medium.mp4", "~mobile.mp4"):   # never ~orig (can be gigabytes)
        hit = next((f for f in files if f.endswith(pref)), None)
        if hit:
            return hit.replace("http://", "https://")
    raise ValueError("no mp4 in NASA asset")


def _svs_video_candidates(query):
    """NASA Scientific Visualization Studio: accurate science ANIMATIONS made by NASA visualisers from
    real data (hurricanes, the Sun, Earth, the Moon, oceans, climate, orbits). Free API, no key; NASA
    work is not copyrighted, credited as NASA's Scientific Visualization Studio."""
    r = _get("https://svs.gsfc.nasa.gov/api/search/", params={"search": query[:80], "limit": 4})
    out = []
    for hit in r.json().get("results", [])[:4]:
        try:
            d = _get(f"https://svs.gsfc.nasa.gov/api/{hit['id']}").json()
        except Exception:
            continue
        movie, still = None, None
        for g in d.get("media_groups") or []:
            for it in g.get("items") or []:
                inst = it.get("instance") or {}
                url = (inst.get("url") or "").replace("http://", "https://")
                w = inst.get("width") or 0
                if inst.get("media_type") == "Movie" and url.endswith(".mp4") and 720 <= w <= 3840 and not movie:
                    movie = url
                if inst.get("media_type") == "Image" and url.endswith((".jpg", ".png")) and not still:
                    still = url
        if movie and still:
            out.append({"kind": "video", "id": ("sv", hit["id"]), "url": movie, "thumb": still, "user": "NASA SVS",
                        "fit": True, "tags": f"{d.get('title', '')} {' '.join(d.get('keywords') or [])}",
                        "credit": "Visualization: NASA's Scientific Visualization Studio"})
    return out


def _commons_video_candidates(query):
    """Wikimedia Commons video (webm/ogv): real footage of specific animals, plants and processes.
    Same licence rule as the photos: public domain, CC0 or CC BY only."""
    import re
    r = _get("https://commons.wikimedia.org/w/api.php", params={
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": f"{query[:80]} filetype:video", "gsrlimit": 10, "prop": "imageinfo",
        "iiprop": "url|extmetadata|size", "iiurlwidth": 640})
    out = []
    for p in (r.json().get("query") or {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        m = ii.get("extmetadata", {})
        lic = (m.get("LicenseShortName", {}).get("value") or "").strip()
        if (not lic.lower().startswith(_OK_LICENCES) or min(ii.get("width", 0), ii.get("height", 0)) < 720
                or not ii.get("thumburl") or ii.get("duration", 99) < 3):
            continue
        artist = re.sub(r"<[^>]+>|\s+", " ", m.get("Artist", {}).get("value", "")).strip()[:60] or "unknown"
        out.append({"kind": "video", "id": ("cv", p.get("pageid")), "url": ii["url"], "thumb": ii["thumburl"],
                    "user": artist, "tags": p.get("title", "").lower(), "fit": True,
                    "credit": f"Video: {artist}, {lic}, via Wikimedia Commons"})
    return out


def _shortlist(cands, query, n=10):
    words = {w for w in query.lower().split() if len(w) > 2}
    def score(c):
        tagwords = set(c["tags"].lower().replace(",", " ").split())
        return (len(words & tagwords), c["fit"], c["kind"] == "video")
    return sorted(cands, key=score, reverse=True)[:n]


_last_call, _cache, _busy_until = {}, {}, {}


def _get(url, **kw):
    """requests.get that is polite to each picture site: spaced-out calls (Pixabay allows about 100
    a minute), search results remembered for the whole video, and if a site keeps saying "too many
    requests" it is skipped for a while - the other sources carry on - instead of stalling the run."""
    import time
    from urllib.parse import urlparse
    host = urlparse(url).netloc
    key = (url, tuple(sorted((kw.get("params") or {}).items())))
    if "api" in host or "/api/" in url:
        if key in _cache:
            return _cache[key]
    if time.time() < _busy_until.get(host, 0):
        raise RuntimeError(f"{host} is resting after rate limits")
    gap = 0.75 if "pixabay" in host else 0.2
    wait = _last_call.get(host, 0) + gap - time.time()
    if wait > 0:
        time.sleep(wait)
    timeout = kw.pop("timeout", 30 if "pixabay" in host else 15)
    for attempt in range(2):
        _last_call[host] = time.time()
        try:
            r = requests.get(url, timeout=timeout, headers=UA, **kw)
        except requests.RequestException:
            _busy_until[host] = time.time() + 600   # not answering: leave it out for 10 minutes
            log(f"visuals: {host} not answering, leaving it out for 10 min")
            raise
        if r.status_code not in (429, 502, 503, 504):
            r.raise_for_status()
            if key[1] or "api" in host:
                _cache[key] = r
            return r
        if attempt == 0:
            pause = min(int(r.headers.get("Retry-After") or 0) or 5, 30)
            time.sleep(pause)
    # still refusing: rate limit -> rest 90 s; server down -> leave it out for 10 minutes.
    # The other picture sources carry on meanwhile, so the video never waits on one site.
    rest = 90 if r.status_code == 429 else 600
    _busy_until[host] = time.time() + rest
    log(f"visuals: {host} unavailable ({r.status_code}), leaving it out for {rest // 60 or 1} min")
    r.raise_for_status()
    return r


def _thumb_bytes(url):
    im = Image.open(io.BytesIO(_get(url).content)).convert("RGB")
    im.thumbnail((320, 320))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return buf.getvalue()


def _judge(narration, query, cands, note=""):
    """The AI looks at the candidate frames and picks the one that shows the narration."""
    imgs, keep = [], []
    for c in cands:
        try:
            imgs.append(_thumb_bytes(c["thumb"]))
            keep.append(c)
        except Exception:
            pass
    if not keep:
        return None, 0
    try:
        out = llm_json(f"""You choose stock footage for one scene of a science YouTube Short.
The narrator says: "{narration}"
Intended visual: "{query}"
{("A previous pick for this scene was REJECTED by the reviewer because: " + note + " Avoid that mistake.") if note else ""}
You are shown {len(keep)} candidate frames, in order (image 1 to {len(keep)}).
Score each 0-10 for how literally and clearly it shows what the narrator is talking about at
this moment, so a viewer instantly connects picture and words. Be strict:
10 = shows exactly the thing said; 7 = clearly the same subject; 5 = a fair visual analogy;
3 = only loosely related (same mood or setting); 0 = unrelated. Most candidates should NOT get 9-10. Score 0 for: green screen,
unrelated people or animals, abstract shapes, text overlays, watermarks, anything misleading
or scientifically wrong for the narration.
The video is shown FULL SCREEN on a phone (tall 9:16), so a landscape frame is cropped to a narrow
vertical slice: also say where the main subject sits left-to-right in the best image.
Return JSON: {{"scores": [numbers, one per image], "best": index starting at 1,
 "subject_x": the horizontal centre of the main subject in the best image, 0 = left edge, 1 = right edge}}""", images=imgs)
        scores = [float(x) if isinstance(x, (int, float, str)) and str(x).replace(".", "", 1).isdigit() else 0.0
                  for x in (out.get("scores") or [])]
        b = out.get("best")
        if isinstance(b, list):
            b = b[0] if b else None
        try:
            best = int(b) - 1
        except (TypeError, ValueError):
            best = max(range(len(scores)), key=scores.__getitem__) if scores else -1
        if 0 <= best < len(keep):
            try:
                sx = min(1.0, max(0.0, float(out.get("subject_x", 0.5))))
            except (TypeError, ValueError):
                sx = 0.5
            return {**keep[best], "subject_x": sx}, float(scores[best]) if best < len(scores) else 5.0
    except Exception as e:
        log(f"visuals: judge unavailable ({str(e)[:60]}), using tag match")
    return keep[0], 4.0


def _download(url, path):
    import time
    for attempt in range(5):
        r = requests.get(url, stream=True, timeout=120, headers=UA)
        if r.status_code not in (429, 502, 503, 504) or (r.status_code != 429 and attempt >= 2):
            break
        r.close()
        time.sleep(15 * (attempt + 1))
    with r:
        r.raise_for_status()
        with open(path, "wb") as fh:
            for chunk in r.iter_content(1 << 16):
                fh.write(chunk)


def _photo_clip(img_path, out_path, seconds, idx):
    """Slow Ken Burns zoom on a still photo so it reads as motion."""
    f = config()["format"]
    W, H = f["width"], f["height"]
    try:  # a landscape photo stays landscape; the editor blur-fills it like a landscape clip
        with Image.open(img_path) as im:
            if H > W and im.width / im.height > 0.9:
                W, H = 1920, 1080
    except Exception:
        pass
    frames = max(int(seconds * f["fps"]) + 15, 30)
    zoom = "min(zoom+0.0009,1.18)" if idx % 2 == 0 else "if(eq(on,1),1.18,max(zoom-0.0009,1.0))"
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(img_path), "-vf",
         f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
         f"crop={W*2}:{H*2},"
         f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={f['fps']}",
         "-frames:v", str(frames), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out_path)])


def _fallback(path, seconds, idx):
    f = config()["format"]
    hue = (idx * 47) % 360
    run(["ffmpeg", "-y", "-f", "lavfi", "-i",
         f"gradients=s={f['width']}x{f['height']}:speed=0.02:c0=0x0b1f3a:c1=0x0a7d68:seed={idx}",
         "-t", f"{seconds:.2f}", "-vf", f"hue=h={hue}", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)])


def pick_scene(i, scene, a, b, job_dir, used, note="", extra_queries=()):
    """Choose and prepare footage for one scene. Returns (score, pick-or-None, credit)."""
    out = job_dir / f"raw_{i:02d}.mp4"
    pick, score = None, 0
    if i in _board and not note:   # this scene is a step on the explainer board
        try:
            from . import diagram
            steps = sorted(_board)
            k = steps.index(i)
            diagram.board_clip(_board[steps[k - 1]] if k else None, _board[i], out, b - a + 0.5, job_dir, i)
            return 8.0, {"kind": "board", "id": ("b", i)}, diagram.CREDIT
        except Exception as e:
            log(f"visuals: board scene {i + 1} skipped ({str(e)[:60]})")
    if scene.get("anim") and not note:   # a number, comparison or process: computed Manim animation
        try:
            from . import animate
            if animate.available():
                animate.render(scene["anim"], out, b - a + 0.5, job_dir)
                return 9.0, {"kind": "anim", "id": ("a", i)}, None
        except Exception as e:
            log(f"visuals: animation for scene {i + 1} skipped ({str(e)[:80]})")
    if scene.get("map") and not note:   # a "where on Earth" line: an exact map from Natural Earth data
        try:
            from . import illustrate, maps
            img = job_dir / f"map_{i:02d}.png"
            places = [str(p) for p in scene["map"]][:3] if isinstance(scene["map"], list) else [str(scene["map"])]
            if maps.render(places, img, label=places[0] if len(places) == 1 else None):
                illustrate.clip(img, out, b - a + 0.5, i)
                img.unlink(missing_ok=True)
                return 9.0, {"kind": "map", "id": ("m", i)}, maps.CREDIT
        except Exception as e:
            log(f"visuals: map scene {i + 1} skipped ({str(e)[:60]})")
    if key("PIXABAY_API_KEY"):
        queries = list(extra_queries)[:3] + [scene["visual_query"]] + list(scene.get("alt_queries", []))[:1]
        cands = []
        for q in queries:
            try:
                cands += [c for c in _video_candidates(q) if c["id"] not in used]
            except Exception as e:
                log(f"visuals: video search error {e}")
        for q in queries[:2]:          # real public-domain footage beyond Pixabay (no key needed)
            for src in (_nasa_video_candidates, _svs_video_candidates, _commons_video_candidates):
                try:
                    cands += [c for c in src(q) if c["id"] not in used]
                except Exception as e:
                    log(f"visuals: {src.__name__[1:-11]} search error {str(e)[:60]}")
        for q in queries[:2]:
            try:
                cands += [c for c in _photo_candidates(q) if c["id"] not in used]
            except Exception as e:
                log(f"visuals: photo search error {e}")
            for src in (_commons_candidates, _openverse_candidates, _nasa_candidates, _inat_candidates,
                        _wellcome_candidates, _met_candidates):
                try:
                    cands += [c for c in src(q) if c["id"] not in used]
                except Exception as e:
                    log(f"visuals: {src.__name__[1:-11]} search error {str(e)[:60]}")
        seen, uniq = set(), []
        for c in cands:
            if c["id"] not in seen:
                seen.add(c["id"])
                uniq.append(c)
        if uniq:
            pick, score = _judge(scene["narration"], scene["visual_query"],
                                 _shortlist(uniq, scene["visual_query"]), note)
    # ILLUSTRATION: when no real footage shows the line exactly, draw it (agents/illustrate.py). Used
    # only if the drawing passes its own accuracy check AND scores higher than the best footage.
    below = config().get("visuals", {}).get("illustrate_below", 8)
    global _drawn
    if score < below:
        try:
            from . import illustrate
            if illustrate.available() and _drawn < illustrate.per_video_cap():
                _drawn += 1
                img = job_dir / f"ill_{i:02d}.jpg"
                s2 = illustrate.scene(scene["narration"], _topic, scene["visual_query"], img, note)
                if s2 > score and img.exists():
                    illustrate.clip(img, out, b - a + 0.5, i)
                    img.unlink(missing_ok=True)
                    return s2, {"kind": "illustration", "id": ("i", i, note[:20])}, illustrate.CREDIT
        except Exception as e:
            log(f"visuals: illustration skipped for scene {i + 1} ({str(e)[:60]})")
    credit = None
    if pick and score >= 5:
        used.add(pick["id"])
        import json as _json   # where the subject is, so the editor crops a landscape clip around it
        (job_dir / f"raw_{i:02d}.json").write_text(_json.dumps({"x": pick.get("subject_x", 0.5)}))
        try:
            if pick["kind"] == "video":
                url = pick["url"] or _nasa_video_url(pick["manifest"])
                if pick["id"][0] in ("nv", "cv", "sv"):   # NASA / SVS / Commons: read only 20 s, as mp4
                    run(["ffmpeg", "-y", "-user_agent", UA["User-Agent"]] + (["-ss", "4"] if pick["id"][0] in ("nv", "sv") else []) + ["-i", url, "-t", "20", "-an",
                         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", str(out)])
                else:
                    _download(url, out)
                credit = pick.get("credit") or f"Video by {pick['user']} on Pixabay"
            else:
                img = job_dir / f"img_{i:02d}.jpg"
                _download(pick["url"], img)
                _photo_clip(img, out, b - a + 0.5, i)
                img.unlink(missing_ok=True)
                credit = pick.get("credit") or f"Photo by {pick['user']} on Pixabay"
        except Exception as e:  # one failed download must not sink the whole video; QA flags the scene
            log(f"visuals: download failed for scene {i + 1} ({str(e)[:60]}), placeholder for now")
            _fallback(out, b - a + 0.5, i)
            score, pick, credit = 0, None, None
    else:
        # nothing on stock sites shows it: draw an explainer diagram (free, checked for accuracy)
        drawn = False
        global _diagrams
        if _diagrams < 3:
            try:
                from . import diagram
                if diagram.make_clip(scene["narration"], _topic, job_dir, i, out, b - a + 0.5):
                    _diagrams += 1
                    drawn, score, pick = True, 7.0, {"kind": "diagram", "id": ("d", i)}
            except Exception as e:
                log(f"visuals: diagram skipped ({str(e)[:60]})")
        if not drawn:
            _fallback(out, b - a + 0.5, i)
            pick = None
    return score, pick, credit


_topic, _diagrams, _board, _drawn = "", 0, {}, 0


def gather(script, times, job_dir):
    global last_scores, last_picks, last_credits, last_used, _topic, _diagrams, _board, _drawn
    _topic, _diagrams, _board, _drawn = script.get("topic", ""), 0, {}, 0
    if config().get("visuals", {}).get("board", True):
        try:
            from . import diagram
            _board = diagram.make_board(script, _topic)
            _diagrams = 1 if _board else 0   # the board counts toward the 3-diagram limit
        except Exception as e:
            log(f"visuals: no explainer board ({str(e)[:60]})")
    try:   # number / comparison / process lines -> computed Manim animations (agents/animate.py)
        from . import animate
        if animate.available():
            animate.plan(script)
    except Exception as e:
        log(f"visuals: no animation plan ({str(e)[:60]})")
    if not key("PIXABAY_API_KEY"):
        log("visuals: no PIXABAY_API_KEY, using gradient backgrounds")
    used, scores, picks, credits = set(), [], [], []
    for i, (scene, (a, b)) in enumerate(zip(script["scenes"], times)):
        score, pick, credit = pick_scene(i, scene, a, b, job_dir, used)
        scores.append(score)
        picks.append(pick)
        credits.append(credit)
    last_scores, last_picks, last_credits, last_used = scores, picks, credits, used
    clips = [job_dir / f"raw_{i:02d}.mp4" for i in range(len(scores))]
    log(f"visuals: {len(clips)} clips, {sum(s >= 6 for s in scores)} strong matches, scores {[round(s) for s in scores]}")
    return clips, sorted({c for c in credits if c})


def repick(script, times, job_dir, scene_notes):
    """Replace footage only for the scenes the reviewer flagged; never reuse a rejected clip."""
    for i, note in scene_notes.items():
        if i >= len(script["scenes"]):
            continue
        bad = last_picks[i]
        if bad:
            last_used.add(bad["id"])
        a, b = times[i]
        sc = script["scenes"][i]
        extra = []
        if last_scores[i] < 5:  # the old search words found nothing good: think of new ones
            try:
                out = llm_json(f"""Stock footage search for one scene of a science Short found nothing that fits.
Narration: "{sc['narration']}"
Searches already tried: {[sc.get('visual_query')] + list(sc.get('alt_queries', []))}
Give 4 NEW searches that a stock site like Pixabay really has clips for: 1-2 plain concrete nouns
each, things a camera can film (an animal, a food, a place, a person doing an action). If the exact
thing is rare on stock sites, pick the closest common thing that still honestly fits the words
(e.g. "krill" -> "shrimp", "salmon fry" -> "fish eggs"). Never abstract words.
Return JSON: {{"queries": ["...", "...", "...", "..."]}}""")
                extra = [q for q in out.get("queries", []) if isinstance(q, str)][:4]
                log(f"visuals: scene {i + 1} new searches {extra}")
            except Exception as e:
                log(f"visuals: no new searches ({str(e)[:60]})")
        score, pick, credit = pick_scene(i, sc, a, b, job_dir, last_used, note,
                                         extra_queries=extra or sc.get("alt_queries", [])[::-1])
        last_scores[i], last_picks[i], last_credits[i] = score, pick, credit
        log(f"visuals: scene {i + 1} re-picked (score {round(score)})")
    return sorted({c for c in last_credits if c})


last_scores, last_picks, last_credits, last_used = [], [], [], set()
