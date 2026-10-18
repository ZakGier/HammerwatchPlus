"""Test-plan checks for the runs group: locked reward chests with padlocks (keys s3), the
Architect row of the run-start loadout (architect s1), the town portal's minimap pip
(campaign s1) and the four HoH1 boss floors of The Forsaken Tower (hoh1floors s2-s5).

The bosses are measured in-engine by `gl trail` (Verbs_runs.as): every frame it follows the
boss's units and projectiles, so a ground spike that lives for two seconds is seen from its
first frame to its last; `gl rayhit` gives where a projectile from a point would stop (the
first Shot raycast hit that is no damage taker, or tiles harder than destroy-at-hardness),
`gl actors` what a boss is casting and whether it can be targeted.

Sections: keys_padlock, architect_loadout, portal_minimap, boss_setup, boss_golem,
boss_warden, boss_councilors, boss_watcher."""
import json
import math
import re
import time

from gamelab.bots.plan_checks import Checks as Base

HOH1 = "hwp_forsaken_tower_hoh1"
# 0-based floors of missions_hwp_forsaken_tower_hoh1.sval
FLOOR_MINES_BOSS, FLOOR_PRISON_BOSS, FLOOR_ARMORY_BOSS, FLOOR_ARCHIVES_BOSS = 2, 5, 8, 11
# boss_armory.lvl's BossLichNode positions (the wraiths walk node to node)
LICH_NODES = [(0, -352), (128, 16), (-272, -112), (-96, -336), (224, -192), (-128, 16), (-160, -272),
              (272, 0), (160, -272), (0, 16), (-224, -192), (96, -336), (272, -112), (-272, 0)]
WRAITHS = ("wraith_staff.unit", "wraith_scythe.unit", "wraith_mage.unit")
TIERS = {"bronze": 0, "silver": 1, "gold": 2, "platinum": 2}


def arch_mul(n_buffs, arch_lvl):
    """CalcArchitectCostMul (scripts/Missions/MissionArchitect.as), no debuffs."""
    n = max(1, n_buffs)
    if arch_lvl >= 1:
        return (n ** 1.6 - 1) / 7.0 + 1.0
    return (n ** 1.8 - 1) / 6.0 + 1.0


def has_num(text, n):
    return re.search(r"(?<!\d)%d(?!\d)" % n, text or "") is not None


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
        return self.g.wait_gl(lambda o: o.get("ev") == "trail" and o.get("tag") == tag, ms / 1000 + 15)

    def boss_floor(self, floor, level, tag):
        r = self.gl("mission", HOH1, floor)
        ok = bool(r.get("ok")) and self.wait_phase("mission", 120)
        time.sleep(3)
        lv = self.gl("state").get("level", "")
        ok = ok and level in lv
        self.flag(f"{tag}_floor", ok, f"mission {r.get('ok')}, level {lv}")
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
        """campaign s1 (the minimap pip; the portal's text is section portal): the portal is in
        town, the HUD minimap on (ui_minimap 1) and the player 70 px south of it, for the shot."""
        town = self.new_char("paladin", "LabPortal")
        self.flag("pip_town", town, "the new character is in town" if town else "the new character is not in town")
        if not town:
            return
        p = self.gl("near", 8000, "forsaken_portal").get("units") or []
        self.flag("pip_portal_in_town", bool(p), f"{p[:1]}")
        if not p:
            return
        self.gl("teleport", p[0]["x"], p[0]["y"] + 70)
        time.sleep(1)
        self.g.console("ui_minimap 1")
        time.sleep(1)
        cv = self.gl("cvars", "ui_minimap").get("cvars", {})
        self.flag("pip_minimap_on", bool(cv.get("ui_minimap")), f"{cv}; portal at {p[0]['x']},{p[0]['y']}")

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
        w = self.wait_units(700, "bosses/warden/warden", names=("warden.unit",), timeout=20)
        self.flag("warden_spawned", bool(w), f"{w[:1]}")
        if not w:
            return
        seen = {"casting": set(), "scenes": set()}
        spots = []

        def warden():
            a = [x for x in self.gl("actors", 800, "bosses/warden/warden").get("actors") or []
                 if x.get("name", "").endswith("warden.unit")]
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
                far_end = time.time() + 6
                while time.time() < min(far_end, until - 0.5):
                    warden()
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
        self.flag("warden_bombs", bool(bombs), f"bomb units {bombs} (warden.inc: the bomb fan is NG only)")

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
        # (plan-runs-c 124854). So 20 s at the middle (everyone attacks), then 20 s at
        # (-120,-40), still in the room, near 29 legs, where the walks between nodes show.
        for spot in ((0, -144), (-120, -40)):
            def watch(until, spot=spot):
                last = 0
                while time.time() < until - 0.5:
                    a = [x for x in self.gl("actors", 900, "HoH1BossLich").get("actors") or []
                         if x.get("name", "").split("/")[-1] in WRAITHS]
                    samples.append(a)
                    # stand still; put back every 2 s in case something pushed the player
                    if time.time() - last >= 2:
                        self.gl("teleport", *spot)
                        last = time.time()
                    time.sleep(0.3)

            ev = self.trail(20000, 900, "HoH1BossLich", 100, watch) or {}
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
                  f"nodes passed within 16 px over 40 s: {visits} ({len(node_pos)} nodes); samples standing still: {still}")
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


def run(p, sections="keys_padlock", **_):
    c = Checks(p)
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
