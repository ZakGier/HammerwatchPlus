"""Wizard orb icons: A the gear up close, B the moment it happens, C an abstract mark."""
from vm import *

BG_A = ("0e0818", "241434")
BG_F = ("140604", "2e1006")
BG_I = ("06101e", "0e2440")


def ga(c=BG_A, light=(12, 12)):
    return G(c[0], c[1], light)


def missile(ic, x, y, ang, s=1.0, rmp=ARCANE):
    r = math.radians(ang)
    ic.streak(x - math.cos(r) * 6 * s, y - math.sin(r) * 6 * s, x, y, 0.9 * s, rmp)
    ic.energy(circle(x, y, 1.8 * s), rmp, falloff=1.6 * s)


def foe(ic, x, y, s=1.0):
    ic.solid(ellipse(x, y, 2.6 * s, 3.6 * s), SHADOW, base=2.2)


def missile_barrage():
    A = ga()
    for k, (x, y) in enumerate(((7, 6), (17, 7), (6, 17), (18, 17), (12, 12))):
        missile(A, x, y, -45 + k * 8, 1.1)
    B = ga()
    staff(B, 5, 18, -45, 0.6)
    for a in (-80, -50, -20, 10):
        r = math.radians(a)
        missile(B, 10 + math.cos(r) * 10, 13 + math.sin(r) * 10, a, 0.9)
    C = ga()
    for k in range(3):
        C.energy(poly([(4 + k * 5, 5), (11 + k * 5, 12), (4 + k * 5, 19), (7 + k * 5, 12)]), ARCANE, falloff=1)
    return A, B, C


def rebounding_missiles():
    A = ga()
    missile(A, 12, 12, -20, 1.4)
    A.energy(arc(12, 12, 8.5, 1.1, 100, 330), ARCANE, falloff=0.6)
    B = ga()
    for x, y in ((5, 17), (12, 7), (19, 16)):
        foe(B, x, y + 1)
    for (x0, y0), (x1, y1) in (((1, 22), (5, 15)), ((5, 15), (12, 5)), ((12, 5), (19, 14))):
        B.streak(x0, y0, x1, y1, 0.8, ARCANE)
    B.energy(circle(19, 14, 1.8), ARCANE, falloff=1.4)
    C = ga()
    C.energy(union(seg(3, 19, 8, 6, 1.0), seg(8, 6, 13, 19, 1.0), seg(13, 19, 18, 6, 1.0)), ARCANE, falloff=0.8)
    C.energy(poly([(16, 4), (22, 3), (19, 9)]), ARCANE, falloff=0.8)
    return A, B, C


def concussive_impacts():
    A = ga()
    missile(A, 14, 10, -30, 1.4)
    for k in range(3):
        a = math.radians(k * 120 + 30)
        A.energy(star(14 + math.cos(a) * 6, 10 + math.sin(a) * 6, 0.6, 1.8, 4), HOLY, falloff=0.8)
    B = ga()
    foe(B, 14, 15, 1.4)
    flash(B, 10, 12, 3, ARCANE)
    for x in (10, 14, 18):
        B.energy(star(x, 5 + (x == 14) * -1, 0.6, 2.0, 4), HOLY, falloff=0.8)
    C = ga()
    C.energy(ring(12, 12, 8, 1.4), ARCANE, falloff=0.8)
    C.energy(star(12, 12, 1.6, 5, 4), HOLY, falloff=1.2)
    return A, B, C


def enhanced_fireball():
    A = ga(BG_F)
    fireball(A, 13, 11, 6.5, ang=-35)
    B = ga(BG_F)
    B.energy(circle(12, 12, 10), EMBER, falloff=4)
    flash(B, 12, 12, 6, FIRE)
    C = ga(BG_F)
    C.energy(circle(12, 12, 3), FIRE, falloff=2.4)
    for a in (45, 135, 225, 315):
        r = math.radians(a)
        C.energy(poly([(12 + math.cos(r) * 6, 12 + math.sin(r) * 6), (12 + math.cos(r - 0.4) * 10.5, 12 + math.sin(r - 0.4) * 10.5), (12 + math.cos(r + 0.4) * 10.5, 12 + math.sin(r + 0.4) * 10.5)]), FIRE, falloff=0.9)
    return A, B, C


def blastwave():
    A = ga(BG_F)
    fireball(A, 8, 12, 4.5, ang=0)
    for r in (11, 15, 19):
        A.energy(arc(4, 12, r, 0.8, -40, 40), FIRE, falloff=0.6)
    B = ga(BG_F)
    foe(B, 14, 13, 1.5)
    B.energy(cut(shard(14, 13, -60, 10, 1.4), circle(0, 0, 0)), CRIMSON, falloff=1)
    flash(B, 6, 14, 3, FIRE)
    C = ga(BG_F)
    C.energy(cut(circle(12, 12, 9), circle(12, 12, 7)), FIRE, falloff=0.8)
    C.energy(poly([(12, 4), (15, 16), (12, 14), (9, 16)]), CRIMSON, falloff=1)
    return A, B, C


def bouncing_fireball():
    A = ga(BG_F)
    for k, (x, y, r) in enumerate(((5, 19, 2), (12, 15, 2.6), (19, 8, 4.2))):
        fireball(A, x, y, r, ang=-30, tail=1.2)
    B = ga(BG_F)
    pts = [(1, 6), (7, 19), (13, 9), (19, 19), (23, 12)]
    for i in range(4):
        B.streak(*pts[i], *pts[i + 1], 0.6, EMBER)
    for x, y in pts[1:4:2]:
        flash(B, x, y, 2.6, FIRE)
    C = ga(BG_F)
    C.energy(union(arc(7, 18, 5, 1.1, 180, 360), arc(17, 18, 5, 1.1, 180, 360)), FIRE, falloff=0.8)
    C.energy(circle(21.5, 10, 2), FIRE, falloff=1.6)
    return A, B, C


def savant():
    A = ga(light=(8, 6))
    book(A, 12, 13, 1.1, cover=ARCANE)
    hourglass(A, 18, 6, 0.45, sand=ARCANE)
    B = ga()
    hourglass(B, 12, 12, 1.0, sand=ARCANE, t=0.8)
    B.energy(arc(12, 12, 10, 1.0, 200, 340), ARCANE, falloff=0.6)
    C = ga()
    C.energy(ring(12, 12, 8.5, 1.3), ARCANE, falloff=0.8)
    C.energy(union(seg(12, 12, 12, 6, 0.9), seg(12, 12, 7, 15, 0.9)), ARCANE, falloff=0.8)
    C.energy(poly([(18, 3), (23, 6), (19, 8)]), ARCANE, falloff=0.8)
    return A, B, C


def arcane_weaponry():
    A = ga()
    sword(A, 12, 12, -45, 1.0, blade=ARCANE)
    B = ga()
    staff(B, 10, 14, -55, 1.0)
    B.energy(arc(12, 12, 10, 1.6, 230, 330), ARCANE, falloff=0.8)
    C = ga()
    C.energy(poly([(12, 2), (15, 12), (12, 22), (9, 12)]), ARCANE, falloff=1.2)
    C.energy(box(12, 15, 6, 1, 0, 0.4), ARCANE, falloff=0.8)
    return A, B, C


def learning():
    A = ga(light=(8, 6))
    book(A, 12, 13, 1.15, cover=ARCANE, open_=True)
    A.energy(star(12, 5, 1, 3, 4), HOLY, falloff=1)
    B = ga()
    B.rays(12, 18, HOLY, n=7, lo=1, hi=3.4)
    book(B, 12, 17, 0.8, cover=ARCANE, open_=True)
    C = ga()
    for k in range(3):
        C.energy(poly([(5, 18 - k * 6), (12, 12 - k * 6), (19, 18 - k * 6), (19, 21 - k * 6), (12, 15 - k * 6), (5, 21 - k * 6)]), HOLY if k == 2 else ARCANE, falloff=0.9)
    return A, B, C


def bubble(ic, cx=12, cy=12, r=9, rmp=SPIRIT):
    ic.energy(cut(circle(cx, cy, r), circle(cx, cy, r - 1.6)), rmp, falloff=1)
    ic.glow(cx, cy, r, rmp[3], 0.3)


def flame_shield():
    A = ga(BG_F)
    bubble(A, rmp=SPIRIT)
    for a in (200, 250, 300, 340):
        r = math.radians(a)
        A.energy(flame(12 + math.cos(r) * 9, 12 + math.sin(r) * 9 + 2, 2, 6, 0, a), FIRE, falloff=1.2)
    B = ga(BG_F)
    B.solid(ellipse(12, 13, 3.6, 6.5), SHADOW, base=2.4)
    for x in (4, 8, 16, 20):
        B.energy(flame(x, 22, 2.4, 11 - abs(x - 12) * 0.4, 0, x), FIRE, falloff=1.4)
    bubble(B, rmp=SPIRIT)
    C = ga(BG_F)
    C.energy(cut(circle(12, 12, 9), circle(12, 12, 7.4)), FIRE, falloff=0.8)
    C.energy(flame(12, 18, 3.4, 11, 0, 2), FIRE, falloff=1.4)
    return A, B, C


def frost_shell():
    A = ga(BG_I)
    shield(A, 12, 11, 1.1, ICE, face=None, boss=None)
    A.glint(8, 6)
    B = ga(BG_I)
    B.solid(ellipse(12, 13, 3.6, 6.5), SHADOW, base=2.4)
    for k in range(6):
        a = k * 60 + 30
        r = math.radians(a)
        B.solid(shard(12 + math.cos(r) * 8.5, 12 + math.sin(r) * 8.5, a, 5, 1.6), ICE, base=4.4, seed=k)
    C = ga(BG_I)
    C.energy(cut(poly([(12, 2), (21, 7), (21, 17), (12, 22), (3, 17), (3, 7)]), poly([(12, 5), (18, 8.5), (18, 15.5), (12, 19), (6, 15.5), (6, 8.5)])), ICE, falloff=1)
    snowflake(C, 12, 12, 4.4, w=0.5)
    return A, B, C


def protective_warding():
    A = ga()
    staff(A, 9, 15, -60, 0.9)
    bubble(A, 15, 9, 6, rmp=SPIRIT)
    B = ga()
    bubble(B, rmp=SPIRIT)
    B.rays(12, 12, ARCANE, n=6, lo=0.6, hi=2)
    flash(B, 12, 12, 3, ARCANE)
    C = ga()
    for r in (4, 7, 10):
        C.energy(arc(12, 14, r, 1.1, 200, 340), SPIRIT, falloff=0.6)
    C.energy(star(12, 15, 1, 3, 4), ARCANE, falloff=1)
    return A, B, C


def burning_ground():
    A = ga(BG_F, (12, 8))
    fireball(A, 15, 7, 4.4, ang=120)
    A.energy(ellipse(9, 19, 8, 2.6), EMBER, falloff=1.2)
    for x in (4, 9, 14):
        A.energy(flame(x, 20, 1.8, 6, 0, x), FIRE, falloff=1.1)
    B = ga(BG_F, (12, 16))
    B.energy(ellipse(12, 17, 11, 4), EMBER, falloff=2)
    for k, x in enumerate((3, 7, 11, 15, 19)):
        B.energy(flame(x, 19 + (k % 2), 2.2, 9 + (k % 3) * 2, 0, k), FIRE, falloff=1.3)
    C = ga(BG_F)
    C.energy(box(12, 19, 9, 1.4, 0, 0.6), FIRE, falloff=0.8)
    for x in (6, 12, 18):
        C.energy(flame(x, 17, 2.4, 9, 0, x), FIRE, falloff=1.2)
    return A, B, C


def comet():
    A = ga(BG_I)
    A.energy(seg(2, 2, 13, 13, 0.8, 3.4), ICE[:6], falloff=2)
    A.solid(circle(15, 15, 5), SMOKE, base=2.6, seed=3)
    A.solid(circle(15, 15, 3.4), ICE, base=4.2, seed=4)
    B = ga(BG_I, (12, 16))
    B.solid(ellipse(12, 19, 9, 2.8), SMOKE, base=1.4)
    for k in range(5):
        a = k * 36 + 198
        r = math.radians(a)
        B.solid(shard(12 + math.cos(r) * 7, 18 + math.sin(r) * 7, a, 6, 1.8), ICE, base=4.4, seed=k)
    flash(B, 12, 17, 3, ICE)
    C = ga(BG_I)
    C.energy(union(seg(4, 4, 14, 14, 0.4, 1.6), seg(9, 2, 16, 9, 0.3, 1.0), seg(2, 9, 9, 16, 0.3, 1.0)), ICE, falloff=0.8)
    C.energy(circle(16, 16, 4), ICE, falloff=3)
    return A, B, C


def rising_crescendo():
    A = ga()
    for k in range(4):
        A.solid(box(5 + k * 4.6, 20 - k * 2.6, 1.6, 1.4 + k * 2.6, 0, 0.5), ARCANE, base=3.6, seed=k)
    A.energy(star(19, 4, 1, 3, 4), CRIMSON, falloff=1)
    B = ga()
    crosshair(B, 12, 12, 6.5, ARCANE)
    B.energy(star(12, 12, 1.2, 4, 4), HOLY, falloff=1)
    C = ga()
    for k in range(3):
        C.energy(poly([(4 + k * 4, 21 - k * 6), (12, 13 - k * 5), (20 - k * 4, 21 - k * 6)]), ARCANE, falloff=0.9)
    C.energy(star(12, 4, 1, 3, 4), HOLY, falloff=1)
    return A, B, C


def incanters_flow():
    A = ga()
    sword(A, 12, 12, -45, 0.95, blade=ARCANE)
    for k in range(3):
        A.energy(arc(12, 12, 9 + k * 1.6, 0.5, 150 + k * 20, 220 + k * 20), ARCANE, falloff=0.4)
    B = ga()
    for k, a in enumerate((210, 260, 310)):
        B.energy(arc(12, 14, 9, 1.4 - k * 0.3, a, a + 45), ARCANE[:6 - k], falloff=0.7)
    B.energy(star(18, 6, 1, 3, 4), ARCANE, falloff=1)
    C = ga()
    C.energy(union(seg(4, 17, 9, 7, 1.0), seg(9, 7, 14, 17, 1.0), seg(14, 17, 19, 7, 1.0)), ARCANE, falloff=0.8)
    for x in (4, 14):
        C.energy(circle(x, 19, 1.4), ARCANE, falloff=1)
    return A, B, C


def hydra_head(ic, x, y, ang, s=1.0, rmp=TEAL, breath=FIRE):
    r = math.radians(ang)
    hx, hy = x + math.cos(r) * 7 * s, y + math.sin(r) * 7 * s
    ic.solid(seg(x, y, hx, hy, 1.6 * s, 1.2 * s), rmp, base=2.8, seed=int(x))
    ic.solid(ellipse(hx, hy, 2.6 * s, 1.7 * s, ang), rmp, base=3.4, seed=int(y))
    if breath:
        ic.streak(hx + math.cos(r) * 2.4 * s, hy + math.sin(r) * 2.4 * s, hx + math.cos(r) * 7 * s, hy + math.sin(r) * 7 * s, 1.0 * s, breath)


def greater_hydra():
    A = ga(BG_F, (12, 16))
    for a, x in ((-120, 9), (-90, 12), (-60, 15)):
        hydra_head(A, x, 22, a, 1.15, breath=None)
    B = ga(BG_F, (12, 16))
    for a, x in ((-150, 8), (-110, 11), (-70, 13), (-30, 16)):
        hydra_head(B, x, 21, a, 0.85)
    C = ga(BG_F)
    for k, a in enumerate((-130, -90, -50)):
        r = math.radians(a)
        C.energy(seg(12, 20, 12 + math.cos(r) * 13, 20 + math.sin(r) * 13, 1.5, 0.6), FIRE, falloff=0.8)
    C.energy(circle(12, 20, 2.4), FIRE, falloff=2)
    return A, B, C


def frost_breath():
    A = ga(BG_I, (12, 16))
    hydra_head(A, 6, 20, -45, 1.1, rmp=ICE, breath=None)
    for k in range(4):
        A.energy(shard(15 + k * 2, 9 - k * 1.5, -45, 3, 1), ICE, falloff=0.8)
    B = ga(BG_I)
    hydra_head(B, 3, 19, -30, 0.9, rmp=TEAL, breath=ICE)
    foe(B, 19, 9, 1.2)
    B.energy(snowflake and circle(19, 9, 0), ICE, falloff=0.5)
    snowflake(B, 19, 9, 3.4, w=0.4)
    C = ga(BG_I)
    C.energy(poly([(3, 10), (12, 8), (21, 3), (21, 21), (12, 16), (3, 14)]), ICE, falloff=1.4)
    return A, B, C


def flame_blade():
    A = ga(BG_F)
    sword(A, 12, 12, -45, 1.05, blade=FIRE)
    B = ga(BG_F)
    sword(B, 12, 13, -90, 0.9, blade=STEEL)
    for a in (180, 230, 310, 0):
        r = math.radians(a)
        B.energy(flame(12 + math.cos(r) * 8, 16 + math.sin(r) * 5, 2, 7, 0, a), FIRE, falloff=1.2)
    C = ga(BG_F)
    C.energy(poly([(12, 1), (15, 15), (12, 19), (9, 15)]), FIRE, falloff=1.2)
    C.energy(box(12, 17, 6, 1, 0, 0.4), FIRE, falloff=0.8)
    C.energy(ring(12, 12, 10, 0.6), FIRE[:5], falloff=0.4)
    return A, B, C


def ice_blade():
    A = ga(BG_I)
    sword(A, 12, 12, -45, 1.05, blade=ICE)
    A.glint(16, 6)
    B = ga(BG_I)
    slash(B, 12, 12, 9, 200, 320, ICE)
    B.solid(box(13, 16, 3, 4, 0, 1), ICE, base=4, seed=2)
    foe(B, 13, 16, 0.8)
    C = ga(BG_I)
    C.energy(poly([(12, 1), (15, 15), (12, 19), (9, 15)]), ICE, falloff=1.2)
    C.energy(box(12, 17, 6, 1, 0, 0.4), ICE, falloff=0.8)
    snowflake(C, 12, 9, 3, w=0.35, rmp=SPIRIT)
    return A, B, C


def blur():
    A = ga()
    for k, al in enumerate((0.35, 0.6, 1.0)):
        boot(A, 7 + k * 4.5, 12, 0.75, rmp=R("10081c", "241238", "3a1e5a", "58307e", "8458b0", "b890e0") if k == 2 else SHADOW)
    B = ga()
    for k in range(3):
        B.solid(ellipse(6 + k * 5, 13, 3.0, 6.5), SHADOW if k < 2 else ARCANE, base=1.4 + k * 0.8)
    B.streak(14, 3, 3, 20, 0.6, STEEL)
    C = ga()
    for k in range(3):
        C.energy(ellipse(8 + k * 4, 12, 2.4 - k * 0.3, 7 - k), ARCANE[:5 + k], falloff=1.4)
    return A, B, C


def temporal_shift():
    A = ga()
    hourglass(A, 12, 12, 1.05, sand=ARCANE, t=0.4)
    B = ga()
    B.energy(ring(12, 12, 9, 1.2), ARCANE, falloff=0.7)
    for x, y in ((6, 8), (17, 16)):
        foe(B, x, y, 0.9)
    B.energy(union(seg(12, 12, 12, 5, 0.8), seg(12, 12, 16, 12, 0.8)), ARCANE, falloff=0.7)
    C = ga()
    C.energy(arc(12, 12, 9, 1.4, 90, 400), ARCANE, falloff=0.8)
    C.energy(poly([(9, 21), (14, 18), (14, 24)]), ARCANE, falloff=0.8)
    C.energy(circle(12, 12, 2.2), ARCANE, falloff=2)
    return A, B, C


def enhanced_strength():
    A = ga()
    fist(A, 12, 13, 1.1)
    A.energy(star(18, 5, 1, 3, 4), ARCANE, falloff=1)
    B = ga()
    B.solid(seg(2, 15, 22, 15, 1.4), STEEL, base=2.8)
    for x in (3, 21):
        B.solid(box(x, 15, 1.6, 5.5, 0, 0.6), STEEL, base=2.4, seed=x)
    B.energy(circle(12, 7, 3.2), ARCANE, falloff=2.6)
    C = ga()
    C.energy(poly([(12, 3), (20, 8), (20, 16), (12, 21), (4, 16), (4, 8)]), CRIMSON, falloff=1.4)
    C.energy(circle(12, 12, 3), ARCANE, falloff=2.4)
    return A, B, C


def enhanced_dexterity():
    A = ga()
    hand_open(A, 12, 14, 1.1)
    for k in range(3):
        a = math.radians(-130 + k * 40)
        A.energy(circle(12 + math.cos(a) * 9, 13 + math.sin(a) * 9, 1.3), ARCANE, falloff=1)
    B = ga()
    for k, (x, y) in enumerate(((6, 18), (12, 8), (18, 15))):
        dagger(B, x, y, -60 + k * 50, 0.6, blade=ARCANE)
    C = ga()
    C.energy(poly([(12, 3), (20, 8), (20, 16), (12, 21), (4, 16), (4, 8)]), LIFE, falloff=1.4)
    C.energy(circle(12, 12, 3), ARCANE, falloff=2.4)
    return A, B, C


def free_movement():
    A = ga()
    boot(A, 12, 11, 0.95, wing=SPIRIT)
    B = ga()
    chain(B, 2, 18, 9, 16, STEEL)
    chain(B, 15, 16, 22, 18, STEEL)
    B.solid(ellipse(12, 12, 3, 6.5), ARCANE, base=3)
    flash(B, 12, 16, 2.4, ARCANE)
    C = ga()
    C.energy(cut(ring(7, 12, 4.4, 1.3), box(10.5, 12, 1.6, 2.4)), STEEL, falloff=0.8)
    C.energy(cut(ring(17, 12, 4.4, 1.3), box(13.5, 12, 1.6, 2.4)), STEEL, falloff=0.8)
    C.energy(star(12, 12, 0.8, 2.6, 4), ARCANE, falloff=1)
    return A, B, C


ORBS = {
    "wiz_magic_missiles_projectiles": missile_barrage, "wiz_magic_missiles_jumps": rebounding_missiles,
    "wiz_magic_missiles_stun": concussive_impacts,
    "fireball_size": enhanced_fireball, "fireball_blastwave": blastwave, "fireball_bounces": bouncing_fireball,
    "wiz_arcane_intellect_scholar": savant, "wiz_arcane_intellect_attacks": arcane_weaponry, "wiz_arcane_intellect_learning": learning,
    "wiz_barrier_fire": flame_shield, "wiz_barrier_ice": frost_shell, "wiz_barrier_generate": protective_warding,
    "wiz_meteor_ground": burning_ground, "wiz_meteor_comet": comet,
    "wiz_incanters_crit": rising_crescendo, "wiz_incanters_attacks": incanters_flow,
    "conjuration_hydras_add": greater_hydra, "conjuration_hydras_ice": frost_breath,
    "conjuration_sword_fire": flame_blade, "conjuration_sword_ice": ice_blade,
    "transmutation_haste_blur": blur, "wiz_haste_slow_aura": temporal_shift,
    "transmutation_body_str": enhanced_strength, "transmutation_body_dex": enhanced_dexterity,
    "transmutation_body_slow": free_movement,
}


# second pass
SCALE = R("06140e", "0e2c22", "1a4a3a", "2a7258", "4aa07a", "90d8a8")


def serpent(ic, bx, by, hx, hy, s=1.0, rmp=SCALE, breath=None, seed=0):
    """A hydra neck rising from (bx, by) to a head at (hx, hy) facing right, jaws open."""
    mx, my = (bx + hx) / 2 - 3 * s, (by + hy) / 2
    ic.solid(union(seg(bx, by, mx, my, 2.2 * s, 1.8 * s), seg(mx, my, hx - 1.5 * s, hy, 1.8 * s, 1.6 * s)), rmp, base=2.4, seed=seed)
    head = cut(ellipse(hx + 1.2 * s, hy, 3.6 * s, 2.4 * s), poly([(hx + 1.5 * s, hy + 0.3 * s), (hx + 6 * s, hy - 1 * s), (hx + 6 * s, hy + 2.6 * s)]))
    ic.solid(head, rmp, base=3.4, seed=seed + 1)
    ic.px([(int(hx + 0.5 * s), int(hy - 1.2 * s))], (255, 230, 90, 255))
    if breath:
        ic.streak(hx + 4 * s, hy + 0.8 * s, hx + 4 * s + 8 * s, hy + 0.8 * s - 3 * s, 1.2 * s, breath)


def greater_hydra():
    A, B, C = _gh()
    A = ga(BG_F, (12, 16))
    for k, (bx, hx, hy) in enumerate(((6, 4, 7), (11, 11, 4), (16, 16, 9))):
        serpent(A, bx, 23, hx, hy, 0.9, seed=k)
    B = ga(BG_F, (12, 16))
    for k, (bx, hx, hy) in enumerate(((5, 3, 12), (9, 8, 5), (14, 13, 10))):
        serpent(B, bx, 23, hx, hy, 0.7, breath=FIRE, seed=k)
    return A, B, C


def frost_breath():
    A, B, C = _fb()
    A = ga(BG_I, (12, 16))
    serpent(A, 6, 23, 7, 9, 1.2, rmp=R("061420", "0e2a40", "1e4a6a", "3a7aa0", "70b0d8", "c0e8ff"), breath=ICE)
    B = ga(BG_I)
    serpent(B, 4, 23, 4, 12, 0.85, breath=ICE)
    foe(B, 19, 8, 1.1)
    snowflake(B, 19, 8, 3.6, w=0.45)
    return A, B, C


def incanters_flow():
    A, B, C = _if()
    B = ga()
    for k in range(3):
        dagger(B, 6 + k * 6, 16 - k * 3, -60, 0.55 + k * 0.12, blade=ARCANE)
    B.energy(arc(12, 14, 10, 1.0, 200, 300), ARCANE, falloff=0.6)
    return A, B, C


def ice_blade():
    A, B, C = _ib()
    B = ga(BG_I)
    B.solid(box(14, 15, 5, 6, 0, 1.2), ICE, base=4, seed=2)
    foe(B, 14, 15, 1.0)
    sword(B, 8, 9, -45, 0.65, blade=ICE)
    return A, B, C


def blur():
    A, B, C = _bl()
    A = ga()
    for k in range(3):
        A.solid(ellipse(7 + k * 5, 12, 3.2, 7), SHADOW, base=1.0 + k * 0.9, seed=k)
    A.solid(ellipse(17, 12, 3.2, 7), ARCANE, base=3.2)
    A.glint(16, 7)
    return A, B, C


def enhanced_dexterity():
    A, B, C = _ed()
    B = ga()
    for k in range(3):
        a = math.radians(-90 + k * 120)
        dagger(B, 12 + math.cos(a) * 5, 12 + math.sin(a) * 5, k * 120 - 90, 0.65, blade=ARCANE)
    B.energy(ring(12, 12, 10, 0.7), ARCANE, falloff=0.5)
    return A, B, C


def learning():
    A, B, C = _le()
    B = ga()
    book(B, 12, 15, 1.0, cover=ARCANE, open_=True)
    for x, y in ((7, 5), (12, 3), (17, 5)):
        B.energy(star(x, y, 0.7, 2.2, 4), HOLY, falloff=0.9)
    return A, B, C


_gh, _fb, _if, _ib, _bl, _ed, _le = (ORBS[k] for k in ("conjuration_hydras_add", "conjuration_hydras_ice", "wiz_incanters_attacks",
                                                      "conjuration_sword_ice", "transmutation_haste_blur", "transmutation_body_dex",
                                                      "wiz_arcane_intellect_learning"))
ORBS.update({"conjuration_hydras_add": greater_hydra, "conjuration_hydras_ice": frost_breath, "wiz_incanters_attacks": incanters_flow,
             "conjuration_sword_ice": ice_blade, "transmutation_haste_blur": blur, "transmutation_body_dex": enhanced_dexterity,
             "wiz_arcane_intellect_learning": learning})
