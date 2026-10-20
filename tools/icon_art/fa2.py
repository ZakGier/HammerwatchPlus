"""The rest of the user-flagged Firearms icons, vanilla style, three ideas each."""
import math
from vpaint import *
from motifs import *
from fa import pineapple, canister, blast, shards

ELEMS = [FIRE, ICE, VOLT, TOXIC]


def rpg_jump():
    # A: the launcher aimed at the floor, its blast throwing it (and you) upward
    A = Icon().ground("140604", "3a1608", light=(12, 18))
    blast(A, 12, 21, 6.5, FIRE, 7)
    tube(A, 12, 9, -90, 0.85)
    for x in (5, 19):
        A.streak(x, 12, x, 2, 0.9, SMOKE)
    # B: a trooper flung skyward off a fireball
    B = Icon().ground("140804", "3a1a0a", light=(12, 18))
    B.rays(12, 22, EMBER, n=6, lo=0, hi=3)
    blast(B, 12, 22, 8, FIRE, 6)
    soldier(B, 12, 9, 0.95)
    # C: a boot print scorched into a blast star, abstract
    C = Icon().ground("100604", "2a1006", light=(12, 12))
    C.glow(12, 13, 12, "ff7020", 0.8)
    C.energy(lambda x, y: math.hypot(x - 12, y - 13) - 9 * (0.55 + 0.45 * abs(math.cos(math.atan2(y - 13, x - 12) * 4))), FIRE, falloff=5)
    C.solid(union(ellipse(12, 10, 3.6, 4.6), ellipse(12, 18, 3, 2.6)), EMBER[:3], base=0.5, spread=0.4, rim=1.2)
    C.streak(12, 23, 12, 1, 1.4, R("1a0604", "8a1e08", "ffa830", "fff0c0", "ffffff"))
    return A, B, C


def shrapnel():
    # A: a grenade casing cracked open, the four elements glowing through the cracks
    A = Icon().ground("0e0a18", "241a3a", light=(12, 12))
    pineapple(A, 12, 13.5, 8, 9.5, GUN, lever=False)
    for (pts, rm) in zip((((11, 6), (9, 10), (11, 13)), ((14, 8), (17, 11), (15, 15)), ((8, 15), (10, 18), (8, 21)), ((13, 16), (12, 19), (15, 22))), ELEMS):
        A.energy(union(*(seg(*pts[i], *pts[i + 1], 0.55) for i in range(2))), rm, falloff=0.9)
        A.glow(pts[1][0], pts[1][1], 4.5, rm[4], 0.6)
    # B: the blast throwing out fragments, each one burning a different element
    B = Icon().ground("0e0a18", "2a1e44", light=(12, 12))
    B.glow(12, 12, 9, "ffd090", 0.9)
    for k in range(8):
        a = math.radians(k * 45 + 20)
        x0, y0 = 12 + math.cos(a) * 4, 12 + math.sin(a) * 4
        x1, y1 = 12 + math.cos(a) * 11, 12 + math.sin(a) * 11
        B.streak(x0, y0, x1, y1, 1.6, ELEMS[k % 4])
    B.energy(circle(12, 12, 3), FIRE, falloff=3)
    # C: four shards meeting point to point, one per element
    C = Icon().ground("0c0a14", "221a34", light=(12, 12))
    for k, (rm, a) in enumerate(zip(ELEMS, (-90, 0, 90, 180))):
        r = math.radians(a)
        ux, uy = math.cos(r), math.sin(r)
        nx, ny = -uy, ux
        p = [(12 + ux * 10.5, 12 + uy * 10.5), (12 + ux * 3 + nx * 3, 12 + uy * 3 + ny * 3), (12 + ux * 0.6, 12 + uy * 0.6), (12 + ux * 3 - nx * 3, 12 + uy * 3 - ny * 3)]
        C.glow(12 + ux * 6, 12 + uy * 6, 6, rm[4], 0.5)
        C.solid(poly(p), rm, light=(-0.7, -0.7), seed=k, rim=1.4)
    return A, B, C


def exposure():
    # A: a skull wreathed in the four elemental flames
    A = Icon().ground("100808", "2a1414", light=(12, 12))
    for k, (x, rm, ln) in enumerate(((5, FIRE, -2), (9.5, VOLT, -1), (14.5, TOXIC, 1), (19, ICE, 2))):
        A.energy(flame(x, 22, 3.6, 18, ln, k), rm, falloff=2.4, seed=k)
    skull(A, 12, 13, 1.0, BONE, eyes=BLOOD)
    # B: a target's weak point lit up: a crit glint where four colours of light converge
    B = Icon().ground("0c0a14", "1e1a2e", light=(12, 12))
    for k, (rm, (x, y)) in enumerate(zip(ELEMS, ((1, 1), (23, 1), (23, 23), (1, 23)))):
        B.streak(x, y, 12 + (x - 12) * 0.12, 12 + (y - 12) * 0.12, 2.0, rm)
    B.glow(12, 12, 7, "ffffff", 0.9)
    B.energy(poly([(12, 5), (13.2, 10.8), (19, 12), (13.2, 13.2), (12, 19), (10.8, 13.2), (5, 12), (10.8, 10.8)]), GOLD, falloff=2.6)
    # C: an eye whose iris is split into the four elements
    C = Icon().ground("0c0a10", "201c28", light=(12, 10))
    f = lambda x, y: (abs((y - 12)) - 6.2 * max(0, 1 - ((x - 12) / 11.5) ** 2))
    C.solid(f, PAPER, base=3.6, spread=1, rim=0.3)
    for k, rm in enumerate(ELEMS):
        q = inter(f, circle(12, 12, 5.4), lambda x, y, k=k: -1 if int(((math.atan2(y - 12, x - 12) + math.pi) / (math.pi / 2))) % 4 == k else 1)
        C.solid(q, rm, base=3.4, spread=1.2, seed=k)
    C.paint(inter(f, ellipse(12, 12, 1.4, 3.4)), lambda x, y, d: BLACK)
    C.px([(10, 9)], WHITE)
    return A, B, C


def _bullet_bg(dark, mid, glowc, at=(15, 8)):
    ic = Icon().ground(dark, mid, light=at)
    ic.glow(at[0], at[1], 9, glowc, 0.7)
    return ic


def scavenger_blind():
    # A: a green-tipped round sweating poison
    A = _bullet_bg("06100a", "142a14", "3e8e1c")
    cartridge(A, 12, 13, -55, 1.35, tip=TOXIC)
    for (x, y, r) in ((6, 16, 1.4), (8, 20, 1.1), (4, 21, 0.9)):
        A.solid(circle(x, y, r), TOXIC, base=4)
    # B: the round bursts into a blinding green cloud, two eyes squeezed shut inside it
    B = Icon().ground("06100a", "1a3a14", light=(12, 12))
    for k, (x, y, r) in enumerate(((7, 9, 6), (16, 8, 6.5), (12, 15, 7), (5, 18, 5), (19, 18, 5))):
        B.solid(circle(x, y, r), TOXIC, base=3 + k * 0.1, spread=1.5, rim=1.2, seed=k)
    for x in (8, 16):
        B.solid(lambda X, Y, x=x: abs(Y - 13 - ((X - x) / 3.5) ** 2 * 2.2) - 0.7 if abs(X - x) < 3.5 else 1, TOXIC[:2], base=0.3, spread=0.2, rim=0, core=0)
    # C: a closed eye weeping a green tear
    C = Icon().ground("06100a", "142a14", light=(12, 8))
    lid = lambda x, y: abs(y - 9 - (1 - ((x - 12) / 9) ** 2) * 3.5) - 1.0 if abs(x - 12) < 9 else 1
    C.solid(lid, SKIN, base=3.6, spread=1)
    for k, x in enumerate((6, 9, 12, 15, 18)):
        yy = 9 + (1 - ((x - 12) / 9) ** 2) * 3.5
        C.solid(seg(x, yy + 1, x + (x - 12) * 0.25, yy + 3.6, 0.45), SKIN, base=2)
    C.energy(lambda x, y: math.hypot(x - 15, y - 18.5) - 2.4 + max(0, 18.5 - y) * 0.55, TOXIC, falloff=2)
    return A, B, C


def scavenger_slow():
    # A: the round sealed in a block of blue ice
    A = _bullet_bg("06101e", "102a4a", "3a8ad0", at=(12, 12))
    cartridge(A, 12, 12, -55, 1.2, tip=ICE)
    blk = box(12, 12, 8.5, 8.5, 12, 1.2)
    for y in range(N):
        for x in range(N):
            d = blk(x + 0.5, y + 0.5)
            if d <= 0:
                o = A.p[x, y]
                k = 0.55 if d > -1.1 else 0.3
                A.p[x, y] = mix(o, ICE[5] if d > -1.1 else ICE[3], k)
    A.px([(7, 6), (8, 5), (9, 4)], WHITE)
    # B: the round crawling, frost trailing behind it, the air crystallising
    B = Icon().ground("06101e", "123258", light=(16, 8))
    B.streak(1, 23, 14, 10, 2.6, ICE)
    slug(B, 16, 8, -45, 1.3, ICE)
    for (x, y) in ((6, 12), (10, 19), (19, 15), (4, 6)):
        B.energy(union(seg(x - 1.6, y, x + 1.6, y, 0.3), seg(x, y - 1.6, x, y + 1.6, 0.3)), ICE, falloff=0.6)
    # C: an hourglass of ice, the sand frozen mid-fall
    C = Icon().ground("06101e", "102a4a", light=(12, 12))
    C.solid(box(12, 3.4, 7, 1.2, 0, 0.4), WOOD, base=3)
    C.solid(box(12, 20.6, 7, 1.2, 0, 0.4), WOOD, base=2.4)
    C.solid(poly([(6, 4.5), (18, 4.5), (13, 12), (18, 19.5), (6, 19.5), (11, 12)]), ICE, base=3.6, spread=1.4, rim=1.2)
    C.solid(poly([(8, 6), (16, 6), (12, 11)]), ICE, base=5, spread=0.6)
    C.solid(poly([(9.5, 19), (14.5, 19), (12, 15.5)]), ICE, base=5, spread=0.6)
    return A, B, C


def scavenger_lightning():
    # A: a yellow round crackling with arcs
    A = _bullet_bg("141004", "2e2608", "e0c028", at=(12, 10))
    cartridge(A, 12, 13, -55, 1.35, tip=VOLT)
    for pts in (((17, 2), (15, 5), (18, 7), (16, 9)), ((4, 14), (7, 13), (5, 10)), ((19, 15), (21, 18), (19, 20))):
        A.energy(union(*(seg(*pts[i], *pts[i + 1], 0.45) for i in range(len(pts) - 1))), VOLT, falloff=0.6)
    # B: the shot is a bolt of lightning itself, a round at its head
    B = Icon().ground("100c02", "2a2206", light=(16, 8))
    pts = [(1, 23), (6, 18), (5, 15), (11, 12), (10, 9), (16, 7)]
    B.glow(10, 13, 11, "e0c028", 0.6)
    B.energy(union(*(seg(*pts[i], *pts[i + 1], 0.9, 0.6) for i in range(len(pts) - 1))), VOLT, falloff=1.0)
    slug(B, 18.5, 5.5, -40, 1.2, VOLT)
    # C: a bullet-shaped bolt, abstract
    C = Icon().ground("100c02", "2a2206", light=(12, 12))
    C.glow(12, 12, 11, "e0c028", 0.7)
    C.energy(poly([(14, 1), (19, 1), (14, 10), (18.5, 10), (8, 23), (11, 13), (6.5, 13)]), VOLT, falloff=2.4)
    return A, B, C


def myturret_shared():
    # A: the turret, its plating painted in all four team colours
    A = Icon().ground("061214", "123034", light=(10, 10))
    turret(A, 2, 4, 1.05)
    for k, c in enumerate(TEAMC):
        A.solid(box(6.5 + (k - 1.5) * 2.2 + 2.1, 9.9, 1.0, 0.8, 0, 0.2), [mix(c, BLACK, 0.6), mix(c, BLACK, 0.3), c, mix(c, WHITE, 0.4)], base=2)
    # B: four hands of light reaching to it from the corners
    B = Icon().ground("040c0c", "0e2224", light=(12, 12))
    for c, (x, y) in zip(TEAMC, ((1, 1), (23, 1), (23, 23), (1, 23))):
        B.glow(x, y, 10, c, 0.8)
        B.streak(x, y, 12 + (x - 12) * 0.25, 12 + (y - 12) * 0.25, 1.6, [mix(c, BLACK, 0.8), mix(c, BLACK, 0.5), c, mix(c, WHITE, 0.5), WHITE])
    turret(B, 3, 5, 0.95)
    # C: four shields locked edge to edge, the turret on top
    C = Icon().ground("061214", "123034", light=(12, 12))
    for k, c in enumerate(TEAMC):
        qx, qy = (k % 2), (k // 2)
        q = inter(circle(12, 12, 10.5), box(6.5 + qx * 11, 6.5 + qy * 11, 5.5, 5.5, 0, 0))
        C.solid(q, [mix(c, BLACK, 0.85), mix(c, BLACK, 0.65), mix(c, BLACK, 0.45), mix(c, BLACK, 0.25)], seed=k)
    turret(C, 3, 4, 0.95)
    return A, B, C


def boom_headshot():
    # A: through the scope: the head in the cross hairs, the scope's black ring
    A = Icon().ground("3a3e2a", "6a7050", light=(12, 8))
    head(A, 12, 11, 0.95, R("101010", "1e1c1c", "2e2a2a", "403a3a"))
    for y in range(N):
        for x in range(N):
            if math.hypot(x - 11.5, y - 11.5) > 10.6:
                A.p[x, y] = BLACK
    A.paint(union(box(12, 11, 11, 0.4), box(12, 11, 0.4, 11)), lambda x, y, d: BLACK if abs(x - 11.5) > 1.6 or abs(y - 10.5) > 1.6 else None)
    A.energy(circle(12, 11, 0.8), BLOOD, falloff=0.8)
    # B: the shot lands: the head snaps back in a gold burst
    B = Icon().ground("140c04", "2e1e0a", light=(12, 8))
    head(B, 11, 12, 1.0, GUN)
    B.glow(13, 9, 9, "ffd060", 0.9)
    B.energy(lambda x, y: math.hypot(x - 13, y - 9) - 5.5 * (0.5 + 0.5 * abs(math.cos(math.atan2(y - 9, x - 13) * 3))), GOLD, falloff=3)
    # C: a gold crosshair locked on a head, abstract
    C = Icon().ground("0e0a06", "241c0e", light=(12, 12))
    head(C, 12, 12, 0.95, R("100c08", "1e1810", "2e2618", "3e3420"))
    C.energy(cut(union(ring(12, 11, 6.2, 1.3), box(12, 11, 9.5, 0.55), box(12, 11, 0.55, 9.5)), circle(12, 11, 2.2)), GOLD, falloff=0.8)
    C.energy(circle(12, 11, 0.9), BLOOD, falloff=0.9)
    return A, B, C


def overpacked():
    # A: a bundle far too fat, sticks crammed together, rope straining
    A = Icon().ground("140604", "34100a", light=(12, 6))
    for k, x in enumerate((3, 6.3, 9.6, 12.9, 16.2, 19.5)):
        dyn(A, x, 15 + (k % 2) * 0.8, -90, 1.0, seed=k, length=17, w=1.65)
    for k, x in enumerate((4.6, 7.9, 11.2, 14.5, 17.8)):
        dyn(A, x, 6.5, -90, 1.0, seed=10 + k, length=6, w=1.65)
    A.solid(box(11.5, 15, 10.5, 1.0, 0, 0.3), WOOD, base=1.6, spread=0.5)
    A.glow(12, 1, 6, "ffa040", 0.8)
    A.energy(circle(12, 1.5, 1.2), FIRE, falloff=1.2)
    # B: a sheaf bursting out of its strap, splayed like a fan
    B = Icon().ground("140604", "34100a", light=(12, 6))
    B.glow(12, 5, 11, "ff7020", 0.6)
    for k, a in enumerate((-50, -34, -18, -2, 14, 30, 46)):
        r = math.radians(a - 90)
        dyn(B, 12 + math.cos(r) * 10, 24 + math.sin(r) * 10, a - 90, 1.0, seed=k, length=14, w=1.6)
    B.solid(box(12, 19.5, 5, 1.4, 0, 0.4), GUN, base=2.6)
    # C: the backpack's worth: an endless stack of crates of TNT vanishing upward
    C = Icon().ground("120604", "2a0e06", light=(12, 16))
    for k, (y, s) in enumerate(((18, 1.0), (10, 0.78), (4, 0.6))):
        w = 9 * s
        crate(C, 12 - w, y - 3.5 * s, 12 + w, y + 3.5 * s, seed=k)
        C.solid(box(12, y + 0.3 * s, 3.2 * s, 1.2 * s, 0, 0.2), RED, base=3)
    C.shade(lambda x, y: -1 if y < 8 else 1, 0.6)
    return A, B, C


def magic_missile():
    # A: the rocket: an ice-crusted nose, a burning tail, on a split ground
    A = Icon()
    for y in range(N):
        for x in range(N):
            A.p[x, y] = (8, 10, 12)
    A.ground("06101e", "123258", light=(18, 6))
    A.shade(lambda x, y: (x + y) - 23, 1.0)
    for y in range(N):
        for x in range(N):
            if x + y > 23:
                v = 0.5 + grain(x, y, 4) * 0.4 - math.hypot(x - 6, y - 18) / 24
                A.p[x, y] = pick(EMBER, v * 3)
    A.energy(flame(5, 20, 3, 9, 0, 3), FIRE, falloff=2) if False else None
    rocket(A, 12, 12, -45, 1.05, nose=ICE, body=GUN, band=GOLD)
    A.energy(lambda x, y: math.hypot(x - 4.5, y - 19.5) - 3.2, FIRE, falloff=2.4)
    # B: the blast: a burst of ice that turns to fire at its edge
    B = Icon().ground("0a0a14", "1e1a2a", light=(12, 12))
    B.glow(12, 12, 13, "ff6010", 0.7)
    B.energy(lambda x, y: math.hypot(x - 12, y - 12) - 10 * (0.65 + 0.35 * abs(math.cos(math.atan2(y - 12, x - 12) * 4))), FIRE, falloff=4)
    B.energy(lambda x, y: math.hypot(x - 12, y - 12) - 6 * (0.6 + 0.4 * abs(math.cos(math.atan2(y - 12, x - 12) * 3 + 0.5))), ICE, falloff=4)
    # C: a spiral of frost and flame chasing each other
    C = Icon().ground("08080e", "1a1824", light=(12, 12))
    for rm, off in ((FIRE, 0), (ICE, math.pi)):
        pts = [(12 + math.cos(off + t * 0.9) * t * 0.85, 12 + math.sin(off + t * 0.9) * t * 0.85) for t in [i * 0.5 for i in range(1, 25)]]
        for i in range(len(pts) - 1):
            C.energy(seg(*pts[i], *pts[i + 1], 0.25 + i * 0.06), rm, falloff=0.4 + i * 0.05)
    return A, B, C


def hoarder():
    # A: the ammo crate brimming: grenades and rocket noses piled over its rim
    A = Icon().ground("140e06", "2e220e", light=(12, 6))
    rocket(A, 17, 7.5, -80, 0.75, fins=False)
    rocket(A, 6, 8.5, -100, 0.65, fins=False)
    for k, (x, y) in enumerate(((5, 12), (10, 11), (15, 12), (19.5, 11.5), (8, 8.2), (13, 8))):
        pineapple(A, x, y, 2.8, 3.1, OLIVE, seed=k, lever=False)
    crate(A, 1.5, 14, 22.5, 23.5)
    A.solid(box(12, 18.5, 3, 1.2, 0, 0.2), GOLD, base=3)
    # B: a bandolier wrapped around the frame, every loop filled with a different explosive
    B = Icon().ground("140e06", "2e220e", light=(12, 12))
    B.solid(seg(-2, 21, 26, 3, 2.6), WOOD, base=2.2, spread=1)
    for k in range(6):
        t = 0.08 + k * 0.17
        x, y = -2 + 28 * t, 21 - 18 * t
        if k % 3 == 0:
            pineapple(B, x, y - 2, 2.6, 3, OLIVE, seed=k, lever=False)
        elif k % 3 == 1:
            rocket(B, x, y - 3, -90, 0.5, fins=False)
        else:
            cut40(B, x, y - 2, -90, 0.6)
    # C: one bulging duffel bag, rocket fins and pins poking out of the zip
    C = Icon().ground("140e06", "2a1e0c", light=(12, 8))
    rocket(C, 8, 6, -110, 0.6, fins=True)
    rocket(C, 15, 5, -70, 0.6, fins=True)
    C.solid(ellipse(12, 15, 10.5, 7.5), OLIVE, seed=3)
    C.solid(box(12, 9.2, 7.5, 0.6, 0, 0.2), GUN, base=1.6)
    C.solid(seg(4, 12, 20, 12, 0.5), OLIVE, base=1.4, spread=0.3, rim=0)
    return A, B, C


def over_reload():
    # A: a mag overflowing: golden rounds spilling out of its lips
    A = Icon().ground("140e04", "34280a", light=(12, 4))
    A.glow(12, 5, 10, "ffd060", 0.8)
    mag(A, 12, 16, 0, 1.0, GUN, h=13, w=4, top_round=False)
    for k, (x, y, a) in enumerate(((12, 7, -90), (9, 4.5, -120), (15, 4, -60), (7, 1.5, -150), (17.5, 1.5, -30))):
        cartridge(A, x, y, a, 0.6, tip=GOLD, case=GOLD, seed=k, w=2.6, length=9)
    # B: the reload ring with its gold mark struck dead centre
    B = Icon().ground("0e0a04", "241c0a", light=(12, 12))
    B.solid(ring(12, 12, 9.4, 2.2), GUN, base=2)
    B.energy(inter(ring(12, 12, 9.4, 2.4), lambda x, y: abs(math.atan2(y - 12, x - 12) + 1.57) - 0.45), GOLD, falloff=1.2)
    B.glow(12, 3, 6, "ffe070", 0.9)
    mag(B, 12, 13, 0, 0.75, GUN, h=12, w=4, top_round=False)
    # C: a single golden round, glowing as if it were treasure
    C = Icon().ground("100c04", "2a2208", light=(12, 12))
    C.glow(12, 12, 11, "ffd060", 0.9)
    cartridge(C, 12, 12.5, -60, 1.6, tip=GOLD, case=GOLD)
    C.glint(17, 5)
    return A, B, C


FA2 = {f.__name__: f for f in (rpg_jump, shrapnel, exposure, scavenger_blind, scavenger_slow, scavenger_lightning,
                              myturret_shared, boom_headshot, overpacked, magic_missile, hoarder, over_reload)}
