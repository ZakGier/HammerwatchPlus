"""Test-plan checks for the Firearms orbs plan_firearms leaves out: Elemental Bullets and its
seven orbs, Extended Clip Crit and Extended Crit Chance, Shrapnel (frag), BOOM Headshot! and
Elemental Exposure (Critical Aim), Overpacked Explosives, Elemental Shrapnel and Rocket Jump
(Demolitionist), Critical Focus and EpiPen (Adrenaline), Our Turret! (My Turret!).

What each check reads:
- Element weights: `hwp firearms elements roll N` runs RollElement, the roll every gun shot
  makes (Elemental.as HWPFirearmsGunShot.DoAction), N times on the live stats; real shots are
  tallied by `hwp firearms elements` (the rounds the gun fired, by element).
- Riders (blind, slow, stun): the dummy's buff tags (`gl actorbuffs`) while the rifle fires
  at it, with the matching bullet-type orb so the element comes up.
- Crit and damage orbs: `gl critprobe` (Verbs_firearms.as) calls the player's own
  modifiers.Crit(player, target, skill) as a hit does (PlayerBase.as:855-900) many times, and
  reads the static crit stats, the skill's m_modCritChance / m_modCritDamage / m_modDamageMul
  and the custom stats.
- Shrapnel and Elemental Shrapnel: the armor_break debuff on a frag-hit dummy; the hp a resist
  dummy (gamelab-hands, 1000 elemental resistance) loses to rockets with and without the penetration.
- Rocket Jump: its log line and how far the player moved; EpiPen: its log line and stacks.
- Our Turret!: only its stat (hwp-turret-shared). Its effect needs a second player, which the
  lab doesn't have.
Sections: orbs_base, orbs_marksman, orbs_demo, orbs_assault, orbs_engineer."""
import re
import time

from gamelab.bots.plan_firearms import Checks as Base

ELEMENTS = ("fire", "ice", "lightning", "poison")
TOUGH = "doodads/generic/target_dummy_normal.unit"  # 10M hp: never dies under fire
RESIST = "gamelab/target_dummy_resist.unit"  # 600 hp, 1000 resistance to every element (gamelab-hands)
ROLLS = 20000


class Checks(Base):
    # --- read-outs
    def rolls(self, n=ROLLS):
        """RollElement n times: (chance, {plain, fire, ice, lightning, poison})."""
        txt = self.hwp(f"firearms elements roll {n}", 0.3, until="elements rolled")
        m = re.findall(r"elements rolled \d+ at chance ([\d.]+): plain (\d+) fire (\d+) ice (\d+) lightning (\d+) poison (\d+)", txt)
        if not m:
            return -1.0, {}
        c = m[-1]
        return float(c[0]), dict(zip(("plain",) + ELEMENTS, map(int, c[1:])))

    def fired(self):
        txt = self.hwp("firearms elements", 0.3, until="elements: plain")
        m = re.findall(r"elements: plain (\d+) fire (\d+) ice (\d+) lightning (\d+) poison (\d+)", txt)
        return dict(zip(("plain",) + ELEMENTS, map(int, m[-1]))) if m else {}

    def probe(self, skill=None, rolls=ROLLS, filt="target_dummy"):
        r = self.gl("critprobe", rolls, 400, filt, *([skill] if skill else []))
        r["rate"] = r.get("crits", 0) / max(1, r.get("rolls", 1))
        return r

    @staticmethod
    def custom(r, name):
        return next((c.get("value") for c in r.get("custom") or [] if c.get("id") == name), 0.0)

    def tough(self, d, dist=60, unit=TOUGH):
        """One dummy that doesn't die, dist along a clear line: (direction, id)."""
        self.clear_dummies()
        d, _ = self.clear_dir(d, dist)
        r = self.gl("spawn", unit, round(d[0] * dist, 1), round(d[1] * dist, 1))
        time.sleep(0.3)
        return d, r.get("unit")

    def set_clip(self, n):
        self.gl("givestacks", self.CLIP, n - self.clip())
        time.sleep(0.3)  # RefreshStats picks the stack's intensity up next frame
        return self.clip()

    def fire_at(self, d, ms):
        """The rifle held on d for ms, with a full clip, the dummy's buff tags seen meanwhile."""
        self.gl("givestacks", self.CLIP, 999)
        self.hwp("firearms elements reset", 0.2, until="elements: reset")
        self.gl("input", ms, 0, 0, d[0], d[1], "main")
        tags = set()
        end = time.time() + ms / 1000.0 + 0.5
        while time.time() < end:
            for ac in self.gl("actorbuffs", 300, "target_dummy").get("actors") or []:
                for bf in ac.get("buffs") or []:
                    tags.update(bf.get("tags") or [])
            time.sleep(0.05)
        return sorted(tags), self.fired()

    def hits(self, secs):
        """Damage numbers seen over secs, as ints (deduped as damage_texts does)."""
        out = []
        for t in self.damage_texts(secs):
            m = re.match(r"\d+", str(t.get("text", "")).replace(",", ""))
            if m:
                out.append(int(m.group(0)))
        return out

    # --- the base kit: Elemental Bullets, Extended Clip Crit, Shrapnel
    def orbs_base(self):
        """Elemental Bullets at level 5 rolls an elemental round half the time, each element a
        quarter of them; a bullet-type orb at level 3 (+1 weight) makes its element 2 in 5;
        real rifle shots come out elemental; Blinding Poison, Slowing Freeze and Stunning Shock
        put their debuff on the dummy only with their orb. Extended Clip Crit adds 10% to the
        rifle's 30 rounds and 2% crit damage per round left; Extended Crit Chance (level 3)
        rolls 0.75% crit per round left. Shrapnel puts armor_break on a frag-hit dummy."""
        self.new_char("LabOrbBase")
        if not self.enter_floor("orbs_base"):
            return
        d = self.open_dirs(130)[0]
        self.hwp("skillpoints 60", 0.6, until="skill points")
        lv = self.gl("skill", "hwp_fs_scavenger", 5).get("level", 0)
        time.sleep(0.6)
        chance, c = self.rolls()
        ele = sum(c.get(e, 0) for e in ELEMENTS)
        shares = {e: round(c.get(e, 0) / max(1, ele), 3) for e in ELEMENTS}
        self.flag("elemental_bullets_chance", lv >= 5 and abs(chance - 0.5) < 1e-3 and abs(ele / ROLLS - 0.5) < 0.02
                  and all(abs(s - 0.25) < 0.03 for s in shares.values()),
                  f"level {lv}, chance {chance}: {ele}/{ROLLS} elemental, shares {shares}")
        for e in ELEMENTS:
            ok, olv = self.orb(f"hwp_fs_scavenger_{e}", 3)
            ch, c = self.rolls()
            n = sum(c.get(x, 0) for x in ELEMENTS)
            share = c.get(e, 0) / max(1, n)
            self.flag(f"bullets_{e}_weighted", ok and olv == 3 and abs(share - 0.4) < 0.03,
                      f"orb level {olv}: {e} {c.get(e)} of {n} elemental = {round(share, 3)} (2 in 5 expected)")
            self.orb_off(f"hwp_fs_scavenger_{e}")

        dd, du = self.tough(d)
        tags, shots = self.fire_at(dd, 3000)
        n = sum(shots.values())
        self.flag("bullets_fire_elemental", n >= 4 and sum(shots.get(e, 0) for e in ELEMENTS) >= 1, f"rifle shots by element {shots}")
        bare = tags
        self.flag("riders_need_orbs", not any(t in bare for t in ("blind", "blindness", "slow", "stun")), f"dummy tags with no rider orb: {bare}")
        for bias, rider, lvl, want in (("poison", "blind", 1, "blind"), ("ice", "slow", 1, "slow"), ("lightning", "stun", 2, "stun")):
            ok1, _ = self.orb(f"hwp_fs_scavenger_{bias}", 3)
            ok2, olv = self.orb(f"hwp_fs_scavenger_{rider}", lvl)
            dd, du = self.tough(d)
            # 2 in 5 of half the rounds: 7 rounds in a slow run carried no ice (20261019-211805),
            # so burst again, up to 3 times, until the element and its rider both show
            tags, shots = set(), {}
            for _ in range(3):
                t, s = self.fire_at(dd, 3500)
                tags.update(t)
                shots = {k: shots.get(k, 0) + v for k, v in s.items()}
                if shots.get(bias, 0) >= 1 and any(want in x for x in tags):
                    break
            tags = sorted(tags)
            self.flag(f"bullets_{rider}_rider", ok1 and ok2 and shots.get(bias, 0) >= 1 and any(want in t for t in tags),
                      f"orb level {olv}: {shots.get(bias, 0)} {bias} rounds of {sum(shots.values())}, dummy tags {tags}")
            self.orb_off(f"hwp_fs_scavenger_{rider}")
            self.orb_off(f"hwp_fs_scavenger_{bias}")

        # Extended Clip Crit: the clip's rounds are the crit damage stack's intensity
        mx0 = self.clip_max()
        lv = self.gl("skill", "hwp_fs_steady", 1).get("level", 0)
        time.sleep(0.6)
        mx1 = self.clip_max()
        self.flag("extended_clip_rounds", lv >= 1 and mx0 == 30 and mx1 == 33, f"clip max {mx0} -> {mx1} at level {lv}")
        dd, du = self.tough(d)
        full = self.set_clip(mx1)
        p_full = self.probe()
        one = self.set_clip(1)
        p_one = self.probe()
        dmg = round(p_full.get("mainCritDmg", 0) - p_one.get("mainCritDmg", 0), 3)
        self.flag("extended_clip_crit_damage", abs(dmg - 0.02 * (full - one)) < 0.005,
                  f"main crit damage {p_one.get('mainCritDmg')} at {one} rounds, {p_full.get('mainCritDmg')} at {full}: +{dmg}")
        ok, olv = self.orb("hwp_fs_steady_crit", 3)
        full = self.set_clip(mx1)
        r_full = self.probe()["rate"]
        one = self.set_clip(1)
        r_one = self.probe()["rate"]
        self.flag("extended_crit_chance", ok and abs(r_full - 0.0075 * full) < 0.02 and abs(r_one - 0.0075) < 0.004,
                  f"orb level {olv}: crit rolls {round(r_full, 4)} at {full} rounds ({0.0075 * full} expected), "
                  f"{round(r_one, 4)} at {one} (0.0075); before the orb {round(p_full['rate'], 4)}")
        self.orb_off("hwp_fs_steady_crit")

        # Shrapnel: the frag's armor_break debuff
        def frag_tags():
            dd, du = self.tough(d, 90)
            self.top_up()
            self.gl("castat", "hwp_fs_frag", dd[0] * 90, dd[1] * 90, "nocd")
            _, tags, _ = self.dummy_watch(du, 2.0)
            return tags
        bare = frag_tags()
        ok, olv = self.orb("hwp_fs_frag_shrapnel", 3)
        tags = frag_tags()
        self.flag("frag_shrapnel_armor_break", ok and "armor_break" in tags and "armor_break" not in bare,
                  f"orb level {olv}: dummy tags {tags}, without the orb {bare}")
        self.orb_off("hwp_fs_frag_shrapnel")
        self.clear_dummies()
        self.to_town()

    # --- Marksman: BOOM Headshot!, Elemental Exposure
    def orbs_marksman(self):
        """BOOM Headshot! (level 3) adds 5% crit chance and 30% crit damage to attacks and
        spells, and as much again to Snipe itself; Elemental Exposure (level 3) rolls 3% crit
        per element afflicting the target: none on a clean dummy, about 3% on a burning one
        (an Incendiary grenade's patch)."""
        self.new_char("LabOrbMark", "hwp_firearms_sniper")
        if not self.enter_floor("orbs_marksman"):
            return
        d = self.open_dirs(130)[0]
        if not (self.level("snipe", "hwp_fs_snipe") and self.level("focus", "hwp_fs_focus")):
            return
        dd, du = self.tough(d, 90)
        b0 = self.probe("hwp_fs_snipe", 1)
        ok, olv = self.orb("hwp_fs_focus_boom", 3)
        b1 = self.probe("hwp_fs_snipe", 1)
        delta = {k: round(b1.get(k, 0) - b0.get(k, 0), 3) for k in ("mainCrit", "mainCritDmg", "spellCrit", "spellCritDmg", "skillCrit", "skillCritDmg")}
        # crit chances stack as independent rolls, 1 - (1 - a)(1 - b) (StatModifier.as CriticalHit),
        # so +5% on a base b adds 0.05 * (1 - b); the skill's own and crit damage just add
        want = {"mainCrit": 0.05 * (1 - b0.get("mainCrit", 0)), "mainCritDmg": 0.3,
                "spellCrit": 0.05 * (1 - b0.get("spellCrit", 0)), "spellCritDmg": 0.3, "skillCrit": 0.05, "skillCritDmg": 0.3}
        self.flag("boom_headshot_crit", ok and all(abs(delta[k] - v) < 0.002 for k, v in want.items()),
                  f"orb level {olv}: added {delta}, expected {({k: round(v, 3) for k, v in want.items()})}")
        self.orb_off("hwp_fs_focus_boom")

        ok, olv = self.orb("hwp_fs_focus_exposure", 3)
        clean = self.probe()["rate"]
        ok2, _ = self.orb("hwp_fs_frag_fire")
        self.top_up()
        self.gl("castat", "hwp_fs_frag", dd[0] * 90, dd[1] * 90, "nocd")
        time.sleep(1.6)  # lands ~0.8 s after the cast, then the patch burns
        tags = sorted({t for ac in self.gl("actorbuffs", 300, "target_dummy").get("actors") or []
                       for bf in ac.get("buffs") or [] for t in bf.get("tags") or []})
        burning = self.probe()["rate"]
        self.flag("exposure_crit_per_element", ok and ok2 and clean < 0.002 and 0.022 < burning < 0.038,
                  f"orb level {olv}: crit rolls {round(clean, 4)} on a clean dummy, {round(burning, 4)} with tags {tags} (0.03 expected)")
        self.orb_off("hwp_fs_frag_fire")
        self.orb_off("hwp_fs_focus_exposure")
        self.clear_dummies()
        self.to_town()

    # --- Demolitionist: Overpacked Explosives, Elemental Shrapnel, Rocket Jump
    def orbs_demo(self):
        """Overpacked Explosives (level 2) multiplies the rocket's and the frag's damage by
        1.25; Elemental Shrapnel (level 2) gives explosions 12% elemental penetration, so
        rockets take more hp from a resist dummy (1000 resistance); Rocket Jump throws the player out
        of their own rocket's blast (logged)."""
        self.new_char("LabOrbDemo", "hwp_firearms_demolitions")
        if not self.enter_floor("orbs_demo"):
            return
        d = self.open_dirs(130)[0]
        if not (self.level("rpg", "hwp_fs_rpg") and self.level("hoarder", "hwp_fs_hoarder")):
            return
        dd, du = self.tough(d, 90)
        m0 = (self.probe("hwp_fs_rpg", 1).get("skillDmgMul"), self.probe("hwp_fs_frag", 1).get("skillDmgMul"))
        ok, olv = self.orb("hwp_fs_hoarder_overpacked", 2)
        m1 = (self.probe("hwp_fs_rpg", 1).get("skillDmgMul"), self.probe("hwp_fs_frag", 1).get("skillDmgMul"))
        self.flag("overpacked_damage", ok and m0 == (1.0, 1.0) and all(abs((x or 0) - 1.25) < 1e-3 for x in m1),
                  f"orb level {olv}: rocket, frag damage mul {m0} -> {m1}")
        self.orb_off("hwp_fs_hoarder_overpacked")

        def rockets(n=3):
            """hp taken by a fresh resist dummy (600 hp, 1000 fire resistance) from n rockets at
            the same spot (the blast scales with distance), and the damage numbers seen"""
            dd, du = self.tough(d, 90, RESIST)
            hp0 = self.hps([du])[du]
            out = []
            for _ in range(n):
                self.top_up()
                # a held aim, not castat: the rocket re-reads the aim (plan_firearms aimed_cast),
                # and castat rockets hit nothing in 20261019-211805
                self.aimed_cast("hwp_fs_rpg", dd, 720)
                out += self.hits(1.4)
            return round((hp0 - self.hps([du])[du]) * 600), out
        bare, tb = rockets()
        ok, olv = self.orb("hwp_fs_hoarder_shrapnel", 2)
        pen = self.custom(self.probe("hwp_fs_rpg", 1), "hwp-shrapnel")
        more, tm = rockets()
        # ApplyArmor: damage x 1/(1 + res*(1-pen)*0.005): 1/6 without, 1/5.4 at 12% -> x1.11
        ratio = more / bare if bare else 0
        self.flag("elemental_shrapnel_pen", ok and abs(pen - 0.12) < 1e-3, f"orb level {olv}: hwp-shrapnel {pen}")
        self.flag("elemental_shrapnel_more_damage", bare > 0 and 1.05 < ratio < 1.18,
                  f"3 rockets took {bare} hp of the resist dummy (texts {tb}) -> {more} with the orb (texts {tm}): "
                  f"x{round(ratio, 3)} (6/5.4 = 1.111 expected)")
        self.orb_off("hwp_fs_hoarder_shrapnel")

        def jump():
            dd, du = self.tough(d, 24)
            self.top_up()
            p0 = self.pos()
            pos = self.log_pos()
            self.gl("castat", "hwp_fs_rpg", dd[0] * 24, dd[1] * 24, "nocd")
            m = self.wait_log(r"rocket jump: [^\n]*", pos, 2.0)
            time.sleep(0.8)
            p1 = self.pos()
            return m, round(((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5, 1)
        # moved1 vs moved0, not a fixed 20: a wall behind cut a logged throw to 18.7 (20261019-211805)
        m0, moved0 = jump()
        ok, olv = self.orb("hwp_fs_rpg_jump")
        m1, moved1 = jump()
        self.flag("rocket_jump_throws", ok and m0 is None and m1 is not None and moved1 > moved0 + 10,
                  f"without the orb: {m0 and m0.group(0)}, moved {moved0}; with it: {m1 and m1.group(0)}, moved {moved1}")
        self.orb_off("hwp_fs_rpg_jump")
        self.clear_dummies()
        self.to_town()

    # --- Assault: Critical Focus, EpiPen
    def orbs_assault(self):
        """Critical Focus (level 3) rolls 1.5% crit per adrenaline stack; EpiPen (level 2)
        gives 15 stacks on a dodge with none, and nothing on a dodge with some; its fuse hiss
        stops at 2 s (faded out from 1 s; the lab is muted, so only the logged stop is seen)."""
        self.new_char("LabOrbAssault", "hwp_firearms_assault")
        if not self.enter_floor("orbs_assault"):
            return
        d = self.open_dirs(130)[0]
        if not self.level("adrenaline", "hwp_fs_adrenaline"):
            return
        dd, du = self.tough(d, 90)
        ok, olv = self.orb("hwp_fs_adrenaline_crit", 3)
        self.gl("givestacks", self.STACKS + "adrenaline", -99)
        r0 = self.probe()["rate"]
        self.gl("givestacks", self.STACKS + "adrenaline", 6)
        n = self.stacks("adrenaline")
        r6 = self.probe()["rate"]
        self.flag("critical_focus_per_stack", ok and r0 < 0.002 and n > 0 and abs(r6 - 0.015 * n) < 0.01,
                  f"orb level {olv}: crit rolls {round(r0, 4)} at 0 stacks, {round(r6, 4)} at {n} ({0.015 * n} expected)")
        self.orb_off("hwp_fs_adrenaline_crit")

        ok, olv = self.orb("hwp_fs_adrenaline_epipen", 2)
        self.gl("givestacks", self.STACKS + "adrenaline", -99)
        pos = self.log_pos()
        self.gl("input", 120, -d[0], -d[1], -d[0], -d[1], "dash")
        m1 = self.wait_log(r"adrenaline: epipen, (\d+) stacks", pos, 2.0)
        s1 = self.stacks("adrenaline")
        hiss = self.wait_log(r"adrenaline: epipen hiss faded out at (\d+) ms", pos, 3.0)
        time.sleep(1.5)  # the dodge's cooldown
        pos = self.log_pos()
        self.gl("input", 120, d[0], d[1], d[0], d[1], "dash")
        m2 = self.wait_log(r"adrenaline: epipen", pos, 1.5)
        s2 = self.stacks("adrenaline")
        self.flag("epipen_on_dodge", ok and m1 is not None and s1 >= 1 and m2 is None and s2 == s1,
                  f"orb level {olv}: dodge at 0 stacks: {m1 and m1.group(0)}, {s1} stacks; dodge with {s1}: {m2 and m2.group(0)}, {s2}")
        self.flag("epipen_hiss_fades", hiss is not None and 2000 <= int(hiss.group(1)) < 2200,
                  f"the fuse hiss: {hiss and hiss.group(0)} (stopped at 2 s, faded from 1 s)")
        self.orb_off("hwp_fs_adrenaline_epipen")
        self.clear_dummies()
        self.to_town()

    # --- Engineer: Our Turret!
    def orbs_engineer(self):
        """Our Turret! sets hwp-turret-shared, which Turret.as FindBooster reads to let other
        players boost; the lab has no second player, so only the stat is checked."""
        self.new_char("LabOrbEng", "hwp_firearms_engineer")
        if not self.enter_floor("orbs_engineer"):
            return
        d = self.open_dirs(130)[0]
        if not self.level("myturret", "hwp_fs_myturret"):
            return
        dd, du = self.tough(d, 90)
        s0 = self.custom(self.probe(rolls=1), "hwp-turret-shared")
        ok, olv = self.orb("hwp_fs_myturret_shared")
        s1 = self.custom(self.probe(rolls=1), "hwp-turret-shared")
        self.flag("our_turret_stat", ok and not s0 and abs((s1 or 0) - 1) < 1e-3,
                  f"orb level {olv}: hwp-turret-shared {s0} -> {s1} (the shared boost itself needs a second player)")
        self.orb_off("hwp_fs_myturret_shared")
        self.clear_dummies()
        self.to_town()


def run(p, sections="orbs_base", **_):
    c = Checks(p)
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
