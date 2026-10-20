"""Paladin orb icons: A the gear up close, B the moment it happens, C an abstract mark."""
from vm import *

BG_H = ("120c04", "2c2008")
BG_F = ("140604", "2e1006")
BG_Y = ("0c0c14", "1e1e30")
BG_S = ("0a0c12", "1c2230")


def ga(c=BG_H, light=(12, 12)):
    return G(c[0], c[1], light)


def foe(ic, x, y, s=1.0):
    ic.solid(ellipse(x, y, 2.6 * s, 3.6 * s), SHADOW, base=2.2)


def massive_strike():
    A = ga()
    hammer(A, 11, 13, -50, 1.25, head=GOLD)
    B = ga(light=(12, 16))
    B.energy(ellipse(12, 17, 11, 4.4), HOLY, falloff=2)
    B.rays(12, 17, HOLY, n=9, lo=0.6, hi=3)
    C = ga()
    C.energy(cut(circle(12, 12, 10), circle(12, 12, 8.4)), HOLY, falloff=0.8)
    C.energy(cut(circle(12, 12, 6), circle(12, 12, 4.6)), HOLY, falloff=0.6)
    C.energy(circle(12, 12, 2), HOLY, falloff=1.6)
    return A, B, C


def purging_flames():
    A = ga(BG_F)
    hammer(A, 11, 13, -50, 1.1, head=GOLD)
    A.energy(flame(17, 10, 3, 9, 0.3, 2), FIRE, falloff=1.4)
    B = ga(BG_F, (12, 16))
    B.energy(ellipse(12, 18, 10, 3.4), HOLY, falloff=1.4)
    for k, x in enumerate((4, 8, 12, 16, 20)):
        B.energy(flame(x, 19, 2, 7 + (2 - abs(k - 2)) * 2.5, 0, k), FIRE, falloff=1.2)
    C = ga(BG_F)
    C.energy(holy_cross(12, 13, 1.25), HOLY, falloff=1.2)
    C.energy(flame(12, 22, 3, 10, 0, 1), FIRE, falloff=1.2)
    return A, B, C


def wrathful_strike():
    A = ga(BG_Y)
    hammer(A, 11, 13, -50, 1.1, head=GOLD)
    bolt(A, [(15, 4), (18, 7), (16, 9), (20, 12)], w=0.6)
    B = ga(BG_Y)
    for x, y in ((5, 8), (18, 6), (12, 18)):
        foe(B, x, y)
    bolt(B, [(5, 8), (11, 6), (18, 6)], w=0.6)
    bolt(B, [(18, 6), (17, 12), (12, 18)], w=0.6)
    C = ga(BG_Y)
    C.energy(box(12, 7, 7, 3.4, 0, 0.8), HOLY, falloff=1)
    bolt(C, [(13, 10), (10, 15), (14, 15), (11, 22)], w=1.0)
    return A, B, C


def hand_light(ic, cx, cy, s=1.0, glow=HOLY):
    ic.glow(cx, cy - 2 * s, 10 * s, glow[3], 0.5)
    hand_open(ic, cx, cy, s)


def invigorating_touch():
    A = ga(("041004", "0e2a10"))
    hand_light(A, 12, 14, 1.1, LIFE)
    for x, y in ((5, 6), (19, 6)):
        A.energy(star(x, y, 0.8, 2.6, 4), LIFE, falloff=1)
    B = ga(("041004", "0e2a10"))
    B.solid(heart(9, 13, 4.6), CRIMSON, base=3.4)
    B.energy(drop(17, 13, 3.6), MANA, falloff=2.4)
    for x in (9, 17):
        B.energy(poly([(x - 2, 6), (x, 3), (x + 2, 6)]), LIFE, falloff=0.8)
    C = ga(("041004", "0e2a10"))
    C.energy(cut(circle(12, 12, 9), circle(12, 12, 7.4)), LIFE, falloff=0.8)
    for k in range(2):
        C.energy(poly([(6, 16 - k * 6), (12, 10 - k * 6), (18, 16 - k * 6), (18, 18 - k * 6), (12, 12 - k * 6), (6, 18 - k * 6)]), LIFE, falloff=0.8)
    return A, B, C


def cleansing_touch():
    A = ga(BG_S)
    hand_light(A, 12, 14, 1.1, SPIRIT)
    for x, y in ((5, 5), (19, 7), (17, 3)):
        A.energy(circle(x, y, 1.2), SPIRIT, falloff=1)
    B = ga(BG_S)
    B.solid(ellipse(12, 13, 3.6, 6.5), SHADOW, base=2.4)
    B.energy(drop(12, 13, 0), SPIRIT, falloff=1)
    for a in (200, 250, 290, 340):
        r = math.radians(a)
        B.streak(12 + math.cos(r) * 6, 13 + math.sin(r) * 6, 12 + math.cos(r) * 11, 13 + math.sin(r) * 11, 0.8, GAS)
    B.energy(ring(12, 13, 8, 0.9), SPIRIT, falloff=0.6)
    C = ga(BG_S)
    C.energy(drop(12, 13, 7.4), SPIRIT, falloff=3)
    C.energy(star(12, 14, 1.2, 3.6, 4), PAPER, falloff=1)
    return A, B, C


def turn_undead():
    A = ga()
    hand_light(A, 9, 15, 0.95)
    skull(A, 17, 7, 0.55)
    B = ga()
    B.rays(12, 3, HOLY, n=7, lo=1, hi=3.2)
    skull(B, 12, 15, 0.85)
    C = ga()
    C.energy(holy_cross(12, 12, 1.4), HOLY, falloff=1.2)
    C.paint(cut(circle(12, 15, 3.2), circle(0, 0, 0)), lambda x, y, d: None)
    skull(C, 12, 16, 0.4)
    return A, B, C


TRI = [ICE, FIRE, VOLT]


def elemental_bulwark():
    A = ga(BG_S)
    shield(A, 12, 11, 1.15, STEEL, face=CRIMSON)
    for k, rm in enumerate(TRI):
        A.energy(circle(7 + k * 5, 7, 1.4), rm, falloff=1.2)
    B = ga(BG_S)
    shield(B, 12, 12, 0.9, STEEL, face=CRIMSON)
    for k, (rm, a) in enumerate(zip(TRI, (200, 270, 340))):
        r = math.radians(a)
        B.streak(12 + math.cos(r) * 13, 12 + math.sin(r) * 13, 12 + math.cos(r) * 9, 12 + math.sin(r) * 9, 1.0, rm)
    C = ga(BG_S)
    for k, rm in enumerate(TRI):
        C.energy(arc(12, 14, 4 + k * 2.8, 1.3, 200, 340), rm, falloff=0.7)
    return A, B, C


def glancing_blows():
    A = ga(BG_S)
    shield(A, 12, 11, 1.15, STEEL, face=STEEL)
    A.glint(7, 5)
    A.glint(16, 9)
    B = ga(BG_S)
    shield(B, 10, 12, 0.9, STEEL, face=CRIMSON)
    sword(B, 18, 7, 135, 0.6)
    flash(B, 15, 9, 2, HOLY)
    C = ga(BG_S)
    C.energy(poly([(12, 3), (20, 6), (19, 15), (12, 21), (5, 15), (4, 6)]), STEEL, falloff=1.4)
    C.energy(seg(2, 22, 8, 15, 0.8), HOLY, falloff=0.6)
    C.energy(seg(16, 9, 22, 2, 0.8), HOLY, falloff=0.6)
    return A, B, C


def armor_of_wrath():
    A = ga(BG_Y)
    A.solid(poly([(4, 6), (9, 4), (12, 6), (15, 4), (20, 6), (19, 18), (12, 21), (5, 18)]), GOLD, base=2.6)
    A.solid(box(12, 12, 1, 7), GOLD, base=1.6)
    bolt(A, [(14, 7), (12, 11), (15, 12), (12, 17)], w=0.7)
    B = ga(BG_Y)
    B.solid(ellipse(7, 14, 3.4, 6), GOLD, base=2.6)
    foe(B, 19, 10)
    bolt(B, [(9, 9), (13, 6), (14, 11), (18, 9)], w=0.7)
    C = ga(BG_Y)
    C.energy(cut(poly([(12, 3), (20, 6), (19, 15), (12, 21), (5, 15), (4, 6)]), poly([(12, 6), (17, 8), (16.5, 14), (12, 18.5), (7.5, 14), (7, 8)])), GOLD, falloff=1)
    bolt(C, [(14, 7), (11, 12), (14, 12), (11, 18)], w=0.8)
    return A, B, C


def resolve():
    A = ga(BG_S)
    potion(A, 12, 13, 1.2, liquid=MANA)
    A.solid(heart(19, 5, 2.6), CRIMSON, base=3.2)
    B = ga(BG_S)
    B.solid(heart(12, 12, 6.0), CRIMSON, base=3.2)
    B.paint(box(12, 7, 12, 5), lambda x, y, d: None)
    B.solid(inter(heart(12, 12, 6.0), box(12, 6, 12, 5)), SMOKE, base=1.6)
    B.energy(drop(19, 18, 2.4), MANA, falloff=1.6)
    C = ga(BG_S)
    C.energy(cut(heart(12, 13, 7.5), heart(12, 13.5, 4.8), box(12, 6, 12, 4)), CRIMSON, falloff=1.2)
    C.energy(drop(12, 13, 2.4), MANA, falloff=1.6)
    return A, B, C


def shield_of_faith():
    A = ga(("04081a", "0e1a3a"))
    shield(A, 12, 11, 1.15, GOLD, face=MANA)
    B = ga(("04081a", "0e1a3a"))
    B.energy(cut(circle(12, 12, 9), circle(12, 12, 7.4)), MANA, falloff=1)
    B.solid(ellipse(12, 13, 3.4, 6), GOLD, base=2.6)
    for a in (-40, 200):
        r = math.radians(a)
        B.streak(12 + math.cos(r) * 14, 12 + math.sin(r) * 14, 12 + math.cos(r) * 9.5, 12 + math.sin(r) * 9.5, 1.0, CRIMSON)
    C = ga(("04081a", "0e1a3a"))
    C.energy(poly([(12, 3), (20, 6), (19, 15), (12, 21), (5, 15), (4, 6)]), MANA, falloff=2.4)
    C.energy(holy_cross(12, 12, 0.8), HOLY, falloff=0.9)
    return A, B, C


def zeal():
    A = ga(("04081a", "0e1a3a"))
    sword(A, 12, 12, -45, 1.05, blade=MANA)
    B = ga(("04081a", "0e1a3a"))
    foe(B, 14, 13, 1.4)
    slash(B, 12, 12, 9, 200, 320, MANA)
    flash(B, 14, 12, 2.4, MANA)
    C = ga(("04081a", "0e1a3a"))
    C.energy(drop(9, 13, 5.4), MANA, falloff=2.4)
    C.energy(poly([(14, 4), (21, 12), (14, 20), (16, 12)]), HOLY, falloff=1)
    return A, B, C


def judgement_hammer(ic, cx, cy, s=1.0, rmp=GOLD):
    hammer(ic, cx, cy, -90, s, head=rmp)
    ic.glow(cx, cy - 6 * s, 8 * s, HOLY[4], 0.4)


def prolonged_prosecution():
    A = ga()
    judgement_hammer(A, 10, 13, 0.95)
    hourglass(A, 18, 15, 0.5, sand=HOLY)
    B = ga()
    skull(B, 7, 16, 0.6)
    B.streak(10, 14, 16, 9, 0.8, HOLY)
    hourglass(B, 18, 8, 0.6, sand=HOLY, t=0.8)
    C = ga()
    C.energy(arc(12, 12, 9, 1.4, 90, 400), HOLY, falloff=0.8)
    C.energy(poly([(9, 21), (14, 18), (14, 24)]), HOLY, falloff=0.8)
    C.energy(holy_cross(12, 12, 0.7), HOLY, falloff=0.9)
    return A, B, C


def hammer_of_wrath():
    A = ga(BG_Y)
    judgement_hammer(A, 12, 13, 1.05)
    bolt(A, [(5, 4), (7, 8), (5, 11), (8, 15)], w=0.6)
    bolt(A, [(19, 4), (17, 8), (19, 11), (16, 15)], w=0.6)
    B = ga(BG_Y, (12, 16))
    foe(B, 12, 17, 1.2)
    B.solid(box(12, 6, 5, 3, 0, 0.6), GOLD, base=2.8)
    bolt(B, [(12, 9), (10, 12), (13, 13), (11, 16)], w=0.7)
    C = ga(BG_Y)
    C.energy(union(box(12, 7, 7, 3.4, 0, 0.6), box(12, 15, 1.2, 6)), GOLD, falloff=1)
    bolt(C, [(19, 11), (16, 15), (19, 15), (16, 21)], w=0.7)
    return A, B, C


def punish_the_wicked():
    A = ga()
    judgement_hammer(A, 12, 11, 0.9)
    A.energy(drop(6, 19, 2), TOXIC, falloff=1.4)
    A.energy(snowflake and circle(18, 19, 0), ICE, falloff=1)
    snowflake(A, 18, 19, 2.6, w=0.35)
    B = ga(light=(12, 16))
    foe(B, 12, 17, 1.3)
    B.energy(cloud and circle(12, 21, 0), GAS, falloff=1)
    for x in (8, 16):
        B.energy(circle(x, 19, 1.4), TOXIC, falloff=1)
    B.solid(box(12, 6, 5, 3, 0, 0.6), GOLD, base=2.8)
    B.solid(box(12, 11, 0.9, 3), WOOD, base=2.4)
    C = ga()
    C.energy(union(box(12, 7, 7, 3.4, 0, 0.6), box(12, 15, 1.2, 6)), GOLD, falloff=1)
    C.energy(circle(5, 20, 1.8), TOXIC, falloff=1.4)
    C.energy(circle(19, 20, 1.8), ICE, falloff=1.4)
    return A, B, C


def shackles():
    A = ga(BG_S)
    for x in (8, 16):
        A.solid(cut(circle(x, 12, 5), circle(x, 12, 3.2)), STEEL, base=2.6, seed=x)
    chain(A, 11, 12, 13, 12)
    A.glint(6, 8)
    B = ga(BG_S)
    foe(B, 5, 13)
    foe(B, 19, 13)
    chain(B, 7, 13, 17, 13, rmp=HOLY)
    C = ga(BG_S)
    C.energy(cut(ring(7, 12, 4.4, 1.3), box(10.5, 12, 1.6, 2.4)), HOLY, falloff=0.8)
    C.energy(cut(ring(17, 12, 4.4, 1.3), box(13.5, 12, 1.6, 2.4)), HOLY, falloff=0.8)
    C.energy(box(12, 12, 3, 0.8), HOLY, falloff=0.6)
    return A, B, C


def pillar(ic, cx, by, h, w=2.4, rmp=HOLY):
    ic.energy(box(cx, by - h / 2, w, h / 2, 0, w * 0.4), rmp, falloff=w * 0.8)
    ic.energy(ellipse(cx, by, w * 1.6, w * 0.6), rmp, falloff=0.8)


def divine_pattern():
    A = ga(light=(12, 16))
    for x, y in ((6, 10), (18, 10), (6, 21), (18, 21), (12, 15)):
        pillar(A, x, y, 9, 1.5)
    B = ga(light=(12, 16))
    for k, (x, y) in enumerate(((4, 21), (9, 17), (14, 13), (19, 9))):
        pillar(B, x, y, 6 + k * 1.6, 1.4 + k * 0.15)
    C = ga()
    for x in (6, 12, 18):
        for y in (6, 12, 18):
            C.energy(box(x, y, 2, 2, 0, 0.6), HOLY, falloff=0.9)
    return A, B, C


def pillars_of_wrath():
    A = ga(BG_Y, (12, 16))
    pillar(A, 12, 21, 18, 3.2, HOLY)
    bolt(A, [(5, 4), (7, 9), (5, 13), (8, 18)], w=0.6)
    bolt(A, [(19, 4), (17, 9), (19, 13), (16, 18)], w=0.6)
    B = ga(BG_Y, (12, 16))
    for x in (6, 18):
        pillar(B, x, 20, 13, 2)
    bolt(B, [(6, 10), (12, 13), (18, 10)], w=0.7)
    C = ga(BG_Y)
    C.energy(box(12, 12, 3, 9, 0, 1), HOLY, falloff=1.4)
    bolt(C, [(13, 4), (10, 11), (14, 12), (11, 20)], rmp=VOLT, w=0.8)
    return A, B, C


def restoration():
    A = ga(("041004", "0e2a10"))
    shield(A, 12, 11, 1.1, GOLD, face=LIFE, boss=None)
    A.energy(holy_cross(12, 12, 0.8), HOLY, falloff=0.9)
    B = ga(("041004", "0e2a10"))
    B.energy(cut(circle(12, 12, 9), circle(12, 12, 7.4)), HOLY, falloff=1)
    B.solid(heart(12, 12, 5.0), CRIMSON, base=3.4)
    for x, y in ((5, 6), (19, 7), (6, 19)):
        B.energy(star(x, y, 0.6, 2, 4), LIFE, falloff=0.9)
    C = ga(("041004", "0e2a10"))
    C.energy(cut(heart(12, 13, 7.5), heart(12, 13.5, 4.8)), LIFE, falloff=1.2)
    C.energy(poly([(9, 14), (12, 10), (15, 14)]), LIFE, falloff=0.8)
    return A, B, C


def divine_retort():
    A = ga(light=(12, 16))
    shield(A, 9, 13, 0.85, GOLD, face=SPIRIT, boss=None)
    pillar(A, 19, 22, 18, 2.2)
    B = ga(light=(12, 16))
    B.energy(cut(circle(12, 15, 8), circle(12, 15, 6.6)), SPIRIT, falloff=0.9)
    for x in (4, 20):
        pillar(B, x, 22, 14, 1.8)
    pillar(B, 12, 15, 12, 1.6)
    C = ga()
    C.energy(poly([(12, 3), (20, 6), (19, 15), (12, 21), (5, 15), (4, 6)]), SPIRIT, falloff=2.4)
    C.energy(box(12, 12, 1.4, 7, 0, 0.4), HOLY, falloff=0.9)
    return A, B, C


def fuel_the_flame():
    A = ga(BG_F)
    A.solid(poly([(8, 22), (16, 22), (15, 17), (9, 17)]), BRASS, base=2.6)
    A.energy(flame(12, 17, 4, 14, 0, 1), FIRE, falloff=1.8)
    B = ga(BG_F)
    B.solid(ellipse(12, 14, 3.4, 6.5), SHADOW, base=2.4)
    for a in (200, 250, 290, 340):
        r = math.radians(a)
        B.energy(flame(12 + math.cos(r) * 8, 14 + math.sin(r) * 8 + 3, 1.8, 6, 0, a), FIRE, falloff=1.2)
    B.energy(poly([(18, 8), (21, 4), (23, 8)]), FIRE, falloff=0.8)
    C = ga(BG_F)
    C.energy(flame(12, 21, 5, 17, 0, 3), FIRE, falloff=2)
    C.energy(poly([(8, 13), (12, 8), (16, 13), (16, 15), (12, 11), (8, 15)]), HOLY, falloff=0.8)
    return A, B, C


def blazing_lance():
    A = ga(BG_F)
    A.solid(seg(3, 21, 17, 7, 0.9), WOOD, base=2.6)
    A.solid(poly([(15, 6), (22, 2), (18, 9)]), GOLD, base=3.2)
    A.energy(flame(19, 7, 2, 6, 0.6, 1), FIRE, falloff=1.2)
    B = ga(BG_F)
    for x, y in ((8, 7), (14, 17)):
        foe(B, x, y)
    B.streak(0, 12, 23, 12, 1.6, FIRE)
    C = ga(BG_F)
    C.energy(union(seg(3, 12, 17, 12, 1.2), poly([(15, 7.5), (23, 12), (15, 16.5)])), FIRE, falloff=1)
    return A, B, C


def flames_of_devotion():
    A = ga(BG_F)
    sword(A, 12, 12, -45, 1.05, blade=FIRE, guard=GOLD)
    B = ga(BG_F)
    for k in range(3):
        B.energy(flame(6 + k * 6, 21, 2.2, 8 + k * 3, 0, k), FIRE, falloff=1.2)
    sword(B, 12, 10, -45, 0.6, guard=GOLD)
    C = ga(BG_F)
    for k in range(3):
        C.energy(flame(6 + k * 6, 20, 2.4, 9 + k * 3, 0, k), HOLY if k == 2 else FIRE, falloff=1.2)
    return A, B, C


def bringer_of_flames():
    A = ga(BG_F)
    shield(A, 12, 11, 1.1, GOLD, face=FIRE, boss=None)
    B = ga(BG_F)
    B.solid(ellipse(12, 13, 3.6, 6.5), GOLD, base=2.6)
    for x in (4, 20):
        B.energy(flame(x, 22, 2.6, 15, 0, x), FIRE, falloff=1.4)
    C = ga(BG_F)
    C.energy(cut(poly([(12, 3), (20, 6), (19, 15), (12, 21), (5, 15), (4, 6)]), poly([(12, 6), (17, 8), (16.5, 14), (12, 18.5), (7.5, 14), (7, 8)])), GOLD, falloff=1)
    C.energy(flame(12, 17, 2.6, 9, 0, 2), FIRE, falloff=1.2)
    return A, B, C


ORBS = {
    "pal_blessed_strikes_size": massive_strike, "pal_blessed_strikes_fire": purging_flames, "pal_blessed_strikes_lightning": wrathful_strike,
    "pal_lay_on_hands_invigorating": invigorating_touch, "pal_lay_on_hands_cleansing": cleansing_touch, "pal_lay_on_hands_undead": turn_undead,
    "pal_armor_resistances": elemental_bulwark, "pal_armor_glancing_blows": glancing_blows, "pal_armor_wrath": armor_of_wrath,
    "pal_conviction_resolve": resolve, "conviction_shield": shield_of_faith, "conviction_mana_damage": zeal,
    "pal_judgement_extend": prolonged_prosecution, "pal_judgement_lightning": hammer_of_wrath,
    "pal_lawbringer_punish": punish_the_wicked, "pal_lawbringer_shackles": shackles,
    "pal_pillars_pattern": divine_pattern, "pal_pillars_lightning": pillars_of_wrath,
    "divine_protection_restoration": restoration, "divine_protection_pillars": divine_retort,
    "radiance_immolation_flames": fuel_the_flame, "radiance_immolation_lance": blazing_lance,
    "radiance_flames_dmg_add": flames_of_devotion, "radiance_flames_resistance": bringer_of_flames,
}


# second pass
_gb, _aw, _rs = glancing_blows, armor_of_wrath, resolve


def glancing_blows():
    A, B, C = _gb()
    C = ga(BG_S)
    C.energy(cut(poly([(12, 3), (20, 6), (19, 15), (12, 21), (5, 15), (4, 6)]), poly([(12, 6), (17, 8), (16.5, 14), (12, 18.5), (7.5, 14), (7, 8)])), STEEL, falloff=1)
    C.energy(arc(12, 12, 11, 1.0, 200, 260), HOLY, falloff=0.6)
    C.energy(poly([(19, 2), (23, 5), (18, 6)]), HOLY, falloff=0.6)
    return A, B, C


def armor_of_wrath():
    A, B, C = _aw()
    A = ga(BG_Y)
    A.solid(poly([(5, 5), (10, 4), (12, 6), (14, 4), (19, 5), (19, 14), (16, 20), (8, 20), (5, 14)]), GOLD, base=2.6)
    A.solid(union(circle(5, 6, 3.4), circle(19, 6, 3.4)), GOLD, base=3.2, seed=3)
    A.shade(box(12, 13, 0.5, 6), 0.5)
    bolt(A, [(15, 8), (12, 12), (15, 13), (11, 19)], w=0.8)
    return A, B, C


def resolve():
    A, B, C = _rs()
    B = ga(BG_S)
    B.solid(heart(12, 12, 6.0), SMOKE, base=1.8)
    B.solid(inter(heart(12, 12, 6.0), box(12, 16, 12, 4)), CRIMSON, base=3.2)
    potion(B, 19, 17, 0.5, liquid=MANA)
    return A, B, C


ORBS.update({"pal_armor_glancing_blows": glancing_blows, "pal_armor_wrath": armor_of_wrath, "pal_conviction_resolve": resolve})
