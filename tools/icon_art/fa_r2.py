"""Firearms Specialist icons, round 2: three new ideas for each icon, built on the user's
round-1 pick and note (out/picks_r1.json). Buff-bar stack icons (*_hud) are painted at
their in-game 14x14. python fa_r2.py [names...] -> out/firearms_r2/<name>_<a|b|c>.png and
out/sheet_r2_<i>.png (the pick, now, beside the three)."""
import math
import sys
from pathlib import Path
from PIL import Image
from vpaint import *
from motifs import *
from fa import pineapple, canister, blast, shards, REPO
from fa3 import epipen

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "firearms_r2"
ELEMS = [FIRE, ICE, VOLT, TOXIC]
# the armor break debuff's own 9x9 icon (special/icons/armorbreak.unit), for frag_shrapnel
ARMORBREAK = (REPO / "gamecode/sdk/hoh2/special/icons/icons.png", (90, 0, 99, 9))


def G(dark, mid, light=(8, 6), n=24):
    return Icon(n).ground(dark, mid, light=light)


def S(dark, mid, light=(5, 4)):
    """A 14x14 buff-bar stack icon's ground."""
    return G(dark, mid, light, 14)


def line(ic, pts, w, rmp, falloff=0.8):
    ic.energy(union(*(seg(*pts[i], *pts[i + 1], w) for i in range(len(pts) - 1))), rmp, falloff=falloff)


def reticle(ic, cx, cy, r, w=0.5, rmp=BLOOD, ticks=True, gap=None):
    """A red crosshair: a ring with four ticks crossing it."""
    fs = [ring(cx, cy, r, w * 2)]
    if ticks:
        t = r * 0.55
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            fs.append(seg(cx + dx * (r - t), cy + dy * (r - t), cx + dx * (r + t), cy + dy * (r + t), w))
    f = union(*fs)
    if gap:
        f = cut(f, circle(cx, cy, gap))
    ic.energy(f, rmp, falloff=w * 1.6)


def paste(ic, src, box_, x, y):
    """Paste a sprite region (with alpha) at (x, y)."""
    im = Image.open(src).convert("RGBA").crop(box_)
    for yy in range(im.height):
        for xx in range(im.width):
            c = im.getpixel((xx, yy))
            if c[3] and 0 <= x + xx < ic.n and 0 <= y + yy < ic.n:
                ic.p[x + xx, y + yy] = mix(ic.p[x + xx, y + yy], c[:3], c[3] / 255)


def nuke(ic, cx, cy, r, disc=GOLD, dark=(24, 20, 8), rot=0):
    """A radiation trefoil: a dark-rimmed yellow disc, three dark blades and a dark hub.
    rot turns the blades (degrees); 0 puts one blade straight up."""
    ic.paint(circle(cx, cy, r + 0.9), lambda x, y, d: dark)
    ic.solid(circle(cx, cy, r), disc, base=3.6, spread=1, seed=7)

    def blades(x, y):
        d = math.hypot(x - cx, y - cy)
        a = math.degrees(math.atan2(y - cy, x - cx)) + 90 - rot
        k = ((a + 60) % 120) - 60
        return -1 if (abs(k) < 31 and r * 0.4 < d < r * 0.98) or d < r * 0.24 else 1
    ic.paint(blades, lambda x, y, d: dark)


# ---------------------------------------------------------------- adrenaline
ECG = [(0, 14), (6, 14), (8, 9), (10, 19), (13, 4), (15, 16), (17, 14), (24, 14)]
YEL = ("100c04", "2a2208")


def adrenaline():
    # the picked heartbeat line, in yellow
    A = G(*YEL, (12, 14))
    line(A, ECG, 0.6, GOLD)
    A.glow(12, 12, 8, "ffe070", 0.5)
    # a hotter line with a dim echo trailing it
    B = G("0e0a02", "241c06", (12, 14))
    line(B, [(x - 1.5, y + 1) for x, y in ECG], 0.5, GOLD[:4], falloff=0.5)
    line(B, ECG, 0.75, VOLT)
    B.glow(13, 5, 6, "fff0a0", 0.7)
    # a racing pulse: the beats bunched up, each spike taller than the last
    C = G(*YEL, (12, 14))
    pts = [(0, 14), (3, 14), (4.5, 11), (6, 16), (7.5, 14), (9.5, 14), (11, 8), (12.5, 18), (14, 14), (15.5, 14),
           (17, 3), (19, 20), (20.5, 14), (24, 14)]
    line(C, pts, 0.6, GOLD)
    C.glow(17, 6, 7, "ffe070", 0.6)
    return A, B, C


def adrenaline_crit():
    # the picked gold heartbeat, its top splotch now a red crosshair on the peak
    A = G("100406", "2a0a0e", (12, 12))
    line(A, ECG, 0.6, GOLD)
    reticle(A, 13, 4.5, 3.2, 0.45)
    # the crosshair big behind the line, the spike stabbing through its centre
    B = G("100406", "2a0a0e", (12, 12))
    reticle(B, 12.5, 9, 6.5, 0.5)
    line(B, ECG, 0.6, GOLD)
    B.glow(13, 5, 5, "ffe070", 0.6)
    # the crosshair in the corner like a badge, the line climbing to it
    C = G("100406", "2a0a0e", (10, 14))
    pts = [(0, 16), (5, 16), (7, 12), (9, 20), (12, 8), (14, 17), (16, 15), (18, 15), (19.5, 6)]
    line(C, pts, 0.6, GOLD)
    reticle(C, 19.5, 5, 3.4, 0.45)
    return A, B, C


def needle_pen(ic, cx, cy, ang, s=1.0, needle=2.6):
    epipen(ic, cx, cy, ang, s)
    parts(ic, cx, cy, ang, s, [(lseg(9.3, 0, 9.3 + needle, 0, 0.32, 0.12), STEEL, {"base": 4.2, "spread": 0.6, "rim": 0.4})])


def adrenaline_epipen():
    A = G("100e04", "2a2608", (12, 8))
    A.glow(12, 12, 9, "e0c028", 0.5)
    needle_pen(A, 11, 13, -45, 1.1)
    # the needle out, a bead of yellow at its point
    B = G("100e04", "2a2608", (12, 8))
    B.glow(12, 12, 9, "e0c028", 0.5)
    needle_pen(B, 10.5, 13.5, -45, 1.05, needle=3.2)
    B.energy(circle(20.6, 3.4, 0.9), VOLT, falloff=0.9)
    # steeper and closer, a glint on the barrel
    C = G("100e04", "262208", (14, 6))
    C.glow(15, 8, 10, "e0c028", 0.6)
    needle_pen(C, 10, 14, -60, 1.25, needle=2.4)
    C.glint(12, 9)
    return A, B, C


def adrenaline_hud():
    # 14x14: the heartbeat from adrenaline_crit, small and yellow
    pts = [(0, 8.5), (3, 8.5), (4.2, 5.8), (5.6, 11.2), (7.4, 2.4), (8.8, 9.6), (10, 8.5), (14, 8.5)]
    A = S(*YEL, (7, 8))
    line(A, pts, 0.42, GOLD, falloff=0.6)
    B = S("0e0a02", "2a2008", (7, 4))
    B.glow(7.5, 4, 6, "ffe070", 0.7)
    line(B, pts, 0.5, VOLT, falloff=0.7)
    C = S("140406", "340a0e", (7, 8))
    line(C, pts, 0.5, GOLD, falloff=0.7)
    return A, B, C


# ---------------------------------------------------------------- shotgun
def burst():
    # two shells kicked apart by the blast between their mouths
    A = G("140804", "34160a", (12, 6))
    A.glow(12, 6, 10, "ff9030", 0.8)
    for k, (x, a) in enumerate(((7, -110), (17, -70))):
        shell(A, x, 15.5, a, 1.05, seed=k, length=14, w=2.0)
    blast(A, 12, 5, 4.2, FIRE, 7)
    for (x, y) in ((4, 3), (20, 2), (2, 9), (22, 8)):
        A.glint(x, y, GOLD[5], arm=0)
    # the same blast bigger, rays behind it
    B = G("140804", "3a1608", (12, 5))
    B.rays(12, 5, EMBER, n=8, lo=0, hi=3)
    for k, (x, a) in enumerate(((6, -115), (18, -65))):
        shell(B, x, 17, a, 1.0, seed=k, length=14, w=2.0)
    blast(B, 12, 5, 5.5, FIRE, 7)
    # close: the shells cropped by the frame's foot, fire filling the top
    C = G("140604", "30100a", (12, 8))
    for k, (x, a) in enumerate(((5, -105), (19, -75))):
        shell(C, x, 19, a, 1.3, seed=k, length=14, w=2.0)
    blast(C, 12, 6, 7, FIRE, 6)
    return A, B, C


def burst_breath():
    # a shell lying on its side, fire roaring out of its open end
    A = G("140604", "34100a", (14, 12))
    A.glow(16, 12, 11, "ff6010", 0.8)
    A.energy(lambda x, y: (abs(y - 12) - ((x - 9) * 0.5 + 1.4) * (0.85 + 0.15 * math.sin(x * 1.4))) if x > 9 else 1, FIRE, falloff=4)
    shell(A, 5.5, 12, 0, 1.15)
    # the shell tipped up, a jet of fire out of its mouth to the corner
    B = G("140604", "34100a", (16, 8))
    B.glow(16, 8, 11, "ff6010", 0.8)
    B.energy(lambda x, y: seg(11, 13, 25, -1, 1.2, 8)(x, y) + 1.1 * math.sin(x * 1.1 - y * 0.9) * min(1, math.hypot(x - 11, y - 13) / 6), FIRE, falloff=3.5)
    shell(B, 6, 18, -45, 1.2)
    # standing on its brass, a column of flame pouring up out of it like a torch
    C = G("120604", "2e0e06", (12, 8))
    C.glow(12, 8, 12, "ff6010", 0.9)
    C.energy(flame(12, 15, 5.5, 15, 0.3, 2), FIRE, falloff=4)
    shell(C, 12, 19, -90, 1.15)
    return A, B, C


def burst_triple():
    # three shells fanned out of one blast
    A = G("140804", "34160a", (12, 6))
    A.glow(12, 5, 10, "ff9030", 0.8)
    for k, (x, a) in enumerate(((5, -115), (12, -90), (19, -65))):
        shell(A, x, 16, a, 1.0, seed=k, length=14, w=2.0)
    blast(A, 12, 5, 4.6, FIRE, 7)
    # the blast's rays and sparks over a tighter fan
    B = G("140804", "3a1608", (12, 4))
    B.rays(12, 4, EMBER, n=8, lo=0, hi=3)
    for k, (x, a) in enumerate(((6.5, -105), (12, -90), (17.5, -75))):
        shell(B, x, 17, a, 0.95, seed=k, length=14, w=2.0)
    blast(B, 12, 4, 5, FIRE, 7)
    for (x, y) in ((2, 6), (22, 5), (3, 12), (21, 13)):
        B.glint(x, y, GOLD[5], arm=0)
    # three shells upright, each with its own tongue of flame
    C = G("120604", "2a0e06", (12, 8))
    for k, x in enumerate((5, 12, 19)):
        C.glow(x, 5, 6, "ff6010", 0.6)
        C.energy(flame(x, 9, 2.6, 8, 0, k), FIRE, falloff=1.8, seed=k)
        shell(C, x, 16, -90, 0.95, seed=k, length=14, w=2.1)
    return A, B, C


def boom_headshot():
    # the pick: the head snapping back in a gold burst, sparks thrown off it
    A = G("140c04", "2e1e0a", (12, 8))
    head(A, 10.5, 12.5, 1.05, GUN)
    A.glow(14, 8, 9, "ffd060", 0.9)
    A.energy(lambda x, y: math.hypot(x - 14, y - 8) - 5.8 * (0.5 + 0.5 * abs(math.cos(math.atan2(y - 8, x - 14) * 3))), GOLD, falloff=3)
    for (x, y) in ((21, 3), (22, 10), (19, 1), (17, 14)):
        A.glint(x, y, GOLD[5], arm=0)
    # hotter: an orange-red burst, the head lit from it
    B = G("140604", "301008", (15, 8))
    head(B, 10.5, 12.5, 1.05, R("100c0e", "1e1a1e", "34303a", "524a52", "7a6a62"))
    B.glow(14, 8, 10, "ff7020", 0.9)
    B.energy(lambda x, y: math.hypot(x - 14, y - 8) - 6 * (0.5 + 0.5 * abs(math.cos(math.atan2(y - 8, x - 14) * 3 + 0.4))), FIRE, falloff=3)
    for (x, y) in ((20, 13), (21, 15), (19, 16)):
        B.px([(x, y)], BLOOD[3])
    # cropped close: a huge head, rays fanning out of the hit
    C = G("140c04", "2e1e0a", (16, 6))
    C.rays(16, 6, R("1a1004", "4a3008", "8a6010", "c89a20", "f0d060"), n=9, lo=0, hi=3)
    head(C, 9, 14, 1.45, GUN)
    C.glow(15, 7, 8, "ffe070", 0.9)
    C.energy(lambda x, y: math.hypot(x - 15, y - 7) - 4.6 * (0.5 + 0.5 * abs(math.cos(math.atan2(y - 7, x - 15) * 3))), GOLD, falloff=2.5)
    return A, B, C


# ---------------------------------------------------------------- aim
def _lens(ic, cx, cy, r):
    ic.paint(circle(cx, cy, r), lambda x, y, d: mix(hexc("06080e"), hexc("1e1a14"), max(0, min(1, (cx + cy - x - y) / (2 * r) + 0.5))))


def chevrons(ic, x, y, n=3, rmp=GOLD, w=2.4):
    """Stacked upward chevrons (the crit stacks), bottom one at y."""
    for k in range(n):
        yy = y - k * 3.2
        ic.paint(union(seg(x - w, yy, x, yy - 2, 1.1), seg(x, yy - 2, x + w, yy, 1.1)), lambda X, Y, d: BLACK)
        ic.solid(union(seg(x - w, yy, x, yy - 2, 0.5), seg(x, yy - 2, x + w, yy, 0.5)), rmp, base=3.6, spread=1, seed=k)


def star4(ic, cx, cy, r, rmp=GOLD, falloff=1.5):
    k = r * 0.28
    ic.energy(poly([(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k), (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)]), rmp, falloff=falloff)


def critical_aim():
    # the kept icon repainted: a red reticle round a dark lens, a gold star at its heart, stacks
    A = G("100604", "2a1408", (12, 12))
    _lens(A, 11, 11, 7)
    reticle(A, 11, 11, 8, 0.6)
    star4(A, 11, 11, 4.6)
    chevrons(A, 20, 22.5)
    # no stacks: a bigger star, a heavier ring
    B = G("100604", "2a1408", (12, 12))
    _lens(B, 12, 12, 7.5)
    reticle(B, 12, 12, 8.6, 0.8)
    star4(B, 12, 12, 5.8, falloff=2)
    B.glow(12, 12, 6, "ffe070", 0.6)
    # close: the ring cropped by the frame, the star small and sharp
    C = G("100604", "2a1408", (12, 12))
    _lens(C, 12, 12, 10)
    reticle(C, 12, 12, 11, 0.8)
    star4(C, 12, 12, 4)
    chevrons(C, 20, 21.5, 2)
    return A, B, C


def focus_hud():
    # 14x14, the crit aim's red reticle with a yellow dot in the middle
    A = S("100604", "2a1408", (7, 7))
    reticle(A, 7, 7, 4.4, 0.5)
    A.energy(circle(7, 7, 1.1), GOLD, falloff=1.1)
    B = S("100604", "2a1408", (7, 7))
    _lens(B, 7, 7, 4.5)
    reticle(B, 7, 7, 4.8, 0.65, ticks=False)
    B.energy(circle(7, 7, 1.4), GOLD, falloff=1.4)
    B.glow(7, 7, 3.4, "ffe070", 0.6)
    C = S("140604", "34100a", (7, 7))
    reticle(C, 7, 7, 5.4, 0.55)
    C.energy(union(seg(7, 3.6, 7, 5.2, 0.35), seg(7, 8.8, 7, 10.4, 0.35), seg(3.6, 7, 5.2, 7, 0.35), seg(8.8, 7, 10.4, 7, 0.35)), BLOOD, falloff=0.5)
    C.energy(circle(7, 7, 1.0), GOLD, falloff=1.0)
    return A, B, C


def snipe():
    # the kept icon repainted: the scoped rifle across a red reticle, a glint at the muzzle
    A = G("0c0a08", "221a14", (12, 12))
    reticle(A, 12, 12, 9, 0.45, rmp=R("1a0406", "3a080c", "6a1014", "9a1a1c", "c83228"))
    rifle(A, 10, 14.5, -40, 1.25, scope=True)
    A.glint(21, 4)
    # the reticle tighter, round the scope's eye
    B = G("0c0a08", "221a14", (10, 10))
    reticle(B, 10, 12.5, 5.6, 0.45, rmp=R("1a0406", "3a080c", "6a1014", "9a1a1c", "c83228"))
    rifle(B, 10, 14.5, -40, 1.25, scope=True)
    B.glint(21, 4)
    # closer: the rifle bigger, the ring cropped by the frame
    C = G("0c0a08", "1e1812", (12, 12))
    reticle(C, 12, 12, 10.5, 0.5, rmp=R("1a0406", "3a080c", "6a1014", "9a1a1c", "c83228"))
    rifle(C, 9, 16, -40, 1.5, scope=True)
    C.glint(21, 3)
    return A, B, C


# ---------------------------------------------------------------- mags
def longmag(ic, cx, cy, ang, s=1.0, rmp=STEEL, length=20, w=3.4, tip=BLOOD, window=True, seed=0):
    """A long box mag lying along ang (top toward ang), a window down its side showing the
    brass inside, the top round's bullet poking out of the lips."""
    hl = length / 2
    items = [
        (lbox(0, 0, hl, w, 0.8), rmp, {}),
        (lbox(-hl - 0.2, 0, 1.0, w + 0.6, 0.5), rmp, {"base": 1.8}),
        (lbox(hl - 0.5, 0, 0.8, w + 0.4, 0.3), GUN, {"base": 2.4}),
    ]
    if window:
        items.append((lbox(-0.5, -0.4, hl - 3, 1.2, 0.5), BRASS, {"base": 2.8, "spread": 1.4}))
    parts(ic, cx, cy, ang, s, items, seed)
    if window:
        a = math.radians(ang)
        for k in range(int(hl - 3)):
            u = -hl + 3.5 + k * 2
            ic.px([(int(cx + (u * math.cos(a) + 0.4 * math.sin(a)) * s), int(cy + (u * math.sin(a) - 0.4 * math.cos(a)) * s))], BRASS[1])
    a = math.radians(ang)
    tx, ty = cx + math.cos(a) * (hl + 1.6) * s, cy + math.sin(a) * (hl + 1.6) * s
    slug(ic, tx, ty, ang, s * 0.9, tip, seed=seed + 9, length=4.6, w=1.7)
    return tx, ty


def steady():
    # the kept icon repainted: the long mag lying corner to corner, its red top round
    A = G("100808", "2a1416", (12, 12))
    tx, ty = longmag(A, 11, 13, -55, 1.0)
    A.streak(tx - 1, ty + 1, 23, 0, 0.6, BLOOD)
    # warmer: the window glowing gold, the laser off
    B = G("120c06", "2a1e10", (12, 12))
    longmag(B, 11.5, 12.5, -55, 1.0, rmp=GUN)
    B.glow(11, 13, 9, "ffd060", 0.5)
    # closer and steeper, the mag cropped by the frame
    C = G("100808", "2a1416", (16, 6))
    tx, ty = longmag(C, 10, 15, -62, 1.25, length=22)
    C.glint(int(tx), int(ty) - 1, BLOOD[5])
    return A, B, C


def steady_crit():
    # the steady mag with a red crosshair laid over the clip
    A = G("100808", "2a1416", (12, 12))
    tx, ty = longmag(A, 11, 13, -55, 1.0)
    A.streak(tx - 1, ty + 1, 23, 0, 0.6, BLOOD)
    reticle(A, 11, 13, 4.6, 0.5)
    # the crosshair sitting round the top round's tip
    B = G("100808", "2a1416", (12, 12))
    tx, ty = longmag(B, 10.5, 13.5, -55, 0.95)
    reticle(B, tx, ty, 3.4, 0.45)
    # the crosshair big and dim behind the whole clip
    C = G("100808", "2a1416", (12, 12))
    reticle(C, 12, 12, 9.4, 0.7, rmp=R("1a0406", "460a0e", "801418", "c02424", "e04030"))
    longmag(C, 12, 12.5, -55, 1.0)
    return A, B, C


def clip_hud():
    # 14x14, three rounds as vanilla paints them: lit forms filling the frame, cropped at the foot
    A = S("0a0c14", "1e2434", (5, 3))
    for k, x in enumerate((2.6, 7, 11.4)):
        cartridge(A, x, 8.5, -90, 1.0, tip=COPPER, seed=k, length=13, w=1.75)
    B = S("0c0a06", "221c10", (7, 4))
    B.glow(7, 6, 7, "ffd060", 0.5)
    for k, (x, y) in enumerate(((2.6, 9), (7, 8), (11.4, 9))):
        cartridge(B, x, y, -90, 1.0, tip=COPPER, seed=k, length=13, w=1.75)
    C = S("0a0c14", "1e2434", (4, 3))
    for k, x in enumerate((3, 7.5, 12)):
        cartridge(C, x, 8, -75, 1.0, tip=COPPER, seed=k, length=14, w=1.9)
    return A, B, C


def hand(ic, x0, y0, s=1.0, sleeve=R("0a1428", "142848", "22427a", "3462a8", "5888d0")):
    """A right hand seen from the side, fingers pointing right and wrapped round something
    upright at about x0 + 8s; (x0, y0) = the wrist's top."""
    def P(x, y):
        return x0 + x * s, y0 + y * s
    ic.solid(box(*P(-2.5, 3.6), 3 * s, 3.8 * s, 0, 1 * s), sleeve, seed=11)
    ic.solid(box(*P(3, 3.4), 3.6 * s, 3.4 * s, 0, 1.6 * s), SKIN, seed=12)
    for k in range(4):
        y = 0.9 + k * 1.75
        ic.solid(seg(*P(4.5, y), *P(10.6 - k * 0.5, y + 0.25), 0.95 * s, 0.85 * s), SKIN, base=3 - k * 0.15, seed=13 + k)
    ic.solid(seg(*P(3.5, 0.6), *P(7.4, -2.4), 1.0 * s, 0.85 * s), SKIN, base=3.4, seed=18)


def reload():
    # the kept icon without its blue arc: the grip above, the mag going in, a cleaner hand
    A = G("0a0c14", "1e2434", (12, 6))
    A.solid(box(12.5, 2.5, 5, 4.6, 0, 1.2), GUN, seed=1)
    A.solid(box(12.5, 10, 3.2, 6, 0, 0.6), STEEL, seed=2)
    A.solid(box(12.5, 16.5, 4, 1.2, 0, 0.5), STEEL, base=2, seed=3)
    hand(A, 4.5, 10.5, 1.0)
    # the palm slapping the mag home from below, the grip cropped at the top
    B = G("0a0c14", "1e2434", (12, 6))
    B.solid(box(11, 1.5, 6, 4.5, 0, 1.2), GUN, seed=1)
    B.solid(box(11, 8.5, 3.4, 4.6, 0, 0.6), STEEL, seed=2)
    B.solid(box(11, 14, 4.4, 1.2, 0, 0.5), STEEL, base=2, seed=3)
    B.solid(ellipse(11, 19.5, 6.5, 3.6), SKIN, seed=4)
    for k, x in enumerate((6, 8.6, 11.2, 13.8)):
        B.solid(seg(x, 18.5, x - 1.4, 15.5, 1.0, 0.9), SKIN, base=3.2, seed=5 + k)
    B.solid(seg(16, 19, 19, 15, 1.1, 0.9), SKIN, base=3.4, seed=9)
    B.solid(box(11, 24, 4.5, 2.4, 0, 0.6), R("0a1428", "142848", "22427a", "3462a8", "5888d0"), seed=10)
    for x in (4, 19):
        B.streak(x, 22, x, 15, 0.6, SMOKE)
    # close: the hand big, round the mag's foot
    C = G("0a0c14", "1e2434", (14, 4))
    C.solid(box(15, 1, 6.5, 4, 0, 1.2), GUN, seed=1)
    C.solid(box(15, 7, 3.4, 5, 0, 0.6), STEEL, seed=2)
    hand(C, 3, 8, 1.3)
    return A, B, C


def arrow_ring(ic, cx, cy, r, w, a0, a1, rmp=ICE, head=2.2):
    """A circular arrow from angle a0 to a1 (degrees, clockwise on screen), its head at a1
    pointing on round the circle: a lit band with a wide triangular head, both dark-edged."""
    lo, hi = math.radians(a0), math.radians(a1)

    def arc(x, y):
        a = math.atan2(y - cy, x - cx)
        while a < lo:
            a += 2 * math.pi
        if a <= hi:
            return ring(cx, cy, r, w)(x, y)
        # past either end: distance to the nearer end cap, so the band ends square
        return 1.5
    ux, uy = math.cos(hi), math.sin(hi)
    tx, ty = -uy, ux
    bx, by = cx + ux * r, cy + uy * r
    tip = poly([(bx + ux * head, by + uy * head), (bx - ux * head, by - uy * head), (bx + tx * head * 1.5, by + ty * head * 1.5)])
    both = union(arc, tip)
    ic.paint(lambda x, y: both(x, y) - 0.8, lambda x, y, d: BLACK)
    ic.solid(both, rmp, base=4, spread=1.2, rim=1.0, seed=3)


def reloading_hud():
    # 14x14: the mag inside a ring that is now an arrow coming round
    A = S("0a0e18", "1a2438", (5, 4))
    arrow_ring(A, 7, 7, 5.0, 1.3, -50, 215, head=2.6)
    A.solid(box(7, 7.5, 1.9, 3.6, 0, 0.5), STEEL, seed=1)
    A.solid(box(7, 4.1, 1.5, 0.6, 0, 0.2), BRASS, base=3.4)
    B = S("0a0e18", "1a2438", (5, 4))
    arrow_ring(B, 7, 7, 5.1, 1.2, -70, 60, head=2.4)
    arrow_ring(B, 7, 7, 5.1, 1.2, 110, 240, head=2.4)
    B.solid(box(7, 7.5, 1.9, 3.6, 0, 0.5), STEEL, seed=1)
    B.solid(box(7, 4.1, 1.5, 0.6, 0, 0.2), BRASS, base=3.4)
    C = S("0a0e18", "1e2a40", (5, 4))
    arrow_ring(C, 7, 7, 5.4, 1.5, -30, 220, head=2.9)
    C.solid(box(7, 7.6, 2.3, 4.2, 0, 0.6), STEEL, seed=1)
    C.solid(box(7, 3.4, 1.8, 0.7, 0, 0.2), BRASS, base=3.4)
    return A, B, C


def topmag(ic, cx, cy, s=1.0, ang=0, tip=COPPER, rmp=GUN, h=14, w=3.2):
    """A box mag standing up (ang tilts it forward), ribbed, its first round lying in the
    lips pointing right; returns the bullet's tip."""
    a = math.radians(ang)
    hh = h / 2

    def T(lx, ly):
        return cx + (lx * math.cos(a) - ly * math.sin(a)) * s, cy + (lx * math.sin(a) + ly * math.cos(a)) * s
    up = ang - 90
    ic.solid(L(lambda u, v: box(0, 0, hh, w, 0, 0.6)(u, v), cx, cy, up, s), rmp, light=(-1, -0.4), seed=1)
    for k in (-2.5, 0.5, 3.5):
        ic.solid(L(lambda u, v, k=k: box(k, 0, 0.3, w - 0.8, 0, 0)(u, v), cx, cy, up, s), rmp, base=1.2, spread=0.3, rim=0, core=0, seed=5)
    ic.solid(L(lambda u, v: box(hh - 0.3, 0, 0.8, w + 0.5, 0, 0.3)(u, v), cx, cy, up, s), STEEL, base=2.4, seed=2)
    ic.solid(L(lambda u, v: box(-hh + 0.5, 0, 1.0, w + 0.7, 0, 0.5)(u, v), cx, cy, up, s), rmp, base=2.6, seed=3)
    rx, ry = T(1.2, -hh - 1.7)
    cartridge(ic, rx, ry, ang, s * 0.85, tip=tip, seed=4, length=11, w=2.0)
    return T(1.2 + 11 * 0.85 * 0.5, -hh - 1.7)


def headshot():
    # a mag, its first round showing in the lips, a red crosshair on the bullet's tip
    A = G("100808", "2a1416", (10, 8))
    tx, ty = topmag(A, 9, 15, 1.0)
    reticle(A, tx, ty, 3, 0.45)
    # tipped forward, the crosshair bigger round the tip
    B = G("100808", "2a1416", (12, 6))
    tx, ty = topmag(B, 8, 15.5, 1.0, ang=18)
    reticle(B, tx, ty, 3.8, 0.45)
    # close: the mag's top and the round huge, the crosshair framing the tip
    C = G("100808", "2a1416", (12, 8))
    tx, ty = topmag(C, 7, 20, 1.45, h=12)
    reticle(C, tx, ty, 4.2, 0.5)
    return A, B, C


def dodge_skip():
    # the pick: the mag skating sideways on purple speed lines
    A = G("0e0a18", "241a3a", (16, 10))
    A.glow(16, 12, 9, "9a6ae0", 0.5)
    for y, x0 in ((6, 0), (10, 2), (14, -1), (18, 3)):
        A.streak(x0, y, x0 + 11, y, 0.9, ARCANE)
    mag(A, 16, 13, 18, 1.0, GUN, h=13, w=3.4, top_round=False)
    # afterimages: the mag left behind twice in fading purple
    B = G("0e0a18", "241a3a", (16, 10))
    for k, (x, al) in enumerate(((5, 0.3), (10, 0.55))):
        sb = Icon(); sb.im = B.im.copy(); sb.p = sb.im.load()
        mag(sb, x, 13, 18, 1.0, GUN, h=13, w=3.4, top_round=False)
        for yy in range(N):
            for xx in range(N):
                if sb.p[xx, yy] != B.p[xx, yy]:
                    B.p[xx, yy] = mix(B.p[xx, yy], mix(sb.p[xx, yy], ARCANE[3], 0.55), al)
    mag(B, 16, 13, 18, 1.0, GUN, h=13, w=3.4, top_round=False)
    # close: the mag big, its trailing edge smeared into the streaks
    C = G("0e0a18", "241a3a", (18, 8))
    for y, x0 in ((4, 0), (9, 1), (14, 0), (19, 2)):
        C.streak(x0, y, x0 + 12, y, 1.1, ARCANE)
    mag(C, 17, 13, 20, 1.3, GUN, h=13, w=3.4, top_round=False)
    return A, B, C


def _tnt_mag(ic, cx, cy, s, sticks=((4.5, -1),), ang=-10, spark=True):
    mag(ic, cx, cy, ang, s, GUN, h=15, w=3.6, top_round=False)
    a = math.radians(ang)
    for k, (dx, dy) in enumerate(sticks):
        dyn(ic, cx + dx * s * math.cos(a), cy + dx * s * math.sin(a) + dy * s, -90 + ang, s, seed=k, length=12, w=1.6)
    for dy in (-3, 3):
        ic.solid(box(cx + 0.8 * s, cy + dy * s, 7 * s, 0.8 * s, ang, 0.2), PAPER, base=2.2, spread=0.6, seed=8)
    fx, fy = cx + sticks[0][0] * s * math.cos(a) + 1.2 * s, cy + sticks[0][1] * s - 7.5 * s
    ic.solid(seg(fx - 1.2 * s, fy + 1.8 * s, fx, fy, 0.35), PAPER[:3], base=1.6)
    if spark:
        ic.glow(fx, fy, 6, "ffa040", 0.9)
        ic.energy(circle(fx, fy, 1.3), FIRE, falloff=1.3)
    return fx, fy


def explosive_reload():
    # the pick: dynamite taped to the mag, the fuse lit
    A = G("140604", "34100a", (12, 6))
    _tnt_mag(A, 10.5, 14, 1.0)
    # a stick taped either side
    B = G("140604", "34100a", (12, 6))
    _tnt_mag(B, 12, 14, 1.0, sticks=((4.6, -1), (-4.6, -1)))
    # hotter: the fuse throwing sparks, the ground lit orange
    C = G("1a0804", "3e1608", (16, 5))
    fx, fy = _tnt_mag(C, 10, 15, 1.05)
    for (dx, dy) in ((-3, -2), (3, -3), (2, 2), (-2, 2.5), (4, 0)):
        C.glint(int(fx + dx), int(fy + dy), GOLD[5], arm=0)
    return A, B, C


def over_reload():
    # the pick: gold rounds spilling over the mag's lips
    A = G("140e04", "34280a", (12, 4))
    A.glow(12, 5, 10, "ffd060", 0.8)
    mag(A, 12, 16, 0, 1.0, GUN, h=13, w=4, top_round=False)
    for k, (x, y, a) in enumerate(((12, 7, -90), (9, 4.5, -120), (15, 4, -60), (7, 1.5, -150), (17.5, 1.5, -30))):
        cartridge(A, x, y, a, 0.6, tip=GOLD, case=GOLD, seed=k, w=2.6, length=9)
    for (x, y) in ((4, 6), (20, 5), (12, 0)):
        A.glint(x, y, GOLD[5])
    # a fountain: more rounds, arcing out to both sides and falling
    B = G("140e04", "34280a", (12, 4))
    B.glow(12, 6, 11, "ffd060", 0.8)
    mag(B, 12, 18, 0, 0.9, GUN, h=12, w=4, top_round=False)
    for k, (x, y, a) in enumerate(((12, 9, -90), (8.5, 6, -125), (15.5, 6, -55), (4.5, 5, -170), (19.5, 5, -10), (3, 10, 150), (21, 10, 30))):
        cartridge(B, x, y, a, 0.5, tip=GOLD, case=GOLD, seed=k, w=2.6, length=9)
    # close: just the lips and three big gold rounds
    C = G("140e04", "34280a", (12, 6))
    C.glow(12, 8, 11, "ffd060", 0.8)
    mag(C, 12, 22, 0, 1.4, GUN, h=13, w=4, top_round=False)
    for k, (x, y, a) in enumerate(((12, 9, -90), (6.5, 6.5, -125), (17.5, 6.5, -55))):
        cartridge(C, x, y, a, 0.85, tip=GOLD, case=GOLD, seed=k, w=2.6, length=9)
    return A, B, C


# ---------------------------------------------------------------- guns
def rifle_attack():
    # the kept icon repainted, its muzzle flash like the new pistol's
    A = G("0a0c14", "1e2434", (16, 6))
    rifle(A, 9.5, 15, -40, 1.2)
    flash(A, 20.6, 5.6, 3)
    # a bigger flash, the spent case kicked out of the side
    B = G("0a0c14", "1e2434", (16, 6))
    rifle(B, 9, 15.5, -40, 1.15)
    flash(B, 19.7, 6.5, 3.8)
    cartridge(B, 8, 6, -120, 0.42, tip=BRASS, case=BRASS, length=8, w=2.6)
    # flatter and closer, the flash cropped by the frame's edge
    C = G("0a0c14", "1e2434", (18, 8))
    rifle(C, 8.5, 14.5, -25, 1.35)
    flash(C, 22.5, 7.8, 3.2)
    return A, B, C


def glock_attack():
    # the pick: the pistol firing to the right
    A = G("0a0c14", "1e2434", (16, 8))
    pistol(A, 10.5, 10.5, 0, 1.35)
    flash(A, 21.5, 9.8, 3.3)
    # tipped up as it kicks, a case flying
    B = G("0a0c14", "1e2434", (16, 8))
    pistol(B, 10.5, 12, -15, 1.3)
    flash(B, 20.5, 7.5, 3.2)
    cartridge(B, 10, 4, 60, 0.42, tip=BRASS, case=BRASS, length=8, w=2.6)
    # warm: the flash lighting the ground around it
    C = G("120c08", "2e2214", (20, 10))
    C.glow(21, 10, 11, "ffa040", 0.6)
    pistol(C, 10.5, 10.5, 0, 1.35, metal=STEEL)
    flash(C, 21.5, 9.8, 3.3)
    return A, B, C


def _pistol_tip(cx, cy, ang, s):
    a = math.radians(ang)
    return cx + math.cos(a) * 7.4 * s, cy + math.sin(a) * 7.4 * s


def glock_dual():
    # two pistols back to back, each aiming up and out at 45 degrees, both firing
    A = G("0a0c14", "1e2434", (12, 6))
    for (x, ang, fl) in ((7.5, -135, True), (16.5, -45, False)):
        pistol(A, x, 15, ang, 1.0, flip=fl)
        flash(A, *_pistol_tip(x, 15, ang, 1.0), 2.4)
    # crossed: the left gun aiming up and right, the right gun up and left
    B = G("0a0c14", "1e2434", (12, 6))
    for (x, ang, fl) in ((8.5, -45, False), (15.5, -135, True)):
        pistol(B, x, 15, ang, 1.0, flip=fl)
    for (x, ang) in ((8.5, -45), (15.5, -135)):
        flash(B, *_pistol_tip(x, 15, ang, 1.0), 2.4)
    # apart, each gun with a tracer going out to its corner
    C = G("0c0a06", "221c10", (12, 8))
    for (x, ang, fl) in ((6, -135, True), (18, -45, False)):
        tx, ty = _pistol_tip(x, 17, ang, 0.9)
        C.streak(tx, ty, tx + (tx - x) * 0.9, ty + (ty - 17) * 0.9, 0.8, GOLD)
        pistol(C, x, 17, ang, 0.9, flip=fl)
        flash(C, tx, ty, 2.0)
    return A, B, C


def launcher(ic, x0, y0, y1, ang=0, s=1.0, rnd=True):
    """The underbarrel launcher close up: an olive tube from the left edge to its muzzle at
    x0, between y0 and y1, a rail above it and the round showing in the muzzle."""
    cy, hh = (y0 + y1) / 2, (y1 - y0) / 2
    f = L(lambda u, v: box(-12, 0, 12, hh, 0, 1.2)(u, v), x0, cy, ang, s)
    ic.solid(f, OLIVE, light=(-0.3, -1), seed=1)
    for k, u in enumerate((-15, -9)):
        ic.solid(L(lambda U, V, u=u: box(u, 0, 0.7, hh + 0.05, 0, 0.2)(U, V), x0, cy, ang, s), OLIVE, base=1.4, spread=0.6, light=(-0.3, -1), seed=4 + k)
    ic.solid(L(lambda u, v: box(-12, -hh - 1.8, 13, 1.1, 0, 0.3)(u, v), x0, cy, ang, s), WOOD, base=2.4, light=(-0.3, -1), seed=2)
    ic.solid(L(lambda u, v: box(-12, -hh - 4, 13, 1.2, 0, 0.3)(u, v), x0, cy, ang, s), STEEL, base=2.6, light=(-0.3, -1), seed=3)
    ic.solid(L(lambda u, v: box(-0.6, 0, 1.4, hh + 0.6, 0, 0.6)(u, v), x0, cy, ang, s), GUN, base=2.2, seed=6)
    ic.paint(L(lambda u, v: ellipse(0, 0, 1.0, hh - 1.2)(u, v), x0, cy, ang, s), lambda x, y, d: BLACK)
    if rnd:
        ic.solid(L(lambda u, v: ellipse(0.2, 0, 0.8, hh - 2.2)(u, v), x0, cy, ang, s), GOLD, base=3.4, seed=7)


def gl_attack():
    # the kept icon repainted: the launcher's tube filling the frame, the round in its muzzle
    A = G("0a0c08", "1e2214", (14, 8))
    launcher(A, 20, 9, 20)
    # tipped up, smoke curling from the muzzle
    B = G("0a0c08", "1e2214", (14, 8))
    launcher(B, 17, 11, 23)
    for k, (x, y, r) in enumerate(((19.5, 7.5, 1.5), (21, 4.5, 1.9), (19.5, 1.5, 2.2))):
        B.solid(circle(x, y, r), SMOKE, base=2.6, seed=k)
    # just fired: the muzzle empty and blazing, the round flying off the frame
    C = G("100c06", "2a2210", (20, 14))
    launcher(C, 15, 9, 20, rnd=False)
    flash(C, 18.5, 14.5, 3.6)
    cut40(C, 22, 9, -40, 0.7)
    return A, B, C


def gl_charges_hud():
    # 14x14: the launcher tube up from the corner, a round sitting in its muzzle
    A = S("0a0c08", "1e2214", (5, 4))
    A.solid(box(3, 11, 7, 3.4, -45, 1), OLIVE, seed=1)
    A.solid(box(7.6, 6.4, 1.0, 4.0, -45, 0.4), GUN, base=2.2, seed=2)
    A.solid(ellipse(9.6, 4.4, 3.0, 2.6, -45), OLIVE, base=3.2, seed=3)
    A.solid(box(8.4, 5.6, 0.5, 2.6, -45, 0.1), GOLD, base=3.4, seed=4)
    # firing: the round leaving the muzzle on a flash
    B = S("100c06", "2a2210", (8, 6))
    B.solid(box(2, 12, 6.5, 3.2, -45, 1), OLIVE, seed=1)
    B.solid(box(6.2, 7.8, 1.0, 3.8, -45, 0.4), GUN, base=2.2, seed=2)
    flash(B, 8, 6, 2.2)
    B.solid(ellipse(11, 3, 2.2, 1.9, -45), OLIVE, base=3.2, seed=3)
    # standing up out of the frame's foot, the round in its mouth
    C = S("0a0c08", "1e2214", (5, 4))
    C.solid(box(7, 12, 3.6, 4.5, 0, 0.8), OLIVE, light=(-1, -0.3), seed=1)
    C.solid(box(7, 7.6, 4.3, 1.0, 0, 0.4), GUN, base=2.2, seed=2)
    C.solid(ellipse(7, 4.4, 3.0, 3.4), OLIVE, base=3.2, seed=3)
    C.solid(box(7, 6.3, 3.1, 0.55, 0, 0.1), GOLD, base=3.4, seed=4)
    return A, B, C


# ---------------------------------------------------------------- grenades
def frag():
    # the pick: the pineapple and its pin ring, a warmer light on it
    A = G("0e1008", "2a3018", (6, 5))
    A.glow(9, 9, 12, "4a5a1a", 0.6)
    pineapple(A, 11.5, 14, 8.5, 9.5)
    A.solid(ring(4.5, 4.5, 2.4, 1.1), GOLD, base=3.5)
    A.glint(3, 3, GOLD[5], arm=0)
    # bigger, cropped by the frame's foot
    B = G("0e1008", "2a3018", (6, 5))
    pineapple(B, 12, 15.5, 9.5, 10.5)
    B.solid(ring(4, 4, 2.6, 1.2), BRASS, base=3.5)
    # back-lit: a green rim light, the ring hanging off the lever
    C = G("080a04", "1a2010", (18, 4))
    C.glow(18, 5, 12, "84963a", 0.7)
    pineapple(C, 11, 14, 8.5, 9.5, R("0e1006", "1e260e", "33401a", "4e5e26", "6e8234", "9ab048"))
    C.solid(ring(20, 7, 2.4, 1.1), GOLD, base=3.5)
    return A, B, C


def grenade_charges_hud():
    # 14x14: the frag as a stack icon
    A = S("0e1008", "262c14", (4, 3))
    pineapple(A, 7, 8.3, 4.6, 5.4)
    B = S("0e1008", "262c14", (4, 3))
    pineapple(B, 7, 9, 5.6, 6.3, lever=False)
    C = S("0e1008", "222812", (4, 3))
    C.glow(7, 8, 7, "84963a", 0.6)
    pineapple(C, 8, 8.5, 4.6, 5.2)
    C.solid(ring(2.6, 2.6, 1.6, 0.8), GOLD, base=3.5)
    return A, B, C


SHIELD = R("0e141c", "1e2a36", "3e5468", "61798c", "758ea2", "9eb0be", "c6d3dc")


def broken_shield(ic, x, y, s=1.0):
    """The armor break debuff's cracked shield, painted at about 9s px from (x, y)."""
    def P(u, v):
        return x + u * s, y + v * s
    sh = poly([P(0.3, 0.6), P(8.7, 0.6), P(8.7, 4.4), P(4.5, 8.8), P(0.3, 4.4)])
    crack = lambda X, Y: abs((X - x) / s - (4.6 + 1.3 * math.sin(((Y - y) / s) * 1.9))) - 0.45
    ic.paint(lambda X, Y: sh(X, Y) - 0.9, lambda X, Y, d: BLACK)
    ic.solid(cut(sh, crack), SHIELD, seed=21)
    ic.paint(inter(sh, crack), lambda X, Y, d: BLACK)


def frag_shrapnel():
    # the frag, and the armor break debuff's own icon in the corner
    A = G("0e1008", "2a3018", (6, 5))
    pineapple(A, 10.5, 13, 8, 9)
    A.solid(ring(4, 4, 2.3, 1.1), GOLD, base=3.5)
    paste(A, ARMORBREAK[0], ARMORBREAK[1], 14, 14)
    # the same, the corner icon painted in the skill style at a size you can read
    B = G("0e1008", "2a3018", (6, 5))
    pineapple(B, 10, 12.5, 8, 9)
    broken_shield(B, 13, 13, 1.15)
    # the grenade bigger, the cracked shield in the top corner
    C = G("0e1008", "2a3018", (6, 8))
    pineapple(C, 10.5, 14.5, 9, 9.8, lever=False)
    broken_shield(C, 13.5, 0.5, 1.1)
    return A, B, C


def gas():
    # the pick: the canister fuming
    A = G("06100a", "142a14", (16, 6))
    A.glow(16, 7, 10, "62963a", 0.5)
    canister(A, 8.5, 11, 24, 5.4, OLIVE, bands=[(14, 14.7, GOLD), (17, 17.7, GOLD)])
    for k, (x, y, r) in enumerate(((14, 7, 4.4), (19.5, 10, 3.8), (10, 4, 3.2), (20, 3.5, 3.6), (16, 13, 2.6), (14, 1, 2.4))):
        A.solid(circle(x, y, r), GAS, base=3.2, spread=1.6, rim=1.2, seed=k)
    # the canister low in the corner, the cloud filling the rest of the frame
    B = G("06100a", "142a14", (16, 6))
    for k, (x, y, r) in enumerate(((16, 5, 6), (8, 5, 5), (20, 14, 5), (12, 11, 4.6), (3, 9, 3.4))):
        B.solid(circle(x, y, r), GAS, base=2.6 + k * 0.2, spread=1.6, rim=1.2, seed=k)
    canister(B, 6, 16, 24, 4.6, OLIVE, bands=[(19, 19.7, GOLD)])
    # a sicker green: the gas glowing toxic over the can
    C = G("061006", "142a10", (14, 6))
    C.glow(14, 7, 12, "7cc434", 0.8)
    canister(C, 9, 11, 24, 5.4, OLIVE, bands=[(14, 14.7, GOLD), (17, 17.7, GOLD)])
    for k, (x, y, r) in enumerate(((14.5, 6.5, 4.2), (19.5, 9.5, 3.4), (10, 3.5, 3), (20, 3, 3.2))):
        C.solid(circle(x, y, r), TOXIC, base=3.6, spread=1.6, rim=1.2, seed=k)
    return A, B, C


def incendiary():
    # the pick: one tall flame, the can black in its heart, embers going up
    A = G("100404", "300a04", (12, 12))
    A.glow(12, 13, 12, "ff5010", 0.9)
    A.energy(flame(12, 24, 9, 23, 0.5, 2), FIRE, falloff=6)
    A.solid(box(12, 17.5, 3, 4.2, 0, 1.2), EMBER[:3], base=0.6, spread=0.5, rim=1.5)
    A.solid(box(12, 12.6, 1.6, 0.9, 0, 0.3), EMBER[:3], base=0.8, spread=0.4)
    for (x, y) in ((4, 5), (19, 3), (21, 9), (3, 12)):
        A.glint(x, y, FIRE[5], arm=0)
    # white-hot: the core of the flame burnt out to white, a gold band on the can
    B = G("140604", "3a1006", (12, 12))
    B.glow(12, 12, 13, "ffa030", 1.0)
    B.energy(flame(12, 24, 9.5, 23, 0.3, 4), FIRE, falloff=3.5)
    B.solid(box(12, 18, 3.2, 4.4, 0, 1.2), EMBER[:3], base=0.6, spread=0.5, rim=1.5)
    B.solid(box(12, 16.5, 3.25, 0.6, 0, 0.1), GOLD[:4], base=1.6, spread=0.6)
    # the can at the foot, a sheet of flame rolling up off it
    C = G("100404", "2a0a04", (12, 16))
    C.glow(12, 16, 13, "ff5010", 0.9)
    for k, (x, h, ln) in enumerate(((6, 15, -2), (12, 22, 0), (18, 16, 2))):
        C.energy(flame(x, 22, 5, h, ln, k), FIRE, falloff=3, seed=k)
    C.solid(box(12, 21, 6.5, 3, 0, 1.4), RED, light=(-0.3, -1), seed=2)
    C.solid(box(12, 21, 0.8, 3.05, 0, 0.3), GOLD, light=(-0.3, -1))
    return A, B, C


FLASHB = R("1a1a40", "5a5ab0", "a8a8ff", "e8e8ff", "ffffff")


def _flashbang(ic, cx, top, bot, hw, ports=((11, 15, 19), (8, 12, 16)), pr=(1.0, 1.4)):
    canister(ic, cx, top, bot, hw, STEEL, bands=[(top + 1, top + 2, GUN)])
    for y in ports[0]:
        for x in ports[1]:
            ic.energy(ellipse(x, y, pr[0], pr[1]), FLASHB, falloff=1)


def stun_grenade():
    # the pick: the flashbang, its ports blazing, a little more light thrown off them
    A = G("0a0c1a", "1e2448", (8, 6))
    _flashbang(A, 12, 6, 23, 6.5)
    A.glow(12, 15, 11, "8a8aff", 0.7)
    # it starts to go: a white star breaking out of the top
    B = G("0a0c1a", "1e2448", (12, 4))
    B.rays(12, 4, R("1a1a40", "4a4ac0", "a0a0ff", "e0e0ff", "ffffff"), n=8, lo=0.5, hi=4, width=0.4)
    _flashbang(B, 12, 9, 24, 6, ports=((13, 17, 21), (8.5, 12, 15.5)))
    B.glow(12, 4, 7, "c0c0ff", 1.0)
    B.energy(circle(12, 4, 2), FLASHB + [WHITE], falloff=2)
    # close: the can big and cropped, ports in a tight grid
    C = G("0a0c1a", "1e2448", (8, 6))
    _flashbang(C, 12, 4, 26, 8.5, ports=((9, 13, 17, 21), (7, 12, 17)), pr=(1.2, 1.5))
    C.glow(12, 14, 11, "8a8aff", 0.6)
    return A, B, C


# ---------------------------------------------------------------- rockets
def _rocket_tail(ic, cx, cy, ang, s, length=16, r=3):
    a = math.radians(ang)
    tx, ty = cx - math.cos(a) * length / 2 * s, cy - math.sin(a) * length / 2 * s
    ic.glow(tx, ty, r * 2.6, "ff7020", 0.8)
    ic.energy(seg(tx - math.cos(a) * r * 1.6, ty - math.sin(a) * r * 1.6, tx, ty, r * 0.2, r * 0.75), FIRE, falloff=r * 0.6)
    return tx, ty


def rocket_():
    # the kept icon repainted: the rocket climbing to the corner on its flame
    A = G("140804", "2e1608", (16, 6))
    _rocket_tail(A, 13.5, 10.5, -50, 1.05)
    rocket(A, 13.5, 10.5, -50, 1.05)
    # a smoke trail curling out behind it
    B = G("0c0806", "221810", (16, 6))
    for k in range(7):
        t = k / 6
        B.solid(circle(1.5 + t * 7, 23 - t * 8, 1.2 + t * 1.6), SMOKE, base=1.6 + t * 1.6, spread=0.8, seed=k)
    _rocket_tail(B, 15, 9, -50, 0.95)
    rocket(B, 15, 9, -50, 0.95)
    # close: the nose and band huge, the fins off the frame
    C = G("140804", "2e1608", (18, 4))
    C.glow(15, 9, 12, "ff6010", 0.5)
    rocket(C, 11, 13, -50, 1.5)
    return A, B, C


def rocket_charges_hud():
    # 14x14: a fat rocket like the launcher skill's, on its flame
    A = S("140804", "2e1608", (9, 4))
    _rocket_tail(A, 8, 6, -45, 0.62, r=2.4)
    rocket(A, 8, 6, -45, 0.62, w=3.4)
    B = S("140804", "2e1608", (7, 3))
    _rocket_tail(B, 7, 6, -90, 0.6, r=2.2)
    rocket(B, 7, 6, -90, 0.6, w=3.6)
    C = S("140604", "2e1006", (9, 5))
    C.glow(7, 7, 7, "ff6010", 0.6)
    rocket(C, 6.5, 7.5, -45, 0.78, w=3.4)
    return A, B, C


def quad_missile():
    # the pick: the four-tube pod, rivets at its corners, the noses glowing in the tubes
    A = G("140804", "2a1608", (8, 6))
    A.solid(box(12, 12, 9.5, 9.5, 0, 1.4), OLIVE, seed=1)
    for (x, y) in ((4, 4), (20, 4), (4, 20), (20, 20)):
        A.px([(x, y)], OLIVE[5])
    for k, (x, y) in enumerate(((7.5, 7.5), (16.5, 7.5), (7.5, 16.5), (16.5, 16.5))):
        A.solid(circle(x, y, 3.4), GUN, base=0.8, spread=0.5, rim=0, core=0)
        A.solid(circle(x, y, 2.2), BLOOD, seed=k)
        A.glint(int(x - 1), int(y - 1), BLOOD[5], arm=0)
    # one tube firing: its missile leaving in a puff, the other three waiting
    B = G("140804", "2a1608", (8, 6))
    B.solid(box(12, 13, 9.5, 9.5, 0, 1.4), OLIVE, seed=1)
    for k, (x, y) in enumerate(((7.5, 8.5), (16.5, 8.5), (7.5, 17.5), (16.5, 17.5))):
        B.solid(circle(x, y, 3.4), GUN, base=0.8, spread=0.5, rim=0, core=0)
        if k != 1:
            B.solid(circle(x, y, 2.2), BLOOD, seed=k)
    B.solid(circle(16.5, 8.5, 3.6), SMOKE, base=3, seed=7)
    rocket(B, 19, 4, -45, 0.55)
    # the pod seen from below, tubes running back in perspective
    C = G("140804", "2a1608", (8, 6))
    C.solid(poly([(2, 4), (19, 2), (23, 20), (5, 23)]), OLIVE, seed=1)
    for k, (x, y) in enumerate(((7, 8), (15.5, 7), (8.5, 16.5), (17, 15.5))):
        C.solid(ellipse(x, y, 3.4, 3.0, -10), GUN, base=0.8, spread=0.5, rim=0, core=0)
        C.solid(ellipse(x + 0.3, y + 0.3, 2.2, 2.0, -10), BLOOD, seed=k)
    return A, B, C


def fatman(ic, cx, cy, ang, s, r=3.8, ru=1.6, rot=0):
    parts(ic, cx, cy, ang, s, [
        (lambda u, v: poly([(-9, -6), (-5, -3), (-5, 3), (-9, 6), (-7.5, 0)])(u, v), STEEL, {"base": 2}),
        (lambda u, v: ellipse(1, 0, 8, 5.8)(u, v), OLIVE, {}),
    ])
    a = math.radians(ang)
    nuke(ic, cx + math.cos(a) * ru * s, cy + math.sin(a) * ru * s, r, rot=rot)


def fat_boy():
    # the pick with a radiation mark in place of the yellow band
    A = G("0a1406", "1e3010", (10, 8))
    fatman(A, 12, 12, -40, 1.1, r=4.4, rot=-40)
    # bigger, the mark large enough to read at a glance
    B = G("0a1406", "1e3010", (10, 8))
    fatman(B, 11, 13, -40, 1.3, r=5.2, rot=-40)
    # falling nose down, a sick green light under it
    C = G("061006", "142a10", (12, 18))
    C.glow(12, 20, 12, "7cc434", 0.7)
    fatman(C, 12, 11, 90, 1.15, r=4.8, rot=60)
    return A, B, C


def magic_missile():
    def split(ic, flip=False):
        ic.ground("06101e", "123258", light=(6, 6))
        for y in range(N):
            for x in range(N):
                if x + y > 23:
                    v = 0.5 + grain(x, y, 4) * 0.4 - math.hypot(x - 18, y - 18) / 24
                    ic.p[x, y] = pick(EMBER, v * 3)
    # the pick: ice ground behind the nose, fire behind the tail, frost flecks off the nose
    A = Icon(); split(A)
    rocket(A, 12, 12, -45, 1.05, nose=ICE, body=GUN, band=GOLD)
    A.energy(lambda x, y: math.hypot(x - 4.5, y - 19.5) - 3.2, FIRE, falloff=2.4)
    for (x, y) in ((20, 8), (16, 3), (22, 4)):
        A.glint(x, y, ICE[5], arm=0)
    # the nose crusted in ice crystals, the tail roaring
    B = Icon(); split(B)
    B.energy(seg(1, 23, 6, 18, 1.4, 3.4), FIRE, falloff=2.6)
    rocket(B, 12.5, 11.5, -45, 1.05, nose=ICE, body=GUN, band=GOLD)
    for k in range(5):
        a = math.radians(-45 + (k - 2) * 35)
        B.energy(seg(18, 6, 18 + math.cos(a) * 4.5, 6 + math.sin(a) * 4.5, 0.6, 0.2), ICE, falloff=0.6)
    # flatter and bigger, the split running under it
    C = Icon(); split(C)
    rocket(C, 11, 13, -30, 1.3, nose=ICE, body=GUN, band=GOLD)
    C.energy(lambda x, y: math.hypot(x - 1.5, y - 19) - 2.6, FIRE, falloff=2)
    return A, B, C


def rpg_jump():
    # the pick: the trooper flung up off the fireball
    A = G("140804", "3a1a0a", (12, 18))
    A.rays(12, 22, EMBER, n=6, lo=0, hi=3)
    blast(A, 12, 22, 8, FIRE, 6)
    soldier(A, 12, 8.5, 0.95)
    # a bigger blast, a ring of smoke rolling out at its foot
    B = G("140804", "3a1a0a", (12, 18))
    for k, (x, r) in enumerate(((3, 3.4), (21, 3.4), (7, 3), (17, 3))):
        B.solid(circle(x, 21.5, r), SMOKE, base=2.4, seed=k)
    blast(B, 12, 21, 9.5, FIRE, 7)
    soldier(B, 12, 7.5, 0.85)
    # higher: the trooper small near the top, speed lines down to the blast
    C = G("140804", "2e1408", (12, 20))
    blast(C, 12, 23, 6.5, FIRE, 6)
    for k, (y, r) in enumerate(((17.5, 2.2), (14.5, 1.7), (12, 1.3))):
        C.solid(circle(12 + (k % 2) * 0.8, y, r), SMOKE, base=2.8, seed=k)
    soldier(C, 12, 6.5, 0.7)
    return A, B, C


def hoarder():
    def fill(ic, y0, scale=1.0):
        rocket(ic, 17, y0 - 6.5 * scale, -80, 0.75 * scale, fins=False)
        rocket(ic, 6, y0 - 5.5 * scale, -100, 0.65 * scale, fins=False)
        for k, (x, y) in enumerate(((5, -2), (10, -3), (15, -2), (19.5, -2.5), (8, -5.8), (13, -6))):
            pineapple(ic, x, y0 + y * scale, 2.8 * scale, 3.1 * scale, OLIVE, seed=k, lever=False)
    # the pick: the crate brimming, a gold light over the pile
    A = G("140e06", "2e220e", (12, 6))
    A.glow(12, 6, 10, "ffd060", 0.4)
    fill(A, 14)
    crate(A, 1.5, 14, 22.5, 23.5)
    A.solid(box(12, 18.5, 3, 1.2, 0, 0.2), GOLD, base=3)
    # heaped higher: three rocket noses standing out of the heap
    B = G("140e06", "2e220e", (12, 6))
    for k, (x, a) in enumerate(((5, -105), (12, -90), (19, -75))):
        rocket(B, x, 7, a, 0.7, fins=False, seed=k)
    fill(B, 15)
    crate(B, 1.5, 15, 22.5, 24)
    # close: the crate's lip cropped, the grenades big
    C = G("140e06", "2e220e", (12, 6))
    for k, (x, y) in enumerate(((4, 13), (12, 12), (20, 13), (8, 7), (16, 7))):
        pineapple(C, x, y, 4, 4.4, OLIVE, seed=k, lever=False)
    crate(C, -1, 16, 25, 26)
    return A, B, C


def overpacked():
    def bundle(ic, xs, top, length, w, y=15, rope=True, glow=True):
        for k, x in enumerate(xs):
            dyn(ic, x, y + (k % 2) * 0.8, -90, 1.0, seed=k, length=length, w=w)
        if rope:
            ic.solid(box(12, y, 11.5, 1.0, 0, 0.3), WOOD, base=1.6, spread=0.5)
            ic.solid(box(12, y + 5, 11.5, 0.8, 0, 0.3), WOOD, base=1.4, spread=0.5)
    # the pick, fuller: a second rank of sticks jammed in over the first
    A = G("140604", "34100a", (12, 6))
    for k, x in enumerate((4.6, 7.9, 11.2, 14.5, 17.8)):
        dyn(A, x, 6.5, -90, 1.0, seed=10 + k, length=6, w=1.65)
    bundle(A, (1.5, 4.5, 7.5, 10.5, 13.5, 16.5, 19.5, 22.5), 0, 17, 1.6)
    A.glow(12, 1, 6, "ffa040", 0.8)
    A.energy(circle(12, 1.5, 1.2), FIRE, falloff=1.2)
    # bulging: the rope biting in, sticks bowing out above and below it
    B = G("140604", "34100a", (12, 6))
    for k in range(8):
        x = 1.5 + k * 3
        lean = (x - 12) * 1.6
        dyn(B, x, 13, -90 + lean, 1.0, seed=k, length=19, w=1.6)
    B.solid(box(12, 13.5, 6.5, 1.1, 0, 0.3), WOOD, base=1.6, spread=0.5)
    B.glow(12, 1, 6, "ffa040", 0.8)
    for x in (8, 12, 16):
        B.energy(circle(x + (x - 12) * 0.3, 2, 0.9), FIRE, falloff=0.9)
    # end on: a fist of red stick ends packed tight, the rope round them
    C = G("140604", "34100a", (12, 6))
    C.solid(circle(12, 12, 11), WOOD, base=1.6, seed=1)
    for k, (x, y) in enumerate([(12 + dx * 3.6 + (dy % 2) * 1.8, 12 + dy * 3.1) for dy in range(-3, 4) for dx in range(-3, 3)]):
        if math.hypot(x - 12, y - 12) < 9.6:
            C.solid(circle(x, y, 1.75), RED, seed=k)
            C.px([(int(x), int(y))], PAPER[3])
    C.energy(circle(12, 12, 1.0), FIRE, falloff=1.0)
    return A, B, C


# ---------------------------------------------------------------- rounds
STL = R("12141a", "2a2e38", "4e5464", "7c8496", "b8c0d0", "f0f4ff")


def tip_of(cx, cy, ang, s, length=12):
    a = math.radians(ang)
    return cx + math.cos(a) * length / 2 * s, cy + math.sin(a) * length / 2 * s


def piercing():
    # through a plank: the round's tail still in the wood, splinters blown out round it
    A = G("0c0e12", "1e222a", (16, 6))
    cartridge(A, 13, 11, -45, 1.4, tip=STL)
    A.solid(box(9.5, 13, 3.4, 14, -12, 0.4), WOOD, seed=3)
    for k in (-1.5, 1.2):
        A.solid(box(9.5 + k, 13, 0.25, 14, -12, 0), WOOD, base=1.2, spread=0.3, rim=0, core=0)
    for k in range(5):
        a = math.radians(-45 + (k - 2) * 30)
        A.solid(seg(11, 11.5, 11 + math.cos(a) * (4 + k % 2 * 2), 11.5 + math.sin(a) * (4 + k % 2 * 2), 0.7, 0.2), WOOD, base=3.4, seed=k)
    A.glint(19, 4)
    # through a steel plate: the hole's lips peeled back toward you, the round out ahead
    B = G("0c0e12", "1e222a", (12, 12))
    B.solid(box(9, 15, 9, 9, 0, 0.8), STEEL, base=2, spread=1.4, seed=2)
    for k in range(6):
        a = math.radians(k * 60 + 20)
        B.solid(poly([(9 + math.cos(a - 0.35) * 2.2, 15 + math.sin(a - 0.35) * 2.2), (9 + math.cos(a) * 5.4, 15 + math.sin(a) * 5.4),
                      (9 + math.cos(a + 0.35) * 2.2, 15 + math.sin(a + 0.35) * 2.2)]), STEEL, base=3.6, seed=k)
    B.paint(circle(9, 15, 2.2), lambda x, y, d: BLACK)
    cartridge(B, 16, 8, -45, 1.0, tip=STL)
    B.streak(9, 15, 12, 12, 0.8, GOLD)
    # through brickwork: the wall cracking open, chips flying, the round bursting out
    C = G("0c0e12", "1e222a", (12, 12))
    BRICK = R("1a0c08", "3a1a10", "5e2c18", "8a4424", "b0603a", "d08a5a")
    for row in range(5):
        for col in range(3):
            x = col * 8 + (row % 2) * 4 - 2
            C.solid(box(x + 3.5, row * 5 + 2, 3.6, 2.1, 0, 0.4), BRICK, seed=row * 3 + col)
    C.paint(lambda x, y: math.hypot(x - 10, y - 13) - 4.2 * (0.7 + 0.3 * math.sin(math.atan2(y - 13, x - 10) * 5)), lambda x, y, d: BRICK[0])
    for k, (x, y) in enumerate(((4, 7), (6, 20), (16, 19), (3, 13))):
        C.solid(box(x, y, 1.2, 0.9, k * 30, 0.2), BRICK, base=3.4, seed=k)
    cartridge(C, 14.5, 9, -45, 1.25, tip=STL)
    return A, B, C


def scavenger():
    # the kept icon repainted with the purple round now yellow: fire, ice, lightning, poison
    A = G("0c0a14", "1e1a2e", (12, 6))
    for k, (rm, x) in enumerate(zip(ELEMS, (4, 9.3, 14.6, 19.9))):
        cartridge(A, x, 13 + (k % 2) * 1.5, -90, 0.9, tip=rm, seed=k, length=16, w=2.1)
    # fanned out of one hand's grip at the foot
    B = G("0c0a14", "1e1a2e", (12, 6))
    for k, (rm, a) in enumerate(zip(ELEMS, (-132, -106, -80, -54))):
        r = math.radians(a)
        cartridge(B, 12 + math.cos(r) * 8, 22 + math.sin(r) * 8, a, 0.85, tip=rm, seed=k, length=16, w=2.1)
    # close, each tip glowing its colour
    C = G("0c0a14", "1e1a2e", (12, 6))
    for k, (rm, x) in enumerate(zip(ELEMS, (3, 9, 15, 21))):
        C.glow(x, 6, 5, rm[4], 0.6)
        cartridge(C, x, 15 + (k % 2), -90, 1.2, tip=rm, seed=k, length=16, w=2.0)
    return A, B, C


def blind_eye(ic, cx, cy, s=1.0, iris=TOXIC, shut=False):
    """The scavenger blind orb's old corner mark: an eye with a red slash through it."""
    f = lambda x, y: (abs((y - cy) / s) - 2.4 * (1 - ((x - cx) / (4.6 * s)) ** 2)) * s if abs(x - cx) < 4.6 * s else 3
    ic.paint(lambda x, y: f(x, y) - 1.0, lambda x, y, d: BLACK)
    if shut:
        ic.solid(lambda x, y: abs(y - cy - ((x - cx) / (4.2 * s)) ** 2 * 1.6 * s) - 0.6 if abs(x - cx) < 4.2 * s else 1, SKIN, base=3.6)
    else:
        ic.solid(f, PAPER, base=4, spread=0.8, rim=0.3)
        ic.solid(inter(f, circle(cx, cy, 1.8 * s)), iris, seed=3)
        ic.paint(inter(f, circle(cx, cy, 0.7 * s)), lambda x, y, d: BLACK)
    ic.energy(seg(cx - 4 * s, cy + 3.4 * s, cx + 4 * s, cy - 3.4 * s, 0.55 * s), BLOOD, falloff=0.6)


def _round_on(rm, dark, mid, glowc, cx=12, cy=12.5, ang=-50, s=1.45, at=None, glow=0.7):
    tx, ty = tip_of(cx, cy, ang, s)
    ic = G(dark, mid, at or (tx, ty))
    ic.glow(tx, ty, 9 + glow * 3, glowc, glow)
    cartridge(ic, cx, cy, ang, s, tip=rm)
    return ic, tx, ty


def scavenger_blind():
    # the pick, and the blinding eye back in its corner
    A = G("06100a", "142a14", (15, 8))
    A.glow(15, 8, 9, "3e8e1c", 0.7)
    cartridge(A, 11, 12, -55, 1.35, tip=TOXIC)
    for (x, y, r) in ((5, 15, 1.4), (7, 19, 1.1), (3, 20, 0.9)):
        A.solid(circle(x, y, r), TOXIC, base=4)
    blind_eye(A, 17.5, 18.5, 1.3)
    # the drops falling onto the eye
    B = G("06100a", "142a14", (14, 6))
    B.glow(15, 6, 9, "3e8e1c", 0.7)
    cartridge(B, 10, 10, -45, 1.25, tip=TOXIC)
    for (x, y, r) in ((15, 13, 1.1), (16.5, 11, 0.8)):
        B.solid(circle(x, y, r), TOXIC, base=4)
    blind_eye(B, 17.5, 18.5, 1.3, iris=GOLD)
    # the eye already shut, the slash through it
    C = G("06100a", "142a14", (15, 8))
    C.glow(15, 8, 9, "3e8e1c", 0.7)
    cartridge(C, 11, 12, -55, 1.35, tip=TOXIC)
    blind_eye(C, 17.5, 18.5, 1.3, shut=True)
    return A, B, C


def _three(fn):
    """Three ideas from one element painter: the pick with its effect grown and its glow
    hotter, a flatter pose, and a close crop."""
    return fn(12, 12.5, -50, 1.45, 1.45, 1.0), fn(11, 13.5, -35, 1.3, 1.1, 0.7), fn(9, 15, -50, 2.0, 1.4, 0.7)


def scavenger_fire():
    def f(cx, cy, ang, s, k, g):
        ic, tx, ty = _round_on(FIRE, "140604", "34100a", "ff6010", cx, cy, ang, s, glow=g)
        ic.energy(flame(tx, ty + 1.4, 2.2 * k, 7 * k, 1.5, 3), FIRE, falloff=1.8)
        return ic
    return _three(f)


def scavenger_ice():
    def f(cx, cy, ang, s, k, g):
        ic, tx, ty = _round_on(ICE, "06101e", "102a4a", "3a8ad0", cx, cy, ang, s, glow=g)
        for j in range(6):
            a = math.radians(j * 60 - 50)
            ic.energy(seg(tx, ty, tx + math.cos(a) * 3.6 * k, ty + math.sin(a) * 3.6 * k, 0.4), ICE, falloff=0.5)
        return ic
    return _three(f)


def scavenger_lightning():
    def f(cx, cy, ang, s, k, g):
        ic, tx, ty = _round_on(VOLT, "141004", "2e2608", "e0c028", cx, cy, ang, s, glow=g)
        for pts in (((0, -6), (-2, -3), (1, -1)), ((-8, 3), (-5, 2), (-7, -1)), ((2, 3), (4, 6), (2, 8))):
            line(ic, [(tx + x * k, ty + y * k) for x, y in pts], 0.5, VOLT, falloff=0.6)
        return ic
    return _three(f)


def scavenger_poison():
    def f(cx, cy, ang, s, k, g):
        ic, tx, ty = _round_on(TOXIC, "06100a", "142a14", "3e8e1c", cx, cy, ang, s, glow=g)
        for (x, y, r) in ((-2.5, 5, 1.2), (-3.5, 8.5, 1.0), (-2.5, 12, 0.8)):
            ic.energy(lambda X, Y, x=tx + x * k, y=ty + y * k, r=r * k: math.hypot(X - x, Y - y) - r + max(0, y - Y) * 0.6, TOXIC, falloff=1)
        return ic
    return _three(f)


def scavenger_slow():
    def f(cx, cy, ang, s, k, g):
        ic = G("06101e", "102a4a", (12, 12))
        ic.glow(12, 12, 9, "3a8ad0", 0.7 * g)
        cartridge(ic, cx, cy, ang, s * 0.83, tip=ICE)
        blk = box(cx, cy, 8.5 * s / 1.45, 8.5 * s / 1.45, 12 + (k - 1) * 20, 1.2)
        for y in range(N):
            for x in range(N):
                d = blk(x + 0.5, y + 0.5)
                if d <= 0:
                    o = ic.p[x, y]
                    ic.p[x, y] = mix(o, ICE[5] if d > -1.1 else ICE[3], 0.55 if d > -1.1 else 0.3)
        ic.px([(int(cx - 5), int(cy - 6)), (int(cx - 4), int(cy - 7)), (int(cx - 3), int(cy - 8))], WHITE)
        return ic
    return f(12, 12, -55, 1.45, 1.4, 1.0), f(12, 12.5, -35, 1.3, 1.0, 0.7), f(11, 13, -55, 1.85, 1.2, 0.7)


def scavenger_stun():
    def f(cx, cy, ang, s, k, g):
        ic, tx, ty = _round_on(VOLT, "141004", "2e2608", "e0c028", cx, cy, ang, s, glow=g)
        # dizzy stars wheeling round the tip
        for j in range(3):
            a = math.radians(j * 120 - 60)
            star4(ic, tx + math.cos(a) * 3.8 * k, ty + math.sin(a) * 2.6 * k, 1.9 * k, VOLT, falloff=0.9)
        return ic
    return _three(f)


def shrapnel():
    CR = (((11, 6), (9, 10), (11, 13)), ((14, 8), (17, 11), (15, 15)), ((8, 15), (10, 18), (8, 21)), ((13, 16), (12, 19), (15, 22)))

    def cracked(ic, dx=0, dy=0, sc=1.0, w=0.55, glow=0.6):
        pineapple(ic, 12 + dx, 13.5 + dy, 8 * sc, 9.5 * sc, GUN, lever=False)
        for pts, rm in zip(CR, ELEMS):
            pts = [(12 + dx + (x - 12) * sc, 13.5 + dy + (y - 13.5) * sc) for x, y in pts]
            ic.energy(union(*(seg(*pts[i], *pts[i + 1], w) for i in range(2))), rm, falloff=w * 1.6)
            ic.glow(pts[1][0], pts[1][1], 4.5, rm[4], glow)
    # the pick: the casing cracked, the four elements glowing through
    A = G("0e0a18", "241a3a", (12, 12))
    cracked(A)
    # the cracks wide open, the light spilling out
    B = G("0e0a18", "2a1e44", (12, 12))
    cracked(B, w=0.9, glow=0.9)
    # close: the grenade huge and cropped
    C = G("0e0a18", "241a3a", (12, 12))
    cracked(C, 0, 1.5, 1.3, w=0.7)
    return A, B, C


def exposure():
    corners = ((1, 1), (23, 1), (23, 23), (1, 23))
    # the pick: four colours of light from the corners meeting at a crit star, heavier
    A = G("0c0a14", "1e1a2e", (12, 12))
    for rm, (x, y) in zip(ELEMS, corners):
        A.streak(x, y, 12 + (x - 12) * 0.12, 12 + (y - 12) * 0.12, 2.4, rm)
    A.glow(12, 12, 8, "ffffff", 1.0)
    star4(A, 12, 12, 7.5, falloff=2.6)
    # the beams from the edges instead, a cross of colour
    B = G("0c0a14", "1e1a2e", (12, 12))
    for rm, (x, y) in zip(ELEMS, ((12, 0), (24, 12), (12, 24), (0, 12))):
        B.streak(x, y, 12 + (x - 12) * 0.15, 12 + (y - 12) * 0.15, 2.2, rm)
    B.glow(12, 12, 7, "ffffff", 0.9)
    star4(B, 12, 12, 6, falloff=2.4)
    # swirling: the four colours curling in to the star
    C = G("0c0a14", "1e1a2e", (12, 12))
    for k, rm in enumerate(ELEMS):
        off = k * math.pi / 2
        pts = [(12 + math.cos(off + t * 0.12) * (12 - t * 0.85), 12 + math.sin(off + t * 0.12) * (12 - t * 0.85)) for t in range(0, 11)]
        for i in range(len(pts) - 1):
            C.energy(seg(*pts[i], *pts[i + 1], 0.4 + i * 0.12), rm, falloff=0.6)
    C.glow(12, 12, 6, "ffffff", 0.9)
    star4(C, 12, 12, 5, falloff=2)
    return A, B, C


# ---------------------------------------------------------------- turrets (all in my_turret's colours)
TG = ("040c0c", "0e2224")


def tur(ic, x, y, s=1.0, seed=0):
    turret(ic, x, y, s, accent=TEAL, seed=seed)
    ic.glow(x + 7 * s, y + 6 * s, 6 * s, "8ae0d4", 0.35)
    return x + 18.9 * s, y + 4.6 * s


def teal_ring(ic, cx, cy, rx, ry, w=0.45):
    ic.energy(lambda x, y: abs(math.hypot((x - cx) / rx, (y - cy) / ry) - 1) * 3 - w, TEAL, falloff=0.6)


def my_turret():
    # the pick: the turret standing in its teal ring
    A = G(*TG, (12, 14))
    teal_ring(A, 12, 19.5, 11, 3.2)
    tur(A, 3, 2.5)
    # the ring doubled and brighter, light coming up off it
    B = G(*TG, (12, 18))
    B.glow(12, 20, 10, "40a8a4", 0.6)
    teal_ring(B, 12, 19.5, 11, 3.2, w=0.6)
    teal_ring(B, 12, 19.5, 7, 2, w=0.35)
    tur(B, 3, 2.5)
    # close: the turret big, the ring cropped by the frame
    C = G(*TG, (12, 14))
    teal_ring(C, 11, 21, 14, 3.4)
    tur(C, 0.5, 0.5, 1.25)
    return A, B, C


def turret_():
    # the pick in my_turret's colours: firing, a flash at the barrel
    A = G(*TG, (14, 8))
    bx, by = tur(A, 1, 4, 1.1)
    flash(A, min(bx, 22.5), by, 2.6)
    # cases spilling off it as it fires
    B = G(*TG, (14, 8))
    bx, by = tur(B, 1, 5, 1.05)
    flash(B, min(bx, 22.5), by, 2.4)
    for k, (x, y, a) in enumerate(((7, 2, -60), (10, 1, -120), (4, 3, -150))):
        cartridge(B, x, y, a, 0.32, tip=BRASS, case=BRASS, seed=k, length=8, w=2.6)
    # close: the barrel's end and the flash big
    C = G(*TG, (16, 8))
    bx, by = tur(C, -2, 3, 1.3)
    flash(C, 22, by, 3)
    return A, B, C


def turret_reinforced():
    # the turret in my_turret's colours, a small shield in its corner
    A = G(*TG, (10, 8))
    tur(A, 0.5, 2.5, 1.05)
    A.solid(poly([(16, 14.5), (23, 14.5), (23, 19), (19.5, 23.5), (16, 19)]), STEEL, seed=2)
    A.solid(poly([(17.2, 15.6), (21.8, 15.6), (21.8, 18.6), (19.5, 21.8), (17.2, 18.6)]), TEAL, base=3, seed=3)
    # the shield up in the top corner
    B = G(*TG, (10, 8))
    tur(B, 0.5, 6, 1.0)
    B.solid(poly([(16, 0.5), (23, 0.5), (23, 5), (19.5, 9.5), (16, 5)]), STEEL, seed=2)
    B.solid(poly([(17.2, 1.6), (21.8, 1.6), (21.8, 4.6), (19.5, 7.8), (17.2, 4.6)]), TEAL, base=3, seed=3)
    # plated: steel panels bolted round its body, the shield in the corner
    C = G(*TG, (10, 8))
    tur(C, 0.5, 2.5, 1.05)
    C.solid(box(7.3, 8.4, 5.6, 4.0, 0, 1), STEEL, seed=4)
    for (x, y) in ((3, 5), (11, 5), (3, 11), (11, 11)):
        C.px([(x, y)], STEEL[5])
    C.solid(box(7.3, 8.4, 2.6, 1.0, 0, 0.3), TEAL, base=3.2, seed=5)
    C.solid(poly([(16, 14.5), (23, 14.5), (23, 19), (19.5, 23.5), (16, 19)]), STEEL, seed=2)
    C.solid(poly([(17.2, 15.6), (21.8, 15.6), (21.8, 18.6), (19.5, 21.8), (17.2, 18.6)]), TEAL, base=3, seed=3)
    return A, B, C


def turret_second():
    # the pick in my_turret's colours: two turrets staggered
    A = G(*TG, (12, 8))
    tur(A, -3, 0, 0.9)
    tur(A, 7, 8, 0.9, seed=3)
    # side by side, a teal ring under each
    B = G(*TG, (12, 12))
    for k, x in enumerate((-1, 10)):
        teal_ring(B, x + 6, 20.5, 5.5, 1.8, w=0.4)
        tur(B, x, 7, 0.72, seed=k * 3)
    # one behind the other, the back one dim
    C = G(*TG, (12, 8))
    tur(C, 5, 0, 0.8)
    C.shade(lambda x, y: -1 if y < 13 else 1, 0.55)
    tur(C, 0, 7, 1.0, seed=3)
    return A, B, C


def feed(ic, pts, s=0.5, ang_off=0):
    """A belt of rounds along pts, their tips cycling fire, ice, lightning, poison."""
    for k in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        a = math.degrees(math.atan2(y1 - y0, x1 - x0)) - 90 + ang_off
        cartridge(ic, x0, y0, a, s, tip=ELEMS[k % 4], seed=k, length=14, w=2.6)


def myturret_feed():
    # my_turret, a belt of four-element rounds chaining into its back
    A = G(*TG, (12, 8))
    tur(A, 5, 1, 1.0)
    feed(A, [(1, 23), (2.5, 20), (4.2, 17.2), (6.2, 14.6), (8, 12), (9.4, 9.5)])
    # the belt feeding in at its side from the foot of the frame
    B = G(*TG, (12, 8))
    feed(B, [(24, 22), (21, 21.4), (18, 20.4), (15.2, 18.8), (12.8, 16.6), (11, 14), (10, 11.5)])
    tur(B, 2, 1, 1.0)
    # the belt straight in from the left edge, the turret close
    C = G(*TG, (12, 8))
    tur(C, 6, 3, 0.95)
    feed(C, [(x, 10) for x in (0.5, 3.3, 6.1, 8.9)])
    return A, B, C


def person(ic, cx, cy, c, s=1.0):
    rmp = [mix(c, BLACK, 0.75), mix(c, BLACK, 0.5), mix(c, BLACK, 0.25), c, mix(c, WHITE, 0.45)]
    ic.solid(union(circle(cx, cy - 1.8 * s, 1.4 * s), box(cx, cy + 1.6 * s, 2.4 * s, 1.5 * s, 0, 1.2 * s)), rmp, base=3, seed=int(cx))


def myturret_shared():
    # the kept icon without its wrench: the turret, its healing pluses, the team beside it
    A = G("061206", "142e14", (8, 6))
    turret(A, 1, 5, 1.05)
    for (x, y) in ((4, 3), (12, 2.5)):
        A.energy(union(box(x, y, 2.3, 0.8), box(x, y, 0.8, 2.3)), TOXIC, falloff=0.9)
    person(A, 15.5, 18, hexc("4ac04a"), 1.4)
    person(A, 21, 18, hexc("e8e8e8"), 1.4)
    # in my_turret's colours, the team in all four of their colours
    B = G(*TG, (8, 6))
    tur(B, 1, 3, 1.0)
    for k, c in enumerate(TEAMC):
        person(B, 3.5 + k * 5.6, 20, c, 1.3)
    # the turret big, two of the team at its feet
    C = G("061206", "142e14", (8, 6))
    turret(C, 0, 1, 1.15)
    C.energy(union(box(20, 3, 2.3, 0.8), box(20, 3, 0.8, 2.3)), TOXIC, falloff=0.9)
    person(C, 16, 19.5, hexc("4ac04a"), 1.4)
    person(C, 21.5, 19.5, hexc("e8e8e8"), 1.4)
    return A, B, C


# ---------------------------------------------------------------- the table
FA_R2 = {f.__name__.rstrip("_"): f for f in (
    adrenaline, adrenaline_crit, adrenaline_epipen, adrenaline_hud, boom_headshot, burst, burst_breath, burst_triple,
    clip_hud, critical_aim, dodge_skip, explosive_reload, exposure, fat_boy, focus_hud, frag, frag_shrapnel, gas,
    gl_attack, gl_charges_hud, glock_attack, glock_dual, grenade_charges_hud, headshot, hoarder, incendiary,
    magic_missile, my_turret, myturret_feed, myturret_shared, over_reload, overpacked, piercing, quad_missile,
    reload, reloading_hud, rifle_attack, rocket_, rocket_charges_hud, rpg_jump, scavenger, scavenger_blind,
    scavenger_fire, scavenger_ice, scavenger_lightning, scavenger_poison, scavenger_slow, scavenger_stun,
    shrapnel, snipe, steady, steady_crit, stun_grenade, turret_, turret_reinforced, turret_second)}


if __name__ == "__main__":
    names = sys.argv[1:] or list(FA_R2)
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for n in names:
        ims = [ic.done() for ic in FA_R2[n]()]
        for k, im in zip("abc", ims):
            im.save(OUT / f"{n}_{k}.png")
        now = OUT / f"{n}_now.png"
        rows.append((n, ims + ([Image.open(now).convert("RGBA")] if now.exists() else [])))
    for i in range(0, len(rows), 14):
        sheet(rows[i:i + 14], OUT.parent / f"sheet_r2_{i // 14}.png", z=5)
    print(len(rows), "icons")
