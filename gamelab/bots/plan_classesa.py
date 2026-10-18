"""Test-plan checks for the HoH1 classes (mods/classes), plan steps classes.s2-s4: the Thief's
knives, Grappling Hook, Smoke Bomb and Sidestep tooltip; the Gladiator's trident, Net, Gladius
and pit fighter; the Witch Hunter's Pyre, hound and Ward. Each section makes its own lab
character, starts Bandit Keep floor 1 in god mode with the floor cleared, and spawns bandit
brutes as targets.

Skills are cast with `gl castat` (Skill.Activate at a point or along a direction, the call the
targeting helper makes once a target is picked: a position skill's target follows the mouse,
which GameLab can't aim), with the emulated aim held past the castpoint and the target brutes
spawned in the same frame (gl multi). The trident is the main-hand attack, through `gl input`. Projectile
flights and the pyre's lifetime are sampled every frame in-engine by `gl track`; enemy debuffs
come from `gl actorbuffs` (tags such as blindness, immobilize, vulnerability); the Sidestep
tooltip is `gl skilltip`, the skill tree's own text (AppendSkillDesc).

Sections: thief, gladiator, witchhunter."""
import math
import re
import time

from gamelab.bots.plan_checks import Checks as Base
from gamelab.hps import hash_string

BRUTE = "actors/humans/bandits/bandit_brute.unit"
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (0.7071, 0.7071), (-0.7071, 0.7071), (0.7071, -0.7071), (-0.7071, -0.7071)]


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def plain(text):
    """A tooltip without its colour codes (\\c<rgb>, \\d, \\z)."""
    return re.sub(r"\\c[0-9a-fA-F]{6}|\\[dz]", "", text or "")


class Checks(Base):
    # --- plumbing
    def me(self):
        pl = self.gl("state").get("player", {})
        return pl.get("x", 0.0), pl.get("y", 0.0)

    def god_on(self):
        if not self.gl("cvars", "cht_god").get("cvars", {}).get("cht_god"):
            self.hwp("god", 0.4)

    def new_char(self, cls, name):
        self.gl("char", cls, name)
        ok = self.wait_phase("town", 60)
        time.sleep(2)
        st = self.gl("state")
        self.hwp("skillpoints 20", 0.4)
        ok = ok and st.get("player", {}).get("class") == cls
        self.flag(f"{cls}_char", ok, f"phase {st.get('phase')}, class {st.get('player', {}).get('class')}")
        return ok

    def arena(self, tag):
        """Bandit Keep floor 1, god mode, the floor's enemies killed (no killer: no drops)."""
        if not self.start_floor(0):
            self.flag(f"{tag}_mission", False)
            return False
        self.god_on()
        self.gl("kill", 6000, "tag:enemy")
        time.sleep(1)
        return True

    def open_dirs(self):
        """The 8 directions by how far the floor is clear along them (gl terrain, 8 px cells),
        clearest first: [(clear px, (dx, dy))]."""
        t = self.gl("terrain", 160, 8)
        rows, n, step = t.get("rows") or [], t.get("size", 0), t.get("step", 8)
        c = n // 2
        out = []
        for dx, dy in DIRS:
            clear = 0
            for r in range(step, 161, step):
                x, y = c + round(dx * r / step), c + round(dy * r / step)
                if not (0 <= y < len(rows) and 0 <= x < len(rows[y])) or rows[y][x] == "#":
                    break
                clear = r
            out.append((clear, (dx, dy)))
        out.sort(key=lambda e: -e[0])
        return out

    def in_wall(self, x, y):
        """Whether the unit at (x, y) stands inside a wall. gl terrain's point query hits every
        unit but the player, so the summon's own cells always read '#': test a ring 24 px
        around the middle of its body (a crusader's colliders reach 15 px up, 8 px aside)
        instead; in a wall when 7 of its 8 points are blocked. None when off the map."""
        t = self.gl("terrain", 160, 8)
        rows, n, step = t.get("rows") or [], t.get("size", 0), t.get("step", 8)
        hits = 0
        for dx, dy in DIRS:
            cx = n // 2 + round((x + dx * 24 - t.get("x", 0)) / step)
            cy = n // 2 + round((y - 5 + dy * 24 - t.get("y", 0)) / step)
            if not (0 <= cy < len(rows) and 0 <= cx < len(rows[cy])):
                return None
            hits += rows[cy][cx] == "#"
        return hits >= 7

    def to_open(self, need=48):
        """Walk to the nearest floor along one of the 8 directions with no wall within `need`
        px (a passive summon lands within the skill's jitter, 20x30 px, of the player and can
        land inside a wall when the player stands at one); (ok, note)."""
        for _ in range(3):
            t = self.gl("terrain", 160, 8)
            rows, n, step = t.get("rows") or [], t.get("size", 0), t.get("step", 8)
            c, k = n // 2, need // step

            def free(cx, cy):
                return all(0 <= y < len(rows) and 0 <= x < len(rows[y]) and rows[y][x] != "#"
                           for y in range(cy - k, cy + k + 1) for x in range(cx - k, cx + k + 1))

            best = None
            for dx, dy in DIRS:
                for r in range(0, 161 - need, step):
                    x, y = c + round(dx * r / step), c + round(dy * r / step)
                    if rows[y][x] == "#":
                        break
                    if free(x, y):
                        if best is None or r < best[0]:
                            best = (r, (dx, dy))
                        break
            if best is None:
                return False, "no open floor within 160 px"
            r, (dx, dy) = best
            if r == 0:
                return True, f"open floor at {self.me()}"
            # ~115 px/s on foot (the gladiator walked 175 px in 1.5 s)
            self.gl("input", int(r / 115 * 1000) + 60, dx, dy)
            time.sleep(r / 115 + 0.5)
        return False, f"still next to a wall at {self.me()}"

    def brutes(self, r=400):
        return [u for u in self.gl("near", r, "bandit_brute").get("units") or [] if not u.get("dead")]

    def unit(self, uid, filt="bandit_brute", r=600):
        for u in self.gl("near", r, filt).get("units") or []:
            if u["unit"] == uid:
                return u
        return None

    def scene(self, spawns=(), cast=None, aim=None, button=None, hold=900):
        """Brutes at the player + each (dx, dy) of spawns, an emulated aim (and button) held
        for hold ms, and castat cast = (skillId, dx, dy), all in one frame (gl multi): a gl
        command a frame gives the brutes ~0.3 s to walk between them. The aim is held past the
        castpoint and update-aim window, or the skill's aim falls back to the real mouse.
        Returns (castat reply, [the new brute nearest each spawn point, or None])."""
        before = {u["unit"] for u in self.brutes(600)}
        px, py = self.me()
        args = []
        for dx, dy in spawns:
            args += ["spawn", BRUTE, round(dx), round(dy), "+"]
        if aim:
            args += ["input", hold, 0, 0, round(aim[0], 4), round(aim[1], 4)] + ([button] if button else []) + ["+"]
        if cast:
            args += ["castat", cast[0], round(cast[1]), round(cast[2]), "nocd", "+"]
        mark = len(self.g.gl)
        self.gl("multi", *args[:-1])
        c = {}
        if cast:
            # multi's sub-replies come under "<id>.<k>"; castat's is the one naming the skill
            c = next((o for o in self.g.gl[mark:] if o.get("skill") == cast[0] and "activated" in o), {})
        new = [u for u in self.brutes(600) if u["unit"] not in before] if spawns else []
        found = []
        for dx, dy in spawns:
            new.sort(key=lambda u: dist((u["x"], u["y"]), (px + dx, py + dy)))
            found.append(new.pop(0) if new else None)
        return c, found

    def clear(self):
        self.gl("kill", 800, "tag:enemy")
        time.sleep(0.5)

    def buffs_of(self, uid, r=400):
        for a in self.gl("actorbuffs", r, "bandit_brute").get("actors") or []:
            if a["unit"] == uid:
                return a
        return None

    def tags(self, actor):
        return sorted({t for b in (actor or {}).get("buffs", []) for t in b.get("tags", [])})

    def track(self, ms, radius, filt, cast):
        """Start a `gl track` of units matching filt, then run cast(); the track event."""
        # wait_gl looks at every event of the session, and a bot step starts a fresh Checks:
        # the tag must be unique per run, not per section
        self._tracks = getattr(self, "_tracks", 0) + 1
        tag = f"cla{int(time.time() * 1000) % 100000000}x{self._tracks}"
        r = self.gl("track", tag, ms, radius, filt)
        if not r.get("ok"):
            return None, r
        res = cast()
        ev = self.g.wait_gl(lambda o: o.get("ev") == "track" and o.get("tag") == tag, ms / 1000 + 10)
        return ev, res

    def summon_wait(self, filt, timeout, exclude=()):
        """Poll near for a live summon matching filt (not one of exclude) up to timeout s;
        (unit entry, seconds waited) or (None, timeout)."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            us = [u for u in self.gl("near", 800, filt).get("units") or [] if not u.get("dead") and u["unit"] not in exclude]
            if us:
                return us[0], time.time() - t0
            time.sleep(0.5)
        return None, timeout

    def follows(self, uid, filt, f):
        """Walk 1.5 s along f, wait for the summon to catch up; (ok, note)."""
        p0, s0 = self.me(), self.unit(uid, filt, 800)
        wall = s0 and self.in_wall(s0["x"], s0["y"])
        self.gl("input", 1500, f[0], f[1])
        time.sleep(1.8 + 2.5)
        p1, s1 = self.me(), self.unit(uid, filt, 800)
        if not s0 or not s1:
            return False, f"summon lost: before {s0}, after {s1}"
        walked = dist(p0, p1)
        moved = dist((s0["x"], s0["y"]), (s1["x"], s1["y"]))
        gap = dist(p1, (s1["x"], s1["y"]))
        return walked > 30 and moved > 20 and gap < 100, (f"player walked {walked:.0f}, summon moved {moved:.0f}, gap now {gap:.0f}"
                                                          + (", the summon stood in a wall" if wall else ""))

    # --- sections
    def thief(self):
        """classes.s2: knives fan out and hit, Grappling Hook pulls you, Smoke Bomb blinds, the
        Sidestep tooltip shows the evade chance."""
        if not self.new_char("hwp_thief", "LabThief"):
            return
        # Sidestep (passive, starting level 0): the tooltip at level 1 and 2
        sk = self.gl("skill", "hwp_thief_sidestep", 1)
        t1 = self.gl("skilltip", "hwp_thief_sidestep")
        t2 = self.gl("skilltip", "hwp_thief_sidestep", 2)
        p1, p2 = plain(t1.get("text")), plain(t2.get("text"))
        self.flag("sidestep_tip_chance", sk.get("level") == 1 and "evade 5% of attacks" in p1
                  and "%chance%" not in p1 and "evade 8% of attacks" in p2,
                  f"level {sk.get('level')}: {p1!r}; level 2: {p2[:80]!r}")
        self.flag("sidestep_tip_levels", "Evade chance" in p1 and "5%/8%/11%/14%/18%" in p1, p1[-80:])
        if not self.arena("thief"):
            return
        dirs = self.open_dirs()
        clear, f = dirs[0]
        self.notes.append(f"thief open dirs {dirs[:3]}")

        # knives: a fan of 3 (level 1), 14 degrees across (ShootProjectileFan spread 14)
        ev, c = self.track(1500, 400, "rog_throwing_knife",
                           lambda: self.scene(cast=("hwp_thief_knives", f[0] * 100, f[1] * 100), aim=f)[0])
        tracks = (ev or {}).get("tracks", [])
        base = math.atan2(f[1], f[0])
        angs = []
        for t in tracks:
            vx, vy = t["x1"] - t["x0"], t["y1"] - t["y0"]
            if math.hypot(vx, vy) < 3:
                vx, vy = t["x0"] - t["px0"], t["y0"] - t["py0"]
            a = math.degrees(math.atan2(vy, vx) - base)
            angs.append(round((a + 180) % 360 - 180, 1))
        spread = max(angs) - min(angs) if angs else 0
        self.flag("knives_fan", c.get("activated") and len(tracks) == 3 and 8 <= spread <= 20,
                  f"cast {c.get('activated')}, {len(tracks)} knives at {sorted(angs)} deg (spread {spread:.1f}), "
                  f"flight {[t['t1'] - t['t0'] for t in tracks]} ms")
        # knives hit: a brute ahead
        c, (b,) = self.scene([(f[0] * 45, f[1] * 45)], ("hwp_thief_knives", f[0] * 100, f[1] * 100), f)
        if b:
            hp0 = 1.0  # a fresh spawn
            time.sleep(0.8)
            b1 = self.unit(b["unit"])
            hp1 = b1.get("hp") if b1 else 0.0
            self.flag("knives_hit", c.get("activated") and hp1 < hp0, f"brute hp {hp0} -> {hp1}")
        else:
            self.flag("knives_hit", False, "no brute spawned")
        self.clear()

        # Grappling Hook: the player lands at the target (the vanilla rogue skill's Teleport)
        clear, f = self.open_dirs()[0]
        want = max(40, min(110, clear - 24))
        p0 = self.me()
        c, _ = self.scene(cast=("rog_grappling_hook", f[0] * want, f[1] * want), aim=f)
        time.sleep(0.9)
        p1 = self.me()
        along = (p1[0] - p0[0]) * f[0] + (p1[1] - p0[1]) * f[1]
        self.flag("grapple_pulls", c.get("activated") and along >= 0.6 * want,
                  f"cast {c.get('activated')} to {c.get('tx')},{c.get('ty')} ({want} px, clear {clear}); moved {along:.0f} along, {dist(p0, p1):.0f} total")

        # Smoke Bomb: blindness (and slow) on enemies in the cloud
        clear, f = self.open_dirs()[0]
        c, (b,) = self.scene([(f[0] * 80, f[1] * 80)], ("hwp_thief_smoke", f[0] * 80, f[1] * 80), f)
        if b:
            time.sleep(0.6)
            tags = self.tags(self.buffs_of(b["unit"]))
            self.flag("smoke_blinds", c.get("activated") and "blindness" in tags, f"cast {c.get('activated')}, brute buff tags {tags}")
        else:
            self.flag("smoke_blinds", False, "no brute spawned")
        self.clear()
        self.to_town()

    def gladiator(self):
        """classes.s3: the trident thrusts, Net roots enemies, the Gladius comes back, a pit
        fighter follows you (and comes again ~20 s after one dies)."""
        if not self.new_char("hwp_gladiator", "LabGladiator"):
            return
        # inspect player equipped: the main hand is a list whose [1] is HashString(item id)
        mh = self.main_hand()
        want = hash_string("hwp_trident_01")
        self.flag("trident_equipped", isinstance(mh, list) and len(mh) > 1 and int(mh[1]) & 0xFFFFFFFF == want,
                  f"main hand {str(mh)[:120]}, HashString(hwp_trident_01) = {want}")
        if not self.arena("gladiator"):
            return
        # trident: a thrust (MeleeSwing dist 40, 3 rays over 16 px; HoH1: 6 rays over a 30 deg
        # arc, dist 30, the same ~16 px at its reach) hits the brute in front, not the one beside
        clear, f = self.open_dirs()[0]
        side = (-f[1], f[0])
        # spawned and attacked in one frame. The attack is "repeating": a button still down
        # when the 600 ms animation ends starts a second thrust whose castpoint (800 ms) falls
        # after a 700 ms hold, aimed by the real mouse (20261018-125943 hit the side brute so).
        # 350 ms covers the castpoint and update-aim (0-200 ms) and starts one thrust.
        _, (front, beside) = self.scene([(f[0] * 26, f[1] * 26), (side[0] * 40, side[1] * 40)], aim=f, button="main", hold=350)
        if front and beside:
            fu, bu = front["unit"], beside["unit"]
            h0 = {fu: 1.0, bu: 1.0}  # fresh spawns
            time.sleep(1.2)
            h1 = {u["unit"]: u.get("hp") for u in self.brutes(200)}
            self.flag("trident_thrust_hits", h1.get(fu, 0) < h0.get(fu, 1), f"front brute hp {h0.get(fu)} -> {h1.get(fu)}")
            self.flag("trident_thrust_narrow", fu in h1 and h1.get(bu) == h0.get(bu),
                      f"brute beside hp {h0.get(bu)} -> {h1.get(bu)}")
        else:
            self.flag("trident_thrust_hits", False, f"spawn failed: {front} {beside}")
            self.flag("trident_thrust_narrow", False, "spawn failed")
        self.clear()

        # Net: immobilize on the netted brute; it stays put while a brute outside the net walks in
        dirs = self.open_dirs()
        (_, f), (_, g) = dirs[0], dirs[1]
        c, (a, b) = self.scene([(f[0] * 100, f[1] * 100), (g[0] * 100, g[1] * 100)],
                               ("hwp_gladiator_net", f[0] * 100, f[1] * 100), f)
        if a and b:
            time.sleep(0.4)
            a1, b1 = self.unit(a["unit"]), self.unit(b["unit"])
            ta, tb = self.tags(self.buffs_of(a["unit"])), self.tags(self.buffs_of(b["unit"]))
            time.sleep(1.6)
            a2, b2 = self.unit(a["unit"]), self.unit(b["unit"])
            self.flag("net_immobilize", c.get("activated") and "immobilize" in ta and "immobilize" not in tb,
                      f"cast {c.get('activated')}, netted tags {ta}, other {tb}")
            if a1 and a2 and b1 and b2:
                ma, mb = dist((a1["x"], a1["y"]), (a2["x"], a2["y"])), dist((b1["x"], b1["y"]), (b2["x"], b2["y"]))
                self.flag("net_roots", ma < 4 and mb > 10, f"netted moved {ma:.1f} in 1.6 s, the other {mb:.1f}")
            else:
                self.flag("net_roots", False, f"lost a brute: {a1} {a2} {b1} {b2}")
        else:
            self.flag("net_immobilize", False, f"spawn failed: {a} {b}")
            self.flag("net_roots", False, "spawn failed")
        self.clear()

        # Gladius: the whirling axe goes out and flies back to the thrower
        clear, f = self.open_dirs()[0]
        ev, c = self.track(4500, 500, "whirling_axe",
                           lambda: self.scene(cast=("hwp_gladiator_gladius", f[0] * 100, f[1] * 100), aim=f)[0])
        tracks = (ev or {}).get("tracks", [])
        t = tracks[0] if tracks else {}
        dmax, dlast, dback = t.get("dmax", 0), t.get("dlast", 999), t.get("dminafter", 999)
        self.flag("gladius_returns", c.get("activated") and len(tracks) == 1 and dmax >= 40 and dlast <= 0.4 * dmax and dback <= 30,
                  f"cast {c.get('activated')}, {len(tracks)} axe(s): out to {dmax:.0f} px at {t.get('tmax')} ms, "
                  f"back to {dback:.0f}, last seen at {dlast:.0f} px after {t.get('t1', 0) - t.get('t0', 0)} ms")

        # Pit Fighters (passive summon, starting level 0): the priest's pikeman
        pk = "crusader_pikeman"
        ok, note = self.to_open()
        self.notes.append("pit fighter spot: " + note)
        sk = self.gl("skill", "hwp_gladiator_pit_fighters", 1)
        s, waited = self.summon_wait(pk, 30)
        self.flag("pit_fighter_arrives", sk.get("level") == 1 and s is not None,
                  f"skill level {sk.get('level')}, first pikeman after {waited:.1f} s (source: first at min(interval, 1 s))")
        if s:
            ok, note = self.follows(s["unit"], pk, self.open_dirs()[0][1])
            self.flag("pit_fighter_follows", ok, note)
            # the interval (20 s) runs again once the summon is gone. The engine reuses unit ids
            # (20261018-125943: the next pikeman came back as the killed one's id 29587 after
            # 20.3 s), so wait for the dead one to go and then for any live pikeman
            k = self.gl("kill", 2000, pk)
            t_kill = time.time()
            while time.time() - t_kill < 3 and self.gl("near", 800, pk).get("units"):
                time.sleep(0.3)
            s2, _ = self.summon_wait(pk, 30)
            waited = time.time() - t_kill
            self.flag("pit_fighter_20s", k.get("killed", 0) >= 1 and s2 is not None and 15 <= waited <= 25,
                      f"killed {k.get('killed')}, next pikeman after {waited:.1f} s")
        self.to_town()

    def witchhunter(self):
        """classes.s4: the Pyre burns enemies next to it for 8 s, a hound follows, the Ward
        leaves enemies vulnerable."""
        if not self.new_char("hwp_witch_hunter", "LabHunter"):
            return
        sk = self.gl("skill", "hwp_witch_hunter_ward", 1)
        self.notes.append(f"ward skill {sk}")
        if not self.arena("witchhunter"):
            return
        # Ward of Branding: fire damage + vulnerability in the area
        clear, f = self.open_dirs()[0]
        c, (b,) = self.scene([(f[0] * 70, f[1] * 70)], ("hwp_witch_hunter_ward", f[0] * 70, f[1] * 70), f)
        if b:
            hp0 = 1.0  # a fresh spawn
            time.sleep(0.6)
            a = self.buffs_of(b["unit"])
            tags = self.tags(a)
            left = [x.get("left") for x in (a or {}).get("buffs", []) if "vulnerability" in x.get("tags", [])]
            self.flag("ward_vulnerable", c.get("activated") and "vulnerability" in tags,
                      f"cast {c.get('activated')}, tags {tags}, vulnerability left {left} ms, hp {hp0} -> {(a or {}).get('hp')}")
        else:
            self.flag("ward_vulnerable", False, "no brute spawned")
        self.clear()

        # Pyre: a player-team unit 24 px ahead that explodes fire (radius 56) every second, ttl 8 s
        clear, f = self.open_dirs()[0]
        samples = []
        pyre = "witchhunter/units/pyre"

        def cast():
            c, (b,) = self.scene([(f[0] * 50, f[1] * 50)], ("hwp_witch_hunter_pyre", f[0] * 100, f[1] * 100), f)
            t0 = time.time()
            while b and time.time() - t0 < 11:
                u = self.unit(b["unit"])
                p = [x for x in self.gl("near", 300, pyre).get("units") or []]
                samples.append((round(time.time() - t0, 1), u.get("hp") if u else None, p[0].get("hp") if p else None))
                time.sleep(0.7)
            return c, b
        ev, res = self.track(11000, 300, pyre, cast)
        c, b = res if isinstance(res, tuple) else (res, None)
        tracks = (ev or {}).get("tracks", [])
        life = tracks[0]["t1"] - tracks[0]["t0"] if tracks else 0
        self.notes.append(f"pyre samples (s, brute hp, pyre hp): {samples}")
        self.flag("pyre_spawned", c.get("activated") and len(tracks) == 1, f"cast {c.get('activated')}, {len(tracks)} pyre(s)")
        self.flag("pyre_8s", 7400 <= life <= 8800, f"pyre lived {life} ms")
        alive = [s for s in samples if s[2] is not None and s[1] is not None]
        after = [s for s in samples if s[2] is None and s[1] is not None and s[0] * 1000 > life + 1200]
        burned = alive[0][1] - alive[-1][1] if len(alive) >= 2 else 0
        self.flag("pyre_burns", bool(b) and burned > 0.05, f"brute hp fell {burned:.3f} while the pyre stood")
        self.flag("pyre_burn_ends", len(after) >= 2 and after[0][1] == after[-1][1],
                  f"after it: {[(s[0], s[1]) for s in after]}")
        self.clear()

        # Hound (passive summon, starting level 0): the ranger's wolf
        wolf = "ranger/units/wolf"
        ok, note = self.to_open()
        self.notes.append("hound spot: " + note)
        sk = self.gl("skill", "hwp_witch_hunter_hound", 1)
        s, waited = self.summon_wait(wolf, 30)
        self.flag("hound_arrives", sk.get("level") == 1 and s is not None, f"skill level {sk.get('level')}, hound after {waited:.1f} s")
        if s:
            ok, note = self.follows(s["unit"], wolf, self.open_dirs()[0][1])
            self.flag("hound_follows", ok, note)
        self.to_town()


def run(p, sections="thief,gladiator,witchhunter", **_):
    c = Checks(p)
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
