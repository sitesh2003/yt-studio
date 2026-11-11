"""Agent 4b - Footage that actually shows what the narrator is saying.

For every scene: search Pixabay videos and photos with several queries, drop junk (green
screen, AI-generated, low quality, already used), then SHOW the AI the preview frames of the
best candidates next to the narration and let it pick the one that fits. If nothing fits, it
falls back to a matching photo with a slow zoom, and only then to a plain moving gradient.
"""
import io

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


def _shortlist(cands, query, n=6):
    words = {w for w in query.lower().split() if len(w) > 2}
    def score(c):
        tagwords = set(c["tags"].lower().replace(",", " ").split())
        return (len(words & tagwords), c["fit"], c["kind"] == "video")
    return sorted(cands, key=score, reverse=True)[:n]


def _get(url, **kw):
    """requests.get that waits out Pixabay's rate limit (HTTP 429) instead of failing the video."""
    import time
    for attempt in range(6):
        r = requests.get(url, timeout=kw.pop("timeout", 30), **kw)
        if r.status_code != 429:
            r.raise_for_status()
            return r
        wait = int(r.headers.get("Retry-After") or 0) or 15 * (attempt + 1)
        log(f"visuals: Pixabay busy, waiting {wait}s")
        time.sleep(min(wait, 90))
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
Return JSON: {{"scores": [numbers, one per image], "best": index starting at 1}}""", images=imgs)
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
            return keep[best], float(scores[best]) if best < len(scores) else 5.0
    except Exception as e:
        log(f"visuals: judge unavailable ({str(e)[:60]}), using tag match")
    return keep[0], 4.0


def _download(url, path):
    import time
    for attempt in range(5):
        r = requests.get(url, stream=True, timeout=120)
        if r.status_code != 429:
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
    frames = max(int(seconds * f["fps"]) + 15, 30)
    zoom = "min(zoom+0.0009,1.18)" if idx % 2 == 0 else "if(eq(on,1),1.18,max(zoom-0.0009,1.0))"
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(img_path), "-vf",
         f"scale={f['width']*2}:{f['height']*2}:force_original_aspect_ratio=increase,"
         f"crop={f['width']*2}:{f['height']*2},"
         f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={f['width']}x{f['height']}:fps={f['fps']}",
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
    if key("PIXABAY_API_KEY"):
        queries = list(extra_queries) + [scene["visual_query"]] + list(scene.get("alt_queries", []))[:2]
        cands = []
        for q in queries:
            try:
                cands += [c for c in _video_candidates(q) if c["id"] not in used]
            except Exception as e:
                log(f"visuals: video search error {e}")
        for q in queries[:2]:
            try:
                cands += [c for c in _photo_candidates(q) if c["id"] not in used]
            except Exception as e:
                log(f"visuals: photo search error {e}")
        seen, uniq = set(), []
        for c in cands:
            if c["id"] not in seen:
                seen.add(c["id"])
                uniq.append(c)
        if uniq:
            pick, score = _judge(scene["narration"], scene["visual_query"],
                                 _shortlist(uniq, scene["visual_query"]), note)
    credit = None
    if pick and score >= 5:
        used.add(pick["id"])
        try:
            if pick["kind"] == "video":
                _download(pick["url"], out)
                credit = f"Video by {pick['user']} on Pixabay"
            else:
                img = job_dir / f"img_{i:02d}.jpg"
                _download(pick["url"], img)
                _photo_clip(img, out, b - a + 0.5, i)
                img.unlink(missing_ok=True)
                credit = f"Photo by {pick['user']} on Pixabay"
        except Exception as e:  # one failed download must not sink the whole video; QA flags the scene
            log(f"visuals: download failed for scene {i + 1} ({str(e)[:60]}), placeholder for now")
            _fallback(out, b - a + 0.5, i)
            score, pick, credit = 0, None, None
    else:
        _fallback(out, b - a + 0.5, i)
        pick = None
    return score, pick, credit


def gather(script, times, job_dir):
    global last_scores, last_picks, last_credits, last_used
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
        score, pick, credit = pick_scene(i, script["scenes"][i], a, b, job_dir, last_used, note,
                                         extra_queries=script["scenes"][i].get("alt_queries", [])[::-1])
        last_scores[i], last_picks[i], last_credits[i] = score, pick, credit
        log(f"visuals: scene {i + 1} re-picked (score {round(score)})")
    return sorted({c for c in last_credits if c})


last_scores, last_picks, last_credits, last_used = [], [], [], set()
