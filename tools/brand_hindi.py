"""Channel picture + banner for Aakhir Kyun? (the Hindi channel): 'क्यों?' in the brand yellow on navy.
Drawn as SVG and rendered by resvg, which shapes Devanagari properly (Pillow here has no shaping
engine and splits conjuncts and vowel signs)."""
import os
import resvg_py

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
OUT = R + "brand/hindi/"
os.makedirs(OUT, exist_ok=True)
FONT = R + "assets/fonts/Hind-Bold.ttf"


def render(svg, w, h, path):
    png = resvg_py.svg_to_bytes(svg_string=svg, font_files=[FONT], font_family="Hind", width=w, height=h)
    open(path, "wb").write(bytes(png))


avatar = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
<rect width="800" height="800" fill="#0a1630"/>
<circle cx="400" cy="400" r="300" fill="none" stroke="#50c8ff" stroke-width="22"/>
<text x="400" y="470" text-anchor="middle" font-family="Hind" font-weight="bold" font-size="230" fill="#ffcc00">क्यों?</text>
</svg>"""
render(avatar, 800, 800, OUT + "avatar.png")

banner = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2560 1440" width="2560" height="1440">
<rect width="2560" height="1440" fill="#0a1630"/>
<circle cx="740" cy="720" r="150" fill="none" stroke="#50c8ff" stroke-width="12"/>
<text x="740" y="755" text-anchor="middle" font-family="Hind" font-weight="bold" font-size="110" fill="#ffcc00">क्यों?</text>
<text x="950" y="725" font-family="Hind" font-weight="bold" font-size="150" fill="#ffcc00">आख़िर क्यों?</text>
<text x="956" y="830" font-family="Hind" font-weight="bold" font-size="66" fill="#f5f5f5">विज्ञान, आसान भाषा में</text>
</svg>"""
render(banner, 2560, 1440, OUT + "banner.png")
print("ok")
