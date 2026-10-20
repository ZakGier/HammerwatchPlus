"""Firearms Specialist icons in the vanilla style, three ideas each (the grenades; fa2.py
and fa3.py hold the rest). python fa.py [names...] -> out/firearms/<name>_<a|b|c>.png and
out/sheet.png, a comparison sheet with the icon in the game now beside each."""
import math, sys
from pathlib import Path
from PIL import Image
from vpaint import *

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "out" / "firearms"
OUT.mkdir(parents=True, exist_ok=True)
CUR = REPO / "mods/firearms/players/hwp/firearms/icons.png"


# ================================================================ shared motifs
def pineapple(ic, cx, cy, rx, ry, rmp=OLIVE, seed=0, lever=True):
    body = ellipse(cx, cy, rx, ry)
    ic.solid(body, rmp, seed=seed, noise=0.35)
    # segment grooves: darker lines on a grid, each segment's upper-left pixel lit
    gx, gy = rx * 2 / 4.2, ry * 2 / 5.2
    for y in range(N):
        for x in range(N):
            if body(x + 0.5, y + 0.5) < -0.6:
                u, v = (x + 0.5 - cx + rx) / gx, (y + 0.5 - cy + ry) / gy
                if (u % 1) < 1 / gx * 1.05 or (v % 1) < 1 / gy * 1.05:
                    o = ic.p[x, y]
                    ic.p[x, y] = tuple(int(c * 0.55) for c in o)
    top = cy - ry
    ic.solid(box(cx, top - 0.2, 2.2, 1.6, 0, 0.4), STEEL, base=3, seed=seed + 1)
    if lever:
        ic.solid(seg(cx + 1.5, top - 1.2, cx + rx * 0.75, cy - ry * 0.1, 0.8), STEEL, base=3.4, seed=seed + 2)


def canister(ic, cx, top, bot, hw, rmp, bands=(), seed=0, cap=STEEL):
    ic.solid(box(cx, (top + bot) / 2, hw, (bot - top) / 2, 0, 1.0), rmp, light=(-1, -0.15), seed=seed)
    for (y0, y1, br) in bands:
        ic.solid(box(cx, (y0 + y1) / 2, hw + 0.01, (y1 - y0) / 2 + 0.01, 0, 0.2), br, light=(-1, -0.15), seed=seed + 3)
    ic.solid(box(cx, top - 1, hw * 0.55, 1.4, 0, 0.4), cap, base=3, light=(-1, -0.3), seed=seed + 1)


def blast(ic, cx, cy, r, rmp=FIRE, n=9, seed=4, hole=0.0):
    """A ragged fire burst: a lobed blob, white-hot inside, a dark hole if hole > 0."""
    def f(x, y):
        a = math.atan2(y - cy, x - cx)
        lob = 1 + 0.22 * math.sin(a * n + seed) + 0.12 * math.sin(a * (n * 2 + 1) + seed * 2)
        return math.hypot(x - cx, y - cy) - r * lob
    ic.energy(f, rmp, falloff=r * 0.8, seed=seed)
    if hole:
        ic.paint(circle(cx, cy, hole), lambda x, y, d: pick(rmp, 0.6 + (-d) * 0 + grain(x, y, seed) * 0.6))
    return f


def shards(ic, cx, cy, r0, r1, n, rmp, seed=6, w=1.0):
    for k in range(n):
        a = (k + h2(k, seed) * 0.6) / n * 6.283
        rr0 = r0 + h2(k, seed + 1) * 2
        rr1 = r1 + h2(k, seed + 2) * 3
        ic.solid(seg(cx + math.cos(a) * rr0, cy + math.sin(a) * rr0, cx + math.cos(a) * rr1, cy + math.sin(a) * rr1, w * 0.4, w),
                 rmp, base=3, seed=seed + k)


# ================================================================ grenades
def frag():
    A = Icon().ground("0e1008", "2a3018", light=(6, 5))
    A.glow(10, 10, 12, "3a4a1a", 0.6)
    pineapple(A, 11.5, 14, 8.5, 9.5)
    A.solid(ring(4.5, 4.5, 2.4, 1.1), BRASS, base=3.5)
    # B: the burst: fire ring, dark smoke hole, iron fragments flying out
    B = Icon().ground("140804", "3a1608", light=(12, 12))
    B.rays(12, 12, EMBER, n=7, lo=0, hi=3)
    blast(B, 12, 12, 7.5, FIRE, 7, hole=2.6)
    shards(B, 12, 12, 8, 11, 7, GUN, w=1.3)
    # C: the pin pulled: a big brass ring hooked on a finger, the grenade dark behind it
    C = Icon().ground("0e1008", "262c14", light=(14, 8))
    pineapple(C, 15, 15, 8, 9, OLIVE[:4], lever=False)
    C.shade(lambda x, y: -1, 0.75)
    C.solid(seg(0, 12, 7, 9, 3.2, 2.6), SKIN, seed=3)
    C.solid(ring(9.5, 10, 4.6, 1.6), GOLD, seed=4)
    C.solid(seg(13.5, 11.5, 18, 6, 0.7), BRASS, base=4)
    return A, B, C


def stun_grenade():
    # A: the flashbang can, its ports blazing
    A = Icon().ground("0a0c1a", "1e2448", light=(8, 6))
    canister(A, 12, 6, 23, 6.5, STEEL, bands=[(7, 8, GUN)])
    for y in (11, 15, 19):
        for x in (8, 12, 16):
            A.energy(ellipse(x, y, 1.0, 1.4), R("1a1a40", "5a5ab0", "a8a8ff", "e8e8ff", "ffffff"), falloff=1)
    A.glow(12, 15, 10, "8a8aff", 0.5)
    # B: it goes off: blinding white star swallowing everything
    B = Icon().ground("0c0e24", "28306a", light=(12, 12))
    B.rays(12, 12, R("1a1a40", "4a4ac0", "a0a0ff", "e0e0ff", "ffffff"), n=8, lo=0.5, hi=4.5, width=0.45)
    B.glow(12, 12, 13, "c0c0ff", 1.2)
    B.energy(poly([(12, 2), (14, 10), (22, 12), (14, 14), (12, 22), (10, 14), (2, 12), (10, 10)]),
             R("2a2a70", "6a6ae0", "b0b0ff", "e8e8ff", "ffffff", "ffffff"), falloff=3)
    # C: a ringing ear: concentric shock rings, the can a dark shape at their heart
    C = Icon().ground("080a18", "1a1e40", light=(12, 12))
    BL = R("1a1a40", "4a4ac0", "a0a0ff", "e0e0ff", "ffffff")
    for r, w in ((10, 1.6), (6, 2.0)):
        arcs = inter(ring(12, 12, r, w), lambda x, y: -abs(math.sin(math.atan2(y - 12, x - 12) * 2 + 0.8)) + 0.35)
        C.energy(arcs, BL, falloff=0.9)
    C.glow(12, 12, 6, "c0c0ff", 1.0)
    C.energy(circle(12, 12, 2.4), BL + [WHITE], falloff=2)
    return A, B, C


def incendiary():
    # A: the red can lying on its side, fire jetting out of its vents
    A = Icon().ground("140604", "3a1206", light=(14, 8))
    A.glow(15, 10, 12, "ff6010", 0.8)
    for k, (x, lean, h) in enumerate(((8, -1.5, 13), (12, 0.5, 17), (16, 1.5, 14), (20, 2, 10))):
        A.energy(flame(x, 18, 3.2, h, lean, k), FIRE, falloff=2.4, seed=k)
    A.solid(box(11, 19.5, 9.5, 3.6, 0, 2.2), RED, light=(-0.3, -1), seed=2)
    for x in (5, 16):
        A.solid(box(x, 19.5, 0.8, 3.65, 0, 0.3), GOLD, light=(-0.3, -1))
    # B: a wall of fire across the floor, the can a black shape lying in it
    B = Icon().ground("140604", "2e0e04", light=(12, 18))
    B.glow(12, 20, 14, "ff4010", 0.9)
    for k, x in enumerate((1, 5.5, 10, 14.5, 19, 23)):
        B.energy(flame(x, 24, 3.6, 12 + 9 * h2(k, 2), (h2(k, 5) - 0.5) * 3, k), FIRE, falloff=2.8, seed=k)
    B.solid(box(12, 20.5, 5.5, 2.4, -8, 1.2), EMBER, base=0.9, spread=0.7, rim=1.2)
    # C: one tall flame, the canister black inside its heart
    C = Icon().ground("100404", "300a04", light=(12, 12))
    C.glow(12, 13, 12, "ff5010", 0.9)
    C.energy(flame(12, 24, 9, 23, 0.5, 2), FIRE, falloff=6)
    C.solid(box(12, 17.5, 3, 4.2, 0, 1.2), EMBER[:3], base=0.6, spread=0.5, rim=1.5)
    C.solid(box(12, 12.6, 1.6, 0.9, 0, 0.3), EMBER[:3], base=0.8, spread=0.4)
    return A, B, C


def gas():
    A = Icon().ground("06100a", "142a14", light=(16, 6))
    canister(A, 9, 10, 24, 5.6, OLIVE, bands=[(13, 13.7, GOLD), (16, 16.7, GOLD)])
    for k, (x, y, r) in enumerate(((14, 6, 4.4), (19, 9, 3.8), (10, 3.5, 3.2), (20, 3.5, 3.4), (16, 12, 2.6))):
        A.solid(circle(x, y, r), GAS, base=3.2, spread=1.6, rim=1.2, seed=k)
    # B: a choking cloud filling the frame, a figure doubled over in it
    B = Icon().ground("06100a", "1a3a14", light=(12, 12))
    for k, (x, y, r) in enumerate(((5, 7, 6), (16, 5, 6.5), (20, 15, 6), (7, 17, 6.5), (13, 20, 5), (12, 11, 5))):
        B.solid(circle(x, y, r), GAS, base=2.2 + k * 0.25, spread=1.4, rim=1.0, seed=k)
    B.solid(union(circle(9, 11, 2.4), seg(10, 13, 14, 15, 2, 2.4), seg(14, 15, 14, 23, 1.6), seg(10, 13, 8, 18, 0.9)), GAS[:2], base=0.6, spread=0.3, rim=0.2, core=0)
    # C: a gas mask, its eyes glowing green
    C = Icon().ground("06100a", "142a14", light=(12, 6))
    C.solid(union(ellipse(12, 11, 8.5, 9), box(12, 19, 3.6, 3, 0, 1.2)), GUN, seed=2)
    for x in (8.2, 15.8):
        C.solid(circle(x, 10, 3), STEEL, base=2.4, seed=3)
        C.energy(circle(x, 10, 2), TOXIC, falloff=1.6)
    C.solid(circle(12, 20, 2.8), OLIVE, base=2.6, seed=4)
    for x in (11, 13):
        C.px([(x, 20)], OLIVE[0])
    return A, B, C


FA = {"frag": frag, "stun_grenade": stun_grenade, "incendiary": incendiary, "gas": gas}


_now = {}


def current(name):
    """The icon the game shows for name now (tools/make_firearms_icons.py's ICONS cell in the
    skills atlas), or None; the tool's table and the atlas are loaded once."""
    if not _now:
        import importlib.util
        spec = importlib.util.spec_from_file_location("m", REPO / "tools/make_firearms_icons.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _now["icons"] = m.ICONS
        _now["atlas"] = Image.open(CUR).convert("RGBA")
    if name not in _now["icons"]:
        return None
    atlas, col, row = _now["icons"][name][:3]
    if atlas != "skills":
        return None
    return _now["atlas"].crop((col * 24, row * 24, col * 24 + 24, row * 24 + 24))


if __name__ == "__main__":
    names = sys.argv[1:] or list(FA)
    rows = []
    for n in names:
        ims = [ic.done() for ic in FA[n]()]
        for k, im in zip("abc", ims):
            im.save(OUT / f"{n}_{k}.png")
        cur = current(n)
        rows.append((n, ims + ([cur] if cur else [])))
    sheet(rows, OUT.parent / "sheet.png", z=6)
    print(len(rows))
