"""Objects for the Firearms icons, painted with vpaint: guns, rounds, mags, rockets,
turrets, and a few body parts. Each takes a centre, an angle (0 = pointing right,
degrees clockwise on screen) and a scale, and paints itself back to front."""
import math
from vpaint import *


def L(f, cx, cy, ang, s=1.0):
    """Wrap a local-space SDF (u forward, v to the right-hand side) into world space."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)

    def g(x, y):
        dx, dy = x - cx, y - cy
        u, v = (dx * ca + dy * sa) / s, (-dx * sa + dy * ca) / s
        return f(u, v) * s
    return g


def lbox(u, v, hu, hv, r=0.3):
    return lambda x, y: box(u, v, hu, hv, 0, r)(x, y)


def lseg(u0, v0, u1, v1, r0, r1=None):
    return lambda x, y: seg(u0, v0, u1, v1, r0, r1)(x, y)


def parts(ic, cx, cy, ang, s, items, seed=0):
    for k, (f, rmp, kw) in enumerate(items):
        ic.solid(L(f, cx, cy, ang, s), rmp, seed=seed + k, **kw)


# ---------------------------------------------------------------- guns
def rifle(ic, cx, cy, ang=-35, s=1.0, scope=False, wood=WOOD, metal=GUN, gl=False, seed=0):
    """About 22 units long at s=1, centred on the receiver."""
    items = [
        (lbox(-7.5, 0.6, 3.6, 1.6, 0.6), wood, {}),                       # stock
        (lbox(-3.6, 1.6, 1.0, 2.2, 0.4), wood, {"base": 1.8}),            # grip
        (lbox(-1, 0, 3.2, 1.5, 0.3), metal, {}),                          # receiver
        (lbox(1.2, 2.6, 1.0, 2.2, 0.3), metal, {"base": 1.6}),            # mag
        (lbox(4.4, 0.3, 2.6, 1.2, 0.4), wood, {"base": 2.6}),             # handguard
        (lbox(8.6, -0.3, 3.2, 0.55, 0.2), metal, {"base": 2.6, "rim": 1.2}),  # barrel
    ]
    if gl:
        items.append((lbox(5.6, 2.0, 3.4, 1.05, 0.6), OLIVE, {"base": 2.6}))
    if scope:
        items.append((lbox(-0.6, -2.3, 3.0, 0.95, 0.6), metal, {"base": 2.2, "rim": 1.5}))
        items.append((lbox(-0.6, -1.3, 0.7, 0.5, 0.1), metal, {"base": 1.5}))
    parts(ic, cx, cy, ang, s, items, seed)


def pistol(ic, cx, cy, ang=0, s=1.0, metal=GUN, grip=None, seed=0, flip=False):
    """About 13 units long at s=1; the grip hangs below (v+)."""
    grip = grip or metal
    fv = -1 if flip else 1
    items = [
        (lbox(-2.2, 3.4 * fv, 1.5, 3.0, 0.5), grip, {"base": 1.8}),
        (lambda x, y: ring(0.6, 2.2 * fv, 1.4, 0.7)(x, y), metal, {"base": 1.8}),
        (lbox(0.6, 0, 6.0, 1.45, 0.4), metal, {"rim": 1.4}),
    ]
    parts(ic, cx, cy, ang, s, items, seed)


def flash(ic, x, y, r=3.2, rmp=FIRE, seed=1):
    f = lambda X, Y: math.hypot(X - x, Y - y) - r * (0.55 + 0.45 * abs(math.cos(math.atan2(Y - y, X - x) * 3 + seed)))
    ic.energy(f, rmp, falloff=r * 0.7, seed=seed)
    ic.glow(x, y, r * 2.4, rmp[4], 0.7)


# ---------------------------------------------------------------- rounds
def cartridge(ic, cx, cy, ang=-90, s=1.0, tip=COPPER, case=BRASS, seed=0, length=12, w=2.0):
    """A whole round; ang points the tip. length/w in units at s=1."""
    hl = length / 2

    def tipf(u, v):
        t = (u - (hl * 0.15)) / (hl * 0.85)
        if t < 0 or t > 1:
            return 1
        return abs(v) - w * max(0.0, 1 - t * t) ** 0.5
    items = [
        (lbox(-hl * 0.42, 0, hl * 0.58, w, 0.3), case, {}),
        (lbox(-hl * 1.0, 0, 0.5, w + 0.2, 0.2), case, {"base": 2}),
        (tipf, tip, {}),
    ]
    parts(ic, cx, cy, ang, s, items, seed)


def slug(ic, cx, cy, ang, s=1.0, rmp=COPPER, seed=0, length=7, w=1.8):
    hl = length / 2

    def f(u, v):
        t = (u + hl) / (2 * hl)
        if t < 0 or t > 1:
            return 1
        prof = w * (1 if t < 0.5 else max(0, 1 - ((t - 0.5) / 0.5) ** 2) ** 0.5)
        return abs(v) - prof
    ic.solid(L(f, cx, cy, ang, s), rmp, seed=seed)


def shell(ic, cx, cy, ang=-90, s=1.0, hull=RED, seed=0, length=12, w=2.6):
    hl = length / 2
    items = [
        (lbox(hl * 0.25, 0, hl * 0.75, w, 0.6), hull, {}),
        (lbox(-hl * 0.65, 0, hl * 0.35, w + 0.15, 0.3), BRASS, {}),
    ]
    parts(ic, cx, cy, ang, s, items, seed)


def mag(ic, cx, cy, ang=0, s=1.0, rmp=GUN, h=12, w=3.4, seed=0, top_round=True):
    """A box mag standing up (ang tilts it), lips at the top."""
    hh = h / 2
    items = [
        (lbox(0, 0, w, hh, 0.6), rmp, {}),
        (lbox(0, hh - 0.6, w + 0.7, 0.9, 0.4), rmp, {"base": 1.6}),
    ]
    a = math.radians(ang)
    # local here: u = x across, v = y down (stand-up mag)
    for k, (f, r, kw) in enumerate(items):
        ic.solid(L(lambda u, v, f=f: f(u, v), cx, cy, ang, s), r, seed=seed + k, **kw)
    if top_round:
        cartridge(ic, cx + math.sin(a) * (hh + 1.4) * s, cy - math.cos(a) * (hh + 1.4) * s, ang - 90, s * 0.55, w=1.8 * 1.5, length=8, seed=seed + 5)


def rocket(ic, cx, cy, ang, s=1.0, nose=RED, body=OLIVE, band=GOLD, length=16, w=2.6, fins=True, seed=0):
    hl = length / 2

    def nosef(u, v):
        t = (u - hl * 0.45) / (hl * 0.55)
        if t < 0 or t > 1:
            return 1
        return abs(v) - w * (1 - t ** 1.6) ** 0.6
    items = []
    if fins:
        items.append((lambda u, v: poly([(-hl, -w - 2.4), (-hl * 0.55, -w), (-hl * 0.55, w), (-hl, w + 2.4), (-hl + 1.4, 0)])(u, v), STEEL, {"base": 2.2}))
    items += [
        (lbox(-hl * 0.05, 0, hl * 0.52, w, 0.4), body, {}),
        (lbox(hl * 0.2, 0, 0.6, w + 0.05, 0.1), band, {}),
        (nosef, nose, {}),
    ]
    parts(ic, cx, cy, ang, s, items, seed)


def tube(ic, cx, cy, ang, s=1.0, seed=0):
    """A shoulder rocket launcher tube."""
    items = [
        (lbox(0, 0, 9.5, 2.4, 0.5), OLIVE, {}),
        (lbox(-9.2, 0, 0.9, 2.9, 0.3), GUN, {"base": 2}),
        (lbox(9.2, 0, 0.9, 2.9, 0.3), GUN, {"base": 2}),
        (lbox(-1, 3.4, 1.0, 2.0, 0.4), WOOD, {"base": 1.8}),
        (lbox(2, -3.2, 1.4, 0.9, 0.3), GUN, {"base": 2.4}),
    ]
    parts(ic, cx, cy, ang, s, items, seed)


def cut40(ic, cx, cy, ang=-90, s=1.0, seed=0):
    """A 40 mm grenade round: stubby olive head on a short brass case."""
    items = [
        (lbox(-2.2, 0, 2.4, 3.0, 0.4), BRASS, {}),
        (lambda u, v: ellipse(1.6, 0, 3.6, 3.0)(u, v), OLIVE, {}),
        (lbox(0.4, 0, 0.5, 3.05, 0.1), GOLD, {}),
    ]
    parts(ic, cx, cy, ang, s, items, seed)


# ---------------------------------------------------------------- turret
def turret(ic, x, y, s=1.0, body=GUN, accent=OLIVE, seed=0, barrel=STEEL):
    """A tripod sentry gun facing right; (x, y) = top-left of its ~19 x 16 box at s=1."""
    def at(f):
        return lambda X, Y: f((X - x) / s, (Y - y) / s) * s
    for k, (x0, y0, x1, y1) in enumerate(((6, 9, 1.5, 16), (8, 9, 13.5, 16), (7, 9, 7, 16))):
        ic.solid(at(seg(x0, y0, x1, y1, 0.7, 0.6)), STEEL, base=2.2 - (k == 2) * 0.6, seed=seed + k)
    ic.solid(at(box(6.5, 5.6, 4.6, 3.2, 0, 1.0)), body, seed=seed + 4)
    ic.solid(at(box(6.5, 5.6, 2.6, 1.0, 0, 0.3)), accent, base=3.2, seed=seed + 5)
    ic.solid(at(box(14.5, 4.6, 4.2, 0.9, 0, 0.3)), barrel, base=3, seed=seed + 6)
    ic.solid(at(box(18.2, 4.6, 0.7, 1.4, 0, 0.2)), barrel, base=2.2, seed=seed + 7)
    ic.solid(at(box(4, 10.2, 2.4, 0.8, 0, 0.2)), BRASS, base=3.4, seed=seed + 8)


# ---------------------------------------------------------------- misc
def heart(cx, cy, sc):
    def f(x, y):
        X, Y = (x - cx) / sc, -(y - cy) / sc + 0.15
        v = (X * X + Y * Y - 1) ** 3 - X * X * Y ** 3
        return v * sc * 0.9
    return f


def skull(ic, cx, cy, s=1.0, rmp=BONE, eyes=None, seed=0):
    sk = union(ellipse(cx, cy - 1.2 * s, 6.5 * s, 6 * s), box(cx, cy + 4 * s, 3.8 * s, 2.6 * s, 0, 1 * s))
    holes = [ellipse(cx - 2.6 * s, cy - 0.4 * s, 1.9 * s, 2 * s), ellipse(cx + 2.6 * s, cy - 0.4 * s, 1.9 * s, 2 * s),
             poly([(cx, cy + 1.6 * s), (cx - 1 * s, cy + 3.2 * s), (cx + 1 * s, cy + 3.2 * s)])]
    ic.solid(cut(sk, *holes), rmp, seed=seed)
    for k, hf in enumerate(holes):
        if eyes and k < 2:
            ic.energy(hf, eyes, falloff=1.4, seed=seed + k)
        else:
            ic.paint(hf, lambda x, y, d: rmp[0])
    for k in range(-2, 3):
        ic.px([(int(cx + k * 1.4 * s), int(cy + 5 * s))], rmp[1])


def head(ic, cx, cy, s=1.0, rmp=GUN, seed=0):
    """A shooting-range head and shoulders silhouette."""
    f = union(ellipse(cx, cy, 4.2 * s, 5 * s), box(cx, cy + 4.5 * s, 1.8 * s, 2 * s, 0, 0.4),
              ellipse(cx, cy + 11 * s, 10 * s, 4.6 * s))
    ic.solid(f, rmp, seed=seed)
    return f


def soldier(ic, cx, cy, s=1.0, seed=0, arms_up=True):
    """A trooper flung through the air, arms and legs splayed."""
    a = 1 if arms_up else -1
    f = union(circle(cx, cy - 5 * s, 2.2 * s),
              box(cx, cy, 2.2 * s, 3.2 * s, 0, 1 * s),
              seg(cx - 1.8 * s, cy - 2 * s, cx - 5 * s, cy - 2 * s - 3.5 * s * a, 0.9 * s),
              seg(cx + 1.8 * s, cy - 2 * s, cx + 5 * s, cy - 2 * s - 3.5 * s * a, 0.9 * s),
              seg(cx - 1.2 * s, cy + 3 * s, cx - 3.6 * s, cy + 7.5 * s, 1.0 * s),
              seg(cx + 1.2 * s, cy + 3 * s, cx + 3.6 * s, cy + 7.5 * s, 1.0 * s))
    ic.solid(f, OLIVE, seed=seed)
    ic.solid(ellipse(cx, cy - 6 * s, 2.6 * s, 1.6 * s), OLIVE, base=3.4, seed=seed + 1)
    return f


def syringe(ic, cx, cy, ang, s=1.0, liquid=BLOOD, seed=0):
    items = [
        (lbox(-7.6, 0, 0.5, 2.6, 0.2), STEEL, {"base": 3}),
        (lbox(-6.2, 0, 1.6, 0.6, 0.1), STEEL, {"base": 3}),
        (lbox(0, 0, 4.4, 2.1, 0.5), PAPER, {"base": 4, "spread": 1}),
        (lbox(0.3, 0, 3.6, 1.4, 0.4), liquid, {}),
        (lbox(4.8, 0, 0.6, 2.4, 0.2), STEEL, {"base": 3}),
        (lseg(5.2, 0, 10, 0, 0.45, 0.2), STEEL, {"base": 4}),
    ]
    parts(ic, cx, cy, ang, s, items, seed)


def dyn(ic, cx, cy, ang=-90, s=1.0, seed=0, length=12, w=1.8, fuse=True):
    hl = length / 2
    items = [(lbox(0, 0, hl, w, 0.5), RED, {}),
             (lbox(hl - 0.4, 0, 0.5, w + 0.01, 0.2), PAPER, {"base": 3.4})]
    parts(ic, cx, cy, ang, s, items, seed)


def crate(ic, x0, y0, x1, y1, seed=0):
    ic.solid(box((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, 0, 0.5), WOOD, seed=seed)
    for y in (y0 + (y1 - y0) * 0.36, y0 + (y1 - y0) * 0.72):
        ic.solid(box((x0 + x1) / 2, y, (x1 - x0) / 2, 0.5, 0, 0.1), WOOD, base=1.2, spread=0.4, rim=0)
    ic.solid(box((x0 + x1) / 2, y0 + 0.5, (x1 - x0) / 2, 0.6, 0, 0.1), WOOD, base=4, spread=0.6)


def eye(ic, cx, cy, s, iris=GOLD, seed=0, open_=1.0):
    f = lambda x, y: (abs((y - cy) / s) - 4.2 * open_ * max(0, 1 - ((x - cx) / (9 * s)) ** 2)) * s
    ic.solid(f, PAPER, base=4, spread=1, seed=seed, rim=0.4)
    ic.paint(inter(f, circle(cx, cy, 3.6 * s)), lambda x, y, d: None)
    ic.solid(inter(f, circle(cx, cy, 3.6 * s)), iris, seed=seed + 1)
    ic.paint(inter(f, ellipse(cx, cy, 1.2 * s, 2.6 * s)), lambda x, y, d: BLACK)
    ic.px([(int(cx - 1.5 * s), int(cy - 1.5 * s))], WHITE)
