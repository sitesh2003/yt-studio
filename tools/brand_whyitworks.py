"""Channel picture + banner for Why It Works: a 3-4-5 right triangle with the squares on its sides."""
import os
from PIL import Image, ImageDraw, ImageFont

R = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))) + "/"
OUT = R + "brand/whyitworks/"
os.makedirs(OUT, exist_ok=True)
NAVY, Y, C, W = (10, 22, 48), (255, 204, 0), (80, 200, 255), (245, 245, 245)


def font(sz):
    import glob
    for f in glob.glob(R + "**/ArchivoBlack*.ttf", recursive=True) + ["C:/Windows/Fonts/arialbd.ttf"]:
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def pythagoras(d, ox, oy, u):
    """Right angle at A=(ox,oy); legs 3u to the right, 4u up. Squares drawn outward on all three sides."""
    A, B, Cc = (ox, oy), (ox + 3 * u, oy), (ox, oy - 4 * u)
    d.polygon([A, B, (B[0], oy + 3 * u), (ox, oy + 3 * u)], fill=C)            # 3 x 3, below
    d.polygon([A, Cc, (ox - 4 * u, Cc[1]), (ox - 4 * u, oy)], fill=C)          # 4 x 4, left
    vx, vy = Cc[0] - B[0], Cc[1] - B[1]                                        # hypotenuse B->C
    nx, ny = -vy, vx                                                           # perpendicular
    if nx * 1 + ny * -1 < 0:                                                   # point away from A (up-right)
        nx, ny = -nx, -ny
    d.polygon([B, Cc, (Cc[0] + nx, Cc[1] + ny), (B[0] + nx, B[1] + ny)], fill=Y)  # 5 x 5
    d.polygon([A, B, Cc], fill=W)


im = Image.new("RGB", (800, 800), NAVY)
d = ImageDraw.Draw(im)
pythagoras(d, 325, 500, 50)
im.save(OUT + "avatar.png")

b = Image.new("RGB", (2560, 1440), NAVY)
d = ImageDraw.Draw(b)
pythagoras(d, 860, 780, 24)
d.text((1060, 600), "Why It Works", font=font(120), fill=Y)
d.text((1064, 760), "Science, explained with the reason", font=font(46), fill=W)
b.save(OUT + "banner.png")
print("ok", im.getbbox())
