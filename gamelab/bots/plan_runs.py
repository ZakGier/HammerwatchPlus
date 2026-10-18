"""Test-plan checks for the runs group: locked reward chests with padlocks (keys s3), the
Architect row of the run-start loadout (architect s1), the town portal's mission window and minimap pip
(campaign s1), the five HoH1 boss floors of The Forsaken Tower (hoh1floors s2-s6) and the
two Battlements floors up to Thundersnow (hoh1floors s7).

The bosses are measured in-engine by `gl trail` (Verbs_runs.as): every frame it follows the
boss's units and projectiles, so a ground spike that lives for two seconds is seen from its
first frame to its last; `gl rayhit` gives where a projectile from a point would stop (the
first Shot raycast hit that is no damage taker, or tiles harder than destroy-at-hardness),
`gl actors` what a boss is casting and whether it can be targeted.

Sections: keys_padlock, architect_loadout, portal_minimap, boss_setup, boss_golem,
boss_warden, boss_councilors, boss_watcher, boss_vampire, battlements."""
import json
import math
import re
import time

from gamelab.bots.plan_checks import Checks as Base

HOH1 = "hwp_forsaken_tower_hoh1"
# 0-based floors of missions_hwp_forsaken_tower_hoh1.sval
FLOOR_MINES_BOSS, FLOOR_PRISON_BOSS, FLOOR_ARMORY_BOSS, FLOOR_ARCHIVES_BOSS = 2, 5, 8, 11
FLOOR_CHAMBERS_BOSS, FLOOR_BATTLEMENTS_1, FLOOR_BATTLEMENTS_2, FLOOR_DRAGON = 14, 15, 16, 17
# a boss and its NG+ copies (HWP/Campaign/HoH1/UnitMap.as: _t2 from NG+1, t3 3, t4 5, t5 10)
WARDEN_UNITS = ("warden.unit",) + tuple(f"warden_t{i}.unit" for i in range(2, 6))
VAMPIRE_UNITS = ("vampire.unit",) + tuple(f"vampire_t{i}.unit" for i in range(2, 6))


def tier_of(ngp):
    return "" if not ngp else "_t" + str(2 + sum(ngp >= n for n in (3, 5, 10)))
# boss_chambers.lvl: the BossLichNodes the vampire flies between, and its VampireCenterNode last
VAMPIRE_NODES = [(-128, -64), (96, -64), (-16, -128), (-96, 80), (64, 80), (-16, -16)]
# the exits' UseTrigger areas (Physics_Rectangle 48x16): battlements_1 'right' (area 8) and
# 'left' (area 9), battlements_2 (area 17)
BATTLEMENTS_EXITS = {"battlements_1": [(2928, -872), (656, -1288)], "battlements_2": [(1080, -1808)]}
# boss_armory.lvl's BossLichNode positions (the wraiths walk node to node)
LICH_NODES = [(0, -352), (128, 16), (-272, -112), (-96, -336), (224, -192), (-128, 16), (-160, -272),
              (272, 0), (160, -272), (0, 16), (-224, -192), (96, -336), (272, -112), (-272, 0)]
WRAITHS = ("wraith_staff.unit", "wraith_scythe.unit", "wraith_mage.unit")
# open floor inside the Armory's BossLichRoom (center (0,-144), 288x224; diagonal walls cut its
# top corners, statues at (+-96,-96) and (0,-224)): from anywhere in the room one of these is
# more than 100 px away
COUNCIL_SPOTS = [(-120, -40), (120, -40), (-60, -190), (60, -190)]
TIERS = {"bronze": 0, "silver": 1, "gold": 2, "platinum": 2}


def arch_mul(n_buffs, arch_lvl):
    """CalcArchitectCostMul (scripts/Missions/MissionArchitect.as), no debuffs."""
    n = max(1, n_buffs)
    if arch_lvl >= 1:
        return (n ** 1.6 - 1) / 7.0 + 1.0
    return (n ** 1.8 - 1) / 6.0 + 1.0


def has_num(text, n):
    return re.search(r"(?<!\d)%d(?!\d)" % n, text or "") is not None


def seg_dist(p, a, b):
    """Distance from point p to the segment a-b."""
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    sq = dx * dx + dy * dy
    t = 0 if sq == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / sq))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


class Checks(Base):
    # --- plumbing
    def god_on(self):
        if not self.gl("cvars", "cht_god").get("cvars", {}).get("cht_god"):
            self.hwp("god", 0.4)

    def new_char(self, cls, name):
        """A fresh character, in town. gl char swaps the record and respawns the player on the
        level already loaded (no level change): in a run the new character would stand in that
        run (plan-runs-a 124403), so the old one leaves the run first."""
        was = self.gl("state").get("phase")
        if was != "town":
            self.to_town()
        self.gl("char", cls, name)
        ok = self.wait_phase("town", 60)
        if not ok:
            self.to_town()
            ok = self.wait_phase("town", 30)
        time.sleep(2)
        st = self.gl("state")
        ok = ok and st.get("phase") == "town" and st.get("player", {}).get("class") == cls
        self.notes.append(f"char {name}: phase {was} -> {st.get('phase')}, class {st.get('player', {}).get('class')}")
        return ok

    def window(self):
        return self.gl("state").get("window") or ""

    def trail(self, ms, radius, filt, step=100, during=None):
        """Start a `gl trail`, run during(until) meanwhile, then wait for the trail event."""
        # wait_gl looks at every event of the session and a bot step starts a fresh Checks:
        # the tag must be unique per run
        self._trails = getattr(self, "_trails", 0) + 1
        tag = f"run{int(time.time() * 1000) % 100000000}x{self._trails}"
        r = self.gl("trail", tag, ms, radius, filt, step)
        if not r.get("ok"):
            self.notes.append(f"trail {filt}: {r}")
            return None
        if during:
            during(time.time() + ms / 1000.0)
        # a long trail comes in parts (gl trail: each event under the print limit)
        ev = self.g.wait_gl(lambda o: o.get("ev") == "trail" and o.get("tag") == tag, ms / 1000 + 15)
        if ev is None:
            return None
        ev = dict(ev, units=list(ev.get("units") or []))
        for k in range(1, ev.get("parts") or 1):
            more = self.g.wait_gl(lambda o: o.get("ev") == "trail" and o.get("tag") == tag and o.get("part") == k, 10)
            if more is None:
                self.notes.append(f"trail {filt}: part {k} of {ev.get('parts')} missing")
                break
            ev["units"] += more.get("units") or []
        return ev

    ngp = None      # run(ngp=...): the floors start at this NG+

    def boss_floor(self, floor, level, tag):
        r = self.gl("mission", HOH1, floor, *([self.ngp] if self.ngp is not None else []))
        ok = bool(r.get("ok")) and self.wait_phase("mission", 120)
        time.sleep(3)
        st = self.gl("state")
        lv = st.get("level", "")
        ok = ok and level in lv
        self.flag(f"{tag}_floor", ok, f"mission {r.get('ok')}, level {lv}, ngp {st.get('ngp')}")
        if self.ngp is not None:
            self.flag(f"{tag}_ngp", abs((st.get("ngp") or 0) - self.ngp) < 0.01, f"ngp {st.get('ngp')}, want {self.ngp}")
        if ok:
            self.god_on()
        return ok

    def wait_units(self, radius, filt, n=1, timeout=20, names=None):
        """Poll near until n live units match (names: their .unit file names), up to timeout s."""
        end = time.time() + timeout
        us = []
        while time.time() < end:
            us = [u for u in self.gl("near", radius, filt).get("units") or []
                  if not u.get("dead") and (names is None or u.get("name", "").split("/")[-1] in names)]
            if len(us) >= n:
                break
            time.sleep(0.7)
        return us

    # --- keys s3
    def reward_chests(self):
        return [u for u in self.gl("near", 5000, "items/chests/chest_").get("units") or []
                if u.get("name", "").split("/")[-1].split("_")[1] in TIERS]

    def locks(self):
        return self.gl("near", 5000, "chest_lock").get("units") or []

    @staticmethod
    def lock_of(chest, locks):
        # HWPChest.SpawnLock: the padlock at the chest's position, 6 px up
        for lk in locks:
            if abs(lk["x"] - chest["x"]) <= 2 and abs(lk["y"] - (chest["y"] - 6)) <= 2:
                return lk
        return None

    def key_counts(self):
        st = self.hwp("keys", 0.3, until="Keys:")
        c = re.findall(r"Keys: bronze (\d+), silver (\d+), gold (\d+), ace (\d+)", st)
        return [int(x) for x in c[-1]] if c else None

    def keys_padlock(self):
        """keys s3: with keys.lock_chance 1 every reward chest of a floor has a padlock; a use
        without the key does nothing; with it the padlock vanishes, the key count drops by one
        and loot spawns."""
        if not self.new_char("paladin", "LabKeys"):
            self.flag("keys_char", False)
        self.hwp("set keys.lock_chance 1")
        self.hwp("set keys.ace_chance 0")
        self.hwp("set keys.debug 1")  # keygive is a debug command
        chests, floor = [], -1
        # Bandit Keep floors roll 0 or 1 equipment chests: next floor until one has some
        for floor in range(5):
            if not self.start_floor(floor):
                break
            self.gl("cull")
            chests = self.reward_chests()
            if chests:
                break
        st = self.hwp("keys", 0.3, until="locked chests this level")
        locked = re.findall(r"locked chests this level: (\d+)", st)
        n = int(locked[-1]) if locked else -1
        locks = self.locks()
        with_lock = [c for c in chests if self.lock_of(c, locks)]
        names = sorted({c["name"].split("/")[-1] for c in chests})
        self.flag("pad_all_locked", n > 0 and n == len(chests), f"floor {floor}: locked {n}, chests {len(chests)}: {names}")
        self.flag("pad_every_chest_padlock", bool(chests) and len(with_lock) == len(chests),
                  f"{len(with_lock)}/{len(chests)} chests with a padlock, {len(locks)} padlocks")
        if not chests:
            return
        counts = self.key_counts() or [0, 0, 0, 0]
        # a chest whose key the player lacks (fresh character: none), by the Pilot's walk
        c, r, mark = None, None, 0
        for cand in chests:
            tier = cand["name"].split("/")[-1].split("_")[1]
            if counts[TIERS[tier]]:
                continue
            mark = len(self.g.read_log())
            r = self.p.use(cand["unit"], timeout=40)
            if r.result != "no_route":
                c = cand
                break
            self.notes.append(f"pad: no route to {cand['name']} at {cand.get('x')},{cand.get('y')}")
        if c is None:
            c = chests[0]
            self.gl("teleport", c["x"], c["y"] + 20)
            time.sleep(0.5)
            mark = len(self.g.read_log())
            r = self.p.use(c["unit"], timeout=20)
        tier = c["name"].split("/")[-1].split("_")[1]
        key = "gold" if tier == "platinum" else tier
        time.sleep(1.5)
        log = self.g.read_log()[mark:]
        still = [u for u in self.reward_chests() if u["unit"] == c["unit"]]
        lock0 = self.lock_of(c, self.locks())
        us = self.gl("usables").get("usables") or []
        mine = [u for u in us if (u.get("unit") or {}).get("unit") == c["unit"]]
        self.flag("pad_no_key_nothing", "unlocked a" not in log and bool(still) and lock0 is not None
                  and not any(u.get("canUse") for u in mine),
                  f"{r.result}: {r.reason}; chest there {bool(still)}, padlock there {lock0 is not None}, usable {mine[:1]}")
        around = self.gl("near", 80, "items/").get("units") or []
        before_ids = {u["unit"] for u in around}
        self.hwp(f"keygive {key} 1", 0.3, until="key(s)")
        time.sleep(0.5)
        k0 = self.key_counts()
        mark = len(self.g.read_log())
        for dx, dy in [(0, 0), (0, -24), (24, 0), (-24, 0), (0, 40)]:
            if (dx, dy) != (0, 0):
                self.gl("teleport", c["x"] + dx, c["y"] + dy)
                time.sleep(0.5)
            r = self.p.use(c["unit"], timeout=40)
            if "stuck" not in (r.reason or ""):
                break
        time.sleep(2.5)
        log = self.g.read_log()[mark:]
        k1 = self.key_counts()
        lock1 = self.lock_of(c, self.locks())
        gone = not [u for u in self.reward_chests() if u["unit"] == c["unit"]]
        after = self.gl("near", 80, "items/").get("units") or []
        new = sorted(u["name"].split("/")[-1] for u in after if u["unit"] not in before_ids)
        i = TIERS[tier]
        self.flag("pad_key_opens", f"unlocked a {key} chest" in log and gone, f"{c['name']}: {r.result}: {r.reason}")
        self.flag("pad_padlock_vanishes", lock0 is not None and lock1 is None,
                  f"padlock before {lock0 and lock0['unit']}, after {lock1}")
        self.flag("pad_key_spent", bool(k0 and k1) and k1[i] == k0[i] - 1, f"{key} keys {k0} -> {k1}")
        self.flag("pad_loot_spawned", bool(new), f"{tier} chest dropped {new}")

    # --- architect s1
    def architect_loadout(self):
        """architect s1: the Architect row of the run-start loadout is clickable; picks
        register; the picker's cost and multiplier are vanilla's (CalcCost: the summed cost
        times CalcArchitectCostMul); starting the run takes that cost."""
        town = self.new_char("paladin", "LabArchitect")
        self.flag("arch_town", town, "the new character is in town" if town else "the new character is not in town")
        if not town:
            return
        b = self.gl("build", "architect")
        lvl = (self.gl("buildings").get("buildings") or {}).get("architect", -1)
        self.flag("arch_building", lvl is not None and lvl >= 0, f"build {b.get('ok')} {b.get('error', '')}, variation {lvl}")
        self.set_gold(100000)
        self.gl("material", "wood", 200)
        self.gl("material", "stone", 200)
        time.sleep(0.3)
        # the console cheat opens the run-start loadout (MissionGameMode StartMission)
        self.g.console("mission_start dark_citadel")
        time.sleep(2)
        w = self.window()
        self.flag("arch_loadout_open", "MissionLoadout" in w, f"window {w}")
        # the row is a clone of the loadout's "rect" button whose func is "architect open"
        r = self.gl("pressfunc", "architect", "open")
        time.sleep(1)
        w2 = self.window()
        self.flag("arch_row_clickable", r.get("ok") and "SelectArchitectSelector" in w2,
                  f"pressfunc {r.get('widget')} id {r.get('wid')!r} {r.get('error', '')}, window {w2}")
        if "SelectArchitectSelector" not in w2:
            return
        cost0 = self.widget("total-cost").get("text", "")
        picks = ["architect_far_sight", "architect_toppled_towers"]
        mark = len(self.g.read_log())
        pressed = [self.gl("press", pk).get("ok") for pk in picks]
        time.sleep(1)
        log = self.g.read_log()[mark:]
        n_picks = len(re.findall(r"\[HWP:architect\][^\n]* picks ", log))
        st = self.hwp("architect", 0.4)
        self.flag("arch_picks", all(pressed) and n_picks == 2, f"pressed {pressed}, {n_picks} pick lines; {st.strip()[-200:]}")
        cost = self.widget("total-cost").get("text", "")
        mul_t = self.widget("cost-mul").get("text", "")
        mul = arch_mul(2, max(0, lvl or 0))
        # vanilla: 2000 gold, 10 wood, 5 stone summed, then int(x * mul)
        want = {"gold": int(2000 * mul), "wood": int(10 * mul), "stone": int(5 * mul)}
        pct = int(mul * 100 + 0.5)
        self.flag("arch_mul_vanilla", has_num(mul_t, pct), f"{mul_t!r}, vanilla {pct}% (architect variation {lvl})")
        self.flag("arch_cost_vanilla", all(has_num(cost, v) for v in want.values()),
                  f"{cost!r} (no picks: {cost0!r}), vanilla {want}; per-item rounding would say {2 * int(1000 * mul)} gold")
        self.gl("func", "exit", "yes")
        time.sleep(1)
        w3 = self.window()
        if "SelectArchitectSelector" in w3:
            self.g.key("escape")
            time.sleep(0.8)
            w3 = self.window()
        inv0 = self.gl("inv").get("materials", {})
        self.gl("func", "play")
        # OnPlay spends the cost in town, just before the level changes
        reads = []
        end = time.time() + 2.5
        while time.time() < end:
            try:
                if self.gl("state", timeout=4).get("phase") != "town":
                    break
                reads.append(self.gl("inv", timeout=4).get("materials", {}).get("gold"))
            except Exception as e:
                reads.append(repr(e)[:40])
                break
            time.sleep(0.3)
        ok = self.wait_phase("mission", 120)
        time.sleep(3)
        buffs = self.gl("inspect", "player", "architect-buffs").get("value")
        self.flag("arch_run_started", ok and isinstance(buffs, list) and len(buffs) == 2,
                  f"window before play {w3}, buffs {json.dumps(buffs)[:200]}")
        self.to_town()
        inv2 = self.gl("inv").get("materials", {})
        g0 = inv0.get("gold", -1)
        spent = [g0 - x for x in reads if isinstance(x, int)] + [g0 - inv2.get("gold", g0)]
        self.flag("arch_gold_taken", want["gold"] in spent,
                  f"gold {g0}: in town after play {reads}, back in town {inv2.get('gold')}; vanilla cost {want['gold']}; "
                  f"wood {inv0.get('wood')} -> {inv2.get('wood')}, stone {inv0.get('stone')} -> {inv2.get('stone')}")

    # --- campaign s1
    def portal_minimap(self):
        """campaign s1: the portal is in town; used, it opens the mission window offering The
        Forsaken Tower (18 floors), closed again without starting; then the HUD minimap on
        (ui_minimap 1) and the player 70 px south of it, for the shot of its pip."""
        town = self.new_char("paladin", "LabPortal")
        self.flag("pip_town", town, "the new character is in town" if town else "the new character is not in town")
        if not town:
            return
        p = self.gl("near", 8000, "forsaken_portal").get("units") or []
        self.flag("pip_portal_in_town", bool(p), f"{p[:1]}")
        if not p:
            return
        px, py = p[0]["x"], p[0]["y"]
        # a fresh character hasn't done the story intro: the portal only says it's dormant
        # (plan-t11 094708), so the intro flag first
        self.g.console("cht_set_flag mission_story_intro_find_npcs 1 0")
        self.gl("teleport", px, py + 50)
        time.sleep(1)
        u = self.gl("use", "forsaken_portal")
        time.sleep(0.8)
        w = self.window()
        # the window's entries (EntryShopMission) draw their title and ": <subtitle>" as
        # BitmapStrings, which the widgets dump can't read back: their text is the shop items'
        # GetTitle/GetSubTitle (gl shop), and the dump shows one visible entry per item
        items = self.gl("shop").get("items") or []
        titles = [(it.get("title", ""), it.get("sub", "")) for it in items]
        entries = [n for r in self.gl("widgets", 20).get("roots", []) for n in r.get("nodes", [])
                   if n.get("type") == "EntryShopMission" and n.get("visible")]
        listed = any(t.strip().lower() == "the forsaken tower" and has_num(sub, 18) for t, sub in titles)
        if w:
            self.g.shot("portal-window")
        self.flag("pip_portal_offers_tower", u.get("ok") and "Mission" in w and listed and len(entries) >= len(items),
                  f"use {u.get('ok')}, window {w!r}, items {titles}, {len(entries)} visible entries (shot portal-window)")
        for _ in range(4):
            if not self.window():
                break
            self.g.key("escape")
            time.sleep(0.5)
        st = self.gl("state")
        self.flag("pip_portal_closed", not st.get("window") and st.get("phase") == "town",
                  f"window {st.get('window')!r}, phase {st.get('phase')}")
        self.gl("teleport", px, py + 70)
        time.sleep(1)
        self.g.console("ui_minimap 1")
        time.sleep(1)
        cv = self.gl("cvars", "ui_minimap").get("cvars", {})
        self.flag("pip_minimap_on", bool(cv.get("ui_minimap")), f"{cv}; portal at {px},{py}")

    # --- hoh1floors s2-s5
    def boss_setup(self):
        self.flag("boss_char", self.new_char("paladin", "LabBosses"))

    def boss_golem(self):
        """hoh1floors s2: the Stone Guardian's ground spikes travel in a line along the floor
        and stop where a wall is (RayProjectile's wall hit or tiles harder than 4)."""
        if not self.boss_floor(FLOOR_MINES_BOSS, "boss_mines", "golem"):
            return
        # AreaTrigger on the circle (0,-240) r70 spawns the golem there 900 ms later
        self.gl("teleport", 0, -190)
        g = self.wait_units(700, "golem/golem_rock", names=("golem_rock.unit",), timeout=15)
        self.flag("golem_spawned", bool(g), f"{g[:1]}")
        if not g:
            return
        gx, gy = g[0]["x"], g[0]["y"]
        # the player steps between spots ~140 px from the golem (its range 200, keeps 150):
        # a spike aimed at the old spot runs on, and the fan's side spikes fly at 45 degrees
        spots = [(gx, gy + 140), (gx - 120, gy + 80), (gx + 120, gy + 80)]

        def dance(until):
            k = 0
            while time.time() < until - 0.5:
                sx, sy = spots[k % len(spots)]
                self.gl("teleport", sx, sy)
                k += 1
                time.sleep(1.4)

        ev = self.trail(14000, 800, "golem_groundspikes", 70, dance) or {}
        spikes = [u for u in ev.get("units") or [] if len(u.get("pts") or []) >= 3]
        plr = ev.get("plr") or []
        self.flag("golem_spikes_seen", bool(spikes), f"{len(spikes)} spikes tracked, truncated {ev.get('truncated')}")
        kinds, straight, notes = [], 0, []
        moved = [u for u in spikes[:16] if math.hypot(u["x1"] - u["x0"], u["y1"] - u["y0"]) >= 1]
        kinds += ["still"] * (len(spikes[:16]) - len(moved))
        dirs = []
        for u in moved:
            length = math.hypot(u["x1"] - u["x0"], u["y1"] - u["y0"])
            dirs.append(((u["x1"] - u["x0"]) / length, (u["y1"] - u["y0"]) / length))
        # one gl multi for all the rays (each gl command is a ~0.3 s round trip)
        rays = self.g.gl_multi([["rayhit", round(u["x0"], 1), round(u["y0"], 1), round(u["x0"] + dx * 700, 1),
                                 round(u["y0"] + dy * 700, 1)] for u, (dx, dy) in zip(moved, dirs)]) if moved else []
        for u, (dx, dy), ray in zip(moved, dirs, rays):
            x0, y0, x1, y1 = u["x0"], u["y0"], u["x1"], u["y1"]
            length = math.hypot(x1 - x0, y1 - y0)
            dev = max(abs((px - x0) * dy - (py - y0) * dx) for px, py, _ in u["pts"])
            if length >= 60 and dev <= 6:
                straight += 1
            stops = [ray[k] for k in ("wd", "td") if ray.get(k) is not None]
            stop = min(stops) if stops else None
            pp = min(plr, key=lambda q: abs(q[2] - u["t1"])) if plr else None
            at_plr = pp is not None and math.hypot(pp[0] - x1, pp[1] - y1) < 24
            if stop is not None and length > stop + 20:
                kind = "through"
            elif stop is not None and abs(length - stop) <= 20:
                kind = "wall"
            elif at_plr:
                kind = "player"
            else:
                kind = "ttl" if u["t1"] - u["t0"] >= 1800 else "short"
            kinds.append(kind)
            what = (ray.get("wname") or f"tile {ray.get('th')}") if stop is not None else "-"
            notes.append(f"{u['name'].split('/')[-1]} {int(length)}px {u['t1'] - u['t0']}ms dev {dev:.1f} "
                         f"stop {stop and int(stop)} ({what}) {kind}")
        self.notes.append("golem spikes: " + "; ".join(notes))
        self.flag("golem_spikes_travel", straight > 0, f"{straight} spikes ran >= 60 px in a line")
        self.flag("golem_spikes_stop_at_wall", "wall" in kinds and "through" not in kinds, f"{kinds}")

    def boss_warden(self):
        """hoh1floors s3: the Warden spins (HoH1WhirlwindSkill) and shoots; bombs: the whirlwind's
        bomb fan is %if !NORMAL in warden.inc, and the level spawns the NORMAL warden."""
        if not self.boss_floor(FLOOR_PRISON_BOSS, "boss_prison", "warden"):
            return
        # AreaTrigger 'ActivateBoss' (rect at (0,-152), 320x32) spawns the Warden at (0,-304)
        self.gl("teleport", 0, -150)
        w = self.wait_units(700, "bosses/warden/", names=WARDEN_UNITS, timeout=20)
        self.flag("warden_spawned", bool(w), f"{w[:1]}")
        if not w:
            return
        if self.ngp is not None:
            want = f"warden{tier_of(self.ngp)}.unit"
            self.flag("warden_tier", w[0].get("name", "").endswith("/" + want), f"{w[0].get('name')}, want {want} at NG+{self.ngp}")
        seen = {"casting": set(), "scenes": set()}
        spots = []

        def warden():
            a = [x for x in self.gl("actors", 800, "bosses/warden/").get("actors") or []
                 if x.get("name", "").split("/")[-1] in WARDEN_UNITS]
            if a:
                seen["casting"].update(a[0].get("casting") or [])
                seen["scenes"].add(a[0].get("scene", ""))
            return a[0] if a else None

        def watch(until):
            # 3 s in melee (whirlwind range 80), then 6 s standing still 160 px off in a clear
            # line of fire (ballista range 70-260, castpoint 400): a target that keeps moving
            # or a flip to melee mid-cast is what an arrow would otherwise end on
            while time.time() < until - 0.5:
                near_end = time.time() + 3
                while time.time() < min(near_end, until - 0.5):
                    a = warden()
                    if a:
                        self.gl("teleport", a["x"], a["y"] + 40)
                    time.sleep(0.2)
                a = warden()
                if not a or time.time() >= until - 1:
                    continue
                wx, wy = a["x"], a["y"]
                cands = [(wx, wy + 160), (wx - 160, wy), (wx + 160, wy), (wx, wy - 160)]
                # one gl multi for the four rays (each gl command is a ~0.3 s round trip)
                rays = self.g.gl_multi([["rayhit", round(wx, 1), round(wy, 1), round(cx, 1), round(cy, 1)] for cx, cy in cands])
                clear = [c for c, r in zip(cands, rays) if not r.get("wall")]
                spot = (clear or cands)[0]
                spots.append((int(spot[0] - wx), int(spot[1] - wy), bool(clear)))
                self.gl("teleport", spot[0], spot[1])
                # held at that offset: the NG+ copies' ballista is a burst skill, which restarts
                # its 4 s cooldown at every check out of range (70-260), and warden_t2 walks
                # the 160 px in under that (HoH1's CompositeActorBurstSkill does the same)
                off = (spot[0] - wx, spot[1] - wy)
                far_end = time.time() + 6
                while time.time() < min(far_end, until - 0.5):
                    a = warden()
                    if a and abs(math.hypot(a["x"] - spot[0], a["y"] - spot[1]) - 160) > 40:
                        spot = (a["x"] + off[0], a["y"] + off[1])
                        self.gl("teleport", spot[0], spot[1])
                    time.sleep(0.3)

        # step 120: 200 player points cover the 24 s (an arrow's first and last sight are per frame anyway)
        ev = self.trail(24000, 800, "bosses/warden/", 120, watch) or {}
        units = ev.get("units") or []
        plr = ev.get("plr") or []
        names = [u.get("name", "").split("/")[-1] for u in units]
        shots = [u for u in units if u.get("name", "").endswith("/arrow.unit")]
        # flown: seen at two positions (trail sees every frame, so even one that hits at once counts)
        arrows = [u for u in shots if math.hypot(u["x1"] - u["x0"], u["y1"] - u["y0"]) >= 2
                  or len({(x, y) for x, y, _ in u.get("pts") or []}) >= 2]
        detail = []
        for u in shots[:8]:
            pp = min(plr, key=lambda q: abs(q[2] - u["t1"])) if plr else None
            to_plr = int(math.hypot(pp[0] - u["x1"], pp[1] - u["y1"])) if pp else -1
            detail.append(f"{int(math.hypot(u['x1'] - u['x0'], u['y1'] - u['y0']))}px/{u['t1'] - u['t0']}ms end {to_plr}px from player")
        bombs = [n for n in names if "bomb" in n]
        whirl = any("Whirlwind" in c for c in seen["casting"]) or any("whirlwind" in s for s in seen["scenes"])
        self.flag("warden_whirlwind", whirl, f"casting {sorted(seen['casting'])}, scenes {sorted(seen['scenes'])[:12]}")
        self.flag("warden_shoots", bool(arrows), f"{len(arrows)}/{len(shots)} arrows flew: {detail}; far spots {spots}; "
                  f"units {sorted(set(names))}")
        self.flag("warden_bombs", bool(bombs), f"bomb units {bombs[:6]} ({len(bombs)}; warden.inc: the bomb fan is in the NG+ copies only)")

    def boss_councilors(self):
        """hoh1floors s4: the three Councilors (wraiths) appear together, move node to node
        (BossLichNode), can't be targeted while moving and attack inside the room."""
        if not self.boss_floor(FLOOR_ARMORY_BOSS, "boss_armory", "council"):
            return
        # the level's way in is the disabled Teleport 717, which runs ScriptLink 'ActivateBoss'
        # and puts the player at (0,-128)
        x = self.gl("wsexec", "ScriptLink", "ActivateBoss")
        self.gl("teleport", 0, -128)
        ws = self.wait_units(800, "bosses/wraith/wraith_", n=3, names=WRAITHS, timeout=30)
        self.flag("council_three", len(ws) == 3,
                  f"wsexec {x}; {[(u['name'].split('/')[-1], int(u['x']), int(u['y'])) for u in ws]}")
        if not ws:
            return
        nodes = self.gl("ws", "BossLichNode").get("scripts") or []
        node_pos = [(n["x"], n["y"]) for n in nodes] or LICH_NODES
        samples = []
        visits = {}

        # The scythe's attack (max-range 100, melee 35, period 1500-2250, castpoint 2200) holds it
        # still for 2.2 s each time it is near the player: at the room's middle, which 53 of the
        # level's 82 node-to-node legs pass within 100 px, it barely got past one node in 20 s
        # (plan-runs-c 124854), and parked next to a fixed spot it cast 71 of 74 samples
        # (142130). So 20 s at the middle (everyone attacks), then 25 s keeping the player more
        # than 100 px from the scythe (a room spot away from it, moving on whenever it closes
        # within 120), where the walks between nodes show.
        moves = []
        near_scythe = []

        def pick(a):
            sc = [(x["x"], x["y"]) for x in a if x["name"].endswith("wraith_scythe.unit")]
            far = [p for p in COUNCIL_SPOTS if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= 130 for q in sc)]
            if far:
                # of those, the one farthest from all three
                return max(far, key=lambda p: min([math.hypot(p[0] - x["x"], p[1] - x["y"]) for x in a] or [0]))
            return max(COUNCIL_SPOTS, key=lambda p: min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in sc))

        def wraiths():
            return [x for x in self.gl("actors", 900, "HoH1BossLich").get("actors") or []
                    if x.get("name", "").split("/")[-1] in WRAITHS]

        for phase, ms in (("middle", 20000), ("away", 25000)):
            spot = [(0, -144) if phase == "middle" else pick(wraiths())]

            def watch(until):
                last = 0
                while time.time() < until - 0.5:
                    a = wraiths()
                    samples.append(a)
                    if phase == "away":
                        d = [math.hypot(x["x"] - spot[0][0], x["y"] - spot[0][1]) for x in a
                             if x["name"].endswith("wraith_scythe.unit")]
                        near_scythe.extend(int(v) for v in d)
                        if d and min(d) < 120:
                            spot[0] = pick(a)
                            moves.append(spot[0])
                            last = 0
                    # stand still; put back every 2 s in case something pushed the player
                    if time.time() - last >= 2:
                        self.gl("teleport", *spot[0])
                        last = time.time()
                    time.sleep(0.3)

            ev = self.trail(ms, 900, "HoH1BossLich", 100, watch) or {}
            for u in ev.get("units") or []:
                name = u.get("name", "").split("/")[-1]
                if name not in WRAITHS:
                    continue
                hit = visits.setdefault(name, set())
                for px, py, _ in u.get("pts") or []:
                    for i, (nx, ny) in enumerate(node_pos):
                        if math.hypot(px - nx, py - ny) <= 16:
                            hit.add(i)
        visits = {k: sorted(v) for k, v in visits.items()}
        still = {w: f"{sum(1 for s in samples for a in s if a['name'].endswith(w) and not a.get('moving'))}/"
                    f"{sum(1 for s in samples for a in s if a['name'].endswith(w))}" for w in WRAITHS}
        alive3 = sum(1 for s in samples if len([a for a in s if not a.get("dead")]) == 3)
        moving = [a for s in samples for a in s if a.get("moving")]
        casters = {a["name"].split("/")[-1] for s in samples for a in s if a.get("casting")}
        self.flag("council_node_to_node", len(visits) == 3 and all(len(v) >= 2 for v in visits.values()),
                  f"nodes passed within 16 px over 45 s: {visits} ({len(node_pos)} nodes); samples standing still: {still}; "
                  f"player moved away from the scythe {len(moves)}x, scythe within 100 px in "
                  f"{sum(1 for v in near_scythe if v < 100)}/{len(near_scythe)} 'away' samples")
        self.flag("council_untargetable_moving", bool(moving) and not any(a.get("targetable") for a in moving),
                  f"{len(moving)} moving samples, targetable while moving {sum(1 for a in moving if a.get('targetable'))}")
        self.flag("council_fight_together", alive3 > 0 and len(casters) >= 2,
                  f"all three alive in {alive3}/{len(samples)} samples; casting: {sorted(casters)}")

    def boss_watcher(self):
        """hoh1floors s5: the Watcher's wisps circle (their angle keeps turning about the eye) at
        the player's distance from the eye (HoH1BossEyeWisp: clamped 30-160, eased)."""
        if not self.boss_floor(FLOOR_ARCHIVES_BOSS, "boss_archives", "watcher"):
            return
        # AllPlayersAreaTrigger (0,0) r160 enables UseTrigger 'StartBoss' at (0,0)
        self.gl("teleport", 0, 40)
        time.sleep(1.5)
        used = {}
        for _ in range(6):
            used = self.gl("usews", "StartBoss")
            if used.get("used"):
                break
            self.gl("teleport", 0, 10)
            time.sleep(1)
        eye = self.wait_units(700, "bosses/eye/eye", names=("eye.unit",), timeout=15)
        wisps = self.wait_units(700, "bosses/eye/wisp", n=2, timeout=15)
        self.flag("watcher_spawned", bool(eye) and len(wisps) >= 2, f"usews {used}; eye {eye[:1]}, {len(wisps)} wisps")
        if not eye:
            return

        def dance(until):
            t0 = time.time()
            while time.time() < until - 0.5:
                e = [u for u in self.gl("near", 800, "bosses/eye/eye").get("units") or [] if u["name"].endswith("/eye.unit")]
                if e:
                    # 6 s at 60 px from the eye, then 6 s at 150
                    far = (time.time() - t0) % 12 >= 6
                    self.gl("teleport", e[0]["x"], e[0]["y"] + (150 if far else 60))
                time.sleep(0.8)

        ev = self.trail(18000, 800, "HoH1BossEye", 100, dance) or {}
        units = ev.get("units") or []
        eyes = [u for u in units if u.get("name", "").endswith("/eye.unit")]
        ws = [u for u in units if "/wisp" in u.get("name", "")]
        if not eyes or not ws:
            self.flag("watcher_wisps_circle", False, f"trail units {[u.get('name') for u in units]}")
            return
        epts = {t: (x, y) for x, y, t in eyes[0]["pts"]}
        ppts = {t: (x, y) for x, y, t in ev.get("plr") or []}
        sweeps, monotone, follow = [], [], []
        for u in ws:
            ang, rad = [], []
            for x, y, t in u["pts"]:
                if t not in epts:
                    continue
                ex, ey = epts[t]
                rx, ry = x - ex, y - ey + 8  # the wisp's offset (0,-8)
                ang.append(math.atan2(ry, rx))
                pd = math.hypot(ppts[t][0] - ex, ppts[t][1] - ey) if t in ppts else None
                rad.append((math.hypot(rx, ry), pd))
            steps = [(b - a + math.pi) % (2 * math.pi) - math.pi for a, b in zip(ang, ang[1:])]
            total = sum(steps)
            sweeps.append(round(abs(total), 2))
            same = sum(1 for d in steps if d * total > 0)
            monotone.append(round(same / len(steps), 2) if steps else 0)
            follow.append([(int(r), int(p)) for r, p in rad[::10] if p is not None])
        self.notes.append(f"watcher wisp radius vs player distance (every 1 s): {follow[:3]}")
        self.flag("watcher_wisps_circle", any(s >= math.pi and m >= 0.8 for s, m in zip(sweeps, monotone)),
                  f"{len(ws)} wisps: angle swept {sweeps} rad, same-direction steps {monotone}")
        # the radius eases toward the player's distance (clamped 30-160): farther out while the
        # player stands farther off
        good = 0
        for f in follow:
            near = [r for r, p in f if p < 100]
            far = [r for r, p in f if p >= 100]
            if near and far and sum(far) / len(far) - sum(near) / len(near) > 30:
                good += 1
        self.flag("watcher_wisps_at_player_distance", good > 0, f"{good}/{len(follow)} wisps farther out while the player is")

    def boss_vampire(self):
        """hoh1floors s6: the Vampire Lord flies node to node as a bat swarm (scene bat-N,
        untargetable, a moving body) and stands in his own scenes between; roaming he flies
        on without stopping and drops fire_area.unit every 50 ms along his path. The bat spray
        (an arc of bat_projectile_spawn) is recorded only: vampire.unit sets its charges to
        BATCHARGES 0 (as HoH1's own vampire.unit does), so the skill never starts; it would
        also need NG+2 and the boss under 20% health."""
        if not self.boss_floor(FLOOR_CHAMBERS_BOSS, "boss_chambers", "vampire"):
            return
        # Setup (100 ms after load) finds no vampire_cross flags and enables AreaTrigger
        # 'ActivateBoss' on the circle (-16,-170) r64: the boss spawns at (-16,-168) 1 s later
        self.gl("teleport", -16, -150)
        v = self.wait_units(700, "bosses/vampire/", names=VAMPIRE_UNITS, timeout=15)
        self.flag("vampire_spawned", bool(v), f"{v[:1]}")
        if not v:
            return
        vname = v[0].get("name", "")
        if self.ngp is not None:
            want = f"vampire{tier_of(self.ngp)}.unit"
            self.flag("vampire_tier", vname.endswith("/" + want), f"{vname}, want {want} at NG+{self.ngp}")
        # the Bat Spray (vampire_skills.inc) needs NG+2, charges (BATCHARGES: 0 in vampire.unit,
        # 1 in vampire_t2) and the boss under 20% health, and fires within 120 px: on NG+2 the
        # health goes to 12% (a feed heals 5-10%) and the player keeps to him while he stands
        spray = (self.ngp or 0) >= 2
        # Roaming needs flag vampire_roaming, which the level sets when a feed (at the center
        # node, every 5th hop) ends with the boss under half health (CheckFeed -> CheckActorHealth
        # < 0.5 -> SetFlag 'vampire_roaming', FlagState Level). Health to 35% (a feed heals 5-10%)
        # and the flag set now the same way, so the next node arrivals may start a roam (40%).
        hurt = self.gl("kill", 900, vname.split("/")[-1], 0.12 if spray else 0.35)
        self.g.console("cht_set_flag vampire_roaming 1 0")
        spot = (-16, 112)  # south side of the hall, between the nodes (-96,80) and (64,80)
        self.gl("teleport", *spot)
        samples, fires, bats = [], {}, {}
        swarm = [0]

        def watch(until):
            last = 0
            while time.time() < until - 0.8:
                r = self.g.gl_multi([["actors", 900, "HoH1BossVampire"], ["near", 900, "fire_area"],
                                     ["near", 900, "bat_projectile_spawn"], ["near", 900, "summon_bat_swarm"]])
                now = [a for a in r[0].get("actors") or [] if a.get("name", "").split("/")[-1] in VAMPIRE_UNITS]
                samples.extend(now)
                for u in r[1].get("units") or []:
                    fires.setdefault(u["unit"], (u["x"], u["y"]))
                for u in r[2].get("units") or []:
                    bats.setdefault(u["unit"], (u["x"], u["y"]))
                swarm[0] += len(r[3].get("units") or [])
                if spray and now and not now[0].get("moving"):
                    self.gl("teleport", now[0]["x"], now[0]["y"] + 60)
                elif time.time() - last >= 3:
                    self.gl("teleport", *spot)
                    last = time.time()
                time.sleep(0.4)

        ev = self.trail(48000, 900, "HoH1BossVampire", 240, watch) or {}
        track = [(x, y) for u in ev.get("units") or [] if u.get("name", "").split("/")[-1] in VAMPIRE_UNITS
                 for x, y, _ in u.get("pts") or []]
        nodes = self.gl("ws", "BossLichNode").get("scripts") or []
        node_pos = [(n["x"], n["y"]) for n in nodes] + [VAMPIRE_NODES[-1]] if nodes else VAMPIRE_NODES
        hit = sorted({i for x, y in track for i, (nx, ny) in enumerate(node_pos) if math.hypot(x - nx, y - ny) <= 16})
        path = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(track, track[1:]))
        self.flag("vampire_roams", len(hit) >= 3,
                  f"hurt {hurt.get('hurt')}; nodes passed within 16 px over 48 s: {hit} of {len(node_pos)}, "
                  f"{len(track)} track points, path {int(path)} px")
        bat = [a for a in samples if a.get("scene", "").startswith("bat")]
        stand = [a for a in samples if not a.get("moving")]
        stand_scenes = sorted({a.get("scene", "").split("-")[0] for a in stand})
        self.flag("vampire_transforms", bool(bat) and bool(stand)
                  and all(a.get("moving") and not a.get("targetable") for a in bat)
                  and not any(a.get("scene", "").startswith("bat") for a in stand),
                  f"{len(samples)} samples: {len(bat)} as bats (moving {sum(1 for a in bat if a.get('moving'))}, "
                  f"targetable {sum(1 for a in bat if a.get('targetable'))}), {len(stand)} standing in {stand_scenes}")
        segs = list(zip(track, track[1:]))
        on = [f for f in fires.values() if segs and min(seg_dist(f, a, b) for a, b in segs) <= 24]
        xs, ys = [f[0] for f in fires.values()], [f[1] for f in fires.values()]
        span = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) if fires else 0
        self.flag("vampire_fire_trail", len(fires) >= 10 and len(on) >= 0.8 * len(fires) and span >= 64,
                  f"{len(fires)} fire areas, {len(on)} within 24 px of his path, spread {int(span)} px")
        feeds = sum(1 for a in samples if a.get("scene") == "feeding")
        self.flag("vampire_feeds", feeds > 0 or swarm[0] > 0,
                  f"{feeds} samples feeding, summon_bat_swarm seen {swarm[0]} times")
        note = f"{len(bats)} bat_projectile_spawn seen"
        if len(bats) >= 3 and track:
            vx, vy = track[-1]
            ang = sorted(math.degrees(math.atan2(y - vy, x - vx)) for x, y in bats.values())
            note += f", angles {[int(a) for a in ang]}"
        self.flag("vampire_bats", bool(bats), note + f" at NG+{self.ngp or 0} (charges BATCHARGES 0 in vampire.unit, 1+ in the NG+ copies)")

    def wait_level(self, part, timeout=90):
        """Until the state's level path has part and the phase is mission (gl may not answer
        while the level loads)."""
        end = time.time() + timeout
        while time.time() < end:
            try:
                st = self.gl("state")
                if part in (st.get("level") or "") and st.get("phase") == "mission":
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def enemies(self, tag, want=None):
        """The floor's live actors (gl actors lists 32 at most) by .unit file; with want, a
        {tag}_{want} flag for whether that unit file is among them."""
        a = [x for x in self.gl("actors", 8000).get("actors") or [] if not x.get("dead")]
        kinds = {}
        for x in a:
            k = x.get("name", "").split("/")[-1]
            kinds[k] = kinds.get(k, 0) + 1
        self.flag(f"{tag}_enemies", len(a) >= 3, f"{len(a)} live actors: {kinds}")
        if want:
            self.flag(f"{tag}_{want}", kinds.get(want + ".unit", 0) > 0, f"{kinds.get(want + '.unit', 0)} {want}")

    def take_exit(self, level, nxt, tag):
        """Stand in the exit's UseTrigger area (its AllPlayersAreaTrigger enables the exit) and
        press use; the next floor must load. hwp finishlevel only if no exit worked."""
        for x, y in BATTLEMENTS_EXITS[level]:
            # 4 px into the area's lower half: the exit_up doodad's collision ends at its top edge
            self.gl("teleport", x, y + 4)
            time.sleep(1.2)
            self.gl("input", 300, 0, 0, 0, 0, "use")
            if self.wait_level(nxt, 25):
                self.flag(f"{tag}_exit", True, f"exit at {x},{y}")
                return True
        self.flag(f"{tag}_exit", False, f"no exit of {BATTLEMENTS_EXITS[level]} loaded {nxt}: hwp finishlevel")
        self.next_floor()
        return self.wait_level(nxt, 30)

    def battlements(self):
        """hoh1floors s7: Battlements 1 and 2 (hand-made HoH1 levels, not generated) load with
        enemies and are left through their exits (stand on the exit, press use: battlements_1
        -> battlements_2 -> boss_dragon); on top Thundersnow waits: dragon_intro.unit stands in
        the level, and entering the circle (0,0) r120 ('EnableBoss') spawns dragon.unit."""
        if not self.boss_floor(FLOOR_BATTLEMENTS_1, "battlements_1", "battlements1"):
            return
        # its enemies are the SpawnEnemyGroup points' ice troll groups (HoH1's EnemyPlacement)
        self.enemies("battlements1", "ice_troll_melee")
        if not self.take_exit("battlements_1", "battlements_2", "battlements1"):
            self.flag("battlements2_floor", False, f"level {self.gl('state').get('level')}")
            return
        time.sleep(3)
        self.god_on()
        self.flag("battlements2_floor", True, self.gl("state").get("level", ""))
        self.enemies("battlements2")
        if not self.take_exit("battlements_2", "boss_dragon", "battlements2"):
            self.flag("dragon_floor", False, f"level {self.gl('state').get('level')}")
            return
        time.sleep(3)
        self.god_on()
        st = self.gl("state")
        self.flag("dragon_floor", True, f"level {st.get('level')}, floor {st.get('floor')}")
        intro = self.gl("near", 1200, "dragon_intro").get("units") or []
        self.gl("teleport", 0, 100)
        d = self.wait_units(900, "bosses/dragon/dragon", names=("dragon.unit",), timeout=15)
        self.flag("thundersnow_present", bool(intro) and bool(d), f"dragon_intro {intro[:1]}; dragon {d[:1]}")
        self.gl("teleport", 0, 300)  # back from the boss for the shot
        time.sleep(1.5)


def run(p, sections="keys_padlock", ngp=None, **_):
    c = Checks(p)
    c.ngp = ngp
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
