"""Vanilla-style 24x24 skill icon painter.

What the vanilla HoH2 icons do, and this copies: no outlines; forms come from a 4-6 step
ramp lit from the upper left, a hard bright rim on the lit edge and a dark core shadow on
the far edge; subjects are big and often cropped by the frame; energy (fire, magic,
speed) is a glowing shape with a white-hot core falling off through the saturated hue to
dark; grounds are near-black, tinted, with soft diagonal bands and clustered grain.

Everything is evaluated per pixel from signed distance functions, so edges stay crisp."""
import math
from PIL import Image

N = 24


# ---------------------------------------------------------------- colour
def hexc(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def R(*cs):
    return [hexc(c) for c in cs]


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def pick(rmp, t):
    """t in ramp-index units (float); clamps."""
    i = int(math.floor(t + 0.5))
    return rmp[max(0, min(len(rmp) - 1, i))]


# ramps run dark -> light, hue shifting warm/cool toward the top like vanilla
STEEL = R("16181f", "2b303b", "485060", "6e788a", "a2acbc", "dfe6ef")
GUN = R("121318", "22252d", "363b46", "535a68", "7e8696", "b8c0cc")
BRASS = R("2a1806", "5a3810", "8e5e1a", "c48e2c", "e8c060", "fff0b0")
GOLD = R("2a1a04", "6a4208", "b07a10", "e8b82a", "ffe070", "fffbe0")
COPPER = R("2a1008", "5a2410", "8e4018", "c46a2c", "eca060", "ffe0b0")
FIRE = R("1e0604", "5a1006", "a82a08", "e86010", "ffa830", "ffe890", "ffffff")
EMBER = R("1a0604", "4a0e06", "8a1e08", "c84010", "f07a20", "ffc060")
ICE = R("06101e", "0e2a4a", "1e5288", "3a8ad0", "7ac4f4", "c8f0ff", "ffffff")
VOLT = R("1e1604", "4a3a06", "8a7010", "d0b020", "ffe848", "fffcc0", "ffffff")
TOXIC = R("061404", "0e3008", "1e5a10", "3e8e1c", "7cc434", "c8f070", "f4ffd0")
GAS = R("08140a", "142a14", "244a1e", "3e6e2a", "62963a", "9cc458")
BLOOD = R("1a0406", "460a0e", "801418", "c02424", "f04a3a", "ff9a80")
OLIVE = R("12160a", "262e12", "3e4a1c", "5a6a28", "84963a", "b8c464")
WOOD = R("1a0e06", "3a200c", "5e3614", "86521e", "b07a34", "d8a860")
ARCANE = R("10061e", "260e48", "44207a", "6a3ab0", "9a6ae0", "d0b0ff", "ffffff")
TEAL = R("041414", "0a2a2c", "14484a", "247274", "40a8a4", "8ae0d4", "e0fff8")
SKIN = R("2a140c", "5a2e1a", "8e5034", "c07a52", "e0a47a", "f6d0a8")
BONE = R("1e1a14", "4a4234", "7a6e58", "aea086", "d8ccb0", "f8f0dc")
SMOKE = R("0e0e12", "22222a", "3a3a44", "5a5a66", "86868f", "bcbcc4")
PAPER = R("2a2620", "5a5444", "8e8670", "c0b89e", "e8e0c8", "fffaf0")
RED = R("1a0606", "4a0c0c", "8a1a16", "c8301e", "f05a32", "ffb070")
WHITE = (255, 255, 255)
BLACK = (8, 8, 10)

TEAMC = [hexc("e84a3a"), hexc("3a8ae8"), hexc("4ac04a"), hexc("e8c83a")]


# ---------------------------------------------------------------- noise
def h2(x, y, s=0):
    n = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def grain(x, y, s=0):
    """Clustered grain: mostly 2x2 blobs with a little per-pixel noise, centred on 0."""
    return (h2(x // 2, y // 2, s) * 0.7 + h2(x, y, s + 7) * 0.3) - 0.5


# ---------------------------------------------------------------- SDFs (negative inside)
def circle(cx, cy, r):
    return lambda x, y: math.hypot(x - cx, y - cy) - r


def ellipse(cx, cy, rx, ry, ang=0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)

    def f(x, y):
        dx, dy = x - cx, y - cy
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        k = math.hypot(u / rx, v / ry)
        return (k - 1) * min(rx, ry)
    return f


def box(cx, cy, hw, hh, ang=0, rad=0.0):
    """Rotated rounded box; ang in degrees, 0 = axis aligned."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)

    def f(x, y):
        dx, dy = x - cx, y - cy
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        qx, qy = abs(u) - hw + rad, abs(v) - hh + rad
        return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - rad
    return f


def seg(x0, y0, x1, y1, r0, r1=None):
    """Tapered capsule from (x0,y0) radius r0 to (x1,y1) radius r1."""
    r1 = r0 if r1 is None else r1
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy or 1e-9

    def f(x, y):
        t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / L2))
        px, py = x0 + dx * t, y0 + dy * t
        return math.hypot(x - px, y - py) - (r0 + (r1 - r0) * t)
    return f


def poly(pts):
    n = len(pts)

    def f(x, y):
        d = 1e9
        inside = False
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            ex, ey = bx - ax, by - ay
            L2 = ex * ex + ey * ey or 1e-9
            t = max(0.0, min(1.0, ((x - ax) * ex + (y - ay) * ey) / L2))
            d = min(d, math.hypot(x - ax - ex * t, y - ay - ey * t))
            if (ay > y) != (by > y) and x < ax + (y - ay) * ex / (by - ay):
                inside = not inside
        return -d if inside else d
    return f


def flame(cx, by, w, h, lean=0.0, seed=0, tongues=2):
    """A flame standing on (cx, by): round base, flickering body, pointed tip."""
    def f(x, y):
        t = (by - y) / h
        if t < -0.15 or t > 1:
            return 1.5
        prof = w * (max(0, 1 - t) ** 0.75) * min(1, (t + 0.15) * 3.2)
        prof *= 1 + 0.18 * math.sin(t * 9 + seed * 1.7) * t
        ox = cx + lean * t * t * h * 0.25 + math.sin(t * 6 + seed) * t * 1.1
        return abs(x - ox) - prof
    return f


def ring(cx, cy, r, w):
    return lambda x, y: abs(math.hypot(x - cx, y - cy) - r) - w / 2


def union(*fs):
    return lambda x, y: min(f(x, y) for f in fs)


def cut(a, *bs):
    return lambda x, y: max(a(x, y), *(-b(x, y) for b in bs))


def inter(*fs):
    return lambda x, y: max(f(x, y) for f in fs)


def moved(f, dx, dy):
    return lambda x, y: f(x - dx, y - dy)


# ---------------------------------------------------------------- canvas
class Icon:
    def __init__(self, n=None):
        """n: the side in pixels, 24 for a skill icon (N), 14 for a buff-bar stack icon."""
        self.n = n or N
        self.im = Image.new("RGB", (self.n, self.n), BLACK)
        self.p = self.im.load()

    # ---- ground
    def ground(self, dark, mid, angle=-40, seed=1, light=(8, 6), band=0.55, hue=None):
        """Near-black tinted ground, soft diagonal bands, clustered grain, a lighter region
        toward `light` and a vignette. dark/mid are hex or rgb."""
        dark = hexc(dark) if isinstance(dark, str) else dark
        mid = hexc(mid) if isinstance(mid, str) else mid
        a = math.radians(angle)
        ux, uy = math.cos(a), math.sin(a)
        ph = [h2(seed, k, 3) * 6.28 for k in range(3)]
        for y in range(self.n):
            for x in range(self.n):
                across = -uy * (x + 0.5) + ux * (y + 0.5)
                v = 0.5 + band * (0.5 * math.sin(across * 0.42 + ph[0]) + 0.3 * math.sin(across * 0.9 + ph[1]) + 0.2 * math.sin(across * 0.21 + ph[2])) / 1.0 * 0.5
                d = math.hypot(x + 0.5 - light[0], y + 0.5 - light[1]) / (22 * self.n / N)
                v += 0.35 - d * 0.6
                e = math.hypot(x - (self.n - 1) / 2, y - (self.n - 1) / 2) / (16.5 * self.n / N)
                v -= e ** 4 * 0.6
                v += grain(x, y, seed) * 0.35
                t = max(0, min(4, round(v * 4))) / 4
                self.p[x, y] = mix(dark, mid, t)
        return self

    def rays(self, cx, cy, rmp, n=9, seed=2, lo=0, hi=2, width=0.5):
        """Radial bands behind the subject (for blasts, flashes)."""
        for y in range(self.n):
            for x in range(self.n):
                a = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
                s = math.sin(a * n + h2(seed, 1) * 6) * 0.5 + 0.5
                if s > 1 - width:
                    d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                    t = hi - d / 14 * (hi - lo) + grain(x, y, seed) * 0.8
                    if t > lo:
                        c = pick(rmp, t)
                        o = self.p[x, y]
                        if sum(c) > sum(o):
                            self.p[x, y] = c
        return self

    # ---- generic per-pixel painter
    def paint(self, sdf, fn, aa=False):
        for y in range(self.n):
            for x in range(self.n):
                d = sdf(x + 0.5, y + 0.5)
                if d <= 0:
                    c = fn(x, y, d)
                    if c is not None:
                        if len(c) == 4:
                            self.p[x, y] = mix(self.p[x, y], c[:3], c[3] / 255)
                        else:
                            self.p[x, y] = c
        return self

    def solid(self, sdf, rmp, light=(-0.7, -0.7), base=None, spread=None, rim=1.0, core=0.9,
              noise=0.5, seed=0, flat=None, spec=None):
        """A lit form: ramp index from a linear gradient along the light, a bright rim on
        lit edges, darker core shadow on the far edge, and grain. base = ramp index at the
        centre (default middle), spread = +- across the form."""
        n = len(rmp)
        base = (n - 1) * 0.5 if base is None else base
        spread = (n - 1) * 0.42 if spread is None else spread
        pts = [(x, y) for y in range(self.n) for x in range(self.n) if sdf(x + 0.5, y + 0.5) <= 0]
        if not pts:
            return self
        lx, ly = light
        L = math.hypot(lx, ly) or 1
        lx, ly = lx / L, ly / L
        proj = [(x + 0.5) * lx + (y + 0.5) * ly for x, y in pts]
        lo, hi = min(proj), max(proj)
        span = (hi - lo) or 1
        for (x, y), pr in zip(pts, proj):
            t = base + spread * ((pr - lo) / span * 2 - 1)
            d = sdf(x + 0.5, y + 0.5)
            if d > -1.05:
                gx = sdf(x + 1.5, y + 0.5) - sdf(x - 0.5, y + 0.5)
                gy = sdf(x + 0.5, y + 1.5) - sdf(x + 0.5, y - 0.5)
                gl = math.hypot(gx, gy) or 1
                facing = (gx * lx + gy * ly) / gl
                if facing > 0.25:
                    t += rim * 1.4 * facing
                elif facing < -0.25:
                    t -= core * 1.2 * -facing
            t += grain(x, y, seed) * noise
            if flat is not None:
                t = flat + grain(x, y, seed) * noise
            self.p[x, y] = pick(rmp, t)
        if spec:
            for (x, y) in spec:
                if 0 <= x < self.n and 0 <= y < self.n:
                    self.p[x, y] = rmp[-1]
        return self

    def glow(self, cx, cy, r, color, strength=1.0, steps=4, seed=5):
        """Additive soft light, posterised with grain like vanilla's halo pixels."""
        c = hexc(color) if isinstance(color, str) else color
        for y in range(self.n):
            for x in range(self.n):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / r
                if d < 1:
                    k = (1 - d) ** 1.5 * strength + grain(x, y, seed) * 0.25
                    k = max(0, min(steps, round(k * steps))) / steps
                    if k > 0:
                        o = self.p[x, y]
                        self.p[x, y] = tuple(min(255, int(o[i] + c[i] * k * 0.8)) for i in range(3))
        return self

    def energy(self, sdf, rmp, falloff=2.5, seed=9, hot=None):
        """A glowing shape: hottest (top of ramp) deep inside, down the ramp toward and a
        little past its edge."""
        n = len(rmp)
        hot = n - 1 if hot is None else hot
        for y in range(self.n):
            for x in range(self.n):
                d = sdf(x + 0.5, y + 0.5)
                if d < 1.2:
                    if d < 0:
                        t = 1.6 + (hot - 1.6) * min(1, -d / falloff)
                    else:
                        t = 1.3 - d
                    t += grain(x, y, seed) * 0.9
                    if t >= 0.6 or d < 0:
                        c = pick(rmp, t)
                        o = self.p[x, y]
                        if d < 0 or sum(c) > sum(o):
                            self.p[x, y] = c
        return self

    def streak(self, x0, y0, x1, y1, w, rmp, seed=3):
        """Tapered motion streak, head at (x1,y1) widest and brightest."""
        f = seg(x0, y0, x1, y1, 0.15, w)
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy or 1

        def fn(x, y, d):
            t = max(0, min(1, ((x + 0.5 - x0) * dx + (y + 0.5 - y0) * dy) / L2))
            k = 1 + t * (len(rmp) - 1.5) + (0.8 if d < -w * 0.4 else 0) + grain(x, y, seed) * 0.8
            return pick(rmp, k)
        return self.paint(f, fn)

    def px(self, pts, c):
        c = hexc(c) if isinstance(c, str) else c
        for x, y in pts:
            if 0 <= x < self.n and 0 <= y < self.n:
                self.p[x, y] = c
        return self

    def glint(self, x, y, c=WHITE, arm=1, armc=None):
        self.px([(x, y)], c)
        if arm:
            armc = armc or mix(self.p[x, y], c, 0.6)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                o = self.p[x + dx, y + dy] if 0 <= x + dx < self.n and 0 <= y + dy < self.n else None
                if o is not None:
                    self.p[x + dx, y + dy] = mix(o, c, 0.55)
        return self

    def shade(self, sdf, k=0.45):
        """Darken a region (cast shadows, occlusion)."""
        for y in range(self.n):
            for x in range(self.n):
                if sdf(x + 0.5, y + 0.5) <= 0:
                    o = self.p[x, y]
                    self.p[x, y] = tuple(int(v * k) for v in o)
        return self

    def done(self):
        im = self.im.convert("RGBA")
        p = im.load()
        for i in range(self.n):
            for (x, y) in ((i, 0), (i, self.n - 1), (0, i), (self.n - 1, i)):
                r, g, b, _ = p[x, y]
                p[x, y] = (int(r * 0.8), int(g * 0.8), int(b * 0.8), 255)
        return im


def sheet(rows, path, z=5, label=118):
    """rows: [(name, [im, im, im(, current)])] -> a labelled comparison sheet."""
    from PIL import ImageDraw
    cols = max(len(r[1]) for r in rows)
    cw = N * z + 8
    out = Image.new("RGBA", (label + cols * cw, len(rows) * (N * z + 8)), (28, 28, 34, 255))
    d = ImageDraw.Draw(out)
    for r, (name, ims) in enumerate(rows):
        y = r * (N * z + 8)
        d.text((4, y + N * z // 2 - 6), name, fill=(230, 230, 230, 255))
        for k, im in enumerate(ims):
            # a smaller icon (a 14x14 stack) shows at its own size against the 24s
            iz = im.resize((im.width * z, im.height * z), Image.Resampling.NEAREST)
            out.alpha_composite(iz, (label + k * cw, y))
            d.text((label + k * cw + 3, y + 2), "ABCD"[k] if k < 3 else "now", fill=(255, 255, 255, 255))
    out.save(path)
