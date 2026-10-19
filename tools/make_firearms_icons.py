"""Builds the Firearms Specialist's icon atlases from art/firearms/.

    python tools/make_firearms_icons.py           # write both atlases and the preview
    python tools/make_firearms_icons.py --check   # report icon refs in mods/firearms that
                                                  # point at no icon; write nothing

Outputs (24x24 cells, x = col * 24, y = row * 24, as the .sval icon rects expect; each sheet
padded to power-of-two sides, which the engine requires):
- mods/firearms/players/hwp/firearms/icons.png   skills, orbs, attacks, HUD stacks
- mods/firearms/items/hwp/firearms_items.png     inventory icons of the guns
- art/firearms/preview.png                       both sheets x4 with names (not shipped)

Where each icon's pixels come from, first match wins:
1. art/firearms/override/<name>.png: hand-made art. Any size: a 24x24 is used as is, a
   whole multiple of 24 is scaled down by that factor (nearest), a 14x14 (vanilla's buff-bar
   size, for the *_hud stack icons) goes in the cell's top-left corner unscaled and the
   stacks point at it with a 14x14 rect, anything else is fitted
   with a smooth resize and then snapped to 32 colours and hard alpha. Export it from
   Aseprite, LibreSprite or Pixelorama (or any editor) as a PNG with transparency.
2. The placeholder in ICONS below: sprites from art/firearms/sprites.txt (ASCII pixel
   grids), recoloured and badged, over a glowing background in the skill's element colour,
   as vanilla's players/icons_skills.png. Item icons get no background (icons_equipment.png).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "art" / "firearms"
MOD = ROOT / "mods" / "firearms"
SKILLS_PNG = MOD / "players" / "hwp" / "firearms" / "icons.png"
ITEMS_PNG = MOD / "items" / "hwp" / "firearms_items.png"
CELL = 24
HUD = 14  # vanilla's buff-bar icon size

PALETTE = {
    "k": (22, 18, 26), "x": (28, 22, 30),
    "d": (52, 56, 66), "m": (96, 102, 116), "M": (150, 158, 172), "W": (232, 236, 240),
    "b": (70, 44, 26), "B": (118, 76, 42), "n": (168, 116, 66),
    "o": (62, 74, 36), "O": (98, 118, 52), "L": (146, 166, 80),
    "r": (120, 24, 24), "R": (204, 52, 44), "f": (232, 110, 28), "F": (255, 186, 58),
    "y": (176, 128, 28), "Y": (236, 196, 72),
    "c": (34, 104, 156), "C": (92, 182, 232), "I": (206, 240, 255),
    "u": (52, 84, 170), "U": (130, 170, 250),
    "p": (82, 44, 112), "P": (154, 96, 206),
    "g": (44, 100, 36), "G": (112, 186, 64), "v": (184, 236, 96),
    "w": (232, 226, 210),
}
OUTLINE = (16, 12, 20, 255)

# element -> (glow at the centre, edge)
BG = {
    "phys": ((104, 112, 128), (16, 18, 26)),
    "fire": ((206, 92, 30), (30, 10, 8)),
    "ice": ((70, 152, 206), (8, 20, 36)),
    "light": ((112, 100, 226), (14, 12, 40)),
    "poison": ((92, 164, 52), (10, 26, 10)),
    "gold": ((206, 162, 52), (30, 22, 8)),
    "blood": ((176, 42, 40), (28, 6, 8)),
    "arcane": ((122, 72, 196), (18, 10, 32)),
}

# Colour swaps for variants (letter -> letter).
STUN = {"O": "m", "L": "M", "o": "d"}
FIRE = {"O": "R", "L": "f", "o": "r"}
GAS = {"O": "G", "L": "v", "o": "g"}
ICE = {"R": "C", "r": "c", "m": "I", "M": "W", "d": "C", "F": "I", "f": "C"}
STEEL = {"m": "u", "M": "U", "d": "x"}
GOLD = {"m": "y", "M": "Y", "d": "y"}
DARKWOOD = {"B": "b", "n": "B", "m": "d", "M": "m"}
GILDED = {"n": "Y", "M": "Y", "m": "y"}


def L(sprite, x=None, y=None, swap=None, flip=False, rot=0, scale=1):
    """A layer: a sprite at (x, y) in the cell; None centres it."""
    return {"sprite": sprite, "x": x, "y": y, "swap": swap or {}, "flip": flip, "rot": rot, "scale": scale}


def badge(name, swap=None):
    return {"sprite": name, "x": "badge", "y": "badge", "swap": swap or {}, "flip": False, "rot": 0, "scale": 1}


# name: (atlas, col, row, background element or None, layers). The name is the override
# file name and the preview label. Legacy icons (the base passives, Assault, and the skills
# no longer in the class) are kept as they were drawn: art/firearms/override/<name>.png.
ICONS = {
    # row 0: skills
    "reload": ("skills", 0, 0, "phys", [L("mag", 5, 4), badge("b_reload")]),
    "frag": ("skills", 1, 0, "phys", [L("grenade")]),
    "stun_grenade": ("skills", 2, 0, "light", [L("grenade", swap=STUN), badge("b_bolt")]),
    "incendiary": ("skills", 3, 0, "fire", [L("grenade", swap=FIRE), badge("b_flame")]),
    "gas": ("skills", 4, 0, "poison", [L("grenade", swap=GAS), badge("b_cloud")]),
    "snipe": ("skills", 5, 0, "phys", [L("rifle", 2, 8), badge("b_cross")]),
    "critical_aim": ("skills", 6, 0, "gold", [L("crosshair"), badge("b_star")]),
    "rocket": ("skills", 7, 0, "fire", [L("rocket")]),
    "hoarder": ("skills", 8, 0, "gold", [L("crate", 4, 5), badge("b_plus")]),
    "scavenger": ("skills", 9, 0, None, []),
    # row 1: orbs
    "dodge_skip": ("skills", 0, 1, "arcane", [L("mag", 5, 4), badge("b_dash")]),
    "explosive_reload": ("skills", 1, 1, "fire", [L("mag", 5, 4), badge("b_boom")]),
    "over_reload": ("skills", 2, 1, "gold", [L("mag", 5, 4), badge("b_plus")]),
    "headshot": ("skills", 3, 1, "blood", [L("skull", 4, 4), badge("b_cross")]),
    "piercing": ("skills", 4, 1, "phys", [L("bullet", 4, 6), badge("b_arrow")]),
    "boom_headshot": ("skills", 5, 1, "gold", [L("skull", 4, 4), badge("b_boom")]),
    "exposure": ("skills", 6, 1, "arcane", [L("crosshair", 3, 3), badge("b_elements")]),
    "fat_boy": ("skills", 7, 1, "poison", [L("nuke", 3, 5), badge("b_rad")]),
    "magic_missile": ("skills", 8, 1, "ice", [L("rocket", swap=ICE), badge("b_snow")]),
    "quad_missile": ("skills", 9, 1, "fire", [L("minirocket", 2, 3), L("minirocket", 13, 6),
                                              L("minirocket", 4, 12), L("minirocket", 14, 16)]),
    # row 2: orbs, attacks, HUD
    "shrapnel": ("skills", 0, 2, "arcane", [L("shards", 3, 3), badge("b_elements")]),
    "overpacked": ("skills", 1, 2, "fire", [L("dynamite", 4, 3), badge("b_plus")]),
    "rifle_attack": ("skills", 2, 2, "phys", [L("rifle")]),
    "glock_attack": ("skills", 3, 2, "phys", [L("pistol")]),
    "glock_dual": ("skills", 4, 2, "phys", [L("pistol", 1, 3), L("pistol", 8, 11, flip=True)]),
    "steady": ("skills", 5, 2, None, []),
    "focus_hud": ("skills", 6, 2, "gold", [L("crosshair")]),
    "grenade_charges_hud": ("skills", 7, 2, "phys", [L("grenade"), badge("b_plus")]),
    "rocket_charges_hud": ("skills", 8, 2, "fire", [L("rocket"), badge("b_plus")]),
    "clip_hud": ("skills", 9, 2, "phys", [L("bullet", 4, 7, rot=90), L("bullet", 10, 7, rot=90),
                                          L("bullet", 16, 7, rot=90)]),
    # row 3: Assault (as drawn), the grenade launcher, reloading
    "burst": ("skills", 0, 3, None, []),
    "adrenaline": ("skills", 1, 3, None, []),
    # Engineer (planned): override art only, no skill files yet
    "turret": ("skills", 3, 3, None, []),
    "my_turret": ("skills", 4, 3, None, []),
    "gl_attack": ("skills", 7, 3, "phys", [L("rifle", 2, 6), badge("b_grenade")]),
    "reloading_hud": ("skills", 8, 3, "arcane", [L("b_reload", scale=2)]),
    # orbs and HUD icons for the class-planner skills (hand-drawn overrides)
    "turret_reinforced": ("skills", 2, 3, None, []),
    "turret_second": ("skills", 5, 3, None, []),
    "myturret_feed": ("skills", 6, 3, None, []),
    "myturret_shared": ("skills", 9, 3, None, []),
    "burst_breath": ("skills", 0, 4, None, []),
    "burst_triple": ("skills", 1, 4, None, []),
    "adrenaline_crit": ("skills", 2, 4, None, []),
    "adrenaline_epipen": ("skills", 3, 4, None, []),
    "steady_crit": ("skills", 4, 4, None, []),
    "frag_shrapnel": ("skills", 5, 4, None, []),
    "rpg_jump": ("skills", 6, 4, None, []),
    "adrenaline_hud": ("skills", 7, 4, None, []),
    "gl_charges_hud": ("skills", 8, 4, None, []),
    "scavenger_fire": ("skills", 0, 5, None, []),
    "scavenger_ice": ("skills", 1, 5, None, []),
    "scavenger_poison": ("skills", 2, 5, None, []),
    "scavenger_lightning": ("skills", 3, 5, None, []),
    "scavenger_blind": ("skills", 4, 5, None, []),
    "scavenger_slow": ("skills", 5, 5, None, []),
    "scavenger_stun": ("skills", 6, 5, None, []),
    # items: the guns' inventory icons, one per item tier
    "rifle_01": ("items", 0, 0, None, [L("rifle")]),
    "rifle_02": ("items", 1, 0, None, [L("rifle", swap=DARKWOOD)]),
    "rifle_03": ("items", 2, 0, None, [L("rifle", swap=GILDED)]),
    "glock_mh_01": ("items", 3, 0, None, [L("pistol")]),
    "glock_mh_02": ("items", 4, 0, None, [L("pistol", swap=STEEL)]),
    "glock_mh_03": ("items", 5, 0, None, [L("pistol", swap=GOLD)]),
    "glock_oh_01": ("items", 6, 0, None, [L("pistol", flip=True)]),
    "glock_oh_02": ("items", 7, 0, None, [L("pistol", swap=STEEL, flip=True)]),
    "glock_oh_03": ("items", 8, 0, None, [L("pistol", swap=GOLD, flip=True)]),
    # close-ups of the rifles' under-barrel launcher, for the off-hand slot
    "rifle_gl_01": ("items", 0, 1, None, [L("rifle", 2, 6)]),
    "rifle_gl_02": ("items", 1, 1, None, [L("rifle", 2, 6, swap=DARKWOOD)]),
    "rifle_gl_03": ("items", 2, 1, None, [L("rifle", 2, 6, swap=GILDED)]),
}
ATLAS_SIZE = {"skills": (10, 6), "items": (9, 2)}


def load_sprites(path: Path) -> dict[str, list[str]]:
    sprites: dict[str, list[str]] = {}
    name = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("#"):
            continue
        m = re.match(r"^==\s*(\S+)", line)
        if m:
            name = m.group(1)
            sprites[name] = []
        elif name and line:
            sprites[name].append(line)
    for n, rows in sprites.items():
        for r in rows:
            bad = sorted({c for c in r if c != "." and c not in PALETTE})
            if bad:
                raise SystemExit(f"sprites.txt: {n}: unknown palette letter(s) {bad}")
    return sprites


def render_sprite(rows: list[str], swap: dict[str, str]) -> Image.Image:
    w = max(len(r) for r in rows)
    im = Image.new("RGBA", (w, len(rows)), (0, 0, 0, 0))
    px = im.load()
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != ".":
                px[x, y] = PALETTE[swap.get(c, c)] + (255,)
    return im


def outlined(im: Image.Image) -> Image.Image:
    """The sprite with a 1 px dark outline (4-neighbours) and a soft shadow down-right."""
    w, h = im.size
    out = Image.new("RGBA", (w + 3, h + 3), (0, 0, 0, 0))
    src = im.load()
    po = out.load()
    solid = {(x, y) for y in range(h) for x in range(w) if src[x, y][3] > 0}
    for (x, y) in solid:
        po[x + 2, y + 2] = (0, 0, 0, 110)
    for (x, y) in solid:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            po[x + 1 + dx, y + 1 + dy] = OUTLINE
    for (x, y) in solid:
        po[x + 1, y + 1] = src[x, y]
    return out


def background(element: str) -> Image.Image:
    """A radial glow, dithered to 5 steps (4x4 Bayer) so it reads as pixel art."""
    centre, edge = BG[element]
    bayer = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
    im = Image.new("RGBA", (CELL, CELL))
    px = im.load()
    c = (CELL - 1) / 2
    for y in range(CELL):
        for x in range(CELL):
            d = min(1.0, (((x - c) ** 2 + (y - c - 2) ** 2) ** 0.5) / (CELL * 0.62))
            t = (1 - d) ** 1.4 * 4 + bayer[y % 4][x % 4] / 16 - 0.5
            t = max(0, min(4, round(t))) / 4
            px[x, y] = tuple(int(edge[i] + (centre[i] - edge[i]) * t) for i in range(3)) + (255,)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, CELL - 1, CELL - 1), outline=tuple(int(v * 0.6) for v in edge) + (255,))
    return im


def build_icon(name: str, spec, sprites) -> Image.Image:
    over = ART / "override" / f"{name}.png"
    if over.exists():
        return load_override(over)
    _, _, _, element, layers = spec
    cell = background(element) if element else Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    for layer in layers:
        if layer["sprite"] not in sprites:
            raise SystemExit(f"{name}: no sprite '{layer['sprite']}' in sprites.txt")
        im = render_sprite(sprites[layer["sprite"]], layer["swap"])
        if layer["flip"]:
            im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if layer["rot"] == 90:
            im = im.transpose(Image.Transpose.ROTATE_90)
        if layer["scale"] != 1:
            im = im.resize((im.width * layer["scale"], im.height * layer["scale"]), Image.Resampling.NEAREST)
        im = outlined(im)
        if layer["x"] == "badge":
            x, y = CELL - im.width, CELL - im.height
        else:
            x = (CELL - im.width) // 2 if layer["x"] is None else layer["x"] - 1
            y = (CELL - im.height) // 2 if layer["y"] is None else layer["y"] - 1
        cell.alpha_composite(im, (max(0, x), max(0, y)))
    return cell


def load_override(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    if im.size == (CELL, CELL):
        return im
    if im.size == (HUD, HUD):
        out = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        out.paste(im, (0, 0))
        return out
    if im.width == im.height and im.width % CELL == 0:
        return im.resize((CELL, CELL), Image.Resampling.NEAREST)
    im.thumbnail((CELL, CELL), Image.Resampling.LANCZOS)
    alpha = im.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
    rgb = im.convert("RGB").quantize(32, dither=Image.Dither.NONE).convert("RGB")
    out = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    rgb.putalpha(alpha)
    out.alpha_composite(rgb, ((CELL - im.width) // 2, (CELL - im.height) // 2))
    return out


def pot(n: int) -> int:
    p = 1
    while p < n:
        p *= 2
    return p


def build() -> dict[str, Image.Image]:
    sprites = load_sprites(ART / "sprites.txt")
    # the engine refuses textures whose sides are not powers of two (TextureLoader), so the
    # sheet is padded out with transparent space
    sheets = {a: Image.new("RGBA", (pot(c * CELL), pot(r * CELL)), (0, 0, 0, 0)) for a, (c, r) in ATLAS_SIZE.items()}
    for name, spec in ICONS.items():
        atlas, col, row, element, layers = spec
        if element is None and not layers and not (ART / "override" / f"{name}.png").exists():
            raise SystemExit(f"{name}: no layers and no override png")
        sheets[atlas].alpha_composite(build_icon(name, spec, sprites), (col * CELL, row * CELL))
    return sheets


def preview(sheets: dict[str, Image.Image]) -> Image.Image:
    z, label = 4, 14
    cols = max(c for c, _ in ATLAS_SIZE.values())
    rows = sum(r for _, r in ATLAS_SIZE.values())
    out = Image.new("RGBA", (cols * CELL * z, rows * (CELL * z + label)), (40, 40, 48, 255))
    d = ImageDraw.Draw(out)
    top = 0
    for atlas, (c, r) in ATLAS_SIZE.items():
        big = sheets[atlas].crop((0, 0, c * CELL, r * CELL)).resize((c * CELL * z, r * CELL * z), Image.Resampling.NEAREST)
        for ry in range(r):
            out.alpha_composite(big.crop((0, ry * CELL * z, c * CELL * z, (ry + 1) * CELL * z)),
                                (0, top + ry * (CELL * z + label)))
        for name, (a, col, row, _, _) in ICONS.items():
            if a == atlas:
                d.text((col * CELL * z + 2, top + row * (CELL * z + label) + CELL * z), name[:16], fill=(220, 220, 220, 255))
        top += r * (CELL * z + label)
    return out


def check() -> int:
    """Every icon rect in mods/firearms that points at our atlases must name an icon."""
    cells = {(a, col * CELL, row * CELL) for a, col, row, _, _ in ICONS.values()}
    pat = re.compile(r"(players/hwp/firearms/icons\.png|items/hwp/firearms_items\.png)</(?:s|string)>\s*"
                     r"<(?:i|int)>\d+</(?:i|int)>\s*<vec4>(\S+) (\S+) (?:24 24|14 14)</vec4>")
    bad = 0
    for f in sorted(MOD.rglob("*.sval")):
        text = f.read_text(encoding="utf-8")
        for m in pat.finditer(text):
            atlas = "skills" if m.group(1).endswith("icons.png") else "items"
            x, y = m.group(2), m.group(3)
            if not (x.isdigit() and y.isdigit()):
                continue  # a %%X%% block parameter
            if (atlas, int(x), int(y)) not in cells:
                bad += 1
                line = text.count("\n", 0, m.start()) + 1
                print(f"{f.relative_to(ROOT)}:{line}: {atlas} {x} {y} is no icon")
    print("icon refs ok" if not bad else f"{bad} icon ref(s) point at no icon")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="only check the icon refs in mods/firearms")
    args = ap.parse_args(argv)
    if args.check:
        return check()
    sheets = build()
    for atlas, path in (("skills", SKILLS_PNG), ("items", ITEMS_PNG)):
        path.parent.mkdir(parents=True, exist_ok=True)
        sheets[atlas].save(path)
        print("wrote", path.relative_to(ROOT))
    preview(sheets).save(ART / "preview.png")
    print("wrote", (ART / "preview.png").relative_to(ROOT))
    return check()


if __name__ == "__main__":
    sys.exit(main())
