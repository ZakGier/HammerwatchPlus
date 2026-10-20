"""Motifs for the vanilla classes' orb icons, painted with vpaint in the vanilla skill-icon
style: blades, shields, bows, books, elements, bodies. Same conventions as motifs.py:
(cx, cy) centre, ang in degrees clockwise on screen (0 = pointing right), s scale."""
import math
from vpaint import *
from motifs import L, lbox, lseg, parts, skull, heart, eye, flash, syringe

LEATHER = R("1a0e08", "3a2010", "5e3a1c", "865a2c", "b08448", "d8b070")
HOLY = R("2a1a04", "6a4a10", "b08a20", "e8c850", "fff0a0", "ffffff")
SHADOW = R("06040c", "140e22", "261a3e", "3e2c60", "62488a", "9a80c0")
FEL = R("0a1404", "1a3008", "2e5410", "4e8a1c", "86c83a", "d0f080", "ffffff")
CRIMSON = R("140406", "3a0a10", "6e1220", "a81e2e", "dc3a40", "ff8a80", "ffffff")
VOID = R("040208", "120a1e", "2a1240", "4a1e70", "7a3ab0", "b880f0", "ffffff")
EARTH = R("140e08", "30220e", "50381a", "785430", "a07a4a", "c8a878")
SPIRIT = R("040c14", "0a2030", "16405a", "286a8a", "50a0c0", "a0e0f0", "ffffff")
MANA = R("04081a", "0a1640", "16307a", "2a58b8", "5a90e8", "a8d0ff", "ffffff")
LIFE = R("041004", "0a2a0a", "146014", "2a9a2a", "5ad05a", "b0f0a0", "ffffff")
WINE = R("10040a", "2a0818", "4a1028", "701a3c", "a02a52", "d06080")


def G(dark, mid, light=(8, 6)):
    return Icon().ground(dark, mid, light=light)


def arc(cx, cy, r, w, a0, a1):
    """Ring segment between angles a0..a1 (degrees, screen clockwise from +x)."""
    A0, A1 = math.radians(a0), math.radians(a1)

    def f(x, y):
        a = math.atan2(y - cy, x - cx)
        while a < A0:
            a += 2 * math.pi
        inside = a <= A1
        d = abs(math.hypot(x - cx, y - cy) - r) - w / 2
        return d if inside else max(d, 1.0)
    return f


def star(cx, cy, r0, r1, n=5, rot=-90):
    pts = []
    for k in range(n * 2):
        a = math.radians(rot + k * 180 / n)
        r = r1 if k % 2 == 0 else r0
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return poly(pts)


# ---------------------------------------------------------------- blades and weapons
def dagger(ic, cx, cy, ang=-45, s=1.0, blade=STEEL, hilt=LEATHER, guard=BRASS, seed=0):
    """About 16 units long; tip toward ang."""
    items = [
        (lbox(-5.4, 0, 2.4, 1.2, 0.6), hilt, {"base": 2.2}),
        (lbox(-2.7, 0, 0.8, 3.0, 0.4), guard, {"base": 2.6}),
        (lambda x, y: poly([(-2.0, -1.9), (4.6, -1.7), (8.6, 0), (4.6, 1.7), (-2.0, 1.9)])(x, y), blade, {"base": 2.8, "rim": 1.5}),
        (lambda x, y: circle(-8.0, 0, 1.3)(x, y), guard, {"base": 2.6}),
    ]
    parts(ic, cx, cy, ang, s, items, seed)


def sword(ic, cx, cy, ang=-45, s=1.0, blade=STEEL, hilt=LEATHER, guard=BRASS, seed=0):
    """About 22 units long."""
    items = [
        (lbox(-8.0, 0, 2.6, 1.2, 0.6), hilt, {"base": 2.2}),
        (lbox(-5.0, 0, 0.9, 4.0, 0.4), guard, {"base": 2.6}),
        (lambda x, y: poly([(-4.2, -2.0), (9.0, -1.8), (12.4, 0), (9.0, 1.8), (-4.2, 2.0)])(x, y), blade, {"base": 2.8, "rim": 1.5}),
        (lambda x, y: circle(-10.8, 0, 1.4)(x, y), guard, {"base": 2.6}),
    ]
    parts(ic, cx, cy, ang, s, items, seed)


def axe(ic, cx, cy, ang=-60, s=1.0, head=STEEL, haft=WOOD, seed=0):
    """Head at the far end (u+), blade to the v- side."""
    items = [
        (lbox(-1, 0, 9.5, 0.9, 0.5), haft, {"base": 2.4}),
        (lambda x, y: poly([(5.0, 0.6), (5.2, -2.0), (3.2, -6.4), (9.6, -6.8), (8.4, -2.0), (8.6, 0.6)])(x, y), head, {"base": 2.6, "rim": 1.6}),
    ]
    parts(ic, cx, cy, ang, s, items, seed)


def hammer(ic, cx, cy, ang=-60, s=1.0, head=STEEL, haft=WOOD, seed=0):
    items = [
        (lbox(-1, 0, 9.0, 0.9, 0.5), haft, {"base": 2.4}),
        (lbox(7.0, 0, 2.6, 4.6, 0.6), head, {"base": 2.6, "rim": 1.6}),
    ]
    parts(ic, cx, cy, ang, s, items, seed)


def flail_head(ic, cx, cy, r, rmp=STEEL, spikes=8, seed=0):
    ic.solid(union(circle(cx, cy, r), *[seg(cx, cy, cx + math.cos(k * 6.283 / spikes) * (r + 2.2),
                                                cy + math.sin(k * 6.283 / spikes) * (r + 2.2), 0.9, 0.2) for k in range(spikes)]),
             rmp, seed=seed, base=2.6)


def chain(ic, x0, y0, x1, y1, rmp=STEEL, link=2.6, seed=0):
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) / link))
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    for k in range(n):
        t = (k + 0.5) / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        a = ang if k % 2 == 0 else ang
        if k % 2 == 0:
            ic.solid(cut(ellipse(x, y, link * 0.75, link * 0.45, a), ellipse(x, y, link * 0.4, link * 0.14, a)), rmp, seed=seed + k, base=2.8)
        else:
            ic.solid(ellipse(x, y, link * 0.75, link * 0.22, a), rmp, seed=seed + k, base=2.0)


def bow(ic, cx, cy, ang=0, s=1.0, rmp=WOOD, string=BONE, seed=0, drawn=0.0):
    """Bow facing ang (the arrow flies that way); limbs to v- and v+."""
    def limb(x, y):
        return abs(math.hypot(x + 6.0, y) - 9.0) - 0.9 if x > -1.2 else 9
    ic.solid(L(lambda x, y: inter(lambda xx, yy: abs(math.hypot(xx + 6.0, yy) - 9.0) - 1.0, lambda xx, yy: -xx - 1.0)(x, y), cx, cy, ang, s), rmp, seed=seed, base=2.6)
    ic.solid(L(lambda x, y: seg(-1.2 - drawn, 0, 0.5, -8.5, 0.35)(x, y), cx, cy, ang, s), string, seed=seed, flat=3.4, noise=0.2)
    ic.solid(L(lambda x, y: seg(-1.2 - drawn, 0, 0.5, 8.5, 0.35)(x, y), cx, cy, ang, s), string, seed=seed, flat=3.4, noise=0.2)


def arrow(ic, cx, cy, ang=-45, s=1.0, shaft=WOOD, head=STEEL, fletch=CRIMSON, seed=0, length=18):
    h = length / 2
    items = [
        (lbox(0, 0, h - 1, 0.8, 0.3), shaft, {"base": 3.0, "rim": 0.6}),
        (lambda x, y: poly([(h - 3.0, -2.4), (h + 2.0, 0), (h - 3.0, 2.4)])(x, y), head, {"base": 3.0, "rim": 1.5}),
        (lambda x, y: poly([(-h, -0.3), (-h + 3.2, -0.3), (-h + 1.6, -2.0), (-h - 0.6, -2.0)])(x, y), fletch, {"base": 3.0}),
        (lambda x, y: poly([(-h, 0.3), (-h + 3.2, 0.3), (-h + 1.6, 2.0), (-h - 0.6, 2.0)])(x, y), fletch, {"base": 2.2}),
    ]
    parts(ic, cx, cy, ang, s, items, seed)


def staff(ic, cx, cy, ang=-60, s=1.0, wood=WOOD, gem=ARCANE, seed=0):
    items = [(lbox(-1, 0, 10, 0.9, 0.5), wood, {"base": 2.4})]
    parts(ic, cx, cy, ang, s, items, seed)
    a = math.radians(ang)
    gx, gy = cx + math.cos(a) * 10 * s, cy + math.sin(a) * 10 * s
    ic.energy(circle(gx, gy, 2.2 * s), gem, falloff=1.6)


def shield(ic, cx, cy, s=1.0, rmp=STEEL, face=None, boss=BRASS, seed=0, kite=True):
    if kite:
        f = poly([(cx - 7 * s, cy - 7 * s), (cx + 7 * s, cy - 7 * s), (cx + 7 * s, cy + 0 * s), (cx, cy + 9 * s), (cx - 7 * s, cy + 0 * s)])
        inner = poly([(cx - 5.2 * s, cy - 5.4 * s), (cx + 5.2 * s, cy - 5.4 * s), (cx + 5.2 * s, cy - 0.4 * s), (cx, cy + 6.6 * s), (cx - 5.2 * s, cy - 0.4 * s)])
    else:
        f = circle(cx, cy, 8.5 * s)
        inner = circle(cx, cy, 6.6 * s)
    ic.solid(f, rmp, seed=seed, base=2.6)
    if face:
        ic.solid(inner, face, seed=seed + 1, base=2.4)
    if boss:
        ic.solid(circle(cx, cy - (1 * s if kite else 0), 1.8 * s), boss, seed=seed + 2, base=3.0)


def book(ic, cx, cy, s=1.0, cover=CRIMSON, page=PAPER, seed=0, open_=False):
    if open_:
        ic.solid(poly([(cx - 10 * s, cy - 4 * s), (cx, cy - 2 * s), (cx + 10 * s, cy - 4 * s), (cx + 10 * s, cy + 5 * s), (cx, cy + 7 * s), (cx - 10 * s, cy + 5 * s)]), cover, seed=seed, base=2.2)
        ic.solid(poly([(cx - 9 * s, cy - 5 * s), (cx - 0.4 * s, cy - 3 * s), (cx - 0.4 * s, cy + 5.6 * s), (cx - 9 * s, cy + 3.6 * s)]), page, seed=seed + 1, base=3.6, spread=0.8)
        ic.solid(poly([(cx + 0.4 * s, cy - 3 * s), (cx + 9 * s, cy - 5 * s), (cx + 9 * s, cy + 3.6 * s), (cx + 0.4 * s, cy + 5.6 * s)]), page, seed=seed + 2, base=3.0, spread=0.8)
    else:
        ic.solid(box(cx + 0.8 * s, cy + 0.8 * s, 6.4 * s, 8 * s, 0, 0.6), page, seed=seed, base=3.2)
        ic.solid(box(cx, cy, 6.4 * s, 8 * s, 0, 0.6), cover, seed=seed + 1, base=2.6)
        ic.solid(box(cx - 5.2 * s, cy, 0.8 * s, 8 * s, 0, 0.2), cover, seed=seed + 2, base=1.6)


def potion(ic, cx, cy, s=1.0, liquid=CRIMSON, glass=SPIRIT, seed=0):
    ic.solid(union(circle(cx, cy + 2 * s, 5.4 * s), box(cx, cy - 4.4 * s, 1.6 * s, 2.6 * s, 0, 0.4)), glass, seed=seed, base=1.6, spread=1.0)
    ic.energy(inter(circle(cx, cy + 2 * s, 4.6 * s), lambda x, y: (cy + 0.4 * s) - y), liquid, falloff=2.5)
    ic.solid(box(cx, cy - 7.2 * s, 2.0 * s, 0.9 * s, 0, 0.3), WOOD, seed=seed + 1, base=3.0)
    ic.glint(int(cx - 2.4 * s), int(cy + 0.4 * s))


# ---------------------------------------------------------------- elements
def bolt_sdf(pts, w=1.1):
    return union(*[seg(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], w * (1 - i * 0.12), w * (1 - (i + 1) * 0.12)) for i in range(len(pts) - 1)])


def bolt(ic, pts, rmp=VOLT, w=1.1, fall=1.0):
    ic.energy(bolt_sdf(pts, w), rmp, falloff=fall)


def snowflake(ic, cx, cy, r, rmp=ICE, w=0.6, fall=0.8):
    arms = []
    for k in range(6):
        a = math.radians(k * 60 - 90)
        ex, ey = cx + math.cos(a) * r, cy + math.sin(a) * r
        arms.append(seg(cx, cy, ex, ey, w))
        for t in (0.55,):
            mx, my = cx + math.cos(a) * r * t, cy + math.sin(a) * r * t
            for sgn in (-1, 1):
                b = a + sgn * math.radians(45)
                arms.append(seg(mx, my, mx + math.cos(b) * r * 0.35, my + math.sin(b) * r * 0.35, w * 0.8))
    ic.energy(union(*arms), rmp, falloff=fall)


def shard(cx, cy, ang, length, w):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    pts = [(-length * 0.35, 0), (0, -w), (length * 0.65, 0), (0, w)]
    return poly([(cx + u * ca - v * sa, cy + u * sa + v * ca) for u, v in pts])


def drop(cx, cy, r):
    """A droplet with its tip up."""
    return union(circle(cx, cy + r * 0.35, r), poly([(cx - r * 0.86, cy + r * 0.0), (cx, cy - r * 1.6), (cx + r * 0.86, cy + r * 0.0)]))


def cloud(ic, puffs, rmp, seed=0, base=None):
    for k, (x, y, r) in enumerate(puffs):
        ic.solid(circle(x, y, r), rmp, seed=seed + k, base=base if base is not None else 2.6 - k * 0.15, spread=1.2)


def fireball(ic, cx, cy, r, ang=-45, rmp=FIRE, tail=1.8):
    a = math.radians(ang)
    tx, ty = cx - math.cos(a) * r * tail * 2, cy - math.sin(a) * r * tail * 2
    ic.energy(union(circle(cx, cy, r), seg(tx, ty, cx, cy, r * 0.25, r * 0.9)), rmp, falloff=r * 0.9)


def wisp(ic, cx, cy, r, rmp=SPIRIT, ang=-90, seed=0):
    """A soul flame: a round head trailing a wavering tail away from ang."""
    a = math.radians(ang)
    pts = []
    for k in range(6):
        t = k / 5
        pts.append((cx - math.cos(a) * r * 3 * t + math.sin(t * 5 + seed) * r * 0.4 * t,
                    cy - math.sin(a) * r * 3 * t))
    f = union(circle(cx, cy, r), *[seg(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], r * (1 - i / 6), r * (1 - (i + 1) / 6)) for i in range(5)])
    ic.energy(f, rmp, falloff=r)


# ---------------------------------------------------------------- bodies
def boot(ic, cx, cy, s=1.0, rmp=LEATHER, seed=0, wing=None):
    """A boot seen from the side, toe to the right; (cx, cy) is the middle of the shaft."""
    P = lambda pts: poly([(cx + u * s, cy + v * s) for u, v in pts])
    if wing:
        for k in range(3):
            ic.solid(ellipse(cx - 6.5 * s - k * 0.8 * s, cy - 4.5 * s + k * 2.6 * s, 4.4 * s - k * 0.6 * s, 1.3 * s, -25 + k * 18), wing, seed=seed + 2 + k, base=3.6 - k * 0.5)
    ic.solid(P([(-4.4, -8.5), (2.6, -8.5), (2.8, 2.0), (6.0, 3.0), (8.6, 4.4), (9.0, 7.6), (-4.6, 7.6), (-5.0, 2.0)]), rmp, seed=seed, base=2.6)
    ic.solid(P([(-4.8, -9.0), (3.0, -9.0), (3.0, -6.6), (-4.8, -6.6)]), rmp, seed=seed + 1, base=3.6)
    ic.solid(P([(-4.8, 6.4), (9.2, 6.4), (9.2, 8.4), (-4.8, 8.4)]), rmp, seed=seed + 6, base=1.0, spread=0.4)


def gauntlet(ic, cx, cy, s=1.0, rmp=STEEL, seed=0):
    """A clenched armoured fist from the front, knuckles up."""
    ic.solid(box(cx, cy + 6 * s, 4.2 * s, 3.4 * s, 0, 1), rmp, seed=seed + 9, base=1.8)
    ic.solid(box(cx, cy + 0.6 * s, 6.0 * s, 4.6 * s, 0, 2.2 * s), rmp, seed=seed, base=2.6)
    for k in range(4):
        ic.solid(ellipse(cx - 4.2 * s + k * 2.8 * s, cy - 3.6 * s, 1.5 * s, 1.4 * s), rmp, seed=seed + k + 1, base=3.4)
    ic.solid(ellipse(cx - 2.0 * s, cy + 2.6 * s, 3.8 * s, 1.4 * s, -10), rmp, seed=seed + 7, base=3.0)


def fist(ic, cx, cy, s=1.0, rmp=SKIN, seed=0):
    ic.solid(box(cx, cy, 5 * s, 4.4 * s, 0, 1.8), rmp, seed=seed, base=2.6)
    for k in range(4):
        ic.solid(box(cx - 3.6 * s + k * 2.4 * s, cy - 3.6 * s, 1.15 * s, 1.6 * s, 0, 0.8), rmp, seed=seed + k + 1, base=3.0)
    ic.solid(box(cx - 4.2 * s, cy + 0.6 * s, 1.4 * s, 3.0 * s, -30, 0.8), rmp, seed=seed + 6, base=2.0)


def hand_open(ic, cx, cy, s=1.0, rmp=SKIN, seed=0):
    ic.solid(box(cx, cy + 2 * s, 4.4 * s, 4.2 * s, 0, 1.6), rmp, seed=seed, base=2.6)
    for k, (dx, h) in enumerate(((-3.3, 5.0), (-1.1, 6.0), (1.1, 6.2), (3.3, 5.2))):
        ic.solid(box(cx + dx * s, cy - 3.2 * s - (h - 5) * s, 0.95 * s, h * 0.55 * s + 1.6 * s, 0, 0.9), rmp, seed=seed + k + 1, base=2.8)
    ic.solid(box(cx - 5.6 * s, cy + 1.4 * s, 1.1 * s, 3.0 * s, 35, 0.9), rmp, seed=seed + 7, base=2.4)


def hourglass(ic, cx, cy, s=1.0, frame=WOOD, sand=GOLD, seed=0, t=0.5):
    glass = union(poly([(cx - 4.4 * s, cy - 7 * s), (cx + 4.4 * s, cy - 7 * s), (cx + 0.7 * s, cy), (cx + 4.4 * s, cy + 7 * s),
                        (cx - 4.4 * s, cy + 7 * s), (cx - 0.7 * s, cy)]))
    ic.solid(glass, SPIRIT, seed=seed, base=1.2, spread=0.9)
    ic.energy(inter(glass, lambda x, y: (cy + 7 * s - (1 - t) * 6 * s) - y if y > cy else (y - (cy - 7 * s + t * 6 * s))), sand, falloff=1.5, hot=4)
    for yy in (-7.6, 7.6):
        ic.solid(box(cx, cy + yy * s, 5.6 * s, 1.0 * s, 0, 0.4), frame, seed=seed + 1, base=3.0)


def wolf_head(ic, cx, cy, s=1.0, rmp=SMOKE, eyes=SPIRIT, seed=0):
    """A wolf's head in profile, snout to the right."""
    ic.solid(union(ellipse(cx - 1 * s, cy, 5.6 * s, 4.8 * s), poly([(cx + 1 * s, cy - 2.4 * s), (cx + 8.6 * s, cy + 0.6 * s), (cx + 8.2 * s, cy + 2.6 * s), (cx + 1 * s, cy + 4 * s)]),
                   poly([(cx - 4.4 * s, cy - 2.6 * s), (cx - 2.6 * s, cy - 9 * s), (cx - 0.4 * s, cy - 3.6 * s)]),
                   poly([(cx - 1.6 * s, cy - 3.4 * s), (cx + 0.6 * s, cy - 8.4 * s), (cx + 2.2 * s, cy - 2.6 * s)])), rmp, seed=seed, base=2.6)
    ic.energy(circle(cx + 1.8 * s, cy - 0.8 * s, 0.9 * s), eyes, falloff=0.8)
    ic.solid(circle(cx + 8.4 * s, cy + 1.0 * s, 0.9 * s), R("08080a", "1a1a1e", "303036"), seed=seed + 3, base=1)


def crosshair(ic, cx, cy, r, rmp=CRIMSON, w=0.8):
    ic.energy(union(ring(cx, cy, r, w * 1.2), seg(cx - r - 2.5, cy, cx - r + 2.2, cy, w * 0.6), seg(cx + r - 2.2, cy, cx + r + 2.5, cy, w * 0.6),
                    seg(cx, cy - r - 2.5, cx, cy - r + 2.2, w * 0.6), seg(cx, cy + r - 2.2, cx, cy + r + 2.5, w * 0.6)), rmp, falloff=0.8)


def holy_cross(cx, cy, s=1.0):
    return union(box(cx, cy, 1.5 * s, 7 * s, 0, 0.4), box(cx, cy - 2.4 * s, 5 * s, 1.5 * s, 0, 0.4))


def sun(ic, cx, cy, r, rmp=HOLY, n=10):
    ic.energy(union(circle(cx, cy, r), *[seg(cx + math.cos(k * 6.283 / n) * r, cy + math.sin(k * 6.283 / n) * r,
                                              cx + math.cos(k * 6.283 / n) * r * 1.9, cy + math.sin(k * 6.283 / n) * r * 1.9, r * 0.25, 0.1) for k in range(n)]), rmp, falloff=r * 0.8)


def bomb(ic, cx, cy, r, rmp=GUN, fuse=True, seed=0, spark=FIRE):
    ic.solid(circle(cx, cy, r), rmp, seed=seed, base=2.2)
    ic.solid(box(cx + r * 0.55, cy - r * 0.85, r * 0.32, r * 0.3, 40, 0.2), STEEL, seed=seed + 1, base=2.8)
    if fuse:
        ic.solid(seg(cx + r * 0.75, cy - r * 1.05, cx + r * 1.15, cy - r * 1.55, 0.45), WOOD, seed=seed + 2, base=3.2)
        flash(ic, cx + r * 1.2, cy - r * 1.6, 1.8, spark)
    ic.glint(int(cx - r * 0.45), int(cy - r * 0.45))


def slash(ic, cx, cy, r, a0, a1, rmp=STEEL, w=1.6):
    """A crescent slash mark."""
    ic.energy(arc(cx, cy, r, w, a0, a1), rmp, falloff=w * 0.6)


def cog(ic, cx, cy, r, rmp=BRASS, teeth=8, seed=0):
    f = union(circle(cx, cy, r), *[box(cx + math.cos(k * 6.283 / teeth) * r, cy + math.sin(k * 6.283 / teeth) * r, 1.4, 1.0,
                                         math.degrees(k * 6.283 / teeth), 0.2) for k in range(teeth)])
    ic.solid(cut(f, circle(cx, cy, r * 0.38)), rmp, seed=seed, base=2.6)
