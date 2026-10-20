"""Priest orb icons: A the gear up close, B the moment it happens, C an abstract mark."""
from vm import *

BG_H = ("120c04", "2c2008")
BG_F = ("140604", "2e1006")
BG_L = ("041004", "0e2a10")
BG_M = ("04081a", "0e1a3a")
BG_R = ("140406", "2e0a10")


def ga(c=BG_H, light=(12, 12)):
    return G(c[0], c[1], light)


def foe(ic, x, y, s=1.0):
    ic.solid(ellipse(x, y, 2.6 * s, 3.6 * s), SHADOW, base=2.2)


def nova(ic, cx, cy, r, rmp=HOLY):
    ic.energy(cut(circle(cx, cy, r), circle(cx, cy, r - 1.8)), rmp, falloff=1.2)
    ic.glow(cx, cy, r, rmp[3], 0.35)


def encompassing_light():
    A = ga()
    sun(A, 12, 12, 4.4)
    B = ga()
    nova(B, 12, 12, 10.5)
    nova(B, 12, 12, 6)
    B.energy(circle(12, 12, 2), HOLY, falloff=1.6)
    C = ga()
    C.energy(circle(12, 12, 3), HOLY, falloff=2.4)
    for a in (45, 135, 225, 315):
        r = math.radians(a)
        C.energy(poly([(12 + math.cos(r) * 10.5, 12 + math.sin(r) * 10.5), (12 + math.cos(r - 0.45) * 6.5, 12 + math.sin(r - 0.45) * 6.5), (12 + math.cos(r + 0.45) * 6.5, 12 + math.sin(r + 0.45) * 6.5)]), HOLY, falloff=0.9)
    return A, B, C


def light_orb(ic, x, y, r=2.6):
    ic.glow(x, y, r * 2.4, HOLY[4], 0.5)
    ic.energy(circle(x, y, r), HOLY, falloff=r)


def celestial_light():
    A = ga()
    light_orb(A, 12, 11, 5)
    for a in (30, 150, 270):
        r = math.radians(a)
        A.energy(star(12 + math.cos(r) * 9, 11 + math.sin(r) * 9, 0.6, 2.2, 4), HOLY, falloff=0.9)
    B = ga()
    light_orb(B, 6, 6, 3)
    foe(B, 17, 16, 1.3)
    B.streak(7, 7, 17, 15, 1.0, HOLY)
    C = ga()
    for k in range(3):
        a = math.radians(k * 120 - 90)
        C.energy(circle(12 + math.cos(a) * 6.5, 12 + math.sin(a) * 6.5, 2.6), HOLY, falloff=2)
    C.energy(circle(12, 12, 1.6), HOLY, falloff=1.2)
    return A, B, C


def shattering_light():
    A = ga()
    sun(A, 12, 12, 4)
    A.energy(poly([(16, 14), (19, 22), (17, 21), (15, 22)]), CRIMSON, falloff=0.8)
    B = ga()
    foe(B, 12, 13, 1.5)
    nova(B, 12, 13, 9)
    B.energy(poly([(10, 11), (14, 11), (12, 17)]), CRIMSON, falloff=0.8)
    C = ga()
    C.energy(cut(star(12, 12, 3, 10, 8), union(seg(4, 4, 20, 20, 0.6), seg(4, 20, 20, 4, 0.6))), HOLY, falloff=1.2)
    return A, B, C


def prayer_circle(ic, cx, cy, r, rmp=HOLY):
    ic.energy(cut(ellipse(cx, cy, r, r * 0.5), ellipse(cx, cy, r - 1.4, (r - 1.4) * 0.5)), rmp, falloff=1)
    ic.glow(cx, cy, r, rmp[3], 0.3)


def encompassing_prayer():
    A = ga(light=(12, 16))
    book(A, 12, 10, 0.95, cover=GOLD, open_=True)
    prayer_circle(A, 12, 19, 9)
    B = ga(light=(12, 16))
    prayer_circle(B, 12, 15, 11)
    prayer_circle(B, 12, 15, 6)
    C = ga()
    C.energy(holy_cross(12, 12, 1.1), HOLY, falloff=1)
    for d in (-1, 1):
        C.energy(poly([(12 + d * 9, 12), (12 + d * 6, 9), (12 + d * 6, 15)]), HOLY, falloff=0.8)
    return A, B, C


def cleansing_prayer():
    A = ga(("0a0c12", "1c2230"), (12, 16))
    potion(A, 12, 10, 0.9, liquid=SPIRIT)
    prayer_circle(A, 12, 19, 9, SPIRIT)
    B = ga(("0a0c12", "1c2230"), (12, 16))
    prayer_circle(B, 12, 18, 10, HOLY)
    B.solid(ellipse(12, 12, 3.2, 6), SHADOW, base=2.4)
    for x in (6, 18):
        B.energy(circle(x, 6, 1.4), GAS, falloff=1)
        B.streak(x, 8, x, 4, 0.4, GAS)
    C = ga(("0a0c12", "1c2230"))
    C.energy(drop(12, 13, 7), SPIRIT, falloff=3)
    C.energy(holy_cross(12, 14, 0.5), PAPER, falloff=0.7)
    return A, B, C


def restoration_prayer():
    A = ga(BG_L, (12, 16))
    A.solid(heart(12, 10, 5.0), CRIMSON, base=3.4)
    prayer_circle(A, 12, 19, 9, LIFE)
    B = ga(BG_L, (12, 16))
    prayer_circle(B, 12, 18, 10, HOLY)
    for x in (7, 17):
        B.solid(ellipse(x, 12, 2.6, 5), SPIRIT, base=3)
        B.energy(poly([(x - 1.6, 5), (x, 3), (x + 1.6, 5)]), LIFE, falloff=0.7)
    C = ga(BG_L)
    C.energy(cut(heart(12, 13, 7.5), heart(12, 13.5, 4.8)), LIFE, falloff=1.2)
    C.energy(holy_cross(12, 13, 0.45), HOLY, falloff=0.6)
    return A, B, C


def divine_sustain():
    A = ga(BG_M)
    potion(A, 12, 13, 1.2, liquid=MANA)
    A.energy(holy_cross(19, 6, 0.4), HOLY, falloff=0.6)
    B = ga(BG_M)
    B.energy(drop(12, 13, 7), SMOKE, falloff=2)
    B.energy(inter(drop(12, 13, 7), box(12, 17, 10, 4)), MANA, falloff=2)
    B.rays(12, 3, HOLY, n=5, lo=1, hi=3)
    C = ga(BG_M)
    C.energy(cut(drop(12, 13.5, 7), drop(12, 13.5, 4.4)), MANA, falloff=1.2)
    C.energy(poly([(9, 15), (12, 11), (15, 15)]), MANA, falloff=0.8)
    return A, B, C


def extended_protection():
    A = ga()
    shield(A, 12, 11, 1.1, GOLD, face=SPIRIT, boss=None)
    A.energy(ring(12, 12, 10.6, 0.6), HOLY, falloff=0.4)
    B = ga()
    B.energy(cut(circle(12, 13, 10), circle(12, 13, 8.6)), HOLY, falloff=1)
    for x in (7, 12, 17):
        B.solid(ellipse(x, 14, 2.2, 4.4), SPIRIT if x == 12 else SHADOW, base=2.6)
    C = ga()
    for r in (4, 7, 10):
        C.energy(arc(12, 14, r, 1.2, 200, 340), HOLY, falloff=0.7)
    return A, B, C


def divine_intervention():
    A = ga()
    hand_open(A, 12, 8, 1.0)
    A.solid(heart(12, 18, 3.6), CRIMSON, base=3.4)
    B = ga()
    B.rays(12, 1, HOLY, n=7, lo=1.5, hi=4)
    B.solid(ellipse(12, 16, 3.2, 6), SPIRIT, base=2.6)
    B.energy(holy_cross(12, 15, 0.5), HOLY, falloff=0.6)
    C = ga()
    C.energy(cut(heart(12, 13, 7.5), heart(12, 13.5, 4.8)), CRIMSON, falloff=1.2)
    C.energy(seg(12, 0, 12, 12, 1.4, 0.4), HOLY, falloff=1)
    return A, B, C


def holy_flames():
    A = ga(BG_F)
    A.solid(poly([(8, 22), (16, 22), (15, 17), (9, 17)]), GOLD, base=2.6)
    A.energy(flame(12, 17, 4, 14, 0, 1), HOLY, falloff=1.8)
    B = ga(BG_F)
    B.solid(ellipse(12, 13, 3.4, 6.5), GOLD, base=2.6)
    B.energy(cut(circle(12, 13, 9.5), circle(12, 13, 7.6)), FIRE, falloff=1)
    for a in (210, 330):
        r = math.radians(a)
        B.energy(flame(12 + math.cos(r) * 9, 13 + math.sin(r) * 9 + 2, 2, 6, 0, a), FIRE, falloff=1.2)
    C = ga(BG_F)
    C.energy(cut(circle(12, 12, 9), circle(12, 12, 7.4)), FIRE, falloff=0.8)
    C.energy(holy_cross(12, 13, 0.9), HOLY, falloff=1)
    return A, B, C


def restoring_favor():
    A = ga(BG_M)
    for k in range(3):
        A.energy(holy_cross(6 + k * 6, 13 + (k == 1) * -3, 0.55), HOLY, falloff=0.7)
    A.energy(drop(12, 20, 2.4), MANA, falloff=1.6)
    B = ga(BG_M)
    B.solid(ellipse(12, 13, 3.4, 6.5), GOLD, base=2.6)
    for x, y in ((5, 6), (19, 7), (5, 18), (19, 18)):
        B.energy(drop(x, y, 1.6), MANA, falloff=1.2)
    C = ga(BG_M)
    C.energy(holy_cross(12, 11, 1.1), MANA, falloff=1)
    C.energy(poly([(6, 21), (12, 17), (18, 21)]), HOLY, falloff=0.7)
    return A, B, C


def fanaticism():
    A = ga(BG_R)
    A.solid(box(12, 15, 6, 6, 0, 1), PAPER, base=2.6)
    A.solid(box(12, 15, 6, 6, 0, 1), WINE, base=1.6, seed=5) if False else None
    book(A, 12, 13, 1.1, cover=WINE)
    A.energy(holy_cross(12, 12, 0.6), HOLY, falloff=0.8)
    B = ga(BG_R)
    B.energy(drop(8, 13, 5), SMOKE, falloff=2)
    B.energy(inter(drop(8, 13, 5), box(8, 17, 6, 3)), MANA, falloff=2)
    B.energy(cut(star(17, 11, 2.4, 6, 8), circle(0, 0, 0)), CRIMSON, falloff=1.2)
    C = ga(BG_R)
    C.energy(holy_cross(12, 12, 1.3), CRIMSON, falloff=1.2)
    C.energy(drop(12, 13, 1.8), MANA, falloff=1.2)
    return A, B, C


def divine_blast():
    A = ga(BG_F, (12, 16))
    prayer_circle(A, 12, 19, 10)
    A.energy(seg(12, 0, 12, 19, 2.6, 2.0), FIRE, falloff=1.6)
    B = ga(BG_F, (12, 16))
    prayer_circle(B, 12, 18, 10)
    foe(B, 12, 15, 1.2)
    B.streak(0, 6, 12, 14, 1.4, HOLY)
    B.energy(flame(12, 19, 3, 10, 0, 1), FIRE, falloff=1.2)
    C = ga(BG_F)
    C.energy(box(12, 12, 2.6, 10, 0, 1), HOLY, falloff=1.4)
    C.energy(ring(12, 17, 6, 1.0), FIRE, falloff=0.6)
    return A, B, C


def massive_blast():
    A = ga()
    A.energy(seg(2, 12, 22, 12, 3.8, 3.8), HOLY, falloff=2.4)
    B = ga()
    for x in (8, 14, 20):
        foe(B, x, 12 + (x % 3), 0.9)
    B.streak(0, 12, 24, 12, 2.0, HOLY)
    C = ga()
    C.energy(union(seg(3, 12, 17, 12, 1.4), poly([(15, 6), (23, 12), (15, 18)]), seg(3, 6, 3, 18, 1.0)), HOLY, falloff=1)
    return A, B, C


def plentiful_orbs():
    A = ga()
    for k, (x, y, r) in enumerate(((7, 7, 3), (17, 8, 3.6), (11, 17, 4))):
        light_orb(A, x, y, r)
    B = ga()
    B.streak(0, 18, 18, 9, 1.4, HOLY)
    for x, y in ((14, 4), (20, 15), (9, 7)):
        light_orb(B, x, y, 2)
    C = ga()
    for x in (6, 12, 18):
        for y in (8, 16):
            C.energy(circle(x, y, 2), HOLY, falloff=1.6)
    return A, B, C


def destructive_orbs():
    A = ga(BG_F)
    light_orb(A, 12, 12, 5.5)
    A.energy(cut(star(12, 12, 4, 10, 8), circle(12, 12, 6)), FIRE, falloff=1)
    B = ga(BG_F)
    light_orb(B, 5, 5, 2.4)
    B.streak(6, 6, 13, 13, 0.8, HOLY)
    flash(B, 15, 15, 5, FIRE)
    C = ga(BG_F)
    C.energy(circle(12, 12, 3), HOLY, falloff=2.4)
    C.energy(cut(star(12, 12, 5, 10.5, 8), circle(12, 12, 4.6)), FIRE, falloff=1.2)
    return A, B, C


def banner(ic, cx, cy, s=1.0, cloth=CRIMSON, sigil=HOLY):
    ic.solid(seg(cx - 5 * s, cy - 9 * s, cx - 5 * s, cy + 10 * s, 0.8 * s), WOOD, base=2.6)
    ic.solid(seg(cx - 6 * s, cy - 8 * s, cx + 6 * s, cy - 8 * s, 0.6 * s), WOOD, base=2.8)
    ic.solid(poly([(cx - 4 * s, cy - 7.4 * s), (cx + 5.4 * s, cy - 7.4 * s), (cx + 5.4 * s, cy + 5 * s), (cx + 0.7 * s, cy + 2.6 * s), (cx - 4 * s, cy + 5 * s)]), cloth, base=2.8)
    if sigil:
        ic.energy(holy_cross(cx + 0.7 * s, cy - 1.2 * s, 0.45 * s), sigil, falloff=0.6)


def invigorating_banner():
    A = ga()
    banner(A, 12, 12, 1.0)
    for k in range(2):
        A.energy(poly([(16, 21 - k * 4), (19, 18 - k * 4), (22, 21 - k * 4), (22, 22 - k * 4), (19, 19 - k * 4), (16, 22 - k * 4)]), HOLY, falloff=0.6)
    B = ga()
    banner(B, 8, 11, 0.7)
    for k in range(3):
        sword(B, 16, 4 + k * 7, 0, 0.45)
    C = ga()
    C.energy(poly([(5, 3), (19, 3), (19, 21), (12, 16), (5, 21)]), CRIMSON, falloff=1.4)
    for k in range(2):
        C.energy(poly([(8, 13 - k * 5), (12, 9 - k * 5), (16, 13 - k * 5), (16, 15 - k * 5), (12, 11 - k * 5), (8, 15 - k * 5)]), HOLY, falloff=0.7)
    return A, B, C


def war_banner():
    A = ga()
    banner(A, 12, 12, 1.0, cloth=CRIMSON, sigil=None)
    crosshair(A, 13, 9, 3.2, HOLY, w=0.6)
    B = ga()
    banner(B, 6, 12, 0.7)
    for x, y in ((15, 8), (19, 17)):
        foe(B, x, y)
        crosshair(B, x, y, 3.4, CRIMSON, w=0.5)
    C = ga()
    C.energy(poly([(5, 3), (19, 3), (19, 21), (12, 16), (5, 21)]), CRIMSON, falloff=1.4)
    crosshair(C, 12, 10, 3.6, HOLY, w=0.6)
    return A, B, C


def crossbow(ic, cx, cy, ang=0, s=1.0, seed=0):
    r = math.radians(ang)
    ux, uy = math.cos(r), math.sin(r)
    vx, vy = -uy, ux
    ic.solid(seg(cx - ux * 8 * s, cy - uy * 8 * s, cx + ux * 6 * s, cy + uy * 6 * s, 1.2 * s), WOOD, base=2.6, seed=seed)
    ic.solid(arc(cx + ux * 3 * s, cy + uy * 3 * s, 7 * s, 0.9 * s, ang + 110, ang + 250) if False else
             union(seg(cx + ux * 4 * s, cy + uy * 4 * s, cx + ux * 1 * s + vx * 7 * s, cy + uy * 1 * s + vy * 7 * s, 0.9 * s),
                   seg(cx + ux * 4 * s, cy + uy * 4 * s, cx + ux * 1 * s - vx * 7 * s, cy + uy * 1 * s - vy * 7 * s, 0.9 * s)), STEEL, base=3, seed=seed + 1)
    ic.solid(union(seg(cx + ux * 1 * s + vx * 7 * s, cy + uy * 1 * s + vy * 7 * s, cx - ux * 2 * s, cy - uy * 2 * s, 0.3),
                   seg(cx + ux * 1 * s - vx * 7 * s, cy + uy * 1 * s - vy * 7 * s, cx - ux * 2 * s, cy - uy * 2 * s, 0.3)), BONE, flat=3.4, noise=0.2)


def call_crossbowmen():
    A = ga()
    crossbow(A, 12, 12, -45, 1.1)
    B = ga()
    for k, (x, y) in enumerate(((6, 8), (6, 17))):
        B.solid(ellipse(x, y, 2.6, 3.6), GOLD, base=2.6, seed=k)
        B.streak(x + 3, y, x + 15, y - 2 + k * 2, 0.7, STEEL)
    foe(B, 20, 12)
    C = ga()
    for k in range(3):
        C.energy(union(seg(4 + k * 5, 18, 10 + k * 5, 6, 0.6), poly([(9 + k * 5, 5), (12 + k * 5, 4), (11 + k * 5, 8)])), HOLY, falloff=0.6)
    return A, B, C


def endless_crusaders():
    A = ga()
    A.solid(box(12, 13, 5.5, 7, 0, 2.6), STEEL, base=2.6)
    A.solid(box(12, 11, 4, 0.8), SHADOW, base=1)
    A.solid(box(12, 13, 0.6, 4), SHADOW, base=1)
    A.solid(box(12, 5, 1.2, 2.4, 0, 0.4), CRIMSON, base=3)
    B = ga()
    B.solid(ellipse(8, 14, 3, 6), SMOKE, base=1.6)
    B.energy(arc(12, 12, 9, 1.4, 120, 360), HOLY, falloff=0.8)
    B.solid(ellipse(16, 14, 3, 6), GOLD, base=2.8)
    C = ga()
    C.energy(arc(12, 12, 9, 1.6, 90, 400), HOLY, falloff=0.8)
    C.energy(poly([(9, 21), (14, 18), (14, 24)]), HOLY, falloff=0.8)
    C.energy(holy_cross(12, 12, 0.7), HOLY, falloff=0.9)
    return A, B, C


def jagged_flail():
    A = ga(BG_R)
    chain(A, 3, 21, 11, 11)
    flail_head(A, 15, 8, 4.4)
    A.energy(drop(19, 17, 2.2), BLOOD, falloff=1.4)
    B = ga(BG_R)
    B.solid(ellipse(12, 13, 3.4, 6.5), SKIN, base=2.6)
    for k in range(3):
        B.paint(seg(9, 9 + k * 3, 15, 11 + k * 3, 0.4), lambda x, y, d: BLOOD[3])
    for x, y in ((5, 18), (19, 17)):
        B.energy(drop(x, y, 1.6), BLOOD, falloff=1.2)
    C = ga(BG_R)
    C.energy(cut(star(12, 12, 5, 10, 8), circle(12, 12, 3)), STEEL, falloff=1.2)
    C.energy(drop(12, 13, 2.4), BLOOD, falloff=1.4)
    return A, B, C


def ecstasy():
    A = ga(("10040a", "2a0818"))
    flail_head(A, 12, 12, 5.5)
    for a in (-90, 30, 150):
        r = math.radians(a)
        A.energy(heart(12 + math.cos(r) * 9.5, 12 + math.sin(r) * 9.5, 1.6), WINE, falloff=1)
    B = ga(("10040a", "2a0818"))
    B.solid(ellipse(12, 13, 3.4, 6.5), SKIN, base=2.6)
    for k in range(8):
        a = math.radians(k * 45)
        B.solid(seg(12 + math.cos(a) * 7, 13 + math.sin(a) * 7, 12 + math.cos(a) * 10.5, 13 + math.sin(a) * 10.5, 0.9, 0.2), STEEL, base=3.4)
    C = ga(("10040a", "2a0818"))
    C.energy(cut(star(12, 12, 5, 10, 12), circle(12, 12, 4)), WINE, falloff=1.2)
    C.energy(circle(12, 12, 2), WINE, falloff=1.6)
    return A, B, C


def masochism():
    A = ga(BG_R)
    A.solid(heart(12, 12, 6.2), CRIMSON, base=3.4)
    for x, y, a in ((5, 6, 30), (19, 7, 150)):
        A.solid(shard(x, y, a, 7, 1.4), STEEL, base=3.4)
    B = ga(BG_R)
    B.solid(ellipse(12, 13, 3.4, 6.5), SKIN, base=2.6)
    flash(B, 9, 10, 2.4, CRIMSON)
    B.energy(poly([(16, 6), (19, 2), (22, 6)]), LIFE, falloff=0.8)
    B.energy(poly([(16, 11), (19, 7), (22, 11)]), LIFE, falloff=0.8)
    C = ga(BG_R)
    C.energy(cut(heart(12, 13, 7.5), heart(12, 13.5, 4.8), seg(3, 4, 21, 22, 0.7)), CRIMSON, falloff=1.2)
    return A, B, C


def grand_retribution():
    A = ga(BG_R)
    A.solid(poly([(5, 5), (10, 4), (12, 6), (14, 4), (19, 5), (19, 14), (16, 20), (8, 20), (5, 14)]), STEEL, base=2.6)
    for k in range(5):
        a = math.radians(-150 + k * 30)
        A.solid(seg(12 + math.cos(a) * 7, 12 + math.sin(a) * 7, 12 + math.cos(a) * 11, 12 + math.sin(a) * 11, 1.0, 0.2), STEEL, base=3.4)
    B = ga(BG_R)
    B.solid(ellipse(12, 15, 7, 7.5), DEMON if False else SHADOW, base=2.4)
    for d in (-1, 1):
        B.solid(poly([(12 + d * 3, 9), (12 + d * 7, 3), (12 + d * 5.5, 10)]), BONE, base=3.2)
    B.streak(0, 3, 9, 12, 1.2, CRIMSON)
    B.streak(24, 3, 15, 12, 1.2, CRIMSON)
    C = ga(BG_R)
    C.energy(cut(star(12, 13, 4, 10, 8), circle(12, 13, 2)), CRIMSON, falloff=1.2)
    C.energy(poly([(6, 5), (8, 1), (10, 4), (12, 0), (14, 4), (16, 1), (18, 5)]), GOLD, falloff=0.8)
    return A, B, C


ORBS = {
    "inner_light_encompassing_light": encompassing_light, "inner_light_celestial_light": celestial_light,
    "inner_light_shattering_light": shattering_light,
    "consecrated_ground_encompassing_prayer": encompassing_prayer, "consecrated_ground_cleansing_prayer": cleansing_prayer,
    "consecrated_ground_restoration_prayer": restoration_prayer,
    "divine_protection_divine_sustain": divine_sustain, "divine_protection_extended_protection": extended_protection,
    "divine_protection_divine_intervention": divine_intervention,
    "divine_favor_holy_flames": holy_flames, "divine_favor_restoring_favor": restoring_favor, "divine_favor_fanaticism": fanaticism,
    "holy_blast_divine_blast": divine_blast, "holy_blast_massive_blast": massive_blast,
    "celestial_orbs_plentiful_orbs": plentiful_orbs, "celestial_orbs_destructive_orbs": destructive_orbs,
    "holy_banner_invigorating_banner": invigorating_banner, "holy_banner_war_banner": war_banner,
    "call_crusaders_call_crossbowmen": call_crossbowmen, "call_crusaders_endless_crusaders": endless_crusaders,
    "flagellate_jagged_flail": jagged_flail, "flagellate_ecstasy": ecstasy,
    "retribution_masochism": masochism, "retribution_grand_retribution": grand_retribution,
}


# second pass
_ib, _wb, _ds = invigorating_banner, war_banner, divine_sustain
PENNANT = poly([(5, 3), (19, 3), (19, 21), (12, 16), (5, 21)])


def invigorating_banner():
    A, B, C = _ib()
    C = ga()
    C.solid(PENNANT, CRIMSON, base=2.8)
    for k in range(2):
        C.energy(poly([(8, 13 - k * 5), (12, 9 - k * 5), (16, 13 - k * 5), (16, 15 - k * 5), (12, 11 - k * 5), (8, 15 - k * 5)]), HOLY, falloff=0.7)
    return A, B, C


def war_banner():
    A, B, C = _wb()
    C = ga()
    C.solid(PENNANT, CRIMSON, base=2.8)
    crosshair(C, 12, 10, 3.6, HOLY, w=0.6)
    return A, B, C


def divine_sustain():
    A, B, C = _ds()
    B = ga(BG_M)
    potion(B, 12, 14, 1.1, liquid=MANA)
    B.paint(box(12, 13, 3, 2), lambda x, y, d: None)
    B.rays(12, 0, HOLY, n=5, lo=1, hi=2.6)
    B.streak(12, 0, 12, 8, 1.0, HOLY)
    return A, B, C


ORBS.update({"holy_banner_invigorating_banner": invigorating_banner, "holy_banner_war_banner": war_banner,
             "divine_protection_divine_sustain": divine_sustain})
