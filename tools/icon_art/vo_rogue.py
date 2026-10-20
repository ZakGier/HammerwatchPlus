"""Rogue orb icons: A the gear up close, B the moment it happens, C an abstract mark."""
from vm import *

RG = ("140608", "34121a")      # the rogue's wine-red ground


def ricochet():
    A = G("0a0c12", "1e2230", (6, 6))
    A.solid(box(21, 12, 3, 13), R("141218", "2a2630", "403a48", "5a5262", "7a7082"), seed=3)
    dagger(A, 13, 12, 20, 0.95)
    flash(A, 18.5, 13.5, 2.6, VOLT)
    B = G("0c0a12", "201a2c", (12, 12))
    pts = [(2, 21), (9, 4), (15, 20), (22, 5)]
    for i in range(3):
        B.streak(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 0.7 + i * 0.25, STEEL)
    for p in pts[1:3]:
        flash(B, p[0], p[1], 1.8, VOLT)
    C = G("0c0a12", "1e1a28", (12, 12))
    C.energy(union(seg(4, 19, 12, 6, 1.2), seg(12, 6, 20, 19, 1.2)), STEEL, falloff=0.9)
    C.energy(poly([(17, 19), (22, 21), (21, 15)]), STEEL, falloff=1.0)
    return A, B, C


def deadly_aim():
    A = G(*RG, (14, 6))
    dagger(A, 11, 13, -45, 1.25)
    A.glint(19, 5, arm=1)
    B = G(*RG, (12, 12))
    B.solid(circle(12, 12, 8.5), BONE, base=3.2, seed=1)
    B.solid(circle(12, 12, 5.8), CRIMSON, base=3.0, seed=2)
    B.solid(circle(12, 12, 3.0), BONE, base=3.6, seed=3)
    dagger(B, 15.5, 8.5, 135, 0.8)
    C = G(*RG, (12, 12))
    eye(C, 12, 12, 1.2, CRIMSON)
    return A, B, C


def poisoned_knives():
    A = G("061006", "142a10", (14, 6))
    dagger(A, 11, 12, -45, 1.2, blade=R("0e2a0c", "1e5214", "3a8a1c", "6ec434", "b8f070", "f0ffd0"))
    for x, y in ((8, 19), (5, 22)):
        A.energy(drop(x, y, 1.1), TOXIC, falloff=1.0)
    B = G("061006", "122410", (4, 20))
    for k, a in enumerate((-70, -45, -20)):
        r = math.radians(a)
        B.streak(3, 21, 3 + math.cos(r) * 18, 21 + math.sin(r) * 18, 1.1, TOXIC)
        B.energy(drop(3 + math.cos(r) * 19.5, 21 + math.sin(r) * 19.5 - 0.5, 1.0), TOXIC, falloff=0.9)
    C = G("061006", "142a10", (12, 12))
    C.energy(drop(12, 13.5, 6.0), TOXIC, falloff=4)
    C.paint(poly([(12, 6.5), (13.4, 12), (12, 19.5), (10.6, 12)]), lambda x, y, d: TOXIC[6] if d < -0.6 else TOXIC[5])
    return A, B, C


def focused_throw():
    A = G("0c0a14", "221c30", (16, 8))
    for k, y in enumerate((7, 12, 17)):
        dagger(A, 11 + (k == 1) * 2, y, 0, 0.9, seed=k)
    B = G("08080e", "1a1824", (20, 12))
    for k, y in enumerate((4, 8, 16, 20)):
        B.streak(1, y, 20, 12, 0.6, STEEL)
    flash(B, 20, 12, 2.6, BONE)
    C = G("0c0a14", "1e1a2c", (12, 12))
    C.energy(poly([(2, 10.5), (17, 11.2), (23, 12), (17, 12.8), (2, 13.5)]), STEEL, falloff=1.4)
    C.energy(union(seg(4, 4, 15, 10.5, 0.5), seg(4, 20, 15, 13.5, 0.5)), SPIRIT, falloff=0.5)
    return A, B, C


def disarming_strikes():
    A = G(*RG, (8, 8))
    hand_open(A, 8, 15, 0.85)
    sword(A, 16, 10, 120, 0.7)
    B = G(*RG, (12, 12))
    sword(B, 12, 12, -30, 0.8)
    for a0 in (200, 20):
        B.energy(arc(12, 12, 10, 1.0, a0, a0 + 70), BONE, falloff=0.5)
    C = G(*RG, (12, 12))
    sword(C, 9, 15, -45, 0.62)
    C.solid(shard(17.5, 6.5, -45, 7, 1.4), STEEL, base=3.4)
    flash(C, 13.2, 10.8, 1.8, BONE)
    return A, B, C


def fiery_bolas():
    A = G("140804", "2e160a", (12, 8))
    A.solid(arc(12, 6, 9, 0.8, 30, 150), LEATHER, base=3.0)
    for x, y in ((4.5, 12), (19.5, 12)):
        A.solid(circle(x, y, 3.4), STEEL, base=2.0)
        A.energy(flame(x, y - 1.5, 2.6, 6, 0, int(x)), FIRE, falloff=1.4)
    B = G("140804", "2a1408", (12, 14))
    B.solid(box(12, 16, 2.6, 8, 0, 1), LEATHER, base=2.4)
    for k in range(3):
        B.energy(ring(12, 11 + k * 3.5, 3.6, 0.9), FIRE, falloff=0.6)
    C = G("140804", "2a1408", (12, 12))
    C.energy(union(circle(6, 15, 3.2), circle(18, 9, 3.2), seg(6, 15, 18, 9, 0.5)), FIRE, falloff=2.2)
    return A, B, C


def shock_assault():
    A = G("141004", "2e2608", (14, 8))
    dagger(A, 12, 12, -45, 1.2)
    bolt(A, [(7, 10), (11, 12), (10, 15), (15, 17)], w=0.6)
    bolt(A, [(14, 6), (16, 9), (19, 9)], w=0.5)
    B = G("100c04", "282008", (12, 12))
    for k, (a0, r) in enumerate(((190, 9), (230, 6.5), (160, 11.5))):
        slash(B, 14, 13, r, a0, a0 + 90, VOLT, 1.4 - k * 0.2)
    C = G("100c04", "2a2208", (12, 12))
    bolt(C, [(15, 1), (8, 11), (14, 12), (8, 23)], w=1.6, fall=1.4)
    return A, B, C


def adrenaline():
    A = G("040818", "0e1a3a", (12, 8))
    potion(A, 12, 13, 1.25, liquid=MANA)
    B = G("040818", "0c1634", (12, 18))
    for k, (x, y, r) in enumerate(((6, 18, 1.8), (12, 13, 2.3), (18, 7, 2.8))):
        B.energy(drop(x, y, r), MANA, falloff=r)
    C = G("040818", "0e1a3a", (12, 12))
    for k in range(3):
        y = 17 - k * 5
        C.energy(union(seg(5, y + 3, 12, y - 2, 1.0), seg(12, y - 2, 19, y + 3, 1.0)), MANA, falloff=0.8 + k * 0.2)
    return A, B, C


def blade_parry():
    A = G("0a0c12", "1e2230", (12, 6))
    dagger(A, 12, 12, -45, 1.2, seed=1)
    dagger(A, 12, 12, -135, 1.2, seed=2)
    B = G("0a0c12", "1c2030", (12, 12))
    dagger(B, 8, 14, -30, 0.95)
    dagger(B, 16.5, 12, 200, 0.95, blade=R("1a0e0a", "3a2016", "6a3a26", "9a5a3a", "c88a64", "f0c8a0"))
    flash(B, 13.5, 10, 3, VOLT)
    C = G("0a0c12", "1e2230", (12, 12))
    C.energy(cut(poly([(12, 3), (20, 6), (19, 15), (12, 21), (5, 15), (4, 6)]), poly([(12, 6.5), (16.6, 8.2), (16, 14), (12, 17.6), (8, 14), (7.4, 8.2)])), STEEL, falloff=1.0)
    C.energy(poly([(12, 8), (13, 12), (12, 16), (11, 12)]), STEEL, falloff=1.0)
    return A, B, C


def agile_casting():
    A = G("0e0818", "241434", (12, 6))
    hand_open(A, 12, 14, 1.0)
    A.energy(circle(12, 5.5, 2.2), ARCANE, falloff=2)
    for x, y in ((6, 4), (18, 6), (15, 2)):
        A.glint(x, y, ARCANE[5])
    B = G("0e0818", "221432", (12, 12))
    hourglass(B, 12, 12, 1.25, sand=ARCANE, t=0.7)
    for y in (6, 12, 18):
        B.streak(22, y, 17, y, 0.6, ARCANE)
    C = G("0e0818", "241434", (12, 12))
    pts = [(12 + math.cos(t * 0.5) * t * 0.7, 12 + math.sin(t * 0.5) * t * 0.7) for t in range(1, 15)]
    C.energy(union(*[seg(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 0.5 + i * 0.07) for i in range(len(pts) - 1)]), ARCANE, falloff=0.9)
    return A, B, C


def fleet_footed():
    A = G("0a0c12", "1c2232", (14, 6))
    boot(A, 13, 11, 1.1, wing=BONE)
    B = G("0a0c12", "1c2030", (16, 12))
    for y, x0 in ((8, 1), (12, 0), (16, 2)):
        B.streak(x0, y, x0 + 9, y, 0.8, SPIRIT)
    boot(B, 15, 10, 0.95)
    C = G("0a0c12", "1c2232", (12, 12))
    for k, (x, y) in enumerate(((5, 19), (10, 14), (15, 10), (20, 5))):
        C.energy(ellipse(x + (1.4 if k % 2 else -1.4), y, 1.5, 2.4, 45), SPIRIT if k == 3 else STEEL, falloff=0.9)
    return A, B, C


def lethal_opening():
    A = G("08060c", "1a1024", (16, 6))
    A.solid(poly([(2, 2), (11, 2), (16, 22), (3, 22)]), SHADOW, base=2.2, seed=1)
    dagger(A, 15, 11, -50, 1.0)
    B = G(*RG, (12, 12))
    eye(B, 12, 12, 1.2, CRIMSON, open_=0.55)
    C = G(*RG, (12, 12))
    C.energy(cut(circle(11, 12, 8), circle(15, 10, 7)), CRIMSON, falloff=1.6)
    C.glint(17, 16, CRIMSON[6])
    return A, B, C


def on_the_move():
    A = G("0a0c12", "1e2230", (16, 10))
    for k, (x, al) in enumerate(((4, 0.35), (9, 0.6))):
        A.solid(ellipse(x, 12, 2.6, 6.5), R("101420", "1e2840", "34446a"), base=1, spread=0.4, seed=k)
    A.solid(ellipse(16, 12, 3, 7), SHADOW, base=3.2, seed=4)
    A.energy(circle(16, 7, 1.2), SPIRIT, falloff=1)
    B = G("0a0c12", "1c2030", (12, 12))
    B.energy(arc(12, 12, 8, 1.6, -60, 220), SPIRIT, falloff=0.9)
    B.energy(poly([(16.5, 4.2), (21, 6.5), (17, 9.8)]), SPIRIT, falloff=1)
    boot(B, 11, 11, 0.6)
    C = G("0a0c12", "1e2230", (12, 12))
    for k in range(3):
        x = 5 + k * 6
        C.energy(union(seg(x, 6, x + 4, 12, 1.0), seg(x + 4, 12, x, 18, 1.0)), SPIRIT, falloff=0.7 + k * 0.25)
    return A, B, C


def phantasmal_strike():
    A = G("040c14", "0e2232", (14, 8))
    sword(A, 12, 12, -45, 0.95, blade=SPIRIT, hilt=SPIRIT, guard=SPIRIT)
    B = G("040c14", "0c1e2c", (6, 12))
    for k, (x, y, s) in enumerate(((19, 5, 0.45), (20, 12, 0.5), (19, 19, 0.45))):
        sword(B, x, y, 0, s, blade=SPIRIT, hilt=SPIRIT, guard=SPIRIT, seed=k)
    flash(B, 5, 12, 3, SPIRIT)
    C = G("040c14", "0e2232", (12, 12))
    for k, (x, y) in enumerate(((5, 12), (13, 6), (13, 18), (20, 12))):
        wisp(C, x, y, 1.6 + (k == 0) * 0.6, SPIRIT, ang=0, seed=k)
    return A, B, C


def crimson_strike():
    A = G(*RG, (14, 6))
    sword(A, 12, 12, -45, 0.95, blade=R("2a0a0e", "5a1018", "8e1a24", "c02a30", "e8786a", "ffd0c0"))
    for x, y in ((7, 19), (5, 22.5)):
        A.energy(drop(x, y, 1.1), CRIMSON, falloff=1)
    B = G(*RG, (12, 14))
    B.solid(heart(12, 15, 0.9), CRIMSON, base=3.4)
    for k, (x, y) in enumerate(((5, 4), (12, 3), (19, 4))):
        B.energy(drop(x, y, 1.2), CRIMSON, falloff=1)
        B.streak(x, y + 1, 12 + (x - 12) * 0.4, 9, 0.6, CRIMSON)
    C = G(*RG, (12, 12))
    C.energy(drop(12, 13.5, 6.0), CRIMSON, falloff=4)
    return A, B, C


def executioner():
    A = G(*RG, (12, 6))
    skull(A, 12, 13, 1.25)
    dagger(A, 13, 9, -100, 0.9)
    B = G("0c0408", "220a12", (12, 4))
    B.solid(poly([(4, 2), (20, 2), (20, 8), (4, 12)]), STEEL, base=3.2)
    B.solid(box(3, 12, 1.4, 11), WOOD, base=2.6)
    B.solid(box(21, 12, 1.4, 11), WOOD, base=2.2)
    B.energy(box(12, 21, 9, 1.0), CRIMSON, falloff=0.8)
    C = G(*RG, (12, 12))
    C.energy(cut(skull_mark(12, 12), circle(9, 11, 1.8), circle(15, 11, 1.8)), CRIMSON, falloff=1.5)
    return A, B, C


def skull_mark(cx, cy):
    return union(circle(cx, cy - 1, 6.4), box(cx, cy + 5, 3.6, 2.6, 0, 1))


def hidden_cuts():
    A = G("06040a", "140e1e", (12, 12))
    A.solid(circle(12, 12, 9), VOID, base=1.4, spread=0.6)
    dagger(A, 12, 12, -45, 1.0, blade=STEEL)
    B = G("08060c", "180e1e", (12, 12))
    for k, (x, y, a) in enumerate(((7, 7, 200), (17, 9, 260), (10, 18, 160))):
        slash(B, x + 3, y + 3, 4.5, a, a + 80, CRIMSON, 1.2)
    B.solid(ellipse(12, 12, 2.2, 5), SHADOW, base=2.6)
    C = G("08060c", "1a1022", (12, 12))
    for k in range(3):
        C.energy(seg(5 + k * 5, 19, 9 + k * 5, 5, 0.9), CRIMSON, falloff=0.7)
    return A, B, C


def billowing_cloud():
    A = G("061006", "12260e", (12, 8))
    cloud(A, [(7, 15, 5), (16, 14, 6), (11, 9, 5), (12, 17, 4)], GAS)
    A.solid(ellipse(12, 12, 2.2, 5.2), SHADOW, base=2.0)
    B = G("061006", "12240e", (12, 12))
    for k in range(3):
        B.energy(arc(12, 12, 4 + k * 3.2, 1.6, k * 70, k * 70 + 200), GAS, falloff=1.0)
    C = G("061006", "142a10", (12, 12))
    C.energy(union(circle(8, 14, 4), circle(15, 13, 5), circle(12, 9, 4)), TOXIC, falloff=1.4, hot=4)
    return A, B, C


def corrosion():
    A = G("061006", "142a10", (12, 6))
    shield(A, 12, 11, 1.1, R("10140c", "283020", "40503a", "5a6a50", "7a8a6c", "a4b090"), boss=None)
    for x, y, r in ((9, 9, 1.6), (15, 13, 2), (11, 16, 1.4)):
        A.energy(circle(x, y, r), TOXIC, falloff=r)
    B = G("061006", "12240e", (12, 6))
    B.solid(box(12, 9, 8, 5, 0, 1), STEEL, base=2.8)
    for k, x in enumerate((7, 11, 16)):
        B.energy(union(drop(x, 17 + k % 2 * 2, 1.4), seg(x, 13, x, 16 + k % 2 * 2, 0.6)), TOXIC, falloff=1)
    C = G("061006", "142a10", (12, 12))
    C.energy(cut(poly([(4, 4), (20, 4), (20, 12), (12, 21), (4, 12)]), poly([(13, 3), (10, 9), (13, 12), (10, 22), (12, 22), (15, 12), (12, 9), (15, 3)])), TOXIC, falloff=1.2)
    return A, B, C


def coated_weapons():
    A = G("061006", "142a10", (14, 6))
    sword(A, 12, 12, -45, 0.95, blade=R("0e2a0c", "1e5214", "3a8a1c", "6ec434", "b8f070", "f0ffd0"))
    B = G("061006", "12240e", (12, 18))
    potion(B, 12, 16, 0.95, liquid=TOXIC)
    dagger(B, 12, 6, 90, 0.7)
    C = G("061006", "142a10", (12, 12))
    C.energy(poly([(4, 20), (16, 6), (20, 4), (18, 8), (6, 21)]), TOXIC, falloff=1.4)
    return A, B, C


def deadly_toxins():
    A = G("061006", "142a10", (12, 6))
    potion(A, 12, 13, 1.25, liquid=TOXIC)
    B = G("061006", "12240e", (12, 10))
    skull(B, 12, 12, 1.3, rmp=R("0e1e0a", "1e3a12", "36601e", "5a8e30", "8ec450", "d0f090"), eyes=TOXIC)
    C = G("061006", "142a10", (12, 12))
    C.energy(ring(12, 12, 8.5, 1.2), TOXIC, falloff=0.8)
    C.energy(drop(12, 13, 4), TOXIC, falloff=3)
    return A, B, C


def incendiary_grenades():
    A = G("140804", "2e1608", (12, 10))
    bomb(A, 11, 14, 6)
    A.energy(flame(17, 22, 3, 9, 0, 2), FIRE, falloff=1.4)
    B = G("140604", "2a1006", (12, 18))
    for k, x in enumerate((4, 9, 14, 19)):
        B.energy(flame(x, 23, 2.8, 9 + (k % 2) * 4, 0, k), FIRE, falloff=1.6)
    C = G("140604", "2e1006", (12, 12))
    C.energy(cut(circle(12, 12, 8), circle(12, 12, 4.5)), FIRE, falloff=1.6)
    C.energy(circle(12, 12, 2.2), FIRE, falloff=2)
    return A, B, C


def shock_grenades():
    A = G("100c04", "282008", (12, 10))
    bomb(A, 11, 14, 6, spark=VOLT)
    bolt(A, [(5, 9), (8, 12), (6, 15)], w=0.5)
    bolt(A, [(17, 13), (15, 17), (19, 19)], w=0.5)
    B = G("100c04", "262008", (5, 18))
    flash(B, 5, 18, 3.4, VOLT)
    bolt(B, [(6, 17), (11, 12), (10, 9), (16, 7), (21, 3)], w=0.8)
    bolt(B, [(10, 9), (14, 13), (20, 12)], w=0.6)
    C = G("100c04", "2a2208", (12, 12))
    C.energy(ring(12, 12, 8.5, 1.4), VOLT, falloff=0.7)
    bolt(C, [(14, 4), (9, 12), (14, 12), (10, 20)], w=1.2)
    return A, B, C


def explosive_exit():
    A = G("0c0a10", "1e1a26", (12, 12))
    bomb(A, 7, 16, 4.6)
    for y in (6, 10, 14):
        A.streak(9, y, 22, y - 3, 0.7, STEEL)
    B = G("140604", "2a1006", (6, 16))
    flash(B, 6, 17, 6, FIRE)
    boot(B, 17, 8, 0.65)
    for y in (6, 9):
        B.streak(10, y + 4, 14, y, 0.6, SMOKE)
    C = G("140604", "2a1006", (12, 12))
    for k in range(2):
        x = 11 + k * 6
        C.energy(union(seg(x, 6, x + 4, 12, 1.0), seg(x + 4, 12, x, 18, 1.0)), STEEL, falloff=0.8)
    C.energy(star(6, 12, 1.4, 4.4, 6), FIRE, falloff=1.4)
    return A, B, C


def zzzap():
    A = G("100c04", "282008", (12, 14))
    fist(A, 12, 15, 1.0, rmp=BRASS)
    bolt(A, [(12, 9), (9, 5), (13, 3), (11, 0)], w=0.7)
    B = G("0c0a04", "221c08", (12, 4))
    bolt(B, [(13, 0), (9, 8), (14, 10), (10, 20)], w=1.1)
    flash(B, 10, 20, 3.4, VOLT)
    C = G("100c04", "2a2208", (12, 12))
    C.energy(union(seg(4, 8, 9, 15, 1.1), seg(9, 15, 14, 8, 1.1), seg(14, 8, 19, 15, 1.1)), VOLT, falloff=0.9)
    return A, B, C


def shrapnels():
    A = G("0e0a06", "241a10", (12, 8))
    cog(A, 12, 12, 6.4)
    for a in (-30, 60, 150, 240):
        r = math.radians(a)
        A.solid(shard(12 + math.cos(r) * 9.5, 12 + math.sin(r) * 9.5, a, 4, 1), STEEL, base=3.2)
    B = G("0e0a06", "221810", (12, 12))
    flash(B, 12, 12, 3, BONE)
    for k in range(8):
        a = k * 45 + 20
        r = math.radians(a)
        B.streak(12 + math.cos(r) * 3, 12 + math.sin(r) * 3, 12 + math.cos(r) * 10, 12 + math.sin(r) * 10, 0.8, STEEL)
    C = G("0e0a06", "241a10", (12, 12))
    for k in range(6):
        a = k * 60
        r = math.radians(a)
        C.energy(shard(12 + math.cos(r) * 6.5, 12 + math.sin(r) * 6.5, a, 6, 1.4), BRASS, falloff=1.0)
    return A, B, C


ORBS = {
    "rog_fan_of_knives_ricochet": ricochet, "rog_fan_of_knives_crit": deadly_aim,
    "rog_fan_of_knives_poison": poisoned_knives, "rog_fan_of_knives_focused": focused_throw,
    "rog_flurry_of_blades_disarm": disarming_strikes, "rog_flurry_of_blades_bolas": fiery_bolas,
    "rog_flurry_of_blades_lightning": shock_assault, "rog_slice_and_dice_adrenaline": adrenaline,
    "rog_slice_and_dice_parry": blade_parry, "rog_slice_and_dice_castspeed": agile_casting,
    "rog_evasion_movespeed": fleet_footed, "rog_evasion_opening": lethal_opening, "rog_evasion_dash": on_the_move,
    "blades_mortal_strike_phantasmal": phantasmal_strike, "blades_mortal_strike_leech": crimson_strike,
    "blades_assassin_executioner": executioner, "blades_assassin_hidden_cuts": hidden_cuts,
    "poison_cloud_evasion": billowing_cloud, "poison_cloud_corrosion": corrosion,
    "poison_mastery_weapons": coated_weapons, "poison_mastery_resistance": deadly_toxins,
    "demolitions_grenade_incendiary": incendiary_grenades, "demolitions_grenade_shock": shock_grenades,
    "demolitions_grenade_dash": explosive_exit, "artificer_suit_zzzap": zzzap, "artificer_suit_shrapnels": shrapnels,
}


# ---------------------------------------------------------------- second pass
def ricochet():
    A = G("0a0c12", "1e2230", (6, 6))
    A.solid(box(22, 12, 3.2, 13), R("141218", "2a2630", "403a48", "5a5262", "7a7082"), seed=3)
    A.streak(2, 22, 17.5, 13, 0.7, SMOKE)
    dagger(A, 11, 7.5, 200, 0.85)
    flash(A, 18.5, 13, 3, VOLT)
    B = G("0c0a12", "201a2c", (12, 12))
    pts = [(1, 20), (8, 5), (14, 19)]
    for i in range(2):
        B.streak(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 0.8 + i * 0.3, STEEL)
    flash(B, 8, 5, 2.2, VOLT)
    flash(B, 14, 19, 2.2, VOLT)
    dagger(B, 18.5, 11, -55, 0.75)
    C = G("0c0a12", "1e1a28", (12, 12))
    C.energy(union(seg(4, 19, 12, 6, 1.2), seg(12, 6, 20, 19, 1.2)), STEEL, falloff=0.9)
    C.energy(poly([(17, 19), (22, 21), (21, 15)]), STEEL, falloff=1.0)
    return A, B, C


def disarming_strikes():
    A = G(*RG, (12, 6))
    sword(A, 12, 12, 115, 0.85)
    for x in (6, 9, 15, 18):
        A.streak(x, 1, x - 1, 6, 0.5, BONE)
    B = G(*RG, (12, 12))
    sword(B, 15, 9, -160, 0.65)
    dagger(B, 7, 17, -45, 0.85)
    flash(B, 11, 13, 2.6, VOLT)
    B.energy(arc(15, 9, 8, 0.9, 200, 300), BONE, falloff=0.5)
    C = G(*RG, (12, 12))
    sword(C, 9, 15, -45, 0.62)
    C.solid(shard(17.5, 6.5, -45, 7, 1.8), STEEL, base=3.4)
    flash(C, 13.2, 10.8, 1.8, BONE)
    return A, B, C


def fiery_bolas():
    A = G("140804", "2e160a", (12, 8))
    A.solid(arc(12, 4, 10, 0.9, 40, 140), LEATHER, base=3.2)
    for k, (x, y) in enumerate(((5, 13), (19, 13), (12, 18))):
        A.solid(circle(x, y, 3.6), LEATHER, base=2.6, seed=k)
        A.energy(ring(x, y, 3.6, 0.7), FIRE, falloff=0.5)
    A.solid(seg(12, 14, 12, 4, 0.45), LEATHER, base=3.2)
    B = G("140804", "2a1408", (12, 14))
    B.solid(box(9, 15, 2.4, 9, 0, 1), LEATHER, base=2.4)
    B.solid(box(15.5, 15, 2.4, 9, 0, 1), LEATHER, base=2.0, seed=2)
    for k in range(3):
        B.energy(ellipse(12, 10 + k * 4, 6.4, 1.3), FIRE, falloff=0.7)
    C = G("140804", "2a1408", (12, 12))
    C.energy(union(circle(6, 15, 3.2), circle(18, 9, 3.2), seg(6, 15, 18, 9, 0.5)), FIRE, falloff=2.2)
    return A, B, C


def shock_assault():
    A = G("141004", "2e2608", (14, 8))
    dagger(A, 12, 12, -45, 1.3)
    bolt(A, [(4, 13), (8, 11), (9, 15), (14, 17)], w=0.6)
    bolt(A, [(12, 4), (16, 7), (20, 6)], w=0.55)
    B = G("100c04", "282008", (12, 12))
    for k, (a0, r) in enumerate(((190, 9), (230, 6.5), (160, 11.5))):
        slash(B, 14, 13, r, a0, a0 + 90, VOLT, 1.6 - k * 0.2)
    C = G("100c04", "2a2208", (12, 12))
    bolt(C, [(15, 1), (8, 11), (14, 12), (8, 23)], w=1.6, fall=1.4)
    return A, B, C


def adrenaline():
    A = G("040818", "0e1a3a", (12, 8))
    potion(A, 12, 13, 1.25, liquid=MANA)
    B = G("040818", "0c1634", (12, 18))
    for k, (x, y, r) in enumerate(((5.5, 18, 2.4), (12, 12.5, 3.0), (18.5, 7, 3.6))):
        B.streak(x, y + 7, x, y + 2, r * 0.5, MANA)
        B.energy(drop(x, y, r), MANA, falloff=r)
    C = G("040818", "0e1a3a", (12, 12))
    for k in range(3):
        y = 17 - k * 5
        C.energy(union(seg(5, y + 3, 12, y - 2, 1.0), seg(12, y - 2, 19, y + 3, 1.0)), MANA, falloff=0.8 + k * 0.2)
    return A, B, C


def blade_parry():
    A = G("0a0c12", "1e2230", (12, 6))
    dagger(A, 12, 12, -45, 1.3, seed=1)
    dagger(A, 12, 12, -135, 1.3, seed=2)
    B = G("0a0c12", "1c2030", (12, 12))
    dagger(B, 8, 15, -30, 1.0)
    dagger(B, 17, 11, 200, 1.0, blade=R("1a0e0a", "3a2016", "6a3a26", "9a5a3a", "c88a64", "f0c8a0"))
    flash(B, 13.5, 10.5, 3.2, VOLT)
    C = G("0a0c12", "1e2230", (12, 12))
    C.energy(cut(poly([(12, 3), (20, 6), (19, 15), (12, 21), (5, 15), (4, 6)]), poly([(12, 6.5), (16.6, 8.2), (16, 14), (12, 17.6), (8, 14), (7.4, 8.2)])), STEEL, falloff=1.0)
    C.energy(poly([(12, 8), (13, 12), (12, 16), (11, 12)]), STEEL, falloff=1.0)
    return A, B, C


def agile_casting():
    A = G("0e0818", "241434", (12, 12))
    A.energy(ring(12, 12, 8, 1.2), ARCANE, falloff=0.8)
    A.energy(cut(star(12, 12, 2.6, 7.2, 5), star(12, 12, 1.4, 5.0, 5)), ARCANE, falloff=0.6)
    for y in (4, 20):
        A.streak(1, y, 8, y, 0.6, ARCANE)
    B = G("0e0818", "221432", (12, 12))
    hourglass(B, 12, 12, 1.25, sand=ARCANE, t=0.7)
    for y in (6, 12, 18):
        B.streak(22, y, 17, y, 0.6, ARCANE)
    C = G("0e0818", "241434", (12, 12))
    pts = [(12 + math.cos(t * 0.5) * t * 0.7, 12 + math.sin(t * 0.5) * t * 0.7) for t in range(1, 15)]
    C.energy(union(*[seg(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 0.5 + i * 0.07) for i in range(len(pts) - 1)]), ARCANE, falloff=0.9)
    return A, B, C


def fleet_footed():
    A = G("0a0c12", "1c2232", (14, 6))
    boot(A, 12, 11, 1.05, wing=BONE)
    B = G("0a0c12", "1c2030", (16, 12))
    for y, x0 in ((6, 0), (11, 0), (16, 1)):
        B.streak(x0, y, x0 + 8, y, 0.8, SPIRIT)
    boot(B, 14, 10, 1.0)
    C = G("0a0c12", "1c2232", (12, 12))
    for k, (x, y) in enumerate(((5, 19), (10, 14), (15, 10), (20, 5))):
        C.energy(ellipse(x + (1.4 if k % 2 else -1.4), y, 1.5, 2.4, 45), SPIRIT if k == 3 else STEEL, falloff=0.9)
    return A, B, C


def lethal_opening():
    A = G("08060c", "1a1024", (16, 8))
    cloud(A, [(6, 16, 5.5), (10, 9, 5), (4, 7, 4)], SHADOW, base=1.6)
    dagger(A, 14, 11, -45, 1.05)
    A.glint(20, 5, CRIMSON[6])
    B = G(*RG, (12, 12))
    B.rays(12, 12, CRIMSON, n=8, lo=1, hi=3.5)
    dagger(B, 11, 13, -45, 1.1)
    C = G(*RG, (12, 12))
    C.energy(cut(circle(11, 12, 8), circle(15, 10, 7)), CRIMSON, falloff=1.6)
    C.glint(17, 16, CRIMSON[6])
    return A, B, C


def ghost(ic, fn, tint, al):
    sb = Icon()
    sb.im = ic.im.copy()
    sb.p = sb.im.load()
    fn(sb)
    for yy in range(N):
        for xx in range(N):
            if sb.p[xx, yy] != ic.p[xx, yy]:
                ic.p[xx, yy] = mix(ic.p[xx, yy], mix(sb.p[xx, yy], tint, 0.5), al)


def on_the_move():
    A = G("0a0c12", "1e2230", (16, 10))
    for x, al in ((7, 0.35), (11, 0.6)):
        ghost(A, lambda ic, x=x: boot(ic, x, 10, 0.85), SPIRIT[3], al)
    boot(A, 15, 10, 0.9)
    B = G("0a0c12", "1c2030", (12, 12))
    B.energy(arc(12, 12, 8.5, 1.8, -60, 220), SPIRIT, falloff=0.9)
    B.energy(poly([(16.5, 4.0), (21.5, 6.5), (17, 10.2)]), SPIRIT, falloff=1)
    boot(B, 11, 11, 0.62)
    C = G("0a0c12", "1e2230", (12, 12))
    for k in range(3):
        x = 5 + k * 6
        C.energy(union(seg(x, 6, x + 4, 12, 1.0), seg(x + 4, 12, x, 18, 1.0)), SPIRIT, falloff=0.7 + k * 0.25)
    return A, B, C


def phantasmal_strike():
    A = G("040c14", "0e2232", (14, 8))
    sword(A, 12, 12, -45, 1.0, blade=SPIRIT, hilt=SPIRIT, guard=SPIRIT)
    B = G("040c14", "0c1e2c", (6, 12))
    for k, (x, y, a) in enumerate(((17, 5, -25), (19, 12, 0), (17, 19, 25))):
        sword(B, x, y, a, 0.42, blade=SPIRIT, hilt=SPIRIT, guard=SPIRIT, seed=k)
    sword(B, 6, 12, 0, 0.5)
    C = G("040c14", "0e2232", (12, 12))
    for k, dx in enumerate((-5, -2.5)):
        C.energy(poly([(4 + dx, 21), (17 + dx, 6), (21 + dx, 3), (19 + dx, 8), (6 + dx, 22)]), SPIRIT[:4 + k], falloff=1.0)
    C.energy(poly([(4, 21), (17, 6), (21, 3), (19, 8), (6, 22)]), SPIRIT, falloff=1.4)
    return A, B, C


def crimson_strike():
    A = G(*RG, (14, 6))
    sword(A, 12, 12, -45, 1.0, blade=R("2a0a0e", "5a1018", "8e1a24", "c02a30", "e8786a", "ffd0c0"))
    for x, y in ((7, 19), (5, 22.5)):
        A.energy(drop(x, y, 1.2), CRIMSON, falloff=1)
    B = G(*RG, (12, 14))
    B.solid(heart(12, 15, 6.5), CRIMSON, base=3.6)
    for x, y in ((4, 4), (12, 2.5), (20, 4)):
        B.energy(drop(x, y + 1, 1.4), CRIMSON, falloff=1)
    B.glint(9, 12)
    C = G(*RG, (12, 12))
    C.energy(drop(12, 13.5, 6.0), CRIMSON, falloff=4)
    return A, B, C


def hidden_cuts():
    A = G("06040a", "140e1e", (12, 12))
    cloud(A, [(12, 13, 8), (6, 8, 4.5), (18, 7, 4.5)], SHADOW, base=1.4)
    dagger(A, 12, 12, -45, 1.1)
    B = G("08060c", "180e1e", (12, 12))
    for x, y, a in ((7, 7, 200), (17, 9, 260), (10, 18, 160)):
        slash(B, x + 3, y + 3, 4.5, a, a + 80, CRIMSON, 1.4)
    B.solid(ellipse(12, 12, 2.4, 5.4), SHADOW, base=2.6)
    C = G("08060c", "1a1022", (12, 12))
    for k in range(3):
        C.energy(seg(5 + k * 5, 19, 9 + k * 5, 5, 0.9), CRIMSON, falloff=0.7)
    return A, B, C


def zzzap():
    A = G("100c04", "282008", (12, 14))
    gauntlet(A, 12, 14, 1.15, rmp=BRASS)
    bolt(A, [(11, 9), (8, 5), (12, 3), (10, 0)], w=0.8)
    bolt(A, [(16, 10), (19, 6), (22, 7)], w=0.6)
    B = G("0c0a04", "221c08", (12, 4))
    bolt(B, [(13, 0), (9, 8), (14, 10), (10, 20)], w=1.2)
    flash(B, 10, 20, 3.4, VOLT)
    C = G("100c04", "2a2208", (12, 12))
    C.energy(union(seg(4, 8, 9, 15, 1.1), seg(9, 15, 14, 8, 1.1), seg(14, 8, 19, 15, 1.1)), VOLT, falloff=0.9)
    return A, B, C


ORBS = {k: globals()[v.__name__] for k, v in ORBS.items()}
