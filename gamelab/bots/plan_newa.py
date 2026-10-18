"""Test-plan checks for three features that had no plan steps yet: the stash Sort button
(mods/stash), the search field on the HammerwatchPlus options tab (mods/core) and the
General Merchant's Trinkets tab (mods/keys). Same style as plan_checks: each section flags
booleans, the scenario's expect asserts them, measured values go in the notes.

Sections:
- stash_sort: two stash tabs filled through gl stashput (Verbs_newa.as) in a scrambled
  order; Sort on the second tab leaves the first alone; Sort on the first orders it by class
  (main requirement), then type (two-handed, main hand, off hand, then armour; weapons by
  family), then item level, highest first; the grid on screen follows; a second press
  changes nothing; closing and reopening keeps the order (stash s1-s4; s5 after a restart
  is the scenario's).
- settings_search: the Plus tab's search field, typed into with posted chars: placeholder,
  filter by title, no match, Backspace, Esc, case, value match, a filtered row still
  works, a reopened menu is unfiltered (search s1-s8).
- merchant_trinkets: the Trinkets tab's stock (6: 2 common, 2 uncommon, 2 rare, no
  repeats, the run trinket shop's price), buying (paid, packed, refused when poor, sold
  out), the packed ones handed over when a run starts, a run's own trinket shop asking the
  same price, and a new stock after every run (trinkets s1-s9; s10 after a restart is the
  scenario's)."""
import json
import re
import time
from pathlib import Path

from gamelab.bots.plan_checks import Checks as Base

REPO = Path(__file__).resolve().parents[2]

# stash tab 0 and tab 1, in the order they are put in ("<baseId>@<ilvl>", all common)
TAB0_IN = ["back_2b@8", "mainhand_mace_01@4", "chest_dex_t1a@8", "twohanded_shortbow_01@6",
           "back_4a@12", "feet_str_t1a@8", "mainhand_wand_fire_01@8", "mainhand_mace_01@14",
           "offhand_shield_01@8", "twohanded_shortbow_01@16", "head_int_t1a@8", "back_2a@8",
           "mainhand_longsword_01@8", "twohanded_maul_01@8", "chest_str_t1a@8"]
TAB1_IN = ["back_2b@9", "twohanded_shortbow_01@9", "head_str_t1a@9", "mainhand_mace_01@9"]
# the order the plan's rule gives: class (str, dex, int, foc, vit), then type, then ilvl
TAB0_SORTED = ["twohanded_maul_01@8", "mainhand_longsword_01@8", "mainhand_mace_01@14", "mainhand_mace_01@4",
               "offhand_shield_01@8", "chest_str_t1a@8", "feet_str_t1a@8",
               "twohanded_shortbow_01@16", "twohanded_shortbow_01@6", "chest_dex_t1a@8",
               "mainhand_wand_fire_01@8", "head_int_t1a@8",
               "back_4a@12", "back_2a@8",
               "back_2b@8"]
TAB1_SORTED = ["mainhand_mace_01@9", "head_str_t1a@9", "twohanded_shortbow_01@9", "back_2b@9"]
# base id -> (its only requirement, slot), from gamecode/datatables/tweak/items/equipment. Not the
# scepters or lanterns: their conditionals want the holy DLC, so the generator returns null
# (EquipmentGenerator.VerifyItem -> CheckGlobalConditionals; plan-newa-a 20261018-122829)
BASES = {
    "twohanded_maul_01": ("str", "twohand"), "mainhand_longsword_01": ("str", "mainhand"),
    "mainhand_mace_01": ("str", "mainhand"), "offhand_shield_01": ("str", "offhand"),
    "chest_str_t1a": ("str", "chest"), "feet_str_t1a": ("str", "feet"), "head_str_t1a": ("str", "head"),
    "twohanded_shortbow_01": ("dex", "twohand"), "chest_dex_t1a": ("dex", "chest"),
    "mainhand_wand_fire_01": ("int", "mainhand"), "head_int_t1a": ("int", "head"),
    "back_4a": ("foc", "back"), "back_2a": ("foc", "back"), "back_2b": ("vit", "back"),
}
CLASS_ORDER = ["str", "dex", "int", "foc", "vit"]
SLOT_ORDER = ["twohand", "mainhand", "offhand", "head", "chest", "hands", "feet", "back"]
WEAPONS = {"twohand", "mainhand", "offhand"}

# Item::QualityColorString (Items/Item.as:241): a trinket entry's title starts \c<colour>
QUALITY_COLOURS = {"ffffff": "common", "42ff00": "uncommon", "00c0ff": "rare", "ff00ff": "epic"}
# a run's trinket shop: price x (1 + 0.2 x ShopLevel) (ShopContent/TrinketShopShopContent.as:46);
# 51 of the 58 placements in gamecode/sdk/hoh2 prefabs/levels are ShopLevel 1
SHOP_RATE = 1.0 + 1 * 0.2
TRINKET_FALLBACK = {"common": 200, "uncommon": 750, "rare": 3000}  # every one of a quality costs the same
RUN_SHOP_PREFAB = "prefabs/barracks/special/shop_room_s_12x12.pfb"  # its npc_trinket_shop: ShopLevel 1


def trinket_data():
    """id -> (quality, price) from the datatables the game parsed (no mod adds trinkets)."""
    out = {}
    for f in sorted((REPO / "gamecode/datatables/tweak/trinkets").glob("*.sval.json")):
        try:
            rows = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for t in rows if isinstance(rows, list) else []:
            if isinstance(t, dict) and "id" in t and "quality" in t:
                out[t["id"]] = (t["quality"], t.get("price", 0))
    return out


def title_quality(title):
    m = re.match(r"\\c([0-9a-fA-F]{6})", title or "")
    return QUALITY_COLOURS.get(m.group(1).lower(), "?") if m else "?"


def item_key(entry):
    """(class rank, slot rank, family, ilvl) of a "<baseId>@<ilvl>" stash entry."""
    base, _, ilvl = entry.partition("@")
    cls, slot = BASES.get(base, ("?", "?"))
    fam = base.split("_")[1] if slot in WEAPONS else ""
    return (CLASS_ORDER.index(cls) if cls in CLASS_ORDER else 9,
            SLOT_ORDER.index(slot) if slot in SLOT_ORDER else 9, fam, int(ilvl or 0))


def rule_sorted(entries):
    """The plan's order for these stash entries: class, then type (weapons by family), then
    item level, highest first. The lists above have no ties past that."""
    return sorted(entries, key=lambda e: (*item_key(e)[:3], -item_key(e)[3]))


class Checks(Base):
    # --- plumbing
    def log_since(self, mark):
        return self.g.read_log()[mark:]

    def close_windows(self, n=3):
        """Escape while a window is up (never with none: that opens the pause menu)."""
        for _ in range(n):
            if not self.gl("state").get("window"):
                return True
            self.g.key("escape")
            time.sleep(0.5)
        return not self.gl("state").get("window")

    def root_nodes(self, root, depth=16):
        """The widget nodes of the open window `root` (its script class), and the dump's
        truncation count."""
        r = self.gl("widgets", depth)
        for rt in r.get("roots", []):
            if rt.get("root") == root:
                return rt.get("nodes", []), r.get("truncated", 0)
        return [], r.get("truncated", 0)

    def root_widget(self, root, wid):
        for n in self.root_nodes(root)[0]:
            if n.get("id") == wid:
                return n
        return {}

    def stash_items(self, tab):
        r = self.gl("stash", tab)
        return r.get("items") if r.get("ok") else None, r.get("name", "")

    def stash_grid(self):
        """Item names in the stash grid on screen (stash-inventory's slots, top to bottom)."""
        nodes, cut = self.root_nodes("PlayerStashWindow")
        for i, n in enumerate(nodes):
            if n.get("id") != "stash-inventory":
                continue
            out = []
            for m in nodes[i + 1:]:
                if m.get("d", 0) <= n.get("d", 0):
                    break
                if "item" in m and m.get("visible", True):
                    out.append(m["item"])
            return out, cut
        return None, cut

    def open_stash(self):
        self.g.console("dbg_show_stash")
        time.sleep(1)
        return self.gl("state").get("window") == "PlayerStashWindow"

    def press_sort(self, mark_name):
        mark = len(self.g.read_log())
        r = self.gl("press", "hwp-stash-sort")
        end = time.time() + 5
        while "[HWP:stash] sorted" not in self.log_since(mark) and time.time() < end:
            time.sleep(0.25)
        said = re.findall(r"\[HWP:stash\] (sorted .*)", self.log_since(mark))
        self.notes.append(f"{mark_name}: press {r.get('widget')}, {said}")
        return r, said

    # --- stash
    def stash_sort(self):
        """stash s1-s4: Sort orders only the tab on screen, by class, type, then item level;
        the grid follows, a second press keeps the order, a reopened stash has it."""
        self.close_windows()
        for t in (0, 1):
            items, _ = self.stash_items(t)
            if items:
                self.notes.append(f"stash tab {t} held {len(items)} item(s) before; cleared")
                self.gl("stashclear", t)
        put = [["stashput", t, *e.split("@")[:1], "common", e.split("@")[1]]
               for t, lst in ((0, TAB0_IN), (1, TAB1_IN)) for e in lst]
        rs = self.g.gl_multi(put)
        bad = [r.get("error", r) for r in rs if not r.get("ok")]
        t0, name0 = self.stash_items(0)
        t1, name1 = self.stash_items(1)
        self.flag("stash_filled", not bad and t0 == TAB0_IN and t1 == TAB1_IN,
                  f"{len(rs)} put, {len(bad)} failed {bad[:3]}; tab0 {t0}; tab1 {t1}")
        if not t0 or not t1:
            self.notes.append("stash: a tab is empty, nothing to sort")
            return
        # a put that failed leaves the rest: sort and check whatever the tabs hold, against
        # the rule applied to that (the same as TAB*_SORTED when every put landed)
        want0, want1 = rule_sorted(t0), rule_sorted(t1)
        # the vanilla display options re-sort / hide the grid (StashInventoryWidget.Refresh):
        # a plain display shows the tab's own order
        srt = self.gl("inspect", "town", "stash-sorting").get("value")
        hid = self.gl("inspect", "town", "stash-hiding").get("value")
        self.flag("stash_display_plain", srt in (0, None) and hid in (0, None), f"stash-sorting {srt}, stash-hiding {hid}")
        self.flag("stash_open", self.open_stash())
        grid0, cut = self.stash_grid()
        self.notes.append(f"grid tab0 before: {grid0} (widgets truncated {cut})")

        # stash s3: Sort on the second tab orders that tab only
        self.gl("func", "button", "right")
        time.sleep(0.4)
        pick = self.root_widget("PlayerStashWindow", "tab-picks").get("text", "")
        self.flag("stash_second_tab_shown", pick == name1, f"tab-picks {pick!r}, tab 1 is {name1!r}")
        _, said = self.press_sort("sort tab 2")
        a0, _ = self.stash_items(0)
        a1, _ = self.stash_items(1)
        self.flag("sort_second_tab_sorted", a1 == want1 and any(f"sorted {len(t1)} item(s) in tab '{name1}'" in s for s in said),
                  f"{a1}, want {want1}; {said}")
        self.flag("sort_first_tab_untouched", a0 == t0, f"{a0}")

        # stash s1: back to the first tab, Sort
        self.gl("func", "button", "left")
        time.sleep(0.4)
        pick = self.root_widget("PlayerStashWindow", "tab-picks").get("text", "")
        self.flag("stash_first_tab_shown", pick == name0, f"tab-picks {pick!r}, tab 0 is {name0!r}")
        _, said = self.press_sort("sort tab 1")
        s0, _ = self.stash_items(0)
        self.flag("sort_logged", any(f"sorted {len(t0)} item(s) in tab '{name0}'" in s and "already" not in s for s in said),
                  f"{said}")
        keys = [item_key(e) for e in s0 or []]
        cls_ok = len(keys) == len(t0) and all(keys[i][0] <= keys[i + 1][0] for i in range(len(keys) - 1))
        type_ok, ilvl_ok, seen = cls_ok, cls_ok, set()
        for i in range(len(keys) - 1):
            a, b = keys[i], keys[i + 1]
            if a[0] != b[0]:
                continue
            if a[1] > b[1]:
                type_ok = False  # a weapon/armour slot out of order within a class
            if a[:2] == b[:2] and a[2] != b[2]:
                if (b[0], b[1], b[2]) in seen:
                    type_ok = False  # a weapon family came back after another one
                seen.add((a[0], a[1], a[2]))
            if a[:3] == b[:3] and a[3] < b[3]:
                ilvl_ok = False
        self.flag("sort_class_first", cls_ok, f"class ranks {[k[0] for k in keys]}")
        self.flag("sort_type_second", type_ok, f"slot ranks {[k[1] for k in keys]}, families {[k[2] for k in keys]}")
        self.flag("sort_ilvl_third", ilvl_ok, f"{s0}")
        self.flag("sort_exact", s0 == want0, f"{s0}, want {want0}")
        # the grid on screen shows the new order (the same names, moved as the items were)
        grid1, cut = self.stash_grid()
        want = [grid0[t0.index(e)] for e in want0] if grid0 and len(grid0) == len(t0) else None
        self.flag("sort_grid_follows", want is not None and grid1 == want, f"grid {grid1} (truncated {cut})")

        # stash s2: a second press changes nothing and says so
        _, said = self.press_sort("sort again")
        s0b, _ = self.stash_items(0)
        self.flag("sort_idempotent", s0b == s0 and any("(already in order)" in s for s in said), f"{said}")

        # stash s4: closed (the window saves) and reopened, both tabs keep their order
        self.close_windows()
        self.flag("stash_reopened", self.open_stash())
        r0, _ = self.stash_items(0)
        r1, _ = self.stash_items(1)
        grid2, _ = self.stash_grid()
        self.flag("sort_kept_reopen", r0 == want0 and r1 == want1 and grid2 == grid1,
                  f"tab0 {r0}; tab1 {r1}; grid same {grid2 == grid1}")
        self.close_windows()

    # --- settings search
    def opt(self, widget):
        return self.gl("menu", "hwp_options", "-", widget)

    def search_focus(self):
        # the field takes the keyboard 250 ms after the command (menu "!click"); pressing it
        # while it already has the keyboard does nothing
        self.gl("menu", "hwp_options", "-", "search", "!click")
        time.sleep(0.8)

    def type(self, text):
        self.search_focus()
        self.g.type_text(text, 0.12)
        time.sleep(0.5)

    def rows(self):
        """search field, colours row, swap key row, hint, placeholder."""
        return (self.opt("search"), self.opt("hwp-opt-colors"), self.opt("hwp-opt-swapkey"),
                self.opt("hint"), self.opt("search-hint"))

    def search_clear(self):
        self.search_focus()
        self.g.key("escape", 0.1)
        time.sleep(0.5)

    def settings_search(self):
        """search s1-s8: the Plus tab's search field filters the rows as you type."""
        self.close_windows()
        self.gl("menu", "character")
        time.sleep(0.5)
        f, c, s, h, ph = self.rows()
        hint0 = h.get("texts", "")
        colors_title, _, colors_value = c.get("texts", "").partition(" | ")
        self.flag("search_tab_open", c.get("tab") == "HWPOptionsTab" and c.get("shown") and s.get("shown"),
                  f"colors {c.get('texts')!r}, swapkey {s.get('texts')!r}")
        self.flag("search_placeholder", f.get("input") == "" and ph.get("shown") and "Search settings" in ph.get("texts", ""),
                  f"input {f.get('input')!r}, placeholder {ph.get('shown')} {ph.get('texts')!r}")

        # s2: a title
        self.type("swap")
        f, c, s, h, ph = self.rows()
        # every gl command above opened the console; its key char must not land in the field
        self.flag("search_typed", f.get("input") == "swap", f"input {f.get('input')!r}, typing {f.get('typing')}")
        self.flag("search_filters_title", s.get("shown") and not c.get("shown"), f"swapkey {s.get('shown')}, colors {c.get('shown')}")
        self.flag("search_placeholder_hidden", ph.get("shown") is False, f"placeholder {ph.get('shown')}")

        # s3: one more letter, nothing matches; Backspace brings the row back
        self.type("z")
        f, c, s, h, ph = self.rows()
        self.flag("search_no_match", f.get("input") == "swapz" and not s.get("shown") and not c.get("shown")
                  and h.get("texts") == 'No settings match "swapz".', f"input {f.get('input')!r}, hint {h.get('texts')!r}")
        self.search_focus()
        self.g.key("backspace", 0.1)
        time.sleep(0.5)
        f, c, s, h, ph = self.rows()
        self.flag("search_backspace_refilters", f.get("input") == "swap" and s.get("shown") and not c.get("shown")
                  and h.get("texts") == hint0, f"input {f.get('input')!r}, hint {h.get('texts')!r}")

        # s4: Esc empties the field, every row is back, the menu stays
        self.search_clear()
        f, c, s, h, ph = self.rows()
        self.flag("search_esc_clears", f.get("input") == "" and c.get("shown") and s.get("shown")
                  and c.get("tab") == "HWPOptionsTab" and h.get("texts") == hint0,
                  f"input {f.get('input')!r}, rows {c.get('shown')}/{s.get('shown')}, hint {h.get('texts')!r}")

        # s5: capitals match too
        self.type("COLORS")
        f, c, s, h, ph = self.rows()
        self.flag("search_case_insensitive", f.get("input") == "COLORS" and c.get("shown") and not s.get("shown"),
                  f"input {f.get('input')!r}, colors {c.get('shown')}, swapkey {s.get('shown')}")

        # s6: the row found still works: a click cycles the preset (then back to the first)
        mark = len(self.g.read_log())
        self.gl("menu", "hwp_options", "-", "hwp-opt-colors", "hwp-opt", "colors")
        time.sleep(0.4)
        c2 = self.opt("hwp-opt-colors")
        v2 = c2.get("texts", "").partition(" | ")[2]
        said = re.findall(r"\[HWP:options\] colors -> (.*)", self.log_since(mark))
        self.flag("search_row_works", bool(said) and v2 != colors_value and c2.get("shown"),
                  f"{colors_value!r} -> {v2!r}, log {said}")
        for _ in range(8):
            if v2 == colors_value or not v2:
                break
            self.gl("menu", "hwp_options", "-", "hwp-opt-colors", "hwp-opt", "colors")
            time.sleep(0.3)
            v2 = self.opt("hwp-opt-colors").get("texts", "").partition(" | ")[2]
        self.notes.append(f"colors restored to {v2!r}")
        self.search_clear()

        # s7: a row's value matches as well as its title
        other = (colors_title + " " + s.get("texts", "")).lower()
        words = [w for w in re.findall(r"[a-z]{3,}", colors_value.lower())
                 if w not in other and not re.search(r"(.)\1", w)]
        if words:
            self.type(words[0])
            f, c, s, h, ph = self.rows()
            self.flag("search_matches_value", f.get("input") == words[0] and c.get("shown") and not s.get("shown"),
                      f"value {colors_value!r}, typed {words[0]!r}: colors {c.get('shown')}, swapkey {s.get('shown')}")
            self.search_clear()
        else:
            self.flag("search_matches_value", False, f"no word of the value {colors_value!r} to type")

        # s8: Enter keeps the filter; the menu closed and opened again is unfiltered
        self.type("swap")
        self.g.key("enter", 0.1)
        time.sleep(0.4)
        f, c, s, h, ph = self.rows()
        kept = f.get("input") == "swap" and not f.get("typing") and not c.get("shown")
        closed = self.close_windows()  # not typing: Esc closes the menu
        self.gl("menu", "character")
        time.sleep(0.5)
        f, c, s, h, ph = self.rows()
        self.flag("search_enter_keeps", kept, "filter after Enter")
        self.flag("search_reopen_reset", closed and f.get("input") == "" and c.get("shown") and s.get("shown"),
                  f"closed {closed}, input {f.get('input')!r}, rows {c.get('shown')}/{s.get('shown')}")
        self.close_windows()

    # --- General Merchant, Trinkets tab
    def open_trinkets(self):
        """Use the exit guard until his shop is up. Closing the shop starts his second
        interact, the "Be careful out there!" bubble (NPCBehavior.NPCUpdate, about 2 s),
        and a Use while it shows only dismisses it (NPCBehavior.Use), so retry."""
        self.npc("npc_misc_guard_exit", "actors/npcs/town/npc_misc_guard_exit.unit")
        u = {}
        for _ in range(4):
            u = self.gl("use", "npc_misc_guard_exit")
            if u.get("window") == "HWPMerchantWindow":
                break
            if self.gl("state").get("window") == "HWPMerchantWindow":
                u = dict(u, window="HWPMerchantWindow")
                break
            time.sleep(0.4)
        time.sleep(0.5)
        self.gl("press", "hwp-tab-trinkets")
        time.sleep(0.3)
        return u.get("window") == "HWPMerchantWindow", self.gl("shop")

    def merchant_text(self, wid):
        return self.root_widget("HWPMerchantWindow", wid).get("text", "")

    def stock_check(self, sh, data, tag):
        """trinkets s1/s2 on a stock: 6 entries, 2/2/2, no repeats, the run shop's price."""
        items = sh.get("items") or []
        ids = [i.get("id", "")[len("hwp_trinket_"):] for i in items]
        quals = [title_quality(i.get("title")) for i in items]
        self.flag(f"{tag}_six", sh.get("count") == 6 and all(i.get("id", "").startswith("hwp_trinket_") for i in items),
                  f"{sh.get('count')} entries: {ids}")
        self.flag(f"{tag}_qualities", sorted(quals) == ["common", "common", "rare", "rare", "uncommon", "uncommon"], f"{quals}")
        self.flag(f"{tag}_no_repeats", len(set(ids)) == len(ids) == 6, f"{ids}")
        wrong, prices = [], []
        for i, tid, q in zip(items, ids, quals):
            dq, base = data.get(tid, (q, TRINKET_FALLBACK.get(q, 0)))
            want = int(base * SHOP_RATE)
            prices.append(f"{tid} {q} {i.get('gold')} (base {base})")
            if dq != q or i.get("gold") != want:
                wrong.append(f"{tid}: {q} (data {dq}) {i.get('gold')} != {want}")
        if tag == "tr":
            self.flag("tr_data_matches", bool(data) and all(t in data for t in ids), f"{len(data)} trinkets in the datatables")
        self.flag(f"{tag}_shop_price", bool(items) and not wrong, "; ".join(wrong or prices))
        return ids, quals

    def merchant_trinkets(self):
        """trinkets s1-s9: the Trinkets tab's stock, buying, the hand-over in a run and the
        new stock after every run."""
        data = trinket_data()
        self.close_windows()
        self.set_gold(100000)
        ok, sh = self.open_trinkets()
        self.flag("tr_open", ok and sh.get("window") == "HWPMerchantWindow", f"{sh.get('window')}")
        ids, quals = self.stock_check(sh, data, "tr")
        items = sh.get("items") or []
        price_of = {title_quality(i.get("title")): i.get("gold") for i in items}
        self.notes.append(f"stock: {list(zip(ids, quals))}; prices {price_of}")
        self.flag("tr_packed_zero", self.merchant_text("extra-info") == "Packed: 0", self.merchant_text("extra-info"))

        # s3: the stock stays while no run starts
        self.close_windows()
        _, sh2 = self.open_trinkets()
        ids2 = [i.get("id", "")[len("hwp_trinket_"):] for i in sh2.get("items") or []]
        self.flag("tr_stock_stays", ids2 == ids, f"{ids} -> {ids2}")

        # s4: a rare: its price comes off, it leaves the list and is packed
        bought = []
        idx = quals.index("rare") if "rare" in quals else 0
        price = items[idx].get("gold", 0) if items else 0
        g0, mark = self.gold(), len(self.g.read_log())
        r = self.gl("shop", "buy", idx)
        time.sleep(0.5)
        g1 = self.gold()
        if r.get("changed"):
            bought.append(ids[idx])
        self.flag("tr_buy_paid", r.get("changed") and g0 - g1 == price and r.get("count") == 5,
                  f"gold {g0} -> {g1}, price {price}, entries {r.get('count')}")
        self.flag("tr_buy_packed", self.merchant_text("extra-info") == "Packed: 1"
                  and f"packed trinket {ids[idx] if ids else '?'} for {price} gold" in self.log_since(mark),
                  self.merchant_text("extra-info"))

        # s5: one gold short of the cheapest: refused, nothing paid
        left = r.get("items") or []
        if left:
            j = min(range(len(left)), key=lambda k: left[k].get("gold", 0))
            cheap = left[j].get("gold", 0)
            self.set_gold(cheap - 1)
            r2 = self.gl("shop", "buy", j)
            time.sleep(0.4)
            self.flag("tr_poor_refused", not r2.get("changed") and r2.get("count") == len(left) and self.gold() == cheap - 1,
                      f"{cheap} asked, {cheap - 1} held: changed {r2.get('changed')}, gold {self.gold()}")

        # s6: buy the rest: the list empties and says so; nothing in the run bag in town
        self.set_gold(100000)
        g0, paid = self.gold(), 0
        for _ in range(6):
            cur = self.gl("shop")
            if not cur.get("items"):
                break
            e = cur["items"][0]
            r3 = self.gl("shop", "buy", 0)
            time.sleep(0.3)
            if r3.get("changed"):
                paid += e.get("gold", 0)
                bought.append(e.get("id", "")[len("hwp_trinket_"):])
        g1 = self.gold()
        empty = self.merchant_text("empty")
        self.flag("tr_buy_all_paid", len(bought) == 6 and g0 - g1 == paid, f"bought {bought}, gold {g0} -> {g1}, paid {paid}")
        self.flag("tr_sold_out", self.gl("shop").get("count") == 0 and empty == "Sold out. New trinkets after your next run.",
                  f"empty {empty!r}, packed {self.merchant_text('extra-info')!r}")
        self.flag("tr_not_in_town_bag", self.gl("trinkets").get("count") == 0)
        self.close_windows()
        _, sh3 = self.open_trinkets()
        self.flag("tr_sold_out_stays", sh3.get("count") == 0, f"{sh3.get('count')} entries on reopening")
        self.close_windows()

        # s7: a run: the packed trinkets are in the run bag once its first level starts
        mark = len(self.g.read_log())
        started = self.start_floor(0)
        end = time.time() + 20
        while "handed over" not in self.log_since(mark) and time.time() < end:
            time.sleep(0.5)
        over = re.findall(r"\[HWP:keys\] (handed over .*)", self.log_since(mark))
        tr = self.gl("trinkets")
        self.flag("tr_run_started", started)
        self.flag("tr_handed_over", sorted(tr.get("ids") or []) == sorted(bought) and any("handed over 6" in o for o in over),
                  f"run bag {tr.get('ids')}, {over}")

        # s8: a run's own trinket shop (a shop room's, ShopLevel 1) asks the same per quality
        self.hwp("god", until="god mode")  # the floor's bandits walk in while the shop is read
        pf = self.gl("prefab", RUN_SHOP_PREFAB, 0, -140)
        time.sleep(1)
        u = self.gl("use", "npc_trinket_shop")
        time.sleep(0.5)
        if u.get("window") == "TrinketShopWindow":
            rs = self.gl("shop").get("items") or []
            got = [(title_quality(i.get("title")), i.get("gold")) for i in rs]
            same = bool(got) and all(price_of.get(q) == g and g == int(TRINKET_FALLBACK.get(q, -1) * SHOP_RATE) for q, g in got)
            self.flag("tr_run_shop_same_price", same, f"run shop {got}, merchant {price_of}")
        else:
            self.flag("tr_run_shop_same_price", False, f"prefab {pf.get('ok')}, use {u}")
        self.close_windows()

        # s9: after the run (abandoned) a new full stock; after the next (failed) another
        stocks = [ids]
        for how in ("aborted", "failed"):
            if how == "failed":
                if not self.start_floor(0):
                    self.flag("tr_rerolled_after_failed", False, "no second run")
                    break
                self.gl("abort", "failed")
                back = self.wait_phase("town", 90)
                time.sleep(2)
                self.close_windows()
            else:
                back = self.to_town()
                self.close_windows()
            bag = self.gl("trinkets").get("count")
            mark = len(self.g.read_log())
            _, sh4 = self.open_trinkets()
            new = [i.get("id", "")[len("hwp_trinket_"):] for i in sh4.get("items") or []]
            rolled = re.findall(r"\[HWP:keys\] (trinket stock rolled \(after a run\).*)", self.log_since(mark))
            quals4 = sorted(title_quality(i.get("title")) for i in sh4.get("items") or [])
            self.flag(f"tr_rerolled_after_{how}", back and bool(rolled) and len(new) == 6
                      and quals4 == ["common", "common", "rare", "rare", "uncommon", "uncommon"],
                      f"town {back}, {new}, {rolled}")
            self.flag(f"tr_new_stock_after_{how}", set(new) != set(stocks[-1]),
                      f"{len(set(new) & set(stocks[-1]))} of 6 the same as before")
            if how == "aborted":
                self.flag("tr_run_bag_emptied", bag == 0, f"{bag} trinket(s) in the bag in town")
                self.flag("tr_packed_cleared", self.merchant_text("extra-info") == "Packed: 0", self.merchant_text("extra-info"))
            stocks.append(new)
            self.close_windows()


def run(p, sections="stash_sort,settings_search", **_):
    c = Checks(p)
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
