"""Plan checks for the gear group: weaponswap s3/s5/s8, droptrade s1-s4, chatlinks s1.

The character screen is driven through the verbs in
mods/gamelab-hands/scripts/GameLab/Verbs_gear.as:
- `hover <widgetId> [child]` selects a widget the way the arrow keys do (Leave the old
  interactable, Hover the new one, OnInteractableIndexChanged rebuilds the key hints);
  `hover equipment-inventory 0` is the first bag slot (the clones have no id);
- `navbar [click <i>]` reads the key hints and clicks one the way the mouse does (Hover,
  OnClickDown, OnClickUp);
- `hold context <ms>` runs the context binding's pressed / down / up handlers (only when the
  binding is not a key we can post);
- `items [r]` lists item pickups around the player with their owner.
Keys (X, Q, G, the context key) are posted (gl key), as plan_checks.swap does.

Sections, each group on its own character, in this order:
  gear_char (LabGear), alt_click (weaponswap s3), alt_twohander (s5 slots; leaves the menu
  open on the alt off-hand slot for a shot), alt_wield (s5: can't wield, stays stored),
  full_swap (s8);
  drop_char (LabDrop), drop_hints (droptrade s1; leaves the menu open for a shot), drop_key
  and drop_click (s2), drop_destroy (s3), dropkey_g (s4), chat_link (chatlinks s1)."""
import json
import re
import time

from gamelab.bots.plan_checks import Checks as Base

LONGSWORD = "mainhand_longsword_01"
# req-str 23-48 over ilvl 1-10 (tweak/items/equipment/equipment_weapons_mainhand.sval): a
# level-1 paladin can't wield it, so it goes on with dbg_cht_ignore_equipment_requirements
HEAVY = "mainhand_longsword_04"
BOW = "twohanded_longbow_01"
BAG = "equipment-inventory"  # the bag widget (core hwp-equipmentinventory); its children are the slots
INVENTORY, EQUIPPED = 1, 0   # ItemWidgetType (GUI/Widgets/EquipmentItemWidget.as)


class Checks(Base):
    # --- plumbing
    def new_char(self, name):
        r = self.gl("char", "paladin", name)
        ok = self.wait_phase("town", 60)
        time.sleep(2)
        st = self.gl("state").get("player") or {}
        self.flag(f"{name}_ready", ok and st.get("name") == name, json.dumps(r)[:200])

    def menu(self):
        """The character screen on its bag (equipment) sub-tab, opened the way its key does."""
        r = self.gl("menu", "character", "equipment-inventory")
        time.sleep(0.6)
        return r

    def close(self):
        """Close every window (Escape; never with none open: that opens the pause menu)."""
        for _ in range(3):
            if not self.gl("state").get("window"):
                return True
            self.g.key("escape")
            time.sleep(0.6)
        return not self.gl("state").get("window")

    def hover(self, wid, child=None):
        r = self.gl("hover", wid) if child is None else self.gl("hover", wid, child)
        time.sleep(0.3)
        return r

    def press(self, key, hold=0.05):
        time.sleep(0.3)  # the console the last gl line opened is shut
        self.g.key(key, hold)
        time.sleep(0.7)

    def bag(self):
        """hwp bag: (items, slots)."""
        m = re.findall(r"Bag: (\d+)/(\d+)", self.hwp("bag", 0.3, until="Bag:"))
        return (int(m[-1][0]), int(m[-1][1])) if m else (-1, -1)

    def req_cheat(self, on):
        """dbg_cht_ignore_equipment_requirements (Console/Cheats.as): MayEquip says yes."""
        name = "dbg_cht_ignore_equipment_requirements"
        self.g.console(f"{name} {1 if on else 0}")
        time.sleep(0.3)
        return self.gl("cvars", name).get("cvars", {}).get(name) == (1 if on else 0)

    def floor_items(self, r=80):
        return self.gl("items", r).get("items") or []

    def pick_up(self, name):
        """Take a pickup back the way the use key does (gl use: IUsable.Use ->
        Item::UnitBehavior.Use -> Take), once its drop animation is over."""
        end = time.time() + 4
        while time.time() < end:
            mine = [i for i in self.floor_items() if i["item"] == name]
            if not mine or mine[0]["anim"] <= 0:
                break
            time.sleep(0.3)
        time.sleep(0.4)  # the pickup's own cooldown
        r = self.gl("use", "items/base.unit")
        time.sleep(0.8)
        return r

    def log_since(self, mark):
        return self.g.read_log()[mark:]

    @staticmethod
    def key_of(name):
        """A posted-key name for a binding as FormatKeyName shows it ("[E]" -> "e"), or None."""
        s = re.sub(r"\\c[0-9a-fA-F]{6}|\\d", "", name or "").strip("[] ").lower()
        if len(s) == 1 and s.isalnum():
            return s
        return {"space": "space", "enter": "enter", "return": "enter", "tab": "tab"}.get(s)

    # --- weaponswap
    def gear_char(self):
        self.new_char("LabGear")

    def alt_click(self):
        """weaponswap s3: the alt main-hand slot's tooltip is the stored item, its hint is the
        swap, and a click swaps (EquipmentItemWidget.ClickDown -> HWPGearSlotWidget.OnClick ->
        HWPAltWeaponSlot.Click -> Swap, as X does)."""
        r = self.gl("equip", LONGSWORD, "common", 1)
        sword = self.main_hand()
        self.hwp("swap", 0.5, until="[HWP:weaponswap] set")
        hands = self.main_hand()
        st = self.status()
        self.flag("s3_sword_stored", bool(r.get("ok")) and sword is not None and hands is None and "Sword" in st[1],
                  f"{json.dumps(r)[:120]} {st}")
        time.sleep(1.2)  # the swap's 1 s cooldown gates a click too
        self.menu()
        h = self.hover("hwp-alt-main")
        self.flag("s3_tooltip_item", bool(h.get("ok")) and h.get("item") == st[1] and h.get("tooltip") != "",
                  json.dumps(h)[:400])
        self.flag("s3_nav_swap", any("Swap to weapon set" in t for t in h.get("nav") or []), str(h.get("nav")))
        mark = len(self.g.read_log())
        c = self.gl("menu", "character", "-", "hwp-alt-main", "!click")  # ClickDown 250 ms later
        time.sleep(1.0)
        back = self.main_hand()
        st2 = self.status()
        self.flag("s3_click_swaps", bool(c.get("ok")) and bool(back and sword and back[1] == sword[1])
                  and "[HWP:weaponswap] set" in self.log_since(mark), f"{back} {st2}")
        self.close()

    def alt_twohander(self):
        """weaponswap s5 (slots): a two-hander in the other set shows in the alt off-hand slot
        too, mirrored and dimmed (HWPAltWeaponSlot.Mirrored, HWPGearSlotWidget m_disabledColor).
        Leaves the character screen open on that slot for a shot."""
        self.close()
        r = self.gl("equip", BOW, "common", 1)
        time.sleep(1.2)
        self.press("x")
        st = self.status()
        self.flag("s5_bow_stored", bool(r.get("ok")) and "bow" in st[1].lower() and st[2] == "-", str(st))
        self.menu()
        hm = self.hover("hwp-alt-main")
        ho = self.hover("hwp-alt-off")
        self.flag("s5_off_shows_bow", bool(ho.get("item")) and ho.get("item") == hm.get("item") == st[1],
                  f"main {hm.get('item')!r}, off {ho.get('item')!r}")
        self.flag("s5_off_dimmed", bool(ho.get("mirrored")) and ho.get("shade", 1) < 0.5 and not hm.get("mirrored"),
                  f"off mirrored {ho.get('mirrored')} shade {ho.get('shade')}, main mirrored {hm.get('mirrored')} "
                  f"shade {hm.get('shade')}")

    def alt_wield(self):
        """weaponswap s5 (requirements): an item you can't wield any more stays in the other set,
        and you are told (WeaponSwap.Swap: MayEquip, then the "cannot" reply)."""
        self.close()
        time.sleep(1.2)
        self.press("x")  # the bow back in hand, the other set empty
        on = self.req_cheat(True)
        r = self.gl("equip", HEAVY, "common", 10)  # the bow goes to the bag
        time.sleep(1.2)
        self.press("x")  # the heavy sword stored, hands empty
        off = self.req_cheat(False)
        st0 = self.status()
        self.flag("s5_heavy_stored", on and off and bool(r.get("ok")) and st0[1] not in ("", "-")
                  and self.main_hand() is None, f"cheat {on}/{off}, {json.dumps(r)[:120]}, {st0}")
        time.sleep(1.2)
        mark = len(self.g.read_log())
        self.press("x")
        log = self.log_since(mark)
        st1 = self.status()
        cannot = re.findall(r"\[HWP\] Cannot equip (.*?) \(requirements\), it stays in the other set", log)
        self.flag("s5_cannot_message", bool(cannot) and cannot[-1] == st0[1], str(cannot))
        self.flag("s5_stays_stored", st1[1] == st0[1] and self.main_hand() is None, f"{st0} -> {st1}")

    def full_swap(self):
        """weaponswap s8: bag full, a swap to a set you can't wield while holding an item you
        can't wield either: the held one can't go back to your hands nor into the bag, so it lands
        at your feet owned by you (Item::DropItem with your record: hidden from and refused to
        everyone else, Items/UnitBehavior.as Initialize / Take); the bag never shows more slots
        than you own (core HWPEquipmentInventoryWidget.SlotCount)."""
        self.close()
        on = self.req_cheat(True)
        r = self.gl("equip", HEAVY, "common", 10)  # hands are empty: a second heavy sword in them
        off = self.req_cheat(False)
        hand = self.main_hand()
        self.hwp("set fishing.debug 1")
        got = ""
        for _ in range(60):
            got = self.hwp("fishing catch 1", 0.4)
            if "Your bag is full" in got:
                break
        n0, cap0 = self.bag()
        self.flag("s8_setup", on and off and bool(r.get("ok")) and hand is not None and 0 < cap0 == n0,
                  f"cheat {on}/{off}, {json.dumps(r)[:120]}, bag {n0}/{cap0}, {got.strip()[-120:]}")
        before = {i["unit"] for i in self.floor_items()}
        st0 = self.status()
        time.sleep(1.2)
        mark = len(self.g.read_log())
        self.press("x")
        time.sleep(0.5)
        log = self.log_since(mark)
        n1, cap1 = self.bag()
        new = [i for i in self.floor_items() if i["unit"] not in before]
        st1 = self.status()
        floor = re.findall(r"\[HWP\] (.*?) no longer fits your hands and your bag is full: it lies at your feet", log)
        landed = [i for i in new if floor and i["item"] == floor[-1]]
        self.flag("s8_cannot", "[HWP] Cannot equip" in log, log.strip()[-300:])
        self.flag("s8_to_feet", bool(landed) and landed[0]["dist"] <= 60, f"{floor} {json.dumps(new)[:300]}")
        self.flag("s8_only_you", bool(landed) and landed[0]["owner"] == "me" and not landed[0]["hidden"],
                  json.dumps(landed)[:200])
        self.flag("s8_hands_empty_alt_kept", self.main_hand() is None and st1[1] == st0[1], f"{st0} -> {st1}")
        self.flag("s8_bag_capped", n1 == n0 and n1 <= cap1, f"bag {n0}/{cap0} -> {n1}/{cap1}")
        self.menu()
        h = self.hover(BAG, 0)
        self.flag("s8_slots_shown", bool(h.get("ok")) and h.get("children") == cap1,
                  f"{h.get('children')} slot widgets, {cap1} owned")
        self.close()
        self.hwp("sell")

    # --- droptrade
    def drop_char(self):
        self.new_char("LabDrop")
        r = self.gl("equip", LONGSWORD, "common", 1)  # the starting mace goes to the bag
        n, cap = self.bag()
        self.flag("drop_bag_item", bool(r.get("ok")) and n >= 1, f"bag {n}/{cap}")

    def drop_hints(self):
        """droptrade s1: an inventory item's hints read Back, Equip, Compare, Destroy, [Q] Drop;
        Destroy and Drop are clickable (Character.as OnInteractableIndexChanged). Leaves the
        screen open on the item for a shot."""
        self.menu()
        h = self.hover(BAG, 0)
        nav = h.get("nav") or []
        click = h.get("clickable") or []
        self.flag("s1_hover_item", bool(h.get("ok")) and bool(h.get("item")) and h.get("type") == INVENTORY
                  and h.get("tooltip") != "", json.dumps(h)[:400])
        self.flag("s1_hints", len(nav) == 5 and all(w in nav[i + 1] for i, w in enumerate(["Equip", "Compare", "Destroy"]))
                  and nav[4] == "[Q] Drop", str(nav))
        self.flag("s1_hints_clickable", len(click) == 5 and click[3] and click[4], str(click))

    def drop_key(self):
        """droptrade s2: Q drops the hovered item at your feet at once (no dialog), it leaves the
        bag, anyone may take it, and picking it up works."""
        self.menu()
        name = self.hover(BAG, 0).get("item", "")
        n0, _ = self.bag()
        before = {i["unit"] for i in self.floor_items()}
        mark = len(self.g.read_log())
        self.press("q")
        log = self.log_since(mark)
        n1, _ = self.bag()
        window = self.gl("state").get("window")
        new = [i for i in self.floor_items() if i["unit"] not in before and i["item"] == name]
        self.flag("s2_q_drops", bool(name) and f"[HWP:droptrade] dropped {name}" in log, f"{name!r}: {log.strip()[-200:]}")
        self.flag("s2_no_dialog", window == "PlayerMenu", str(window))
        self.flag("s2_left_bag", n1 == n0 - 1, f"bag {n0} -> {n1}")
        self.flag("s2_at_feet", bool(new) and new[0]["dist"] <= 60, json.dumps(new)[:200])
        self.flag("s2_anyone", bool(new) and new[0]["owner"] == "shared", json.dumps(new)[:200])
        self.close()
        u = self.pick_up(name)
        n2, _ = self.bag()
        left = [i for i in self.floor_items() if new and i["unit"] == new[0]["unit"]]
        self.flag("s2_pickup", bool(u.get("ok")) and n2 == n0 and not left, f"{json.dumps(u)[:160]}, bag {n1} -> {n2}")

    def drop_click(self):
        """droptrade s2: clicking the Drop hint does what Q does."""
        self.menu()
        name = self.hover(BAG, 0).get("item", "")
        n0, _ = self.bag()
        mark = len(self.g.read_log())
        c = self.gl("navbar", "click", 4)
        time.sleep(0.5)
        log = self.log_since(mark)
        n1, _ = self.bag()
        self.flag("s2_click_drop", bool(c.get("handler")) and bool(name) and f"[HWP:droptrade] dropped {name}" in log
                  and n1 == n0 - 1, f"{json.dumps(c)[:200]}, bag {n0} -> {n1}")
        self.close()
        self.pick_up(name)

    def drop_destroy(self):
        """droptrade s3: clicking Destroy opens the vanilla confirm (Character.as MenuAdditional ->
        ShowDialog "destroy"); No keeps the item. A hovered equipped item has no Drop hint and Q
        drops nothing (HWPHoveredItem: inventory items only)."""
        self.menu()
        self.hover(BAG, 0)
        n0, _ = self.bag()
        c = self.gl("navbar", "click", 3)
        time.sleep(0.5)
        n1, _ = self.bag()
        self.flag("s3_destroy_confirm", bool(c.get("handler")) and c.get("top") == "DialogWindow" and n1 == n0,
                  f"{json.dumps(c)[:200]}, bag {n0} -> {n1}")
        self.gl("func", "no")  # the dialog's own No (DialogWindow.OnFunc -> Close)
        time.sleep(0.5)
        window = self.gl("state").get("window")
        n2, _ = self.bag()
        self.flag("s3_no_keeps", window == "PlayerMenu" and n2 == n0, f"{window}, bag {n0} -> {n2}")
        e0 = self.main_hand()
        h = self.hover("mainhand")
        self.flag("s3_equipped_no_drop_hint", bool(h.get("ok")) and h.get("type") == EQUIPPED
                  and not any("Drop" in t for t in h.get("nav") or []), json.dumps(h)[:300])
        before = {i["unit"] for i in self.floor_items()}
        mark = len(self.g.read_log())
        self.press("q")
        log = self.log_since(mark)
        n3, _ = self.bag()
        new = [i for i in self.floor_items() if i["unit"] not in before]
        self.flag("s3_equipped_not_dropped", "[HWP:droptrade] dropped" not in log and self.main_hand() == e0
                  and n3 == n0 and not new, f"bag {n0} -> {n3}, new {json.dumps(new)[:160]}")
        self.close()

    def dropkey_g(self):
        """droptrade s4: hwp dropkey 10 G: the hint reads [G] Drop, G drops, Q no longer does."""
        rep = self.hwp("dropkey 10 G", 0.3, until="Inventory drop key")
        self.menu()
        h = self.hover(BAG, 0)
        name, nav = h.get("item", ""), h.get("nav") or []
        self.flag("s4_hint_g", "Inventory drop key: G" in rep and len(nav) == 5 and nav[4] == "[G] Drop",
                  f"{rep.strip()[-120:]} | {nav}")
        n0, _ = self.bag()
        mark = len(self.g.read_log())
        self.press("q")
        log = self.log_since(mark)
        n1, _ = self.bag()
        self.flag("s4_q_ignored", "[HWP:droptrade] dropped" not in log and n1 == n0, f"bag {n0} -> {n1}")
        self.menu()  # in case Q is bound to something in the menu
        self.hover(BAG, 0)
        mark = len(self.g.read_log())
        self.press("g")
        log = self.log_since(mark)
        n2, _ = self.bag()
        self.flag("s4_g_drops", bool(name) and f"[HWP:droptrade] dropped {name}" in log and n2 == n0 - 1,
                  f"bag {n0} -> {n2}")
        self.hwp("dropkey 20 Q", 0.3, until="Inventory drop key")
        self.close()
        self.pick_up(name)

    # --- chatlinks
    def chat_link(self):
        """chatlinks s1: holding the context key ~1 s on a bag item links it (Character.as
        MenuContextUp, m_contextC >= 1000 -> GameEvents::PlayerLinkedItem). The vanilla loot
        log shows "You show everyone [item]" (LootLog.OnEventPlayerLinkedItem, read by
        `overlays`); the chat line HWPChatLinksModule adds is drawn by the menu script context,
        which gl can't read: the scenario's shot right after this section shows it."""
        self.menu()
        h = self.hover(BAG, 0)
        name, color = h.get("item", ""), h.get("color", "")
        nb = self.gl("navbar")
        key = self.key_of(nb.get("context"))
        via = f"key {key}"
        if key:
            self.press(key, hold=1.3)
        else:
            via = "hold verb"
            self.gl("hold", "context", 1100)
        texts = [a.get("text", "") for a in self.gl("overlays").get("announces") or []]
        hit = [t for t in texts if name and name in t]
        if not hit and key:
            via += ", then hold verb"
            self.gl("hold", "context", 1100)
            texts = [a.get("text", "") for a in self.gl("overlays").get("announces") or []]
            hit = [t for t in texts if name and name in t]
        self.flag("link_event", bool(hit), f"context binding {nb.get('context')!r} via {via}: {texts}")
        self.flag("link_rarity_colour", any(f"\\c{color}[" in t for t in hit), f"colour {color}: {hit}")
        self.close()


def run(p, sections="gear_char,alt_click", **_):
    c = Checks(p)
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
