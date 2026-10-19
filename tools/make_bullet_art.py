"""Writes the Firearms rounds' and missiles' in-flight art into
mods/firearms/players/hwp/firearms/projectiles/:

- rounds.png (128x64; textures must be powers of two or the boot hangs):
  - left half, 16x8 cells: rows plain, fire, ice, lightning, poison; columns rifle f0, f1,
    pistol f0, f1; row 5 the rifle launcher's 40 mm shell f0, f1.
  - right half, 32x16 cells: rows rocket, fatboy, magic, quad; columns f0, f1.
  Everything points right (+x is the flight direction, as crossbow_bolt.png).
- one effect per sprite, laid out as players/projectiles/crossbow_bolt.effect (shadow,
  sprite, trail, light; the rounds have no trail) plus particles for the elemental rounds
  and the missiles:
  round_<rifle|pistol>[_<element>].effect, gl_shell.effect, missile_<name>.effect.
  Rifle-sized rounds are for the rifles, the sniper shot and the turret; pistol rounds
  are a little smaller. Params: angle, height (never r/g/b: those names render wrong).

    python tools/make_bullet_art.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parents[1] / "mods/firearms/players/hwp/firearms/projectiles"
TEX = "./rounds.png"


def h(s: str, a: int = 255) -> tuple:
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def put(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), c)


def draw(img, ox, oy, rows, pal):
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in pal:
                put(img, ox + x, oy + y, pal[ch])


# ---- bullets: 16x8 cells, slug on rows 2-4, nose at x=13 -------------------------------
# rifle / turret round: long jacket, pointed ogive, longer smear (13 x 3)
RIFLE = [
    ["....::sscccb.", ".::;;SSCCCHWw", "....::sscccb."],
    ["...:::sscccb.", "::;;;SSCCCHWw", "...:::sscccb."],
]
# pistol round: a little smaller, a short round-nosed slug, short smear (9 x 3)
PISTOL = [
    ["...:scc..", ".:;SCHW..", "...:scc.."],
    ["..::scc..", ":;;SCHW..", "..::scc.."],
]

ELEMENTS = {
    "plain": {":": h("ffcc66", 70), ";": h("ffd98a", 150), "s": h("8a5a24"), "S": h("c8862e"),
              "c": h("b0642a"), "C": h("e09040"), "b": h("6e3816"), "H": h("ffd27a"), "W": h("fff4d0"), "w": h("ffe6a0", 140)},
    "fire": {":": h("ff5a10", 90), ";": h("ff9a20", 170), "s": h("c02a08"), "S": h("ff6a10"),
             "c": h("e04410"), "C": h("ff9a2a"), "b": h("8a1a06"), "H": h("ffe070"), "W": h("ffffe0"), "w": h("ffd040", 160)},
    "ice": {":": h("7ad8ff", 70), ";": h("b8ecff", 150), "s": h("2a70b0"), "S": h("54a8e6"),
            "c": h("3c8cd0"), "C": h("8cd4ff"), "b": h("1a4a80"), "H": h("dff6ff"), "W": h("ffffff"), "w": h("c8f0ff", 150)},
    "lightning": {":": h("a89cff", 80), ";": h("d4ccff", 160), "s": h("4a3ab0"), "S": h("7a6aef"),
                  "c": h("6a5ae0"), "C": h("b0a6ff"), "b": h("2a1a80"), "H": h("ecebff"), "W": h("ffffff"), "w": h("fff6a0", 170)},
    "poison": {":": h("7ae040", 70), ";": h("a8f070", 150), "s": h("2e7a24"), "S": h("4caa30"),
               "c": h("3c9a2a"), "C": h("8ad850"), "b": h("1c4a18"), "H": h("d6ff9a"), "W": h("f4ffd8"), "w": h("c8ff80", 140)},
}
BULLET_ROWS = ["plain", "fire", "ice", "lightning", "poison"]


def element_marks(img, ox, oy, el, frame, tip, k=1.0):
    """Per-element flourishes around the slug. (ox, oy) is where the slug's rows start
    (oy the cell top), tip the nose's x in them; k shrinks the offsets for the pistol."""
    P = ELEMENTS[el]

    def mark(dx, y, c):  # dx: px behind the nose on the rifle round
        put(img, ox + tip - round(dx * k), oy + y, c)
    if el == "fire":        # flame tongues licking back off the slug
        for dx, y in ([(6, 1), (8, 5), (9, 1)] if frame == 0 else [(7, 5), (9, 1), (10, 5)]):
            mark(dx, y, P[";"])
        mark(5, 1 if frame else 5, h("ffcc40", 200))
    elif el == "ice":       # frost glints above and below the nose
        for dx, y in ([(3, 1), (6, 5)] if frame == 0 else [(4, 5), (7, 1)]):
            mark(dx, y, h("ffffff", 220))
    elif el == "lightning":  # a jagged spark arc flicking off the slug
        for dx, y in ([(4, 1), (5, 0), (7, 1)] if frame == 0 else [(4, 5), (6, 6), (7, 5)]):
            mark(dx, y, h("fff6a0", 230))
    elif el == "poison":    # a drip falling behind
        dx, y = (7, 5) if frame == 0 else (8, 6)
        mark(dx, y, P["C"])
        mark(dx - 1, y, h("a8f070", 120))


def bullets(img):
    for r, el in enumerate(BULLET_ROWS):
        for shape, col0 in ((RIFLE, 0), (PISTOL, 2)):
            for f in (0, 1):
                ox, oy = (col0 + f) * 16, r * 8
                rows = shape[f]
                x0 = 14 - len(rows[0])
                draw(img, ox + x0, oy + 2, rows, ELEMENTS[el])
                if el != "plain":
                    nose = max(i for i, ch in enumerate(rows[1]) if ch != ".")
                    element_marks(img, ox + x0, oy, el, f, nose, 1.0 if shape is RIFLE else 0.6)


# ---- the rifle launcher's 40 mm shell: copper driving band, olive ogive ------------------
SHELL = [
    ["..:boGGGm..", ".:;boGHHGm.", ".:;boGGGGmm", "..:boMMMm.."],
    [".::boGGGm..", "::;boGHHGm.", "::;boGGGGmm", ".::boMMMm.."],
]
SHELL_PAL = {":": h("d8d0c0", 60), ";": h("eee8dc", 120), "b": h("5e400c"), "o": h("d8862e"),
             "G": h("6a7a3a"), "H": h("a8b270"), "M": h("424a26"), "m": h("2a3018")}


def shell(img):
    for f in (0, 1):
        draw(img, f * 16 + 3, 5 * 8 + 2, SHELL[f], SHELL_PAL)


# ---- missiles: 32x16 cells at x 64.., nose at the cell's right edge ---------------------
FLAME = [h("ffffe0"), h("ffe070"), h("ffa030"), h("ff6018", 230), h("c02a08", 170), h("7a1a0e", 90)]
MAGIC_FLAME = [h("ffffff"), h("e8f8ff"), h("a0dcff"), h("ffb040", 230), h("ec7020", 180), h("7a1a0e", 90)]


def flame(img, ox, oy, x_base, cy, length, half, frame, pal):
    """An exhaust plume from x_base (the nozzle) back to the left; frame 1 is longer and
    ragged, so the two frames flicker."""
    n = length + (2 if frame else 0)
    for i in range(n):
        k = i / max(1, n - 1)
        ww = half * (1 - k ** 1.4)
        if frame and i % 3 == 1:
            ww *= 1.25
        for dy in range(-int(round(ww)), int(round(ww)) + 1):
            core = abs(dy) / (half + 0.01)
            idx = min(len(pal) - 1, int(k * (len(pal) - 1) + core * 1.6))
            put(img, ox + x_base - 1 - i, oy + cy + dy, pal[idx])


ROCKET = [  # 17 x 7: olive body, dark fins, red warhead
    "..ff.............",
    "..ffbbbbbbbbbbr..",
    ".ffBMMMMMMMMMMRr.",
    ".nnBMMHHHHHHMMRRw",
    ".ffBmmmmmmmmmmRr.",
    "..ffbbbbbbbbbbr..",
    "..ff.............",
]
ROCKET_PAL = {"f": h("3c3c46"), "n": h("16141c"), "b": h("2c3018"), "B": h("1c1c22"),
              "M": h("5e6836"), "H": h("a8b270"), "m": h("424a26"), "R": h("c42a2a"), "r": h("84161c"), "w": h("f05a4a")}

FATBOY = [  # 22 x 11: a fat green bomb with a hazard band
    "...ff.................",
    "...fff.bbbbbbbbbb.....",
    "...ffbbMMMMMMMMMMbb...",
    "....bMMMHHHHHHHHMMMbr.",
    "..nnBMMYYkkYYkkMMMMRRr",
    "..nnBMMYkkYYkkYMMMMRRw",
    "..nnBMMkkYYkkYYMMMMRRr",
    "....bmmmmmmmmmmmmmmbr.",
    "...ffbbmmmmmmmmmmbb...",
    "...fff.bbbbbbbbbb.....",
    "...ff.................",
]
FATBOY_PAL = {"f": h("2a2a32"), "n": h("101014"), "b": h("1c2a14"), "B": h("141a0c"),
              "M": h("3a6a2a"), "H": h("7ab050"), "m": h("2a4a1c"), "Y": h("e8c040"), "k": h("2a1c06"),
              "R": h("5a8a30"), "r": h("2e4a18"), "w": h("c8ff80")}

MAGIC = [  # 16 x 7: a crystalline ice missile with rune bands and a frost nose
    "..cc............",
    "..ccbbbbbbbbi...",
    ".ccBMMrMMrMMIi..",
    ".nnBMHHrHHrHHIIw",
    ".ccBMMrMMrMMIi..",
    "..ccbbbbbbbbi...",
    "..cc............",
]
MAGIC_PAL = {"c": h("2a70b0"), "n": h("0a1a30"), "b": h("16406e"), "B": h("0a1a30"),
             "M": h("54a8e6"), "H": h("a0dcff"), "r": h("e8f8ff"), "I": h("dff6ff"), "i": h("8cd4ff"), "w": h("ffffff")}

QUAD = [  # 11 x 3: a small grey missile with a red tip
    ".fbbbbbbr..",
    "nfMMHHMMRRw",
    ".fbbbbbbr..",
]
QUAD_PAL = {"f": h("3c3c46"), "n": h("16141c"), "b": h("464b58"), "M": h("9299ab"), "H": h("c8ced8"),
            "R": h("c42a2a"), "r": h("84161c"), "w": h("f05a4a")}

MISSILES = [  # name, rows, palette, flame half-width, flame length, flame palette
    ("rocket", ROCKET, ROCKET_PAL, 2, 9, FLAME),
    ("fatboy", FATBOY, FATBOY_PAL, 3, 10, FLAME),
    ("magic", MAGIC, MAGIC_PAL, 2, 9, MAGIC_FLAME),
    ("quad", QUAD, QUAD_PAL, 1, 6, FLAME),
]


def missiles(img):
    for r, (_, rows, pal, half, length, fpal) in enumerate(MISSILES):
        w, hh = len(rows[0]), len(rows)
        for f in (0, 1):
            ox, oy = 64 + f * 32, r * 16
            x0 = 31 - w
            nozzle = x0 + min(i for i, ch in enumerate(rows[hh // 2]) if ch != ".")
            flame(img, ox, oy, nozzle, 8, length, half, f, fpal)
            draw(img, ox + x0, oy + 8 - hh // 2, rows, pal)


def sheet() -> Image.Image:
    img = Image.new("RGBA", (128, 64), (0, 0, 0, 0))
    bullets(img)
    shell(img)
    missiles(img)
    return img


# ---- effects -----------------------------------------------------------------------------
# element -> (trail rgb, light rgb, speckle color-mul or None)
LOOK = {
    "plain": ((1, 0.82, 0.5), (1, 0.8, 0.45), None),
    "fire": ((1, 0.45, 0.1), (1, 0.45, 0.1), "2.8;0.6;0.1;1"),
    "ice": ((0.55, 0.85, 1), (0.4, 0.75, 1), "0.9;1.8;2.8;1"),
    "lightning": ((0.75, 0.7, 1), (0.6, 0.55, 1), "2.4;2.2;3;1"),
    "poison": ((0.45, 0.9, 0.3), (0.35, 0.85, 0.2), "0.7;2.4;0.4;1"),
}


def sprite_pair(frames: list[str], origin: str, frame_ms: int) -> str:
    fr = "\n".join(f'\t\t<frame time="{frame_ms}">{f}</frame>' for f in frames)
    out = []
    for mat, y in (("shadow", "+height"), ("default", "-height")):
        out.append(f'''\t<sprite looping="true" origin="{origin}" texture="{TEX}" material="system/default.mats:{mat}"
\t\tpos-x="0"
\t\tpos-y="{y}"
\t\tangle="angle">
{fr}
\t</sprite>''')
    return "\n".join(out)


def trail(rgb, back: float, size: float, alpha: float) -> str:
    # wpos-track and segments stay at 3: 8 drew a screen-wide line at rifle speed
    return f'''\t<trail texture="special/empty.png" material="system/default.mats:default-simple">
\t\t<pos-x value="wposx(i)+cos(angle)*-{back}" />
\t\t<pos-y value="-height+(wposy(i))+sin(angle)*-{back}" />
\t\t<angle value="angle"/>
\t\t<length value="1000" />
\t\t<looping value="true" />
\t\t<segments value="3" />
\t\t<size value="{size}-(({size}/3)*i)" />
\t\t<uv-x value="0" />
\t\t<uv-y value="0" />
\t\t<color-r value="{rgb[0]}" />
\t\t<color-g value="{rgb[1]}" />
\t\t<color-b value="{rgb[2]}" />
\t\t<color-a value="{alpha}-i*({alpha / 3:.3f})" />
\t</trail>'''


def light(rgb, size: int, mul: float) -> str:
    return f'''\t<light pos-x="cos(angle)*2" pos-y="-height+sin(angle)*2">
\t\t<sprite texture="effects/lights/light2_L.png">
\t\t\t<frame time="800">0 0 128 128</frame>
\t\t</sprite>
\t\t<looping value="true" />
\t\t<length value="150" />
\t\t<cast-shadows value="false" />
\t\t<size value="{size}" />
\t\t<color-r value="{rgb[0] * mul:.2f}" />
\t\t<color-g value="{rgb[1] * mul:.2f}" />
\t\t<color-b value="{rgb[2] * mul:.2f}" />
\t\t<color-a value="0"/>
\t</light>'''


def speckles(color_mul: str, rate: int, back: float, ttl: str) -> str:
    """Additive sparks shed behind the round (vanilla crossbow_bolt_explosive's embers)."""
    return f'''\t<particle_spawner
\t\tspawn-rate="{rate}"
\t\tlength="200"
\t\tlooping="true"
\t\tttl="{ttl}"
\t\tangle="0"
\t\tpos="cos(angle)*-{back};-height+sin(angle)*-{back};0"
\t\tcolor-mul="{color_mul}"
\t\trot-speed="rpick(-2.2,2.2)"
\t\trot-damping="2"
\t\tforce-damping="rpick(1,3)">
\t\t<behaviors>
\t\t\t<spread_range radius="rpick(0,1.5)"/>
\t\t\t<force_dir dir="cos(angle)*-0.2;sin(angle)*-0.2;0"/>
\t\t\t<fade_to a="0" r="0" g="0" b="0" />
\t\t</behaviors>
\t\t<particle src="effects/subeffects/particles_speckles.unit:single_grey200_add_offset_2"/>
\t\t<particle src="effects/subeffects/particles_speckles.unit:single_grey200_add"/>
\t</particle_spawner>'''


def smoke(rate: int, back: float, grey: int) -> str:
    return f'''\t<particle_spawner
\t\tspawn-rate="{rate}"
\t\tlength="200"
\t\tlooping="true"
\t\tttl="rpick(350,800)"
\t\tangle="0"
\t\tpos="cos(angle)*-{back};-height+sin(angle)*-{back};0"
\t\tcolor="{grey} {grey} {grey} {grey}"
\t\tcolor-mul="1;1;1;1"
\t\trot-speed="rpick(-2.2,2.2)"
\t\trot-damping="2"
\t\tforce-damping="rpick(1,3)">
\t\t<behaviors>
\t\t\t<spread_range radius="rpick(0,1)"/>
\t\t\t<force_dir dir="cos(angle);sin(angle);0"/>
\t\t\t<fade_to a="0" r="0" g="0" b="0" />
\t\t</behaviors>
\t\t<particle src="effects/subeffects/particles_grayscale.unit:smoke_1_tiny-grow"/>
\t\t<particle src="effects/subeffects/particles_grayscale.unit:smoke_2_tiny-grow"/>
\t</particle_spawner>'''


def effect(comment: str, body: list[str]) -> str:
    return (f"<!-- {comment} Generated by tools/make_bullet_art.py; edit that, not this. -->\n"
            '<effect looping="true" wpos-track="3">\n'
            '\t<param name="angle" default="0" />\n'
            '\t<param name="height" default="0" />\n\n'
            + "\n\n".join(body) + "\n</effect>\n")


def effects() -> dict[str, str]:
    out = {}
    for r, el in enumerate(BULLET_ROWS):
        _trail_rgb, light_rgb, specks = LOOK[el]
        suffix = "" if el == "plain" else "_" + el
        for kind, col0, origin, back in (("rifle", 0, "9 3.5", 4), ("pistol", 2, "10 3.5", 2)):
            frames = [f"{(col0 + f) * 16} {r * 8} 16 8" for f in (0, 1)]
            # no trail on a round: only the missiles keep one
            body = [sprite_pair(frames, origin, 60)]
            if specks:
                body.append(speckles(specks, 10 if kind == "rifle" else 7, back, "rpick(150,350)"))
            body.append(light(light_rgb, 40 if kind == "rifle" else 30, 0.2 if el == "plain" else 0.35))
            what = "rifle/turret" if kind == "rifle" else "pistol (a little smaller)"
            out[f"round_{kind}{suffix}.effect"] = effect(f"A {what} round, {el}.", body)
    out["gl_shell.effect"] = effect("The rifle launcher's 40 mm shell.", [
        sprite_pair([f"{f * 16} 40 16 8" for f in (0, 1)], "8 3.5", 80),
        smoke(20, 4, 120),
        light((1, 0.75, 0.4), 30, 0.15)])
    for r, (name, rows, *_rest) in enumerate(MISSILES):
        frames = [f"{64 + f * 32} {r * 16} 32 16" for f in (0, 1)]
        tail = 31 - len(rows[0])          # where the body starts in the cell
        back = 24 - tail                  # origin x is 24: px from origin to the nozzle
        if name == "magic":
            extra = [speckles("0.9;1.8;2.8;1", 24, back, "rpick(250,500)"), smoke(10, back, 90)]
            lrgb = (0.45, 0.75, 1)
        elif name == "fatboy":
            extra = [speckles("2.8;0.6;0.1;1", 24, back, "rpick(300,700)"), smoke(40, back, 155)]
            lrgb = (1, 0.55, 0.2)
        else:
            extra = [speckles("2.8;0.5;0.05;1", 16 if name == "quad" else 22, back, "rpick(250,600)"),
                     smoke(18 if name == "quad" else 32, back, 155)]
            lrgb = (1, 0.55, 0.2)
        body = [sprite_pair(frames, "24 8", 50)] + extra + [
            trail((1, 0.7, 0.35) if name != "magic" else (0.6, 0.85, 1), back, 2 if name != "quad" else 1.2, 0.5),
            light(lrgb, 70 if name == "fatboy" else (40 if name == "quad" else 56), 0.35)]
        out[f"missile_{name}.effect"] = effect(f"Missile: {name}.", body)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sheet().save(OUT / "rounds.png")
    for name, text in effects().items():
        (OUT / name).write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote rounds.png and {len(effects())} effects in {OUT}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:          # an output dir, for previews
        OUT = Path(sys.argv[1])
    main()
