"""Test-plan checks for the Firearms Specialist (mods/firearms): firearms s3 (the Frag Grenade
lands where aimed and explodes with damage numbers), s4 (`hwp levelup 20`, the Subclass
Picker offers three doctrines; each doctrine skill casts and costs what its tooltip says) and
s5 (Decoy pulls enemies onto the dummy and is gone after 8 s; Jetpack lands at the cursor with
a fire burst). s2 (ammo) is plan_checks.firearms_ammo. Same style as plan_checks: each section
flags booleans, the scenario's expect asserts them, measured values go in the notes.

Targeted skills (frag, flashbang, stun grenade, jetpack: TargetingMode::TargetAOE) are cast
the way a player casts them: the skill button opens the targeting circle and the main-hand
click casts at the cursor (PlayerTargetingHelper.Update; with g_quickcast on, the button's
release). A posted mouse never reaches the game (RE_NOTES 2026-10-18), so `gl cursor dx dy`
(Verbs_firearms.as) writes GameInput.MousePos and reads it back; whatever the cursor reads at
the click is where the cast is expected to land (CalcMouseTargetPos: its direction, the
distance clamped to the skill's range).

Only three skill buttons exist: GetSkillInput (PlayerTargetingHelper.as:744-749) gives the
third and every later active spell Skill3, and reload and frag already hold Skill1 and
Skill2. A doctrine's skills are levelled in reverse class order, so the newest one is the
first Skill3 skill in m_skills and the one a press casts. `<spec>_own_buttons` reports whether
the finished doctrine has a button per active skill (`gl skillbar`).

Mana is read unrounded from `gl skillbar` (m_record.mana x max, = state manaExact). A costed
cast starts from a full magazine (topped up with Reload), so regeneration only runs after the
cost is taken: the fall between the last full reading and the next is the cost less at most
the regen over that gap (the rate measured from the rise after). Expected = tooltip x the
state's manaCostMul. Direction presses are held past the skill's castpoint.

Sections: firearms_frag (s3), firearms_spec_pick, firearms_sniper (s4 + the s5 decoy),
firearms_demo (s4 + the s5 jetpack), firearms_assault (s4)."""
import math
import re
import time
from pathlib import Path

from gamelab.bots.plan_checks import Checks as Base

MOD = Path(__file__).resolve().parents[2] / "mods" / "firearms"
SKILLS = MOD / "players" / "hwp" / "firearms" / "skills"
LANG = MOD / "res" / "language" / "english" / "hwp_firearms.lang"
DUMMY = "doodads/generic/target_dummy_breakable.unit"  # 500 hp, stands still, enemy team
BRUTE = "actors/humans/bandits/bandit_brute.unit"
PICKER = "actors/npcs/town/npc_subclass_picker.unit"
DECOY = "units/decoy"
DMG_TEXTS = {7, 8, 9, 11}  # FloatingTextType EnemyHurt, EnemyHurtLocal, EnemyHurtHusk, EnemyImmortal (a crit)
TOL = 0.4  # mana units

# subclass -> its skills in class order: (id, sval, tag, targeted range or None)
SPECS = {
    "hwp_firearms_sniper": [("hwp_fs_snipe", "sniper_snipe.sval", "snipe", None),
                            ("hwp_fs_flashbang", "sniper_flashbang.sval", "flashbang", (16, 170)),
                            ("hwp_fs_decoy", "sniper_decoy.sval", "decoy", None)],
    "hwp_firearms_demolitions": [("hwp_fs_tube", "demo_tube.sval", "tube", None),
                                 ("hwp_fs_rpg", "demo_rpg.sval", "rpg", None),
                                 ("hwp_fs_jetpack", "demo_jetpack.sval", "jetpack", (40, 190))],
    "hwp_firearms_assault": [("hwp_fs_burst", "assault_burst.sval", "burst", None),
                             ("hwp_fs_stun", "assault_stun.sval", "stun", (16, 170)),
                             ("hwp_fs_adrenaline", "assault_adrenaline.sval", "adrenaline", None)],
}


def tooltip_cost(sval, level=1):
    """The mana cost the skill's tooltip shows (its "mana-cost" description param at that
    level; a tooltip without one shows no cost: 0)."""
    m = re.search(r"<array><s>mana-cost</s>(.*?)</array>", (SKILLS / sval).read_text(encoding="utf-8"))
    if not m:
        return 0
    vals = re.findall(r"<s>([^<]*)</s>", m.group(1))[1:]  # the first is the label string
    return int(vals[min(level, len(vals)) - 1])


def sval_cost(sval):
    """The level-1 mana-cost the skill's own data sets (the skill dict's first mana-cost)."""
    m = re.search(r'<int name="mana-cost">(\d+)</int>', (SKILLS / sval).read_text(encoding="utf-8"))
    return int(m.group(1)) if m else 0


def castpoint(sval):
    """The skill's castpoint (ms): a press is held past it (and its update-aim window), or the
    aim goes back to the real mouse when the emulated input lets go (lessons from live runs)."""
    m = re.search(r'<int name="castpoint">(\d+)</int>', (SKILLS / sval).read_text(encoding="utf-8"))
    return int(m.group(1)) if m else 0


def hold(sval):
    return castpoint(sval) + 120


def spec_names():
    text = LANG.read_text(encoding="utf-8")
    return [re.search(rf'name="skills.hwp_firearms.mastery_{i}.name">([^<]*)<', text).group(1) for i in (1, 2, 3)]


def unit(dx, dy):
    n = math.hypot(dx, dy) or 1.0
    return round(dx / n, 3), round(dy / n, 3)


class Checks(Base):
    # --- plumbing
    def god_on(self):
        if not self.gl("cvars", "cht_god").get("cvars", {}).get("cht_god"):
            self.hwp("god", 0.5, until="god mode")

    def pos(self):
        pl = self.gl("state").get("player", {})
        return pl.get("x", 0.0), pl.get("y", 0.0)

    def bar(self):
        return self.gl("skillbar")

    @staticmethod
    def entry(bar, sid):
        return next((s for s in bar.get("skills", []) if s.get("id") == sid), {})

    def open_dirs(self, dist=130):
        """Unit vectors (of 8) along which the pathfinder walks about straight to dist away:
        open floor for a dummy, a throw or a leap. Answered ones first, then the 0-node replies
        (a straight line or no path)."""
        px, py = self.pos()
        good, maybe = [], []
        for ang in range(0, 360, 45):
            ux, uy = round(math.cos(math.radians(ang)), 3), round(math.sin(math.radians(ang)), 3)
            pf = self.gl("pathfind", round(px + ux * dist, 1), round(py + uy * dist, 1))
            n = pf.get("nodes", -1)
            if pf.get("ok") and n > 0 and pf.get("length", 1e9) <= dist * 1.25:
                good.append((ux, uy))
            elif pf.get("ok") and n == 0:
                maybe.append((ux, uy))
        dirs = good + maybe
        self.notes.append(f"open directions from {round(px)},{round(py)}: {len(good)} answered, {len(maybe)} 0-node")
        return dirs or [(1.0, 0.0)]

    def enter_floor(self, tag):
        if not self.start_floor(0):
            self.flag(f"{tag}_mission", False)
            return False
        self.god_on()
        self.gl("kill", 6000, "tag:enemy")  # an empty floor: nothing hits the player or blocks a cast
        time.sleep(1)
        self.quickcast = bool(self.gl("cvars", "g_quickcast").get("cvars", {}).get("g_quickcast"))
        return True

    def new_char(self, name, sub=None):
        """A fresh gunner at level 21 (`hwp levelup 20`), in town, with points for every
        doctrine skill; with `sub` the doctrine is picked (gl subclass = the picker's switch)."""
        self.gl("char", "hwp_firearms", name)
        self.wait_phase("town", 60)
        time.sleep(2)
        lv = self.hwp("levelup 20", 1.0, until="now level")
        sc = self.gl("subclass", sub) if sub else {}
        self.hwp("skillpoints 40", 0.6, until="skill points")
        self.base_skills()
        pl = self.gl("state").get("player", {})
        self.notes.append(f"{name}: {' '.join(re.findall(r'now level \d+', lv))[-20:]}, class {pl.get('class')}")
        return sc, pl

    def base_skills(self):
        """Reload and Frag learned (the buttons count only skills with a level: without them
        the doctrine skills would move up to Skill1/Skill2)."""
        have = {x.get("id") for x in self.bar().get("skills", [])}
        missing = [sid for sid in ("hwp_fs_reload", "hwp_fs_frag") if sid not in have]
        if missing:
            self.hwp("skillpoints 10", 0.6, until="skill points")
            for sid in missing:
                self.gl("skill", sid, 1)
            time.sleep(0.6)
        self.notes.append(f"base skills learned by the bot: {missing}")

    def dummy(self, dx, dy):
        r = self.gl("spawn", DUMMY, round(dx, 1), round(dy, 1))
        time.sleep(0.3)
        return r.get("unit")

    def hps(self, ids, r=600):
        """unit id -> hp fraction (0 for a dead or vanished one)."""
        live = {u["unit"]: (0.0 if u.get("dead") else u.get("hp", 1.0))
                for u in self.gl("near", r, "target_dummy").get("units") or []}
        return {i: live.get(i, 0.0) for i in ids}

    def clear_dummies(self):
        self.gl("kill", 800, "target_dummy")
        time.sleep(0.3)

    def damage_texts(self, secs):
        """Damage numbers seen over `secs` (polled: a floating text lives 500 ms, a line ~0.3 s).
        Deduped by (text, x): a text's x is fixed once made, its y rises."""
        seen = {}
        end = time.time() + secs
        while time.time() < end:
            for t in self.gl("floats").get("texts") or []:
                if t.get("type") in DMG_TEXTS:
                    seen.setdefault((t.get("text"), round(t.get("x", 0.0))), t)
            time.sleep(0.05)
        return list(seen.values())

    def top_up(self):
        """Fill the magazine with Reload (Skill1, 50 %, 2 s cooldown) so the next cost is measured
        from a full one."""
        for _ in range(4):
            b = self.bar()
            if b.get("mana", 0) >= b.get("manaMax", 1) - 0.01:
                return True
            self.gl("input", 60, 0, 0, 1, 0, "skill1")
            time.sleep(2.3)
        b = self.bar()
        return b.get("mana", 0) >= b.get("manaMax", 1) - 0.01

    def cursor_on(self, dx, dy, rng):
        """Write the cursor onto player + (dx, dy) and read it back: (the offset a cast at it uses,
        whether the write held, the raw read)."""
        self.gl("cursor", round(dx, 1), round(dy, 1))
        c = self.gl("cursor")
        cx, cy = c.get("dx", 0.0), c.get("dy", 0.0)
        held = abs(cx - dx) < 4 and abs(cy - dy) < 4
        d = math.hypot(cx, cy) or 1.0
        k = min(rng[1], max(rng[0], d)) / d
        return (cx * k, cy * k), held, c

    def targeted(self, button, dx, dy, rng):
        """A TargetAOE cast at player + (dx, dy) as a player makes it: the cursor there, the
        button (the targeting circle opens), then the main-hand click; with g_quickcast the
        button's release casts. Returns the offset the cursor gave at the click, and whether
        the cursor write held throughout."""
        (tx, ty), held, _ = self.cursor_on(dx, dy, rng)
        ax, ay = unit(tx, ty)
        self.gl("input", 60, 0, 0, ax, ay, button)
        time.sleep(0.35)
        if not self.quickcast:
            (tx, ty), held2, _ = self.cursor_on(dx, dy, rng)  # again, just before the click
            held = held and held2
            self.gl("input", 60, 0, 0, ax, ay, "main")
        return (tx, ty), held

    def cast_watch(self, sid, cast, secs=1.6):
        """Run cast() and watch the skill bar for secs: mana before, the lowest after, this
        skill's cooldown, and any other skill that went on cooldown with it."""
        b0 = self.bar()
        cd0 = {s["id"]: s.get("cd", 0) for s in b0.get("skills", [])}
        m0, t0 = b0.get("mana", 0.0), time.time()
        cast()
        low, cd, others = m0, 0.0, set()
        samples = [(t0, m0)]
        end = time.time() + secs
        while time.time() < end:
            b = self.bar()
            samples.append((time.time(), b.get("mana", m0)))
            low = min(low, b.get("mana", m0))
            for s in b.get("skills", []):
                if s.get("cd", 0) > 0 and cd0.get(s["id"], 0) == 0:
                    if s["id"] == sid:
                        cd = max(cd, s["cd"])
                    else:
                        others.add(s["id"])
            time.sleep(0.05)
        # the fall: the first reading below the start, the gap from the reading before it; the
        # regen rate from the rise after the lowest reading (while below the maximum)
        i = next((k for k, (_, m) in enumerate(samples) if m < m0 - 0.05), None)
        gap = samples[i][0] - samples[i - 1][0] if i else 0.0
        top = b0.get("manaMax", 0) - 0.05
        k = min(range(len(samples)), key=lambda j: samples[j][1])
        rise = [(t, m) for t, m in samples[k:] if m < top]
        rate = (rise[-1][1] - rise[0][1]) / (rise[-1][0] - rise[0][0]) if len(rise) > 1 and rise[-1][0] > rise[0][0] else 0.0
        fall = m0 - samples[i][1] if i else 0.0
        return {"m0": round(m0, 2), "low": round(low, 2), "drop": round(fall, 2), "gap": round(gap, 2),
                "rate": round(max(rate, 0.0), 2), "cd": round(cd, 3), "others": sorted(others)}

    def cost_flag(self, tag, sid, sval, w):
        tip, data = tooltip_cost(sval), sval_cost(sval)
        live = self.entry(self.bar(), sid).get("mana")
        mul = self.gl("state").get("player", {}).get("manaCostMul", 1.0) or 1.0
        want = tip * mul
        # the cost lies between the fall and the fall + the regen over the gap it was seen in
        lo, hi = w["drop"] - TOL, w["drop"] + w["rate"] * w["gap"] + TOL
        self.flag(f"{tag}_cost", lo <= want <= hi and tip == data == live,
                  f"mana {w['m0']} -> {w['low']} (fall {w['drop']} over {w['gap']} s, regen {w['rate']}/s), "
                  f"tooltip {tip} x cost mul {mul}, sval {data}, GetCost {live}")

    def level(self, tag, sid):
        r = self.gl("skill", sid, 1)
        time.sleep(0.6)  # SkillUp reloads the skills (LoadSkills)
        ok = r.get("level", 0) >= 1
        if not ok:
            self.flag(f"{tag}_learned", False, str(r))
        return ok

    def buttons_flag(self, spec):
        b = self.bar()
        act = [(s["id"], s.get("button")) for s in b.get("skills", []) if s.get("type") == 4 and s.get("mode", 0) != 0]
        btns = [x[1] for x in act]
        self.flag(f"{spec}_own_buttons", len(btns) == len(set(btns)),
                  f"active spells {act} (only skill1-3 exist: GetSkillInput gives the 3rd and later Skill3)")

    # --- direction skills: a dummy in the line of fire
    def direction_test(self, tag, sid, sval, d, dist=80):
        """A Direction skill (snipe, tube, rpg, burst) fired at a dummy `dist` along d: it casts
        (its cooldown starts, the dummy loses HP) and costs the tooltip's mana."""
        self.clear_dummies()
        du = self.dummy(d[0] * dist, d[1] * dist)
        if tooltip_cost(sval):
            self.top_up()
        hp0 = self.hps([du])
        w = self.cast_watch(sid, lambda: self.gl("input", hold(sval), 0, 0, d[0], d[1], "skill3"))
        time.sleep(0.3)
        hp1 = self.hps([du])
        hit = hp1[du] < hp0[du] - 0.001
        self.flag(f"{tag}_casts", w["cd"] > 0 and hit,
                  f"cooldown {w['cd']}, dummy hp {hp0[du]} -> {hp1[du]}, also cooled {w['others']}")
        self.cost_flag(tag, sid, sval, w)
        return w

    # --- sections
    def firearms_frag(self):
        """firearms s3: Frag Grenade (Skill2, 16-170 range, 56 radius) thrown at two spots 110
        out, one dummy at each: the aimed one loses HP, the other doesn't, and the damage number
        floats over the hit one."""
        self.gl("char", "hwp_firearms", "LabFrag")
        self.wait_phase("town", 60)
        time.sleep(2)
        self.base_skills()
        if not self.enter_floor("frag"):
            return
        dirs = self.open_dirs(110)
        a = dirs[0]
        b = next((v for v in dirs[1:] if v[0] * a[0] + v[1] * a[1] < 0.1), (-a[1], a[0]))  # >= 84 deg: the spots 150 apart, the blast 56
        rng = (16, 170)
        spots = [(a[0] * 110, a[1] * 110), (b[0] * 110, b[1] * 110)]
        eff = []
        for sx, sy in spots:  # the cursor decides where a throw lands: the dummies go where it reads
            e, held, c = self.cursor_on(sx, sy, rng)
            eff.append((e, held, c))
        units = [self.dummy(e[0][0], e[0][1]) for e in eff]
        self.notes.append(f"frag spots asked {[(round(x), round(y)) for x, y in spots]}, cursor gave "
                          f"{[(round(e[0][0]), round(e[0][1]), e[1]) for e in eff]}, gamepad {eff[0][2].get('gamepad')}, "
                          f"quickcast {self.quickcast}")
        self.flag("frag_cursor_held", all(e[1] for e in eff), "gl cursor wrote GameInput.MousePos and read it back")
        results, texts_all, casts = [], [], []
        for i, (e, _, _) in enumerate(eff):
            hp0 = self.hps(units)
            self.targeted("skill2", e[0], e[1], rng)
            texts = self.damage_texts(1.6)  # at once: it lands ~0.5 s after the click, its number lives 0.5 s
            cd = self.entry(self.bar(), "hwp_fs_frag").get("cd", 0)
            hp1 = self.hps(units)
            casts.append(cd > 0 or hp1 != hp0)
            hit = [u for u in units if hp1[u] < hp0[u] - 0.001]
            px, py = self.pos()
            results.append((units[i] in hit, [u for u in hit if u != units[i]], hp0, hp1))
            # a damage number over the aimed dummy: x within a few px (made at the unit, +-3 random)
            target_x = px + e[0]
            near_texts = [t for t in texts if abs(t.get("x", 0) - target_x) <= 12]
            texts_all.append((near_texts, texts))
            self.notes.append(f"throw {i + 1} at {round(e[0])},{round(e[1])}: hit {hit}, hp {hp0} -> {hp1}, "
                              f"damage texts {[(t.get('text'), round(t.get('x', 0)), t.get('type')) for t in texts]}, "
                              f"cooldown {cd}")
            if i == 0:
                time.sleep(4.2)  # the 4 s cooldown
        self.flag("frag_thrown", all(casts), f"{casts}")
        self.flag("frag_explodes", any(r[0] for r in results), f"aimed dummy hit per throw {[r[0] for r in results]}")
        self.flag("frag_lands_where_aimed", all(r[0] and not r[1] for r in results),
                  f"per throw: aimed hit {[r[0] for r in results]}, others hit {[r[1] for r in results]}")
        self.flag("frag_damage_numbers", all(n for n, _ in texts_all) and
                  all(int(re.sub(r'\D', '', t.get('text', '0')) or 0) > 0 for n, _ in texts_all for t in n),
                  f"numbers over the aimed dummy {[[t.get('text') for t in n] for n, _ in texts_all]}")
        self.clear_dummies()
        self.to_town()

    def firearms_spec_pick(self):
        """firearms s4, first half: at level 21 (`hwp levelup 20`; the picker opens from level
        10) the Subclass Picker shows the three doctrines, and picking takes each id."""
        self.new_char("LabPick")
        pl = self.gl("state").get("player", {})
        self.npc("npc_subclass_picker", PICKER)
        u = self.gl("use", "npc_subclass_picker")
        time.sleep(0.8)
        win = self.gl("state").get("window")
        shown = []
        for _ in range(4):
            texts = {}
            for root in self.gl("widgets", 12).get("roots", []):
                for n in root.get("nodes", []):
                    if n.get("id") in ("class-prev", "class-curr", "class-next", "skill-active-name", "skill-passive-name"):
                        texts.setdefault(n["id"], n.get("text", ""))
            shown.append(texts)
            self.gl("func", "nextclass")
            time.sleep(0.3)
        if self.gl("state").get("window"):
            self.g.key("escape")
            time.sleep(0.5)
        names = spec_names()
        curr = [s.get("class-curr", "") for s in shown]
        trio = {shown[0].get(k, "") for k in ("class-prev", "class-curr", "class-next")} if shown else set()
        self.notes.append(f"picker window {win}: shown {shown}")
        self.flag("spec_pick_open", u.get("ok") and pl.get("level", 0) >= 20 and bool(curr and curr[0]),
                  f"level {pl.get('level')}, use {u.get('ok')}, window {win}")
        self.flag("spec_pick_three", sorted(set(curr[:3])) == sorted(names) and curr[3] == curr[0] and trio == set(names),
                  f"stepped {curr}, prev/curr/next {sorted(trio)}, expected {names}")
        took = []
        for sub in SPECS:
            took.append(self.gl("subclass", sub).get("class"))
        self.flag("spec_pick_takes", took == list(SPECS), f"{took}")

    def firearms_sniper(self):
        """firearms s4 for the Sniper (decoy, flashbang, snipe, levelled in that order) and the
        s5 decoy: three brutes beside it go for the dummy, not the player who walked off; it
        is gone 8 s after the cast."""
        sc, pl = self.new_char("LabSniper", "hwp_firearms_sniper")
        if not self.enter_floor("sniper"):
            return
        dirs = self.open_dirs(130)
        d = dirs[0]
        perp = next((v for v in dirs if abs(v[0] * d[0] + v[1] * d[1]) < 0.2), (-d[1], d[0]))
        # decoy: Direction, SpawnUnit 24 px along the aim. Cast 1 alone times its life (castpoint
        # 200 + ttl 8000); cast 2, after the 15 s cooldown, gets three brutes beside it.
        if self.level("decoy", "hwp_fs_decoy"):
            c0 = self.gl("clock").get("sceneMs", 0)
            w = self.cast_watch("hwp_fs_decoy", lambda: self.gl("input", hold("sniper_decoy.sval"), 0, 0, d[0], d[1], "skill3"), secs=0.6)
            dec = [u for u in self.gl("near", 300, DECOY).get("units") or [] if not u.get("dead")]
            self.flag("decoy_casts", w["cd"] > 0 and len(dec) == 1, f"cooldown {w['cd']}, decoys {len(dec)}")
            self.cost_flag("decoy", "hwp_fs_decoy", "sniper_decoy.sval", w)
            last, gone, hp_last = None, None, None
            end = time.time() + 12
            while time.time() < end:
                now = self.gl("clock").get("sceneMs", 0) - c0
                us = [u for u in self.gl("near", 800, DECOY).get("units") or [] if not u.get("dead")]
                if us:
                    last, hp_last = now, us[0].get("hp")
                elif last is not None:
                    gone = now
                    break
                time.sleep(0.15 if now > 6500 else 0.8)
            self.flag("decoy_vanishes_8s", last is not None and gone is not None and last >= 7200 and gone <= 9500,
                      f"seen until {last} ms after the press (hp {hp_last}), gone at {gone} (castpoint 200 + ttl 8000)")
            # the 15 s cooldown from the first cast, then cast 2
            while self.entry(self.bar(), "hwp_fs_decoy").get("cd", 0) > 0 and time.time() < end + 10:
                time.sleep(0.5)
            self.gl("input", hold("sniper_decoy.sval"), 0, 0, d[0], d[1], "skill3")
            time.sleep(0.5)
            dec = [u for u in self.gl("near", 300, DECOY).get("units") or [] if not u.get("dead")]
            if dec:
                dx0, dy0 = dec[0]["x"], dec[0]["y"]
                # walk off the other way, then three brutes 100 to the decoy's side
                self.gl("input", 1200, -d[0], -d[1])
                time.sleep(1.4)
                px, py = self.pos()
                rx, ry = dx0 - px, dy0 - py
                spawns = []  # one gl multi: the three land in the same frame
                for k in (-25, 0, 25):
                    spawns += ["+", "spawn", BRUTE, round(rx + perp[0] * 100 + d[0] * k, 1), round(ry + perp[1] * 100 + d[1] * k, 1)]
                self.gl("multi", *spawns[1:])
                time.sleep(2.5)
                px, py = self.pos()
                br = [u for u in self.gl("near", 600, "bandit_brute").get("units") or [] if not u.get("dead")]
                dd = [round(math.hypot(u["x"] - dx0, u["y"] - dy0)) for u in br]
                dp = [round(math.hypot(u["x"] - px, u["y"] - py)) for u in br]
                dhp = [u.get("hp") for u in self.gl("near", 600, DECOY).get("units") or []]
                self.flag("decoy_pulls", len(br) >= 2 and all(a < b for a, b in zip(dd, dp)) and max(dd) <= 50
                          and math.hypot(px - dx0, py - dy0) >= 80,
                          f"brutes to decoy {dd}, to player {dp} (player {round(math.hypot(px - dx0, py - dy0))} from it), "
                          f"decoy hp {dhp} (a decoy killed by them counts: they went for it)")
                self.gl("kill", 600, "bandit_brute")
            else:
                self.flag("decoy_pulls", False, "no decoy on the second cast")
        # flashbang: TargetAOE, no damage: its cooldown is the cast
        if self.level("flashbang", "hwp_fs_flashbang"):
            tgt = (d[0] * 100, d[1] * 100)
            w = self.cast_watch("hwp_fs_flashbang", lambda: self.targeted("skill3", tgt[0], tgt[1], (16, 170)))
            self.flag("flashbang_casts", w["cd"] > 0, f"cooldown {w['cd']}, also cooled {w['others']}")
            self.cost_flag("flashbang", "hwp_fs_flashbang", "sniper_flashbang.sval", w)
        if self.level("snipe", "hwp_fs_snipe"):
            self.direction_test("snipe", "hwp_fs_snipe", "sniper_snipe.sval", d)
        self.buttons_flag("sniper")
        self.clear_dummies()
        self.to_town()

    def firearms_demo(self):
        """firearms s4 for Demolitions (jetpack, rpg, tube) and the s5 jetpack: the leap lands
        where the cursor is and the landing's fire burst hurts a dummy beside it."""
        self.new_char("LabDemo", "hwp_firearms_demolitions")
        if not self.enter_floor("demo"):
            return
        dirs = self.open_dirs(130)
        d = dirs[0]
        if self.level("jetpack", "hwp_fs_jetpack"):
            rng = (40, 190)
            (lx, ly), held, c = self.cursor_on(d[0] * 120, d[1] * 120, rng)
            px, py = self.pos()
            perp = (-d[1], d[0])
            du = self.dummy(lx + perp[0] * 22, ly + perp[1] * 22)  # inside the 40 burst, off the landing spot
            hp0 = self.hps([du])
            box = {}
            w = self.cast_watch("hwp_fs_jetpack", lambda: box.setdefault("at", self.targeted("skill3", lx, ly, rng)), secs=1.4)
            (tx, ty), held2 = box.get("at", ((lx, ly), False))
            time.sleep(0.3)
            texts = self.damage_texts(0.6)
            qx, qy = self.pos()
            hp1 = self.hps([du])
            miss = math.hypot((qx - px) - tx, (qy - py) - ty)
            self.flag("jetpack_casts", w["cd"] > 0, f"cooldown {w['cd']}, also cooled {w['others']}")
            self.flag("jetpack_lands_at_cursor", miss <= 16 and math.hypot(qx - px, qy - py) >= 30,
                      f"cursor at {round(tx)},{round(ty)} (held {held and held2}), landed {round(qx - px)},{round(qy - py)}: {round(miss)} off")
            self.flag("jetpack_fire_burst", hp1[du] < hp0[du] - 0.001,
                      f"dummy 22 off the landing hp {hp0[du]} -> {hp1[du]}, damage texts {[t.get('text') for t in texts]}")
            self.cost_flag("jetpack", "hwp_fs_jetpack", "demo_jetpack.sval", w)
            time.sleep(0.5)
        if self.level("rpg", "hwp_fs_rpg"):
            self.direction_test("rpg", "hwp_fs_rpg", "demo_rpg.sval", d)
        if self.level("tube", "hwp_fs_tube"):
            self.direction_test("tube", "hwp_fs_tube", "demo_tube.sval", d)
        self.buttons_flag("demo")
        self.clear_dummies()
        self.to_town()

    def firearms_assault(self):
        """firearms s4 for Assault (stun grenade, burst; adrenaline is passive)."""
        self.new_char("LabAssault", "hwp_firearms_assault")
        if not self.enter_floor("assault"):
            return
        dirs = self.open_dirs(130)
        d = dirs[0]
        if self.level("adrenaline", "hwp_fs_adrenaline"):
            e = self.entry(self.bar(), "hwp_fs_adrenaline")
            self.flag("adrenaline_passive", e.get("mode") == 0 and not e.get("button"), f"{e}")
        if self.level("stun", "hwp_fs_stun"):
            self.clear_dummies()
            rng = (16, 170)
            (sx, sy), held, c = self.cursor_on(d[0] * 100, d[1] * 100, rng)
            du = self.dummy(sx, sy)
            hp0 = self.hps([du])
            w = self.cast_watch("hwp_fs_stun", lambda: self.targeted("skill3", sx, sy, rng), secs=1.4)
            time.sleep(0.3)
            hp1 = self.hps([du])
            self.flag("stun_casts", w["cd"] > 0 and hp1[du] < hp0[du] - 0.001,
                      f"cooldown {w['cd']}, dummy at the cursor ({round(sx)},{round(sy)}, held {held}) hp {hp0[du]} -> {hp1[du]}")
            self.cost_flag("stun", "hwp_fs_stun", "assault_stun.sval", w)
        if self.level("burst", "hwp_fs_burst"):
            self.direction_test("burst", "hwp_fs_burst", "assault_burst.sval", d, dist=60)
        self.buttons_flag("assault")
        self.clear_dummies()
        self.to_town()


def run(p, sections="firearms_frag", **_):
    c = Checks(p)
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
