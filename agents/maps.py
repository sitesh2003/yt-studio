"""Agent 4d - Maps drawn from real map data, so a "where on Earth" line is shown exactly right.

Data: Natural Earth admin-0 countries, 1:50m (public domain, naturalearthdata.com), read from the
project's official GitHub copy and kept in a local cache. Shapes come straight from the data, so a
map can never be "almost" right the way a drawn or AI picture can. Used by the visuals agent when a
scene names places ("map": ["Japan"] or a continent), and the base for a geography channel.

Projection: equirectangular, corrected by the cosine of the map's middle latitude, which keeps
shapes true for a country- or region-sized view (not for a whole-world view, where it is the usual
plate carree).
"""
import json
import math
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .core import config, log

SRC = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
       "ne_50m_admin_0_countries.geojson")
CACHE = Path.home() / ".cache" / "yt-studio" / "ne_50m_admin_0_countries.geojson"
CREDIT = "Maps: Natural Earth (public domain)"
OCEAN, LAND, EDGE, HIT, HIT_EDGE = (14, 42, 74), (58, 84, 112), (96, 124, 152), (255, 214, 10), (255, 245, 190)
_DATA = None


def _features():
    global _DATA
    if _DATA is None:
        if not CACHE.exists():
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(SRC, headers={"User-Agent": "yt-studio-maps/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                CACHE.write_bytes(r.read())
        _DATA = json.loads(CACHE.read_text(encoding="utf-8"))["features"]
    return _DATA


def _names(f):
    p = f["properties"]
    return {str(p.get(k, "")).lower() for k in ("NAME", "NAME_LONG", "ADMIN", "NAME_EN", "FORMAL_EN", "ABBREV")} - {""}


def find(places):
    """Features for each place name: a country, or a continent ("Africa", "South America")."""
    hits, missing = [], []
    for name in places:
        n = name.lower().strip()
        got = [f for f in _features() if n in _names(f)]
        if not got:
            got = [f for f in _features() if str(f["properties"].get("CONTINENT", "")).lower() == n]
        (hits.extend(got) if got else missing.append(name))
    return hits, missing


def _rings(f):
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for poly in polys:
        yield poly[0]               # outer ring; lakes are too small to matter at this size


def _bbox(feats):
    xs, ys = [], []
    for f in feats:
        for ring in _rings(f):
            # skip far-flung overseas islands so France means France, not France plus Guiana
            xs += [p[0] for p in ring]
            ys += [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def _main_bbox(feats):
    """The bbox of each feature's LARGEST polygon (the mainland), so overseas territories don't
    zoom the map out to the whole planet."""
    def box(r):
        xs, ys = [p[0] for p in r], [p[1] for p in r]
        return min(xs), min(ys), max(xs), max(ys)

    def area(b):
        return (b[2] - b[0]) * (b[3] - b[1])

    best = []
    for f in feats:
        boxes = [box(r) for r in _rings(f)]
        big = max(boxes, key=area)
        bx, by = (big[0] + big[2]) / 2, (big[1] + big[3]) / 2
        for b in boxes:   # big islands close to the mainland count (Hokkaido); far territories don't
            if area(b) >= 0.05 * area(big) and abs((b[0] + b[2]) / 2 - bx) < 40 and abs((b[1] + b[3]) / 2 - by) < 15:
                best.append({"geometry": {"type": "Polygon", "coordinates": [[(b[0], b[1]), (b[2], b[3])]]}})
    return _bbox(best)


def render(places, out_png, label=None, size=None):
    """Draw the places highlighted on a calm map, centred, with room around them. Returns False if
    a place is not in the data (the caller then uses footage instead)."""
    f_cfg = config()["format"]
    W, H = size or (f_cfg["width"], f_cfg["height"])
    hits, missing = find(places)
    if missing or not hits:
        log(f"maps: not in Natural Earth: {missing}")
        return False
    x0, y0, x1, y1 = _main_bbox(hits)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    k = math.cos(math.radians(max(-70, min(70, cy))))
    span_x, span_y = max((x1 - x0) * k, 2.0), max(y1 - y0, 2.0)
    scale = min(W * 0.62 / span_x, H * 0.42 / span_y)          # the place fills the middle of the frame
    ss = 2                                                      # draw at 2x, then downsample: smooth edges
    img = Image.new("RGB", (W * ss, H * ss), OCEAN)
    d = ImageDraw.Draw(img)

    def xy(lon, lat):
        return ((W / 2 + (lon - cx) * k * scale) * ss, (H / 2 - (lat - cy) * scale) * ss)

    hit_ids = {id(f) for f in hits}
    for f in _features():
        for ring in _rings(f):
            pts = [xy(*p[:2]) for p in ring]
            if id(f) in hit_ids:
                continue
            d.polygon(pts, fill=LAND, outline=EDGE)
    glow = Image.new("L", img.size, 0)
    gd = ImageDraw.Draw(glow)
    for f in hits:
        for ring in _rings(f):
            gd.polygon([xy(*p[:2]) for p in ring], fill=255)
    img.paste(Image.new("RGB", img.size, HIT), (0, 0), glow.filter(ImageFilter.GaussianBlur(18 * ss)).point(lambda v: v // 3))
    for f in hits:
        for ring in _rings(f):
            d.polygon([xy(*p[:2]) for p in ring], fill=HIT, outline=HIT_EDGE)
    img = img.resize((W, H), Image.LANCZOS)
    if label:
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(str(Path(__file__).resolve().parent.parent / "assets" / "fonts" / "ArchivoBlack-Regular.ttf"), int(W * 0.075))
        except OSError:
            font = ImageFont.load_default()
        tw = d.textlength(label.upper(), font=font)
        d.text(((W - tw) / 2, H * 0.17), label.upper(), font=font, fill=(255, 255, 255),
               stroke_width=max(3, W // 270), stroke_fill=(0, 0, 0))
    img.save(out_png, quality=95)
    return True
