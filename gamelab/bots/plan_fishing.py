"""Test-plan checks for fishing (mods/fishing) and the Gambler's Sell (mods/gambler, the
core market). Same style as plan_checks: each section flags booleans, the scenario's
expect asserts them, measured values go in the notes. Each section makes its own fresh
character with `gl char`.

Sections:
- fish_sword: town catches (`hwp fishing catch <tier>`, debug) as bag items: stars in the
  name, quality by stars, the town item levels, wielded as a sword (the longsword attack),
  the equipped fish's tooltip (stars, ilvl) on the character screen (fishing s5).
- fish_hit: a wielded fish's swing on a Bandit Keep floor takes a dummy's HP (fishing s5).
- fish_enchant: an uncommon fish at an enchanter (shop level set, as the town's prefab
  does): Upgrade, then Enchant and a new modifier; the worked fish is no ware any more and
  Sell leaves it in the bag while fresh 1/2/3-star fish sell; Enchant on a fresh (unworked)
  uncommon / rare fish, which is caught with its quality's modifiers (fishing s6).
- gambler_sell: fish of 1/2/3 stars, crops and a worked fish at the Gambler: the Sell
  caption, gold for crops, tokens for fish, the token line, the worked fish kept (gambler s7).
- rod_slot: the character screen's rod slot and its tooltip, before and after a rod (fishing s13).
- traps_run: three traps, a run at g_timescale 16 until 20+ game minutes, back to town: the
  rolls, the full-trap units and icon, walking up to one (fishing s9).
- run_spot: a floor's fishing spot beside a well (run_chance 100): no bait, three casts
  reeled through the window's own bar (gl sweepclick), loot and floor-level fish, the 4th
  cast refused (fishing s10).
- run_stars: rod 4, 30 casts a floor at a debug hole: the zone width of each bite gives
  the rolled tier on a first-half floor, a second-half floor and the boss floor (fishing s11).

Verbs: bagitems, wield, shoplevel, wcaption, wchildren, pressin, sweepclick
(mods/gamelab-hands/scripts/GameLab/Verbs_fishing.as) and tooltip (Verbs_farming.as)."""
import json
import math
import re
import time
from pathlib import Path

from gamelab.bots.plan_checks import Checks as Base

REPO = Path(__file__).resolve().parents[2]
# mods/fishing/scripts/HWP/Fishing/FishingModule.as
TIER = {"perch": 1, "carp": 1, "trout": 2, "pike": 2, "salmon": 3, "sturgeon": 3,
        "golden_carp": 4, "abyssal_eel": 4}
STARS = {1: 1, 2: 1, 3: 2, 4: 3}            # StarOf
QUALITY = {1: 1, 2: 2, 3: 4}                # stars -> Item::Quality bits (common, uncommon, rare)
MODS = {1: 0, 2: 1, 4: 2}                   # Equipment::EquipmentModifiersPerQuality by quality
TOKENS = {1: 1, 2: 3, 3: 5}                 # bet tokens per fish by stars
FISH_ILVL = {1: 1, 2: 5, 3: 10, 4: 15}      # town catches, per tier
ZONE_WIDTH = [40, 26, 16, 10]
MARKER_SPEED = [0.18, 0.23, 0.28, 0.34]
BAR_WIDTH, MARKER_WIDTH, BITE_WINDOW = 240, 3, 2500
ROD_NAMES = {1: "Driftwood Rod", 2: "Sturdy Rod", 3: "Sea Rod", 4: "Captain's Rod"}
TRAP_FULL = "doodads/hwp/fish_trap_full.unit"
TRAP_TO_SPOT = (44, -40)                    # a trap sits at its coast spot + (TRAP_DX, TRAP_DY) = (-44, 40)
WELLS = ("well_default", "well_dark_halls", "barrel_refill", "crypt_refill", "fountain")


def reel_table(rod):
    """(zone widths, marker speeds) per fish tier for a rod (ZoneScale / SpeedScale)."""
    zs, ss = 1 + 0.2 * (rod - 1), 1 - 0.1 * (rod - 1)
    return [min(int(w * zs + 1e-4), BAR_WIDTH // 2) for w in ZONE_WIDTH], [s * ss for s in MARKER_SPEED]


def tier_of(zw, rod):
    widths, _ = reel_table(rod)
    return min(range(4), key=lambda i: abs(widths[i] - zw)) + 1


def plain(s):
    """A game string without its colour codes (\\cRRGGBB, \\d)."""
    return re.sub(r"\\c[0-9a-fA-F]{6}|\\d", "", s or "")


def fish_tier(item):
    fid = (item or {}).get("id", "")
    return TIER.get(fid[len("hwp_fish_"):], 0) if fid.startswith("hwp_fish_") else 0


class Checks(Base):
    # --- plumbing
    def fresh(self, name):
        r = self.gl("char", "paladin", name)
        self.wait_phase("town", 60)
        time.sleep(2)
        self.hwp("set fishing.debug 1")
        return r.get("ok")

    def bag(self):
        return self.gl("bagitems")

    def fish(self, b=None):
        b = b or self.bag()
        return [it for it in b.get("bag", []) if fish_tier(it)]

    def catch(self, tier):
        out = self.hwp(f"fishing catch {tier}", 0.4, until="[HWP] Caught")
        m = re.findall(r"\[HWP\] Caught: ([^!]*)!", plain(out))
        return m[-1] if m else ""

    def tooltip(self, wid):
        r = self.gl("tooltip", wid)
        return [plain(t) for t in r.get("texts", [])], r

    def mats(self):
        return self.gl("inv").get("materials", {})

    def window(self):
        return self.gl("state").get("window") or ""

    def close_windows(self, n=4):
        for _ in range(n):
            if not self.window():
                return
            self.g.key("escape")
            time.sleep(0.5)

    def exceptions_since(self, mark):
        """Script exceptions since the log offset mark. A verb's own call chain is caught by
        the probe ("exception in verb ..." reply, no "Script exception" line), so the
        heartbeat's exceptions count is compared too (waits for a heartbeat after mark)."""
        end = time.time() + 2.5
        while time.time() < end and '"ev":"hb"' not in self.g.read_log()[mark:]:
            time.sleep(0.2)
        log = self.g.read_log()
        lines = log[mark:].splitlines()
        out = []
        for i, ln in enumerate(lines):
            if "Script exception" in ln or "exception in verb" in ln:
                out.append(" / ".join(x.strip()[-110:] for x in lines[i:i + 3]))
        before = re.findall(r'"ev":"hb".*?"exceptions":(\d+)', log[:mark])
        after = re.findall(r'"ev":"hb".*?"exceptions":(\d+)', log[mark:])
        if before and after and int(after[-1]) > int(before[-1]):
            out.append(f"heartbeat exceptions {before[-1]} -> {after[-1]}")
        return out

    def enchant_view(self):
        """Enchant on the main hand (entry 0) of the open enchanter: (modifier entries
        [{id, caption, selected}], candidates the generator offered ("Num item mods" print),
        exceptions, top-level groups {id: visible})."""
        btns, _ = self.entry_buttons()
        mark = len(self.g.read_log())
        key = next((b for b, fn in btns.items() if fn == "enchant"), None)
        if key:
            self.gl("pressin", "0", key)
            time.sleep(0.6)
        ex = self.exceptions_since(mark)
        cand = re.findall(r"Num item mods: (\d+)", self.g.read_log()[mark:])
        # the window's own print: which item the view is for
        self.enchanting = (re.findall(r"Now enchanting: ([^\r\n]*)", self.g.read_log()[mark:]) or [""])[-1].strip()
        groups = {n["id"]: n["visible"] for n in self.gl("wchildren", "^enchant", 1).get("nodes", [])}
        entries, cur = [], None
        for n in self.gl("wchildren", "enchant-list", 2).get("nodes", []):
            if n["depth"] == 1:
                cur = {"id": n["id"], "caption": n["caption"], "selected": False}
                entries.append(cur)
            elif cur is not None and n["id"] == "selected":
                cur["selected"] = n["visible"]
        return entries, int(cand[-1]) if cand else -1, ex, groups, btns

    def blueprints(self):
        """Every modifier blueprint in the town (base cheat; the scenario sets e_cheats 1)."""
        mark = len(self.g.read_log())
        self.g.console("cht_add_all_blueprints")
        end = time.time() + 4
        while time.time() < end and "adding ItemModifier to town" not in self.g.read_log()[mark:]:
            time.sleep(0.25)
        return len(re.findall(r"adding ItemModifier to town", self.g.read_log()[mark:]))

    def reel(self, rod, timeout_ms=9000, report="log,casts"):
        """One cast and reel through gl sweepclick; the sweepclick event (result, zx, zw, texts)."""
        widths, speeds = reel_table(rod)
        pairs = ",".join(f"{w}:{s:.5f}" for w, s in zip(widths, speeds))
        r = self.gl("sweepclick", "cast-btn", "zone", BAR_WIDTH, MARKER_WIDTH, pairs, timeout_ms, BITE_WINDOW, report)
        if not r.get("ok"):
            return {"result": "error", "error": r.get("error", "")}
        cid = r["id"]
        ev = self.g.wait_gl(lambda o: o.get("ev") == "sweepclick" and o.get("id") == cid, timeout_ms / 1000 + 8)
        return ev or {"result": "noevent"}

    def open_spot(self, unit_filter):
        """Walk to the nearest unit matching unit_filter and use it (the fishing window)."""
        us = self.gl("near", 8000, unit_filter).get("units") or []
        if not us:
            return None, f"no {unit_filter}"
        r = self.p.use(us[0]["unit"], timeout=60)
        time.sleep(0.8)
        how = f"{r.result}: {r.reason}"
        if "FishingMenu" not in self.window():
            self.gl("use", unit_filter.split("/")[-1].replace(".unit", ""))
            time.sleep(0.8)
            how += " (then gl use)"
        return us[0], how

    def enchanter(self):
        """The enchanter beside the player (its story flag set), at shop level 3."""
        self.hwp("unlockflags", 1.0)
        self.npc("npc_enchanter", "actors/npcs/town/npc_enchanter.unit")
        r = self.gl("shoplevel", "npc_enchanter", 3)
        return r

    def entry_buttons(self, entry="0"):
        """The enchanter list's entry (its equipment slot index) and its option buttons:
        {button id: confirm func} for the visible ones."""
        r = self.gl("wchildren", "equipment-list", 3)
        nodes = r.get("nodes", [])
        out, inside = {}, False
        for n in nodes:
            if n["depth"] == 1:
                inside = n["id"] == entry
                continue
            if inside and n.get("confirm") is not None and n.get("visible"):
                out[n["id"]] = n["confirm"]
        return out, nodes

    def upgrade_main(self):
        """Enchanter Upgrade on the main hand (entry 0): the main hand after, the dust paid, notes."""
        btns, _ = self.entry_buttons()
        key = next((b for b, f in btns.items() if f == "upgrade"), None)
        if not key:
            return None, 0, f"no upgrade button: {btns}"
        d0 = self.mats().get("dust", 0)
        self.gl("pressin", "0", key)
        time.sleep(0.6)
        return self.bag().get("main", {}), d0 - self.mats().get("dust", 0), f"{btns}"

    # --- fishing s5
    def fish_sword(self):
        self.fresh("LabAngler")
        names = {t: self.catch(t) for t in (1, 2, 3, 4)}
        fish = self.fish()
        by_tier = {fish_tier(f): f for f in fish}
        self.flag("fish_caught", len(by_tier) == 4, json.dumps({t: names[t] for t in names}))
        stars_ok = all(f"({STARS[t]} star)" in plain(by_tier[t]["name"]) for t in by_tier)
        self.flag("fish_name_stars", stars_ok and len(by_tier) == 4,
                  "; ".join(f"t{t}: {plain(f['name'])}" for t, f in sorted(by_tier.items())))
        self.flag("fish_quality_by_stars", all(by_tier[t]["quality"] == QUALITY[STARS[t]] for t in by_tier),
                  "; ".join(f"t{t} q{f['quality']}" for t, f in sorted(by_tier.items())))
        lv = {t: by_tier[t]["ilvl"] for t in by_tier}
        # worms catch tiers 1-2 only (BAIT_MAX_TIER): those are the town's usual fish
        self.flag("fish_town_ilvl", all(1 <= lv.get(t, 0) <= 6 for t in (1, 2)),
                  f"ilvl by tier {lv} (FISH_ILVL {FISH_ILVL}; shrimp/squid catches, tiers 3-4, are 10/15)")
        # a fresh 2/3-star fish has the modifiers its quality has (the enchanter reads them)
        self.flag("fresh_fish_has_mods", len(by_tier) == 4 and all(
            len(f["mods"]) == MODS.get(f["quality"], -1) for f in by_tier.values()),
            "; ".join(f"t{t} q{f['quality']}: {f['mods']}" for t, f in sorted(by_tier.items())))

        # wielded: the bag click's path; each star's tooltip on the character screen
        tips = {}
        main = {}
        for t in (1, 3, 4):
            if t not in by_tier:
                continue
            w = self.gl("wield", by_tier[t]["id"])
            main = w.get("main", {}) if w.get("ok") else {}
            if t == 1:
                self.flag("fish_wields", fish_tier(main) == 1 and main.get("slot") == "mainhand",
                          f"{w.get('error', '')} main {main.get('id')} slot {main.get('slot')}, replaced {w.get('replaced')}")
                self.flag("fish_longsword_attack", main.get("skill") == "attack_swing_longsword", f"skill {main.get('skill')}")
            self.gl("menu", "character")
            time.sleep(0.5)
            texts, r = self.tooltip("mainhand")
            tips[t] = (texts, main.get("ilvlText", ""))
            self.close_windows()
        self.flag("fish_tooltip_stars", len(tips) == 3 and all(
            tx and f"({STARS[t]} star)" in tx[0] for t, (tx, _) in tips.items()),
            "; ".join(f"t{t}: {tx[:1]}" for t, (tx, _) in tips.items()))
        self.flag("fish_tooltip_ilvl", len(tips) == 3 and all(
            any(re.search(rf"ilvl: {re.escape(il)}\b", x) for x in tx) for t, (tx, il) in tips.items() if il),
            "; ".join(f"t{t}: {[x for x in tx if 'ilvl' in x]} (item {il})" for t, (tx, il) in tips.items()))

    def fish_hit(self):
        self.fresh("LabSwinger")
        self.catch(1)
        f = (self.fish() or [{}])[-1]
        w = self.gl("wield", f.get("id", "hwp_fish_"))
        if not (w.get("ok") and fish_tier(w.get("main"))):
            self.flag("fish_hits", False, f"wield: {w}")
            return
        if not self.start_floor(0):
            self.flag("fish_hits", False, "no mission")
            return
        self.hwp("god")
        self.gl("kill", 6000, "tag:enemy")
        time.sleep(1)
        self.gl("spawn", "actors/humans/bandits/bandit_brute.unit", 24, 0)
        time.sleep(0.8)
        us = self.gl("near", 300, "bandit_brute").get("units") or []
        if not us:
            self.flag("fish_hits", False, "no dummy")
            self.to_town()
            return
        u = us[0]
        pl = self.gl("state").get("player", {})
        dx, dy = u["x"] - pl.get("x", 0), u["y"] - pl.get("y", 0)
        n = max((dx * dx + dy * dy) ** 0.5, 1e-3)
        hp0 = u.get("hp")
        main = self.bag().get("main", {}).get("id")
        for _ in range(3):
            self.gl("input", 500, 0, 0, round(dx / n, 3), round(dy / n, 3), "main")
            time.sleep(0.9)
        after = {x["unit"]: x for x in self.gl("near", 300, "bandit_brute").get("units") or []}
        hp1 = after.get(u["unit"], {}).get("hp", 0.0 if u["unit"] not in after else hp0)
        self.flag("fish_hits", hp0 is not None and hp1 is not None and hp1 < hp0,
                  f"dummy hp {hp0} -> {hp1} at {round(n)} px, main hand {main}")
        self.to_town()

    # --- fishing s6
    def fish_enchant(self):
        self.fresh("LabEnchant")
        self.hwp("material all 200000", 0.8)
        e = self.enchanter()
        self.flag("enchanter_level", e.get("ok") and e.get("level") == 3, json.dumps(e)[:200])
        self.catch(3)
        f = [x for x in self.fish() if fish_tier(x) == 3]
        w = self.gl("wield", f[-1]["id"] if f else "hwp_fish_")
        orig = w.get("replaced", "")
        main0 = w.get("main", {})
        u = self.gl("use", "npc_enchanter")
        time.sleep(0.8)
        self.flag("enchanter_open", u.get("ok") and "Enchant" in str(u.get("window")), str(u.get("window") or u.get("error")))
        btns, _ = self.entry_buttons()
        self.flag("fish_offers_both", sorted(btns.values()) == ["enchant", "upgrade"],
                  f"uncommon {main0.get('id')} q{main0.get('quality')}: {btns}")

        # Upgrade: uncommon -> rare, the generator rolls its modifiers (dust paid)
        mark = len(self.g.read_log())
        main1, paid, how = self.upgrade_main()
        main1 = main1 or {}
        self.flag("fish_upgrade_works", main1.get("quality") == 4 and len(main1.get("mods", [])) >= 1 and paid > 0
                  and not self.exceptions_since(mark),
                  f"q{main0.get('quality')} -> q{main1.get('quality')}, mods {main1.get('mods')}, dust {paid}, {how}")

        # Enchant: the view of the rare fish's modifier slot, then a different modifier. The
        # list only shows modifiers whose blueprint the town owns (every one in
        # modifiers_equipment.sval needs one); the fixture town has none, so first without
        # (the generator's candidates vs the list), then with every blueprint
        entries0, cand0, _, _, _ = self.enchant_view()
        self.close_windows()
        added = self.blueprints()
        self.gl("use", "npc_enchanter")
        time.sleep(0.8)
        entries, cand, ex, groups, _ = self.enchant_view()
        cand_fish, listed_fish = cand, len(entries)
        self.flag("fish_enchant_pool", cand > 0 and len(entries) > 0,
                  f"no blueprints: {len(entries0)} listed of {cand0} candidates; {added} blueprints added: "
                  f"{len(entries)} listed of {cand}")
        self.flag("fish_enchant_view", groups.get("enchant") is True and not ex,
                  f"groups {groups}, {len(entries)} modifiers, exceptions {ex[:2]}")
        lst = entries
        pick = next((x for x in entries if not x["selected"] and x["id"]), None)
        if pick:
            m0 = self.bag().get("main", {})
            c0 = self.mats()
            mark = len(self.g.read_log())
            self.gl("pressin", "enchant-list", pick["id"])
            time.sleep(0.6)
            m1 = self.bag().get("main", {})
            c1 = self.mats()
            spent = {k: c0.get(k, 0) - c1.get(k, 0) for k in ("crystals", "dust")}
            self.flag("fish_enchant_works", pick["id"] in m1.get("mods", []) and m0.get("mods") != m1.get("mods")
                      and any(v > 0 for v in spent.values()) and not self.exceptions_since(mark),
                      f"{m0.get('mods')} -> {m1.get('mods')} ({pick['id']}), paid {spent}")
        else:
            self.flag("fish_enchant_works", False, f"no modifier to pick: {lst[:4]}")
        self.close_windows()
        worked = self.bag().get("main", {})

        # the worked fish back in the bag, fresh 1/2/3-star fish beside it: wares and Sell.
        # Fresh 2/3-star fish have modifiers too: the worked one is told apart by its own
        def is_worked(x):
            return (x.get("id") == worked.get("id") and x.get("mods") == worked.get("mods")
                    and x.get("quality") == worked.get("quality"))

        if orig:
            self.gl("wield", orig)
        for t in (1, 3, 4):
            self.catch(t)
        b = self.bag()
        kept = [x for x in b.get("bag", []) if is_worked(x)]
        fresh = [x for x in b.get("bag", []) if fish_tier(x) and not is_worked(x)]
        wares = self.hwp("wares", 0.4, until="Bet tokens")
        line = (re.findall(r"\[HWP\] (Wares: [^\n]*|You carry no wares\.)", wares) or [""])[-1]
        n_wares = sum(int(n) for n in re.findall(r"(\d+)x ", line))
        self.flag("worked_not_ware", bool(kept) and bool(worked.get("mods")) and n_wares == len(fresh) == 3,
                  f"worked {worked.get('id')} q{worked.get('quality')} mods {worked.get('mods')} in bag: {bool(kept)}; "
                  f"fresh {[(x['id'], x['quality'], len(x['mods'])) for x in fresh]}; {line}")
        t0 = self.tokens()
        sold = self.hwp("sell", 0.5, until="[HWP]")
        t1 = self.tokens()
        b2 = self.bag()
        still = [x for x in b2.get("bag", []) if is_worked(x)]
        left = [x for x in b2.get("bag", []) if fish_tier(x) and not is_worked(x)]
        self.flag("worked_kept_on_sell", bool(still) and not left,
                  f"{' '.join(re.findall(r'Sold your wares[^\n]*', sold))[-120:]}; worked kept {bool(still)}, fresh left {left}")
        self.flag("fresh_mod_fish_sold", not left and t1 - t0 == 9 and any(x.get("mods") for x in fresh),
                  f"tokens {t0} -> {t1} (1 + 3 + 5) for {[(x['id'], len(x['mods'])) for x in fresh]}")

        # Enchant on fresh (unworked) uncommon and rare fish
        for t, flag in ((3, "fresh_uncommon_enchant"), (4, "fresh_rare_enchant")):
            self.catch(t)
            f = [x for x in self.fish() if fish_tier(x) == t and not is_worked(x)]
            if not f:
                self.flag(flag, False, "no fresh fish")
                continue
            self.gl("wield", f[-1]["id"])
            self.gl("use", "npc_enchanter")
            time.sleep(0.8)
            ents, cand_f, ex, groups, btns = self.enchant_view()
            self.flag(flag, "enchant" in btns.values() and not ex and groups.get("enchant") is True and len(ents) > 0,
                      f"{f[-1]['id']} q{f[-1]['quality']} mods {f[-1].get('mods')} buttons {btns}; "
                      f"{len(ents)} listed of {cand_f}; exceptions {ex[:2]}")
            self.close_windows()

        # control: a vanilla longsword of the same quality and item level offers the same pool
        # (its strength requirement grows with the item level: 18 at ilvl 10; a fish has none)
        il = worked.get("ilvl", 10)
        self.hwp("levelup 20", 1.0)
        self.gl("assign", "str", "all")
        e = self.gl("equip", "mainhand_longsword_01", "rare", il)
        main = self.bag().get("main", {})
        self.gl("use", "npc_enchanter")
        time.sleep(0.8)
        ents_v, cand_v, ex_v, _, _ = self.enchant_view()
        self.close_windows()
        on_sword = (main.get("id") == "mainhand_longsword_01" and bool(self.enchanting)
                    and plain(self.enchanting) == plain(main.get("name", "")))
        self.flag("fish_pool_like_longsword", e.get("ok") and on_sword and cand_v == cand_fish and len(ents_v) == listed_fish,
                  f"equip {e.get('ok')} {e.get('error', '')}; main {main.get('id')} {main.get('name')!r}, "
                  f"enchanting {self.enchanting!r}: {len(ents_v)} listed of {cand_v} "
                  f"(fish: {listed_fish} of {cand_fish}); {ex_v[:1]}")

    # --- gambler s7
    def gambler_sell(self):
        self.fresh("LabSeller")
        self.hwp("material all 200000", 0.8)
        # a worked fish: an uncommon one upgraded at the enchanter, then back in the bag
        self.enchanter()
        self.catch(3)
        f = [x for x in self.fish() if fish_tier(x) == 3]
        w = self.gl("wield", f[-1]["id"] if f else "hwp_fish_")
        self.gl("use", "npc_enchanter")
        time.sleep(0.8)
        worked, _, how = self.upgrade_main()
        self.close_windows()
        if w.get("replaced"):
            self.gl("wield", w["replaced"])
        worked = worked or {}
        self.notes.append(f"gambler_sell worked fish: {worked.get('id')} q{worked.get('quality')} mods {worked.get('mods')} ({how})")
        # wares: one fish of each star, a wild carrot plot's crops
        self.hwp("set farm.debug 1")
        for t in (1, 3, 4):
            self.catch(t)
        self.hwp("farm wild carrot", 1.5)
        self.gl("use", "wild/carrot")
        time.sleep(0.8)
        wares = self.hwp("wares", 0.4, until="Bet tokens")
        wl = (re.findall(r"\[HWP\] (Wares: [^\n]*)", wares) or [""])[-1]
        t0, g0 = self.tokens(), self.gold()
        # the Gambler stands in the tavern (fixture town-tavern); a town without one gets him
        # beside the player, the unit the gambler module places
        self.npc("hwp_gambler", "actors/npcs/town/hwp_gambler.unit")
        u = self.gl("use", "hwp_gambler")
        time.sleep(0.6)
        if "Gambler" not in self.window():
            self.notes.append(f"gambler_sell: gl use hwp_gambler: {u}, window {self.window()!r}")
        cap = self.gl("wcaption", "sell-btn", "token-amount").get("texts", {})
        sell = plain(cap.get("sell-btn", ""))
        line0 = plain(cap.get("token-amount", ""))
        m = re.match(r"Sell (\d+): (.*)$", sell)
        gm = re.search(r"(\d+) g\b", sell)
        tm = re.search(r"(\d+) tok\b", sell)
        self.flag("sell_caption", bool(m and gm and tm and int(tm.group(1)) == 9),
                  f"{sell!r} (window {u.get('window')}); {wl}")
        self.gl("press", "sell-btn")
        time.sleep(0.8)
        cap1 = self.gl("wcaption", "token-amount", "result-text", "sell-btn").get("texts", {})
        line1 = plain(cap1.get("token-amount", ""))
        msg = plain(cap1.get("result-text", ""))
        self.close_windows()
        t1, g1 = self.tokens(), self.gold()
        n0 = re.findall(r"Bet tokens: (\d+)", line0)
        n1 = re.findall(r"Bet tokens: (\d+)", line1)
        self.flag("sell_message", "Sold your wares" in msg, msg)
        self.flag("sell_fish_tokens", t1 - t0 == 9, f"tokens {t0} -> {t1} (1 + 3 + 5)")
        self.flag("sell_crops_gold", g1 > g0 and (not gm or g1 - g0 == int(gm.group(1))),
                  f"gold {g0} -> {g1}, caption {gm.group(0) if gm else '-'}")
        self.flag("token_line_up", bool(n0 and n1) and int(n1[0]) - int(n0[0]) == 9, f"{line0!r} -> {line1!r}")
        kept = [x for x in self.bag().get("bag", []) if x["id"] == worked.get("id") and x.get("mods") == worked.get("mods")
                and x.get("quality") == worked.get("quality")]
        self.flag("sell_keeps_worked", bool(kept) and bool(worked.get("mods")),
                  f"{worked.get('id')} mods {worked.get('mods')}, caption after {plain(cap1.get('sell-btn', ''))!r}")

    # --- fishing s13
    def rod_slot(self):
        self.fresh("LabRod")
        self.hwp("fishing bait worm 7", 0.4, until="[HWP]")
        self.gl("menu", "character")
        time.sleep(0.5)
        sibs = {n["id"]: n for n in self.gl("wchildren", "^hwp-gear-rod", 1).get("nodes", [])}
        rod = sibs.get("hwp-gear-rod", {})
        # the rod slot sits beside <equipment> (offset 0 0), the gear slots inside it
        grid = self.gl("wchildren", "equipment", 1).get("nodes", [])
        cells = {n["id"]: n for n in grid}
        hands, feet = cells.get("hands", {}), cells.get("feet", {})
        # bottom left: under the hands slot (left column), level with the feet slot (bottom row)
        placed = bool(rod and hands and feet) and abs(rod["x"] - hands["x"]) <= 2 and abs(rod["y"] - feet["y"]) <= 2
        self.flag("rod_slot_bottom_left", rod.get("visible") is True and placed,
                  f"rod {rod.get('x')},{rod.get('y')} hands {hands.get('x')},{hands.get('y')} feet {feet.get('x')},{feet.get('y')}")
        texts, r = self.tooltip("hwp-gear-rod")
        self.flag("rod_tip_name", bool(texts) and ROD_NAMES[1] in texts[0], f"{texts} ({r.get('tooltip', r.get('error'))})")
        body = " ".join(texts[1:])
        self.flag("rod_tip_bait", "Bait: Worms 7" in body and "Shrimp 0" in body and "Glow Squid 0" in body, body)
        self.close_windows()
        self.hwp("material gold 300000")
        self.hwp("fishing buy rod", 0.5, until="[HWP]")
        self.gl("menu", "character")
        time.sleep(0.5)
        texts2, _ = self.tooltip("hwp-gear-rod")
        body2 = " ".join(texts2[1:])
        self.flag("rod_tip_upgraded", bool(texts2) and ROD_NAMES[2] in texts2[0]
                  and "catch zone +20%" in body2 and "reel speed -10%" in body2, f"{texts2}")
        # left open for the scenario's shot of the character screen

    # --- fishing s9
    def traps_run(self):
        self.fresh("LabTrapper")
        self.hwp("material gold 300000")
        for _ in range(3):
            self.hwp("fishing buy trap", 0.5)
        st = self.hwp("fishing traps", 0.3, until="[HWP] Fish traps")
        self.flag("traps_owned", "Fish traps 3/3" in st, st.strip()[-160:])
        if not self.start_floor(0):
            self.flag("traps_run_counts", False, "no mission")
            return
        self.hwp("god")
        self.gl("kill", 6000, "tag:enemy")
        self.gl("timescale", 16)
        t0, mins, samples = time.time(), 0, []
        while time.time() - t0 < 150:
            time.sleep(8)
            out = self.hwp("fishing traps", 0.3, until="This run so far")
            m = re.findall(r"This run so far: (\d+) min", out)
            if m:
                mins = int(m[-1])
                samples.append((round(time.time() - t0), mins))
            if mins >= 21:
                break
        self.gl("timescale", 1)
        self.flag("traps_run_counts", mins >= 20, f"(real s, game min) {samples}")
        mark = len(self.g.read_log())
        self.to_town()
        time.sleep(3)
        log = self.g.read_log()[mark:]
        m = re.findall(r"\[HWP:fishing\] traps: (\d+) min run, (\d+) rolls, (\d+) fish", log)
        filled = re.findall(r"Your fish traps caught (\d+) fish during the (\d+) minute run", log)
        run_min, rolls, caught = (int(x) for x in m[-1]) if m else (0, 0, 0)
        self.flag("traps_resolved", bool(m) and run_min >= 20 and rolls == run_min // 10,
                  f"{m[-1:] or 'no traps line'}; reply {filled[-1:]}")
        if caught == 0:
            # the step's quick test: 60 minutes of rolls (6 per trap)
            q = self.hwp("fishing traps 60", 0.6, until="[HWP] Fish traps")
            self.notes.append("traps: no fish from the run's rolls; quick test: "
                              + " ".join(re.findall(r"traps: [^\n]*", q))[-160:])
            time.sleep(1.5)
        st = self.hwp("fishing traps", 0.3, until="[HWP] Fish traps")
        lists = re.findall(r"Fish traps \d+/\d+: (.*?)\. This run", st)
        per = []
        for part in (lists[-1].split("; ") if lists else []):
            ids = part.split(": ", 1)[-1]
            per.append(0 if ids == "-" else len(ids.split(",")))
        self.flag("traps_cap_3", len(per) == 3 and all(n <= 3 for n in per) and sum(per) > 0, f"fish per trap {per}")
        full = self.gl("near", 8000, "fish_trap_full").get("units") or []
        self.flag("traps_full_shown", len(full) == sum(1 for n in per if n), f"{len(full)} full trap units, {per}")
        src = (REPO / "mods/fishing/doodads/hwp/fish_trap_full.unit").read_text(encoding="utf-8")
        # the live unit's minimap icon (Verbs_farming mapicons: its scene draws a minimap
        # sprite, not hidden); filtered to the full-trap unit (the reply is capped, FetchAllUnits order)
        icons = []
        mi = {}
        if full:
            mi = self.gl("mapicons", round(full[0]["x"]), round(full[0]["y"]), 24, TRAP_FULL)
            icons = mi.get("units") or []
        file_icon = "<minimap_sprite" in src and "gui/hwp/map_icons.png" in src
        self.flag("traps_full_icon", bool(mi.get("minimap")) and bool(icons)
                  and all(u.get("icon") and not u.get("hidden") for u in icons) and file_icon,
                  f"minimap {mi.get('minimap')} (ui_minimap {mi.get('uiMinimap')}); units {icons[:2]}; "
                  f"fish_trap_full.unit has a minimap_sprite: {file_icon}")
        if not full:
            return
        # beside the trap, on a clear line to it; the map tab open on it for the scenario's shot
        spot, tried = self.trap_approach(full[0])
        self.notes.append(f"traps_run: approach {spot} for the trap at {full[0]['x']},{full[0]['y']} ({tried})")
        self.gl("menu", "map")
        time.sleep(0.8)

    def trap_counts(self):
        st = self.hwp("fishing traps", 0.3, until="[HWP] Fish traps")
        lists = re.findall(r"Fish traps \d+/\d+: (.*?)\. This run", st)
        per = []
        for part in (lists[-1].split("; ") if lists else []):
            ids = part.split(": ", 1)[-1]
            per.append(0 if ids == "-" else len(ids.split(",")))
        return per

    def trap_approach(self, u, skip=()):
        """A start beside a trap for the walk-up. The trap sits in the sea off its coast spot (the
        long walk from the town got stuck, 131626) and is used once the player is on its sensor
        (fish_trap_full.unit rect -20 -20 72 40: x -20..52, y -20..20 from it), so the
        candidates are 20-48 px outside that rect on the land side (+x, -y; the coast spot
        is at +44,-40), nearest the coast spot first, with no wall or hard tile on the line to
        the rect (gl rayhit), not already on the sensor, and where a teleport stays put.
        The player is left there. (x, y) or None, and what was tried."""
        tx, ty = round(u["x"]), round(u["y"])
        sx, sy = TRAP_TO_SPOT
        cands = [(sx, sy)]
        for gap in (20, 32, 48):
            cands += [(52 + gap, 0), (52 + gap, -12), (52 + gap, 12), (36, -20 - gap), (16, -20 - gap),
                      (0, -20 - gap), (52 + gap * 7 // 10, -20 - gap * 7 // 10)]
        cands = sorted(set(cands), key=lambda c: math.hypot(c[0] - sx, c[1] - sy))
        tried = []
        for dx, dy in cands:
            cx, cy = tx + dx, ty + dy
            if (cx, cy) in skip:
                continue
            ex, ey = tx + min(max(dx, -20), 52), ty + min(max(dy, -20), 20)
            h = self.gl("rayhit", cx, cy, ex, ey)
            if h.get("tile") or (h.get("wall") and not h.get("wsensor") and h.get("wname") != TRAP_FULL):
                tried.append(f"{cx},{cy} blocked ({h.get('wname') or h.get('th')})")
                continue
            self.gl("teleport", cx, cy)
            time.sleep(0.6)
            pl = self.p.state().get("player", {})
            px, py = pl.get("x", 0), pl.get("y", 0)
            if math.hypot(px - cx, py - cy) > 12:
                tried.append(f"{cx},{cy} teleport ended at {round(px)},{round(py)}")
                continue
            tops = [x for x in self.gl("usables").get("usables") or [] if x.get("top")]
            if tops and (tops[0].get("unit") or {}).get("unit") == u["unit"]:
                tried.append(f"{cx},{cy} already on the sensor")
                continue
            return (cx, cy), "; ".join(tried[-4:]) or "first candidate"
        return None, "; ".join(tried[-6:])

    def traps_walk(self):
        """fishing s9: walking up to a full trap empties it into the bag. traps_run left the player
        at a clear spot beside it (the map shot); a walk that fails is retried from the next
        spot (up to 4 starts), then gl use is the labelled fallback (trap_collected fails then)."""
        self.close_windows()
        full = self.gl("near", 8000, TRAP_FULL).get("units") or []
        if not full:
            self.flag("trap_collected", False, "no full trap")
            return
        u = full[0]
        per = self.trap_counts()
        n0 = len(self.fish())
        walked, tries, done = 0, [], set()
        for attempt in range(4):
            pl = self.p.state().get("player", {})
            here = (round(pl.get("x", 0)), round(pl.get("y", 0)))
            near = 40 <= math.hypot(here[0] - u["x"], here[1] - u["y"]) <= 120
            if attempt > 0 or not near:
                spot, why = self.trap_approach(u, skip=done)
                if spot is None:
                    tries.append(f"no start left ({why})")
                    break
                here = spot
            done.add(here)
            r = self.p.use(u["unit"], timeout=30)
            time.sleep(1.2)
            pl = self.p.state().get("player", {})
            walked = len(self.fish()) - n0
            tries.append(f"from {here[0]},{here[1]} ({round(math.hypot(here[0] - u['x'], here[1] - u['y']))} px"
                         f" from the trap) to {round(pl.get('x', 0))},{round(pl.get('y', 0))}: {r.result}: {r.reason}"
                         f", {walked} fish")
            if walked > 0:
                break
        fallback = 0
        if walked <= 0:
            self.gl("use", "fish_trap_full")
            time.sleep(1.0)
            fallback = len(self.fish()) - n0
            tries.append(f"FALLBACK gl use: {fallback} fish (not a walk-up)")
        per2 = self.trap_counts()
        self.flag("trap_collected", walked > 0 and sum(per) - sum(per2) == walked,
                  f"walk-up: bag fish {n0} -> {n0 + walked + fallback}, traps {per} -> {per2}; " + " | ".join(tries))
        left = self.gl("near", 8000, TRAP_FULL).get("units") or []
        self.flag("trap_emptied", u["unit"] not in [x["unit"] for x in left], f"full trap units after: {len(left)}")

    # --- fishing s10
    def run_spot(self):
        self.fresh("LabFisher")
        self.hwp("set fishing.run_chance 100")
        self.hwp("set fishing.debug 0")
        status = self.hwp("fishing", 0.4, until="[HWP]")
        spot, floor = None, None
        for fl in (1, 3):
            mark = len(self.g.read_log())
            if not self.start_floor(fl):
                continue
            end = time.time() + 10
            while time.time() < end and "run spot by a well" not in self.g.read_log()[mark:]:
                time.sleep(0.5)
            m = re.findall(r"\[HWP:fishing\] run spot by a well at (-?\d+),(-?\d+)", self.g.read_log()[mark:])
            if m:
                spot, floor = (int(m[-1][0]), int(m[-1][1])), fl
                break
            self.notes.append(f"run_spot: floor {fl} placed no spot")
            self.to_town()
        self.hwp("set fishing.run_chance 30")
        self.flag("run_spot_placed", spot is not None, f"floor {floor}, at {spot}")
        if spot is None:
            return
        self.hwp("god")
        self.gl("kill", 6000, "tag:enemy")
        self.hwp("set fishing.bite_min 300")
        self.hwp("set fishing.bite_max 600")
        b0 = self.bag()
        src = (REPO / "mods/fishing/doodads/hwp/fishing_hole_well.unit").read_text(encoding="utf-8")
        self.flag("run_spot_icon", "<minimap_sprite" in src and bool(self.gl("near", 8000, "fishing_hole_well").get("units")),
                  "fishing_hole_well.unit has a minimap_sprite (file); unit present")
        u, how = self.open_spot("fishing_hole_well")
        near = self.gl("near", 140).get("units") or []
        wells = [x for x in near if any(w in x.get("name", "") for w in WELLS)]
        self.flag("run_spot_by_well", bool(wells) and u is not None,
                  f"wells within 140 of the spot: {[(x['name'].split('/')[-1], round(x['dist'])) for x in wells][:3]}; {how}")
        bait_btn = self.widget("bait-btn")
        casts = self.widget("casts").get("text", "")
        self.flag("run_no_bait", "Worms 0" in status and bait_btn.get("visible") is False and "FishingMenu" in self.window(),
                  f"bait-btn {bait_btn.get('visible')}, window {self.window()}, {casts!r}")
        self.flag("run_casts_3", "Casts left here: 3" in casts, casts)
        loot0 = {x["unit"] for x in self.gl("near", 150, "items/").get("units") or []}
        mark = len(self.g.read_log())
        evs = [self.reel(1) for _ in range(3)]
        time.sleep(1.0)
        log = self.g.read_log()[mark:]
        caught = re.findall(r"\[HWP:fishing\] .* caught tier (\d) \((\d+) casts left\)", log)
        b1 = self.bag()
        new = b1.get("bag", [])[len(b0.get("bag", [])):]
        loot1 = {x["unit"] for x in self.gl("near", 150, "items/").get("units") or []}
        self.flag("run_three_catches", len(caught) == 3 and len([x for x in new if fish_tier(x)]) == 3
                  and all("Something bit" in plain(e.get("texts", {}).get("log", "")) for e in evs),
                  f"{[(e.get('result'), e.get('zw'), e.get('ms')) for e in evs]}, log {caught}")
        self.flag("run_loot", len(loot1 - loot0) >= len(caught) > 0, f"{len(loot1 - loot0)} new item units")
        d = b1.get("diffLevel", 0)
        lo, hi = max(1, int(d + 0.5) - 1), min(b1.get("dropCap", 99), int(d + 0.5) + 1)
        lv = [x["ilvl"] for x in new if fish_tier(x)]
        self.flag("run_fish_ilvl", bool(lv) and all(lo <= v <= hi for v in lv),
                  f"fish ilvl {lv}, floor diff level {d} (ngp {b1.get('ngp')}), cap {b1.get('dropCap')}")
        self.gl("press", "cast-btn")
        time.sleep(0.8)
        log4 = plain(self.widget("log").get("text", ""))
        casts4 = self.widget("casts").get("text", "")
        n4 = len([x for x in self.bag().get("bag", []) if fish_tier(x)])
        self.flag("run_fourth_refused", "Nothing bites here any more" in log4 and "Casts left here: 0" in casts4
                  and n4 == len([x for x in b1.get("bag", []) if fish_tier(x)]), f"{log4!r} {casts4!r}")
        self.gl("press", "close-btn")
        time.sleep(0.5)
        self.hwp("set fishing.bite_min 800")
        self.hwp("set fishing.bite_max 3000")
        self.to_town()

    # --- fishing s11
    def run_stars(self):
        self.fresh("LabStars")
        self.hwp("material gold 300000")
        for _ in range(3):
            self.hwp("fishing buy rod", 0.5, until="[HWP]")
        rod = 4 if ROD_NAMES[4] in self.hwp("fishing", 0.4, until="[HWP]") else 1
        self.hwp("set fishing.run_casts 30")
        self.hwp("set fishing.bite_min 200")
        self.hwp("set fishing.bite_max 300")
        self.hwp("set fishing.run_chance 0")
        seen = {}
        for fl, n in ((0, 15), (3, 15), (5, 8)):
            if not self.start_floor(fl):
                self.notes.append(f"run_stars: floor {fl} did not start")
                continue
            self.hwp("god")
            if fl != 5:
                self.gl("kill", 6000, "tag:enemy")
            mark = len(self.g.read_log())
            self.hwp("fishing hole", 0.6)
            u, how = self.open_spot("doodads/hwp/fishing_hole.unit")
            tiers, results = [], []
            for _ in range(n if "FishingMenu" in self.window() else 0):
                e = self.reel(rod)
                results.append(e.get("result"))
                if e.get("zw"):
                    tiers.append(tier_of(e["zw"], rod))
            logged = [int(t) for t in re.findall(r"caught tier (\d)", self.g.read_log()[mark:])]
            seen[fl] = tiers
            self.notes.append(f"run_stars floor {fl}: zone tiers {tiers}, logged {logged}, {how}, results {results}")
            self.gl("press", "close-btn")
            time.sleep(0.5)
            self.to_town()
        self.hwp("set fishing.run_casts 3")
        self.hwp("set fishing.bite_min 800")
        self.hwp("set fishing.bite_max 3000")
        self.hwp("set fishing.run_chance 30")
        f0, f3, f5 = seen.get(0, []), seen.get(3, []), seen.get(5, [])
        self.flag("stars_rod4", rod == 4, f"rod {rod}")
        self.flag("stars_first_half_1star", len(f0) >= 10 and all(STARS[t] == 1 for t in f0), f"floor 0 tiers {f0}")
        self.flag("stars_later_2star", len(f3) >= 10 and any(STARS[t] == 2 for t in f3) and all(t <= 3 for t in f3),
                  f"floor 3 tiers {f3}")
        self.flag("stars_boss_3star", len(f5) >= 5 and all(STARS[t] == 3 for t in f5), f"boss floor tiers {f5}")


def run(p, sections="fish_sword,fish_enchant,rod_slot", **_):
    c = Checks(p)
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
