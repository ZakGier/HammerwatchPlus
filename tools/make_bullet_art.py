"""Writes mods/firearms/players/hwp/firearms/projectiles/bullet.png: the gun rounds' sprite.

A 6x3 slug on an 8x8 sheet, pointing right (+x is the shot's direction, as crossbow_bolt.png), drawn in
greys so bullet.effect can tint it per round: brass for plain rounds, an element's color
for elemental ones (color-r/g/b multiply the texel). Row 0-2 of frame 0; frame 1 (rows
3-5) is the same slug a shade brighter, so the round flickers like the bolt does.

    python tools/make_bullet_art.py
"""
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parents[1] / "mods/firearms/players/hwp/firearms/projectiles/bullet.png"

# grey levels per pixel, back (left) to tip (right); 0 is transparent
SLUG = [
    [0, 0, 150, 190, 170, 0],
    [110, 170, 230, 255, 255, 210],
    [0, 0, 120, 150, 140, 0],
]


def main() -> None:
    img = Image.new("RGBA", (8, 8), (0, 0, 0, 0))   # textures must be a power of two
    for frame, gain in ((0, 1.0), (1, 1.12)):
        for y, row in enumerate(SLUG):
            for x, v in enumerate(row):
                if v:
                    g = min(255, round(v * gain))
                    img.putpixel((x, frame * 3 + y), (g, g, g, 255))
    img.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
