"""Warrior orb icons: A the gear up close, B the moment it happens, C an abstract mark."""
from vm import *

BG = ("120a06", "2c180c")
BG_F = ("140604", "2e1006")
BG_R = ("140406", "2e0a10")
BG_Y = ("100c04", "262008")
BG_I = ("06101e", "0e2440")
BG_S = ("0a0c12", "1c2230")


def ga(c=BG, light=(12, 12)):
    return G(c[0], c[1], light)


def foe(ic, x, y, s=1.0):
    ic.solid(ellipse(x, y, 2.6 * s, 3.6 * s), SHADOW, base=2.2)


def spin(ic, cx, cy, r, rmp=STEEL, w=1.0):
    for k in range(3):
        ic.energy(arc(cx, cy, r, w, k * 120, k * 120 + 70), rmp, falloff=0.6)


def revolving_axes():
    A = ga()
    axe(A, 12, 12, -60, 1.1)
    A.energy(arc(12, 12, 10.5, 0.8, 150, 330), STEEL, falloff=0.5)
    A.energy(poly([(1, 13), (3, 9), (5, 13)]), STEEL, falloff=0.5)
    B = ga()
    B.solid(ellipse(12, 13, 3.2, 6), LEATHER, base=2.6)
    for a in (-30, 150):
        r = math.radians(a)
        axe(B, 12 + math.cos(r) * 8, 13 + math.sin(r) * 8, a + 90, 0.5)
    B.energy(ring(12, 13, 8, 0.5), STEEL, falloff=0.4)
    C = ga()
    C.energy(arc(12, 12, 8.5, 1.6, 90, 400), STEEL, falloff=0.9)
    C.energy(poly([(9, 21), (14, 18), (14, 24)]), STEEL, falloff=0.9)
    C.energy(poly([(9, 8), (16, 8), (15, 15), (12, 12)]), STEEL, falloff=0.9)
    return A, B, C


def burning_axes():
    A = ga(BG_F)
    axe(A, 12, 12, -60, 1.1, head=FIRE)
    B = ga(BG_F)
    B.solid(ellipse(12, 13, 3.2, 6), LEATHER, base=2.6)
    spin(B, 12, 13, 9, FIRE, 1.2)
    C = ga(BG_F)
    C.energy(poly([(7, 6), (17, 4), (18, 14), (12, 11), (9, 15)]), FIRE, falloff=1.2)
    C.energy(seg(9, 13, 5, 22, 0.8), FIRE, falloff=0.6)
    return A, B, C


def culling_axes():
    A = ga(BG_R)
    axe(A, 12, 12, -60, 1.1, head=STEEL)
    skull(A, 17, 18, 0.45)
    B = ga(BG_R)
    skull(B, 12, 13, 0.85)
    B.solid(seg(3, 3, 21, 21, 0.9), CRIMSON, base=3.4)
    C = ga(BG_R)
    C.energy(cut(heart(12, 13, 7.5), heart(12, 13.5, 5.0)), CRIMSON, falloff=1.2)
    C.energy(inter(heart(12, 13.5, 5.0), box(12, 18, 8, 2.4)), CRIMSON, falloff=1)
    C.energy(seg(3, 3, 21, 21, 0.7), STEEL, falloff=0.6)
    return A, B, C


def horn(ic, cx, cy, s=1.0):
    ic.solid(poly([(cx - 8 * s, cy + 3 * s), (cx - 1 * s, cy - 1 * s), (cx + 6 * s, cy - 6 * s), (cx + 7.6 * s, cy - 3.4 * s), (cx + 1 * s, cy + 3 * s), (cx - 7 * s, cy + 5.6 * s)]), BONE, base=2.6)
    ic.solid(ellipse(cx + 6.8 * s, cy - 4.8 * s, 1.6 * s, 2.6 * s, -35), BONE, base=3.6, seed=3)


def cry(ic, cx, cy, rmp, n=3, a0=-40, a1=40):
    for k in range(n):
        ic.energy(arc(cx, cy, 4 + k * 3.4, 1.0, a0, a1), rmp, falloff=0.6)


def intimidating_cry():
    A = ga(BG_R)
    horn(A, 9, 15, 0.95)
    cry(A, 14, 9, CRIMSON, 2, -70, 10)
    B = ga(BG_R)
    B.solid(ellipse(6, 13, 3.4, 6.5), LEATHER, base=2.6)
    cry(B, 7, 12, CRIMSON, 2)
    for y in (6, 18):
        foe(B, 19, y, 0.9)
        B.energy(poly([(19, y - 1), (21, y + 1), (17, y + 1)]), CRIMSON, falloff=0.6) if False else None
    B.energy(poly([(17, 10), (21, 10), (19, 14)]), CRIMSON, falloff=0.6)
    C = ga(BG_R)
    cry(C, 3, 12, CRIMSON, 3)
    C.energy(poly([(16, 9), (22, 9), (19, 15)]), CRIMSON, falloff=0.8)
    return A, B, C


def second_wind():
    A = ga(("041004", "0e2a10"))
    horn(A, 10, 13, 0.95)
    A.solid(heart(17, 6, 3.0), CRIMSON, base=3.4)
    B = ga(("041004", "0e2a10"))
    B.solid(heart(12, 13, 5.6), CRIMSON, base=3.4)
    cry(B, 12, 13, LIFE, 2, 200, 340)
    C = ga(("041004", "0e2a10"))
    C.energy(cut(heart(12, 13, 7.5), heart(12, 13.5, 4.8)), CRIMSON, falloff=1.2)
    cry(C, 12, 13, LIFE, 1, 210, 330)
    return A, B, C


def battle_cry():
    A = ga()
    horn(A, 10, 14, 0.95)
    for k in range(3):
        A.energy(poly([(13 + k * 3.4, 4), (15 + k * 3.4, 4), (14 + k * 3.4, 9)]), CRIMSON, falloff=0.6)
    B = ga()
    B.solid(ellipse(12, 13, 3.4, 6.5), LEATHER, base=2.6)
    for a in (200, 260, 320, 20, 140):
        r = math.radians(a)
        foe(B, 12 + math.cos(r) * 9, 13 + math.sin(r) * 9, 0.6)
    cry(B, 12, 13, CRIMSON, 1, 0, 360)
    C = ga()
    for k in range(4):
        C.energy(box(6 + k * 4, 12, 0.9, 6, 12, 0.3), CRIMSON, falloff=0.6)
    cry(C, 12, 12, HOLY, 1, 200, 340)
    return A, B, C


def combat_training():
    A = ga()
    sword(A, 12, 12, -45, 1.1)
    B = ga()
    sword(B, 8, 14, -45, 0.75)
    sword(B, 16, 14, -135, 0.75)
    flash(B, 12, 8, 2.4, HOLY)
    C = ga()
    C.energy(union(seg(4, 20, 20, 4, 1.3, 0.3), seg(4, 4, 20, 20, 1.3, 0.3)), STEEL, falloff=0.9)
    return A, B, C


def toughness():
    A = ga(BG_S)
    A.solid(box(12, 13, 7, 8, 0, 2.8), STEEL, base=2.6)
    A.shade(box(12, 13, 0.5, 8), 0.5)
    for x, y in ((8, 9), (16, 9), (8, 17), (16, 17)):
        A.solid(circle(x, y, 1), BRASS, base=3.6)
    B = ga(BG_S)
    B.solid(ellipse(12, 13, 4, 7), STEEL, base=2.6)
    for a in (200, 300, 30):
        r = math.radians(a)
        B.streak(12 + math.cos(r) * 13, 13 + math.sin(r) * 13, 12 + math.cos(r) * 7.5, 13 + math.sin(r) * 7.5, 0.8, CRIMSON)
        flash(B, 12 + math.cos(r) * 6.5, 13 + math.sin(r) * 6.5, 1.4, STEEL)
    C = ga(BG_S)
    C.energy(poly([(12, 3), (20, 6), (19, 15), (12, 21), (5, 15), (4, 6)]), STEEL, falloff=2.4)
    C.energy(poly([(9, 9), (15, 9), (12, 14)]), CRIMSON, falloff=0.7)
    return A, B, C


def mighty_strength():
    A = ga()
    hammer(A, 12, 12, -60, 1.2)
    B = ga()
    B.solid(box(16, 12, 3, 8, 0, 0.6), STEEL, base=2.4)
    B.paint(union(seg(16, 4, 15, 12, 0.4), seg(15, 12, 18, 18, 0.4)), lambda x, y, d: STEEL[0])
    hammer(B, 8, 15, -30, 0.7)
    C = ga()
    C.energy(poly([(2, 12), (16, 6), (14, 11), (22, 12), (14, 13), (16, 18)]), STEEL, falloff=1.1)
    return A, B, C


def brutality():
    A = ga(BG_R)
    axe(A, 12, 12, -60, 1.1, head=CRIMSON)
    B = ga(BG_R)
    foe(B, 12, 13, 1.5)
    slash(B, 12, 12, 9, 200, 320, CRIMSON)
    B.energy(star(12, 12, 1.2, 4, 4), HOLY, falloff=1)
    C = ga(BG_R)
    for k in range(3):
        C.energy(seg(5 + k * 5, 4, 9 + k * 5, 20, 1.1, 0.3), CRIMSON, falloff=0.8)
    C.energy(star(19, 18, 1, 3, 4), HOLY, falloff=1)
    return A, B, C


def killer_physique():
    A = ga(("041004", "0e2a10"))
    fist(A, 12, 13, 1.1)
    A.energy(poly([(16, 6), (19, 2), (22, 6)]), LIFE, falloff=0.8)
    B = ga(("041004", "0e2a10"))
    skull(B, 7, 15, 0.6)
    B.solid(heart(17, 9, 4), CRIMSON, base=3.4)
    B.energy(poly([(14, 19), (17, 16), (20, 19)]), LIFE, falloff=0.8)
    C = ga(("041004", "0e2a10"))
    C.energy(cut(heart(12, 13, 7.5), heart(12, 13.5, 4.8)), LIFE, falloff=1.2)
    for k in range(3):
        C.energy(box(9 + k * 3, 12, 0.6, 2.6, 15), CRIMSON, falloff=0.6)
    return A, B, C


def dauntless():
    A = ga()
    shield(A, 9, 13, 0.85, STEEL, face=CRIMSON)
    sword(A, 16, 10, -45, 0.7)
    B = ga()
    B.solid(ellipse(14, 13, 8, 8.5), SHADOW, base=2.4)
    for d in (-1, 1):
        B.solid(poly([(14 + d * 3, 7), (14 + d * 8, 1), (14 + d * 6, 8)]), BONE, base=3.2)
    sword(B, 6, 15, -45, 0.6)
    flash(B, 9, 12, 2, HOLY)
    C = ga()
    C.energy(poly([(12, 3), (20, 6), (19, 15), (12, 21), (5, 15), (4, 6)]), CRIMSON, falloff=2)
    C.energy(poly([(6, 9), (8, 5), (10, 8), (12, 4), (14, 8), (16, 5), (18, 9)]), GOLD, falloff=0.8)
    return A, B, C


def trembling_impact():
    A = ga(BG, (12, 16))
    hammer(A, 12, 10, -90, 0.9)
    for k in range(3):
        A.energy(arc(12, 21, 4 + k * 3.4, 0.8, 190, 350), EARTH, falloff=0.6)
    B = ga(BG, (12, 16))
    B.solid(ellipse(12, 19, 11, 3.4), EARTH, base=2)
    for x, y in ((5, 18), (12, 20), (19, 18)):
        B.solid(poly([(x - 2.4, y), (x - 0.6, y - 6), (x + 1.4, y - 4), (x + 2.4, y)]), EARTH, base=3.4, seed=x)
    C = ga()
    C.energy(union(seg(2, 14, 6, 9, 0.9), seg(6, 9, 10, 17, 0.9), seg(10, 17, 14, 7, 0.9), seg(14, 7, 18, 15, 0.9), seg(18, 15, 22, 11, 0.9)), EARTH, falloff=0.8)
    return A, B, C


def fiery_leap():
    A = ga(BG_F)
    boot(A, 13, 9, 0.85)
    for k, x in enumerate((5, 10, 15, 20)):
        A.energy(flame(x, 23, 2.4, 6 + (k % 2) * 3, 0, k), FIRE, falloff=1.4)
    B = ga(BG_F)
    B.energy(arc(12, 18, 9, 0.7, 190, 350), SMOKE, falloff=0.5)
    for x in (4, 20):
        B.energy(flame(x, 21, 2.4, 9, 0, x), FIRE, falloff=1.3)
    B.solid(ellipse(12, 7, 2.6, 4), LEATHER, base=2.6)
    C = ga(BG_F)
    C.energy(arc(12, 18, 8, 1.3, 190, 350), FIRE, falloff=0.8)
    for x in (4, 20):
        C.energy(flame(x, 21, 2.2, 8, 0, x), FIRE, falloff=1.2)
    return A, B, C


def unyielding_rage():
    A = ga(BG_R)
    A.solid(heart(12, 12, 6.2), SMOKE, base=1.8)
    A.solid(inter(heart(12, 12, 6.2), box(12, 18, 12, 3)), CRIMSON, base=3.2)
    A.energy(flame(12, 9, 2.6, 8, 0, 1), FIRE, falloff=1.2)
    B = ga(BG_R)
    B.solid(ellipse(12, 13, 3.6, 6.6), CRIMSON, base=2.6)
    B.glow(12, 13, 10, CRIMSON[4], 0.6)
    for a in (210, 270, 330):
        r = math.radians(a)
        B.streak(12 + math.cos(r) * 12, 13 + math.sin(r) * 12, 12 + math.cos(r) * 8, 13 + math.sin(r) * 8, 0.8, STEEL)
    C = ga(BG_R)
    C.energy(poly([(12, 3), (20, 6), (19, 15), (12, 21), (5, 15), (4, 6)]), CRIMSON, falloff=2.4)
    C.energy(box(12, 17, 5, 1.2), FIRE, falloff=0.8)
    return A, B, C


def furious_cry():
    A = ga(BG_R)
    horn(A, 10, 14, 0.95)
    A.energy(flame(17, 10, 2.4, 8, 0.4, 2), FIRE, falloff=1.2)
    B = ga(BG_R)
    B.solid(ellipse(12, 13, 3.6, 6.6), CRIMSON, base=2.6)
    cry(B, 12, 13, FIRE, 2, 200, 340)
    hourglass(B, 20, 19, 0.35, sand=FIRE)
    C = ga(BG_R)
    cry(C, 3, 12, FIRE, 3)
    C.energy(arc(18, 12, 4, 1.0, 90, 360), CRIMSON, falloff=0.6)
    return A, B, C


def totem(ic, cx, by, s=1.0, rmp=WOOD, eyes=VOLT):
    ic.solid(box(cx, by - 8 * s, 3.4 * s, 8 * s, 0, 0.8 * s), rmp, base=2.6)
    for k in range(3):
        ic.solid(box(cx, by - 3 * s - k * 5 * s, 3.8 * s, 0.6 * s), rmp, base=1.6, seed=k)
    for d in (-1, 1):
        ic.energy(circle(cx + d * 1.6 * s, by - 12 * s, 0.7 * s), eyes, falloff=0.6)
    ic.solid(union(poly([(cx - 3.4 * s, by - 15 * s), (cx - 6 * s, by - 18 * s), (cx - 2 * s, by - 16 * s)]), poly([(cx + 3.4 * s, by - 15 * s), (cx + 6 * s, by - 18 * s), (cx + 2 * s, by - 16 * s)])), BONE, base=3.2)


def shock_totems():
    A = ga(BG_Y, (12, 16))
    totem(A, 12, 22, 1.1)
    bolt(A, [(5, 6), (3, 10), (6, 12)], w=0.5)
    bolt(A, [(19, 6), (21, 10), (18, 12)], w=0.5)
    B = ga(BG_Y, (12, 16))
    totem(B, 6, 22, 0.75)
    totem(B, 18, 22, 0.75)
    bolt(B, [(6, 10), (12, 8), (18, 10)], w=0.7)
    C = ga(BG_Y)
    C.energy(box(12, 14, 3.4, 8, 0, 0.6), VOLT, falloff=1)
    C.paint(box(12, 14, 1.4, 6), lambda x, y, d: None)
    bolt(C, [(13, 2), (11, 5), (13, 6)], w=0.6)
    return A, B, C


def frostbite_totems():
    A = ga(BG_I, (12, 16))
    totem(A, 12, 22, 1.1, rmp=R("0a1a2a", "1a3a5a", "2a5a8a", "5a8ab8", "a0c8e8", "e0f4ff"), eyes=ICE)
    B = ga(BG_I, (12, 16))
    totem(B, 6, 22, 0.75, eyes=ICE)
    B.solid(box(17, 15, 4, 6, 0, 1), ICE, base=4, seed=2)
    foe(B, 17, 15, 0.9)
    C = ga(BG_I)
    C.energy(box(12, 14, 3.4, 8, 0, 0.6), ICE, falloff=1)
    C.paint(box(12, 14, 1.4, 6), lambda x, y, d: None)
    snowflake(C, 12, 4, 2.8, w=0.4)
    return A, B, C


def tempest_strikes():
    A = ga(BG_Y)
    sword(A, 12, 12, -45, 1.05, blade=VOLT)
    B = ga(BG_Y)
    foe(B, 8, 13, 1.2)
    foe(B, 19, 9, 0.9)
    slash(B, 8, 13, 6, 200, 320, STEEL)
    bolt(B, [(10, 10), (14, 11), (17, 9)], w=0.6)
    C = ga(BG_Y)
    C.energy(seg(3, 21, 15, 9, 1.2, 0.4), STEEL, falloff=0.8)
    bolt(C, [(18, 2), (15, 8), (19, 9), (16, 16)], w=0.8)
    return A, B, C


def glacial_strikes():
    A = ga(BG_I)
    sword(A, 12, 12, -45, 1.05, blade=ICE)
    B = ga(BG_I)
    foe(B, 13, 13, 1.3)
    for k in range(6):
        a = k * 60 + 15
        r = math.radians(a)
        B.solid(shard(13 + math.cos(r) * 6, 13 + math.sin(r) * 6, a, 4, 1.2), ICE, base=4.4, seed=k)
    C = ga(BG_I)
    C.energy(seg(3, 21, 13, 11, 1.2, 0.4), STEEL, falloff=0.8)
    snowflake(C, 16, 8, 5, w=0.6)
    return A, B, C


def barbed_chains():
    A = ga(BG_R)
    chain(A, 3, 20, 20, 4)
    for x, y in ((7, 16), (12, 11), (17, 7)):
        A.solid(poly([(x - 1, y - 1), (x - 2.6, y - 3.6), (x + 1, y)]), STEEL, base=3.6)
    B = ga(BG_R)
    foe(B, 16, 12, 1.3)
    chain(B, 2, 18, 13, 13)
    for x, y in ((14, 20), (19, 19)):
        B.energy(drop(x, y, 1.6), BLOOD, falloff=1.2)
    C = ga(BG_R)
    for k in range(3):
        C.energy(cut(ellipse(5 + k * 7, 12, 3.6, 2.4), ellipse(5 + k * 7, 12, 2, 1)), STEEL, falloff=0.8)
    C.energy(drop(12, 19, 2), BLOOD, falloff=1.4)
    return A, B, C


def spiked_chains():
    A = ga(BG_S)
    chain(A, 3, 20, 14, 9)
    A.solid(star(17, 6, 1.6, 5, 4, rot=-45), STEEL, base=3.4)
    B = ga(BG_S)
    chain(B, 2, 20, 11, 11)
    for a in range(0, 360, 45):
        r = math.radians(a)
        B.solid(shard(13 + math.cos(r) * 6, 9 + math.sin(r) * 6, a, 4, 1), STEEL, base=3.6, seed=a)
    C = ga(BG_S)
    C.energy(star(12, 12, 2.4, 10, 8), STEEL, falloff=1.4)
    return A, B, C


def exploding_gibs():
    A = ga(BG_R)
    A.solid(box(12, 14, 6, 4, 20, 2), CRIMSON, base=2.6)
    A.solid(seg(10, 8, 13, 19, 1.1), BONE, base=3.2)
    A.solid(union(circle(9, 7, 1.6), circle(11.5, 7, 1.6)), BONE, base=3.2)
    B = ga(BG_R)
    flash(B, 12, 12, 5, BLOOD)
    for k in range(6):
        a = math.radians(k * 60 + 20)
        B.solid(ellipse(12 + math.cos(a) * 9, 12 + math.sin(a) * 9, 1.6, 1.0, k * 60), CRIMSON, base=3)
    C = ga(BG_R)
    C.energy(cut(star(12, 12, 4, 10, 8), circle(12, 12, 2.4)), BLOOD, falloff=1.2)
    return A, B, C


def slayer():
    A = ga(BG_R)
    axe(A, 12, 12, -60, 1.1)
    A.solid(box(18, 20, 4, 1.2), SMOKE, base=1.6)
    A.solid(box(16, 20, 2, 1.0), CRIMSON, base=3)
    B = ga(BG_R)
    B.solid(box(12, 6, 9, 2, 0, 0.6), SMOKE, base=1.6)
    B.solid(box(7, 6, 4, 1.6, 0, 0.5), CRIMSON, base=3.2)
    foe(B, 12, 16, 1.4)
    slash(B, 12, 15, 8, 200, 320, STEEL)
    C = ga(BG_R)
    C.energy(cut(circle(12, 12, 9), circle(12, 12, 7.4)), CRIMSON, falloff=0.8)
    C.energy(inter(circle(12, 12, 6), lambda x, y: y - 14), CRIMSON, falloff=1)
    C.energy(seg(4, 20, 20, 4, 0.7), STEEL, falloff=0.6)
    return A, B, C


ORBS = {
    "whirling_axes_return": revolving_axes, "whirling_axes_fire": burning_axes, "whirling_axes_culling": culling_axes,
    "warcry_weakness": intimidating_cry, "warcry_restore_health": second_wind, "warcry_killing_spree": battle_cry,
    "constitution_melee": combat_training, "constitution_dmg_reduction": toughness, "constitution_armor_pen": mighty_strength,
    "killing_spree_crit": brutality, "killing_spree_regen": killer_physique, "killing_spree_dauntless": dauntless,
    "leap_tremors": trembling_impact, "leap_fire": fiery_leap,
    "rage_low_health": unyielding_rage, "rage_warcry": furious_cry,
    "primalist_totem_shock": shock_totems, "primalist_totem_frost": frostbite_totems,
    "primalist_strikes_tempest": tempest_strikes, "primalist_strikes_glacial": glacial_strikes,
    "tyrant_chains_bleeding": barbed_chains, "tyrant_chains_spikes": spiked_chains,
    "tyrant_explode": exploding_gibs, "tyrant_missing_health": slayer,
}


# second pass: a war axe with a real head, a curled war horn, heavier chains
from motifs import lbox as _lbox, parts as _parts


def axe(ic, cx, cy, ang=-60, s=1.0, head=STEEL, haft=WOOD, seed=0):
    items = [
        (_lbox(-1, 0, 10, 1.0, 0.5), haft, {"base": 2.4}),
        (lambda x, y: poly([(3.6, 1.2), (3.8, -2.2), (1.4, -8.6), (6.4, -6.4), (11.0, -9.4), (9.8, -2.4), (9.8, 1.2)])(x, y), head, {"base": 2.6, "rim": 1.6}),
        (_lbox(10.4, 0, 1.0, 1.6, 0.4), head, {"base": 3.2}),
    ]
    _parts(ic, cx, cy, ang, s, items, seed)


def horn(ic, cx, cy, s=1.0):
    """A war horn curling up to the right, bell at the top right; (cx, cy) its middle."""
    pts = []
    for k in range(9):
        t = k / 8
        a = math.radians(200 - t * 150)
        pts.append((cx + 1 + math.cos(a) * 8 * s, cy + 4 * s + math.sin(a) * 8 * s * 0.9, 0.6 * s + t * 2.4 * s))
    for i in range(8):
        x0, y0, w0 = pts[i]
        x1, y1, w1 = pts[i + 1]
        ic.solid(seg(x0, y0, x1, y1, w0, w1), BONE, base=2.6 + i * 0.1, seed=i)
    xb, yb, wb = pts[-1]
    ic.solid(ellipse(xb + 0.6 * s, yb - 0.6 * s, wb * 1.15, wb * 0.6, -55), BONE, base=3.6, seed=9)
    ic.paint(ellipse(xb + 0.8 * s, yb - 0.8 * s, wb * 0.6, wb * 0.28, -55), lambda x, y, d: BONE[0])
    for i in (3, 6):
        x, y, w = pts[i]
        ic.solid(circle(x, y, w + 0.4), BRASS, base=3.2, seed=20 + i)


def chain(ic, x0, y0, x1, y1, rmp=STEEL, link=4.2, seed=0):
    _chain(ic, x0, y0, x1, y1, rmp=rmp, link=link, seed=seed)


import vm as _vm
_chain = _vm.chain
_st, _ft = shock_totems, frostbite_totems


def shock_totems():
    A, B, C = _st()
    C = ga(BG_Y, (12, 16))
    totem(C, 12, 22, 1.0, rmp=GUN)
    for x in (4, 20):
        bolt(C, [(x, 4), (x - 1.6, 9), (x + 1.4, 10), (x, 15)], w=0.7)
    return A, B, C


def frostbite_totems():
    A, B, C = _ft()
    C = ga(BG_I, (12, 16))
    totem(C, 12, 22, 1.0, rmp=GUN, eyes=ICE)
    snowflake(C, 4, 8, 3, w=0.4)
    snowflake(C, 20, 12, 3, w=0.4)
    return A, B, C


ORBS.update({"primalist_totem_shock": shock_totems, "primalist_totem_frost": frostbite_totems})


def horn(ic, cx, cy, s=1.0):
    """A war horn: mouthpiece lower left, sagging curve, bell upper right; (cx, cy) its middle."""
    P0, P1, P2 = (cx - 8 * s, cy + 1 * s), (cx + 1 * s, cy + 9 * s), (cx + 7 * s, cy - 5 * s)
    pts = []
    for k in range(9):
        t = k / 8
        x = (1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0]
        y = (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1]
        pts.append((x, y, 0.7 * s + t * 2.6 * s))
    for i in range(8):
        x0, y0, w0 = pts[i]
        x1, y1, w1 = pts[i + 1]
        ic.solid(seg(x0, y0, x1, y1, w0, w1), BONE, base=2.6 + i * 0.1, seed=i)
    xb, yb, wb = pts[-1]
    ic.solid(ellipse(xb + 0.4 * s, yb - 0.8 * s, wb * 1.2, wb * 0.55, -60), BONE, base=3.6, seed=9)
    ic.paint(ellipse(xb + 0.5 * s, yb - 0.9 * s, wb * 0.6, wb * 0.25, -60), lambda x, y, d: BONE[0])
    for i in (3, 6):
        x, y, w = pts[i]
        ic.solid(circle(x, y, w + 0.4), BRASS, base=3.2, seed=20 + i)
