"""Agent 4c - Illustrated scenes: a drawing of exactly what the narrator is saying.

Why: every fast-growing channel in our genre (13 Nov 2026 study: The Why Side, Infinite Desk,
MapLore) shows each line as one clear illustrated scene filling the phone. Stock footage only
loosely matches. This agent draws the scene in ONE consistent stylised look - never photo-real -
and then a separate vision check looks at the picture: does it show what is said, and is anything
in it scientifically wrong (wrong number of legs, wrong colour, wrong shape, any lettering)? Only a
picture that passes is used, and only when it beats the best real footage for that line.

Engine: FLUX.2 [klein] 4B (Apache 2.0) on Cloudflare Workers AI, free tier (10,000 neurons a day,
about 60 images at 864x1536). It switches on by itself once the CLOUDFLARE_ACCOUNT_ID and
CLOUDFLARE_API_TOKEN secrets exist; without them nothing changes. A daily cap keeps it inside the
free tier, so it can never cost money.
"""
import base64
import datetime as dt
import io
import random

import requests
from PIL import Image

from .core import DATA, config, key, llm_json, log, read_json, run, write_json

MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
DAILY_CAP = 60            # images a day; ~140 neurons each, so it stays inside the free 10,000
LONG_CAP = 25             # of those, at most this many for the weekly long video
PASS = 7                 # the vision check's score a picture needs before it can be used
CREDIT = "Illustrations: drawn for this video with FLUX.2 [klein] 4B (AI, Apache 2.0) and checked for accuracy"
# The style goes FIRST: the model weights the start of a prompt most. With the style at the end
# (first cloud test, 13 Nov 2026), 1 picture in 3 drifted to a photo look and failed the check.
STYLE_HEAD = ("A stylised 3D cartoon illustration with simplified rounded shapes and matte clay-like "
              "materials, like a frame from an animated science explainer.")
STYLE_TAIL = ("Bright clean colours, soft even lighting, plain soft-gradient background, one clear subject "
              "large in the frame. No text, no letters, no numbers, no labels, no logos, no watermark. "
              "Not a photograph, not photorealistic.")
STYLE = STYLE_HEAD + " " + STYLE_TAIL


def full_prompt(scene_prompt):
    return f"{STYLE_HEAD} {_unphoto(scene_prompt)} {STYLE_TAIL}"


USAGE = DATA / "illustrate_usage.json"


def available():
    return bool(key("CLOUDFLARE_ACCOUNT_ID") and key("CLOUDFLARE_API_TOKEN"))


def _size():
    f = config()["format"]
    return (864, 1536) if f["height"] > f["width"] else (1536, 864)


def _spend():
    """True (and counted) if today's free allowance has room for one more image."""
    today = dt.date.today().isoformat()
    u = read_json(USAGE, {}) or {}
    if u.get("date") != today:
        u = {"date": today, "images": 0}
    long_form = _size()[0] > _size()[1]          # the weekly episode has ~40 scenes: it may not eat
    if u["images"] >= DAILY_CAP or (long_form and u.get("long", 0) >= LONG_CAP):   # the Shorts' share
        return False
    u["images"] += 1
    if long_form:
        u["long"] = u.get("long", 0) + 1
    write_json(USAGE, u)
    return True


def _render(prompt, w, h):
    url = (f"https://api.cloudflare.com/client/v4/accounts/{key('CLOUDFLARE_ACCOUNT_ID')}"
           f"/ai/run/{MODEL}")
    r = requests.post(url, headers={"Authorization": f"Bearer {key('CLOUDFLARE_API_TOKEN')}"},
                      files={"prompt": (None, prompt[:2000]), "width": (None, str(w)),
                             "height": (None, str(h)), "seed": (None, str(random.randint(1, 2**31 - 1)))},
                      timeout=120)
    r.raise_for_status()
    if r.headers.get("content-type", "").startswith("image/"):
        return r.content
    data = r.json()
    img = (data.get("result") or {}).get("image") or data.get("image")
    if not img:
        raise RuntimeError(f"no image in reply: {str(data)[:120]}")
    return base64.b64decode(img)


def _jpeg(raw, longest=None):
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    if longest:
        im.thumbnail((longest, longest))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=92)
    return buf.getvalue()


def _describe(narration, topic, query, note):
    return llm_json(f"""You art-direct ONE scene of an accurate science video. The picture is shown while the
narrator says: "{narration}"
Video topic: "{topic}". Intended visual: "{query}".
{("A previous picture for this scene was rejected because: " + note + ". Fix that.") if note else ""}
Write an image prompt for an illustrator. Rules:
- Show literally what the line is about: one clear subject or one simple scene, composed for a
  {'tall phone screen (9:16)' if _size()[1] > _size()[0] else 'wide screen (16:9)'}.
- Scientifically exact: correct anatomy (count of legs, wings, eyes), real colours and shapes, correct
  scale relationships, correct cause and effect. If the idea is invisible (heat, sound, a force), show
  its visible effect or a simple honest cutaway, never a made-up gadget.
- No people's faces in close-up, no real brands, no text of any kind in the picture.
- SIMPLE beats detailed: only the parts needed to show the idea, nothing floating or decorative
  (no stray bubbles, sparkles or particles unless they are the point, and then exactly where they
  really are). The key feature must be big and obvious (e.g. the comb-like fringe along the
  feather's front edge, shown large).
- 1-3 sentences, concrete nouns and positions. Never say photo, photograph or realistic, and do not
  describe the art style (a stylised illustration style is added for you).
Return JSON: {{"prompt": "...", "must_show": "the one thing a viewer must see, in a few words"}}""")


def _check(jpg, narration, must_show):
    out = llm_json(f"""You are the strict picture checker for an accurate science video.
The narrator says: "{narration}"
The picture must show: "{must_show}"
Look at the picture. Score 0-10 for how clearly and literally it shows that, so a viewer instantly
connects picture and words (10 exact, 7 clearly right, 5 loose, 0 wrong).
Score 0 if ANYTHING in it is scientifically wrong or misleading (wrong number of legs, wings or eyes,
impossible anatomy, wrong colour or shape for the real thing, wrong cause and effect), if it contains
any letters, numbers, words or symbols that look like writing, if it looks like a real photograph,
or if it is confusing or cluttered.
Return JSON: {{"score": number, "problem": "what is wrong, or empty"}}""", images=[_jpeg(jpg, 640)])
    try:
        return float(out.get("score", 0)), str(out.get("problem", ""))[:200]
    except (TypeError, ValueError):
        return 0.0, "unreadable check"


def _unphoto(p):
    """Never photo-real: the art director sometimes writes 'macro photograph'; the style decides."""
    import re
    p = re.sub(r"(?i)\b(hyper-?realistic|photo-?realistic|realistic|photograph(?:ic|y)?|photo|dslr)\b", "", p)
    p = re.sub(r"(?i)\bmacro\b", "close-up", p)
    return re.sub(r"\s{2,}", " ", re.sub(r"\s+([,.])", r"\1", p)).strip()


def scene(narration, topic, query, out_jpg, note="", tries=2):
    """Draw and check one scene. Returns the checker's score (0 if nothing passed); the picture is
    saved to out_jpg only when it passes."""
    if not available():
        return 0.0
    w, h = _size()
    best, best_score, problem = None, 0.0, note
    for attempt in range(tries):
        if not _spend():
            log("illustrate: today's free allowance is used up; footage only for the rest of the day")
            break
        try:
            d = _describe(narration, topic, query, problem)
            raw = _render(full_prompt(d["prompt"]), w, h)
            score, problem = _check(raw, narration, d.get("must_show", query))
        except Exception as e:
            log(f"illustrate: attempt {attempt + 1} failed ({str(e)[:80]})")
            continue
        log(f"illustrate: drawn '{query}' -> check {score:.0f}/10{(' (' + problem + ')') if problem else ''}")
        if score > best_score:
            best, best_score = raw, score
        if score >= 9:
            break
    if best is None or best_score < PASS:
        return 0.0
    out_jpg.write_bytes(_jpeg(best))
    return best_score


def clip(img, out, seconds, idx):
    """The picture as a full-screen moving shot: a slow push in or pull out (never a frozen frame,
    which the QA freeze check rightly rejects)."""
    f = config()["format"]
    W, H = f["width"], f["height"]
    frames = max(int(seconds * f["fps"]) + 15, 30)
    zoom = "min(zoom+0.0007,1.12)" if idx % 2 == 0 else "if(eq(on,1),1.12,max(zoom-0.0007,1.0))"
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-vf",
         f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase:flags=lanczos,crop={W * 2}:{H * 2},"
         f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={f['fps']}",
         "-frames:v", str(frames), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])
