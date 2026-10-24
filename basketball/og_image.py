"""Branded 1200x630 Open Graph image for Discord and other link previews.

Generated on the server, cached in memory, and available as ordinary PNG.
No bot, OAuth credentials, third-party images, or API calls required.
"""
from functools import lru_cache
from io import BytesIO
from math import hypot

from PIL import Image, ImageDraw, ImageFont

SIZE = (1200, 630)
DARK = (10, 16, 32)
ORANGE = (250, 138, 55)
WHITE = (245, 248, 252)
MUTED = (171, 188, 207)


def font(size, bold=True):
    paths = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


@lru_cache(maxsize=1)
def render_preview_png():
    image = Image.new("RGB", SIZE, DARK)
    px = image.load()
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            glow = max(0.0, 1.0 - hypot((x - 963) / 770, (y - 360) / 550))
            cool = max(0.0, 1.0 - hypot((x - 100) / 900, (y - 620) / 810))
            px[x, y] = (
                int(10 + 24 * glow + 5 * cool),
                int(16 + 13 * glow + 14 * cool),
                int(32 + 22 * glow + 24 * cool),
            )
    draw = ImageDraw.Draw(image)
    # Signature orange frame line and arena accents.
    draw.rectangle((0, 0, 13, 629), fill=ORANGE)
    draw.rounded_rectangle((53, 46, 1146, 583), radius=32, outline=(54, 68, 87), width=3)
    draw.line((54, 524, 1146, 524), fill=(51, 64, 85), width=2)
    # Basketball art — no third-party team logos or NBA endorsement.
    cx, cy, radius = 948, 303, 199
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(233, 115, 39))
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=(255, 181, 104), width=8)
    shadow = (83, 43, 31)
    draw.arc((cx - 145, cy - radius, cx + 145, cy + radius), 88, 272, fill=shadow, width=10)
    draw.arc((cx - 145, cy - radius, cx + 145, cy + radius), 268, 92, fill=shadow, width=10)
    draw.arc((cx - radius, cy - 88, cx + radius, cy + 88), 0, 180, fill=shadow, width=10)
    draw.arc((cx - radius, cy - 88, cx + radius, cy + 88), 180, 360, fill=shadow, width=10)
    draw.line((cx - radius + 5, cy, cx + radius - 5, cy), fill=shadow, width=10)
    draw.line((cx, cy - radius + 5, cx, cy + radius - 5), fill=shadow, width=10)

    # Solid panels keep wording readable in a small Discord thumbnail.
    draw.rounded_rectangle((89, 90, 550, 145), radius=16, fill=(43, 38, 37))
    draw.text((113, 102), "BASKETBALL BOT", font=font(25), fill=ORANGE)
    draw.text((89, 183), "YOUR DISCORD.", font=font(63), fill=WHITE)
    draw.text((89, 267), "OUR COURT.", font=font(76), fill=ORANGE)
    draw.text((93, 379), "UPCOMING NBA GAMES  /  LIVE STATUS", font=font(23, bold=False), fill=MUTED)
    draw.text((93, 421), "DISCORD DASHBOARD  /  COMMUNITY", font=font(23, bold=False), fill=MUTED)
    draw.rounded_rectangle((87, 544, 335, 577), radius=13, fill=(39, 52, 68))
    draw.text((102, 549), "EXPLORE THE DASHBOARD", font=font(16), fill=WHITE)
    draw.text((814, 552), "COMMUNITY PROJECT", font=font(16), fill=MUTED)
    out = BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()
