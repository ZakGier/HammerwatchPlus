"""Test-plan checks for the classes mod's masteries (plan steps classes.s5 and classes.s6).

classes.s5: at level 20 (hwp levelup 20) each HoH1 class (Thief, Gladiator, Witch Hunter) has
three specs at the Subclass Picker, and the self-buff skills (Slice and Dice, Cloak of Shadows,
Shield Wall, Immolation) show their buff with a HUD icon for the listed time.
classes.s6: the Priest and the Paladin get a 4th spec, Smiter (Smite, Divine Hammer, Last
Rites) and Holy Storm (Holy Storm, Shield of Faith, Zealous Charge), and the skills cast.

Sections: thief_specs, gladiator_specs, witchhunter_specs (s5), priest_smiter,
paladin_holystorm (s6). Each makes its own fresh character with `gl char`.

The picker is the town's npc_subclass_picker (Town/SubclassPickShopContent.as): its
`class-curr` TextWidget names the shown subclass, OnFunc "nextclass" steps it. Skills are
cast with `gl input` buttons in a Bandit Keep floor. The buffs / skills / hurt verbs are
mods/gamelab-hands/scripts/GameLab/Verbs_classesb.as: buffs gives each buff's ms left, the
def's duration, the HUD icon and the scene time; skills gives each live skill's cooldown and
the button GetSkillInput maps it to. Without them the checks fall back to `gl state` buffs,
`gl clock` and mana."""
import re
import time

from gamelab.bots import picker_skills
from gamelab.bots.plan_checks import Checks as Base

DUMMY = "actors/humans/bandits/bandit_brute.unit"


class Checks(Base):
    # --- plumbing
    def god(self, on=True):
        """hwp god toggles the cht_god cvar; toggle until it reads `on`."""
        for _ in range(3):
            m = re.findall(r"god mode (on|off)", self.hwp("god", 0.4, until="god mode"))
            if m and (m[-1] == "on") == on:
                return True
        return False

    HOLD = 320  # ms: past every cast point / update-aim window tested here (80-200 ms) + 80

    def press(self, button, wait=0.6, aim=(1, 0)):
        """One emulated press (Pressed on the first frame only), held past the skill's cast
        point: once the emulated aim lets go, the aim follows the real mouse cursor."""
        self.gl("input", self.HOLD, 0, 0, aim[0], aim[1], button)
        time.sleep(wait)

    def mana_exact(self):
        return self.gl("state").get("player", {}).get("manaExact", self.mana())

    def spent_enough(self, m0, cost):
        """Mana fell by most of the skill's cost (sval mana-cost x the modifiers' manaCostMul):
        the cast signal for a skill whose cooldown can't be read."""
        mul = self.gl("state").get("player", {}).get("manaCostMul", 1.0) or 1.0
        return m0 - self.mana_exact() >= cost * mul * 0.8

    def started(self, skill_id):
        """The skill's cooldown is running (skills verb); None when it can't be read (no verb,
        or cd -1: a class with no cooldown counter the verb knows)."""
        cd = self.skill_cd(skill_id)
        if cd is None or cd < 0:
            return None
        return cd > 0

    def buff_poll(self):
        """(scene ms, {name key: entry}) from the buffs verb; entries carry dur/left/hud/icon/num.
        Fallback: gl state names and gl clock, entries with left None."""
        r = self.gl("buffs")
        if "buffs" in r:
            return r.get("now"), {b["name"]: b for b in r["buffs"]}
        names = self.gl("state").get("player", {}).get("buffs") or []
        now = self.gl("clock").get("sceneMs")
        return now, {n: {"name": n, "dur": None, "left": None, "hud": None, "icon": None, "num": ""} for n in names}

    def skills_info(self):
        """{skill id: {type, mode, cd, button}} from the skills verb, or None without it."""
        r = self.gl("skills")
        if "skills" not in r:
            return None
        return {s["id"]: s for s in r["skills"]}

    def skill_cd(self, skill_id):
        info = self.skills_info()
        if info is None or skill_id not in info:
            return None
        return info[skill_id].get("cd")

    def button_for(self, tag, skill_id, fallback):
        """The button the game maps the skill to (skills verb), and a flag that no other live
        active skill listens on it: GetSkillInput puts the 3rd and every later active spell
        on Skill3, where the first one in m_skills order takes the press."""
        info = self.skills_info()
        if info is None:
            self.notes.append(f"{tag}: no skills verb, assuming {skill_id} on {fallback}")
            return fallback
        e = info.get(skill_id)
        btn = e.get("button") if e else ""
        shared = [k for k, v in info.items() if k != skill_id and btn and v.get("button") == btn]
        self.flag(f"{tag}_own_button", bool(e) and bool(btn) and not shared,
                  f"{skill_id} on {btn or '-'}, also on it: {shared}; live skills "
                  f"{[(k, v.get('button')) for k, v in info.items()]}")
        return btn or fallback

    def cast(self, skill_id, button, cost, done=None, aim=(1, 0)):
        """Press `button` until `skill_id` has cast: its cooldown started (skills verb), `done()`
        holds, or (no `done`) mana fell by most of its cost. With `done` (a self-buff) mana is not
        a signal: the Thief's Smoke Bomb, on the same button, costs as much. A press a TargetAOE skill took (it then waits
        for the attack button) is confirmed with "main", then the button is pressed once more.
        Returns (presses of `button` it took, 0 when it never cast; mana spent)."""
        m0 = self.mana_exact()

        def cast_done():
            if done and done():
                return True
            if self.started(skill_id):
                return True
            return done is None and self.spent_enough(m0, cost)

        for attempt in (1, 2, 3):
            self.press(button, aim=aim)
            if cast_done():
                return attempt, round(m0 - self.mana_exact(), 1)
            self.press("main", 0.8, aim=aim)  # fire whatever targeting skill took the press
            if cast_done():
                return attempt, round(m0 - self.mana_exact(), 1)
        self.press("off", 0.3)  # cancel a targeting left open
        return 0, round(m0 - self.mana_exact(), 1)

    def dummies(self, r=300):
        return [u for u in self.gl("near", r, "bandit_brute").get("units") or []]

    def dummy_hit(self, before):
        """Did a dummy alive in `before` lose HP or die."""
        now = {u["unit"]: u for u in self.dummies()}
        for u in before:
            v = now.get(u["unit"])
            if v is None or v.get("dead") or v.get("hp", 1) < u.get("hp", 1) - 0.001:
                return True
        return False

    def fresh_dummy(self, dx, dy=0):
        self.gl("kill", 600, "bandit_brute")
        time.sleep(0.3)
        self.gl("spawn", DUMMY, dx, dy)
        time.sleep(0.6)
        return [u for u in self.dummies() if not u.get("dead")]

    def new_char(self, cls, name):
        r = self.gl("char", cls, name)
        self.wait_phase("town", 60)
        time.sleep(2)
        lv = self.hwp("levelup 20", 1.0, until="now level")
        pl = self.gl("state").get("player", {})
        return r, pl, lv

    def picker(self, count):
        """Open the Subclass Picker (spawned beside the player when the town lacks it) and step
        through it with OnFunc "nextclass": the subclass names it shows, in order. Each one's
        skill row (picker_skills.read_row) goes in self.picker_rows by name."""
        self.npc("npc_subclass_picker", "actors/npcs/town/npc_subclass_picker.unit")
        u = self.gl("use", "npc_subclass_picker")
        time.sleep(0.8)
        win = self.gl("state").get("window")
        names = []
        self.picker_rows = {}
        for _ in range(count + 2):
            roots = self.gl("widgets", 12).get("roots", [])
            curr = next((n.get("text", "") for r in roots for n in r.get("nodes", []) if n.get("id") == "class-curr"), "")
            names.append(curr)
            self.picker_rows.setdefault(curr, picker_skills.read_row(roots))
            self.gl("func", "nextclass")
            time.sleep(0.3)
        if self.gl("state").get("window"):
            self.g.key("escape")
            time.sleep(0.5)
        distinct = []
        for n in names:
            if n and n not in distinct:
                distinct.append(n)
        self.notes.append(f"picker: use {u.get('ok')} window {win}, shown {names}")
        return distinct

    def enter_floor(self, tag):
        if not self.start_floor(0):
            self.flag(f"{tag}_mission", False)
            return False
        self.god(True)
        self.gl("kill", 6000, "tag:enemy")  # an empty floor: nothing hits or blocks the casts
        time.sleep(1)
        return True

    def watch_buff(self, name, listed, first):
        """Poll from the first reply that had the buff (`first` = (now, entries)) until it is
        gone. The buff's own clock (ActorBuff.m_duration counts down in scene ms) dates the
        cast: cast_at = now - (dur - left). It expired between the last poll that had it and
        the first that didn't."""
        now, ent = first
        b = ent[name]
        dur, left0 = b.get("dur"), b.get("left")
        cast_at = now - (dur - left0) if dur is not None and left0 is not None and now is not None else now
        last, gone = now, None
        icons, huds, nums = [b.get("icon")], [b.get("hud")], [b.get("num")]
        end = time.time() + listed / 1000 + 8
        while time.time() < end:
            now, ent = self.buff_poll()
            if name in ent:
                last = now
                icons.append(ent[name].get("icon"))
                huds.append(ent[name].get("hud"))
                nums.append(ent[name].get("num"))
            else:
                gone = now
                break
            time.sleep(0.1)
        return {"dur": dur, "left0": left0, "cast_at": cast_at, "last": last, "gone": gone,
                "icons": icons, "huds": huds, "nums": nums}

    def buff_test(self, tag, skill_id, buff, listed, fallback_button, cost):
        """Cast a self-buff skill and time its buff: present with a HUD icon from the cast for
        the listed ms (the def's duration is the listed one, and it expired in the window the
        polls bracket, give or take a frame)."""
        button = self.button_for(tag, skill_id, fallback_button)
        state = {}

        def seen():
            p = self.buff_poll()
            if buff in p[1]:
                state["first"] = p
                return True
            return False

        presses, spent = self.cast(skill_id, button, cost, done=seen)
        if "first" not in state and presses:
            seen()  # the cooldown said it cast; one more look for the buff
        self.flag(f"{tag}_cast", "first" in state,
                  f"{skill_id} on {button}: {presses} press(es) (0 = never cast), mana -{spent}")
        if "first" not in state:
            self.flag(f"{tag}_icon", False, "no buff")
            self.flag(f"{tag}_duration", False, "no buff")
            return
        w = self.watch_buff(buff, listed, state["first"])
        known = w["cast_at"] is not None
        lo = w["last"] - w["cast_at"] if known and w["last"] is not None else None
        hi = w["gone"] - w["cast_at"] if known and w["gone"] is not None else None
        self.flag(f"{tag}_icon", all(w["huds"]) and all(w["icons"]),
                  f"hud icon def {set(w['huds'])}, HUD widget visible {set(w['icons'])}, num {w['nums'][:3]}..{w['nums'][-2:]}")
        ok = (w["dur"] in (None, listed) and lo is not None and hi is not None
              and lo <= listed + 50 and hi >= listed - 50 and hi - lo <= 2500)
        self.flag(f"{tag}_duration", ok,
                  f"def {w['dur']} ms (listed {listed}), left {w['left0']} at first look; "
                  f"shown {lo}..{hi} ms after the cast (scene clock)")

    def labels_flag(self, key, ids):
        """The picker's skill row for each spec id: its own skills, each labelled by its real
        type (core SubclassPick.as; vanilla labels the last two defs Active/Passive)."""
        probs = {}
        for sub in ids:
            defs = self.gl("classskills", sub)
            row = self.picker_rows.get(defs.get("name"), [])
            probs[sub] = picker_skills.row_problems(row, defs) if defs.get("ok") else [f"classskills: {defs.get('error')}"]
        self.flag(f"{key}_picker_skill_labels", not any(probs.values()),
                  f"rows {self.picker_rows}; problems {probs}")

    def specs_s5(self, key, cls, ids, names):
        """Character, level 20, the picker's three specs, every spec id taken by ChangeClass."""
        r, pl, lv = self.new_char(cls, "Lab" + key.capitalize())
        self.flag(f"{key}_char", r.get("ok") and pl.get("class") == cls, f"{r} class {pl.get('class')}")
        self.flag(f"{key}_level20", pl.get("level", 0) >= 20, f"level {pl.get('level')}: {lv.strip()[-60:]}")
        shown = self.picker(len(names))
        self.flag(f"{key}_three_specs", len(shown) == 3 and set(shown) == set(names),
                  f"picker {shown}, sval {names}")
        self.labels_flag(key, ids)
        took = [self.gl("subclass", i).get("class") for i in ids]
        self.flag(f"{key}_subclass_ids", took == ids, f"{took}")

    # --- classes.s5
    def thief_specs(self):
        st = self.hwp("classes", 0.5, until="HoH1 classes")
        self.flag("hoh1_classes_status", "3/3 registered (9 subclasses)" in st, st.strip()[-120:])
        self.specs_s5("thief", "hwp_thief", ["hwp_thief_assassin", "hwp_thief_trickster", "hwp_thief_shadow"],
                      ["Assassin", "Trickster", "Shadow"])
        self.gl("subclass", "hwp_thief_trickster")
        self.hwp("skillpoints 30")
        sk = self.gl("skill", "hwp_thief_slice", 1)
        self.flag("slice_learned", sk.get("level", 0) >= 1, f"{sk}")
        if not self.enter_floor("thief"):
            return
        # knives, hook and smoke are learned at level 1, so Slice is the 4th active spell: core's
        # extra key hwp_skill4 (SkillKeys.as; vanilla would share Skill3 with Smoke Bomb)
        self.buff_test("slice", "hwp_thief_slice", ".skills.hwp_thief.slice.name", 6000, "skill3", 10)
        sc = self.gl("subclass", "hwp_thief_shadow")
        self.hwp("skillpoints 30")
        sk = self.gl("skill", "hwp_thief_cloak", 1)
        self.flag("cloak_learned", sc.get("class") == "hwp_thief_shadow" and sk.get("level", 0) >= 1, f"{sc} {sk}")
        time.sleep(1)
        self.buff_test("cloak", "hwp_thief_cloak", ".skills.hwp_thief.cloak.name", 2500, "skill3", 8)
        self.to_town()

    def gladiator_specs(self):
        self.specs_s5("gladiator", "hwp_gladiator",
                      ["hwp_gladiator_champion", "hwp_gladiator_beastmaster", "hwp_gladiator_retiarius"],
                      ["Champion", "Beastmaster", "Retiarius"])
        self.gl("subclass", "hwp_gladiator_champion")
        self.hwp("skillpoints 30")
        sk = self.gl("skill", "hwp_gladiator_shield_wall", 1)
        self.flag("shield_wall_learned", sk.get("level", 0) >= 1, f"{sk}")
        if not self.enter_floor("gladiator"):
            return
        # net and gladius are the two base actives: Shield Wall is the 3rd (Skill3, alone)
        self.buff_test("shield_wall", "hwp_gladiator_shield_wall", ".skills.hwp_gladiator.shield_wall.name",
                       5000, "skill3", 10)
        self.to_town()

    def witchhunter_specs(self):
        self.specs_s5("witchhunter", "hwp_witch_hunter",
                      ["hwp_witch_hunter_inquisitor", "hwp_witch_hunter_pyromancer", "hwp_witch_hunter_hunter"],
                      ["Inquisitor", "Pyromancer", "Hunter"])
        self.gl("subclass", "hwp_witch_hunter_pyromancer")
        self.hwp("skillpoints 30")
        sk = self.gl("skill", "hwp_witch_hunter_immolation", 1)
        self.flag("immolation_learned", sk.get("level", 0) >= 1, f"{sk}")
        if not self.enter_floor("witchhunter"):
            return
        # pyre is the only base active at level 1 (ward starts at 0): Immolation on Skill2
        self.buff_test("immolation", "hwp_witch_hunter_immolation", ".skills.hwp_witch_hunter.immolation.name",
                       8000, "skill2", 12)
        self.to_town()

    # --- classes.s6
    def specs_s6(self, key, cls, spec_id, spec_name, skills):
        """Character, level 20, a 4th spec at the picker, the spec taken, its 3 skills learned."""
        r, pl, lv = self.new_char(cls, "Lab" + key.capitalize())
        self.flag(f"{key}_char", r.get("ok") and pl.get("class") == cls, f"{r} class {pl.get('class')}")
        shown = self.picker(4)
        self.flag(f"{key}_four_specs", len(shown) == 4 and spec_name in shown, f"picker {shown}")
        self.labels_flag(key, [spec_id])
        sc = self.gl("subclass", spec_id)
        self.hwp("skillpoints 30")
        lv = {s: self.gl("skill", s, 1).get("level", 0) for s in skills}
        self.flag(f"{key}_spec_learned", sc.get("class") == spec_id and all(v >= 1 for v in lv.values()),
                  f"{sc.get('class')} {lv}")
        return sc.get("class") == spec_id

    def damage_cast(self, tag, skill_id, fallback_button, cost, dist, cooldown, hold=500):
        """A fresh dummy `dist` along the aim and the press in one frame (gl multi: a dummy
        walks and steers in the ~0.3 s a gl command takes). Hit: the dummy lost HP or died
        (gone from `near`); a hit is also proof of the cast. A spawn a wall pushed away gets the
        next direction, after the skill's cooldown. The press is held `hold` ms: past the cast
        point, so the aim stays the emulated one (it falls back to the real mouse after)."""
        button = self.button_for(tag, skill_id, fallback_button)
        presses, spent, hit, seen = 0, 0.0, False, []
        for aim in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            self.gl("kill", 600, "bandit_brute")
            time.sleep(0.4)
            m0 = self.mana_exact()
            self.gl("multi", "spawn", DUMMY, aim[0] * dist, aim[1] * dist, "+",
                    "input", hold, 0, 0, aim[0], aim[1], button)
            time.sleep(hold / 1000 + 0.7)  # cast point, projectiles in flight
            started = self.started(skill_id)
            paid = self.spent_enough(m0, cost)
            now = self.dummies()
            struck = not now or any(u.get("dead") or u.get("hp", 1) < 0.999 for u in now)
            seen.append((aim, self.skill_cd(skill_id), round(m0 - self.mana_exact(), 1),
                         [(round(u.get("hp", 1), 3), u.get("dead")) for u in now]))
            if started or paid or struck:
                presses, spent = presses or 1, max(spent, round(m0 - self.mana_exact(), 1))
            if struck:
                hit = True
                break
            time.sleep(cooldown / 1000 + 0.2)
        if not presses:
            # never cast from the one-frame press: the plain press loop (and a targeting confirm)
            self.fresh_dummy(dist)
            presses, spent = self.cast(skill_id, button, cost)
        self.flag(f"{tag}_cast", presses > 0, f"{skill_id} on {button}: {presses} press(es), mana -{spent}")
        self.flag(f"{tag}_hits", hit, f"dummy at {dist}: (aim, cooldown left, mana spent, dummies hp/dead) {seen}")

    def hp(self):
        pl = self.gl("state").get("player", {})
        return pl.get("hp", 0), pl.get("hpMax", 0)

    def priest_smiter(self):
        skills = ["hwp_priest_hoh1_smite", "hwp_priest_hoh1_divine_hammer", "hwp_priest_hoh1_last_rites"]
        if not self.specs_s6("priest", "priest", "hwp_priest_hoh1", "Smiter", skills):
            return
        if not self.enter_floor("priest"):
            return
        # inner light is the base active (consecrated ground starts at 0, divine protection is
        # passive): Smite on Skill2, Divine Hammer on Skill3
        self.damage_cast("smite", "hwp_priest_hoh1_smite", "skill2", 10, 28, 1500)
        # 40, not 60: the right-hand whirling axe curves off a straight line as it flies
        self.damage_cast("hammer", "hwp_priest_hoh1_divine_hammer", "skill3", 12, 40, 4000)
        # Last Rites: every kill heals 8 (level 1) in 80 around you. Hurt, time the regen alone,
        # then a credited kill (gl kill ... me runs PlayerKilledActor: Kill trigger) and compare
        self.gl("kill", 600, "bandit_brute")
        before = self.fresh_dummy(40)
        h = self.gl("hurt", 0.5)
        if "hp" not in h:
            self.flag("last_rites_heals", False, f"no hurt verb: {h}")
        else:
            time.sleep(0.3)
            a0 = self.hp()[0]
            t0 = time.time()
            time.sleep(1.0)
            a1 = self.hp()[0]
            regen = (a1 - a0) / max(0.1, time.time() - t0)
            self.gl("hurt", 0.5)
            time.sleep(0.2)
            b0 = self.hp()[0]
            t1 = time.time()
            k = self.gl("kill", 300, "bandit_brute", "me")
            time.sleep(0.6)
            b1, mx = self.hp()
            gain = b1 - b0 - regen * (time.time() - t1)
            self.flag("last_rites_heals", bool(before) and k.get("killed", 0) >= 1 and gain >= 5,
                      f"kill {k.get('killed')}: hp {b0} -> {b1}/{mx}, regen alone {regen:.1f}/s, kill heal ~{gain:.1f} (8 listed)")
            self.gl("hurt", 1)
        self.to_town()

    def paladin_holystorm(self):
        skills = ["hwp_paladin_hoh1_holy_storm", "hwp_paladin_hoh1_shield_of_faith", "hwp_paladin_hoh1_zealous_charge"]
        if not self.specs_s6("paladin", "paladin", "hwp_paladin_hoh1", "Holy Storm", skills):
            return
        if not self.enter_floor("paladin"):
            return
        # blessed strikes is the base active (lay on hands starts at 0): Holy Storm on Skill2,
        # Shield of Faith on Skill3, Zealous Charge on core's extra key hwp_skill4 (vanilla: Skill3 too)
        self.damage_cast("holy_storm", "hwp_paladin_hoh1_holy_storm", "skill2", 20, 40, 8000)
        self.gl("kill", 600, "bandit_brute")
        self.buff_test("sof", "hwp_paladin_hoh1_shield_of_faith", ".skills.hwp_paladin_hoh1.shield_of_faith.name",
                       6000, "skill3", 15)
        # its own key (skills verb); on a shared Skill3 only Shield of Faith's cooldown would let it through
        button = self.button_for("charge", "hwp_paladin_hoh1_zealous_charge", "skill3")
        before = self.fresh_dummy(90)
        pl0 = self.gl("state").get("player", {})
        m0 = self.mana_exact()
        presses, spent = self.cast("hwp_paladin_hoh1_zealous_charge", button, 12)
        time.sleep(0.6)  # the 450 ms leap
        pl1 = self.gl("state").get("player", {})
        moved = ((pl1.get("x", 0) - pl0.get("x", 0)) ** 2 + (pl1.get("y", 0) - pl0.get("y", 0)) ** 2) ** 0.5
        # the leap itself is the proof it cast; the button flag (charge_own_button) is separate
        self.flag("charge_cast", presses > 0 or moved >= 20 or self.spent_enough(m0, 12),
                  f"on {button}: {presses} press(es), mana -{spent}, moved {moved:.0f} px")
        self.flag("charge_leaps", moved >= 20, f"moved {moved:.0f} px")
        # the leap's target is TargetAOE's CalcMouseTargetPos (the real cursor, PlayerTargetingHelper.as:262)
        # unless the input is a gamepad's; the emulated aim doesn't move it, so no hit is required
        self.notes.append(f"charge dummy hit {bool(before) and self.dummy_hit(before)}")
        self.to_town()


def run(p, sections="thief_specs,gladiator_specs,witchhunter_specs", **_):
    c = Checks(p)
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
