"""Ranger orb icons: A the gear up close, B the moment it happens, C an abstract mark."""
from vm import *

BG_W = ("0a0e06", "1c2610")
BG_R = ("140406", "2e0a10")
BG_I = ("06101e", "0e2440")
BG_Y = ("100c04", "262008")
BG_S = ("040c14", "0c2030")
BG_L = ("041004", "0e2a10")


def ga(c=BG_W, light=(12, 12)):
    return G(c[0], c[1], light)


def foe(ic, x, y, s=1.0):
    ic.solid(ellipse(x, y, 2.6 * s, 3.6 * s), SHADOW, base=2.2)


def mark(ic, cx, cy, r, rmp=CRIMSON):
    crosshair(ic, cx, cy, r, rmp, w=0.7)


def hot_pursuit():
    A = ga()
    boot(A, 13, 11, 0.9, wing=SPIRIT)
    mark(A, 5, 5, 3)
    B = ga()
    for y, x0 in ((7, 0), (12, 1), (17, 0)):
        B.streak(x0, y, x0 + 9, y, 0.8, SPIRIT)
    foe(B, 18, 12, 1.2)
    mark(B, 18, 12, 4.4)
    C = ga()
    for k in range(2):
        x = 5 + k * 6
        C.energy(union(seg(x, 6, x + 4, 12, 1.1), seg(x + 4, 12, x, 18, 1.1)), SPIRIT, falloff=0.9)
    mark(C, 18, 12, 3.2)
    return A, B, C


def thrill_of_the_hunt():
    A = ga()
    dagger(A, 9, 13, -45, 1.0)
    A.solid(heart(18, 17, 3.2), CRIMSON, base=3.4)
    A.energy(drop(18, 6, 2.4), MANA, falloff=1.6)
    B = ga()
    skull(B, 8, 14, 0.7)
    mark(B, 8, 13, 6.5)
    B.energy(poly([(17, 9), (20, 5), (23, 9)]), LIFE, falloff=0.8)
    B.energy(poly([(17, 14), (20, 10), (23, 14)]), MANA, falloff=0.8)
    C = ga()
    mark(C, 12, 12, 8)
    C.solid(heart(12, 12, 3.4), CRIMSON, base=3.4)
    return A, B, C


def big_game_hunter():
    A = ga()
    bow(A, 10, 12, -45, 1.0)
    arrow(A, 12, 10, -45, 0.85)
    A.solid(poly([(17, 17), (19, 22), (21, 17), (19, 19)]), BONE, base=3)
    B = ga()
    B.solid(ellipse(13, 14, 8, 8.5), SHADOW, base=2.4)
    for d in (-1, 1):
        B.solid(poly([(13 + d * 3, 8), (13 + d * 8, 2), (13 + d * 6, 9)]), BONE, base=3.2)
    mark(B, 13, 14, 5)
    C = ga()
    mark(C, 12, 13, 8.5)
    C.energy(poly([(6, 5), (8, 1), (10, 4), (12, 0), (14, 4), (16, 1), (18, 5)]), GOLD, falloff=0.8)
    return A, B, C


def trap(ic, cx, cy, s=1.0, rmp=STEEL, teeth=SPIRIT):
    ic.solid(ellipse(cx, cy, 8 * s, 3.4 * s), rmp, base=2.4)
    ic.paint(ellipse(cx, cy, 5.6 * s, 2.0 * s), lambda x, y, d: rmp[1])
    for k in range(7):
        x = cx - 6 * s + k * 2 * s
        ic.solid(poly([(x - 0.8 * s, cy - 2.6 * s), (x, cy - 5.4 * s), (x + 0.8 * s, cy - 2.6 * s)]), rmp, base=3.6)


def multiple_deploy():
    A = ga(light=(12, 16))
    trap(A, 12, 15, 1.2)
    B = ga(light=(12, 16))
    for x, y in ((6, 9), (17, 12), (8, 20)):
        trap(B, x, y, 0.6)
    C = ga()
    for k in range(3):
        C.energy(union(*[poly([(3 + k * 6 + j * 2, 14), (4 + k * 6 + j * 2, 9), (5 + k * 6 + j * 2, 14)]) for j in range(2)]), STEEL, falloff=0.8)
    C.energy(box(12, 16, 9, 1), STEEL, falloff=0.6)
    return A, B, C


def serrated_traps():
    A = ga(BG_R, (12, 16))
    trap(A, 12, 15, 1.2)
    A.energy(drop(19, 8, 2.2), BLOOD, falloff=1.4)
    B = ga(BG_R, (12, 16))
    foe(B, 12, 12, 1.2)
    trap(B, 12, 17, 0.9)
    for x, y in ((5, 20), (19, 21)):
        B.energy(drop(x, y, 1.6), BLOOD, falloff=1.2)
    C = ga(BG_R)
    C.energy(union(*[poly([(3 + j * 3, 15), (4.5 + j * 3, 8), (6 + j * 3, 15)]) for j in range(6)]), STEEL, falloff=0.8)
    C.energy(drop(12, 19, 2.2), BLOOD, falloff=1.4)
    return A, B, C


def frost_traps():
    A = ga(BG_I, (12, 16))
    trap(A, 12, 15, 1.2, rmp=ICE)
    B = ga(BG_I, (12, 16))
    B.solid(box(12, 13, 4.4, 7, 0, 1.2), ICE, base=4, seed=2)
    foe(B, 12, 13, 1.0)
    trap(B, 12, 20, 0.8, rmp=ICE)
    C = ga(BG_I)
    C.energy(union(*[poly([(3 + j * 3, 17), (4.5 + j * 3, 11), (6 + j * 3, 17)]) for j in range(6)]), ICE, falloff=0.8)
    snowflake(C, 12, 6, 3.6, w=0.45)
    return A, B, C


def in_the_flow():
    A = ga()
    bow(A, 12, 12, -45, 1.1, drawn=2)
    for k in range(3):
        A.energy(arc(12, 12, 10 + k * 1.4, 0.4, 120 + k * 15, 190 + k * 15), SPIRIT, falloff=0.4)
    B = ga()
    for k in range(3):
        arrow(B, 8 + k * 4, 14 - k * 2, -30, 0.6)
    B.streak(0, 22, 10, 18, 0.6, SPIRIT)
    C = ga()
    for k in range(3):
        C.energy(arc(12, 12, 4 + k * 3, 1.0, k * 40 + 180, k * 40 + 300), SPIRIT, falloff=0.6)
    C.energy(poly([(18, 3), (23, 6), (19, 8)]), SPIRIT, falloff=0.8)
    return A, B, C


def efficiency():
    A = ga(("04081a", "0e1a3a"))
    potion(A, 12, 13, 1.15, liquid=MANA)
    for k in range(3):
        A.energy(arc(12, 12, 10.5, 0.5, 200 + k * 30, 220 + k * 30), SPIRIT, falloff=0.4)
    B = ga(("04081a", "0e1a3a"))
    B.energy(drop(12, 13, 7), MANA, falloff=3)
    B.energy(poly([(9, 9), (15, 9), (12, 14)]), PAPER, falloff=0.6)
    C = ga(("04081a", "0e1a3a"))
    C.energy(cut(drop(12, 13.5, 7), drop(12, 13.5, 4.4)), MANA, falloff=1.2)
    C.energy(poly([(9, 12), (15, 12), (12, 16)]), MANA, falloff=0.8)
    return A, B, C


def momentum():
    A = ga()
    boot(A, 14, 11, 0.9)
    for y in (7, 12, 17):
        A.streak(0, y, 6, y, 0.6, SPIRIT)
    B = ga()
    for k in range(2):
        B.solid(ellipse(5 + k * 5, 13, 2.6, 6), SHADOW, base=1 + k * 0.8, seed=k)
    B.solid(ellipse(16, 13, 2.6, 6), LEATHER, base=2.8)
    B.energy(arc(16, 13, 8, 1.0, 200, 340), SPIRIT, falloff=0.6)
    C = ga()
    for k in range(3):
        C.energy(union(seg(4 + k * 5, 6, 8 + k * 5, 12, 1.0), seg(8 + k * 5, 12, 4 + k * 5, 18, 1.0)), SPIRIT[:5 + k], falloff=0.8)
    return A, B, C


def cloak(ic, cx, cy, s=1.0, rmp=OLIVE):
    ic.solid(poly([(cx - 3 * s, cy - 8 * s), (cx + 3 * s, cy - 8 * s), (cx + 8 * s, cy + 9 * s), (cx, cy + 7 * s), (cx - 8 * s, cy + 9 * s)]), rmp, base=2.6)
    ic.solid(ellipse(cx, cy - 6 * s, 3.4 * s, 3.6 * s), rmp, base=3.2, seed=4)
    ic.paint(ellipse(cx, cy - 5.4 * s, 2 * s, 2.2 * s), lambda x, y, d: rmp[0])


def evasive_maneuver():
    A = ga()
    cloak(A, 12, 12, 1.0)
    B = ga()
    B.solid(ellipse(8, 13, 2.8, 6), SHADOW, base=1.2)
    cloak(B, 15, 12, 0.75)
    B.streak(0, 4, 18, 22, 0.6, STEEL)
    C = ga()
    for k in range(3):
        C.energy(ellipse(8 + k * 4, 12, 2.4 - k * 0.3, 7 - k), OLIVE[:5] + (SPIRIT[5],) if False else SPIRIT[:5 + k], falloff=1.4)
    return A, B, C


def tactical_maneuver():
    A = ga()
    cloak(A, 10, 12, 0.9)
    A.energy(poly([(16, 9), (22, 12), (16, 15), (18, 12)]), SPIRIT, falloff=0.8)
    B = ga()
    B.solid(ellipse(9, 13, 3, 6.5), OLIVE, base=2.6)
    flash(B, 7, 10, 2.4, CRIMSON)
    for y in (9, 14):
        B.streak(12, y, 22, y, 0.8, SPIRIT)
    C = ga()
    C.energy(union(seg(4, 6, 9, 12, 1.1), seg(9, 12, 4, 18, 1.1), seg(11, 6, 16, 12, 1.1), seg(16, 12, 11, 18, 1.1)), SPIRIT, falloff=0.9)
    C.energy(poly([(19, 9), (21, 12), (19, 15), (17, 12)]), CRIMSON, falloff=0.8)
    return A, B, C


def quick_recovery():
    A = ga(BG_L)
    potion(A, 12, 13, 1.15, liquid=LIFE)
    B = ga(BG_L)
    cloak(B, 12, 13, 0.8)
    for x, y in ((5, 5), (19, 6), (4, 15), (20, 16)):
        B.energy(poly([(x - 1.6, y + 1), (x, y - 1.4), (x + 1.6, y + 1)]), LIFE, falloff=0.7)
    C = ga(BG_L)
    C.energy(cut(heart(12, 13, 7.5), heart(12, 13.5, 4.8)), LIFE, falloff=1.2)
    for k in range(2):
        C.energy(poly([(9, 15 - k * 3), (12, 12 - k * 3), (15, 15 - k * 3), (15, 16 - k * 3), (12, 13 - k * 3), (9, 16 - k * 3)]), LIFE, falloff=0.6)
    return A, B, C


def rain(ic, xs, rmp=STEEL, y0=2, y1=16):
    for k, x in enumerate(xs):
        arrow(ic, x, y0 + (y1 - y0) / 2 + (k % 2) * 2, 100, 0.55)


def storm_of_arrows():
    A = ga(light=(12, 16))
    for k, x in enumerate((4, 9, 14, 19)):
        arrow(A, x, 9 + (k % 2) * 3, 100, 0.6)
    A.energy(ellipse(12, 20, 11, 2.6), STEEL, falloff=1)
    B = ga(light=(12, 16))
    B.energy(cut(ellipse(12, 17, 11, 5), ellipse(12, 17, 9.6, 3.8)), CRIMSON, falloff=0.8)
    for x, y in ((6, 15), (12, 19), (17, 15), (10, 13), (15, 18)):
        B.solid(seg(x, y, x - 0.6, y - 5, 0.5), WOOD, base=3)
        B.solid(poly([(x - 1.6, y - 6), (x + 0.6, y - 6), (x - 0.4, y - 4)]), CRIMSON, base=3)
    C = ga()
    for k in range(5):
        C.energy(seg(3 + k * 4.5, 3 + (k % 2) * 3, 4 + k * 4.5, 14 + (k % 2) * 3, 0.7), STEEL, falloff=0.6)
    C.energy(cut(ellipse(12, 19, 10, 3), ellipse(12, 19, 8.6, 1.8)), STEEL, falloff=0.6)
    return A, B, C


def thundercaller():
    A = ga(BG_Y)
    bow(A, 9, 14, -60, 0.95)
    bolt(A, [(15, 2), (13, 7), (17, 8), (14, 14)], w=0.8)
    B = ga(BG_Y, (12, 16))
    for x, h in ((5, 12), (12, 18), (19, 10)):
        bolt(B, [(x + 1, 22 - h), (x - 1, 22 - h * 0.6), (x + 1, 22 - h * 0.3), (x, 22)], w=0.7)
        B.energy(ellipse(x, 22, 2.6, 0.9), VOLT, falloff=0.8)
    C = ga(BG_Y)
    C.energy(union(seg(4, 20, 16, 4, 0.9), poly([(14, 2), (19, 1), (18, 6)])), STEEL, falloff=0.7)
    bolt(C, [(13, 10), (10, 15), (14, 15), (11, 22)], w=0.9)
    return A, B, C


def fast_shot():
    A = ga()
    bow(A, 9, 13, -45, 1.0, drawn=2)
    arrow(A, 13, 9, -45, 0.85)
    for k in range(3):
        A.streak(13 + k * 2, 21 - k * 4, 19 + k * 2, 15 - k * 4, 0.4, SPIRIT)
    B = ga()
    for y in (6, 12, 18):
        arrow(B, 12, y, 0, 0.7)
        B.streak(0, y, 5, y, 0.4, SPIRIT)
    C = ga()
    for k in range(3):
        C.energy(poly([(3 + k * 6, 5), (10 + k * 6, 12), (3 + k * 6, 19), (6 + k * 6, 12)]), SPIRIT, falloff=1)
    return A, B, C


def frost_arrows():
    A = ga(BG_I)
    arrow(A, 12, 12, -45, 1.2, head=ICE, fletch=SPIRIT)
    snowflake(A, 18, 6, 2.8, w=0.4)
    B = ga(BG_I)
    foe(B, 14, 13, 1.3)
    B.streak(0, 22, 12, 14, 0.6, STEEL)
    for k in range(6):
        a = k * 60 + 15
        r = math.radians(a)
        B.solid(shard(14 + math.cos(r) * 6, 13 + math.sin(r) * 6, a, 4, 1.2), ICE, base=4.4, seed=k)
    C = ga(BG_I)
    C.energy(union(seg(3, 21, 14, 10, 0.8), poly([(12, 7), (18, 6), (17, 12)])), ICE, falloff=0.7)
    snowflake(C, 17, 7, 5, w=0.5)
    return A, B, C


def spirit_wolf(ic, cx, cy, s=1.0, ang=0):
    wolf_head(ic, cx, cy, s, rmp=SPIRIT, eyes=PAPER)


def relentless_hunters():
    A = ga(BG_S)
    wolf_head(A, 12, 12, 1.1, rmp=SPIRIT, eyes=PAPER)
    B = ga(BG_S)
    for x, y in ((5, 17), (12, 7), (19, 16)):
        foe(B, x, y + 1)
    for (x0, y0), (x1, y1) in (((5, 15), (12, 5)), ((12, 5), (19, 14))):
        B.streak(x0, y0, x1, y1, 1.0, SPIRIT)
    C = ga(BG_S)
    C.energy(union(seg(3, 19, 8, 6, 1.0), seg(8, 6, 13, 19, 1.0), seg(13, 19, 18, 6, 1.0)), SPIRIT, falloff=0.8)
    C.energy(circle(19, 5, 2), SPIRIT, falloff=1.6)
    return A, B, C


def restless_spirits():
    A = ga(BG_S)
    skull(A, 8, 15, 0.7)
    wolf_head(A, 16, 8, 0.6, rmp=SPIRIT, eyes=PAPER)
    B = ga(BG_S)
    skull(B, 12, 17, 0.6)
    B.energy(wisp and circle(12, 6, 0), SPIRIT, falloff=1)
    wisp(B, 12, 7, 4, SPIRIT, ang=-90)
    C = ga(BG_S)
    C.energy(arc(12, 12, 9, 1.6, 90, 400), SPIRIT, falloff=0.8)
    C.energy(poly([(9, 21), (14, 18), (14, 24)]), SPIRIT, falloff=0.8)
    C.energy(circle(12, 12, 2.6), SPIRIT, falloff=2)
    return A, B, C


def wolf_pack():
    A = ga()
    for k, (x, y, s) in enumerate(((6, 14, 0.55), (18, 14, 0.55), (12, 11, 0.8))):
        wolf_head(A, x, y, s, seed=k)
    B = ga()
    for k, (x, y) in enumerate(((5, 8), (5, 16), (11, 12))):
        B.solid(ellipse(x, y, 3.6, 1.8), SMOKE, base=2.4, seed=k)
        B.solid(circle(x + 3.4, y - 0.6, 1.6), SMOKE, base=3, seed=k + 3)
    foe(B, 19, 12, 1.2)
    C = ga()
    for k, x in enumerate((6, 12, 18)):
        C.energy(union(poly([(x - 2.6, 12), (x - 1.6, 7), (x, 10)]), poly([(x + 2.6, 12), (x + 1.6, 7), (x, 10)]), poly([(x - 2.6, 12), (x + 2.6, 12), (x, 17)])), SMOKE[:5] + [STEEL[5]], falloff=0.9)
    return A, B, C


def winter_wolf():
    A = ga(BG_I)
    wolf_head(A, 12, 12, 1.1, rmp=R("0a1a2a", "1a3a5a", "2a5a8a", "5a8ab8", "a0c8e8", "e0f4ff"), eyes=ICE)
    B = ga(BG_I)
    wolf_head(B, 8, 10, 0.7)
    for k in range(4):
        B.solid(shard(15 + k * 2, 12 + k * 2, 30, 3, 1), ICE, base=4.4, seed=k)
    foe(B, 19, 17, 0.9)
    C = ga(BG_I)
    C.energy(union(poly([(6, 12), (8, 3), (11, 9)]), poly([(18, 12), (16, 3), (13, 9)]), poly([(6, 12), (18, 12), (12, 21)])), ICE, falloff=1.2)
    return A, B, C


def roots(ic, cx, by, s=1.0, rmp=WOOD):
    for k, a in enumerate((-120, -90, -60)):
        r = math.radians(a)
        ic.solid(seg(cx + (k - 1) * 3 * s, by, cx + math.cos(r) * 11 * s, by + math.sin(r) * 13 * s, 1.4 * s, 0.4), rmp, base=2.6, seed=k)


def healing_wisps():
    A = ga(BG_L, (12, 16))
    roots(A, 12, 23, 1.0, rmp=OLIVE)
    wisp(A, 18, 8, 3, LIFE)
    B = ga(BG_L)
    B.solid(ellipse(12, 13, 3.4, 6.5), LEATHER, base=2.6)
    for a in (-60, 60, 180):
        r = math.radians(a)
        wisp(B, 12 + math.cos(r) * 8, 13 + math.sin(r) * 8, 2.2, LIFE)
    C = ga(BG_L)
    C.energy(drop(12, 14, 6.4), LIFE, falloff=3)
    C.energy(poly([(9, 15), (12, 11), (15, 15)]), PAPER, falloff=0.7)
    return A, B, C


def poison_ivy():
    A = ga(BG_W, (12, 16))
    roots(A, 12, 23, 1.0, rmp=OLIVE)
    for x, y in ((7, 9), (17, 8), (12, 4)):
        A.solid(ellipse(x, y, 2.4, 1.4, 30), TOXIC, base=3.4)
    B = ga(BG_W, (12, 16))
    foe(B, 12, 11, 1.3)
    roots(B, 12, 23, 0.9, rmp=OLIVE)
    for x, y in ((6, 5), (18, 4)):
        B.energy(circle(x, y, 2), TOXIC, falloff=1.6)
    C = ga(BG_W)
    C.energy(union(ellipse(8, 12, 4.4, 2.4, -30), ellipse(16, 12, 4.4, 2.4, 30), ellipse(12, 8, 2.4, 4.4)), TOXIC, falloff=1.2)
    C.energy(seg(12, 13, 12, 21, 0.6), OLIVE, falloff=0.5)
    return A, B, C


def gust(ic, cx, cy, r, rmp=SPIRIT, a0=180, w=1.1):
    ic.energy(arc(cx, cy, r, w, a0, a0 + 230), rmp, falloff=0.7)
    ic.energy(arc(cx + r * 0.4, cy, r * 0.55, w * 0.8, a0 + 60, a0 + 260), rmp, falloff=0.6)


def winter_winds():
    A = ga(BG_I)
    gust(A, 10, 12, 7)
    snowflake(A, 18, 17, 3.4, w=0.4)
    B = ga(BG_I)
    for y in (6, 12, 18):
        B.streak(0, y, 16, y - 2, 0.8, SPIRIT)
    foe(B, 19, 12, 1.1)
    B.solid(shard(16, 8, 0, 4, 1.1), ICE, base=4.4)
    C = ga(BG_I)
    for k in range(3):
        C.energy(union(seg(3, 6 + k * 6, 16, 6 + k * 6, 0.8), arc(16, 4 + k * 6, 2, 0.8, -90, 90)), ICE, falloff=0.6)
    return A, B, C


def wind_runner():
    A = ga(BG_S)
    boot(A, 13, 12, 0.85, wing=SPIRIT)
    gust(A, 6, 19, 3.4, w=0.7)
    B = ga(BG_S)
    B.solid(ellipse(12, 12, 3, 6), LEATHER, base=2.6)
    for a in range(0, 360, 60):
        r = math.radians(a)
        B.streak(12 + math.cos(r) * 6, 12 + math.sin(r) * 6, 12 + math.cos(r) * 11, 12 + math.sin(r) * 11, 0.9, SPIRIT)
    C = ga(BG_S)
    for k in range(4):
        a = k * 90
        C.energy(arc(12, 12, 8, 1.3, a, a + 60), SPIRIT, falloff=0.7)
        r = math.radians(a + 60)
        C.energy(circle(12 + math.cos(r) * 8, 12 + math.sin(r) * 8, 1.4), SPIRIT, falloff=1)
    return A, B, C


ORBS = {
    "ran_mark_pursuit": hot_pursuit, "ran_mark_kill": thrill_of_the_hunt, "ran_mark_big_game": big_game_hunter,
    "ran_trap_multiple": multiple_deploy, "ran_trap_bleeding": serrated_traps, "ran_trap_frost": frost_traps,
    "ran_rhythm_attack_speed": in_the_flow, "ran_rhythm_mana_cost": efficiency, "ran_rhythm_dash": momentum,
    "ran_survivalist_evasion": evasive_maneuver, "ran_survivalist_dash": tactical_maneuver, "ran_survivalist_regen": quick_recovery,
    "ran_rain_of_arrows_size": storm_of_arrows, "ran_rain_of_arrows_lightning": thundercaller,
    "archery_speed": fast_shot, "archery_frost_arrows": frost_arrows,
    "beasts_spirit_wolves_chain": relentless_hunters, "beasts_spirit_wolves_kills": restless_spirits,
    "beasts_wolf_pack": wolf_pack, "beasts_wolf_winter": winter_wolf,
    "nature_entangle_heal": healing_wisps, "nature_entangle_poison": poison_ivy,
    "nature_wind_weaver_winter": winter_winds, "nature_wind_weaver_dash": wind_runner,
}


# second pass: a front-facing wolf head, bigger arrows
def wolf(ic, cx, cy, s=1.0, rmp=SMOKE, eyes=SPIRIT, seed=0):
    P = lambda pts: poly([(cx + u * s, cy + v * s) for u, v in pts])
    ic.solid(P([(-7, -9), (-3, -4), (3, -4), (7, -9), (8, -1), (6, 3), (2.4, 9), (0, 10), (-2.4, 9), (-6, 3), (-8, -1)]), rmp, base=2.6, seed=seed)
    ic.solid(P([(-6, -7.6), (-3.6, -4.4), (-5.6, -3)]), rmp[:2] + rmp[1:], base=1.2, seed=seed + 1)
    ic.solid(P([(6, -7.6), (3.6, -4.4), (5.6, -3)]), rmp[:2] + rmp[1:], base=1.2, seed=seed + 2)
    ic.solid(P([(-2.6, 2), (2.6, 2), (1.6, 8), (0, 9), (-1.6, 8)]), rmp, base=3.6, seed=seed + 3)
    ic.solid(P([(-1.2, 7), (1.2, 7), (0, 8.8)]), SHADOW, base=1.2)
    for d in (-1, 1):
        ic.px([(int(cx + d * 3.2 * s), int(cy - 0.4 * s))], eyes[5] if len(eyes) > 5 else eyes[-1])
        ic.px([(int(cx + d * 3.2 * s - d), int(cy - 0.4 * s))], eyes[4])


GHOST = R("040c14", "0a2030", "16405a", "286a8a", "50a0c0", "a0e0f0")
FROST = R("0a1a2a", "1a3a5a", "2a5a8a", "5a8ab8", "a0c8e8", "e0f4ff")
_rh, _rs, _wp, _ww, _sa, _fs, _if, _md = (ORBS[k] for k in ("beasts_spirit_wolves_chain", "beasts_spirit_wolves_kills", "beasts_wolf_pack",
                                                          "beasts_wolf_winter", "ran_rain_of_arrows_size", "archery_speed",
                                                          "ran_rhythm_attack_speed", "ran_trap_multiple"))


def relentless_hunters():
    A, B, C = _rh()
    A = ga(BG_S)
    A.glow(12, 12, 11, SPIRIT[3], 0.5)
    wolf(A, 12, 12, 1.05, rmp=GHOST, eyes=PAPER)
    return A, B, C


def restless_spirits():
    A, B, C = _rs()
    A = ga(BG_S)
    skull(A, 7, 17, 0.6)
    A.glow(15, 9, 8, SPIRIT[3], 0.5)
    wolf(A, 15, 9, 0.7, rmp=GHOST, eyes=PAPER)
    return A, B, C


def wolf_pack():
    A, B, C = _wp()
    A = ga()
    wolf(A, 6, 13, 0.55, seed=1)
    wolf(A, 18, 13, 0.55, seed=2)
    wolf(A, 12, 11, 0.85)
    C = ga()
    for x in (5, 12, 19):
        C.energy(union(poly([(x - 3, 12), (x - 3.2, 6), (x - 0.8, 9)]), poly([(x + 3, 12), (x + 3.2, 6), (x + 0.8, 9)]), poly([(x - 3, 10), (x + 3, 10), (x, 17)])), STEEL, falloff=0.9)
    return A, B, C


def winter_wolf():
    A, B, C = _ww()
    A = ga(BG_I)
    wolf(A, 12, 12, 1.05, rmp=FROST, eyes=ICE)
    B = ga(BG_I)
    wolf(B, 8, 10, 0.65)
    for k in range(4):
        B.solid(shard(15 + k * 2, 13 + k * 2, 30, 3, 1), ICE, base=4.4, seed=k)
    return A, B, C


def storm_of_arrows():
    A, B, C = _sa()
    A = ga(light=(12, 16))
    for k, x in enumerate((5, 12, 19)):
        arrow(A, x, 9 + (k % 2) * 3, 100, 0.95)
    A.energy(ellipse(12, 21, 11, 2.2), STEEL, falloff=1)
    return A, B, C


def fast_shot():
    A, B, C = _fs()
    B = ga()
    for y in (5, 12, 19):
        arrow(B, 14, y, 0, 0.95)
        B.streak(0, y, 4, y, 0.5, SPIRIT)
    return A, B, C


def in_the_flow():
    A, B, C = _if()
    A = ga()
    bow(A, 13, 12, -45, 0.95)
    for k in range(3):
        A.energy(arc(11, 13, 9.5 + k * 1.4, 0.5, 110 + k * 12, 170 + k * 12), SPIRIT, falloff=0.4)
    B = ga()
    for k in range(3):
        arrow(B, 7 + k * 5, 15 - k * 3, -30, 0.85)
    return A, B, C


def multiple_deploy():
    A, B, C = _md()
    C = ga(light=(12, 16))
    for x, y in ((6, 9), (18, 9), (12, 18)):
        C.energy(union(*[poly([(x - 3 + j * 2, y), (x - 2 + j * 2, y - 4), (x - 1 + j * 2, y)]) for j in range(3)], box(x, y + 0.6, 3.6, 0.8)), STEEL, falloff=0.8)
    return A, B, C


ORBS.update({"beasts_spirit_wolves_chain": relentless_hunters, "beasts_spirit_wolves_kills": restless_spirits, "beasts_wolf_pack": wolf_pack,
             "beasts_wolf_winter": winter_wolf, "ran_rain_of_arrows_size": storm_of_arrows, "archery_speed": fast_shot,
             "ran_rhythm_attack_speed": in_the_flow, "ran_trap_multiple": multiple_deploy})
