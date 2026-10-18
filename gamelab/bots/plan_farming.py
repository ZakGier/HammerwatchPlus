"""Plan checks for the farming group: farming s1, s2, s7, s8, s11.

The town is grown to farm_2 (onion and wheat fields and the farmer: 12-23 "town num building
steps", tweak/town/prefabs_segments.sval) with `build` and the Verbs_farming `buildup` verb,
then loaded fresh through one aborted run. The character screen's can slot is read with the
Verbs_farming `tooltip` verb (the slot's own ShowTooltip, what hovering does).

Sections, in this order:
  plan-farming-a: fa_char (LabFarmer), can_slot_before (s8, leaves the character screen open
  for a shot), farm_town, fields (s1), farmer_buy (s2), groove_plant (s2), can_slot_after (s8),
  lucky_leaf (s7: plant, grow, harvest, smoke from a plot window), herb_loadout (s7: the
  mission board's loadout, the run, the run after);
  plan-farming-b: wild_char (LabForager), wild_floor (s11, leaves the player on the plot for a
  shot), wild_use, wild_yield, wild_boss;
  plan-farming-c: wild_char, wild_rate (s11: floors with a plot at the default chance)."""
import json
import re
import time

from gamelab.bots.plan_checks import Checks as Base
from gamelab.hps import hash_string

FARMER = "npc_misc_farmer_man"
# the order the town builder offers them; each plot needs a built neighbour (BuildingPlot.IsBuildable)
BUILDINGS = ["guild_hall", "tavern", "chapel", "blacksmith", "general_store", "magic_shop", "training_grounds",
             "apothecary", "trading_post", "library", "tailor", "hunters_cabin", "enchanter", "architect", "pyre"]
# yieldMin, yieldMax per seed (FarmingModule.as DefineSeeds)
YIELD = {"cabbage": (2, 4), "carrot": (3, 5), "onion": (2, 4), "potato": (3, 6), "wheat": (4, 8),
         "lucky_leaf": (1, 2), "ember_kush": (1, 2), "saints_sage": (1, 2), "gamblers_gold": (1, 2)}
HERB_SLOT = hash_string("hwp_herb")
LUCKY_BUFF = hash_string("hwp_herb_lucky_leaf")
WILD_LINE = r"\[HWP:farming\] (wild (\w+) plot at (-?\d+),(-?\d+)|no spot for a wild plot on this floor)"


def dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


class Checks(Base):
    # --- plumbing
    def safe_gl(self, *a, tries=3):
        """A gl command that may land during a level reload (a build reloads the town)."""
        for _ in range(tries):
            try:
                return self.gl(*a)
            except Exception:
                time.sleep(2)
        return {}

    def new_char(self, name):
        r = self.gl("char", "paladin", name)
        ok = self.wait_phase("town", 60)
        time.sleep(2)
        self.g.console("e_cheats 1")
        st = self.gl("state").get("player") or {}
        self.flag(f"{name}_ready", ok and st.get("name") == name, json.dumps(r)[:200])
        return ok

    def close_windows(self):
        """Escape until no window is open (never with none open: that opens the pause menu)."""
        for _ in range(4):
            if not self.gl("state").get("window"):
                return True
            self.g.key("escape")
            time.sleep(0.5)
        return not self.gl("state").get("window")

    def top_widget(self, wid, depth=12):
        """The widget with this id in the top-most window that has one (the widgets dump lists
        the windows top last), or {}."""
        for root in reversed(self.gl("widgets", depth).get("roots", [])):
            for n in root.get("nodes", []):
                if n.get("id") == wid:
                    return n
        return {}

    def row_ids(self):
        ids = set()
        for root in self.gl("widgets", 12).get("roots", []):
            for n in root.get("nodes", []):
                m = re.fullmatch(r"row-(\d+)", n.get("id") or "")
                if m:
                    ids.add(int(m.group(1)))
        return sorted(ids)

    def units(self, filt, r=8000):
        """Every unit matching filt within r, and how many `near` left out (its cap)."""
        n = self.gl("near", r, filt)
        return n.get("units") or [], n.get("truncated", 0)

    def grooves(self):
        """The field grooves from their plot units: columns (onion field, farm_groove_v, by x)
        and rows (wheat field, farm_groove_h, by y). Each is {"fixed", "lo", "hi", "units"}."""
        out = {}
        for kind, cross, along in (("v", "x", "y"), ("h", "y", "x")):
            us, _ = self.units("farm_groove_" + kind)
            groups = {}
            for u in us:
                key = next((k for k in groups if abs(k - u[cross]) < 4), u[cross])
                groups.setdefault(key, []).append(u)
            out[kind] = [{"fixed": sum(u[cross] for u in g) / len(g), "lo": min(u[along] for u in g),
                          "hi": max(u[along] for u in g), "units": g}
                         for _, g in sorted(groups.items())]
        return out

    def bbox(self, grooves):
        us = [u for g in grooves for u in g["units"]]
        return (min(u["x"] for u in us), min(u["y"] for u in us), max(u["x"] for u in us), max(u["y"] for u in us))

    def on_groove(self, g):
        """Stand on a groove (its middle plot unit): PlotIndexAt reads the player's position."""
        u = g["units"][len(g["units"]) // 2]
        self.gl("teleport", u["x"], u["y"] + 2)
        time.sleep(0.4)
        return u

    def farm_status(self):
        """hwp farm: the planted list, the seeds owned, the can line."""
        st = self.hwp("farm", 0.5, until="Farm:")
        planted = re.findall(r"Planted: (.*)", st)
        seeds = re.findall(r"Seeds: (.*)", st)
        can = re.findall(r"(\w+ Watering Can: \d+/\d+ water|No watering can)", st)
        return (planted[-1].strip() if planted else ""), (seeds[-1].strip() if seeds else ""), (can[-1] if can else "")

    def seed_names(self):
        """The seeds owned, in g_seeds order (the plot window's plant rows)."""
        _, seeds, _ = self.farm_status()
        return [re.sub(r" \d+$", "", s.strip()) for s in seeds.split(",") if s.strip()]

    def tooltip(self, wid="hwp-gear-can"):
        self.close_windows()
        self.gl("menu", "character")
        time.sleep(0.6)
        return self.gl("tooltip", wid)

    def herb_buff(self):
        """Whether the player record holds the Lucky Leaf buff in the hwp_herb slot
        (PlayerRecord "mission-buffs": slot hash, buff hash, ...), and how many it holds."""
        v = self.gl("inspect", "player", "mission-buffs").get("value") or []
        v = [x & 0xFFFFFFFF for x in v if isinstance(x, int)]
        return any(v[i] == HERB_SLOT and v[i + 1] == LUCKY_BUFF for i in range(0, len(v) - 1, 2)), len(v) // 2

    def god_on(self):
        """hwp god toggles (the cht_god cvar, which outlives the floor): on, never back off."""
        if "god mode off" in self.hwp("god", 0.4, until="god mode"):
            self.hwp("god", 0.4, until="god mode")

    def farmer(self):
        us, _ = self.units(FARMER)
        return us[0] if us else None

    def shop(self):
        f = self.farmer()
        if f:
            self.gl("teleport", f["x"], f["y"] + 24)
            time.sleep(0.4)
        u = self.gl("use", FARMER)
        time.sleep(0.5)
        return u

    # --- plan-farming-a
    def fa_char(self):
        self.new_char("LabFarmer")
        self.hwp("set farm.debug 1")
        self.set_gold(5000)

    def can_slot_before(self):
        """s8: before any can the slot (core hwp-gear-can, nav-pos 2 2: the gear grid's bottom
        right) is dimmed (HWPFarmCanSlot.Dim: CanTier <= 0, the same test as its tooltip text)
        and says so. The character screen stays open for the shot."""
        _, _, can = self.farm_status()
        t = self.tooltip()
        texts = t.get("texts") or []
        self.flag("s8_slot_shown", t.get("ok") and "HWPGearSlotWidget" in t.get("widget", "") and t.get("visible"),
                  f"{t.get('widget')} in {t.get('window')}, visible {t.get('visible')}, error {t.get('error')}")
        self.flag("s8_slot_no_can", can == "No watering can" and texts[:1] == ["Watering can"]
                  and any("no watering can yet" in s for s in texts), f"{can!r}; tooltip {texts}")

    def grow_town(self, target):
        b = self.safe_gl("buildings").get("buildings") or {}
        steps = sum(v + 1 for v in b.values())
        log = []
        progress = True
        while steps < target and progress:
            progress = False
            for bid in BUILDINGS:
                if steps >= target:
                    break
                if bid in b:
                    continue
                r = self.safe_gl("build", bid)
                time.sleep(3)
                if r.get("ok") and not r.get("existed"):
                    progress = True
                    log.append(bid)
                b = self.safe_gl("buildings").get("buildings") or b
                steps = sum(v + 1 for v in b.values())
        for bid in BUILDINGS:
            if steps >= target:
                break
            if bid not in b:
                continue
            r = self.safe_gl("buildup", bid, target - steps)
            time.sleep(3)
            if r.get("ok"):
                log.append(f"{bid}->{r.get('variation')}")
            b = self.safe_gl("buildings").get("buildings") or b
            steps = sum(v + 1 for v in b.values())
        return steps, log, b

    def farm_town(self, target=16):
        """The farm_2 town (12-23 building steps), loaded fresh: one aborted run."""
        self.close_windows()
        steps, log, b = self.grow_town(int(target))
        self.notes.append(f"town: {steps} steps after {log}; buildings {b}")
        self.hwp("set farm.debug 1")
        self.gl("save")
        time.sleep(0.5)
        mark = len(self.g.read_log())
        ok = self.start_floor(0) and self.to_town()
        end = time.time() + 15
        while "[HWP:farming] fields:" not in self.g.read_log()[mark:] and time.time() < end:
            time.sleep(0.5)
        time.sleep(1.5)
        self.close_windows()
        fields = re.findall(r"\[HWP:farming\] fields: (.*)", self.g.read_log()[mark:])
        self.flag("fa_town_farm2", ok and 12 <= steps < 24 and bool(fields), f"{steps} steps, round trip {ok}, {fields[-1:]}")

    def fields(self):
        """s1: the onion and wheat crops are hidden, their grooves are plots, the apple tree
        stands just above the wheat field's top fence."""
        log = self.g.read_log()
        f = re.findall(r"\[HWP:farming\] fields: (.*) \((\d+) crops hidden\)", log)
        text, hidden = (f[-1][0], int(f[-1][1])) if f else ("", -1)
        counts = {k: int(n) for n, k in re.findall(r"(\d+) (\w+) grooves", text)}
        un = self.hwp("farm units", 0.4, until="hidden crops")
        m = re.findall(r"plots (\d+) \((\w+)\).*hidden crops (\d+), tree moved (\w+)", un)
        gr = self.grooves()
        self.flag("s1_fields", counts.get("onion", 0) > 0 and counts.get("wheat", 0) > 0 and bool(m) and m[-1][1] == "fields"
                  and bool(gr["v"]) and bool(gr["h"]),
                  f"{text!r}; {m[-1:]}; {len(gr['v'])} groove columns, {len(gr['h'])} rows")
        # every onion / wheat crop on the fields is hidden (stray ones elsewhere stay)
        box = self.bbox(gr["v"] + gr["h"]) if gr["v"] and gr["h"] else (0, 0, 0, 0)
        on_field = 0
        for crop in ("crop_onions", "crop_wheat"):
            us, cut = self.units(crop)
            on_field += sum(1 for u in us if box[0] - 30 <= u["x"] <= box[2] + 30 and box[1] - 30 <= u["y"] <= box[3] + 30)
            if cut:
                self.notes.append(f"{crop}: near left {cut} out")
        self.flag("s1_crops_gone", hidden > 0 and bool(m) and int(m[-1][2]) == hidden and on_field <= hidden,
                  f"{hidden} hidden (log), units line {m[-1:]}, {on_field} onion/wheat crop units on the fields")
        # a groove opens the plot window
        win, title, state = "", "", ""
        if gr["v"]:
            self.on_groove(gr["v"][0])
            win = self.gl("use", "farm_groove").get("window", "")
            time.sleep(0.5)
            title = self.top_widget("title").get("text", "")
            state = self.top_widget("state").get("text", "")
            self.close_windows()
        self.flag("s1_groove_is_plot", win == "HWPFarmMenu" and title.startswith("Farm Plot") and state.startswith("Empty soil"),
                  f"{win} {title!r} {state!r}")
        # the apple tree: moved to (x, top wheat row - 39), above the field
        mv = re.findall(r"moved the apple tree from (-?\d+),(-?\d+) to (-?\d+),(-?\d+)", log)
        trees, _ = self.units("tree_oak_apple")
        ok, note = False, f"moves {mv[-1:]}, {len(trees)} apple trees"
        if mv and gr["h"]:
            tx, ty = int(mv[-1][2]), int(mv[-1][3])
            top = min(g["fixed"] for g in gr["h"])
            x0, _, x1, _ = self.bbox(gr["h"])
            at = [t for t in trees if abs(t["x"] - tx) <= 3 and abs(t["y"] - ty) <= 3]
            ok = bool(at) and abs(ty - (top - 39)) <= 3 and x0 - 40 <= tx <= x1 + 40
            note += f"; tree at {tx},{ty}, top wheat row y {top:.0f}, rows x {x0:.0f}..{x1:.0f}, unit there {bool(at)}"
        self.flag("s1_apple_tree_above_wheat", ok, note)

    def farmer_buy(self):
        """s2: the farmer stands between the two fields (the town's own, not spawned); the can
        and a cabbage seed from his window. The plan says 150 g for the can: the source says
        200 (CAN_PRICE[1], README), 150 is the Lucky Leaf seed."""
        gr = self.grooves()
        f0 = self.farmer()
        time.sleep(3)
        f1 = self.farmer()
        ok, note = False, f"farmer {f0}"
        if f0 and f1 and gr["v"] and gr["h"]:
            vb, hb = self.bbox(gr["v"]), self.bbox(gr["h"])
            cv = ((vb[0] + vb[2]) / 2, (vb[1] + vb[3]) / 2)
            ch = ((hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2)
            fp = (f1["x"], f1["y"])

            def inside(p, bx):
                return bx[0] <= p[0] <= bx[2] and bx[1] <= p[1] <= bx[3]
            between = dist(cv, fp) + dist(fp, ch) <= 1.3 * dist(cv, ch) and not inside(fp, vb) and not inside(fp, hb)
            moved = dist((f0["x"], f0["y"]), fp)
            ok = between and moved <= 4
            note = (f"farmer {fp[0]:.0f},{fp[1]:.0f} (moved {moved:.1f} in 3 s); onion field "
                    f"{[round(x) for x in vb]}, wheat field {[round(x) for x in hb]}")
        self.flag("s2_farmer_between_fields", ok, note)
        self.set_gold(5000)
        u = self.shop()
        st0 = self.top_widget("state").get("text", "")
        g0 = self.gold()
        mark = len(self.g.read_log())
        self.gl("press", "row-0")
        time.sleep(0.5)
        g1 = self.gold()
        st1 = self.top_widget("state").get("text", "")
        self.gl("press", "row-1")  # the first seed: cabbage
        time.sleep(0.5)
        g2 = self.gold()
        said = self.farm_say(mark)
        self.close_windows()
        self.flag("s2_can_bought", u.get("window") == "HWPFarmMenu" and g0 - g1 > 0 and "4/4" in st1,
                  f"{st0!r} -> {st1!r}, paid {g0 - g1} g (plan says 150, source CAN_PRICE[1] = 200)")
        self.flag("s2_can_price_150", g0 - g1 == 150, f"paid {g0 - g1} g: the plan's 150 g; the source and README say 200")
        self.flag("s2_seed_bought", g1 - g2 == 20 and any("Cabbage seed" in s for s in said), f"gold {g1} -> {g2}, {said}")

    def groove_plant(self):
        """s2: an empty groove's window, pick the seed: sprouts along the whole groove."""
        gr = self.grooves()
        if not gr["v"]:
            self.flag("s2_sprouts_whole_groove", False, "no groove columns")
            return
        g = gr["v"][0]
        before = [s for s in self.units("farm_sprout")[0] if abs(s["x"] - g["fixed"]) <= 6]
        self.on_groove(g)
        self.gl("use", "farm_groove")
        time.sleep(0.5)
        state = self.top_widget("state").get("text", "")
        self.gl("press", "row-0")
        time.sleep(1.0)
        win = self.gl("state").get("window")
        planted, _, _ = self.farm_status()
        sp = [s for s in self.units("farm_sprout")[0] if abs(s["x"] - g["fixed"]) <= 6]
        ys = [s["y"] for s in sp]
        whole = bool(ys) and len(sp) >= 3 and min(ys) <= g["lo"] + 2 and max(ys) >= g["hi"] - 2
        self.flag("s2_planted", "Empty soil" in state and "Cabbage" in planted and not win,
                  f"window {state!r}, then {win!r}; planted {planted!r}")
        self.flag("s2_sprouts_whole_groove", not before and whole,
                  f"{len(before)} -> {len(sp)} sprouts at x {g['fixed']:.0f}, y {min(ys, default=0):.0f}..{max(ys, default=0):.0f}; "
                  f"groove plot units y {g['lo']:.0f}..{g['hi']:.0f}")

    def can_slot_after(self):
        """s8: with the can the slot's tooltip names it and its water; watering lowers it."""
        t = self.tooltip()
        a = t.get("texts") or []
        self.close_windows()
        gr = self.grooves()
        mark = len(self.g.read_log())
        if gr["v"]:
            self.on_groove(gr["v"][0])  # the cabbage: growing, so use waters it
            self.gl("use", "farm_groove")
            time.sleep(0.8)
        said = self.farm_say(mark)
        self.close_windows()
        b = self.tooltip().get("texts") or []
        self.close_windows()
        self.flag("s8_slot_tier_water", a[:1] == ["Mahogany Watering Can"] and any(s.startswith("Water: 4/4") for s in a), str(a))
        self.flag("s8_water_drops", any(s.startswith("Water: 3/4") for s in b) and any("atered" in s for s in said),
                  f"{said}; tooltip {b}")

    def lucky_leaf(self):
        """s7: a Lucky Leaf seed (150 g), planted on a wheat row, grown, harvested, smoked from
        an empty plot's window."""
        self.set_gold(5000)
        self.shop()
        g0 = self.gold()
        self.gl("press", "row-6")  # the can upgrade, then the seeds in DefineSeeds order: lucky_leaf is the 6th
        time.sleep(0.5)
        g1 = self.gold()
        self.close_windows()
        gr = self.grooves()
        if len(gr["h"]) < 2:
            self.flag("s7_planted", False, f"{len(gr['h'])} wheat rows")
            return
        names = self.seed_names()
        row = names.index("Lucky Leaf") if "Lucky Leaf" in names else -1
        self.on_groove(gr["h"][0])
        self.gl("use", "farm_groove")
        time.sleep(0.5)
        if row >= 0:
            self.gl("press", f"row-{row}")
            time.sleep(1.0)
        self.close_windows()
        planted, _, _ = self.farm_status()
        self.flag("s7_planted", g0 - g1 == 150 and "Lucky Leaf" in planted, f"paid {g0 - g1}, seeds {names}, planted {planted!r}")
        for _ in range(6):
            if "Lucky Leaf ready" in planted:
                break
            self.hwp("farm grow", 0.5, until="runs counted")
            planted, _, _ = self.farm_status()
        mark = len(self.g.read_log())
        self.on_groove(gr["h"][0])
        self.gl("use", "farm_groove")
        time.sleep(1.0)
        self.close_windows()
        got = re.findall(r"harvested (\d+)x lucky_leaf \(\+(\d+) seeds\)", self.g.read_log()[mark:])
        self.flag("s7_harvested", bool(got) and 1 <= int(got[-1][0]) <= 2, f"{planted!r}; {got}")
        # smoke it from an empty plot's window (the herb rows come after the plant rows)
        self.on_groove(gr["h"][-1])
        w = self.gl("use", "farm_groove").get("window", "")
        time.sleep(0.5)
        rows = self.row_ids()
        active0 = self.top_widget("active").get("text", "")
        if rows:
            self.gl("press", f"row-{rows[-1]}")
            time.sleep(0.6)
        active1 = self.top_widget("active").get("text", "")
        msg = self.top_widget("message").get("text", "")
        self.close_windows()
        buff, n = self.herb_buff()
        self.flag("s7_smoked", w == "HWPFarmMenu" and "Active herb: Lucky Leaf" in active1 and "smoke a Lucky Leaf" in msg and buff,
                  f"{w}, rows {rows}; {active0!r} -> {active1!r}; {msg!r}; buff {buff} ({n} mission buffs)")

    def herb_loadout(self):
        """s7: the mission board's loadout (vanilla mission_start: SetMission + the loadout
        menu); it should list the herb (no loadout segment does: not implemented). Its
        constructor empties the mission buffs (ResetForNewMission, GUI/MissionLoadoutMenu.as:207):
        the farming fix puts the herb back. Then the run has it; after the run it is gone."""
        self.close_windows()
        mark = len(self.g.read_log())
        self.g.console("mission_start bandit_keep")
        time.sleep(2.0)
        w = self.gl("state").get("window")
        listed = "Lucky Leaf" in self.widget_text()
        kept, _ = self.herb_buff()
        back = re.findall(r"\[HWP:farming\] the loadout cleared the mission buffs: (.*)", self.g.read_log()[mark:])
        self.flag("s7_loadout_lists_herb", w == "MissionLoadoutMenu" and listed, f"{w}, 'Lucky Leaf' in its widgets: {listed}")
        self.flag("s7_herb_survives_loadout", w == "MissionLoadoutMenu" and kept, f"buff after the loadout opened {kept}, {back}")
        self.gl("func", "play")
        ok = self.wait_phase("mission", 150)
        time.sleep(3)
        in_run, n = self.herb_buff()
        self.flag("s7_herb_in_run", ok and in_run, f"mission {ok}, buff {in_run} ({n} mission buffs)")
        home = self.to_town()
        time.sleep(2)
        after, n = self.herb_buff()
        self.close_windows()
        self.flag("s7_herb_gone_after_run", home and not after, f"town {home}, buff {after} ({n} mission buffs)")

    # --- plan-farming-b / -c
    def wild_char(self):
        """A saved town (a fixture boot has none, and a run loads the town's HWP settings from
        the save): the tavern built, then the farm settings, saved."""
        self.new_char("LabForager")
        b = self.safe_gl("build", "tavern")
        time.sleep(3)
        self.hwp("set farm.debug 1")
        self.hwp("set farm.run_chance 100")
        self.gl("save")
        time.sleep(0.5)
        self.flag("wild_town_saved", bool(b.get("ok")), json.dumps(b)[:200])

    def wild_line(self, mark, wait=3.0):
        time.sleep(wait)
        return re.findall(WILD_LINE, self.g.read_log()[mark:])

    def wild_floor(self):
        """s11: at farm.run_chance 100 the first floor gets a wild plot, beside a pot, crate or
        chest (FindWildSpot: FreeSpot 56 px from one). The player is left on it for the shot
        (its minimap icon)."""
        mark = len(self.g.read_log())
        ok = self.start_floor(0)
        self.god_on()
        lines = self.wild_line(mark)
        wild = [ln for ln in lines if ln[1]]
        self.flag("s11_wild_on_floor", ok and bool(wild), f"{lines}")
        if not wild:
            return
        x, y = int(wild[-1][2]), int(wild[-1][3])
        self.gl("teleport", x, y + 2)
        time.sleep(0.6)
        near = self.gl("near", 80).get("units") or []
        anchors = [u for u in near if re.search(r"Breakable|Chest", u.get("behavior", ""))]
        plots = [u for u in near if "doodads/hwp/wild/" in u.get("name", "")]
        dmin = min((dist((u["x"], u["y"]), (x, y)) for u in anchors), default=-1)
        self.flag("s11_wild_beside_anchor", bool(plots) and 0 <= dmin <= 60,
                  f"plot {plots[:1]}, nearest anchor {dmin:.0f} px {[(a['name'], a['behavior']) for a in anchors[:3]]}")

    def wild_use(self):
        """s11: using it gives the crop's usual yield, opens no window (no planting), and it is
        gone for this player: not usable, a second use yields nothing."""
        mark = len(self.g.read_log())
        u = self.gl("use", "doodads/hwp/wild/")
        time.sleep(0.8)
        log = self.g.read_log()[mark:]
        got = re.findall(r"harvested a wild (\w+) plot: (\d+) \(\+(\d+) seeds\)", log)
        ok = bool(got) and got[-1][0] in YIELD and YIELD[got[-1][0]][0] <= int(got[-1][1]) <= YIELD[got[-1][0]][1]
        self.flag("s11_wild_yield", ok, f"{u.get('unit')}: {got}")
        win = self.gl("state").get("window")
        self.flag("s11_wild_no_planting", u.get("ok") and not win and "planted" not in log, f"window {win!r}")
        us = self.gl("usables").get("usables") or []
        still = [x for x in us if "doodads/hwp/wild/" in (x.get("unit") or {}).get("name", "") and x.get("canUse")]
        mark2 = len(self.g.read_log())
        self.gl("use", "doodads/hwp/wild/")
        time.sleep(0.8)
        again = re.findall(r"harvested a wild", self.g.read_log()[mark2:])
        if self.gl("state").get("window"):
            self.close_windows()
        self.flag("s11_wild_vanishes", bool(got) and not still and not again, f"usable after: {still[:1]}, second use {again}")

    def wild_yield(self, picks=60):
        """s11: wild seed-back odds are twice the farm's (source: farm 25 % one / 5 % two
        seeds, FarmingModule.as OnHarvest; wild 50 % / 10 %, HarvestWild). Measured on debug
        wild cabbage plots (hwp farm wild cabbage + wild pick): the yield stays 2-4, a seed
        comes back on about half (0.35-0.65 here; the farm's rate is 0.25)."""
        mark = len(self.g.read_log())
        for _ in range(int(picks)):
            self.hwp("farm wild cabbage", 0.15, until="wild cabbage plot placed", timeout=2)
            self.hwp("farm wild pick", 0.15, until="harvested a wild", timeout=2)
        got = re.findall(r"harvested a wild cabbage plot: (\d+) \(\+(\d+) seeds\)", self.g.read_log()[mark:])
        n = len(got)
        ys = [int(a) for a, _ in got]
        back = [int(b) for _, b in got]
        rate = sum(1 for b in back if b > 0) / n if n else 0
        self.flag("s11_wild_yield_range", n >= 20 and min(ys) >= 2 and max(ys) <= 4,
                  f"{n} picks, yields {min(ys, default=0)}..{max(ys, default=0)}")
        self.flag("s11_wild_seeds_double", n >= 20 and 0.35 <= rate <= 0.65,
                  f"seed back on {rate:.2f} of {n} (farm 0.25), mean {sum(back) / n if n else 0:.2f} seeds (farm 0.35, wild 0.70)")

    def wild_boss(self):
        """s11: at 100 % every later floor gets one; the boss floor never."""
        lines = []
        for _ in range(4):
            mark = len(self.g.read_log())
            self.next_floor()
            lv = self.gl("state").get("level", "")
            lines.append((lv, self.wild_line(mark)))
        mark = len(self.g.read_log())
        self.next_floor()
        lv = self.gl("state").get("level", "")
        boss = self.wild_line(mark, 4.0)
        self.flag("s11_wild_every_floor", all(ln for _, ln in lines), f"{[(lv0, [x[0] for x in ln]) for lv0, ln in lines]}")
        self.flag("s11_no_wild_boss", "boss" in lv and not boss, f"{lv}: {boss}")
        self.to_town()

    def wild_rate(self, missions=3, lo=1, hi=10):
        """s11: at the default farm.run_chance (35) about a third of the floors get a wild plot
        (5 floors a run; the count's 99 % band over 15 floors is about 1-10)."""
        self.hwp("set farm.run_chance 35")
        self.gl("save")
        time.sleep(0.5)
        floors, wild, seen = 0, 0, []
        for _ in range(int(missions)):
            mark = len(self.g.read_log())
            if not self.start_floor(0):
                break
            self.god_on()
            for k in range(5):
                if k:
                    mark = len(self.g.read_log())
                    self.next_floor()
                ln = self.wild_line(mark, 2.5)
                floors += 1
                wild += 1 if any(x[1] for x in ln) else 0
                seen.append(len([x for x in ln if x[1]]))
            self.to_town()
        self.flag("s11_wild_about_third", floors >= 10 and lo <= wild <= hi and all(s <= 1 for s in seen),
                  f"{wild} of {floors} floors ({wild / floors if floors else 0:.2f}), per floor {seen}")


def run(p, sections="", **_):
    """sections: comma separated; "name:arg" passes one argument (farm_town:16, wild_yield:60)."""
    c = Checks(p)
    for s in sections.split(","):
        if not s:
            continue
        name, _, arg = s.partition(":")
        try:
            getattr(c, name)(*([arg] if arg else []))
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{name}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
