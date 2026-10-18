"""Test-plan checks for the pets group (pets s2/s4/s5/s9/s10/s12, goldpet s2/s3), on top of
plan_checks' helpers. Everything goes through gl verbs, HWP console commands and the game's
own windows (gl use / press / presslist), never real input.

Sections, by scenario:
  plan-pets-a (the fixture's own GameLab character, made before HWP was enabled):
    legacy_record, dyer_nopet, petshop, dyer_choice, dye_pet | legacy_run, dye_floor,
    to_town | restart | dye_restart, dye_remove
  plan-pets-b (a fresh LabPets): pets_setup, smash, mend, stun, puzzle_wait, morale_on |
    morale_combat | morale_after
  plan-pets-c (the GameLab character): gp_gates, gp_summon | gp_run | restart | gp_reload

Verbs beyond plan_checks: presslist / querycmp / unitdestroy (Verbs_pets.as), buildup
(Verbs_farming.as), hurt / buffs (Verbs_classesb.as), actorbuffs (Verbs_classesa.as)."""
import json
import math
import re
import time

from gamelab.bots.plan_checks import Checks as Base

# the three dyes the town is given (tweak/player_colors.sval): blueprint -> mid colour
# (PetDye.Name writes the name in m_colors[1]) and the tailor's price for the quality
DYES = {"dye_gray": ("414b57", 100), "dye_lemon": ("b8a434", 250), "dye_midnight": ("222270", 500)}
PUZZLE_PFB = "prefabs/puzzles/puzzle_lights_out_small.pfb"
PUZZLE_UNIT = "doodads/buttons/button_magic.unit"
CAT = "hwp_gold_collector_pet"
VENDOR = "hwp_pet_vendor"


class Checks(Base):
    # --- plumbing
    def window(self):
        return self.gl("state").get("window") or ""

    def close_windows(self):
        for _ in range(3):
            if not self.window():
                return
            self.g.key("escape")
            time.sleep(0.4)

    def player(self):
        return self.gl("state").get("player", {})

    def pet(self):
        """The HoH1/vanilla pet (a MiniPet unit) nearest the player, or {}: not the Gold Collector."""
        us = self.gl("near", 1200, "pets/").get("units") or []
        us = [u for u in us if "pets/" in u.get("name", "") and CAT not in u.get("name", "")]
        return min(us, key=lambda u: u.get("dist", 1e9)) if us else {}

    def clear(self):
        """cull, then goblin totems by name: cull and kill tag:enemy leave them (live runs),
        and any live enemy within 350 px keeps Morale off."""
        self.gl("cull")
        self.gl("kill", 800, "totem")
        time.sleep(0.5)

    def foe_at(self, dist):
        """A spawn offset `dist` px out that the pathfinder reaches (a spawn into a wall is
        pushed elsewhere); (dist, 0) when none answers."""
        sp = self.spot(dist)
        return (sp[0], sp[1]) if sp else (dist, 0)

    def cat(self, r=500):
        return self.gl("near", r, CAT).get("units") or []

    def god(self, on=True):
        """hwp god toggles; toggle again when the reply says the other state."""
        want = "god mode on" if on else "god mode off"
        for _ in range(2):
            if want in self.hwp("god", 0.4, until="god mode"):
                return True
        return False

    def hp(self):
        pl = self.player()
        return pl.get("hp", 0), max(1, pl.get("hpMax", 1))

    def set_hp(self, frac):
        """gl hurt (PlayerRecord.hp); without that verb, cht_damage down to the fraction."""
        r = self.gl("hurt", frac)
        if r.get("ok"):
            time.sleep(0.3)
            return
        hp, mx = self.hp()
        if hp > frac * mx:
            self.g.console(f"cht_damage {int(hp - frac * mx)}")
        time.sleep(0.4)

    def hwp_keys(self):
        """The keys of the record's "hwp" dictionary, or None when the record has none."""
        r = self.gl("inspect", "player", "hwp")
        return r.get("keys") or [] if r.get("ok") else None

    def petdye(self):
        """hwp pet dye (pets.debug): (current dye text, pet unit file)."""
        out = self.hwp("pet dye", 0.6, until="| unit")
        # the log line has the reply's colour codes stripped (HWP::Commands::Reply prints Plain)
        m = re.findall(r"\[HWP\] (.*?) \| unit (\S+)", out)
        return m[-1] if m else ("", "")

    @staticmethod
    def dyed(cur, unit):
        """The pet wears a dye: a two-section pet (the text names both sections) is swapped
        for its dye-ready unit copy (players/pets/hwp/dye/); a one-section pet's text names
        a dye instead of "no dye"."""
        if ", " in cur.split(": ", 1)[-1]:
            return "/dye/" in unit
        return bool(cur) and "no dye" not in cur

    def spot(self, dist, avoid=()):
        """An offset `dist` px away the pathfinder reaches on a near-straight path (a detour
        round a wall is past a pet's leash), or None."""
        pl = self.player()
        for a in [0, 180, 90, 270, 45, 135, 225, 315]:
            if a in avoid:
                continue
            dx, dy = round(dist * math.cos(math.radians(a))), round(dist * math.sin(math.radians(a)))
            pf = self.gl("pathfind", pl.get("x", 0) + dx, pl.get("y", 0) + dy)
            if pf.get("ok") and pf.get("nodes", 0) > 0 and pf.get("length", 1e9) <= dist * 1.25:
                return dx, dy, a
        return None

    def gone(self, unit, filt, wait=8, r=1200):
        """Whether unit id `unit` (a `filt` match) leaves the floor within `wait` s."""
        end = time.time() + wait
        while time.time() < end:
            ids = {u["unit"] for u in self.gl("near", r, filt).get("units") or []}
            if unit not in ids:
                return True
            time.sleep(0.5)
        return False

    # --- pets s12: a character from before HWP
    def legacy_record(self):
        """The fixture character was made with only the GameLab mods: its record has no HWP pet
        toggles (no pets.options_set) and vanilla's pet-options 0."""
        po = self.gl("inspect", "player", "pet-options").get("value")
        keys = self.hwp_keys()
        self.legacy_keys = keys
        self.flag("legacy_char", po in (0, -1) and "pets.options_set" not in (keys or []),
                  f"pet-options {po}, hwp keys {keys}")

    def legacy_run(self):
        """pets s12: with the toggles never touched, the pet picks up gold, materials and a
        health pickup (owner below 30 %) at once."""
        self.hwp("set pets.debug true", 0.4)
        self.start_floor(0)
        self.gl("cull")
        time.sleep(1.5)
        g0 = self.gold()
        n, left = 0, -1
        for _ in range(3):
            n = self.gold_drop()
            left = self.gold_left(8)
            if left == 0 or not hasattr(self, "drop_dir"):
                break
            self.bad_dirs = getattr(self, "bad_dirs", set()) | {self.drop_dir}
            del self.drop_at
            self.dropped = []
        g1 = self.gold()
        self.flag("legacy_pet_gold", n > 0 and left == 0 and g1 > g0, f"{n} drop(s) at {self.drop_at}, {left} left, gold {g0} -> {g1}")
        w0 = (self.gl("inv").get("materials") or {}).get("wood", 0)
        d = self.gl("drop", "wood", 5, *self.drop_at)
        ok = d.get("ok") and self.gone(d.get("unit"), "materials/", 8)
        w1 = (self.gl("inv").get("materials") or {}).get("wood", 0)
        self.flag("legacy_pet_materials", ok and w1 > w0, f"drop {d.get('name')}, wood {w0} -> {w1}")
        self.set_hp(0.2)
        h0, mx = self.hp()
        a = self.gl("spawn", "items/pickups/health_apple.unit", *self.drop_at)
        ok = a.get("ok") and self.gone(a.get("unit"), "health_apple", 8)
        h1, _ = self.hp()
        self.flag("legacy_pet_potion", ok and h1 > h0, f"{a.get('name')} fetched {ok}, hp {h0} -> {h1} / {mx}")
        self.set_hp(1.0)
        keys = self.hwp_keys()
        self.flag("legacy_toggles_untouched", "pets.options_set" not in (keys or []), f"hwp keys {keys}")

    # --- pets s9/s10: the tailor
    def tailor(self):
        """The tailor's building and NPC: the story flag its unit and building want, the building
        (gl build: the town builder's own AddBuilding), a refresh; spawned when still missing."""
        self.g.console("cht_set_flag mission_story_unlocked_dyer 1 1")
        time.sleep(0.3)
        b = self.gl("build", "tailor")
        self.gl("townrefresh")
        time.sleep(3)
        self.npc("npc_dyer", "actors/npcs/town/npc_dyer.unit")
        return b

    def use_dyer(self):
        """Use the tailor. A fixture character (gl char) has no portrait pieces, and the vanilla
        dyer's preview throws on a missing one (GetPortraitModel(null)) and leaves the game
        paused with the NPC stuck mid-interaction, so give it the defaults first."""
        if not getattr(self, "portrait_done", False):
            r = self.gl("portrait")
            self.portrait_done = bool(r.get("ok"))
            self.portrait_note = f"portrait {r.get('before')} -> {r.get('after')} pieces, added {r.get('added')}"
        self.close_windows()
        u = self.gl("use", "npc_dyer")
        time.sleep(0.8)
        return u, self.window()

    def dyer_nopet(self):
        """pets s9: without a pet out the tailor opens the vanilla dyer straight away."""
        b = self.tailor()
        u, w = self.use_dyer()
        self.flag("dyer_nopet_direct", "EquipmentDyerWindow" in w,
                  f"build {b.get('ok')}, {getattr(self, 'portrait_note', 'no portrait')}, use {u.get('ok')} {u.get('error') or u.get('unit')}, window {w!r}")
        self.close_windows()

    def dyer_choice(self):
        """pets s9: with a pet out the tailor asks Dye gear / Dye pet; gear is the vanilla dyer."""
        self.hwp("set pets.debug true", 0.4)
        u, w = self.use_dyer()
        txt = self.widget("pet-dye").get("text", "")
        self.flag("dyer_choice_opens", w == "HWPDyerChoice" and bool(self.widget("gear-btn")) and bool(self.widget("pet-btn")),
                  f"window {w!r}, {txt!r}")
        self.gl("press", "gear-btn")
        time.sleep(0.8)
        w2 = self.window()
        self.flag("dyer_gear_vanilla", "EquipmentDyerWindow" in w2, f"gear -> {w2!r}")
        self.close_windows()

    def dye_menu(self):
        """Tailor -> Dye pet; (window, dyes unlocked, rows)."""
        u, w = self.use_dyer()
        if w == "HWPDyerChoice":
            self.gl("press", "pet-btn")
            time.sleep(0.8)
            w = self.window()
        m = re.findall(r"\((\d+) dyes", self.widget("points").get("text", ""))
        return w, int(m[-1]) if m else -1, self.gl("presslist", "list").get("count", -1)

    def press_row(self, idx):
        """One row of the dye list: (gold paid, message)."""
        g0 = self.gold()
        r = self.gl("presslist", "list", idx)
        time.sleep(0.7)
        return g0 - self.gold(), self.widget("message").get("text", "") if r.get("ok") else f"presslist: {r.get('error')}"

    def dye_pet(self):
        """pets s10: the pet window lists the town's unlocked dyes in their colours at the
        quality's price; a pick pays and re-makes the pet in the dye."""
        self.hwp("set pets.debug true", 0.4)
        self.set_gold(100000)
        w0, n0, rows0 = self.dye_menu()
        self.close_windows()
        for bp in DYES:
            self.g.console("cht_add_blueprint " + bp)
            time.sleep(0.2)
        pet0 = self.pet()
        cur0, unit0 = self.petdye()
        w, n1, rows1 = self.dye_menu()
        self.flag("dye_menu_open", w == "HWPPetDyeMenu", f"{w0!r} then {w!r}, state {self.widget('state').get('text', '')!r}")
        self.flag("dye_lists_unlocked", n1 - n0 == len(DYES), f"{n0} -> {n1} unlocked, rows {rows0} -> {rows1}")
        on_page = min(max(n1, 0), 10)
        # rows: the section switch of a two-section pet, the remove row once dyed, the dyes,
        # then prev / next (PetDye.as HWPPetDyeMenu.Refresh)
        head = rows1 - on_page - (1 if n1 > 10 else 0)
        seen = {}
        for k in range(on_page):
            paid, msg = self.press_row(head + k if k == 0 else head + 1 + k)
            hexes = re.findall(r"\\c([0-9a-fA-F]{6})", msg)
            seen[hexes[-1].lower() if hexes else f"?{k}"] = (paid, msg)
        self.close_windows()
        time.sleep(1)
        pet1 = self.pet()
        cur1, unit1 = self.petdye()
        want = {h: c for h, c in DYES.values()}
        self.flag("dye_in_colour", all(h in seen and "Dyed" in seen[h][1] for h in want),
                  "; ".join(f"{h}: {v[1]!r}" for h, v in seen.items()))
        self.flag("dye_price_paid", all(seen.get(h, (None,))[0] == c for h, c in want.items()),
                  ", ".join(f"{h} paid {v[0]}" for h, v in seen.items()))
        if n0 == 0:
            self.flag("dye_only_unlocked", set(seen) == set(want), f"listed {sorted(seen)}")
        else:
            self.notes.append(f"dye_only_unlocked: skipped, the town had {n0} dye(s) before")
        self.flag("dye_pet_remade", pet0.get("unit") != pet1.get("unit") and self.dyed(cur1, unit1),
                  f"pet {pet0.get('unit')} {unit0} ({cur0!r}) -> {pet1.get('unit')} {unit1} ({cur1!r})")

    def dye_floor(self):
        """pets s10: the dye is still on after a floor change (run from legacy_run's floor)."""
        self.hwp("set pets.debug true", 0.4)
        if self.gl("state").get("phase") != "mission":
            self.start_floor(0)
        cur0, unit0 = self.petdye()
        self.next_floor()
        time.sleep(3)
        cur1, unit1 = self.petdye()
        self.flag("dye_kept_floor", self.dyed(cur0, unit0) and self.dyed(cur1, unit1),
                  f"{cur0!r} {unit0} -> {cur1!r} {unit1}")

    def dye_restart(self):
        """pets s10: the dye is still on after quitting and loading the character."""
        self.hwp("set pets.debug true", 0.4)
        time.sleep(1)
        cur, unit = self.petdye()
        self.flag("dye_kept_restart", self.dyed(cur, unit), f"{cur!r} {unit}")

    def dye_remove(self):
        """pets s10: "Remove the dye" is free and gives the plain pet back."""
        self.hwp("set pets.debug true", 0.4)
        self.npc("npc_dyer", "actors/npcs/town/npc_dyer.unit")
        self.set_gold(5000)
        cur0, unit0 = self.petdye()
        w, n, rows = self.dye_menu()
        # the remove row follows the section switch of a two-section pet
        two = ", " in cur0.split(": ", 1)[-1]
        paid, msg = self.press_row(1 if two else 0)
        self.close_windows()
        time.sleep(1)
        cur1, unit1 = self.petdye()
        self.flag("dye_remove_free", paid == 0 and "washes out" in msg, f"{w!r}, paid {paid}, {msg!r}")
        self.flag("dye_removed_plain", not self.dyed(cur1, unit1) and "/dye/" not in unit1,
                  f"{cur0!r} {unit0} -> {cur1!r} {unit1}")

    # --- pets s2/s4/s5: a fresh character's pet in a run
    def pets_setup(self):
        self.gl("char", "paladin", "LabPets")
        self.wait_phase("town", 60)
        time.sleep(2)
        self.petshop()
        self.hwp("set pets.debug true", 0.4)
        st = self.hwp("pet xp 20000", 0.8, until="level")
        self.flag("pets_ready", bool(self.pet()) and "point" in st, st.strip()[-160:])
        self.start_floor(0)
        self.gl("cull")
        time.sleep(2)

    def spend(self, skill, n):
        out = ""
        for _ in range(n):
            out = self.hwp(f"pet skill {skill}", 0.4, until="level")
        return out.strip()[-120:]

    def smash(self):
        """pets s4: a pot beside the pet stays whole without Smash and breaks once a point is in."""
        pl, pet = self.player(), self.pet()
        dx = round(pet.get("x", pl.get("x", 0)) - pl.get("x", 0)) + 24
        dy = round(pet.get("y", pl.get("y", 0)) - pl.get("y", 0))
        v = self.gl("spawn", "doodads/containers/vase_small.unit", dx, dy)
        time.sleep(4)
        ids = {b["unit"] for b in self.gl("breakables", 400).get("breakables") or []}
        before = v.get("unit") in ids
        st = self.spend("smash", 1)
        broke = False
        end = time.time() + 12
        while time.time() < end and not broke:
            time.sleep(0.5)
            broke = v.get("unit") not in {b["unit"] for b in self.gl("breakables", 400).get("breakables") or []}
        self.flag("smash_control", v.get("ok") and before, f"pot {v.get('unit')} at {dx},{dy} whole after 4 s without Smash")
        self.flag("smash_breaks_pots", before and broke, f"{st}; pet {pet.get('dist')} px from the player")

    def hp_jumps(self, secs):
        """Heals of >= 7 % max hp from one 0.25 s sample to the next (Mend heals 4-10 %;
        regen is far slower), and the hp trace."""
        jumps, trace = [], []
        h0, mx = self.hp()
        end = time.time() + secs
        while time.time() < end:
            time.sleep(0.25)
            h1, mx = self.hp()
            if h1 - h0 >= 0.07 * mx:
                jumps.append(h1 - h0)
            trace.append(h1)
            h0 = h1
        return jumps, trace[::4], mx

    def mend(self):
        """pets s5: Mend heals the owner below 80 % hp and not above."""
        st = self.spend("mend", 5)
        self.set_hp(0.5)
        low, tl, mx = self.hp_jumps(10)
        self.set_hp(0.9)
        high, th, _ = self.hp_jumps(10)
        self.set_hp(1.0)
        self.flag("mend_heals_below_80", len(low) >= 1, f"{st}; at 50 %: heals {low}, hp {tl} / {mx}")
        self.flag("mend_idle_above_80", len(high) == 0, f"at 90 %: heals {high}, hp {th}")

    def stunned(self, filt, secs):
        """Whether an actor matching filt carries a stun-tagged buff within secs; its distances."""
        dists = []
        end = time.time() + secs
        while time.time() < end:
            for a in self.gl("actorbuffs", 400, filt).get("actors") or []:
                dists.append(round(a.get("dist", 0)))
                if any("stun" in b.get("tags", []) or "stun" in b.get("name", "") for b in a.get("buffs", [])):
                    return True, dists
            time.sleep(0.3)
        return False, dists

    def stun(self):
        """pets s5: Stun (rank 5, every 6 s) never takes an elite, and takes a goblin."""
        self.god(True)
        st = self.spend("stun", 5)
        self.clear()
        at = self.foe_at(60)
        mark = len(self.g.read_log())
        e = self.gl("spawn", "actors/humans/bandits/bandit_brute_elite.unit", *at)
        hit_e, de = self.stunned("bandit_brute_elite", 13)
        self.gl("kill", 600, "bandit_brute_elite")
        time.sleep(1)
        log_e = re.findall(r"stun rank \d+: \d+ target", self.g.read_log()[mark:])
        mark = len(self.g.read_log())
        gb = self.gl("spawn", "actors/beasts/goblins/goblin_redcap.unit", *at)
        hit_g, dg = self.stunned("goblin_redcap", 13)
        log_g = re.findall(r"\[HWP:pets\] (peer \d+ stun rank \d+: \d+ target)", self.g.read_log()[mark:])
        self.clear()
        near = sum(1 for d in de if d <= 160)
        self.flag("stun_skips_elite", e.get("ok") and not hit_e and near >= 10 and not log_e,
                  f"{st}; elite {e.get('name')} within 160 px in {near}/{len(de)} samples {de[:12]}, host log {log_e}")
        self.flag("stun_hits_goblin", gb.get("ok") and hit_g, f"{gb.get('name')} dists {dg[:12]}, host log {log_g[:2]}")

    def morale_state(self):
        """(buff on the player, its HUD icon shown, how): gl state's buff names; the icon from
        the buffs verb (ActorBuff.m_hudIcon visible), else any visible BuffWidget on the HUD
        (the floor is culled: no other buff is expected)."""
        on = ".hwp.pets.buff.morale" in (self.player().get("buffs") or [])
        b = self.gl("buffs")
        if b.get("ok"):
            mine = [x for x in b.get("buffs") or [] if x.get("name") == ".hwp.pets.buff.morale"]
            return on, any(x.get("icon") for x in mine), f"buffs {mine}"
        n = 0
        for root in self.gl("widgets", 6).get("roots", []):
            if str(root.get("root", "")).startswith("HUD"):
                n += sum(1 for x in root.get("nodes", []) if x.get("type") == "BuffWidget" and x.get("visible"))
        return on, n > 0, f"{n} visible BuffWidget(s) on the HUD"

    def foes(self):
        """Live actors within 350 px (Morale's combat radius), for the note."""
        return [(a.get("name", "").rsplit("/", 1)[-1], round(a.get("dist", 0)))
                for a in self.gl("actorbuffs", 350).get("actors") or []][:8]

    def morale_on(self):
        """pets s5: Morale out of combat: the buff and its icon."""
        self.clear()
        st = self.spend("morale", 5)
        time.sleep(3)
        on, icon, how = self.morale_state()
        self.flag("morale_out_of_combat", on, f"{st}; actors within 350: {self.foes()}")
        self.flag("morale_icon_shown", on and icon, how)

    def morale_combat(self):
        """pets s5: an enemy within 350 px: no Morale, no icon (the 2.6 s buff runs out)."""
        self.god(True)
        e = self.gl("spawn", "actors/humans/bandits/bandit_brute.unit", *self.foe_at(150))
        time.sleep(4)
        on, icon, how = self.morale_state()
        foes = [round(a.get("dist", 0)) for a in self.gl("actorbuffs", 400, "bandit_brute").get("actors") or []]
        self.flag("morale_gone_in_combat", e.get("ok") and foes and min(foes) <= 350 and not on and not icon,
                  f"enemy at {foes}; {how}")

    def morale_after(self):
        """pets s5: the enemy dead, Morale and its icon are back."""
        self.clear()
        time.sleep(3.5)
        on, icon, how = self.morale_state()
        self.flag("morale_back_after_combat", on and icon, f"{how}; actors within 350: {self.foes()}")
        self.god(False)

    def pet_samples(self, secs=2.0):
        """Pet positions over secs: (last pet, how far it moved from the first sample)."""
        first, last, moved = None, {}, 0.0
        end = time.time() + secs
        while time.time() < end:
            last = self.pet()
            if last:
                if first is None:
                    first = (last["x"], last["y"])
                moved = max(moved, math.hypot(last["x"] - first[0], last["y"] - first[1]))
            time.sleep(0.4)
        return last, moved

    def puzzle_wait(self):
        """pets s2: the pet follows a walk; with a puzzle (vanilla lights-out) at the end of
        the same walk it stays outside, still, while the player is in, and follows again when
        the player comes out. querycmp says what each scene query sees of the buttons (PetWait
        fetches with FetchAllUnits: the buttons have no collision, QueryCircle misses them)."""
        self.gl("cull")
        pl = self.player()
        sx, sy = pl.get("x", 0), pl.get("y", 0)
        sp = self.spot(220)
        if sp is None:
            self.flag("puzzle_spot", False, "no straight 220 px path from the floor start")
            return
        dx, dy, a = sp
        # control: the same walk with no puzzle
        r = self.p.path_to(sx + dx, sy + dy, tol=8, timeout=10)
        time.sleep(2.5)
        c = self.pet()
        self.flag("pet_follows_control", r.ok and bool(c) and c["dist"] < 90, f"walk {r.result}, pet {c.get('dist')} px")
        self.p.path_to(sx, sy, tol=8, timeout=10)
        time.sleep(2.5)
        pf = self.gl("prefab", PUZZLE_PFB, dx, dy)
        time.sleep(1)
        r = self.p.path_to(sx + dx, sy + dy, tol=8, timeout=12)
        time.sleep(2.5)
        q = self.gl("querycmp", 140, PUZZLE_UNIT)
        p1, moved = self.pet_samples(2.0)
        # a step inside the room: the pet still does not move
        px, py = -dy / 220 * 30, dx / 220 * 30
        self.p.path_to(sx + dx + px, sy + dy + py, tol=6, timeout=6)
        time.sleep(1)
        p2, moved2 = self.pet_samples(1.6)
        # the step: where the pet is now against where it was parked before it (a follower
        # would have walked the 30 px before the samples start)
        shift = math.hypot(p2["x"] - p1["x"], p2["y"] - p1["y"]) if p1 and p2 else 1e9
        self.flag("pet_waits_outside_puzzle", pf.get("ok") and r.ok and bool(p1) and p1["dist"] > 90 and moved < 10
                  and moved2 < 10 and shift < 10,
                  f"prefab {pf.get('ok')} at {dx},{dy}; walk {r.result}; pet {p1.get('dist')} px off, moved {moved:.0f} / {moved2:.0f} px, "
                  f"{shift:.0f} px over the step; "
                  f"querycmp {json.dumps({k: q.get(k) for k in ('querySensors', 'querySolid', 'fetchAll', 'fetchType', 'levelType', 'levelNearest', 'queryPuzzle', 'queryUnits')})}")
        r = self.p.path_to(sx, sy, tol=8, timeout=12)
        time.sleep(3)
        p3 = self.pet()
        self.flag("pet_follows_after_puzzle", r.ok and bool(p3) and p3["dist"] < 90, f"walk out {r.result}, pet {p3.get('dist')} px")

    # --- goldpet s2/s3
    def vendor(self):
        self.close_windows()
        end = time.time() + 10
        while time.time() < end and not self.gl("near", 8000, VENDOR).get("units"):
            time.sleep(0.5)
        self.gl("use", VENDOR)
        time.sleep(0.6)
        return self.window()

    def lodge_up(self):
        r = self.gl("buildup", "hunters_cabin")
        time.sleep(2)
        self.gl("townrefresh")
        time.sleep(3)
        return r

    def gp_gates(self):
        """goldpet s2: tier 2 needs Lodge tier 2, tier 3 needs Lodge tier 3."""
        b = self.gl("build", "hunters_cabin")
        self.gl("townrefresh")
        time.sleep(3)
        self.set_gold(10000)
        self.vendor()
        self.gl("press", "buy-tier1")
        time.sleep(1.5)
        self.close_windows()
        self.flag("gp_tier1_bought", self.gold() == 0 and bool(self.cat()), f"build {b.get('ok')}, gold {self.gold()}, cat {self.cat()[:1]}")
        self.set_gold(60000)
        self.vendor()
        req = self.widget("tier2-req").get("text", "")
        self.gl("press", "buy-tier2")
        time.sleep(1)
        g = self.gold()
        self.close_windows()
        self.flag("gp_tier2_needs_lodge2", g == 60000 and req == "Requires Hunter Lodge Tier 2", f"lodge 0: {req!r}, gold 60000 -> {g}")
        up = self.lodge_up()
        self.set_gold(60000)
        w = self.vendor()
        req = self.widget("tier2-req").get("text", "")
        self.gl("press", "buy-tier2")
        time.sleep(1.5)
        g = self.gold()
        self.close_windows()
        self.set_gold(200000)
        self.vendor()
        status = self.widget("tier-status").get("text", "")
        req3 = self.widget("tier3-req").get("text", "")
        self.gl("press", "buy-tier3")
        time.sleep(1)
        g3 = self.gold()
        self.close_windows()
        self.flag("gp_tier2_at_lodge2", up.get("variation") == 1 and g == 10000 and "Tier 2" in status,
                  f"buildup {up.get('ok')} -> {up.get('variation')}, {w!r} {req!r}, gold 60000 -> {g}, {status!r}")
        self.flag("gp_tier3_needs_lodge3", g3 == 200000 and req3 == "Requires Hunter Lodge Tier 3", f"lodge 1: {req3!r}, gold 200000 -> {g3}")
        up = self.lodge_up()
        self.vendor()
        req3 = self.widget("tier3-req").get("text", "")
        self.close_windows()
        # not bought: the run checks are tier 2's
        self.flag("gp_tier3_ready_at_lodge3", up.get("variation") == 2 and req3 == "Ready to upgrade!",
                  f"buildup -> {up.get('variation')}, {req3!r}")

    def gp_summon(self):
        """goldpet s3: a missing cat: the vendor shows Summon, and Summon brings it back."""
        c0 = self.cat()
        d = self.gl("unitdestroy", 800, CAT)
        time.sleep(1.5)
        c1 = self.cat()
        self.vendor()
        sb = self.widget("summon-button")
        self.gl("press", "summon-button")
        time.sleep(2)
        self.close_windows()
        time.sleep(1)
        c2 = self.cat()
        # (no cat to start with: the town refresh lost it, which is what Summon is for)
        self.flag("gp_summon_shown", not c1 and bool(sb.get("visible")),
                  f"cat {len(c0)} -> destroyed {d.get('count')} -> {len(c1)}; button {sb}")
        self.flag("gp_summon_brings_back", not c1 and bool(c2), str(c2[:1]))

    def gp_run(self):
        """goldpet s2/s3 in a run: the tier 2 cat picks materials up and follows to the next floor."""
        self.start_floor(0)
        self.gl("cull")
        time.sleep(2)
        c = self.cat()
        self.flag("gp_cat_in_run", bool(c), str(c[:1]))
        bad, ok, note = set(), False, ""
        for _ in range(3):
            sp = self.spot(100, bad)  # inside the cat's 200 px seek radius wherever it stands
            if sp is None:
                break
            w0 = (self.gl("inv").get("materials") or {}).get("wood", 0)
            d = self.gl("drop", "wood", 5, sp[0], sp[1])
            ok = d.get("ok") and self.gone(d.get("unit"), "materials/", 10)
            w1 = (self.gl("inv").get("materials") or {}).get("wood", 0)
            note = f"wood at {sp[:2]}: fetched {ok}, wood {w0} -> {w1}"
            ok = ok and w1 > w0
            if ok:
                break
            bad.add(sp[2])
        self.flag("gp_tier2_picks_materials", ok, note)
        self.next_floor()
        time.sleep(3)
        c = self.cat()
        self.flag("gp_back_after_floor", bool(c), str(c[:1]))
        self.to_town()

    def gp_reload(self):
        """goldpet s3/s2 after quitting and loading the character: the cat is back; in a run it
        picks up an XP scroll (after the restart: the fixture's readback wants level 1)."""
        time.sleep(3)
        c = self.cat()
        self.flag("gp_back_after_reload", bool(c), str(c[:1]))
        self.start_floor(0)
        self.gl("cull")
        time.sleep(2)
        bad, ok, note = set(), False, ""
        for _ in range(3):
            sp = self.spot(100, bad)  # inside the cat's 200 px seek radius wherever it stands
            if sp is None:
                break
            x0 = self.gl("inspect", "player", "experience").get("value", 0)
            s = self.gl("spawn", "items/pickups/exp_1.unit", sp[0], sp[1])
            ok = s.get("ok") and self.gone(s.get("unit"), "exp_1", 10)
            x1 = self.gl("inspect", "player", "experience").get("value", 0)
            note = f"scroll at {sp[:2]}: fetched {ok}, xp {x0} -> {x1}"
            ok = ok and x1 != x0
            if ok:
                break
            bad.add(sp[2])
        self.flag("gp_tier2_picks_xp_scroll", ok, note)
        self.to_town()


def run(p, sections="", **_):
    c = Checks(p)
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
