"""The other Firearms icons (skills, orbs, attacks, HUD), vanilla style, three ideas each."""
import math
from vpaint import *
from motifs import *
from fa import pineapple, canister, blast, shards

ELEMS = [FIRE, ICE, VOLT, TOXIC]


def G(dark, mid, light=(8, 6)):
    return Icon().ground(dark, mid, light=light)


def tracer(ic, x0, y0, x1, y1, w=0.9, rmp=GOLD):
    ic.streak(x0, y0, x1, y1, w, rmp)


# ---------------------------------------------------------------- core skills
def reload():
    A = G("0a0c14", "1e2434", (14, 6))
    pistol(A, 13, 7, 0, 1.25)
    mag(A, 10.5, 17.5, 0, 1.0, GUN, h=10, w=2.6, top_round=False)
    for x in (6, 15):
        A.streak(x, 24, x, 17, 0.7, SMOKE)
    B = G("0a0c14", "1e2434", (12, 12))
    mag(B, 9, 9, -25, 0.95, GUN, h=12, w=3.2, top_round=False)
    for k, (x, y, a) in enumerate(((16, 15, 30), (13, 20, -60), (19, 21, 80))):
        cartridge(B, x, y, a, 0.5, tip=BRASS, seed=k, length=8, w=2.4)
    C = G("0a0c14", "1a2030", (12, 12))
    C.solid(ring(12, 12, 9, 2.2), STEEL, base=2.2)
    C.energy(inter(ring(12, 12, 9, 2.3), lambda x, y: -1 if math.atan2(y - 12, x - 12) > -0.6 else 1), ARCANE, falloff=1.2)
    mag(C, 12, 13, 0, 0.8, GUN, h=12, w=4, top_round=True)
    return A, B, C


def snipe():
    A = G("0c1008", "222c16", (8, 6))
    rifle(A, 12, 12, -35, 1.1, scope=True)
    B = G("06080c", "141a24", (19, 5))
    B.streak(0, 22, 18, 6, 1.4, R("100c04", "4a3a10", "c09030", "ffe070", "fffbe0", "ffffff"))
    slug(B, 19.5, 4.5, -42, 1.1, STEEL)
    B.glow(20, 4, 6, "ffe070", 0.6)
    C = G("0c1008", "1e2614", (12, 12))
    C.energy(cut(union(ring(12, 12, 8.5, 1.2), box(4, 12, 3, 1), box(20, 12, 3, 1), box(12, 4, 1, 3), box(12, 20, 1, 3),
                       box(12, 12, 5, 0.35), box(12, 12, 0.35, 5)), circle(12, 12, 0.01)), R("101408", "3a4a1c", "8aa040", "d0e080", "ffffff"), falloff=0.7)
    C.energy(circle(12, 12, 0.9), BLOOD, falloff=0.9)
    return A, B, C


def critical_aim():
    A = G("100c04", "2a2008", (12, 12))
    A.solid(circle(12, 12, 10), GUN, seed=1)
    A.solid(circle(12, 12, 7.4), R("1a1004", "4a3008", "8a6010", "c89a20", "f0d060", "fff4c0"), seed=2, light=(-0.6, -0.8))
    A.paint(union(box(12, 12, 7.4, 0.35), box(12, 12, 0.35, 7.4)), lambda x, y, d: BLACK)
    A.glint(9, 8)
    B = G("0e0a04", "241c0a", (12, 12))
    eye(B, 12, 12, 1.15, GOLD)
    for x in range(2, 22):
        B.px([(x, 6 - int(2 * max(0, 1 - ((x - 12) / 10) ** 2)))], WOOD[1])
    C = G("100c04", "2a2008", (12, 12))
    for k in range(4):
        r = 10 - k * 2.4
        C.energy(inter(ring(12, 12, r, 1.0), lambda x, y, k=k: -1 if (math.atan2(y - 12, x - 12) + k) % 1.6 < 1.0 else 1), GOLD, falloff=0.6)
    C.energy(poly([(12, 8), (13, 11), (16, 12), (13, 13), (12, 16), (11, 13), (8, 12), (11, 11)]), GOLD, falloff=1.5)
    return A, B, C


def focus_hud():
    return critical_aim()


def rocket_():
    A = G("140804", "2e1608", (14, 8))
    tube(A, 11, 13, -30, 0.95)
    rocket(A, 19, 8.5, -30, 0.55, fins=False)
    B = G("0c0806", "221810", (18, 6))
    for k in range(9):
        t = k / 8
        B.solid(circle(2 + t * 12, 22 - t * 12, 1 + t * 2.2), SMOKE, base=1.6 + t * 1.6, spread=0.8, seed=k)
    B.energy(flame(14, 12, 2.2, 5, 0, 2), FIRE, falloff=1.5)
    rocket(B, 17, 7, -45, 0.8)
    C = G("140604", "2e1006", (12, 12))
    C.glow(12, 12, 12, "ff6010", 0.8)
    rocket(C, 12.5, 11.5, -45, 1.25)
    return A, B, C


def scavenger():
    A = G("0c0a14", "1e1a2e", (12, 8))
    for k, (rm, x) in enumerate(zip(ELEMS, (4.5, 9.5, 14.5, 19.5))):
        cartridge(A, x, 13 + (k % 2), -90, 0.85, tip=rm, seed=k, length=14, w=2.2)
    B = G("08060e", "18142a", (6, 16))
    for k, (rm, a) in enumerate(zip(ELEMS, (-58, -40, -22, -4))):
        r = math.radians(a)
        B.streak(3, 19, 3 + math.cos(r) * 20, 19 + math.sin(r) * 20, 1.3, rm)
    flash(B, 3, 19, 3)
    C = G("0a0a0e", "1a1a22", (12, 12))
    for k, rm in enumerate(ELEMS):
        C.glow(12 + (6 if k % 3 else -6) * (1 if k < 2 else 1), 12 + (-6 if k < 2 else 6), 9, rm[4], 0.5)
    cartridge(C, 12, 12, -55, 1.5, tip=R("1a1a20", "4a3a5a", "8a6aa0", "c0a0e0", "f0e0ff"))
    return A, B, C


def dodge_skip():
    A = G("0e0a18", "241a3a", (16, 10))
    for y, x0 in ((7, 1), (11, 3), (15, 0), (19, 4)):
        A.streak(x0, y, x0 + 9, y, 0.9, ARCANE)
    mag(A, 16, 13, 15, 1.0, GUN, h=13, w=3.4, top_round=False)
    B = G("0e0a18", "241a3a", (16, 12))
    for k, (x, al) in enumerate(((5, 0.25), (10, 0.5))):
        sb = Icon(); sb.im = B.im.copy(); sb.p = sb.im.load()
        soldier(sb, x, 12, 0.8, arms_up=False)
        for yy in range(N):
            for xx in range(N):
                B.p[xx, yy] = mix(B.p[xx, yy], mix(sb.p[xx, yy], ARCANE[3], 0.5), al)
    soldier(B, 16, 12, 0.85, arms_up=False)
    C = G("0e0a18", "221838", (12, 12))
    C.energy(lambda x, y: abs(math.hypot(x - 12, y - 12) - 7.5) - 1.6 + (0 if math.atan2(y - 12, x - 12) < 1.8 else 4), ARCANE, falloff=1.4)
    C.energy(poly([(17, 15), (21, 12.5), (21, 18.5)]), ARCANE, falloff=1.2)
    mag(C, 12, 12, 0, 0.6, GUN, h=12, w=4, top_round=False)
    return A, B, C


def explosive_reload():
    A = G("140604", "34100a", (12, 6))
    mag(A, 11, 14, -10, 1.0, GUN, h=15, w=3.6, top_round=False)
    dyn(A, 15.5, 13, -90, 1.0, length=12, w=1.6)
    A.solid(box(12.5, 13, 6.5, 0.9, -10, 0.2), PAPER, base=2.2, spread=0.6)
    A.energy(circle(16, 5, 1.3), FIRE, falloff=1.3)
    A.glow(16, 5, 6, "ffa040", 0.9)
    B = G("140804", "3a1608", (12, 12))
    B.rays(12, 12, EMBER, n=7, lo=0, hi=3)
    blast(B, 12, 12, 6.5, FIRE, 7, hole=2)
    for k in range(6):
        a = math.radians(k * 60 + 15)
        cartridge(B, 12 + math.cos(a) * 9, 12 + math.sin(a) * 9, k * 60 + 15, 0.45, tip=COPPER, seed=k, length=9, w=2.4)
    C = G("120604", "2a0e06", (12, 12))
    C.glow(12, 15, 12, "ff6010", 0.9)
    C.energy(lambda x, y: math.hypot(x - 12, y - 17) - 7 * (0.55 + 0.45 * abs(math.cos(math.atan2(y - 17, x - 12) * 4))), FIRE, falloff=4)
    mag(C, 12, 9, 0, 0.75, GUN, h=12, w=4, top_round=False)
    return A, B, C


def headshot():
    A = G("140406", "340a0e", (16, 6))
    A.glow(16, 6, 8, "f04a3a", 0.8)
    cartridge(A, 12, 12, -45, 1.5, tip=BLOOD)
    B = G("100c08", "2a2218", (14, 8))
    B.solid(inter(ellipse(12, 15, 10, 9), lambda x, y: y - 16), OLIVE, seed=1)
    B.solid(box(12, 16, 10.5, 1.4, 0, 0.5), OLIVE, base=1.6)
    B.paint(circle(15, 9, 1.5), lambda x, y, d: BLACK)
    B.energy(lambda x, y: math.hypot(x - 17, y - 7) - 3 * (0.4 + 0.6 * abs(math.cos(math.atan2(y - 7, x - 17) * 3))), BLOOD, falloff=2)
    C = G("100406", "2a0a0e", (12, 12))
    skull(C, 12, 12, 1.3, BONE)
    C.paint(circle(13.5, 7.5, 1.2), lambda x, y, d: BLACK)
    C.energy(lambda x, y: math.hypot(x - 13.5, y - 7.5) - 2.6, BLOOD, falloff=0.8) if False else None
    for (x, y) in ((14, 9), (14, 10), (15, 11)):
        C.px([(x, y)], BLOOD[3])
    return A, B, C


def piercing():
    STL = R("12141a", "2a2e38", "4e5464", "7c8496", "b8c0d0", "f0f4ff")
    A = G("0c0e12", "1e222a", (16, 6))
    cartridge(A, 12, 12, -45, 1.55, tip=STL)
    A.glint(18, 5)
    B = G("0c0e12", "1e222a", (12, 12))
    for k, x in enumerate((4, 12, 20)):
        B.solid(box(x, 12, 1.3, 7.5 - k * 0.6, 0, 0.3), WOOD, base=2.8 - k * 0.5, seed=k)
    B.streak(0, 12, 23, 12, 0.9, R("100c04", "4a3a10", "c09030", "ffe070", "ffffff"))
    for x in (4, 12, 20):
        B.px([(x, 12), (x + 1, 12)], BLACK)
    C = G("0c0e12", "1a1e26", (12, 12))
    C.solid(cut(box(12, 12, 8.5, 8.5, 0, 0.6), circle(12, 12, 2)), STEEL, seed=2)
    for k in range(6):
        a = math.radians(k * 60 + 10)
        C.solid(seg(12 + math.cos(a) * 2, 12 + math.sin(a) * 2, 12 + math.cos(a) * 6, 12 + math.sin(a) * 6, 0.35), STEEL[:2], base=0.5)
    C.energy(circle(12, 12, 1.6), GOLD, falloff=1.6)
    C.glow(12, 12, 6, "ffe070", 0.8)
    return A, B, C


def fat_boy():
    def fat(ic, cx, cy, ang, s):
        items = [
            (lambda u, v: poly([(-9, -6), (-5, -3), (-5, 3), (-9, 6), (-7.5, 0)])(u, v), STEEL, {"base": 2}),
            (lambda u, v: ellipse(1, 0, 8, 5.8)(u, v), OLIVE, {}),
            (lbox(-2.5, 0, 0.7, 5.4, 0.2), GOLD, {}),
        ]
        parts(ic, cx, cy, ang, s, items)
    A = G("0a1406", "1e3010", (10, 8))
    fat(A, 12, 12, -40, 1.1)
    B = G("141206", "2e2a0c", (12, 10))
    B.glow(12, 9, 11, "7cc434", 0.8)
    B.solid(box(12, 17, 2.6, 6, 0, 1), GAS, base=2.6, spread=1)
    for k, (x, y, r) in enumerate(((12, 8, 6), (6.5, 9.5, 3.6), (17.5, 9.5, 3.6), (12, 4, 3.8))):
        B.solid(circle(x, y, r), TOXIC, base=3.4, spread=1.4, seed=k)
    for k, (x, r) in enumerate(((5, 3.5), (12, 4.2), (19, 3.5))):
        B.solid(ellipse(x, 22.5, r * 1.5, 2.2), GAS, base=2, seed=k + 5)
    C = G("061006", "142a10", (12, 12))
    C.glow(12, 12, 12, "7cc434", 0.7)
    fat(C, 12, 12, -90, 1.2)
    return A, B, C


def quad_missile():
    A = G("140804", "2a1608", (8, 6))
    A.solid(box(12, 12, 9.5, 9.5, 0, 1.4), OLIVE, seed=1)
    for k, (x, y) in enumerate(((7.5, 7.5), (16.5, 7.5), (7.5, 16.5), (16.5, 16.5))):
        A.solid(circle(x, y, 3.4), GUN, base=0.8, spread=0.5, rim=0, core=0)
        A.solid(circle(x, y, 2.2), BLOOD, seed=k)
    B = G("0c0806", "221810", (14, 8))
    for k, a in enumerate((-78, -58, -38, -18)):
        r = math.radians(a)
        x, y = 3 + math.cos(r) * 15, 21 + math.sin(r) * 15
        B.streak(3, 21, x - math.cos(r) * 3, y - math.sin(r) * 3, 1.1, SMOKE)
        rocket(B, x, y, a, 0.45, seed=k)
    C = G("140604", "2e1006", (12, 12))
    C.glow(12, 12, 12, "ff6010", 0.6)
    for k in range(4):
        rocket(C, 4.5 + k * 5, 12 + (2 if k % 2 else -2), -90, 0.7, seed=k)
    return A, B, C


# ---------------------------------------------------------------- attacks
def rifle_attack():
    A = G("0a0c14", "1e2434", (16, 6))
    rifle(A, 11, 13, -35, 1.0)
    flash(A, 20, 6.5, 3)
    B = G("0c0a06", "221c10", (18, 10))
    for k, y in enumerate((6, 12, 18)):
        tracer(B, 0 + k * 2, y + 2, 19 + k, y - 1, 0.8)
        slug(B, 20 + k, y - 1.2, -9, 0.7, COPPER, seed=k)
    C = G("0a0c14", "1a2030", (12, 12))
    C.glow(12, 12, 11, "4a5a8a", 0.6)
    rifle(C, 12, 12, -90, 1.0)
    return A, B, C


def glock_attack():
    A = G("0a0c14", "1e2434", (16, 8))
    pistol(A, 11, 10, 0, 1.3)
    flash(A, 21.5, 9.5, 3)
    B = G("0a0c14", "1e2434", (12, 8))
    pistol(B, 10, 14, -12, 1.2)
    cartridge(B, 13, 5, 60, 0.5, tip=BRASS, case=BRASS, length=8, w=2.6)
    for (x, y) in ((11, 8), (10, 6)):
        B.px([(x, y)], SMOKE[3])
    C = G("0a0c14", "1a2030", (12, 12))
    C.glow(12, 12, 11, "4a5a8a", 0.6)
    pistol(C, 12, 10, -30, 1.35)
    return A, B, C


def glock_dual():
    A = G("0a0c14", "1e2434", (12, 6))
    pistol(A, 9, 15, -40, 1.1, flip=True)
    pistol(A, 15, 15, -140, 1.1)
    B = G("0c0a06", "221c10", (12, 12))
    pistol(B, 16, 10, 0, 1.0)
    pistol(B, 8, 15, 180, 1.0, flip=True)
    flash(B, 23, 9.5, 2.6)
    flash(B, 1, 15.5, 2.6)
    C = G("0a0c14", "1a2030", (12, 12))
    for k, a in enumerate((-60, -120)):
        r = math.radians(a)
        C.streak(12, 18, 12 + math.cos(r) * 13, 18 + math.sin(r) * 13, 1.4, GOLD)
    flash(C, 12, 18, 3)
    return A, B, C


def gl_attack():
    A = G("0a0c14", "1e2434", (14, 8))
    rifle(A, 12, 12, -35, 1.05, gl=True)
    cut40(A, 18.5, 18.5, -60, 0.75)
    B = G("100c06", "2a2210", (16, 12))
    for k in range(8):
        t = k / 7
        B.px([(int(2 + t * 13), int(21 - math.sin(t * 2.6) * 14))], SMOKE[4])
    cut40(B, 17, 11, 60, 0.95)
    C = G("100c06", "26200e", (12, 12))
    C.glow(12, 12, 11, "8a9a3a", 0.6)
    cut40(C, 12, 12, -90, 1.7)
    return A, B, C


# ---------------------------------------------------------------- reload family / HUD
def steady():
    A = G("0a0c14", "1e2434", (12, 6))
    mag(A, 12, 13, 0, 1.0, GUN, h=21, w=3.6, top_round=True)
    for y in range(5, 20, 3):
        A.px([(12, y)], BRASS[4])
    B = G("100c04", "2a2008", (12, 12))
    for k in range(7):
        cartridge(B, 10 + (k % 2) * 2, 21 - k * 3, 180, 0.55, tip=COPPER, seed=k, length=14, w=2.6)
    B.glint(18, 2)
    C = G("100c04", "2a2008", (12, 12))
    C.glow(12, 12, 12, "ffd060", 0.6)
    for k in range(5):
        cartridge(C, 4 + k * 4, 12, -90, 0.8, tip=GOLD if k == 4 else COPPER, seed=k, length=16, w=2.2)
    return A, B, C


def steady_crit():
    A = G("100c04", "2a2008", (12, 6))
    mag(A, 12, 13, 0, 1.0, GUN, h=21, w=3.6, top_round=True)
    for y in range(5, 20, 3):
        A.px([(12, y)], GOLD[5])
    A.glow(12, 12, 8, "ffd060", 0.4)
    B = G("140406", "300a0e", (12, 12))
    for k in range(7):
        cartridge(B, 10 + (k % 2) * 2, 21 - k * 3, 180, 0.55, tip=BLOOD, seed=k, length=14, w=2.6)
    B.energy(poly([(18, 1), (19, 4), (22, 5), (19, 6), (18, 9), (17, 6), (14, 5), (17, 4)]), GOLD, falloff=1.4)
    C = G("140406", "2a0a0e", (12, 12))
    C.glow(12, 12, 12, "f04a3a", 0.6)
    for k in range(5):
        cartridge(C, 4 + k * 4, 12, -90, 0.8, tip=BLOOD, seed=k, length=16, w=2.2)
    C.energy(poly([(20, 1), (21, 4), (24, 5), (21, 6), (20, 9), (19, 6), (16, 5), (19, 4)]), GOLD, falloff=1.4)
    return A, B, C


def clip_hud():
    A = G("0a0c14", "1e2434", (12, 8))
    for k in range(5):
        cartridge(A, 4 + k * 4, 12, -90, 0.8, tip=COPPER, seed=k, length=16, w=2.2)
    B = G("0a0c14", "1e2434", (12, 12))
    mag(B, 12, 13, 0, 1.0, GUN, h=19, w=5.2, top_round=False)
    for k in range(5):
        cartridge(B, 11.4 + (k % 2) * 1.2, 7 + k * 3, 180, 0.5, tip=COPPER, seed=k, length=14, w=2.6)
    C = G("0a0c14", "1a2030", (12, 12))
    C.glow(12, 12, 11, "4a5a8a", 0.6)
    cartridge(C, 12, 12, -90, 1.55, tip=COPPER)
    return A, B, C


def reloading_hud():
    A = G("0e0a18", "241a3a", (12, 6))
    mag(A, 12, 16, 0, 1.0, GUN, h=13, w=4.2, top_round=False)
    for k, y in enumerate((2, 6.5)):
        cartridge(A, 12, y, -90, 0.5, tip=COPPER, seed=k, length=8, w=2.6)
    B = G("0e0a18", "241a3a", (12, 12))
    B.solid(ring(12, 12, 9.2, 2.2), GUN, base=1.6)
    B.energy(inter(ring(12, 12, 9.2, 2.3), lambda x, y: -1 if math.atan2(y - 12, x - 12) < 0.6 else 1), ARCANE, falloff=1.2)
    C = G("0e0a18", "221838", (12, 14))
    mag(C, 12, 12, 0, 1.0, GUN, h=18, w=4.6, top_round=False)
    C.energy(box(12, 16.5, 3.4, 3.8, 0, 0.6), ARCANE, falloff=2)
    return A, B, C


def grenade_charges_hud():
    A = G("0e1008", "262c14", (12, 6))
    A.solid(seg(-1, 7, 25, 7, 1.8), WOOD, base=2)
    for k, x in enumerate((5, 12, 19)):
        pineapple(A, x, 15, 3.6, 4.4, OLIVE, seed=k)
    B = G("0e1008", "262c14", (12, 12))
    for k, (x, y) in enumerate(((7, 16), (17, 16), (12, 9))):
        pineapple(B, x, y, 4.6, 5.4, OLIVE, seed=k)
    C = G("0e1008", "222812", (12, 12))
    C.glow(12, 13, 11, "84963a", 0.6)
    pineapple(C, 12, 13.5, 7.5, 8.6, OLIVE)
    return A, B, C


def rocket_charges_hud():
    A = G("140804", "2a1608", (12, 6))
    for k, x in enumerate((6, 12, 18)):
        rocket(A, x, 12, -90, 0.85, seed=k)
    A.solid(box(12, 17, 11, 1, 0, 0.3), GUN, base=2)
    B = G("140804", "2a1608", (12, 6))
    for k, x in enumerate((6, 12, 18)):
        rocket(B, x, 9, -90, 0.7, fins=False, seed=k)
    crate(B, 1, 13, 23, 23.5)
    C = G("140604", "2e1006", (12, 12))
    C.glow(12, 12, 12, "ff6010", 0.6)
    rocket(C, 12, 12, -90, 1.3)
    return A, B, C


def gl_charges_hud():
    A = G("100c06", "2a2210", (12, 8))
    for k, x in enumerate((5, 12, 19)):
        cut40(A, x, 12, -90, 1.0, seed=k)
    B = G("100c06", "2a2210", (12, 12))
    B.solid(circle(12, 12, 10.5), GUN, seed=1)
    for k in range(6):
        a = math.radians(k * 60 - 90)
        B.solid(circle(12 + math.cos(a) * 6.2, 12 + math.sin(a) * 6.2, 2.8), OLIVE, seed=k + 2)
    B.solid(circle(12, 12, 1.6), STEEL, base=2)
    C = G("100c06", "26200e", (12, 12))
    C.glow(12, 12, 11, "8a9a3a", 0.6)
    cut40(C, 12, 12, -90, 1.7)
    return A, B, C


# ---------------------------------------------------------------- shotgun
def burst():
    A = G("0e0c0a", "26201a", (8, 6))
    A.solid(box(12, 12, 11, 7, 0, 2), GUN, seed=1)
    for x in (7, 17):
        A.solid(circle(x, 12, 5), STEEL, seed=2)
        A.paint(circle(x, 12, 3.2), lambda X, Y, d: BLACK)
    B = G("140804", "34180a", (6, 13))
    B.glow(5, 13, 12, "ff9030", 0.8)
    for k in range(30):
        a = math.radians(-28 + h2(k, 3) * 56)
        r = 5 + h2(k, 4) * 18
        B.px([(int(3 + math.cos(a) * r), int(13 + math.sin(a) * r))], GOLD[5] if k % 3 else WHITE)
    flash(B, 3, 13, 3.5)
    C = G("100406", "2a0a0e", (12, 12))
    C.glow(12, 12, 11, "c8301e", 0.5)
    shell(C, 8, 12, -90, 1.4, seed=1)
    shell(C, 16, 12, -90, 1.4, seed=2)
    return A, B, C


def burst_breath():
    A = G("140604", "34100a", (16, 6))
    A.glow(17, 5, 9, "ff6010", 0.9)
    A.energy(flame(17.5, 9, 3.4, 9, 1, 2), FIRE, falloff=2)
    shell(A, 12, 14, -60, 1.4)
    B = G("140604", "34100a", (12, 12))
    B.glow(10, 12, 13, "ff6010", 0.8)
    B.energy(lambda x, y: (abs(y - 12) - (x * 0.55 + 0.5) * (0.85 + 0.15 * math.sin(x * 1.3))) if x > 0 else 1, FIRE, falloff=4.5)
    C = G("120604", "2a0e06", (12, 12))
    C.glow(14, 12, 12, "ff6010", 0.7)
    dragon = union(ellipse(8, 12, 6.5, 4.5), poly([(9, 8), (20, 9.5), (20, 12), (11, 14)]), poly([(9, 14), (18, 15), (17, 17.5), (8, 16.5)]),
                   poly([(4, 9), (1, 3), (7, 8)]), poly([(7, 8), (6, 2), (10, 8)]))
    C.solid(dragon, R("120806", "2a120a", "4a1e10", "6e2c16", "963e20", "c0582c"), seed=2)
    C.energy(poly([(19, 12.5), (24, 9), (24, 17)]), FIRE, falloff=2)
    C.energy(circle(10, 10.5, 0.8), GOLD, falloff=0.8)
    return A, B, C


def burst_triple():
    A = G("0e0c0a", "26201a", (8, 6))
    A.solid(circle(12, 12, 10.5), GUN, seed=1)
    for (x, y) in ((7.5, 9), (16.5, 9), (12, 17)):
        A.solid(circle(x, y, 4.2), STEEL, seed=2)
        A.paint(circle(x, y, 2.6), lambda X, Y, d: BLACK)
    B = G("0c0a06", "221c10", (12, 12))
    for k, (x, y, a) in enumerate(((6, 13, -120), (12, 9, -90), (18, 13, -60))):
        shell(B, x, y, a, 1.0, seed=k)
    for k, (x, y) in enumerate(((5, 4), (12, 1), (19, 4))):
        B.solid(circle(x, y, 1.8), SMOKE, base=2.4, seed=k)
    C = G("100406", "2a0a0e", (12, 12))
    C.glow(12, 12, 11, "c8301e", 0.5)
    for k, x in enumerate((5.5, 12, 18.5)):
        shell(C, x, 12, -90, 1.3, seed=k)
    return A, B, C


# ---------------------------------------------------------------- adrenaline
def adrenaline():
    A = G("140406", "340a0e", (12, 8))
    A.glow(12, 12, 9, "c02424", 0.6)
    syringe(A, 12, 12, -45, 1.15, BLOOD)
    B = G("140406", "340a0e", (12, 12))
    B.glow(12, 12, 12, "f04a3a", 0.7)
    for r in (10.5, 8.6):
        B.energy(inter(ring(12, 12, r, 0.8), lambda x, y: abs(abs(math.atan2(y - 12, x - 12)) - 1.57) - 0.8), BLOOD, falloff=0.6)
    B.solid(heart(12, 12.5, 6.4), BLOOD, seed=1)
    C = G("140406", "2a080c", (12, 14))
    pts = [(0, 14), (6, 14), (8, 9), (10, 19), (13, 4), (15, 16), (17, 14), (24, 14)]
    C.energy(union(*(seg(*pts[i], *pts[i + 1], 0.6) for i in range(len(pts) - 1))), BLOOD, falloff=0.8)
    C.glow(12, 12, 8, "f04a3a", 0.5)
    return A, B, C


def adrenaline_crit():
    A = G("100c04", "2a2008", (12, 8))
    A.glow(12, 12, 9, "e8b82a", 0.6)
    syringe(A, 12, 12, -45, 1.15, GOLD)
    A.glint(19, 4)
    B = G("140406", "340a0e", (12, 12))
    B.solid(heart(12, 13, 6.4), BLOOD, seed=1)
    B.energy(poly([(16, 3), (17.3, 7.7), (22, 9), (17.3, 10.3), (16, 15), (14.7, 10.3), (10, 9), (14.7, 7.7)]), GOLD, falloff=2)
    C = G("100406", "2a0a0e", (12, 12))
    pts = [(0, 14), (6, 14), (8, 9), (10, 19), (13, 4), (15, 16), (17, 14), (24, 14)]
    C.energy(union(*(seg(*pts[i], *pts[i + 1], 0.6) for i in range(len(pts) - 1))), GOLD, falloff=0.8)
    C.glow(13, 5, 6, "ffe070", 0.8)
    return A, B, C


def epipen(ic, cx, cy, ang, s=1.0):
    items = [
        (lbox(-7, 0, 2.2, 2.3, 0.6), R("0a1a30", "143a6a", "2a64a8", "4a90d0", "8ac0f0", "d0ecff"), {}),
        (lbox(1.5, 0, 6.5, 2.3, 0.6), VOLT, {}),
        (lbox(2, 0, 2.2, 2.35, 0.2), PAPER, {"base": 4}),
        (lbox(8.6, 0, 0.8, 2.1, 0.4), COPPER, {}),
    ]
    parts(ic, cx, cy, ang, s, items)


def adrenaline_epipen():
    A = G("100e04", "2a2608", (12, 8))
    A.glow(12, 12, 9, "e0c028", 0.5)
    epipen(A, 12, 12, -45, 1.15)
    B = G("100e04", "262208", (12, 18))
    epipen(B, 12, 9, 90, 1.0)
    for a in (-160, -125, -55, -20):
        r = math.radians(a + 180)
        B.streak(12 + math.cos(r) * 3, 20 + math.sin(r) * 1.5, 12 + math.cos(r) * 8, 20 + math.sin(r) * 4, 0.8, VOLT)
    C = G("100e04", "262208", (12, 12))
    C.glow(12, 12, 12, "e0c028", 0.6)
    for k, x in enumerate((-6, -1)):
        C.solid(seg(4, 18 + x * 0.3, 20, 6 + x * 0.3, 0.6 - k * 0.2), VOLT, base=4 - k)
    soldier(C, 13, 12, 0.75, arms_up=False)
    return A, B, C


def adrenaline_hud():
    A = G("140406", "340a0e", (12, 8))
    A.solid(box(12, 13, 4.5, 8, 0, 1.4), PAPER, base=3.4, spread=1)
    A.solid(box(12, 15, 3.4, 5.4, 0, 1), BLOOD, seed=1)
    A.solid(box(12, 4, 3, 1.6, 0, 0.4), STEEL, base=3)
    B = G("140406", "340a0e", (12, 12))
    B.glow(12, 12, 12, "f04a3a", 0.7)
    B.solid(heart(12, 12.5, 7), BLOOD, seed=1)
    C = G("140406", "2a080c", (12, 12))
    syringe(C, 12, 12, -90, 1.25, BLOOD)
    return A, B, C


# ---------------------------------------------------------------- turret family
def turret_():
    A = G("061214", "123034", (10, 8))
    turret(A, 1, 4, 1.1)
    flash(A, 22, 9, 2.6)
    B = G("061214", "123034", (12, 14))
    turret(B, 3, 2, 1.0)
    for k, (x, y, r) in enumerate(((3, 21, 3), (12, 22.5, 3.6), (20, 21, 3))):
        B.solid(ellipse(x, y, r * 1.4, r * 0.7), SMOKE, base=3, seed=k)
    for x in (5, 18):
        B.streak(x, 0, x, 5, 0.6, SMOKE)
    C = G("061214", "10282c", (12, 12))
    C.glow(12, 12, 11, "40a8a4", 0.6)
    turret(C, 2.5, 4, 1.0)
    return A, B, C


def my_turret():
    A = G("061214", "123034", (10, 8))
    A.glow(10, 10, 12, "8ae0d4", 0.8)
    turret(A, 1, 4, 1.1, accent=TEAL)
    B = G("040c0c", "0e2224", (12, 14))
    B.energy(lambda x, y: abs(math.hypot((x - 12) / 11, (y - 19.5) / 3.2) - 1) * 3 - 0.45, TEAL, falloff=0.6)
    turret(B, 3, 2, 1.0, accent=TEAL)
    B.glow(10, 8, 7, "8ae0d4", 0.5)
    C = G("061214", "10282c", (12, 12))
    C.solid(heart(12, 12.5, 9), TEAL, seed=3, base=2.2, spread=1.4)
    turret(C, 3, 4, 0.95, accent=TEAL)
    return A, B, C


def turret_reinforced():
    A = G("061214", "123034", (10, 8))
    turret(A, 1, 4, 1.1)
    A.solid(box(8, 10, 6.5, 4.2, 0, 1), STEEL, seed=4)
    for (x, y) in ((3, 7), (13, 7), (3, 13), (13, 13)):
        A.px([(x, y)], STEEL[5])
    B = G("061214", "123034", (12, 12))
    turret(B, 5, 4, 1.0)
    B.solid(box(11, 10, 6, 4, 0, 1), STEEL, seed=4)
    for k, (y, x) in enumerate(((6, 4), (11, 3), (15, 5))):
        B.streak(-1, y + 1, x, y, 0.6, GOLD)
        B.glint(x + 1, y, GOLD[5])
    C = G("061214", "10282c", (12, 12))
    C.solid(poly([(12, 1), (22, 4), (21, 13), (12, 23), (3, 13), (2, 4)]), STEEL, seed=2)
    C.solid(poly([(12, 3), (20, 5.5), (19.2, 12.6), (12, 20.6), (4.8, 12.6), (4, 5.5)]), TEAL, seed=3, base=2.4)
    turret(C, 3.5, 4.5, 0.9)
    return A, B, C


def turret_second():
    A = G("061214", "123034", (12, 8))
    turret(A, -3, 0, 0.9)
    turret(A, 7, 8, 0.9)
    B = G("061214", "123034", (12, 12))
    turret(B, -3, 8, 0.9)
    turret(B, 8, -1, 0.85)
    for x in (12, 19):
        B.streak(x, 14, x, 20, 0.6, SMOKE)
    C = G("061214", "10282c", (12, 12))
    for k, (x, y) in enumerate(((7, 12), (17, 12))):
        C.glow(x, y, 8, "40a8a4", 0.5)
    turret(C, -1, 4, 0.75)
    turret(C, 9, 4, 0.75)
    return A, B, C


def myturret_feed():
    A = G("061214", "123034", (10, 6))
    turret(A, 4, 0, 1.0)
    for k in range(6):
        cartridge(A, 3 + k * 3, 15 + (k - 2.5) ** 2 * 0.35, -90, 0.42, tip=ELEMS[k % 4], seed=k, length=14, w=2.6)
    B = G("040c0c", "0e2224", (12, 12))
    turret(B, -2, 5, 1.0)
    for k, rm in enumerate(ELEMS):
        B.streak(17, 10, 24, 3 + k * 4.5, 1.0, rm)
    C = G("061214", "10282c", (12, 12))
    for k in range(7):
        a = math.radians(200 + k * 20)
        cartridge(C, 12 + math.cos(a) * 8, 15 + math.sin(a) * 8, 200 + k * 20 - 180 + 90, 0.42, tip=ELEMS[k % 4], seed=k, length=14, w=2.6)
    return A, B, C


# ---------------------------------------------------------------- frag orb
def frag_shrapnel():
    A = G("0e0e0a", "26261a", (10, 6))
    A.solid(union(ellipse(12, 12, 8.5, 10), box(12, 4, 4, 2.5, 0, 1)), STEEL, seed=1)
    for (pts) in (((8, 7), (11, 11), (9, 16)), ((15, 8), (13, 13)), ((14, 16), (16, 20))):
        for i in range(len(pts) - 1):
            A.solid(seg(*pts[i], *pts[i + 1], 0.4), STEEL[:2], base=0.5, rim=0, core=0)
    for (x, y) in ((8, 7), (15, 8), (14, 16)):
        A.solid(circle(x, y, 1.1), OLIVE, base=4)
    B = G("0e0e0a", "26261a", (12, 12))
    B.solid(box(16, 12, 6, 9, 0, 1), STEEL, seed=1)
    for k, y in enumerate((5, 9, 13, 17)):
        B.streak(0, y + k % 2, 9.5, y, 0.9, R("1a1004", "4a3010", "8a6020", "c09040", "f0d080"))
    for (x0, y0, x1, y1) in ((10, 5, 14, 8), (10, 13, 15, 15), (10, 17, 13, 20)):
        B.solid(seg(x0, y0, x1, y1, 0.35), STEEL[:2], base=0.3, rim=0, core=0)
    C = G("0e0e0a", "222218", (12, 12))
    for k, (dx, a) in enumerate(((-2.2, -12), (2.2, 12))):
        half = inter(union(ellipse(12, 12, 8.5, 10), box(12, 4, 4, 2.5, 0, 1)), lambda x, y, k=k: (x - 12) * (1 if k else -1) * -1 + 0.4 * math.sin(y * 1.5))
        C.solid(moved(half, dx, 0), STEEL, seed=k)
    C.energy(seg(12, 1, 12, 23, 0.6), GOLD, falloff=0.8)
    return A, B, C


# ---------------------------------------------------------------- elemental bullets
def _round_on(rm, dark, mid, glowc):
    ic = G(dark, mid, (16, 6))
    ic.glow(16, 6, 9, glowc, 0.7)
    cartridge(ic, 12, 12.5, -50, 1.45, tip=rm)
    return ic


def scavenger_fire():
    A = _round_on(FIRE, "140604", "34100a", "ff6010")
    A.energy(flame(17.5, 6.5, 2.4, 6.5, 1.5, 3), FIRE, falloff=1.6)
    B = G("140604", "2e0e06", (16, 8))
    B.energy(lambda x, y: seg(2, 22, 15, 9, 0.3, 3.4)(x, y) - 0.6 * math.sin(x * 1.7 + y), FIRE, falloff=2.4)
    slug(B, 17, 7, -45, 1.1, COPPER)
    C = G("120604", "2a0e06", (12, 12))
    C.glow(12, 12, 12, "ff6010", 0.7)
    C.energy(flame(12, 23, 7, 22, 0.8, 4), FIRE, falloff=4)
    slug(C, 12, 13, -90, 1.4, R("1a0604", "3a0e06", "5a1e0e", "7a2e16"))
    return A, B, C


def scavenger_ice():
    A = _round_on(ICE, "06101e", "102a4a", "3a8ad0")
    for k in range(6):
        a = math.radians(k * 60 - 50)
        A.energy(seg(17.5, 6, 17.5 + math.cos(a) * 3.4, 6 + math.sin(a) * 3.4, 0.35), ICE, falloff=0.5)
    B = G("06101e", "123258", (16, 8))
    slug(B, 8, 16, -45, 1.0, ICE)
    for k in range(6):
        a = math.radians(-45 + (k - 2.5) * 22)
        B.solid(seg(13 + math.cos(a) * 1.5, 11 + math.sin(a) * 1.5, 13 + math.cos(a) * 9, 11 + math.sin(a) * 9, 1.1, 0.2), ICE, seed=k, base=3.6)
    C = G("06101e", "102a4a", (12, 12))
    C.glow(12, 12, 11, "7ac4f4", 0.6)
    for k in range(6):
        a = math.radians(k * 60 + 90)
        C.energy(seg(12, 12, 12 + math.cos(a) * 9.5, 12 + math.sin(a) * 9.5, 0.6), ICE, falloff=0.8)
        for d in (4.5, 7):
            for sgn in (-1, 1):
                b = a + sgn * 0.8
                C.energy(seg(12 + math.cos(a) * d, 12 + math.sin(a) * d, 12 + math.cos(a) * d + math.cos(b) * 2.4, 12 + math.sin(a) * d + math.sin(b) * 2.4, 0.4), ICE, falloff=0.5)
    return A, B, C


def scavenger_poison():
    A = _round_on(TOXIC, "06100a", "142a14", "3e8e1c")
    for (x, y, r) in ((15, 11, 1.2), (14, 14.5, 1.0), (15, 18, 0.8)):
        A.energy(lambda X, Y, x=x, y=y, r=r: math.hypot(X - x, Y - y) - r + max(0, y - Y) * 0.6, TOXIC, falloff=1)
    B = G("06100a", "142a14", (14, 10))
    slug(B, 5, 19, -45, 0.9, TOXIC)
    for k, (x, y, r) in enumerate(((14, 10, 4.6), (19, 6, 2.6), (19, 14, 2.4), (11, 4, 2), (21, 20, 1.4), (8, 12, 1.4))):
        B.solid(circle(x, y, r), TOXIC, base=3.4, spread=1.4, seed=k)
    C = G("06100a", "122812", (12, 12))
    C.glow(12, 13, 11, "7cc434", 0.7)
    C.solid(lambda x, y: math.hypot(x - 12, y - 15) - 7 + max(0, 15 - y) * 0.62, TOXIC, seed=2)
    C.px([(9, 13), (9, 14), (10, 12)], TOXIC[6])
    return A, B, C


def scavenger_stun():
    A = _round_on(VOLT, "141004", "2e2608", "e0c028")
    for k in range(4):
        a = math.radians(k * 90 + 45)
        A.energy(poly([(17.5 + math.cos(a) * 4, 6 + math.sin(a) * 4), (17.5 + math.cos(a + 0.4) * 1.2, 6 + math.sin(a + 0.4) * 1.2), (17.5 + math.cos(a - 0.4) * 1.2, 6 + math.sin(a - 0.4) * 1.2)]), VOLT, falloff=1)
    B = G("100c02", "2a2206", (12, 8))
    head(B, 12, 14, 0.95, GUN)
    for k in range(5):
        a = math.radians(k * 72 - 90)
        x, y = 12 + math.cos(a) * 7, 6 + math.sin(a) * 2.6
        B.energy(poly([(x, y - 1.8), (x + 0.6, y - 0.6), (x + 1.8, y), (x + 0.6, y + 0.6), (x, y + 1.8), (x - 0.6, y + 0.6), (x - 1.8, y), (x - 0.6, y - 0.6)]), VOLT, falloff=1)
    C = G("100c02", "26200a", (12, 12))
    C.glow(12, 12, 12, "e0c028", 0.6)
    C.energy(lambda x, y: math.hypot(x - 12, y - 12) - 10 * (0.45 + 0.55 * abs(math.cos(math.atan2(y - 12, x - 12) * 2.5 + 1.57))), VOLT, falloff=3.5)
    return A, B, C


FA3 = {
    "reload": reload, "snipe": snipe, "critical_aim": critical_aim, "focus_hud": focus_hud, "rocket": rocket_,
    "scavenger": scavenger, "dodge_skip": dodge_skip, "explosive_reload": explosive_reload, "headshot": headshot,
    "piercing": piercing, "fat_boy": fat_boy, "quad_missile": quad_missile, "rifle_attack": rifle_attack,
    "glock_attack": glock_attack, "glock_dual": glock_dual, "gl_attack": gl_attack, "steady": steady,
    "steady_crit": steady_crit, "clip_hud": clip_hud, "reloading_hud": reloading_hud,
    "grenade_charges_hud": grenade_charges_hud, "rocket_charges_hud": rocket_charges_hud, "gl_charges_hud": gl_charges_hud,
    "burst": burst, "burst_breath": burst_breath, "burst_triple": burst_triple, "adrenaline": adrenaline,
    "adrenaline_crit": adrenaline_crit, "adrenaline_epipen": adrenaline_epipen, "adrenaline_hud": adrenaline_hud,
    "turret": turret_, "my_turret": my_turret, "turret_reinforced": turret_reinforced, "turret_second": turret_second,
    "myturret_feed": myturret_feed, "frag_shrapnel": frag_shrapnel, "scavenger_fire": scavenger_fire,
    "scavenger_ice": scavenger_ice, "scavenger_poison": scavenger_poison, "scavenger_stun": scavenger_stun,
}


# ---------------------------------------------------------------- second pass
_crit, _scav, _dual, _fat, _breath, _epi, _gla = critical_aim, scavenger, glock_dual, fat_boy, burst_breath, adrenaline_epipen, gl_attack


def critical_aim():
    A, B, C = _crit()
    A = G("100c04", "2a2008", (12, 12))
    A.solid(circle(12, 12, 10.5), GUN, seed=1)
    A.paint(circle(12, 12, 8), lambda x, y, d: mix(hexc("06080e"), hexc("1a2438"), max(0, min(1, (24 - x - y) / 24))))
    A.energy(union(box(12, 12, 6.5, 0.3), box(12, 12, 0.3, 6.5)), GOLD, falloff=0.5)
    A.energy(ring(12, 12, 3.2, 0.35), GOLD, falloff=0.5)
    A.energy(circle(12, 12, 0.8), BLOOD, falloff=0.8)
    A.px([(8, 7), (7, 8), (9, 6)], hexc("7a8aa8"))
    return A, B, C


def scavenger():
    A, B, C = _scav()
    C = G("0a0a0e", "1a1a22", (12, 12))
    for (x, y), rm in zip(((5, 5), (19, 5), (5, 19), (19, 19)), ELEMS):
        C.glow(x, y, 9, rm[4], 0.7)
    cartridge(C, 12, 12, -55, 1.5, tip=R("1a1a20", "4a3a5a", "8a6aa0", "c0a0e0", "f0e0ff"))
    return A, B, C


def glock_dual():
    A, B, C = _dual()
    A = G("0a0c14", "1e2434", (12, 6))
    pistol(A, 8.5, 13, -65, 1.05, flip=True)
    pistol(A, 15.5, 13, -115, 1.05)
    return A, B, C


def fat_boy():
    A, B, C = _fat()
    B = G("141206", "2e2a0c", (12, 10))
    B.glow(12, 8, 11, "7cc434", 0.8)
    B.solid(box(12, 16, 2.2, 6, 0, 1), GAS, base=2.6, spread=1)
    B.solid(ellipse(12, 15, 5, 1.6), TOXIC, base=3, seed=7)
    B.solid(union(ellipse(12, 8, 10, 4.6), ellipse(12, 5.5, 6.5, 3.5)), TOXIC, base=3.4, spread=1.4, seed=1)
    B.solid(ellipse(12, 10.8, 8.6, 1.4), GAS, base=1.4, seed=3)
    for k, (x, r) in enumerate(((4, 3.2), (12, 4.4), (20, 3.2))):
        B.solid(ellipse(x, 22.5, r * 1.6, 2.2), GAS, base=2, seed=k + 5)
    return A, B, C


def burst_breath():
    A, B, C = _breath()
    C = G("120604", "2a0e06", (8, 12))
    C.glow(6, 12, 10, "ff6010", 0.8)
    for k in range(16):
        a = math.radians(-34 + h2(k, 3) * 68)
        r = 6 + h2(k, 4) * 16
        x, y = 3 + math.cos(a) * r, 12 + math.sin(a) * r
        C.energy(flame(x, y + 1.2, 1.0 + r * 0.05, 2.4 + r * 0.08, 0, k), FIRE, falloff=1.2)
    flash(C, 3, 12, 3.2)
    return A, B, C


def adrenaline_epipen():
    A, B, C = _epi()
    C = G("100e04", "262208", (14, 12))
    for y, x0 in ((8, 0), (12, -1), (16, 1)):
        C.streak(x0, y, x0 + 8, y, 0.8, VOLT)
    C.glow(14, 12, 10, "e0c028", 0.6)
    C.energy(heart(14.5, 12.5, 7), VOLT, falloff=2.4)
    return A, B, C


def gl_attack():
    A, B, C = _gla()
    C = G("100c06", "2a1208", (12, 12))
    C.rays(15, 9, EMBER, n=7, lo=0, hi=3)
    blast(C, 15, 9, 6, FIRE, 7, hole=1.6)
    for k in range(5):
        t = k / 4
        C.solid(circle(2 + t * 8, 22 - t * 8, 1.1 + t * 0.6), SMOKE, base=2.4, seed=k)
    return A, B, C


FA3.update({"critical_aim": critical_aim, "scavenger": scavenger, "glock_dual": glock_dual, "fat_boy": fat_boy,
            "burst_breath": burst_breath, "adrenaline_epipen": adrenaline_epipen, "gl_attack": gl_attack})


def _glock_dual3():
    A, B, C = glock_dual()
    A = G("0a0c14", "1e2434", (12, 6))
    pistol(A, 10, 8.5, 0, 1.0)
    pistol(A, 13, 15.5, 0, 1.0)
    return A, B, C


def _scavenger3():
    A, B, C = scavenger()
    C = G("0a0a0e", "1a1a22", (12, 12))
    for k, rm in enumerate(ELEMS):
        a = math.radians(k * 90 - 45)
        x, y = 12 + math.cos(a) * 6.5, 12 + math.sin(a) * 6.5
        C.glow(x, y, 6, rm[4], 0.6)
        C.energy(circle(x, y, 3), rm, falloff=2.2)
    return A, B, C


FA3.update({"glock_dual": _glock_dual3, "scavenger": _scavenger3})
