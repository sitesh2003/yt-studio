"""Find free 3D models for whatever a script talks about (owner, 20 Nov 2026: "whatever script will be
written, GitHub can search open-source animations around the web and based on that we can animate").

    python -m agents.asset_finder research/hero/<name>/script.json      # writes assets.json beside it

1. A free AI (agents/free_llm, never paid) reads the script and lists the 3D subjects it needs, each with
   what it must DO (walk/run = needs a rig; drive/fall/spin/still = any model; cut-away = any model).
2. Each subject is looked up, best licence first, in:
     local packs already in assets/3d (CC0, rigged dinosaurs, Kenney cars)        no key
     Poly Haven (CC0, 500+ real-world objects)                                     no key
     NASA 3D Resources (public domain: spacecraft, planets, rovers)                no key
     Poly Pizza (CC0 / CC-BY low-poly, 10,000+ incl. Quaternius & Kenney)          POLYPIZZA_API_KEY
     Sketchfab (only CC0 and CC-BY, only downloadable)                             SKETCHFAB_API_TOKEN
3. The chosen file is downloaded to assets/3d/found/<source>/<id>/ and its licence and author go into
   assets/3d/found/credits.json, so the description credits CC-BY authors automatically.
A subject nobody has is reported, never faked: the shot falls back to a diagram.
"""
import json
import re
import sys
from pathlib import Path

import requests

from .core import key, log

ROOT = Path(__file__).resolve().parent.parent
FOUND = ROOT / "assets" / "3d" / "found"
UA = {"User-Agent": "yt-studio-asset-finder/1.0"}
RIGGED = {"walk", "run", "fly", "swim", "roar", "attack", "jump"}

LOCAL = [   # packs already in the repo: (words that match, file, licence, author, rigged actions)
    ({"t. rex", "trex", "tyrannosaurus", "t-rex"}, "dinos/Trex.fbx", "CC0", "Quaternius", ["walk", "run", "idle", "attack", "jump"]),
    ({"velociraptor", "raptor"}, "dinos/Velociraptor.fbx", "CC0", "Quaternius", ["walk", "run", "idle", "attack", "jump"]),
    ({"triceratops"}, "dinos/Triceratops.fbx", "CC0", "Quaternius", ["walk", "run", "idle", "attack", "jump"]),
    ({"stegosaurus"}, "dinos/Stegosaurus.fbx", "CC0", "Quaternius", ["walk", "run", "idle", "attack", "jump"]),
    ({"apatosaurus", "brontosaurus", "sauropod"}, "dinos/Apatosaurus.fbx", "CC0", "Quaternius", ["walk", "run", "idle", "attack", "jump"]),
    ({"parasaurolophus", "hadrosaur", "duck-billed dinosaur"}, "dinos/Parasaurolophus.fbx", "CC0", "Quaternius", ["walk", "run", "idle", "attack", "jump"]),
    ({"car", "sedan", "vehicle"}, "cars/sedan.glb", "CC0", "Kenney", []),
    ({"taxi", "cab"}, "cars/taxi.glb", "CC0", "Kenney", []),
]


def _words(s):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower()))


def subjects(script):
    """What 3D things the script needs and what each must do. Free AI; None if no provider answers."""
    from . import free_llm
    text = "\n".join(s["narration"] for s in script["scenes"])
    prompt = ("List the physical things a 3D animator must model to show this YouTube Short accurately. "
              "Only real objects, animals or body parts that appear on screen; no abstract ideas. For each give "
              'its plain name (singular, e.g. "car", "human heart"), up to 3 search words, and what it must do '
              "on screen: one of walk, run, fly, swim, drive, fall, spin, still, cutaway.\n"
              'JSON: {"subjects": [{"name": "...", "search": ["..."], "does": "..."}]}\n\nScript:\n' + text)
    out = free_llm.ask_json(prompt, temperature=0.2)
    return (out or {}).get("subjects") or []


def local(subj):
    q = {subj["name"].lower(), *[s.lower() for s in subj.get("search", [])]}
    for names, f, lic, author, acts in LOCAL:
        if q & names or any(n in subj["name"].lower() for n in names):
            return {"source": "local", "id": f, "title": Path(f).stem, "licence": lic, "author": author,
                    "rigged": bool(acts), "actions": acts, "file": f"assets/3d/{f}"}


_PH = None


def polyhaven(subj):
    global _PH
    if _PH is None:
        try:
            _PH = requests.get("https://api.polyhaven.com/assets?t=models", headers=UA, timeout=30).json()
        except Exception:
            _PH = {}
    want = _words(" ".join([subj["name"], *subj.get("search", [])]))
    best, score = None, 0
    for aid, a in _PH.items():
        named = _words(aid.replace("_", " ") + " " + a.get("name", ""))
        tags = _words(" ".join([*a.get("tags", []), *a.get("categories", [])]))
        s = 2 * len(want & named) + len((want & tags) - named)
        if s > score:
            best, score = aid, s
    if best and score >= 2:
        a = _PH[best]
        return {"source": "polyhaven", "id": best, "title": a.get("name", best), "licence": "CC0",
                "author": ", ".join(a.get("authors", {}).keys()) or "Poly Haven", "rigged": False, "match": score,
                "thumb": a.get("thumbnail_url")}


_NASA = None


def nasa(subj):
    global _NASA
    if _NASA is None:
        h = dict(UA)
        if key("GITHUB_TOKEN"):
            h["Authorization"] = f"Bearer {key('GITHUB_TOKEN')}"
        try:
            t = requests.get("https://api.github.com/repos/nasa/NASA-3D-Resources/git/trees/master?recursive=1",
                             headers=h, timeout=60).json()
            _NASA = [x["path"] for x in t.get("tree", []) if x["path"].startswith("3D Models/")
                     and x["path"].lower().endswith((".glb", ".gltf", ".obj", ".stl"))]
        except Exception:
            _NASA = []
    want = _words(" ".join([subj["name"], *subj.get("search", [])])) - {"the", "a", "of"}
    hits = [(len(want & _words(p)), p) for p in _NASA]
    hits = [h for h in hits if h[0]]
    if hits:
        s, p = max(hits)
        return {"source": "nasa", "id": p, "title": Path(p).stem, "licence": "NASA media (public domain, no endorsement)",
                "author": "NASA", "rigged": False, "match": s}


def polypizza(subj):
    k = key("POLYPIZZA_API_KEY")
    if not k:
        return None
    for q in [subj["name"], *subj.get("search", [])]:
        try:
            r = requests.get(f"https://api.poly.pizza/v1.1/search/{requests.utils.quote(q)}",
                             headers={**UA, "x-auth-token": k}, timeout=30).json()
        except Exception:
            continue
        for m in r.get("results", []):
            lic = m.get("Licence") or m.get("License") or ""
            if "CC0" in lic or "CC-BY" in lic or "Attribution" in lic:
                return {"source": "polypizza", "id": m.get("ID"), "title": m.get("Title"), "licence": lic,
                        "author": (m.get("Creator") or {}).get("Username", ""), "rigged": bool(m.get("Animated")),
                        "url": m.get("Download")}


def sketchfab(subj):
    for lic in ("cc0", "by"):
        try:
            r = requests.get("https://api.sketchfab.com/v3/search", headers=UA, timeout=30, params={
                "type": "models", "q": subj["name"], "downloadable": "true", "license": lic,
                "animated": "true" if subj.get("does") in RIGGED else None, "sort_by": "-likeCount"}).json()
        except Exception:
            continue
        for m in r.get("results", [])[:6]:
            hit = {"source": "sketchfab", "id": m["uid"], "title": m["name"],
                   "licence": "CC0" if lic == "cc0" else "CC-BY 4.0", "author": m["user"]["username"],
                   "rigged": bool(m.get("animationCount")), "page": m.get("viewerUrl"),
                   "thumb": max((m.get("thumbnails") or {}).get("images", [{}]), key=lambda i: i.get("width", 0)).get("url"),
                   "needs_token": not key("SKETCHFAB_API_TOKEN")}
            if accurate(hit, subj) is not False:
                return hit


def accurate(hit, subj):
    """A free vision model looks at the model's thumbnail: is this really the subject, true to life
    (not a cartoon spaceship for "space shuttle", not a cannon for "barrel")? True / False / None (unchecked)."""
    if not hit.get("thumb"):
        return None
    try:
        from . import free_llm
        img = requests.get(hit["thumb"], headers=UA, timeout=30).content
        out = free_llm.ask_json(
            f'This is a thumbnail of a free 3D model titled "{hit.get("title")}". Is it an accurate, real-world '
            f'depiction of: {subj["name"]}? A stylised low-poly look is fine; a different object, a fictional '
            'design or a wrong shape is not. JSON: {"accurate": true/false, "why": "..."}', images=[img], temperature=0)
    except Exception:
        return None
    if out is None:
        return None
    hit["check"] = out.get("why", "")
    return bool(out.get("accurate"))


def find(subj):
    """Best free model for one subject, or None. A subject that must walk/run/fly needs a rig."""
    need_rig = subj.get("does") in RIGGED
    tried = []
    for fn in (local, polyhaven, nasa, polypizza, sketchfab):
        try:
            hit = fn(subj)
        except Exception as e:
            log(f"asset_finder: {fn.__name__} failed ({type(e).__name__})")
            hit = None
        if hit and hit["source"] in ("polyhaven", "nasa", "polypizza") and accurate(hit, subj) is False:
            log(f"asset_finder: {hit['title']} is not a true {subj['name']} ({hit.get('check', '')}); next")
            hit = None
        if hit:
            tried.append(hit)
            if hit["rigged"] or not need_rig:
                return hit, tried
    return (tried[0] if tried else None), tried


def download(hit):
    """Fetch a hit into assets/3d/found and record its credit. Returns the local path or None."""
    if hit["source"] == "local":
        return hit["file"]
    d = FOUND / hit["source"] / re.sub(r"[^A-Za-z0-9_.-]", "_", str(hit["id"]))[:80]
    d.mkdir(parents=True, exist_ok=True)
    path = None
    if hit["source"] == "polyhaven":
        files = requests.get(f"https://api.polyhaven.com/files/{hit['id']}", headers=UA, timeout=30).json()
        g = files["gltf"]["1k"]["gltf"]
        path = d / Path(g["url"]).name
        path.write_bytes(requests.get(g["url"], headers=UA, timeout=120).content)
        for rel, inc in (g.get("include") or {}).items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(requests.get(inc["url"], headers=UA, timeout=120).content)
    elif hit["source"] == "nasa":
        url = "https://media.githubusercontent.com/media/nasa/NASA-3D-Resources/master/" + requests.utils.quote(hit["id"])
        path = d / Path(hit["id"]).name
        path.write_bytes(requests.get(url, headers=UA, timeout=180).content)
    elif hit["source"] == "polypizza" and hit.get("url"):
        path = d / f"{hit['id']}.glb"
        path.write_bytes(requests.get(hit["url"], headers=UA, timeout=120).content)
    elif hit["source"] == "sketchfab" and key("SKETCHFAB_API_TOKEN"):
        r = requests.get(f"https://api.sketchfab.com/v3/models/{hit['id']}/download", timeout=30,
                         headers={**UA, "Authorization": f"Token {key('SKETCHFAB_API_TOKEN')}"}).json()
        url = (r.get("glb") or {}).get("url")
        if url:
            path = d / f"{hit['id']}.glb"
            path.write_bytes(requests.get(url, timeout=300).content)
    if not path:
        return None
    credits = FOUND / "credits.json"
    c = json.loads(credits.read_text(encoding="utf-8")) if credits.exists() else {}
    c[str(path.relative_to(ROOT)).replace("\\", "/")] = {k: hit.get(k) for k in ("source", "title", "author", "licence", "page")}
    credits.write_text(json.dumps(c, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path.relative_to(ROOT)).replace("\\", "/")


def plan(script_path, fetch=True):
    sp = Path(script_path)
    script = json.loads(sp.read_text(encoding="utf-8"))
    out = []
    for s in subjects(script):
        hit, tried = find(s)
        row = {"subject": s, "chosen": hit, "also": [t for t in tried if t is not hit]}
        if hit and fetch:
            row["file"] = download(hit)
        out.append(row)
        log(f"asset_finder: {s.get('name')} ({s.get('does')}) -> "
            f"{(hit or {}).get('source', 'NOTHING')} {(hit or {}).get('title', '')}")
    (sp.parent / "assets.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


if __name__ == "__main__":
    plan(sys.argv[1], fetch="--no-fetch" not in sys.argv)
