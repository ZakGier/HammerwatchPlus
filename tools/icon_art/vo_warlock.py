"""Warlock orb icons: A the gear up close, B the moment it happens, C an abstract mark."""
from vm import *

BG_V = ("0a0410", "22102e")
BG_F = ("140604", "2e1006")
BG_R = ("140406", "2e0a10")
BG_G = ("08100a", "16261a")
BG_Y = ("100c04", "262008")
DEMON = R("140406", "3a0a12", "6a1620", "a02a2a", "d0503a", "f0906a")


def ga(c=BG_V, light=(12, 12)):
    return G(c[0], c[1], light)


def foe(ic, x, y, s=1.0):
    ic.solid(ellipse(x, y, 2.6 * s, 3.6 * s), SHADOW, base=2.2)


def lash(ic, pts, rmp=DEMON, w=1.5, tip=True):
    for i in range(len(pts) - 1):
        k = i / max(1, len(pts) - 2)
        ic.solid(seg(*pts[i], *pts[i + 1], w * (1.3 - 0.6 * k), w * (1.3 - 0.6 * (i + 1) / max(1, len(pts) - 1))), rmp, base=2.8, seed=i)
    if tip:
        x0, y0 = pts[-2]
        x1, y1 = pts[-1]
        a = math.atan2(y1 - y0, x1 - x0)
        ic.solid(poly([(x1 + math.cos(a) * 3, y1 + math.sin(a) * 3), (x1 + math.cos(a + 2.2) * 2.2, y1 + math.sin(a + 2.2) * 2.2),
                       (x1 + math.cos(a - 2.2) * 2.2, y1 + math.sin(a - 2.2) * 2.2)]), DEMON, base=3.6)


WHIP = [(3, 20), (7, 13), (12, 9), (17, 9), (20, 5)]


def crackling_lash():
    A = ga(BG_Y)
    lash(A, WHIP)
    for x, y in ((9, 10), (15, 6), (19, 12)):
        bolt(A, [(x, y), (x + 2, y + 2), (x + 1, y + 4)], w=0.45)
    B = ga(BG_Y)
    foe(B, 6, 8)
    foe(B, 18, 17)
    lash(B, [(2, 22), (8, 18), (13, 15)], w=0.9)
    bolt(B, [(13, 15), (10, 12), (7, 10)], w=0.6)
    bolt(B, [(13, 15), (16, 15), (18, 16)], w=0.6)
    C = ga(BG_Y)
    C.energy(union(arc(10, 14, 7, 1.1, 180, 340), seg(16.6, 11.6, 20, 18, 1.0)), DEMON, falloff=0.8)
    bolt(C, [(15, 3), (12, 9), (16, 9), (13, 15)], w=0.7)
    return A, B, C


def fiery_lash():
    A = ga(BG_F)
    lash(A, WHIP)
    for x, y in ((7, 13), (12, 9), (17, 9)):
        A.energy(flame(x, y + 1, 1.6, 5, 0, x), FIRE, falloff=1.1)
    B = ga(BG_F, (12, 16))
    lash(B, [(2, 8), (8, 14), (14, 17), (21, 18)], w=0.8)
    for k, x in enumerate((6, 10, 14, 18)):
        B.energy(flame(x, 22, 2, 7 + (k % 2) * 2, 0, k), FIRE, falloff=1.2)
    C = ga(BG_F)
    C.energy(union(arc(10, 14, 7, 1.1, 180, 340), seg(16.6, 11.6, 20, 18, 1.0)), DEMON, falloff=0.8)
    C.energy(flame(10, 15, 2.6, 9, 0, 1), FIRE, falloff=1.2)
    return A, B, C


def heavy_impact():
    A = ga()
    lash(A, [(3, 21), (6, 12), (11, 7)], w=1.1, tip=False)
    A.solid(circle(15, 6, 3.6), STEEL, base=3, seed=4)
    for a in range(0, 360, 60):
        r = math.radians(a)
        A.solid(seg(15, 6, 15 + math.cos(r) * 5, 6 + math.sin(r) * 5, 0.9, 0.2), STEEL, base=3.4)
    B = ga()
    foe(B, 13, 15, 1.4)
    flash(B, 13, 10, 3, DEMON)
    for x in (9, 13, 17):
        B.energy(star(x, 4 + (x == 13) * -1, 0.6, 2, 4), HOLY, falloff=0.8)
    C = ga()
    C.energy(ring(12, 12, 8, 1.4), DEMON, falloff=0.8)
    C.energy(star(12, 12, 1.6, 5, 4), HOLY, falloff=1.2)
    return A, B, C


def rune_circle(ic, cx, cy, r, rmp, sq=0.45):
    ic.energy(union(ellipse(cx, cy, r, r * sq), ), rmp, falloff=1.6)
    ic.paint(ellipse(cx, cy, r - 1.4, (r - 1.4) * sq), lambda x, y, d: None)
    for k in range(5):
        a = math.radians(k * 72 - 90)
        ic.energy(circle(cx + math.cos(a) * (r - 0.5), cy + math.sin(a) * (r - 0.5) * sq, 0.9), rmp, falloff=0.8)


def blood_ritual():
    A = ga(BG_R)
    dagger(A, 12, 11, -100, 1.1, blade=STEEL, hilt=WINE)
    A.energy(drop(15, 19, 2.4), BLOOD, falloff=1.6)
    B = ga(BG_R, (12, 16))
    B.energy(ellipse(12, 17, 10, 4), BLOOD, falloff=2.4)
    foe(B, 12, 12, 1.2)
    for x, y in ((7, 9), (17, 10), (12, 4)):
        B.energy(drop(x, y, 1.6), BLOOD, falloff=1.2)
    C = ga(BG_R)
    C.energy(cut(star(12, 12, 4, 10, 5), circle(12, 12, 2.4)), BLOOD, falloff=1.2)
    C.energy(drop(12, 13, 2.0), BLOOD, falloff=1.4)
    return A, B, C


def conflagration():
    A = ga(BG_F)
    book(A, 12, 14, 1.0, cover=DEMON, open_=True)
    A.energy(flame(12, 11, 3.4, 10, 0, 1), FIRE, falloff=1.4)
    B = ga(BG_F, (12, 16))
    B.energy(ellipse(12, 17, 10.5, 4.2), FIRE, falloff=1.4)
    for k, x in enumerate((4, 8, 12, 16, 20)):
        B.energy(flame(x, 17 + abs(x - 12) * 0.1, 2, 8 + (2 - abs(k - 2)) * 3, 0, k), FIRE, falloff=1.2)
    C = ga(BG_F)
    C.energy(cut(star(12, 12, 4, 10, 5), circle(12, 12, 2.4)), FIRE, falloff=1.2)
    C.energy(flame(12, 16, 2.0, 7, 0, 2), FIRE, falloff=1.2)
    return A, B, C


def leeching_ritual():
    A = ga(BG_R)
    A.solid(box(12, 15, 5.5, 5, 0, 2), BONE, base=2.4)
    A.energy(ellipse(12, 11, 5, 1.6), BLOOD, falloff=1.2)
    A.energy(drop(12, 5, 2.2), BLOOD, falloff=1.4)
    B = ga(BG_R)
    B.solid(ellipse(12, 13, 3.6, 6.5), SPIRIT, base=3)
    for a in (200, 250, 290, 340):
        r = math.radians(a)
        B.streak(12 + math.cos(r) * 11, 13 + math.sin(r) * 11, 12 + math.cos(r) * 6, 13 + math.sin(r) * 6, 0.8, BLOOD)
    B.energy(ellipse(12, 20, 9, 2.4), BLOOD, falloff=1.2)
    C = ga(BG_R)
    C.energy(cut(star(12, 12, 4, 10, 5), circle(12, 12, 2.4)), BLOOD, falloff=1.2)
    C.solid(heart(12, 12, 2.4), CRIMSON, base=3.6)
    return A, B, C


def essence_orb(ic, cx, cy, r, rmp=VOID):
    ic.glow(cx, cy, r * 2.2, rmp[4], 0.5)
    ic.energy(circle(cx, cy, r), rmp, falloff=r * 0.9)


def siphon(ic, x0, y0, x1, y1, rmp):
    for k in range(3):
        t = k / 3
        ic.energy(circle(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + math.sin(t * 6) * 1.5, 1.4 - k * 0.2), rmp, falloff=1.2)


def life_siphon():
    A = ga(BG_R)
    essence_orb(A, 8, 9, 3.6)
    A.solid(heart(15, 15, 6.0), CRIMSON, base=3.4)
    B = ga(BG_R)
    foe(B, 5, 7, 1.0)
    siphon(B, 5, 9, 14, 14, VOID)
    B.solid(heart(16, 15, 5.4), CRIMSON, base=3.4)
    C = ga(BG_R)
    C.energy(cut(heart(12, 13, 7.5), heart(12, 13.5, 4.8)), CRIMSON, falloff=1.2)
    C.energy(circle(12, 12, 2.2), VOID, falloff=2)
    return A, B, C


def energy_siphon():
    A = ga(("04081a", "0e1a3a"))
    essence_orb(A, 8, 9, 3.6)
    potion(A, 15, 14, 0.95, liquid=MANA)
    B = ga(("04081a", "0e1a3a"))
    foe(B, 5, 7, 1.0)
    siphon(B, 5, 9, 14, 14, VOID)
    B.energy(drop(16, 15, 4), MANA, falloff=3)
    C = ga(("04081a", "0e1a3a"))
    C.energy(cut(drop(12, 13.5, 7), drop(12, 13.5, 4.4)), MANA, falloff=1.2)
    C.energy(circle(12, 15, 2), VOID, falloff=2)
    return A, B, C


def drain_blood():
    A = ga(BG_R)
    essence_orb(A, 12, 12, 5, VOID)
    for a in (-60, 60, 180):
        r = math.radians(a)
        A.energy(drop(12 + math.cos(r) * 9, 12 + math.sin(r) * 9, 1.8), BLOOD, falloff=1.2)
    B = ga(BG_R)
    foe(B, 7, 12, 1.4)
    B.streak(9, 12, 21, 12, 1.0, VOID)
    for x, y in ((5, 18), (9, 19)):
        B.energy(drop(x, y, 1.6), BLOOD, falloff=1.2)
    C = ga(BG_R)
    C.energy(drop(12, 13, 7), BLOOD, falloff=3)
    C.energy(circle(12, 15, 2.2), VOID, falloff=2)
    return A, B, C


def essence_harvester():
    A = ga()
    A.solid(seg(5, 21, 16, 4, 0.8), WOOD, base=2.6)
    A.solid(poly([(14, 3), (22, 6), (21, 9), (16, 6.5)]), STEEL, base=3.2)
    essence_orb(A, 7, 9, 3)
    B = ga()
    skull(B, 9, 15, 0.7)
    for k, (x, y) in enumerate(((15, 8), (19, 4), (19, 12))):
        essence_orb(B, x, y, 1.8 - k * 0.2)
    C = ga()
    C.energy(arc(12, 12, 9, 1.6, 200, 360), VOID, falloff=0.9)
    C.energy(seg(12, 22, 12, 4, 0.8), VOID, falloff=0.6)
    C.energy(circle(12, 12, 2.4), VOID, falloff=2)
    return A, B, C


def aura(ic, cx=12, cy=12, r=9, rmp=FEL):
    ic.energy(cut(circle(cx, cy, r), circle(cx, cy, r - 1.4)), rmp, falloff=1.2)
    ic.glow(cx, cy, r, rmp[3], 0.25)


def agony():
    A = ga(BG_G)
    aura(A)
    skull(A, 12, 12, 0.8, eyes=FEL)
    B = ga(BG_G)
    aura(B, rmp=FEL)
    foe(B, 12, 13, 1.3)
    B.energy(cut(shard(12, 13, -60, 12, 1.4), circle(0, 0, 0)), CRIMSON, falloff=1)
    C = ga(BG_G)
    aura(C)
    C.energy(poly([(12, 4), (15, 16), (12, 14), (9, 16)]), CRIMSON, falloff=1)
    return A, B, C


def spreading_corruption():
    A = ga(BG_G)
    sword(A, 12, 12, -45, 1.0, blade=FEL)
    A.energy(drop(19, 19, 2), TOXIC, falloff=1.4)
    B = ga(BG_G)
    foe(B, 6, 15, 1.2)
    foe(B, 18, 8, 1.2)
    slash(B, 6, 15, 6, 200, 320, STEEL)
    B.streak(8, 12, 16, 8, 0.8, TOXIC)
    B.energy(cloud and circle(18, 8, 3.4), TOXIC, falloff=2)
    C = ga(BG_G)
    for k, (x, y) in enumerate(((6, 17), (12, 9), (18, 14))):
        C.energy(circle(x, y, 2.4 - k * 0.3), TOXIC, falloff=2)
    C.energy(union(seg(6, 17, 12, 9, 0.5), seg(12, 9, 18, 14, 0.5)), TOXIC, falloff=0.4)
    return A, B, C


def spontaneous_combustion():
    A = ga(BG_F)
    aura(A, rmp=FEL)
    A.energy(flame(12, 17, 3.6, 12, 0, 3), FIRE, falloff=1.6)
    B = ga(BG_F)
    for x, y in ((5, 8), (18, 7), (12, 17)):
        foe(B, x, y + 1, 0.9)
        B.energy(flame(x, y + 3, 2, 7, 0, x), FIRE, falloff=1.2)
    C = ga(BG_F)
    C.energy(cut(circle(12, 12, 9), circle(12, 12, 7.4)), FEL, falloff=0.8)
    C.energy(cut(star(12, 12, 3, 7, 8), circle(12, 12, 1.4)), FIRE, falloff=1.2)
    return A, B, C


def fiend(ic, cx, cy, s=1.0, rmp=DEMON, seed=0):
    ic.solid(ellipse(cx, cy + 2 * s, 4.4 * s, 4 * s), rmp, base=2.4, seed=seed)
    ic.solid(circle(cx, cy - 3 * s, 3.4 * s), rmp, base=3.0, seed=seed + 1)
    for d in (-1, 1):
        ic.solid(poly([(cx + d * 1.8 * s, cy - 5.4 * s), (cx + d * 4.6 * s, cy - 9.4 * s), (cx + d * 3.4 * s, cy - 4.2 * s)]), BONE, base=3.4)
    ic.px([(int(cx - 1.4 * s), int(cy - 3 * s)), (int(cx + 1.4 * s), int(cy - 3 * s))], (255, 220, 80, 255))


def infernal_fiends():
    A = ga(BG_F)
    fiend(A, 12, 13, 1.2)
    A.energy(flame(19, 21, 2.4, 8, 0, 1), FIRE, falloff=1.2)
    B = ga(BG_F)
    fiend(B, 7, 14, 0.9)
    fireball(B, 17, 9, 3.4, ang=-30)
    C = ga(BG_F)
    C.energy(union(poly([(6, 12), (4, 3), (10, 9)]), poly([(18, 12), (20, 3), (14, 9)])), DEMON, falloff=1)
    C.energy(flame(12, 21, 4, 13, 0, 2), FIRE, falloff=1.6)
    return A, B, C


def explosive_demise():
    A = ga(BG_F)
    fiend(A, 12, 13, 1.1)
    bomb(A, 18, 18, 3, fuse=True)
    B = ga(BG_F)
    flash(B, 12, 13, 6, FIRE)
    for k in range(6):
        a = math.radians(k * 60 + 20)
        B.solid(circle(12 + math.cos(a) * 9, 13 + math.sin(a) * 9, 1.2), DEMON, base=3)
    C = ga(BG_F)
    C.energy(union(poly([(6, 12), (4, 3), (10, 9)]), poly([(18, 12), (20, 3), (14, 9)])), DEMON, falloff=1)
    C.energy(cut(star(12, 16, 3, 7.5, 8), circle(12, 16, 1.4)), FIRE, falloff=1.2)
    return A, B, C


GARG = R("0e0e14", "22222c", "383844", "56566a", "80808f", "b0b0bc")


def claw(ic, cx, cy, s=1.0, rmp=GARG):
    for k in range(3):
        a = math.radians(-120 + k * 30)
        ic.solid(seg(cx, cy, cx + math.cos(a) * 9 * s, cy + math.sin(a) * 9 * s, 1.6 * s, 0.3), rmp, base=3.2, seed=k)
    ic.solid(circle(cx, cy + 2 * s, 4 * s), rmp, base=2.4)


def flaming_strikes():
    A = ga(BG_F)
    claw(A, 12, 17, 1.1)
    for k in range(3):
        a = math.radians(-120 + k * 30)
        A.energy(flame(12 + math.cos(a) * 9, 17 + math.sin(a) * 9 + 1, 1.4, 4, 0, k), FIRE, falloff=1)
    B = ga(BG_F)
    for k in range(3):
        B.streak(5 + k * 5, 3, 9 + k * 5, 21, 1.1, FIRE)
    C = ga(BG_F)
    C.energy(union(*[seg(6 + k * 5, 4, 9 + k * 5, 20, 1.1, 0.4) for k in range(3)]), FIRE, falloff=0.9)
    return A, B, C


def lightning_trident():
    A = ga(BG_Y)
    A.solid(seg(4, 21, 15, 9, 0.8), GARG, base=2.6)
    for d in (-1, 0, 1):
        a = math.radians(-48 + d * 22)
        A.solid(seg(15, 9, 15 + math.cos(a) * 7, 9 + math.sin(a) * 7, 0.8, 0.3), STEEL, base=3.4)
    bolt(A, [(19, 3), (21, 6), (19, 9), (22, 12)], w=0.5)
    B = ga(BG_Y)
    foe(B, 7, 15)
    foe(B, 18, 16)
    bolt(B, [(12, 2), (10, 8), (8, 12)], w=0.7)
    bolt(B, [(12, 2), (15, 9), (18, 13)], w=0.7)
    C = ga(BG_Y)
    C.energy(union(seg(12, 22, 12, 7, 0.9), arc(12, 9, 6, 0.9, 0, 180), seg(6, 9, 6, 3, 0.8), seg(18, 9, 18, 3, 0.8), seg(12, 9, 12, 2, 0.8)), VOLT, falloff=0.8)
    return A, B, C


def vortex(ic, cx, cy, r, rmp=VOID):
    for k in range(3):
        ic.energy(arc(cx, cy, r - k * 2.6, 1.3 - k * 0.2, k * 120, k * 120 + 200), rmp, falloff=0.8)
    ic.energy(circle(cx, cy, 1.8), rmp, falloff=1.6)


def lightning_vortex():
    A = ga(BG_Y)
    vortex(A, 12, 12, 9)
    for x, y in ((4, 4), (20, 6), (19, 20)):
        bolt(A, [(x, y - 3), (x + 1, y), (x - 1, y + 2), (x, y + 4)], w=0.5)
    B = ga(BG_Y, (12, 16))
    for x, h in ((5, 12), (12, 18), (19, 10)):
        bolt(B, [(x + 1, 22 - h), (x - 1, 22 - h * 0.6), (x + 1, 22 - h * 0.3), (x, 22)], w=0.7)
        B.energy(ellipse(x, 22, 2.6, 0.9), VOLT, falloff=0.8)
    C = ga(BG_Y)
    vortex(C, 12, 12, 9, VOLT)
    return A, B, C


def vortex_shroud():
    A = ga()
    vortex(A, 12, 12, 9)
    A.solid(ellipse(12, 13, 3, 5.5), SHADOW, base=2.2)
    B = ga()
    vortex(B, 15, 12, 7)
    for k in range(2):
        B.solid(ellipse(5 + k * 4, 13, 2.6, 6), SHADOW, base=1.0 + k * 0.9, seed=k)
    C = ga()
    for k in range(3):
        C.energy(ellipse(8 + k * 4, 12, 2.4 - k * 0.3, 7 - k), VOID[:5 + k], falloff=1.4)
    return A, B, C


SOUL = R("06100e", "0e2a26", "1a4a44", "2a7a6e", "50b8a4", "a8f0e0", "ffffff")


def soul_cleave():
    A = ga(("04100e", "0c2422"))
    wisp(A, 12, 13, 5.5, SOUL, ang=-45)
    A.energy(star(17, 7, 1, 3.4, 4), FIRE, falloff=1)
    B = ga(("04100e", "0c2422"))
    foe(B, 14, 13, 1.4)
    flash(B, 14, 12, 5, SOUL)
    C = ga(("04100e", "0c2422"))
    C.energy(cut(star(12, 12, 4, 10, 6), circle(12, 12, 2.6)), SOUL, falloff=1.2)
    return A, B, C


def relentless_souls():
    A = ga(("04100e", "0c2422"))
    for k, (x, y) in enumerate(((7, 17), (16, 8))):
        wisp(A, x, y, 3.6, SOUL, ang=-45, seed=k)
    B = ga(("04100e", "0c2422"))
    for x, y in ((5, 17), (12, 7), (19, 16)):
        foe(B, x, y + 1)
    for (x0, y0), (x1, y1) in (((5, 15), (12, 5)), ((12, 5), (19, 14))):
        B.streak(x0, y0, x1, y1, 0.8, SOUL)
    C = ga(("04100e", "0c2422"))
    C.energy(union(seg(3, 19, 8, 6, 1.0), seg(8, 6, 13, 19, 1.0), seg(13, 19, 18, 6, 1.0)), SOUL, falloff=0.8)
    C.energy(circle(19, 5, 2), SOUL, falloff=1.6)
    return A, B, C


CHAOS = R("10040a", "300a20", "5a1240", "8a1e5a", "c03a7a", "f080b0", "ffffff")


def blade_arcs():
    A = ga(BG_R)
    sword(A, 9, 15, -45, 0.9, blade=CHAOS)
    for a in (-80, -50, -20):
        r = math.radians(a)
        A.energy(arc(9, 15, 12, 0.9, a - 10, a + 10), CHAOS, falloff=0.6)
    B = ga(BG_R)
    slash(B, 6, 12, 7, 290, 430, CHAOS)
    for a in (-30, 0, 30):
        r = math.radians(a)
        B.energy(arc(6 + math.cos(r) * 12, 12 + math.sin(r) * 12, 3, 0.9, a - 70, a + 70), CHAOS, falloff=0.6)
    C = ga(BG_R)
    for r in (5, 9, 13):
        C.energy(arc(3, 12, r, 1.1, -45, 45), CHAOS, falloff=0.7)
    return A, B, C


def rupture():
    A = ga(BG_R)
    sword(A, 12, 12, -45, 1.0, blade=CHAOS)
    A.energy(drop(18, 18, 2.2), BLOOD, falloff=1.4)
    B = ga(BG_R)
    foe(B, 12, 12, 1.4)
    slash(B, 12, 12, 7, 200, 330, CHAOS)
    for x, y in ((6, 18), (12, 20), (18, 18)):
        B.energy(drop(x, y, 1.5), BLOOD, falloff=1.2)
    C = ga(BG_R)
    C.energy(seg(4, 20, 20, 4, 1.4, 0.4), CHAOS, falloff=1)
    for x, y in ((8, 9), (15, 17)):
        C.energy(drop(x, y, 2), BLOOD, falloff=1.4)
    return A, B, C


def rift(ic, cx, cy, s=1.0, rmp=CHAOS):
    ic.glow(cx, cy, 9 * s, rmp[3], 0.5)
    ic.energy(poly([(cx, cy - 9 * s), (cx + 3 * s, cy - 2 * s), (cx + 1 * s, cy + 3 * s), (cx, cy + 9 * s), (cx - 2.6 * s, cy + 1 * s), (cx - 1 * s, cy - 4 * s)]), rmp, falloff=2 * s)


def chaos_reaper():
    A = ga(BG_R)
    rift(A, 15, 11, 0.9)
    skull(A, 7, 16, 0.6)
    B = ga(BG_R)
    rift(B, 12, 12, 1.1)
    for k in range(4):
        a = math.radians(k * 90 + 45)
        B.solid(circle(12 + math.cos(a) * 9, 12 + math.sin(a) * 9, 1.0), SHADOW, base=2)
    C = ga(BG_R)
    C.energy(arc(12, 12, 9, 1.6, 200, 360), CHAOS, falloff=0.9)
    C.energy(seg(12, 22, 12, 4, 0.8), CHAOS, falloff=0.6)
    rift(C, 12, 13, 0.5)
    return A, B, C


def rift_blade():
    A = ga(BG_R)
    sword(A, 10, 14, -45, 0.9, blade=CHAOS)
    rift(A, 18, 7, 0.55)
    B = ga(BG_R)
    slash(B, 9, 13, 7, 200, 330, CHAOS)
    rift(B, 17, 12, 0.8)
    C = ga(BG_R)
    rift(C, 12, 12, 1.0)
    C.energy(seg(3, 20, 21, 4, 0.6), STEEL, falloff=0.5)
    return A, B, C


ORBS = {
    "demons_tail_lightning": crackling_lash, "demons_tail_fire": fiery_lash, "war_demons_tail_stun": heavy_impact,
    "dark_ritual_blood": blood_ritual, "dark_ritual_fire": conflagration, "dark_ritual_leech": leeching_ritual,
    "drain_essence_life": life_siphon, "drain_essence_mana": energy_siphon, "drain_essence_blood": drain_blood,
    "drain_essence_harvester": essence_harvester,
    "aura_vulnerability": agony, "aura_poison": spreading_corruption, "aura_fire": spontaneous_combustion,
    "summon_fiends_infernal": infernal_fiends, "summon_fiends_explosive": explosive_demise,
    "summon_gargoyle_fire": flaming_strikes, "summon_gargoyle_lightning": lightning_trident,
    "soul_vortex_lightning": lightning_vortex, "soul_vortex_evasion": vortex_shroud,
    "soul_shaper_cleave": soul_cleave, "soul_shaper_jumps": relentless_souls,
    "chaos_blade_arcs": blade_arcs, "chaos_blade_bleeding": rupture,
    "chaos_rift_kill": chaos_reaper, "chaos_rift_blade": rift_blade,
}


# second pass
def scythe_mark(ic, rmp):
    ic.energy(seg(15, 22, 9, 3, 0.9), rmp, falloff=0.6)
    ic.energy(cut(circle(17, 7, 9), circle(19, 10, 8.4), lambda x, y: x - 10.5, lambda x, y: y - 9), rmp, falloff=1.0)


_lr, _eh, _cr, _sc, _db, _lv, _vs = (ORBS[k] for k in ("dark_ritual_leech", "drain_essence_harvester", "chaos_rift_kill",
                                                      "aura_poison", "drain_essence_blood", "soul_vortex_lightning", "soul_vortex_evasion"))


def leeching_ritual():
    A, B, C = _lr()
    A = ga(BG_R)
    A.solid(poly([(5, 5), (19, 5), (16, 12), (13, 13), (13, 18), (17, 20), (17, 21), (7, 21), (7, 20), (11, 18), (11, 13), (8, 12)]), BRASS, base=2.8)
    A.energy(ellipse(12, 6.4, 6.2, 1.2), BLOOD, falloff=1)
    A.glint(8, 8)
    return A, B, C


def essence_harvester():
    A, B, C = _eh()
    C = ga()
    scythe_mark(C, VOID)
    C.energy(circle(7, 17, 2.4), VOID, falloff=2)
    return A, B, C


def chaos_reaper():
    A, B, C = _cr()
    C = ga(BG_R)
    scythe_mark(C, CHAOS)
    return A, B, C


def spreading_corruption():
    A, B, C = _sc()
    B = ga(BG_G)
    foe(B, 6, 15, 1.2)
    foe(B, 18, 8, 1.2)
    B.streak(8, 13, 16, 9, 0.9, TOXIC)
    B.energy(circle(18, 8, 4), TOXIC, falloff=3)
    return A, B, C


def drain_blood():
    A, B, C = _db()
    B = ga(BG_R)
    foe(B, 7, 12, 1.4)
    for k in range(4):
        x = 11 + k * 3
        B.energy(drop(x, 12 + math.sin(k * 1.6) * 2, 1.4 + k * 0.15), BLOOD, falloff=1.2)
    essence_orb(B, 21, 12, 2.2)
    return A, B, C


def vortex(ic, cx, cy, r, rmp=VOID):
    for k in range(3):
        ic.energy(arc(cx, cy, r - k * 2.6, 2.0 - k * 0.3, k * 120, k * 120 + 220), rmp, falloff=1.1)
    ic.energy(circle(cx, cy, 2.4), rmp, falloff=2)


ORBS.update({"dark_ritual_leech": leeching_ritual, "drain_essence_harvester": essence_harvester, "chaos_rift_kill": chaos_reaper,
             "aura_poison": spreading_corruption, "drain_essence_blood": drain_blood})


def scythe_mark(ic, rmp):
    ic.energy(seg(15, 22, 9, 3, 1.0), rmp, falloff=0.7)
    ic.energy(poly([(8, 2), (14, 1), (19, 2.6), (22.5, 7.5), (18, 5.2), (13, 4.4), (9, 5)]), rmp, falloff=1.2)
