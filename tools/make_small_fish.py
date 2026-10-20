"""Make mods/fishing/doodads/hwp/fish_small.png: the vanilla pond fish (doodads/terrain/fish.png,
ten 19x20 frames of one fish swimming a loop) shrunk to fit a bucket or a well's basin.
The fish itself is scaled by SCALE and its loop squeezed to PATH_X x PATH_Y px, so every
frame is FW x FH. Same frame order as the vanilla sheet: frame i at (i % 5 * FW, i // 5 * FH).
The vanilla fish are blue, which vanishes in a well's blue water, so these are recoloured
to a koi orange (KOI_HUE, same light and saturation).
Run from the repo root after tools/bootstrap.py (it reads gamecode/sdk/hoh2)."""
from pathlib import Path

import colorsys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "gamecode/sdk/hoh2/doodads/terrain/fish.png"
OUT = ROOT / "mods/fishing/doodads/hwp/fish_small.png"
SCALE = 0.6
FW, FH = 12, 10
PATH_X, PATH_Y = 6.0, 4.0
KOI_HUE = 24 / 360  # the vanilla blues (about 215 degrees) turned orange


def koi(im):
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            _, l, sat = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            r2, g2, b2 = colorsys.hls_to_rgb(KOI_HUE, min(1.0, l * 1.1), sat)
            px[x, y] = (round(r2 * 255), round(g2 * 255), round(b2 * 255), a)
    return out


def pot(n):
    p = 1
    while p < n:
        p *= 2
    return p


def main():
    sheet = Image.open(SRC).convert("RGBA")
    frames = []
    for i in range(10):
        f = sheet.crop(((i % 5) * 19, (i // 5) * 20, (i % 5) * 19 + 19, (i // 5) * 20 + 20))
        box = f.getbbox()
        frames.append((f.crop(box), box))
    cx = [(b[0] + b[2]) / 2 for _, b in frames]
    cy = [(b[1] + b[3]) / 2 for _, b in frames]
    mx, my = (min(cx) + max(cx)) / 2, (min(cy) + max(cy)) / 2
    sx, sy = PATH_X / (max(cx) - min(cx)), PATH_Y / (max(cy) - min(cy))
    # the game only loads power-of-two textures: the 60x20 of frames sits top left of 64x32
    out = Image.new("RGBA", (pot(5 * FW), pot(2 * FH)))
    for i, (blob, _) in enumerate(frames):
        w, h = max(2, round(blob.width * SCALE)), max(2, round(blob.height * SCALE))
        small = blob.resize((w, h), Image.LANCZOS)
        # keep it crisp: alpha snapped to opaque or empty, like the source pixels
        small.putalpha(small.split()[3].point(lambda a: 255 if a >= 96 else 0))
        x = FW / 2 + (cx[i] - mx) * sx - w / 2
        y = FH / 2 + (cy[i] - my) * sy - h / 2
        out.alpha_composite(small, ((i % 5) * FW + round(x), (i // 5) * FH + round(y)))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    koi(out).save(OUT)
    print(f"{OUT.relative_to(ROOT)}: 10 frames of {FW}x{FH}")


if __name__ == "__main__":
    main()
