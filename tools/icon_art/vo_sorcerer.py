"""Sorcerer orb icons: A the gear up close, B the moment it happens, C an abstract mark."""
from vm import *

ELEM = [FIRE, ICE, VOLT]


def ghost(ic, fn, tint, al):
    sb = Icon()
    sb.im = ic.im.copy()
    sb.p = sb.im.load()
    fn(sb)
    for yy in range(N):
        for xx in range(N):
            if sb.p[xx, yy] != ic.p[xx, yy]:
                ic.p[xx, yy] = mix(ic.p[xx, yy], mix(sb.p[xx, yy], tint, 0.5), al)


def orb(ic, cx, cy, r, rmp, fall=None):
    ic.glow(cx, cy, r * 2.2, rmp[4], 0.5)
    ic.energy(circle(cx, cy, r), rmp, falloff=fall or r * 0.9)


def chain_lightning():
    A = G("100c04", "262008", (4, 12))
    bolt(A, [(1, 12), (6, 9), (10, 13)], w=0.9)
    bolt(A, [(10, 13), (14, 6), (17, 8)], w=0.8)
    bolt(A, [(10, 13), (15, 17), (20, 16)], w=0.8)
    for x, y in ((10, 13), (17, 8), (20, 16)):
        flash(A, x, y, 1.8, VOLT)
    B = G("0e0a04", "221a08", (12, 12))
    for x, y in ((4, 18), (12, 6), (20, 17)):
        B.solid(ellipse(x, y + 1, 2.4, 3.2), SHADOW, base=2.2)
    bolt(B, [(4, 16), (8, 9), (12, 5)], w=0.8)
    bolt(B, [(12, 5), (15, 11), (20, 15)], w=0.8)
    C = G("100c04", "2a2208", (12, 12))
    for k in range(3):
        C.energy(ring(5 + k * 7, 12, 2.6, 1.0), VOLT, falloff=0.6)
    C.energy(union(seg(7.6, 12, 9.4, 12, 0.7), seg(14.6, 12, 16.4, 12, 0.7)), VOLT, falloff=0.6)
    return A, B, C


def extended_discharge():
    A = G("0c0a04", "201a08", (4, 12))
    A.energy(circle(3, 12, 2.4), VOLT, falloff=2)
    for k, a in enumerate((-24, -8, 8, 24)):
        r = math.radians(a)
        bolt(A, [(4, 12), (4 + math.cos(r) * 9, 12 + math.sin(r) * 9 + (1 if k % 2 else -1)), (4 + math.cos(r) * 20, 12 + math.sin(r) * 20)], w=0.55)
    B = G("0c0a04", "201a08", (12, 12))
    for k, r in enumerate((4, 7, 10)):
        B.energy(arc(2, 12, r * 1.7, 0.9 + k * 0.2, -35, 35), VOLT, falloff=0.6)
    C = G("100c04", "2a2208", (12, 12))
    C.energy(union(seg(3, 12, 19, 12, 1.0), poly([(17, 7.5), (23, 12), (17, 16.5)]), seg(3, 7, 3, 17, 0.9)), VOLT, falloff=0.8)
    return A, B, C


def scorching_rays():
    A = G("140604", "2e1006", (4, 12))
    A.energy(circle(3, 12, 2.6), FIRE, falloff=2.4)
    for a in (-22, 0, 22):
        r = math.radians(a)
        A.streak(4, 12, 4 + math.cos(r) * 20, 12 + math.sin(r) * 20, 1.1, FIRE)
    B = G("140604", "2a1006", (6, 12))
    B.solid(ellipse(15, 13, 3, 6), SHADOW, base=2.2)
    B.streak(0, 13, 23, 13, 1.2, FIRE)
    flash(B, 15, 13, 2.4, FIRE)
    C = G("140604", "2e1006", (12, 12))
    for a in (-30, 0, 30):
        r = math.radians(a)
        C.energy(seg(4, 12, 4 + math.cos(r) * 18, 12 + math.sin(r) * 18, 0.4, 1.4), FIRE, falloff=0.9)
    return A, B, C


def rays_of_frost():
    A = G("06101e", "0e2440", (4, 12))
    A.energy(circle(3, 12, 2.6), ICE, falloff=2.4)
    for a in (-8, 0, 8):
        r = math.radians(a)
        A.streak(4, 12, 4 + math.cos(r) * 20, 12 + math.sin(r) * 20, 0.9, ICE)
    B = G("06101e", "0e223c", (12, 12))
    B.solid(ellipse(17, 12, 3.2, 6.2), SHADOW, base=2.2)
    for y in (10, 12, 14):
        B.streak(0, y + (y - 12) * 0.6, 17, y, 0.7, ICE)
    for x, y in ((15, 8), (18, 15)):
        B.solid(shard(x, y, -60, 4, 1.1), ICE, base=4.6)
    C = G("06101e", "0e2440", (12, 12))
    C.energy(poly([(3, 9), (21, 11), (21, 13), (3, 15)]), ICE, falloff=1.2)
    snowflake(C, 18, 12, 4, w=0.45)
    return A, B, C


def adaptive_orb():
    A = G("0c0a12", "1e1a28", (12, 12))
    orb(A, 12, 12, 6.5, ARCANE)
    for k, rm in enumerate(ELEM):
        a = math.radians(k * 120 - 90)
        A.energy(circle(12 + math.cos(a) * 9, 12 + math.sin(a) * 9, 1.6), rm, falloff=1.4)
    B = G("0c0a12", "1c1826", (12, 12))
    B.energy(inter(circle(12, 12, 7), lambda x, y: x - 12), FIRE, falloff=3)
    B.energy(inter(circle(12, 12, 7), lambda x, y: 12 - x), ICE, falloff=3)
    C = G("0c0a12", "1e1a28", (12, 12))
    for k, rm in enumerate(ELEM):
        a0 = k * 120 - 90
        C.energy(arc(12, 12, 7.5, 2.4, a0 + 8, a0 + 112), rm, falloff=1.0)
    C.energy(circle(12, 12, 2.2), ARCANE, falloff=2)
    return A, B, C


def stable_orb():
    A = G("0c0a12", "1e1a28", (12, 12))
    A.solid(ring(12, 12, 9, 1.8), BRASS, base=2.6)
    orb(A, 12, 12, 5.8, ARCANE)
    for a in (45, 135, 225, 315):
        r = math.radians(a)
        A.solid(circle(12 + math.cos(r) * 9, 12 + math.sin(r) * 9, 1.3), BRASS, base=3.4)
    B = G("0c0a12", "1c1826", (12, 12))
    hourglass(B, 8, 12, 0.95, sand=ARCANE, t=0.2)
    orb(B, 17, 12, 4.0, ARCANE)
    C = G("0c0a12", "1e1a28", (12, 12))
    C.energy(circle(12, 12, 5), ARCANE, falloff=4)
    C.energy(ring(12, 12, 8.4, 0.9), ARCANE, falloff=0.5)
    C.energy(ring(12, 12, 10.4, 0.6), ARCANE[:5], falloff=0.4)
    return A, B, C


def elemental_torrent():
    A = G("0c0a12", "1e1a28", (12, 12))
    orb(A, 12, 12, 4.5, ARCANE)
    for k in range(8):
        a = math.radians(k * 45 + 10)
        A.energy(circle(12 + math.cos(a) * 9, 12 + math.sin(a) * 9, 1.3), ELEM[k % 3], falloff=1.2)
    B = G("0c0a12", "1c1826", (12, 12))
    orb(B, 12, 12, 3.6, ARCANE)
    for k in range(9):
        a = math.radians(k * 40)
        B.streak(12 + math.cos(a) * 4, 12 + math.sin(a) * 4, 12 + math.cos(a) * 11, 12 + math.sin(a) * 11, 0.9, ELEM[k % 3])
    C = G("0c0a12", "1e1a28", (12, 12))
    for k in range(3):
        a = math.radians(k * 120 - 90)
        C.energy(drop(12 + math.cos(a) * 6, 12 + math.sin(a) * 6, 2.8), ELEM[k], falloff=2)
    return A, B, C


def uncontrolled_power():
    A = G("0e0818", "241434", (12, 12))
    staff(A, 10, 14, -60, 1.0, gem=ARCANE)
    A.rays(15, 5, ARCANE, n=7, lo=1, hi=3.4)
    flash(A, 15, 5, 3, ARCANE)
    B = G("0e0818", "221432", (12, 12))
    B.rays(12, 12, ARCANE, n=11, lo=1, hi=4.5, width=0.4)
    B.energy(star(12, 12, 2.4, 6.5, 4, rot=-90), ARCANE, falloff=2)
    C = G("0e0818", "241434", (12, 12))
    C.energy(cut(star(12, 12, 4, 10, 4, rot=-45), star(12, 12, 1.5, 5, 4, rot=-45)), ARCANE, falloff=1.2)
    return A, B, C


def power_surge():
    A = G("0e0818", "241434", (14, 8))
    boot(A, 13, 11, 0.9, rmp=R("10081c", "241238", "3a1e5a", "58307e", "8458b0", "b890e0"))
    bolt(A, [(4, 6), (7, 10), (5, 13), (8, 17)], rmp=ARCANE, w=0.6)
    B = G("0e0818", "221432", (16, 12))
    for y, x0 in ((5, 0), (11, 1), (17, 0)):
        B.streak(x0, y, x0 + 11, y, 0.9, ARCANE)
    B.energy(star(18, 11, 2, 5, 4), ARCANE, falloff=1.6)
    C = G("0e0818", "241434", (12, 12))
    C.energy(poly([(13, 2), (6, 13), (11, 13), (9, 22), (18, 9), (13, 9), (16, 2)]), ARCANE, falloff=1.6)
    return A, B, C


def mana_surge():
    A = G("040818", "0e1a3a", (12, 8))
    potion(A, 12, 13, 1.25, liquid=MANA)
    A.energy(star(19, 5, 1.2, 3.4, 4), ARCANE, falloff=1)
    B = G("040818", "0c1634", (12, 12))
    B.rays(12, 12, MANA, n=9, lo=1, hi=4)
    B.energy(drop(12, 13, 4.2), MANA, falloff=3)
    C = G("040818", "0e1a3a", (12, 12))
    C.energy(cut(drop(12, 13.5, 6.4), drop(12, 13.5, 3.8)), MANA, falloff=1.2)
    C.energy(star(12, 14, 1.0, 3.0, 4), ARCANE, falloff=1)
    return A, B, C


def elemental_ward():
    A = G("0c0a12", "1e1a28", (12, 6))
    shield(A, 12, 11, 1.1, STEEL, face=SHADOW, boss=None)
    for k, rm in enumerate(ELEM):
        A.energy(circle(8 + k * 4, 10 + (k == 1) * -2, 1.6), rm, falloff=1.4)
    B = G("0c0a12", "1c1826", (12, 12))
    B.energy(ring(12, 12, 8.5, 1.4), SPIRIT, falloff=0.8)
    for k, (rm, a) in enumerate(zip(ELEM, (200, 300, 60))):
        r = math.radians(a)
        x, y = 12 + math.cos(r) * 13, 12 + math.sin(r) * 13
        B.streak(x, y, 12 + math.cos(r) * 9.5, 12 + math.sin(r) * 9.5, 1.0, rm)
    C = G("0c0a12", "1e1a28", (12, 12))
    for k, rm in enumerate(ELEM):
        C.energy(arc(12, 12, 4 + k * 2.6, 1.3, 200, 340), rm, falloff=0.7)
    return A, B, C


def elemental_penetration():
    A = G("0c0a12", "1e1a28", (12, 12))
    A.solid(box(16, 12, 3, 9), STEEL, base=2.2)
    for k, rm in enumerate(ELEM):
        A.streak(1, 6 + k * 6, 21, 6 + k * 6, 0.9, rm)
    B = G("0c0a12", "1c1826", (12, 12))
    shield(B, 14, 11, 1.0, STEEL, boss=None)
    B.energy(shard(9, 12, 0, 16, 1.6), FIRE, falloff=1.2)
    C = G("0c0a12", "1e1a28", (12, 12))
    for k, rm in enumerate(ELEM):
        C.energy(poly([(3 + k * 6, 6), (9 + k * 6, 12), (3 + k * 6, 18), (5 + k * 6, 12)]), rm, falloff=0.9)
    return A, B, C


def elemental_equilibrium():
    A = G("0c0a12", "1e1a28", (12, 6))
    A.solid(seg(4, 9, 20, 9, 0.7), BRASS, base=3)
    A.solid(box(12, 15, 0.9, 7), BRASS, base=2.6)
    A.solid(poly([(9, 22), (15, 22), (12, 19)]), BRASS, base=2.6)
    orb(A, 5, 13, 2.8, FIRE)
    orb(A, 19, 13, 2.8, ICE)
    B = G("0c0a12", "1c1826", (12, 12))
    for k, rm in enumerate(ELEM):
        a = math.radians(k * 120 - 90)
        B.energy(circle(12 + math.cos(a) * 5.5, 12 + math.sin(a) * 5.5, 3.6), rm, falloff=2.4)
    C = G("0c0a12", "1e1a28", (12, 12))
    C.energy(cut(circle(12, 12, 8), union(circle(12, 8, 4), lambda x, y: x - 12 if y > 8 else 9)), FIRE, falloff=1.6)
    C.energy(cut(inter(circle(12, 12, 8), lambda x, y: 12 - x if True else 0), circle(12, 16, 4)), ICE, falloff=1.6)
    C.energy(circle(12, 8, 1.2), ICE, falloff=1)
    C.energy(circle(12, 16, 1.2), FIRE, falloff=1)
    return A, B, C


def flamewalker():
    A = G("140604", "2e1006", (12, 12))
    boot(A, 12, 9, 0.85, rmp=EMBER)
    for k, x in enumerate((5, 10, 15, 20)):
        A.energy(flame(x, 23, 2.4, 6 + (k % 2) * 3, 0, k), FIRE, falloff=1.4)
    B = G("140604", "2a1006", (12, 12))
    B.solid(ellipse(12, 12, 3.4, 7.5), SHADOW, base=2.4)
    B.energy(ring(12, 13, 8, 1.6), FIRE, falloff=1)
    for x in (4, 20):
        B.energy(flame(x, 18, 2, 7, 0, x), FIRE, falloff=1.2)
    C = G("140604", "2e1006", (12, 12))
    C.energy(ring(12, 12, 8.5, 1.6), FIRE, falloff=0.9)
    C.energy(flame(12, 18, 3.6, 12, 0, 3), FIRE, falloff=1.6)
    return A, B, C


def flamestep():
    A = G("140604", "2e1006", (14, 8))
    boot(A, 14, 10, 0.95)
    A.energy(flame(5, 22, 3, 10, -0.6, 2), FIRE, falloff=1.4)
    B = G("140604", "2a1006", (16, 12))
    for y, x0 in ((7, 0), (12, 0), (17, 1)):
        B.streak(x0, y, x0 + 9, y, 0.8, SMOKE)
    for x in (12, 16, 20):
        B.energy(flame(x, 22, 2, 10, 0, x), FIRE, falloff=1.2)
    C = G("140604", "2e1006", (12, 12))
    for k in range(2):
        x = 6 + k * 7
        C.energy(union(seg(x, 6, x + 4, 12, 1.1), seg(x + 4, 12, x, 18, 1.1)), FIRE, falloff=0.9)
    return A, B, C


def wall_placement():
    A = G("140604", "2e1006", (12, 12))
    crosshair(A, 12, 13, 6.5, FIRE)
    for x in (8, 12, 16):
        A.energy(flame(x, 16, 1.7, 6, 0, x), FIRE, falloff=1.1)
    B = G("140604", "2a1006", (12, 12))
    staff(B, 6, 15, -70, 0.7, gem=FIRE)
    for k, x in enumerate((11, 15, 19)):
        B.energy(flame(x, 15 - k * 2, 2, 8, 0, k), FIRE, falloff=1.3)
    C = G("140604", "2e1006", (12, 12))
    C.energy(poly([(12, 22), (7, 14), (17, 14)]), FIRE, falloff=1)
    C.energy(union(*[seg(4 + k * 4, 11, 4 + k * 4, 4, 1.0, 0.3) for k in range(5)]), FIRE, falloff=0.9)
    return A, B, C


def volatile_flames():
    A = G("140604", "2e1006", (12, 12))
    A.energy(flame(12, 21, 5, 16, 0, 3), FIRE, falloff=2)
    flash(A, 12, 6, 4, FIRE)
    B = G("140604", "2a1006", (12, 12))
    B.rays(12, 12, FIRE, n=10, lo=1, hi=4)
    B.energy(star(12, 12, 3, 8, 8), FIRE, falloff=2.4)
    C = G("140604", "2e1006", (12, 12))
    C.energy(cut(star(12, 12, 4, 10, 6), circle(12, 12, 3)), FIRE, falloff=1.4)
    return A, B, C


def healing_flames():
    A = G("140604", "2e1006", (12, 12))
    A.energy(flame(12, 21, 6, 17, 0, 1), LIFE, falloff=2)
    B = G("140604", "2a1006", (12, 14))
    B.solid(heart(12, 14, 6.0), CRIMSON, base=3.4)
    B.energy(flame(12, 9, 2.4, 7, 0, 2), FIRE, falloff=1.4)
    C = G("140604", "2e1006", (12, 12))
    C.energy(cut(heart(12, 13, 7.5), heart(12, 13.5, 4.8)), FIRE, falloff=1.2)
    C.energy(flame(12, 17, 2.2, 7, 0, 4), FIRE, falloff=1.2)
    return A, B, C


def frost_seekers():
    A = G("06101e", "0e2440", (12, 12))
    for k, (x, y, a) in enumerate(((7, 16, -30), (14, 8, -10))):
        A.energy(shard(x, y, a, 9, 2), ICE, falloff=1.6)
    A.energy(arc(15, 18, 7, 0.8, 200, 300), ICE, falloff=0.5)
    B = G("06101e", "0e223c", (12, 12))
    B.solid(ellipse(19, 17, 2.6, 4), SHADOW, base=2.2)
    pts = [(2, 4), (7, 6), (12, 10), (16, 14)]
    for i in range(3):
        B.streak(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 0.6 + i * 0.25, ICE)
    B.energy(shard(17, 15, 45, 5, 1.4), ICE, falloff=1.2)
    C = G("06101e", "0e2440", (12, 12))
    crosshair(C, 12, 12, 6.5, ICE)
    C.energy(shard(12, 12, -45, 6, 1.4), ICE, falloff=1)
    return A, B, C


def frost_splinters():
    A = G("06101e", "0e2440", (12, 12))
    A.energy(shard(12, 12, -45, 14, 3), ICE, falloff=2)
    for k in range(5):
        a = math.radians(k * 72 + 30)
        A.energy(shard(12 + math.cos(a) * 9, 12 + math.sin(a) * 9, k * 72 + 30, 3.6, 0.9), ICE, falloff=0.9)
    B = G("06101e", "0e223c", (12, 12))
    skull(B, 12, 12, 0.9, rmp=R("0a1a2a", "1a3a5a", "2a5a8a", "5a8ab8", "a0c8e8", "e0f4ff"), eyes=ICE)
    for k in range(8):
        a = math.radians(k * 45)
        B.streak(12 + math.cos(a) * 7, 12 + math.sin(a) * 7, 12 + math.cos(a) * 11.5, 12 + math.sin(a) * 11.5, 0.7, ICE)
    C = G("06101e", "0e2440", (12, 12))
    snowflake(C, 12, 12, 9, w=0.8)
    return A, B, C


def shatter():
    A = G("06101e", "0e2440", (12, 12))
    A.solid(poly([(12, 2), (20, 8), (19, 18), (11, 22), (4, 16), (5, 6)]), ICE, base=4, seed=1)
    A.paint(union(seg(12, 3, 11, 11, 0.4), seg(11, 11, 18, 14, 0.4), seg(11, 11, 6, 17, 0.4), seg(11, 11, 6, 7, 0.35)), lambda x, y, d: ICE[1])
    B = G("06101e", "0e223c", (12, 12))
    flash(B, 12, 12, 3.4, ICE)
    for k in range(7):
        a = k * 51 + 15
        r = math.radians(a)
        B.solid(shard(12 + math.cos(r) * 8, 12 + math.sin(r) * 8, a, 5, 1.4), ICE, base=4.4, seed=k)
    C = G("06101e", "0e2440", (12, 12))
    C.energy(cut(star(12, 12, 3, 10, 6, rot=-90), union(seg(12, 2, 12, 22, 0.5), seg(3, 7, 21, 17, 0.5))), ICE, falloff=1.4)
    return A, B, C


def ice_block():
    A = G("06101e", "0e2440", (12, 12))
    A.solid(box(12, 12, 8, 8, 0, 1.5), ICE, base=3.6, seed=2)
    A.solid(box(12, 12, 4, 4, 0, 1), ICE, base=4.8, seed=3)
    A.glint(7, 7)
    B = G("06101e", "0e223c", (12, 12))
    B.solid(box(15, 12, 4, 9, 0, 1), ICE, base=4.0)
    for y in (7, 12, 17):
        B.streak(1, y, 10, y, 0.8, STEEL)
    flash(B, 11, 12, 2.6, ICE)
    C = G("06101e", "0e2440", (12, 12))
    C.energy(cut(poly([(12, 3), (21, 8), (21, 17), (12, 21), (3, 17), (3, 8)]), poly([(12, 6), (18, 9.5), (18, 15.5), (12, 18.5), (6, 15.5), (6, 9.5)])), ICE, falloff=1)
    C.energy(poly([(12, 9), (15, 12), (12, 15), (9, 12)]), ICE, falloff=1)
    return A, B, C


def energized_ball():
    A = G("100c04", "262008", (12, 12))
    orb(A, 12, 12, 6, VOLT)
    for a in (20, 140, 260):
        r = math.radians(a)
        bolt(A, [(12 + math.cos(r) * 6, 12 + math.sin(r) * 6), (12 + math.cos(r + 0.3) * 9, 12 + math.sin(r + 0.3) * 9), (12 + math.cos(r) * 11.5, 12 + math.sin(r) * 11.5)], w=0.5)
    B = G("0e0a04", "221a08", (12, 12))
    for x, y in ((4, 18), (20, 17)):
        B.solid(ellipse(x, y, 2.4, 3.6), SHADOW, base=2.2)
    orb(B, 12, 9, 4.6, VOLT)
    bolt(B, [(10, 12), (6, 15), (4, 17)], w=0.5)
    bolt(B, [(14, 12), (18, 14), (20, 16)], w=0.5)
    C = G("100c04", "2a2208", (12, 12))
    C.energy(ring(12, 12, 8, 1.4), VOLT, falloff=0.8)
    C.energy(circle(12, 12, 4), VOLT, falloff=3)
    hourglass_mark = poly([(18, 2), (22, 2), (20, 5)])
    C.energy(hourglass_mark, VOLT, falloff=0.8)
    return A, B, C


def static_field():
    A = G("100c04", "262008", (12, 16))
    for k in range(4):
        bolt(A, [(3 + k * 5.5, 21), (5 + k * 5.5, 17), (3 + k * 5.5, 14), (5.5 + k * 5.5, 10)], w=0.5)
    A.energy(ellipse(12, 20, 10, 2.4), VOLT, falloff=0.9)
    B = G("0e0a04", "221a08", (12, 12))
    orb(B, 6, 8, 3.4, VOLT)
    B.streak(8, 10, 22, 20, 1.6, VOLT)
    bolt(B, [(12, 16), (14, 21)], w=0.4)
    bolt(B, [(17, 17), (20, 23)], w=0.4)
    C = G("100c04", "2a2208", (12, 12))
    C.energy(union(*[seg(2, 6 + k * 6, 22, 6 + k * 6, 0.3) for k in range(3)]), VOLT[:5], falloff=0.3)
    C.energy(union(seg(4, 16, 8, 6, 0.8), seg(8, 6, 12, 16, 0.8), seg(12, 16, 16, 6, 0.8), seg(16, 6, 20, 16, 0.8)), VOLT, falloff=0.8)
    return A, B, C


def arc_lightning():
    A = G("100c04", "262008", (12, 12))
    staff(A, 8, 15, -60, 0.9, gem=VOLT)
    bolt(A, [(13, 6), (17, 9), (20, 7), (22, 11)], w=0.6)
    B = G("0e0a04", "221a08", (12, 12))
    for x, y in ((5, 8), (18, 6), (12, 18)):
        B.solid(ellipse(x, y, 2.2, 3.2), SHADOW, base=2.2)
    bolt(B, [(5, 8), (11, 6), (18, 6)], w=0.6)
    bolt(B, [(18, 6), (17, 12), (12, 18)], w=0.6)
    C = G("100c04", "2a2208", (12, 12))
    C.energy(arc(12, 16, 9, 1.8, 190, 350), VOLT, falloff=0.9)
    C.energy(union(circle(3, 16, 1.6), circle(21, 16, 1.6)), VOLT, falloff=1.2)
    return A, B, C


def null_field():
    A = G("0c0a12", "1e1a28", (12, 12))
    A.energy(ring(12, 12, 8.5, 1.4), VOLT, falloff=0.8)
    arrow(A, 12, 12, -45, 0.8)
    A.paint(seg(5, 5, 19, 19, 0.9), lambda x, y, d: VOLT[5])
    B = G("0c0a12", "1c1826", (12, 12))
    B.energy(arc(9, 12, 8, 1.6, -70, 70), VOLT, falloff=0.9)
    for y in (7, 12, 17):
        arrow(B, 21, y, 180, 0.4)
    flash(B, 16.5, 12, 2, VOLT)
    C = G("0c0a12", "1e1a28", (12, 12))
    C.energy(cut(circle(12, 12, 9), circle(12, 12, 7.2)), VOLT, falloff=0.8)
    bolt(C, [(14, 4), (9, 12), (14, 12), (10, 20)], w=1.0)
    return A, B, C


ORBS = {
    "static_discharge_chain": chain_lightning, "static_discharge_range": extended_discharge,
    "static_discharge_fire": scorching_rays, "static_discharge_ice": rays_of_frost,
    "elemental_orb_affinity": adaptive_orb, "elemental_orb_duration": stable_orb, "elemental_orb_spew": elemental_torrent,
    "innate_power_critdamage": uncontrolled_power, "innate_power_surge": power_surge, "innate_power_mana": mana_surge,
    "elemental_affinity_ward": elemental_ward, "elemental_affinity_penetration": elemental_penetration,
    "elemental_affinity_equilibrium": elemental_equilibrium,
    "fire_wall_flamewalker": flamewalker, "fire_wall_dash": flamestep, "fire_wall_targeted": wall_placement,
    "fire_mastery_volatile": volatile_flames, "fire_mastery_heal": healing_flames,
    "ice_frost_nova_retarget": frost_seekers, "ice_frost_nova_kill": frost_splinters,
    "ice_mastery_shatter": shatter, "ice_mastery_block": ice_block,
    "lightning_ball_ttl": energized_ball, "lightning_ball_static": static_field,
    "lightning_mastery_arc": arc_lightning, "lightning_mastery_block": null_field,
}


# second pass: the weak ones
_fs, _nf, _sh = frost_seekers, null_field, shatter


def frost_seekers():
    A, B, C = _fs()
    A = G("06101e", "0e2440", (12, 12))
    for x, y, a in ((7, 17, -40), (16, 9, -40)):
        A.solid(shard(x, y, a, 11, 3.2), ICE, base=4.4, seed=x)
    A.energy(arc(12, 12, 10, 0.9, 120, 200), ICE, falloff=0.5)
    A.energy(arc(12, 12, 10, 0.9, 300, 20), ICE, falloff=0.5)
    return A, B, C


def null_field():
    A, B, C = _nf()
    B = G("0c0a12", "1c1826", (12, 12))
    B.energy(circle(12, 12, 8), SPIRIT, falloff=6)
    B.energy(ring(12, 12, 8, 1.2), VOLT, falloff=0.7)
    bolt(B, [(1, 3), (4, 6), (3, 8), (5.5, 9.5)], w=0.7)
    bolt(B, [(5.5, 9.5), (2, 13), (0, 14)], w=0.6)
    flash(B, 5.5, 9.5, 2, VOLT)
    return A, B, C


def shatter():
    A, B, C = _sh()
    C = G("06101e", "0e2440", (12, 12))
    for k in range(4):
        a = k * 90 + 45
        r = math.radians(a)
        C.energy(poly([(12 + math.cos(r) * 2, 12 + math.sin(r) * 2), (12 + math.cos(r - 0.35) * 10, 12 + math.sin(r - 0.35) * 10), (12 + math.cos(r + 0.35) * 10, 12 + math.sin(r + 0.35) * 10)]), ICE, falloff=1.6)
    return A, B, C


ORBS["ice_frost_nova_retarget"] = frost_seekers
ORBS["lightning_mastery_block"] = null_field
ORBS["ice_mastery_shatter"] = shatter
