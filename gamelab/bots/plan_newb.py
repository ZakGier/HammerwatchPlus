"""Test-plan checks for three features that had no plan steps yet: HoH1 puzzle rooms (the
Constellation, mods/puzzles), the architect challenges (HoH1's bad wishes, mods/architect)
and mercenary mode (mods/mercenary). Same style as plan_checks: each section flags
booleans, the scenario's expect asserts them, measured values go in the notes.

Sections:
- constellation_fail: a Constellation fabricated in town; a correct star counts, a wrong one
  fails it and locks every star (puzzles s4).
- puzzle_rooms: a town save, puzzles.room_chance 0 (no room), then 100 with the
  Constellation weighted up; the real floor's room is walked to, solved, and drops its
  reward (puzzles s1-s3).
- architect_paid / architect_free: the loadout's Architect picker through its own
  widgets (gl func / gl press), the Mul line and the total cost after each pick, then the
  town's gold and materials before and after the run starts (architect s6-s8).
- merc_enlist / merc_bonus / merc_floor / merc_boss / merc_fall: mercenary mode
  (mercenary s1-s7)."""
import re
import time

from gamelab.bots.plan_checks import Checks as Base
from gamelab.hps import hash_string

CHALLENGES = {  # id -> discount, mods/architect/scripts/HWP/Architect/Challenges.as
    "hwp_challenge_crowded": 0.15, "hwp_challenge_champions": 0.15,
    "hwp_challenge_lean_pickups": 0.10, "hwp_challenge_bitter_draughts": 0.10,
    "hwp_challenge_glass_bones": 0.25, "hwp_challenge_sharp_traps": 0.10,
    "hwp_challenge_slim_pickings": 0.15,
}
EFFECTS = {  # what each challenge's tooltip says it does (hwp_architect.lang)
    "hwp_challenge_crowded": "more enemies", "hwp_challenge_champions": "Elites and minibosses",
    "hwp_challenge_lean_pickups": "restore half", "hwp_challenge_bitter_draughts": "confuses you",
    "hwp_challenge_glass_bones": "40% more damage", "hwp_challenge_sharp_traps": "double damage",
    "hwp_challenge_slim_pickings": "Half the wood",
}
MATS = ["gold", "wood", "stone", "iron", "crystals", "dust", "ore"]
STARS = [(r, c) for r in range(5) for c in range(5)]


def vanilla_mul(buys, arch_lvl):
    """CalcArchitectCostMul (Missions/MissionArchitect.as) for `buys` bought alterations and
    no vanilla debuffs."""
    n = max(1, buys)
    return (n ** 1.6 - 1) / 7 + 1 if arch_lvl >= 1 else (n ** 1.8 - 1) / 6 + 1


def cost_mul(picks, arch_lvl):
    """HWP::Architect::CostMul: vanilla's curve over the bought ones, times what the
    challenges leave (never below 0)."""
    buys = [p for p in picks if p not in CHALLENGES]
    off = sum(CHALLENGES.get(p, 0) for p in picks)
    return vanilla_mul(len(buys), arch_lvl) * max(0.0, 1.0 - off)


def cost_parts(text):
    """{material: amount} from a ShopCost.GetText line ("icn-gold"750  "icn-wood"7, with
    \\cff0000 ... \\d around what the player can't afford)."""
    text = re.sub(r"\\c[0-9a-fA-F]{6}|\\d", "", text or "")
    return {m: int(n) for m, n in re.findall(r"icn-([a-z]+)\W*(\d+)", text)}


class Checks(Base):
    # --- plumbing
    def log_since(self, mark):
        return self.g.read_log()[mark:]

    def mats(self):
        return {k: v for k, v in (self.gl("inv").get("materials") or {}).items()}

    def god(self, on):
        """hwp god toggles; toggle again when the reply says the other state."""
        want = "god mode on" if on else "god mode off"
        for _ in range(2):
            if want in self.hwp("god", 0.4, until="god mode"):
                return True
        return False

    def wait_boot(self, mark, timeout=150):
        """Wait for a new level's boot line (not a [preload] one) after `mark`, then the
        mission phase: from a mission, the phase reads "mission" before the change too."""
        end = time.time() + timeout
        while time.time() < end:
            new = self.g.read_log()[mark:]
            if any('[GL] {"ev":"boot"' in ln and "[preload]" not in ln for ln in new.splitlines()):
                break
            time.sleep(0.25)
        ok = self.wait_phase("mission", 30)
        time.sleep(2)
        return ok

    def start_mission(self, mission, floor):
        mark = len(self.g.read_log())
        r = self.gl("mission", mission, floor)
        return bool(r.get("ok")) and self.wait_boot(mark), self.g.read_log()[mark:]

    def wait_level(self, cmd, timeout=90):
        """An HWP console command that changes level (finishlevel, boss): wait for the new
        floor's boot line (not a [preload] one) and the mission phase."""
        mark = len(self.g.read_log())
        self.hwp(cmd, 0.3)
        end = time.time() + timeout
        while time.time() < end:
            new = self.g.read_log()[mark:]
            if any('[GL] {"ev":"boot"' in ln and "[preload]" not in ln for ln in new.splitlines()):
                break
            time.sleep(0.25)
        ok = self.wait_phase("mission", 30)
        time.sleep(2)
        return ok, self.g.read_log()[mark:]

    def first_run(self):
        """A fixture boot has no town save (TownRecord.Save returns false for an empty town),
        so a mission would load none and the HWP settings with it: one story run, finished
        at once, saves the town (mod-puzzle-rooms 20261018-081802)."""
        r = self.gl("mission", "story_intro_find_npcs", 0)
        ok = bool(r.get("ok")) and self.wait_phase("mission", 120)
        self.g.console("e_cheats 1")
        time.sleep(0.5)
        self.g.console("cht_finish_level")
        ok = self.wait_phase("town", 120) and ok
        time.sleep(3)
        if self.gl("state").get("window"):
            self.g.key("escape")
            time.sleep(1)
        return ok

    # --- puzzles
    def ws(self, kind, prefix):
        return self.gl("ws", kind, prefix).get("scripts") or []

    def remaining(self):
        s = self.ws("Variable", "hwp_remaining")
        return s[0].get("v") if len(s) == 1 else None

    def pattern(self):
        """The stars of the picked pattern: their hwp_correct_r_c link is the enabled one."""
        return [s["c"][len("hwp_correct_"):] for s in self.ws("ScriptLink", "hwp_correct_") if s.get("e")]

    def link_state(self, comment):
        s = self.ws("ScriptLink", comment)
        return (s[0].get("e"), s[0].get("t")) if s else (None, None)

    def stars_locked(self):
        stars = self.ws("UseTrigger", "hwp_star_")
        return len(stars) == 25 and not any(s.get("e") for s in stars)

    def constellation_fail(self):
        """puzzles s4: fabricated in town, a pattern (7-12 stars) is picked; a correct star
        counts down, a wrong one fails the puzzle and locks every star; solved never runs."""
        r = self.gl("prefab", "prefabs/puzzles/hwp/puzzle_constellation.pfb", 0, -110)
        time.sleep(0.8)
        n0 = self.remaining()
        pat = self.pattern()
        self.flag("cf_pattern_picked", r.get("ok") and n0 is not None and 7 <= n0 <= 12 and len(pat) == n0,
                  f"prefab {r.get('ok')}, remaining {n0}, pattern {pat}")
        if not pat:
            return
        u = self.gl("usews", f"hwp_star_{pat[0]}", "ScriptLink", f"hwp_correct_{pat[0]}")
        time.sleep(0.4)
        n1 = self.remaining()
        self.flag("cf_correct_counts", u.get("used") and n1 == n0 - 1, f"pressed {pat[0]}: {n0} -> {n1}")
        wrong = next(f"{r_}_{c}" for r_, c in STARS if f"{r_}_{c}" not in pat)
        mark = len(self.g.read_log())
        u = self.gl("usews", f"hwp_star_{wrong}", "ScriptLink", f"hwp_wrong_{wrong}")
        time.sleep(0.8)
        fe, ft = self.link_state("hwp_failed")
        se, st = self.link_state("hwp_solved")
        self.flag("cf_wrong_fails", u.get("used") and fe is False and ft == 0 and st == 1,
                  f"pressed {wrong}: failed e={fe} t={ft}, solved e={se} t={st}")
        self.flag("cf_locked", self.stars_locked() and self.remaining() == n1,
                  f"remaining {self.remaining()}; log {re.findall(r'stars fade|constellation shines', self.log_since(mark))}")

    def puzzle_rooms(self):
        """puzzles s1-s3 on real Bandit Keep floors: with room_chance 0 no puzzle room rolls;
        with 100 a keep_puzzle room is placed and, the Constellation weighted up, its picker
        picks it. Walked to (gl goto), solved with the pattern's stars: remaining 0, solved
        ran once, stars locked, and the room's RewardSpot dropped an item."""
        self.flag("pr_town_saved", self.first_run())
        self.hwp("set puzzles.room_chance 0", 0.4)
        self.gl("save")
        mark = len(self.g.read_log())
        ok = self.start_floor(0)
        log = self.log_since(mark)
        lines = re.findall(r"\[HWP:puzzles\][^\n]*", log)[:3]
        self.flag("pr_chance0_no_room", ok and "keep_puzzle not rolled (0%)" in log and "SpawnPrefabSet: keep_puzzle" not in log,
                  f"floor {ok}; {lines}")
        self.to_town()
        self.hwp("set puzzles.room_chance 100", 0.4)
        self.hwp("set puzzles.constellation 100000", 0.4)
        self.gl("save")
        tries, picked, placed, added = 0, False, False, False
        for tries in range(1, 6):
            _, log = self.start_mission("bandit_keep", 0)
            added = added or bool(re.search(r"\[HWP:puzzles\] puzzle rooms added to \d+ mission level generator", log))
            placed = placed or "SpawnPrefabSet: keep_puzzle" in log
            if re.search(r"\[HWP:puzzles\] constellation picked \(\d+ vanilla candidates\)", log):
                picked = True
                break
        self.flag("pr_room_placed", added and placed, f"rooms added {added}, keep_puzzle placed {placed}")
        self.flag("pr_constellation_picked", picked, f"after {tries} floor(s)")
        if not picked:
            self.to_town()
            return
        self.g.console("e_cheats 1")
        self.god(True)
        g = self.gl("goto", "RewardSpot", "constellation", 0, 0)
        time.sleep(1)
        items0 = self.gl("near", 6000, "items/").get("count", 0)
        n0 = self.remaining()
        pat = self.pattern()
        self.flag("pr_walked_there", g.get("found") == 1 and n0 is not None and len(pat) == n0,
                  f"goto {g}, remaining {n0}, pattern {pat}")
        mark = len(self.g.read_log())
        for cell in pat:
            self.gl("usews", f"hwp_star_{cell}", "ScriptLink", f"hwp_correct_{cell}")
            time.sleep(0.15)
        time.sleep(2)
        se, st = self.link_state("hwp_solved")
        fe, ft = self.link_state("hwp_failed")
        n1 = self.remaining()
        self.flag("pr_solved", n1 == 0 and st == 0 and ft == 1 and self.stars_locked(),
                  f"remaining {n1}, solved e={se} t={st}, failed t={ft}")
        items1 = self.gl("near", 6000, "items/").get("count", 0)
        self.flag("pr_reward", items1 > items0, f"items/ units {items0} -> {items1}")
        self.to_town()

    # --- architect
    def wtext(self, *ids):
        """{id: text} of the top window's widgets (gl wtext, Verbs_newb.as); the widgets dump
        when that verb isn't registered (its budget can run out on the loadout menu below
        the picker). A missing id is left out."""
        r = self.gl("wtext", *ids)
        if r.get("ok"):
            return r.get("texts") or {}
        out = {}
        for i in ids:
            n = self.widget(i)
            if n:
                out[i] = n.get("text", "")
        return out

    def picker_line(self):
        t = self.wtext("cost-mul", "total-cost")
        mul = t.get("cost-mul", "")
        m = re.search(r"(\d+)%", mul)
        return (int(m.group(1)) if m else None), cost_parts(t.get("total-cost", "")), mul

    def open_picker(self):
        """mission_start dark_citadel (vanilla's cheat: SetMission + the loadout menu, what the
        mission board does); the Architect row's own func opens the picker."""
        self.g.console("mission_start dark_citadel")
        time.sleep(1.5)
        w0 = self.gl("state").get("window")
        f = self.gl("func", "architect", "open")
        time.sleep(0.6)
        w1 = self.gl("state").get("window")
        return w0, w1, f

    def press_picks(self, picks, arch_lvl, label, start=()):
        """Press each row; after every press the picker's Mul line must be CostMul of the list
        so far (`start`: what the picker already has picked). Returns (all matched, the picks
        now, the % shown after each press)."""
        chosen, steps, shown_all, good = list(start), [], [], True
        for pid in picks:
            r = self.gl("press", pid)
            if pid in chosen:
                chosen.remove(pid)
            else:
                chosen.append(pid)
            time.sleep(0.4)
            shown, cost, _ = self.picker_line()
            want = int(cost_mul(chosen, arch_lvl) * 100 + 0.5)
            good = good and r.get("ok") and shown == want
            shown_all.append(shown)
            steps.append(f"{pid.replace('architect_', '').replace('hwp_challenge_', 'c:')} {shown}%/{want}% {cost}")
        self.notes.append(f"{label}: " + "; ".join(steps))
        return good, chosen, shown_all

    def start_from_loadout(self):
        """Close the picker (its Apply), Play in the loadout; the town store before, and in
        the mission the town record's materials (OnPlay spends from the town store)."""
        self.gl("func", "exit", "yes")
        time.sleep(0.5)
        before = self.mats()
        w = self.gl("state").get("window")
        self.gl("func", "play")
        ok = self.wait_phase("mission", 150)
        time.sleep(2)
        tm = self.gl("inspect", "town", "materials").get("value") or []
        after = dict(zip(MATS, tm)) if len(tm) >= 7 else {}
        picks = [v & 0xFFFFFFFF for v in (self.gl("inspect", "player", "architect-buffs").get("value") or [])]
        return ok, w, before, after, picks

    def architect_setup(self):
        """A saved town first (first_run): the mission loads the town record from the save,
        so the spend is read back from a real one. Then the Architect built and the store
        filled; saved again."""
        self.flag("ar_town_saved", self.first_run())
        self.g.console("e_cheats 1")
        b = self.gl("build", "architect")
        lvl = (self.gl("buildings").get("buildings") or {}).get("architect", 0)
        if not isinstance(lvl, int):
            lvl = 0
        self.set_gold(50000)
        for m in ("wood", "stone"):
            self.gl("material", m, 500 - self.mats().get(m, 0))
        self.gl("save")
        time.sleep(0.3)
        self.notes.append(f"architect built {b}, variation {lvl}")
        return b.get("ok"), lvl

    def architect_paid(self):
        """architect s6/s7: the picker lists the seven challenges at no cost, and hovering one
        shows its effect and its discount ("Alterations cost 25% less"); Far Sight alone
        is vanilla (Mul 100%, 1000 gold 10 wood), Glass Bones takes 25% off (750 gold, 7
        wood); the start takes exactly that from the town."""
        built, lvl = self.architect_setup()
        self.arch_lvl = lvl
        w0, w1, f = self.open_picker()
        self.flag("ar_picker_open", built and w0 == "MissionLoadoutMenu" and w1 == "SelectArchitectSelector",
                  f"build {built}, windows {w0} -> {w1}, func {f}")
        rows = self.wtext(*CHALLENGES)  # the picker's rows have the buff ids (SetID)
        self.flag("ar_challenges_listed", all(k in rows for k in CHALLENGES), f"missing {[k for k in CHALLENGES if k not in rows]}")
        tips_ok, free_ok, seen = True, True, []
        for cid, d in CHALLENGES.items():
            t = self.gl("hovertip", cid)  # the row hovered: its func-hover sets the tooltip
            text = re.sub(r"\\c[0-9a-fA-F]{6}|\\d", "", " ".join(t.get("texts") or []))
            cost = (t.get("children") or {}).get("cost")
            want = f"Alterations cost {int(d * 100 + 0.5)}% less"
            tip = bool(t.get("ok")) and text.startswith("Challenge: ") and EFFECTS[cid] in text and want in text
            tips_ok, free_ok = tips_ok and tip, free_ok and cost == ""
            if not tip or cost != "":
                seen.append(f"{cid}: {t.get('error') or text[:90]!r} cost {cost!r}")
        self.flag("ar_challenge_tips", tips_ok, "; ".join(seen)[:600] or "all 7 say their effect and discount")
        self.flag("ar_challenges_free", free_ok, "; ".join(seen)[:600] or "all 7 rows: no cost")
        good, chosen, _ = self.press_picks(["architect_far_sight", "hwp_challenge_glass_bones"], lvl, "paid picks")
        shown, cost, line = self.picker_line()
        self.flag("ar_glass_discount", good and shown == 75 and cost == {"gold": 750, "wood": 7}, f"{line!r} {cost}")
        ok, w, before, after, picks = self.start_from_loadout()
        paid = {m: before.get(m, 0) - after.get(m, 0) for m in MATS} if after else {}
        self.flag("ar_paid_exact", ok and paid.get("gold") == 750 and paid.get("wood") == 7
                  and all(paid.get(m) == 0 for m in MATS if m not in ("gold", "wood")),
                  f"window {w}; town {before} -> {after}: paid {paid}")
        want = sorted(hash_string(p) for p in chosen)
        self.flag("ar_picks_on_record", sorted(picks) == want, f"{picks} vs {want}")
        self.to_town()

    def architect_free(self):
        """architect s8: all seven challenges on top of Far Sight bring Mul to 0%, a second
        alteration keeps it at 0% (not below), unpicking Glass Bones brings a multiplier back,
        picking it again is 0% once more; the start takes nothing and pays nothing out."""
        lvl = getattr(self, "arch_lvl", None)
        if lvl is None:
            _, lvl = self.architect_setup()
        w0, w1, f = self.open_picker()
        order = ["architect_far_sight", "hwp_challenge_glass_bones", "hwp_challenge_crowded",
                 "hwp_challenge_champions", "hwp_challenge_slim_pickings", "hwp_challenge_lean_pickups",
                 "hwp_challenge_bitter_draughts", "hwp_challenge_sharp_traps"]
        good, chosen, _ = self.press_picks(order, lvl, "free picks")
        shown, cost, line = self.picker_line()
        self.flag("ar_stack_to_zero", w1 == "SelectArchitectSelector" and good and shown == 0 and not cost,
                  f"{line!r} {cost}")
        good2, chosen, _ = self.press_picks(["architect_fewer_enemies"], lvl, "second alteration", chosen)
        s2, c2, _ = self.picker_line()
        self.flag("ar_never_below_zero", good2 and s2 == 0 and not c2, f"Mul {s2}%, cost {c2}")
        # Glass Bones unpicked: 25% of two alterations' curve comes back (35% at architect 0); picked again: 0%
        good3, chosen, toggled = self.press_picks(["hwp_challenge_glass_bones", "hwp_challenge_glass_bones"], lvl, "toggle", chosen)
        self.flag("ar_unpick_restores", good3 and bool(toggled[0]) and toggled[1] == 0, f"Mul {toggled}")
        ok, w, before, after, picks = self.start_from_loadout()
        diff = {m: after.get(m, 0) - before.get(m, 0) for m in MATS} if after else {}
        self.flag("ar_free_run", ok and bool(after) and all(v == 0 for v in diff.values()),
                  f"town {before} -> {after}: change {diff}")
        self.flag("ar_free_picks_on_record", len(picks) == len(chosen) == 9, f"{len(picks)} on record, {len(chosen)} picked")
        self.to_town()

    # --- mercenary
    def merc(self):
        out = self.hwp("merc", 0.4, until="[HWP] ")
        m = re.findall(r"mercenary (\w+)(?: \(FALLEN[^)]*\))?, (\d+) prestige.*?; (\d+) floor\(s\), (\d+) boss\(es\).*?"
                       r"gold gain x([\d.]+), experience x([\d.]+)", out)
        if not m:
            return {"text": out.strip()[-200:]}
        rank, pr, fl, bo, g, x = m[-1]
        return {"rank": rank, "prestige": int(pr), "floors": int(fl), "bosses": int(bo),
                "gold": float(g), "xp": float(x), "fallen": "(FALLEN" in out, "text": out.strip()[-200:]}

    def experience(self):
        return self.gl("inspect", "player", "experience").get("value", 0)

    def xp_gain(self, amount=500):
        e0 = self.experience()
        self.hwp(f"xp {amount}", 0.4, until="gave ")
        return self.experience() - e0

    def merc_enlist(self):
        """mercenary s1/s2: without a level-20 Paladin enlisting is locked; the levelled hero
        is refused (only a fresh level-1); with that veteran saved, a new level-1 Paladin is
        asked to confirm and enlists at level 10."""
        self.g.console("e_cheats 1")
        self.gl("char", "paladin", "LabVet")
        time.sleep(1.5)
        not_merc = self.hwp("merc", 0.4, until="[HWP] ")
        locked = self.hwp("merc enlist", 0.4, until="[HWP] ")
        self.flag("mc_not_merc", "LabVet is not a mercenary" in not_merc, not_merc.strip()[-120:])
        self.flag("mc_locked", "Reach level 20 with another Paladin first" in locked, locked.strip()[-120:])
        self.xp0 = self.xp_gain()  # a regular hero's gain, the baseline for the rank bonus
        for _ in range(4):
            if self.gl("state").get("player", {}).get("level", 0) >= 20:
                break
            self.hwp("levelup 20", 0.6)
        lvl = self.gl("state").get("player", {}).get("level")
        refused = self.hwp("merc enlist", 0.4, until="[HWP] ")
        self.flag("mc_levelled_refused", lvl == 20 and "only a fresh level-1 character can enlist" in refused,
                  f"level {lvl}: {refused.strip()[-120:]}")
        self.gl("char", "paladin", "LabMerc")  # saves LabVet first (VerbChar)
        time.sleep(1.5)
        ask = self.hwp("merc enlist", 0.4, until="[HWP] ")
        self.flag("mc_veteran_unlocks", "Type hwp merc enlist confirm to enlist" in ask and "Reach level" not in ask,
                  ask.strip()[-160:])
        done = self.hwp("merc enlist confirm", 0.8, until="enlists as a mercenary")
        st = self.gl("state").get("player", {})
        self.flag("mc_enlisted_l10", "LabMerc enlists as a mercenary: level 10, rank Private" in done and st.get("level") == 10,
                  f"level {st.get('level')}: {done.strip()[-160:]}")

    def merc_bonus(self):
        """mercenary s3/s4: Private gives +15% experience over a regular hero; 50 prestige is
        Corporal (+30%), and the experience gain grows by 1.30/1.15."""
        m0 = self.merc()
        g1 = self.xp_gain()
        x0 = getattr(self, "xp0", 0)
        self.flag("mc_private", m0.get("rank") == "Private" and abs(m0.get("xp", 0) - 1.15) < 0.005
                  and abs(m0.get("gold", 0) - 1.15) < 0.005, m0.get("text"))
        self.flag("mc_private_xp", x0 > 0 and abs(g1 / x0 - 1.15) < 0.02, f"500 xp: regular {x0}, Private {g1}")
        up = self.hwp("merc prestige 50", 0.6, until="Rank gained")
        m1 = self.merc()
        g2 = self.xp_gain()
        self.flag("mc_corporal", "Rank gained: Corporal! +30% gold and experience" in up and m1.get("rank") == "Corporal"
                  and abs(m1.get("xp", 0) - 1.30) < 0.005, m1.get("text"))
        self.flag("mc_corporal_xp", g1 > 0 and abs(g2 / g1 - 1.30 / 1.15) < 0.02, f"500 xp: Private {g1}, Corporal {g2}")

    def pickup_gold(self, amount=1000):
        """A real gold pickup (gl drop: DropMaterial with an amount) a few steps away, walked
        onto with the Pilot (path_to); a teleport onto it if the walk didn't take it."""
        pl = self.gl("state").get("player", {})
        x, y = pl.get("x", 0.0), pl.get("y", 0.0)
        spot = (40, 0)
        for dx, dy in [(40, 0), (0, 40), (-40, 0), (0, -40), (30, 30), (-30, 30)]:
            pf = self.gl("pathfind", x + dx, y + dy)
            if pf.get("ok") and pf.get("nodes", 0) > 0:
                spot = (dx, dy)
                break
        g0 = self.gold()
        d = self.gl("drop", "gold", amount, *spot)
        time.sleep(0.5)
        walked = self.p.path_to(d.get("x", x + spot[0]), d.get("y", y + spot[1]), tol=4, timeout=8)
        time.sleep(0.8)
        left = d.get("unit") in {u["unit"] for u in self.gl("near", 300, "materials/gold").get("units") or []}
        how = f"walk {walked.result}"
        if left:
            self.gl("teleport", d.get("x"), d.get("y"))
            time.sleep(0.8)
            how += ", then a teleport onto it"
        return self.gold() - g0, how

    def merc_floor(self):
        """mercenary s5: the first floor reminds the mercenary, counts one prestige, and a gold
        pickup lands times the rank's multiplier."""
        p0 = self.merc().get("prestige", 0)
        mark = len(self.g.read_log())
        ok = self.start_floor(0)
        log = self.log_since(mark)
        self.g.console("e_cheats 1")
        self.god(True)
        self.gl("kill", 800, "tag:enemy")
        m = self.merc()
        self.flag("mc_reminder", ok and "Mercenary Corporal: if you die, it's permanent" in log, f"floor {ok}")
        self.flag("mc_floor_counted", m.get("prestige") == p0 + 1 and m.get("floors", 0) >= 1, m.get("text"))
        gain, how = self.pickup_gold()
        want = 1000 * m.get("gold", 0)
        self.flag("mc_gold_pickup", abs(gain - want) <= 5 and abs(m.get("gold", 0) - 1.30) < 0.005,
                  f"1000 dropped, {gain} gained, want {want:.0f} (x{m.get('gold')}); {how}")

    def merc_boss(self):
        """mercenary s6: the mission's boss floor (hwp boss: levels/boss_bandits.lvl) counts a
        floor, its boss kill (credited to the player) 10 more, and only once per floor."""
        if self.gl("state").get("phase") != "mission":
            self.start_floor(0)
        m0 = self.merc()
        ok, log = self.wait_level("boss")
        self.g.console("e_cheats 1")
        self.god(True)
        lvl = self.gl("state").get("level")
        m1 = self.merc()
        k = self.gl("kill", 4000, "tag:boss", "me")
        if not k.get("killed"):
            self.gl("spawn", "actors/bosses/boss_bandit/boss_bandit.unit", 80, -60)
            time.sleep(1.5)
            k = self.gl("kill", 800, "tag:boss", "me")
        time.sleep(1.5)
        m2 = self.merc()
        self.gl("spawn", "actors/bosses/boss_bandit/boss_bandit.unit", 80, -60)
        time.sleep(1.5)
        k2 = self.gl("kill", 800, "tag:boss", "me")
        time.sleep(1.5)
        m3 = self.merc()
        self.flag("mc_boss_floor", ok and m1.get("prestige") == m0.get("prestige", 0) + 1, f"{lvl}: {m0.get('prestige')} -> {m1.get('prestige')}")
        self.flag("mc_boss_kill", k.get("killed", 0) >= 1 and m2.get("bosses") == 1 and m2.get("prestige") == m1.get("prestige", 0) + 10,
                  f"killed {k.get('killed')} {[n.split('/')[-1] for n in k.get('names', [])]}: {m2.get('text')}")
        self.flag("mc_boss_once", k2.get("killed", 0) >= 1 and m3.get("bosses") == 1 and m3.get("prestige") == m2.get("prestige"),
                  f"second boss killed {k2.get('killed')}: {m3.get('text')}")

    def merc_fall(self):
        """mercenary s7: dying on a floor is a fall, announced; back in town the picker opens
        (a fallen hero can't be played), its mission setup closes as it opens, the rank bonus
        is gone and the ledger lists it."""
        if self.gl("state").get("phase") != "mission":
            self.start_floor(0)
        self.g.console("e_cheats 1")
        self.god(False)
        mark = len(self.g.read_log())
        dead = False
        for _ in range(8):
            self.g.console("cht_damage 999999")
            time.sleep(1)
            if "fell (" in self.log_since(mark):
                dead = True
                break
        time.sleep(1.5)
        log = self.log_since(mark)
        self.flag("mc_fell", dead and bool(re.search(r"\[HWP:mercenary\] LabMerc fell \(", log)), "")
        self.flag("mc_fall_announced", bool(re.search(r"LabMerc, Corporal \(level \d+ Paladin\), has fallen", log)),
                  "; ".join(re.findall(r"has fallen[^\n]*", log))[:160])
        if self.gl("state").get("window") == "DeadMenu" or dead:
            self.g.key("enter")  # the death screen's accept (DeadMenu.as)
        ok = self.wait_phase("town", 120)
        time.sleep(3)
        if self.gl("state").get("window") == "MissionEndMenu":
            self.g.key("escape")
        mark = len(self.g.read_log())
        end = time.time() + 12
        while time.time() < end and "opening the character picker" not in self.log_since(mark):
            time.sleep(0.5)
        w = self.gl("state").get("window")
        self.flag("mc_picker_forced", ok and w == "PickCharacterWindow" and "opening the character picker" in self.log_since(mark),
                  f"town {ok}, window {w}")
        m = self.merc()
        self.flag("mc_fallen_no_bonus", m.get("fallen") and m.get("xp") == 1.0 and m.get("gold") == 1.0, m.get("text"))
        mark = len(self.g.read_log())
        self.g.console("mission_start bandit_keep")
        time.sleep(2)
        log = self.log_since(mark)
        w2 = self.gl("state").get("window")
        self.flag("mc_no_run", "closed the mission setup of a fallen mercenary" in log and w2 != "MissionLoadoutMenu",
                  f"window {w2}")
        led = self.hwp("merc ledger", 0.4, until="Ledger")
        self.flag("mc_ledger", bool(re.search(r"- LabMerc, Corporal, level \d+ Paladin, \d+ prestige, fell in", led)),
                  led.strip()[-200:])


def run(p, sections="constellation_fail", **_):
    c = Checks(p)
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
