"""Test-plan checks for the Firearms Specialist (mods/firearms): firearms s3 (the Frag Grenade
lands where aimed and explodes with damage numbers), s4 (`hwp levelup 20`, the Subclass
Picker offers three specializations; each one's active casts and costs what its tooltip says,
its passive is passive) and the orbs (`gl orb`, Verbs_firearms.as: the skill sphere's
SkillTempUp): Marksman and Demolitionist orbs in their sections, the base kit's (Reload, Frag)
in firearms_base_orbs. s2 (the clip) and the guns are plan_checks.firearms_ammo / _guns. Same
style as plan_checks: each section flags booleans, the scenario's expect asserts them,
measured values go in the notes.

Targeted skills (frag, Assault's stun grenade: TargetingMode::TargetAOE) are cast
the way a player casts them: the skill button opens the targeting circle and the main-hand
click casts at the cursor (PlayerTargetingHelper.Update; with g_quickcast on, the button's
release). A posted mouse never reaches the game (RE_NOTES 2026-10-18), so `gl cursor dx dy`
(Verbs_firearms.as) writes GameInput.MousePos and reads it back; whatever the cursor reads at
the click is where the cast is expected to land (CalcMouseTargetPos: its direction, the
distance clamped to the skill's range). Orb tests cast with `gl castat <skill> dx dy nocd`
instead (Skill.Activate as the helper calls it, the cooldown cleared first), so they need not
wait out each variant's cooldown.

The game has three skill buttons: vanilla GetSkillInput (PlayerTargetingHelper.as:744-749)
gives the third and every later active spell Skill3. Core's extra skill keys (mods/core,
SkillKeys.as) give the 4th to 6th their own key, which `gl input` holds as hwp_skill4..6.
Reload and frag hold Skill1 and Skill2; a specialization's active is the 3rd (Skill3).
`<spec>_own_buttons`: the finished doctrine has a button per active skill (`gl skillbar`), and
a press of Skill3 and of each extra key casts its skill and no other.

Mana is read unrounded from `gl skillbar` (m_record.mana x max, = state manaExact). A costed
cast starts from full mana (top_up waits out the regen) and a full clip (givestacks), so
regeneration only runs after the cost is taken: the fall between the last full reading and
the next is the cost less at most the regen over that gap (the rate measured from the rise after). Expected = tooltip x the
state's manaCostMul. Direction presses are held past the skill's castpoint.

Sections: firearms_frag (s3), firearms_spec_pick, firearms_marksman, firearms_demolitionist,
firearms_assault (s4), firearms_base_orbs."""
import math
import re
import time
from pathlib import Path

from gamelab.bots import picker_skills
from gamelab.bots.plan_checks import Checks as Base

MOD = Path(__file__).resolve().parents[2] / "mods" / "firearms"
SKILLS = MOD / "players" / "hwp" / "firearms" / "skills"
LANG = MOD / "res" / "language" / "english" / "hwp_firearms.lang"
DUMMY = "doodads/generic/target_dummy_breakable.unit"  # 500 hp, stands still, enemy team
PICKER = "actors/npcs/town/npc_subclass_picker.unit"
DMG_TEXTS = {7, 8, 9, 11}  # FloatingTextType EnemyHurt, EnemyHurtLocal, EnemyHurtHusk, EnemyImmortal (a crit)
TOL = 0.4  # mana units

# subclass -> its skills in class order: (id, sval, tag, targeted range or None)
SPECS = {
    "hwp_firearms_sniper": [("hwp_fs_snipe", "sniper_snipe.sval", "snipe", None),
                            ("hwp_fs_focus", "sniper_focus.sval", "focus", None)],
    "hwp_firearms_demolitions": [("hwp_fs_rpg", "demo_rpg.sval", "rpg", None),
                                 ("hwp_fs_hoarder", "demo_hoarder.sval", "hoarder", None)],
    "hwp_firearms_assault": [("hwp_fs_burst", "assault_burst.sval", "burst", None),
                             ("hwp_fs_adrenaline", "assault_adrenaline.sval", "adrenaline", None)],
    "hwp_firearms_engineer": [("hwp_fs_turret", "engineer_turret.sval", "turret", (0, 120)),
                              ("hwp_fs_myturret", "engineer_myturret.sval", "myturret", None)],
}
TURRET = "hwp/firearms/units/turret"
BRUTE = "actors/humans/bandits/bandit_brute.unit"


def tooltip_cost(sval, level=1):
    """The mana cost the skill's tooltip shows (its "mana-cost" description param at that
    level; a tooltip without one shows no cost: 0)."""
    m = re.search(r"<array><s>mana-cost</s>(.*?)</array>", (SKILLS / sval).read_text(encoding="utf-8"))
    if not m:
        return 0
    vals = re.findall(r"<s>([^<]*)</s>", m.group(1))[1:]  # the first is the label string
    if not vals:
        return 0
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


# one rifle round: past its castpoint (80, attacks_firearms.sval), inside its 560 anim
RIFLE_PRESS = 200
# what a projectile hits before the dummy (gl near behaviors)
BLOCKERS = {"Breakable", "CompositeActorBehavior", "CompositeActorBehaviorNPC", "StateActorBehavior"}


def hold(sval):
    """Past the castpoint and the timeline's last entry (Double Barrel's second shell at 200
    ms aims where the press points: plan-firearms-b 20261019-143401 let go at 121 ms and the
    second shell missed)."""
    text = (SKILLS / sval).read_text(encoding="utf-8")
    m = re.search(r'<array name="timeline">(.*?)</array>', text, re.S)
    last = max((int(x) for x in re.findall(r"<i>(\d+)</i>", m.group(1))), default=0) if m else 0
    return max(castpoint(sval), last) + 120


def spec_names():
    text = LANG.read_text(encoding="utf-8")
    return [re.search(rf'name="skills.hwp_firearms.mastery_{i}.name">([^<]*)<', text).group(1) for i in (1, 2, 3, 4)]


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
        # the class starts with a pistol; these checks were written for the rifle (no 6 px muzzle offset)
        self.gl("equip", "hwp_rifle_01", "common")
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
        """A full clip (givestacks) and full mana (waits out the regen, up to 15 s), so the next
        cost is measured from a full pool and a round-gated skill can fire."""
        self.gl("givestacks", self.CLIP, 999)
        self.g.console("cht_give_mana 999")  # Deploy Turret's 50 regenerates in ~45 s
        end = time.time() + 15
        while time.time() < end:
            b = self.bar()
            if b.get("mana", 0) >= b.get("manaMax", 1) - 0.01:
                return True
            time.sleep(0.4)
        return False

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
        the cursor write held throughout. The click is one frame (input 1 ms): the helper casts
        on MainHandAttack.Pressed and lets go of the skill, so a main button still Down the next
        frame fires a bullet (1 mana; seen as flashbang's 0.82 "cost", run 20261018-121101).
        The mana just before the click goes in self.mark for cast_watch."""
        (tx, ty), held, _ = self.cursor_on(dx, dy, rng)
        ax, ay = unit(tx, ty)
        self.gl("input", 60, 0, 0, ax, ay, button)
        time.sleep(0.35)
        if not self.quickcast:
            (tx, ty), held2, _ = self.cursor_on(dx, dy, rng)  # again, just before the click
            held = held and held2
            self.mark = (time.time(), self.bar().get("mana", 0.0))
            self.gl("input", 1, 0, 0, ax, ay, "main")
        return (tx, ty), held

    def cast_watch(self, sid, cast, secs=1.6):
        """Run cast() and watch the skill bar for secs: mana before, the lowest after, this
        skill's cooldown, and any other skill that went on cooldown with it. A targeted cast
        (several commands before its click) leaves the mana read just before the click in
        self.mark: the window starts there."""
        b0 = self.bar()
        cd0 = {s["id"]: s.get("cd", 0) for s in b0.get("skills", [])}
        m0, t0 = b0.get("mana", 0.0), time.time()
        self.mark = None
        cast()
        if self.mark:
            t0, m0 = self.mark
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
                "rate": round(max(rate, 0.0), 2), "cd": round(cd, 3), "others": sorted(others),
                "full": m0 >= top, "span": round(samples[-1][0] - t0, 2), "end": round(samples[-1][1], 2)}

    def cost_flag(self, tag, sid, sval, w):
        tip, data = tooltip_cost(sval), sval_cost(sval)
        live = self.entry(self.bar(), sid).get("mana")
        mul = self.gl("state").get("player", {}).get("manaCostMul", 1.0) or 1.0
        want = tip * mul
        # the cost lies between the fall and the fall + the regen over the gap it was seen in
        lo, hi = w["drop"] - TOL, w["drop"] + w["rate"] * w["gap"] + TOL
        self.flag(f"{tag}_cost", w["full"] and lo <= want <= hi and tip == data == live,
                  f"from full {w['full']}: mana {w['m0']} -> low {w['low']}, {w['end']} after {w['span']} s "
                  f"(first fall {w['drop']} within a {w['gap']} s read gap, regen {w['rate']}/s), "
                  f"tooltip {tip} x cost mul {mul}, sval {data}, GetCost {live}")

    def level(self, tag, sid):
        r = self.gl("skill", sid, 1)
        time.sleep(0.6)  # SkillUp reloads the skills (LoadSkills)
        ok = r.get("level", 0) >= 1
        if not ok:
            self.flag(f"{tag}_learned", False, str(r))
        return ok

    def buttons_flag(self, spec, d=(1.0, 0.0)):
        b = self.bar()
        act = [(s["id"], s.get("button")) for s in b.get("skills", []) if s.get("type") == 4 and s.get("mode", 0) != 0]
        btns = [x[1] for x in act]
        # Skill3 and each extra key (hwp_skill4..6): a press casts that doctrine skill alone
        info = {e[0]: e for v in SPECS.values() for e in v}
        tried = []
        for sid, btn in act:
            if sid not in info or not (btn == "skill3" or (btn or "").startswith("hwp_skill")):
                continue
            _, sval, _, rng = info[sid]
            end = time.time() + 20
            while self.entry(self.bar(), sid).get("cd", 0) > 0 and time.time() < end:
                time.sleep(0.5)
            self.top_up()
            if rng:
                w = self.cast_watch(sid, lambda: self.targeted(btn, d[0] * 100, d[1] * 100, rng), secs=1.4)
            else:
                w = self.cast_watch(sid, lambda: self.gl("input", hold(sval), 0, 0, d[0], d[1], btn), secs=1.0)
            tried.append((sid, btn, w["cd"] > 0, w["others"]))
            time.sleep(0.5)
        self.flag(f"{spec}_own_buttons", len(btns) == len(set(btns)) and all(c and not o for _, _, c, o in tried),
                  f"active spells {act}; presses (skill, button, cast, others cooled) {tried}")

    # --- direction skills: a dummy in the line of fire
    def clear_dir(self, pref, dist):
        """A direction from where the player stands now with a clear shot dist (+16) out (gl
        rayhit: no wall, no hard tile; and no breakable or actor within 12 of the line, which a
        round that stops at its first hit would hit instead), pref first. Run 20261018-130918:
        snipe fired along the direction probed before the decoy walks moved the player, and hit
        nothing."""
        px, py = self.pos()
        cands = [pref] + sorted(((round(math.cos(math.radians(a)), 3), round(math.sin(math.radians(a)), 3))
                                 for a in range(0, 360, 45)), key=lambda q: -(q[0] * pref[0] + q[1] * pref[1]))
        near = [u for u in self.gl("near", dist + 30).get("units") or []
                if u.get("behavior") in BLOCKERS and "target_dummy" not in u.get("name", "")]
        r = {}
        for u in cands:
            r = self.gl("rayhit", round(px, 1), round(py, 1), round(px + u[0] * (dist + 16), 1), round(py + u[1] * (dist + 16), 1))
            if not r.get("ok") or r.get("wall") or r.get("tile"):
                continue
            on = [n["name"] for n in near if 6 < (n["x"] - px) * u[0] + (n["y"] - py) * u[1] < dist + 16
                  and abs((n["x"] - px) * u[1] - (n["y"] - py) * u[0]) < 12]
            if on:
                self.notes.append(f"line {u} from {round(px)},{round(py)} blocked by {on}")
                continue
            return u, r
        self.notes.append(f"no clear line {dist} out from {round(px)},{round(py)}: last rayhit {r}")
        return pref, r

    def direction_test(self, tag, sid, sval, d, dist=80):
        """A Direction skill (snipe, rpg, burst) fired at a dummy `dist` along d: it casts
        (its cooldown starts, the dummy loses HP) and costs the tooltip's mana."""
        self.clear_dummies()
        d, ray = self.clear_dir(d, dist)
        du = self.dummy(d[0] * dist, d[1] * dist)
        self.top_up()
        hp0 = self.hps([du])
        w = self.cast_watch(sid, lambda: self.gl("input", hold(sval), 0, 0, d[0], d[1], "skill3"))
        time.sleep(0.3)
        hp1 = self.hps([du])
        hit = hp1[du] < hp0[du] - 0.001
        self.flag(f"{tag}_casts", w["cd"] > 0 and hit,
                  f"aim {d} (line clear: wall {ray.get('wall')}, tile {ray.get('tile')}), cooldown {w['cd']}, "
                  f"dummy hp {hp0[du]} -> {hp1[du]}, also cooled {w['others']}")
        self.cost_flag(tag, sid, sval, w)
        return w

    # --- sections
    def firearms_frag(self):
        """firearms s3: Frag Grenade (Skill2, 16-170 range, 64 radius) thrown at two spots 110
        out, as far apart as the open directions allow, one dummy at each: the aimed one loses HP, the other doesn't, and the damage number
        floats over the hit one. Beside the first spot, a dummy 40 to one side (inside 64) is hit
        by the first throw and one 96 to the other (inside the old 128) isn't."""
        self.gl("char", "hwp_firearms", "LabFrag")
        self.wait_phase("town", 60)
        time.sleep(2)
        self.base_skills()
        if not self.enter_floor("frag"):
            return
        dirs = self.open_dirs(110)
        a = dirs[0]
        # the open direction furthest round from a: at 84 deg the spots are only 147 apart, at
        # 180 deg 220 (the blast was 128 until 2026-10-19, 64 now)
        b = min(dirs[1:], key=lambda v: v[0] * a[0] + v[1] * a[1], default=None)
        if b is None or b[0] * a[0] + b[1] * a[1] >= 0.1:
            b = (-a[1], a[0])
        rng = (16, 170)
        spots = [(a[0] * 110, a[1] * 110), (b[0] * 110, b[1] * 110)]
        eff = []
        for sx, sy in spots:  # the cursor decides where a throw lands: the dummies go where it reads
            e, held, c = self.cursor_on(sx, sy, rng)
            eff.append((e, held, c))
        units = [self.dummy(e[0][0], e[0][1]) for e in eff]
        # square to the throw line from the first spot (behind it, the aimed dummy blocks the
        # blast's line of sight: Explode.as:173-190), 40 to one side and 96 to the other:
        # inside and outside 64
        ex, ey = eff[0][0]
        el = max(1.0, (ex * ex + ey * ey) ** 0.5)
        ring = [self.dummy(ex - ey / el * d, ey + ex / el * d) for d in (40, -96)]
        self.notes.append(f"frag spots asked {[(round(x), round(y)) for x, y in spots]}, cursor gave "
                          f"{[(round(e[0][0]), round(e[0][1]), e[1]) for e in eff]}, gamepad {eff[0][2].get('gamepad')}, "
                          f"quickcast {self.quickcast}")
        self.flag("frag_cursor_held", all(e[1] for e in eff), "gl cursor wrote GameInput.MousePos and read it back")
        results, texts_all, casts = [], [], []
        for i, (e, _, _) in enumerate(eff):
            hp0 = self.hps(units)
            r0 = self.hps(ring) if i == 0 else None
            self.targeted("skill2", e[0], e[1], rng)
            texts = self.damage_texts(1.6)  # at once: it lands ~0.5 s after the click, its number lives 0.5 s
            cd = self.entry(self.bar(), "hwp_fs_frag").get("cd", 0)
            hp1 = self.hps(units)
            if i == 0:
                r1 = self.hps(ring)
                inner, outer = (r1[u] < r0[u] - 0.001 for u in ring)
                self.flag("frag_radius_64", inner and not outer,
                          f"dummy 40 beside the spot hit {inner}, 96 beside hit {outer} (hp {r0} -> {r1})")
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
        10) the Subclass Picker shows the four doctrines, its skill row shows each doctrine's
        skills labelled by type (picker_skill_labels), and picking takes each id."""
        self.new_char("LabPick")
        pl = self.gl("state").get("player", {})
        self.npc("npc_subclass_picker", PICKER)
        u = self.gl("use", "npc_subclass_picker")
        time.sleep(0.8)
        win = self.gl("state").get("window")
        shown, rows = [], {}
        for _ in range(5):
            texts = {}
            roots = self.gl("widgets", 12).get("roots", [])
            for root in roots:
                for n in root.get("nodes", []):
                    if n.get("id") in ("class-prev", "class-curr", "class-next", "skill-active-name", "skill-passive-name"):
                        texts.setdefault(n["id"], n.get("text", ""))
            shown.append(texts)
            rows.setdefault(texts.get("class-curr", ""), picker_skills.read_row(roots))
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
        self.flag("spec_pick_four", sorted(set(curr[:4])) == sorted(names) and curr[4] == curr[0]
                  and len(trio) == 3 and trio <= set(names),
                  f"stepped {curr}, prev/curr/next {sorted(trio)}, expected {names}")
        # the skill row by the skills' real types (core SubclassPick.as), against each spec's defs
        probs = {}
        for sub in SPECS:
            defs = self.gl("classskills", sub)
            probs[defs.get("name") or sub] = (picker_skills.row_problems(rows.get(defs.get("name"), []), defs)
                                              if defs.get("ok") else [f"classskills {sub}: {defs.get('error')}"])
        self.flag("picker_skill_labels", len(probs) == len(SPECS) and not any(probs.values()),
                  f"rows {rows}; problems {probs}")
        took = []
        for sub in SPECS:
            took.append(self.gl("subclass", sub).get("class"))
        self.flag("spec_pick_takes", took == list(SPECS), f"{took}")

    # --- clip, stacks and orbs
    STACKS = "players/hwp/firearms/stacks_firearms.sval:"

    def stacks(self, name):
        """A firearms stack's count (givestacks 0 adds nothing and replies GetStacks)."""
        return self.gl("givestacks", self.STACKS + name, 0).get("stacks", -1)

    def orb(self, oid, times=1):
        r = self.gl("orb", oid, times)
        time.sleep(0.6)  # SkillTempUp reloads the skills (LoadSkills)
        return r.get("ok", False), r.get("level", 0)

    def orb_off(self, oid):
        for _ in range(5):
            if not self.gl("orb", oid, "down").get("ok"):
                break
        time.sleep(0.6)

    @staticmethod
    def crits(texts):
        return [t for t in texts if t.get("type") == 11 or str(t.get("text", "")).endswith("!")]

    def aimed_cast(self, sid, d, ms, wait=True):
        """A held Skill3 press along d (ms: past the skill's update-aim, which re-reads the aim
        until its castpoint), the cooldown waited out first unless wait is False. Not castat:
        run 20261019-013510, castat Snipe with the aim held along d took its rounds and hit
        neither dummy on the line, where a held skill3 press hit."""
        if wait:
            self.ready(sid)
        return self.gl("input", ms, 0, 0, d[0], d[1], "skill3")

    def log_pos(self):
        """The game log's size in bytes: a mark for log_from."""
        p = self.g.log_path
        return p.stat().st_size if p.exists() else 0

    def log_from(self, pos):
        """The game log from byte pos on (not the whole file: it is MBs by now)."""
        p = self.g.log_path
        if not p.exists():
            return ""
        with open(p, "rb") as f:
            f.seek(pos)
            return f.read().decode("utf-8", errors="replace")

    def wait_log(self, pattern, pos, secs, poll=0.02):
        """The first match of pattern logged after pos, polled every poll s, or None after secs.
        The poll sleeps, so the bot doesn't take CPU from the game it is timing."""
        end = time.time() + secs
        while True:
            m = re.search(pattern, self.log_from(pos))
            if m or time.time() >= end:
                return m
            time.sleep(poll)

    def ready(self, sid, secs=20):
        end = time.time() + secs
        while self.entry(self.bar(), sid).get("cd", 0) > 0 and time.time() < end:
            time.sleep(0.25)

    def line_dummies(self, d, dists):
        """Dummies along a clear line from the player (d first) at each distance: (direction
        used, ids)."""
        self.clear_dummies()
        d, _ = self.clear_dir(d, max(dists))
        return d, [self.dummy(d[0] * r, d[1] * r) for r in dists]

    def dummy_watch(self, du, secs):
        """Damage numbers and the dummies' buff tags seen over secs, and the dummy's hp after."""
        seen, tags = {}, set()
        end = time.time() + secs
        while time.time() < end:
            for t in self.gl("floats").get("texts") or []:
                if t.get("type") in DMG_TEXTS:
                    seen.setdefault((t.get("text"), round(t.get("x", 0.0))), t)
            for ac in self.gl("actorbuffs", 300, "target_dummy").get("actors") or []:
                for bf in ac.get("buffs") or []:
                    tags.update(bf.get("tags") or [])
            time.sleep(0.05)
        return [t.get("text") for t in seen.values()], sorted(tags), self.hps([du])[du]

    def refill_after_empty(self, dash_at=None):
        """Seconds from emptying the clip to it refilling (the automatic reload)."""
        self.ready("hwp_fs_reload", 5)
        self.gl("givestacks", self.CLIP, -999)
        t = self.refill_time(dash_at=dash_at)
        time.sleep(0.5)
        return t

    # --- sections
    def firearms_marksman(self):
        """Marksman: Snipe (Skill3) hits a dummy, costs its tooltip mana and no rounds; Critical
        Aim is passive, a gun round that hits gives Focus and one that hits nothing loses it all;
        Piercing Bullet takes Snipe through a first dummy into a second; with Headshot (taken first, so the
        round stops at its target) the first dummy a Snipe round hits takes a critical hit (2 of 2)."""
        self.new_char("LabMarksman", "hwp_firearms_sniper")
        if not self.enter_floor("marksman"):
            return
        d = self.open_dirs(130)[0]
        if self.level("snipe", "hwp_fs_snipe"):
            self.direction_test("snipe", "hwp_fs_snipe", "sniper_snipe.sval", d)
            c, mx = self.clip(), self.clip_max()
            self.flag("snipe_no_rounds", c == mx, f"clip {c}/{mx} after one Snipe from full (mana only)")
        if self.level("focus", "hwp_fs_focus"):
            e = self.entry(self.bar(), "hwp_fs_focus")
            self.flag("focus_passive", e.get("mode") == 0 and not e.get("button"), f"{e}")
            d2, _ = self.line_dummies(d, [60])
            self.gl("givestacks", self.CLIP, 999)
            f0 = self.stacks("focus")
            for _ in range(3):
                self.gl("input", RIFLE_PRESS, 0, 0, d2[0], d2[1], "main")
                time.sleep(0.8)
            f1 = self.stacks("focus")
            self.clear_dummies()
            self.gl("input", RIFLE_PRESS, 0, 0, -d2[0], -d2[1], "main")
            time.sleep(2.0)  # the round flies until a wall or its ttl
            f2 = self.stacks("focus")
            self.flag("focus_gains", f1 >= f0 + 2, f"focus {f0} -> {f1} after 3 shots at a dummy")
            self.flag("focus_lost_on_miss", f1 > 0 and f2 == 0, f"focus {f1} -> {f2} after a shot at nothing")
        # Headshot before Piercing Bullet: a round that stops at its first target is destroyed
        # before that hit's damage (NewProjectile.OnHit), the case that never crit
        ok, lvl = self.orb("hwp_fs_snipe_headshot")
        shots = []
        for _ in range(2):
            d4, (du,) = self.line_dummies(d, [70])
            self.top_up()
            self.aimed_cast("hwp_fs_snipe", d4, hold("sniper_snipe.sval"))
            texts = self.damage_texts(1.0)
            shots.append(([t.get("text") for t in texts], len(self.crits(texts))))
        self.flag("headshot_crits", ok and all(n >= 1 for _, n in shots), f"orb level {lvl}; per Snipe (texts, crits) {shots}")
        ok, lvl = self.orb("hwp_fs_snipe_pierce", 3)
        d3, (a, b) = self.line_dummies(d, [50, 90])
        self.top_up()
        hp0 = self.hps([a, b])
        self.aimed_cast("hwp_fs_snipe", d3, hold("sniper_snipe.sval"))
        time.sleep(1.0)
        hp1 = self.hps([a, b])
        self.flag("snipe_pierce_both", ok and hp1[a] < hp0[a] - 0.001 and hp1[b] < hp0[b] - 0.001,
                  f"orb level {lvl}; dummies at 50/90: {hp0} -> {hp1}")
        self.buttons_flag("sniper", d)
        self.clear_dummies()
        self.to_town()

    def firearms_demolitionist(self):
        """Demolitionist: the Rocket Launcher (Skill3) hits a dummy and costs its tooltip mana;
        Fat Boy's rocket blinds, Magic Missile hits twice (ice, then the fire), Quad Missile
        Chambers fires 4 missiles; Ordinance Hoarder (passive) banks a rocket charge while the
        launcher waits ready and spends it to clear the cooldown after a cast."""
        self.new_char("LabDemo", "hwp_firearms_demolitions")
        if not self.enter_floor("demo"):
            return
        d = self.open_dirs(130)[0]
        if not self.level("rpg", "hwp_fs_rpg"):
            return
        self.direction_test("rpg", "hwp_fs_rpg", "demo_rpg.sval", d)

        def fire(orb, watch=1.4):
            ok, lvl = self.orb(orb)
            dd, (du,) = self.line_dummies(d, [80])
            self.top_up()
            hp0 = self.hps([du])[du]
            self.aimed_cast("hwp_fs_rpg", dd, 720)  # Quad re-aims to 600
            texts, tags, hp1 = self.dummy_watch(du, watch)
            self.orb_off(orb)
            return {"ok": ok, "lvl": lvl, "hit": hp1 < hp0 - 0.001, "hp": (hp0, hp1), "texts": texts, "tags": tags}

        r = fire("hwp_fs_rpg_fatboy")
        self.flag("fatboy_blinds", r["ok"] and r["hit"] and "blindness" in r["tags"], f"{r}")
        r = fire("hwp_fs_rpg_magic")
        self.flag("magic_missile_two_hits", r["ok"] and r["hit"] and len(r["texts"]) >= 2, f"{r}")
        r = fire("hwp_fs_rpg_quad", watch=1.8)
        self.flag("quad_four_missiles", r["ok"] and r["hit"] and len(r["texts"]) >= 4, f"{r}")
        if self.level("hoarder", "hwp_fs_hoarder"):
            e = self.entry(self.bar(), "hwp_fs_hoarder")
            self.flag("hoarder_passive", e.get("mode") == 0 and not e.get("button"), f"{e}")
            self.ready("hwp_fs_rpg")
            # level 1: a charge per 8 s x 0.9091 = 7.27 s ready, max 1
            seen, t0 = [], time.time()
            while time.time() - t0 < 9.5:
                seen.append((round(time.time() - t0, 1), self.stacks("rocket_charges")))
                if seen[-1][1] >= 1:
                    break
                time.sleep(0.5)
            banked = seen[-1][1]
            shown0 = self.stacks("rocket_charges_shown")
            self.flag("hoarder_banks_charge", banked == 1 and seen[-1][0] >= 6.0, f"(s, charges) {seen[-3:]}")
            self.top_up()
            self.aimed_cast("hwp_fs_rpg", d, 420, wait=False)
            time.sleep(1.6)
            cd1, ch1 = self.entry(self.bar(), "hwp_fs_rpg").get("cd", 0), self.stacks("rocket_charges")
            self.aimed_cast("hwp_fs_rpg", d, 420, wait=False)
            time.sleep(1.6)
            cd2, ch2 = self.entry(self.bar(), "hwp_fs_rpg").get("cd", 0), self.stacks("rocket_charges")
            shown2 = self.stacks("rocket_charges_shown")
            # the icon counts every use ready: 1 stored + the skill = 2, then 0 on cooldown
            self.flag("hoarder_icon_counts_all", shown0 == 2 and shown2 == 0, f"icon {shown0} ready, {shown2} on cooldown")
            self.flag("hoarder_spends_charge", banked == 1 and cd1 == 0 and ch1 == 0 and cd2 > 0,
                      f"after cast 1: cooldown {cd1}, charges {ch1}; after cast 2: cooldown {cd2}, charges {ch2}")
        self.buttons_flag("demo", d)
        self.clear_dummies()
        self.to_town()

    def firearms_base_orbs(self):
        """The base kit's orbs. Explosive Reload: Reload throws the magazine at its castpoint
        (the 2 s reload), which blows up a dummy; with dual pistols the second magazine follows
        the first by about 100 ms. Dodge Reload Skip: a dodge 0.3 s into the automatic reload
        refills the clip at once, and so does one 0.8 s into a manual Reload.
        Over-Reload: a Reload inside the automatic reload's logged window is perfect (+6
        rounds of clip) and the bonus is lost when the clip runs dry; during a manual Reload a
        second press inside its window is perfect, a second perfect doesn't stack, and a plain
        Reload clears the bonus. Frag orbs: Stun Grenade stuns or slows, Incendiary and Gas
        keep hurting after the blast."""
        self.gl("char", "hwp_firearms", "LabOrbs")
        self.wait_phase("town", 60)
        time.sleep(2)
        self.gl("equip", "hwp_rifle_01", "common")  # the class starts with a pistol
        self.base_skills()
        if not self.enter_floor("orbs"):
            return
        d = self.open_dirs(130)[0]

        ok, lvl = self.orb("hwp_fs_reload_explosive")
        # a direction throw lands 100 out (IProjectile.as GetTargetPos; GroundBouncing hit-target)
        d1, (du,) = self.line_dummies(d, [100])
        self.gl("givestacks", self.CLIP, 999)
        self.gl("givestacks", self.CLIP, -1)  # Reload won't start on a full clip
        rounds = self.clip()
        hp0 = self.hps([du])[du]
        self.gl("input", hold("fs_reload.sval"), 0, 0, d1[0], d1[1], "skill1")  # Reload re-aims to its castpoint
        texts, _, hp1 = self.dummy_watch(du, 3.5)  # thrown at the 2 s castpoint
        self.flag("explosive_reload_hits", ok and hp1 < hp0 - 0.001,
                  f"{rounds} rounds thrown: dummy {hp0} -> {hp1}, texts {texts}")

        # dual pistols: the off hand's magazine is a second timeline entry, 100 ms on
        self.g.console("dbg_cht_ignore_equipment_requirements 0")
        self.g.console("dbg_cht_ignore_equipment_requirements 1")
        eq = [bool(self.gl("equip", it, "common").get("ok")) for it in ("hwp_glock_mh_01", "hwp_glock_oh_01")]
        time.sleep(1.0)  # the gun markers re-apply every 250 ms
        d1, (du,) = self.line_dummies(d, [100])
        self.ready("hwp_fs_reload")
        self.gl("givestacks", self.CLIP, 999)
        self.gl("givestacks", self.CLIP, -2)
        rounds = self.clip()
        hp0 = self.hps([du])[du]
        mark = self.log_pos()
        self.gl("input", hold("fs_reload.sval"), 0, 0, d1[0], d1[1], "skill1")
        texts, _, hp1 = self.dummy_watch(du, 3.5)
        log = self.log_from(mark)
        first = re.search(r"explosive reload: (\d+) rounds at \d+, two magazines \(scene (\d+) ms\)", log)
        second = re.search(r"explosive reload: second magazine, (\d+) rounds \(scene (\d+) ms\)", log)
        gap = int(second[2]) - int(first[2]) if first and second else None
        self.flag("explosive_reload_dual_in_turn",
                  all(eq) and gap is not None and 50 <= gap <= 250 and int(first[1]) == rounds
                  and int(second[1]) == rounds // 2 and hp1 < hp0 - 0.001,
                  f"equip {eq}, {rounds} rounds; first {first and first.group(0)}, second "
                  f"{second and second.group(0)}, gap {gap} ms; dummy {hp0} -> {hp1}")
        self.gl("equip", "hwp_rifle_01", "common")
        time.sleep(1.0)
        self.g.console("dbg_cht_ignore_equipment_requirements 0")
        self.orb_off("hwp_fs_reload_explosive")
        self.clear_dummies()

        base = self.refill_after_empty()
        ok, lvl = self.orb("hwp_fs_reload_dodge")
        skip = self.refill_after_empty(dash_at=0.3)
        self.flag("dodge_skip_finishes_reload", ok and base is not None and skip is not None and skip < 0.9 and base > 1.3,
                  f"refill after emptying: {base} s without a dodge, {skip} s with a dodge at 0.3 s")
        # dodges are charges that recharge (Player.as, BaseDashRechargeTime): one 4 s after the
        # last never left (plan-firearms-orbs 20261019-154049), so wait for a charge first. The
        # max is read before: the gl call after an hwp console line took ~3 s, and the dodge
        # landed after the reload (plan-firearms-orbs 20261019-154656). The game logs the dodge.
        mx = self.clip_max()
        time.sleep(5)
        self.ready("hwp_fs_reload")
        self.gl("givestacks", self.CLIP, 999)
        self.gl("givestacks", self.CLIP, -5)
        before, mark, t0 = self.clip(), self.log_pos(), time.time()
        self.gl("input", 60, 0, 0, d[0], d[1], "skill1")
        time.sleep(max(0.0, t0 + 0.8 - time.time()))
        self.gl("input", 120, 0, 1, 0, 1, "dash")
        time.sleep(0.4)
        after = self.clip()
        line = re.search(r"reload: dodge at (\d+)/(\d+) ms finishes it", self.log_from(mark))
        self.flag("dodge_skip_finishes_manual", ok and before < mx and line is not None and after == mx,
                  f"clip {before}/{mx}, {after} after the dodge; logged {line and line.group(0)}")
        self.orb_off("hwp_fs_reload_dodge")

        ok, lvl = self.orb("hwp_fs_reload_over")
        # with Explosive Reload too: a perfect on the automatic reload must not throw a
        # magazine (the clip was empty; the top-up comes after the cast lands)
        self.orb("hwp_fs_reload_explosive")
        mx0 = self.clip_max()
        lag, tries, perfect, thrown = 0.0, [], False, None
        for _ in range(5):
            self.ready("hwp_fs_reload")
            mark = self.log_pos()
            self.gl("givestacks", self.CLIP, -999)
            t0 = time.time()
            win = self.wait_log(r"over-reload: window (\d+)-(\d+) of (\d+) ms", mark, 1.0)
            if not win:
                tries.append("no window logged")
                break
            a, b, _ = (int(x) for x in win.groups())
            # t0 is about the reload's start; press so the game sees it mid-window, less the
            # lateness the last miss measured
            time.sleep(max(0.0, t0 + (a + b) / 2000 - lag - time.time()))
            self.gl("input", 60, 0, 0, d[0], d[1], "skill1")
            time.sleep(0.4)
            log = self.log_from(mark)
            hit = re.search(r"over-reload: perfect at (\d+)", log)
            miss = re.search(r"over-reload: missed at (\d+)", log)
            got = int((hit or miss).group(1)) if (hit or miss) else None
            tries.append((a, b, got))
            if hit:
                perfect = True
                thrown = re.findall(r"explosive reload: .*", log)
                break
            if got is not None:
                lag += (got - (a + b) / 2) / 1000
            time.sleep(1.8)
        time.sleep(0.3)
        c1, mx1 = self.clip(), self.clip_max()
        self.flag("over_reload_perfect", ok and perfect and mx1 == mx0 + 5 and c1 == mx1,
                  f"tries (window start, end, pressed at) {tries}; clip {c1}/{mx1}, max before {mx0}")
        self.flag("over_reload_no_free_mag", perfect and thrown == [],
                  f"magazines thrown by the perfect auto-reload with Explosive Reload: {thrown}")
        self.orb_off("hwp_fs_reload_explosive")
        self.gl("givestacks", self.CLIP, -999)
        time.sleep(2.6)  # the automatic reload
        c2, mx2 = self.clip(), self.clip_max()
        self.flag("over_reload_lost_when_dry", perfect and mx2 == mx0 and c2 == mx0, f"clip {c2}/{mx2} after running dry")

        # a manual Reload with rounds left: the cast is the timed reload, and a second press
        # inside its window is perfect (and lands the cast at once)
        def manual(second=True, lag=0.0):
            self.ready("hwp_fs_reload")
            self.gl("givestacks", self.CLIP, 999)
            self.gl("givestacks", self.CLIP, -10)
            mark = self.log_pos()
            t0 = time.time()
            self.gl("input", 60, 0, 0, d[0], d[1], "skill1")
            win = self.wait_log(r"over-reload: manual window (\d+)-(\d+) of (\d+) ms", mark, 0.5)
            if not win:
                return None, "no window logged"
            a, b, _ = (int(x) for x in win.groups())
            if second:
                # both presses take the same path in, so time the second from the first
                time.sleep(max(0.0, t0 + (a + b) / 2000 - lag - time.time()))
                self.gl("input", 60, 0, 0, d[0], d[1], "skill1")
            time.sleep(0.8 if second else 2.6)  # a plain Reload lands at its 2 s castpoint
            log = self.log_from(mark)
            hit = re.search(r"over-reload: manual perfect at (\d+)", log)
            miss = re.search(r"over-reload: manual missed at (\d+)", log)
            got = int((hit or miss).group(1)) if (hit or miss) else None
            return bool(hit), (a, b, got)

        def perfect_manual():
            lag, tries = 0.0, []
            for _ in range(6):
                hit, t = manual(lag=lag)
                tries.append(t)
                if hit:
                    return True, tries
                if isinstance(t, tuple) and t[2] is not None:
                    lag += (t[2] - (t[0] + t[1]) / 2) / 1000
            return False, tries

        mp1, mtries1 = perfect_manual()
        c3, mx3 = self.clip(), self.clip_max()
        self.flag("over_reload_manual_perfect", mp1 and mx3 == mx0 + 5 and c3 == mx3,
                  f"tries (window start, end, pressed at) {mtries1}; clip {c3}/{mx3}, max before {mx0}")
        mp2, mtries2 = perfect_manual()
        c4, mx4 = self.clip(), self.clip_max()
        self.flag("over_reload_capped", mp1 and mp2 and mx4 == mx0 + 5 and c4 == mx4,
                  f"second perfect: tries {mtries2}; clip {c4}/{mx4} (empty-clip perfect gives {mx0 + 5})")
        _, plain = manual(second=False)
        c5, mx5 = self.clip(), self.clip_max()
        self.flag("over_reload_plain_clears", mp1 and mx5 == mx0 and c5 == mx0,
                  f"plain manual Reload {plain}: clip {c5}/{mx5}")

        def bar():
            out = self.hwp("firearms reload", 0.3, until="reload bar: ")
            lines = [ln for ln in out.splitlines() if "reload bar: " in ln]
            return lines[-1] if lines else out.strip()[-300:]

        # a left click inside the automatic reload's gold window is perfect too
        lag, ctries, cperfect = 0.0, [], False
        for _ in range(5):
            mark = self.log_pos()
            self.gl("givestacks", self.CLIP, -999)
            t0 = time.time()
            win = self.wait_log(r"over-reload: window (\d+)-(\d+) of (\d+) ms", mark, 1.0)
            if not win:
                ctries.append("no window logged")
                break
            a, b, _ = (int(x) for x in win.groups())
            time.sleep(max(0.0, t0 + (a + b) / 2000 - lag - time.time()))
            self.gl("input", 60, 0, 0, d[0], d[1], "main")
            time.sleep(0.4)
            log = self.log_from(mark)
            hit = re.search(r"over-reload: perfect \(click\) at (\d+)", log)
            miss = re.search(r"over-reload: missed \(click\) at (\d+)", log)
            got = int((hit or miss).group(1)) if (hit or miss) else None
            ctries.append((a, b, got))
            if hit:
                cperfect = True
                break
            if got is not None:
                lag += (got - (a + b) / 2) / 1000
            time.sleep(1.8)
        time.sleep(0.3)
        c6, mx6 = self.clip(), self.clip_max()
        # the click that lands it may go on to start a burst once the clip is full
        self.flag("over_reload_click_perfect", cperfect and mx6 == mx0 + 5 and c6 >= mx6 - 3,
                  f"tries (window start, end, clicked at) {ctries}; clip {c6}/{mx6}")
        self.gl("givestacks", self.CLIP, -999)
        time.sleep(2.6)

        # a miss: the bar stays up with its white red, and a second press in the gold does nothing
        mark = self.log_pos()
        self.gl("givestacks", self.CLIP, -999)
        t0 = time.time()
        win = self.wait_log(r"over-reload: window (\d+)-(\d+) of (\d+) ms", mark, 1.0)
        missed, red, second = None, "", None
        if win:
            a, b, total = (int(x) for x in win.groups())
            early = a - total // 2 >= 300   # room for a click before the gold
            # late gold: click right after it, so the click (with the console lag) still lands before the end
            at = (total // 2 + 60) if early else min(total - 80, b + 40)
            time.sleep(max(0.0, t0 + at / 1000 - time.time()))
            self.gl("input", 60, 0, 0, d[0], d[1], "main")
            time.sleep(0.15)
            self.g.shot("reload-bar-missed", settle=False)  # before the console line, while the bar is up
            red = bar()
            if early:
                time.sleep(max(0.0, t0 + (a + b) / 2000 - time.time()))
                self.gl("input", 60, 0, 0, d[0], d[1], "skill1")
            time.sleep(0.3)
            log = self.log_from(mark)
            missed = re.search(r"over-reload: missed \(click\) at (\d+)", log)
            second = re.findall(r"over-reload: (?:manual )?(?:perfect|missed)", log)
        time.sleep(2.0)
        mx7 = self.clip_max()
        # the bar stays red to the reload's end (shot reload-bar-missed); read after the shot it may have ended
        self.flag("over_reload_miss_red_once", missed is not None and ", red," in red and len(second or []) == 1
                  and mx7 == mx0, f"window {win and win.group(0)}; bar after the miss {red!r}; judged {second}; max {mx7}")
        self.orb_off("hwp_fs_reload_over")

        # without the orb: the bar still shows (white, no gold) for the automatic and a manual
        # reload, just above the HUD's health bar
        self.gl("givestacks", self.CLIP, -999)
        time.sleep(0.4)
        self.g.shot("reload-bar-plain", settle=False)
        plain_auto = bar()
        time.sleep(2.2)
        self.ready("hwp_fs_reload")
        self.gl("givestacks", self.CLIP, -10)
        self.gl("input", 60, 0, 0, d[0], d[1], "skill1")
        time.sleep(0.3)
        self.g.shot("reload-bar-manual", settle=False)
        plain_manual = bar()
        time.sleep(2.0)
        self.flag("reload_bar_without_orb", "now auto, white, gold no" in plain_auto and "now manual, white, gold no" in plain_manual
                  and "health bar none" not in plain_auto, f"{plain_auto!r} / {plain_manual!r}")

        def frag(orb, secs, land=0.9):
            ok, _ = self.orb(orb)
            dd, (du,) = self.line_dummies(d, [90])
            self.top_up()
            self.gl("castat", "hwp_fs_frag", dd[0] * 90, dd[1] * 90, "nocd")
            time.sleep(land)  # the throw lands ~0.8 s after the cast (castpoint 150, arc 650)
            h0 = self.hps([du])[du]
            _, tags, h1 = self.dummy_watch(du, secs)
            self.orb_off(orb)
            return ok, h0, h1, tags

        # level 1 stuns and slows for 1 s from the landing: watch from before it lands (run
        # 20261019-014544 read the tags from ~1.5 s, after the hp read, and saw none)
        ok, h0, h1, tags = frag("hwp_fs_frag_stun", 1.4, land=0.2)
        self.flag("stun_grenade_stuns", ok and ("stun" in tags or "slow" in tags), f"dummy buffs {tags}, hp {h0} -> {h1}")
        ok, h0, h1, tags = frag("hwp_fs_frag_fire", 2.5)
        self.flag("incendiary_burns", ok and h1 < h0 - 0.001, f"hp after the blast {h0} -> {h1} 2.5 s later, buffs {tags}")
        ok, h0, h1, tags = frag("hwp_fs_frag_gas", 2.5)
        self.flag("gas_lingers", ok and h1 < h0 - 0.001, f"hp after the blast {h0} -> {h1} 2.5 s later, buffs {tags}")
        self.clear_dummies()
        self.to_town()

    def firearms_assault(self):
        """firearms s4 for Assault. Double Barrel Burst fires two shells (logged by
        HWPFirearmsShotgun: "shotgun: N hit, M within R at xMUL"), a dummy 60 px out is in
        close range (80 at level 1, x1.5); Triple Barrel fires three; Dragon's Breath logs its
        burning ground. Adrenaline is passive and a kill gives a stack."""
        self.new_char("LabAssault", "hwp_firearms_assault")
        if not self.enter_floor("assault"):
            return
        dirs = self.open_dirs(130)
        d = dirs[0]
        if self.level("adrenaline", "hwp_fs_adrenaline"):
            e = self.entry(self.bar(), "hwp_fs_adrenaline")
            self.flag("adrenaline_passive", e.get("mode") == 0 and not e.get("button"), f"{e}")
            self.gl("spawn", BRUTE, round(d[0] * 60, 1), round(d[1] * 60, 1))
            time.sleep(0.4)
            a0 = self.stacks("adrenaline")
            self.gl("kill", 300, "bandit_brute", "me")
            time.sleep(0.5)
            a1 = self.stacks("adrenaline")
            self.flag("adrenaline_on_kill", a1 == a0 + 1, f"adrenaline {a0} -> {a1} after a kill")
        if self.level("burst", "hwp_fs_burst"):
            pos = self.log_pos()
            self.direction_test("burst", "hwp_fs_burst", "assault_burst.sval", d, dist=60)
            time.sleep(0.3)
            shells = re.findall(r"shotgun: (\d+) hit, (\d+) within (\d+) at x([\d.]+)", self.log_from(pos))
            self.flag("burst_two_shells", len(shells) == 2, f"{shells}")
            self.flag("burst_close_range", bool(shells) and all(x[1] == "1" and x[2] == "80" and x[3].startswith("1.5") for x in shells),
                      f"{shells}")
            for orb, want, tag in (("hwp_fs_burst_triple", 3, "triple_barrel_three"), ("hwp_fs_burst_breath", 2, "dragons_breath_ground")):
                ok, lvl = self.orb(orb)
                dd, (du,) = self.line_dummies(d, [60])
                self.top_up()
                pos = self.log_pos()
                self.aimed_cast("hwp_fs_burst", dd, 800)
                time.sleep(0.8)
                log = self.log_from(pos)
                n = len(re.findall(r"shotgun: \d+ hit", log))
                fire = len(re.findall(r"shotgun: .*burning ground", log))
                self.flag(tag, ok and n == want and (tag != "dragons_breath_ground" or fire >= 1),
                          f"orb level {lvl}: {n} shells, {fire} with burning ground")
                self.orb_off(orb)
        self.buttons_flag("assault", d)
        self.clear_dummies()
        self.to_town()


    # --- Engineer
    def turrets(self):
        """The local player's turrets near: (unit id, hp fraction) each."""
        return [(u["unit"], u.get("hp", 1.0)) for u in self.gl("near", 400, TURRET).get("units") or []
                if not u.get("dead")]

    def place(self, d, dist=80, nocd=True):
        """A turret dist along d (castat: the cast PlayerTargetingHelper makes), and the log
        line it logged ("turret: placed, N hp (+P% ...), a shot every R ms")."""
        self.g.console("cht_give_mana 999")
        time.sleep(0.2)
        pos = self.log_pos()
        self.gl("castat", "hwp_fs_turret", round(d[0] * dist, 1), round(d[1] * dist, 1), *(["nocd"] if nocd else []))
        m = self.wait_log(r"turret: placed, (\d+) hp \(\+(\d+)% of the owner's\), a shot every (\d+) ms", pos, 3)
        time.sleep(0.4)
        return m

    def firearms_engineer(self):
        """Engineer: Deploy Turret (Skill3, TargetAOE) places a turret where aimed, costs its
        tooltip mana and starts its 12 s cooldown; the turret shoots an enemy, wears down
        (30 s for its whole bar) and one turret replaces the last; Second Turret keeps two
        (a third replaces the oldest); Reinforced Turret adds 75% of the player's max HP.
        My Turret! is passive: near it the turret is repaired and boosted (logged), Elemental
        Belt-Feed's chance comes with the boost. Our Turret! needs a second player: not run."""
        self.new_char("LabEngineer", "hwp_firearms_engineer")
        if not self.enter_floor("engineer"):
            return
        d = self.open_dirs(130)[0]
        if not self.level("turret", "hwp_fs_turret"):
            return
        self.top_up()
        pos = self.log_pos()
        w = self.cast_watch("hwp_fs_turret", lambda: self.targeted("skill3", d[0] * 80, d[1] * 80, (0, 120)), secs=1.4)
        m = self.wait_log(r"turret: placed, (\d+) hp \(\+(\d+)% of the owner's\), a shot every (\d+) ms", pos, 2)
        t = self.turrets()
        px, py = self.pos()
        at = [(round(u["x"] - px), round(u["y"] - py)) for u in self.gl("near", 400, TURRET).get("units") or []]
        self.flag("turret_casts", w["cd"] > 0 and len(t) == 1 and m is not None and m.group(3) == "600",
                  f"cooldown {w['cd']}, turrets {t} at {at} (aimed {round(d[0] * 80)},{round(d[1] * 80)}), log {m and m.group(0)}")
        self.flag("turret_where_aimed", len(at) == 1 and math.hypot(at[0][0] - d[0] * 80, at[0][1] - d[1] * 80) < 20, f"{at}")
        self.cost_flag("turret", "hwp_fs_turret", "engineer_turret.sval", w)

        # wears down: no passive yet, so nothing repairs it
        h0 = self.turrets()
        time.sleep(3.0)
        h1 = self.turrets()
        drop = (h0[0][1] - h1[0][1]) / 3.0 if h0 and h1 else 0
        self.flag("turret_decays", 0.025 < drop < 0.045, f"hp {h0} -> {h1} over 3 s: {round(drop, 4)}/s (1/30 = 0.0333)")

        # shoots an enemy beside it (god mode keeps the player up; the brute may hit the turret)
        tu = self.gl("near", 400, TURRET).get("units") or []
        if tu:
            # 50 past it: 130 out, inside the line open_dirs checked (70 past, a brute landed in a
            # wall out of the turret's sight, 20261019-210718 and -211402)
            ex, ey = tu[0]["x"] - px + d[0] * 50, tu[0]["y"] - py + d[1] * 50
            e = self.gl("spawn", BRUTE, round(ex, 1), round(ey, 1)).get("unit")
            time.sleep(0.3)
            b0 = [u.get("hp", 1.0) for u in self.gl("near", 600, "bandit_brute").get("units") or []]
            time.sleep(3.0)
            b1 = [(u.get("hp", 1.0), u.get("dead")) for u in self.gl("near", 600, "bandit_brute").get("units") or []]
            self.flag("turret_shoots", bool(b0) and (not b1 or b1[0][1] or b1[0][0] < b0[0] - 0.001),
                      f"brute {e} hp {b0} -> {b1} over 3 s")
            self.gl("kill", 800, "bandit_brute")
            time.sleep(0.3)

        # one at a time: a second placement replaces the first
        self.place(d)
        n1 = len(self.turrets())
        ok2, _ = self.orb("hwp_fs_turret_second")
        self.place(d, 60)
        n2 = len(self.turrets())
        self.place(d, 100)
        n3 = len(self.turrets())
        self.flag("turret_one_at_a_time", n1 == 1, f"{n1} after a second placement")
        self.flag("second_turret_two", ok2 and n2 == 2 and n3 == 2, f"orb {ok2}: {n2} after two, {n3} after three")
        self.orb_off("hwp_fs_turret_second")

        ok, lvl = self.orb("hwp_fs_turret_reinforced", 3)
        mx = self.gl("state").get("player", {}).get("hpMax") or 0
        m = self.place(d)
        hp = int(m.group(1)) if m else 0
        self.flag("reinforced_turret_hp", ok and m is not None and m.group(2) == "75" and hp > 100,
                  f"orb level {lvl}, player max hp {mx}, log {m and m.group(0)}")
        self.orb_off("hwp_fs_turret_reinforced")

        if self.level("myturret", "hwp_fs_myturret"):
            e = self.entry(self.bar(), "hwp_fs_myturret")
            self.flag("myturret_passive", e.get("mode") == 0 and not e.get("button"), f"{e}")
            ok, lvl = self.orb("hwp_fs_myturret_feed", 3)
            pos = self.log_pos()
            self.place(d, 40)
            b = self.wait_log(r"turret: boosted by [^,]*, \+(\d+) hp/s, \+(\d+)% damage, (\d+)% elemental", pos, 3)
            self.flag("myturret_boosts", b is not None and b.group(1) == "10" and b.group(2) == "10",
                      f"log {b and b.group(0)}")
            self.flag("belt_feed_chance", ok and b is not None and b.group(3) == "60", f"orb level {lvl}, log {b and b.group(0)}")
            self.gl("kill", 400, TURRET, 0.5)
            time.sleep(0.3)
            r0 = self.turrets()
            time.sleep(2.0)
            r1 = self.turrets()
            rise = (r1[0][1] - r0[0][1]) / 2.0 if r0 and r1 else 0
            # 10 hp/s on a 100 hp turret, less 1/30 a second of decay: +0.067/s
            self.flag("myturret_repairs", 0.045 < rise < 0.09, f"hp {r0} -> {r1} over 2 s: {round(rise, 4)}/s")
            glow = [bf for ac in self.gl("actorbuffs", 400, TURRET).get("actors") or [] for bf in ac.get("buffs") or []]
            # actorbuffs gives no name for a buff without one: turret_glow is the 300 ms buff
            self.flag("myturret_glows", any(not bf.get("debuff") and 0 < bf.get("left", 0) <= 300 for bf in glow),
                      f"turret buffs {glow}")
            # NEAR is 60 px: a turret placed 120 px out along the open direction (it replaces the
            # first) is not boosted until the player walks up to it
            pos = self.log_pos()
            far = self.place(d, 120)
            time.sleep(1.0)
            early = self.wait_log(r"turret: boosted by", pos, 0.1)
            p0 = self.gl("state").get("player") or {}
            tu = [(u.get("x"), u.get("y")) for u in self.gl("near", 400, TURRET).get("units") or []]
            pos = self.log_pos()
            self.gl("input", 1500, d[0], d[1], d[0], d[1])
            on = self.wait_log(r"turret: boosted by", pos, 2.5)
            p1 = self.gl("state").get("player") or {}
            self.flag("myturret_only_near", far is not None and early is None and on is not None,
                      f"placed at 120: {far and far.group(0)}, boosted then: {early and early.group(0)}, "
                      f"after walking up: {on and on.group(0)}; turrets at {tu}, player "
                      f"{p0.get('x')},{p0.get('y')} -> {p1.get('x')},{p1.get('y')}")
            self.orb_off("hwp_fs_myturret_feed")
        self.buttons_flag("engineer", d)
        self.gl("kill", 400, TURRET)
        self.clear_dummies()
        self.to_town()


    # --- the pistol's raised arm (Combat.as AimHold)
    def firearms_pistol_arm(self):
        """After a rifle or pistol shot the arm stays up (logged "gun arm: held") and comes down
        1 s after the last shot, or at once on a dodge or a reload. Frames per gun: the arm
        0.4 s after a shot (up), and after it is lowered."""
        self.gl("char", "hwp_firearms", "LabArm")
        self.wait_phase("town", 60)
        time.sleep(2)
        if not self.enter_floor("arm"):
            return
        for gun, item in (("rifle", "hwp_rifle_01"), ("pistol", "hwp_glock_mh_01")):
            self.gun_arm(gun, item)
        self.to_town()

    def gun_arm(self, gun, item):
        eq = self.gl("equip", item, "common").get("ok")
        time.sleep(1.0)
        lowered = r"gun arm: lowered \(([^)]*)\)"

        def shoot():
            self.gl("givestacks", self.CLIP, 999)
            pos = self.log_pos()
            self.gl("input", 60, 0, 0, 1, 0, "main")
            m = self.wait_log(r"gun arm: held", pos, 2.0)
            return pos, m, time.time()

        pos, held, t0 = shoot()
        time.sleep(0.4)
        self.g.shot(f"{gun} arm held")
        low = self.wait_log(lowered, pos, 3.0)
        dt = time.time() - t0
        time.sleep(0.6)
        self.g.shot(f"{gun} arm lowered")
        self.flag(f"{gun}_arm_held", bool(eq) and held is not None, f"equip {eq}, log {held and held.group(0)}")
        self.flag(f"{gun}_arm_lowers_after_1s", low is not None and "without a shot" in low.group(1) and 0.7 < dt < 1.8,
                  f"{low and low.group(0)} {round(dt, 2)} s after the shot was held")
        time.sleep(0.5)
        pos, held, t0 = shoot()
        self.gl("input", 120, 0, 1, 0, 1, "dash")
        low = self.wait_log(lowered, pos, 1.5)
        self.flag(f"{gun}_arm_lowers_on_dodge", held is not None and low is not None and "skill" in low.group(1)
                  and time.time() - t0 < 0.9, f"{low and low.group(0)}")
        time.sleep(1.0)
        pos, held, t0 = shoot()
        self.gl("givestacks", self.CLIP, -999)
        low = self.wait_log(lowered, pos, 1.5)
        self.flag(f"{gun}_arm_lowers_on_reload", held is not None and low is not None and low.group(1) == "reloading",
                  f"{low and low.group(0)}")
        time.sleep(1.5)


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
