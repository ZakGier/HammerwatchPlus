"""Test-plan checks that need arithmetic between game reads (gold before and after, an
item's roll before and after), which a scenario's expect can't do. Each section returns
its own flags; the scenario asserts them. Everything goes through gl verbs, HWP console
commands and the game's own windows (gl use / press / shop), never real input.

Sections: gambler (reroll gold/tokens/refusals), sell (wares at the Gambler), merchant
(bag slot), traps (pirate fish traps), full_bag (a catch with a full bag), mission (start
Bandit Keep), bets (affordable bets, flips, reshuffle), farm (can, seed, plant, water, well),
petshop / petbowl / petgold (HoH1 pets, XP and feeding, the Gold toggle in a run),
goldpet / goldpet_run (the Gold Collector vendor and the cat in a run), floor_chests (the floor's own locked chests), chests (silver key loot, ace chest legendary and epic), swap (weapon sets
with the X key), swap_sets (the other set's slots and HUD tip, a bow, R as the key, swapdrop)."""
import json
import re
import time


class Checks:
    def __init__(self, p):
        self.p = p
        self.g = p.game
        self.out = {}
        self.notes = []

    # --- plumbing
    def gl(self, *a, **kw):
        return self.g.gl_cmd(*a, **kw)

    def hwp(self, line, wait=0.8, until=None, timeout=4.0):
        """An HWP console command; the log text it added. With `until`, polls up to
        `timeout` seconds for that text (a reply can land a few frames late)."""
        mark = len(self.g.read_log())
        for attempt in range(2):
            self.g.console("hwp " + line)
            time.sleep(wait)
            end = time.time() + timeout
            while until and until not in self.g.read_log()[mark:] and time.time() < end:
                time.sleep(0.25)
            # a console line can arrive mangled (seen: a stray backtick before "hwp"); once more
            if not until or until in self.g.read_log()[mark:]:
                break
        return self.g.read_log()[mark:]

    def gold(self):
        return self.gl("inv")["materials"]["gold"]

    def tokens(self):
        m = re.findall(r"Bet tokens: (\d+)", self.hwp("wares", 0.3, until="Bet tokens"))
        return int(m[-1]) if m else -1

    def main_hand(self):
        v = self.gl("inspect", "player", "equipped").get("value") or [None]
        return v[0]

    def widget_text(self):
        return json.dumps(self.gl("widgets", 12))

    def widget(self, wid, depth=12):
        """The first open widget with this id (the widgets dump: type, visible, text for
        TextWidgets, enabled for buttons), or {}. A button's own caption is a BitmapString
        the dump can't read back."""
        for root in self.gl("widgets", depth).get("roots", []):
            for n in root.get("nodes", []):
                if n.get("id") == wid:
                    return n
        return {}

    def flag(self, name, ok, note=""):
        self.out[name] = bool(ok)
        if note:
            self.notes.append(f"{name}: {note}")

    def wait_phase(self, phase, timeout=150):
        end = time.time() + timeout
        while time.time() < end:
            try:
                if self.gl("state").get("phase") == phase:
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

    # --- sections
    def gambler(self):
        self.hwp("material gold 300000")
        r = self.gl("equip", "mainhand_mace_01", "rare", 3)
        if not r.get("ok"):
            r = self.gl("equip", "mainhand_mace_01", "rare", 1)
        ilvl = r.get("ilvl", 1)
        self.flag("rare_equipped", r.get("ok"), f"ilvl {ilvl}")
        u = self.gl("use", "hwp_gambler")
        self.flag("gambler_open", u.get("ok"), str(u.get("window")))
        time.sleep(0.5)

        # gold reroll: 2000 x ilvl, same base and quality, new roll
        e0, g0 = self.main_hand(), self.gold()
        self.gl("press", "reroll-btn")
        time.sleep(0.6)
        e1, g1 = self.main_hand(), self.gold()
        msg = self.widget("result-text").get("text", "")
        self.flag("reroll_message", "Rerolled" in msg, msg)
        self.flag("reroll_cost", g0 - g1 == 2000 * ilvl, f"gold {g0} -> {g1}, ilvl {ilvl}")
        self.flag("reroll_changed", bool(e0 and e1 and e0[1] == e1[1] and e0[3] == e1[3] and e0 != e1),
                  f"{e0} -> {e1}")

        # too little gold: refused, nothing changes, the price is shown
        self.gl("material", "gold", -(g1 - 100))
        time.sleep(0.3)
        g2 = self.gold()
        self.gl("press", "reroll-btn")
        time.sleep(0.6)
        e3, g3 = self.main_hand(), self.gold()
        # the button's own caption (the price) is a BitmapString the dump can't read; the
        # refusal line under the cards names the price
        msg = self.widget("result-text").get("text", "")
        self.flag("reroll_poor_refused", g2 == g3 == 100 and e3 == e1, f"gold {g2} -> {g3}")
        self.flag("reroll_poor_message", "Not enough gold" in msg and str(2000 * ilvl) in msg, msg)

        # tokens: 1 per 5 item levels
        self.hwp("tokens 3")
        t0 = self.tokens()
        self.gl("press", "reroll-tok-btn")
        time.sleep(0.6)
        e4, t1 = self.main_hand(), self.tokens()
        cost = (max(1, ilvl) + 4) // 5
        self.flag("token_reroll", t0 - t1 == cost and e4 != e3, f"tokens {t0} -> {t1}, cost {cost}")
        # spend the rest, then a token reroll is refused
        for _ in range(10):
            before = self.tokens()
            if before < cost:
                break
            self.gl("press", "reroll-tok-btn")
            time.sleep(0.5)
            if self.tokens() == before:
                break
        e5, t5 = self.main_hand(), self.tokens()
        self.gl("press", "reroll-tok-btn")
        time.sleep(0.6)
        e6, t6 = self.main_hand(), self.tokens()
        msg = self.widget("result-text").get("text", "")
        self.flag("token_poor_refused", t5 == t6 and e5 == e6, f"tokens {t5} -> {t6}")
        self.flag("token_poor_message", "Not enough bet tokens" in msg and f"costs {cost}" in msg, msg)
        self.g.key("escape")
        time.sleep(0.5)

        # a legendary keeps its modifiers
        r = self.gl("equip", "mainhand_mace_01", "legendary", 1)
        if r.get("ok") and self.gl("use", "hwp_gambler").get("ok"):
            time.sleep(0.4)
            self.hwp("material gold 100000")
            e7, g7 = self.main_hand(), self.gold()
            self.gl("press", "reroll-btn")
            time.sleep(0.6)
            e8, g8 = self.main_hand(), self.gold()
            text = self.widget("result-text").get("text", "")
            self.flag("legendary_refused", e7 == e8 and g7 == g8 and "kindly" in text,
                      f"quality {r.get('quality')}, gold {g7} -> {g8}")
            self.g.key("escape")
            time.sleep(0.5)
        else:
            self.notes.append(f"legendary_refused: no legendary mace ({r})")

    def sell(self):
        # wares: two 1-star fish and a wild carrot plot's crop
        self.hwp("set fishing.debug 1")
        self.hwp("set farm.debug 1")
        self.hwp("fishing catch 1")
        self.hwp("fishing catch 1")
        self.hwp("farm wild carrot", 1.5)
        self.gl("use", "wild/carrot")
        time.sleep(0.8)
        wares = self.hwp("wares")
        t0, g0 = self.tokens(), self.gold()
        self.gl("use", "hwp_gambler")
        time.sleep(0.6)
        self.gl("press", "sell-btn")
        time.sleep(0.8)
        msg = self.widget("result-text").get("text", "")
        self.g.key("escape")
        time.sleep(0.4)
        t1, g1 = self.tokens(), self.gold()
        after = self.hwp("wares", 0.3, until="Bet tokens")
        self.flag("sell_message", "Sold your wares" in msg, msg)
        self.flag("sell_fish_tokens", t1 - t0 == 2, f"tokens {t0} -> {t1}")
        self.flag("sell_crops_gold", g1 > g0, f"gold {g0} -> {g1}")
        self.flag("sell_emptied", "You carry no wares" in after, wares.strip()[-200:])

    def merchant(self):
        self.hwp("material gold 300000")
        self.gl("spawn", "actors/npcs/town/npc_misc_guard_exit.unit", 30, 0)
        time.sleep(0.8)
        self.gl("use", "npc_misc_guard_exit")
        time.sleep(0.5)
        p0 = self.gl("shop")["items"][4]["gold"]
        b0 = re.findall(r"Bag: \d+/(\d+) items", self.hwp("bag", 0.3, until="Bag:"))
        g0 = self.gold()
        self.gl("shop", "buy", 4)
        time.sleep(0.6)
        p1 = self.gl("shop")["items"][4]["gold"]
        b1 = re.findall(r"Bag: \d+/(\d+) items", self.hwp("bag", 0.3, until="Bag:"))
        g1 = self.gold()
        self.flag("bag_slot_bought", bool(b0 and b1 and int(b1[-1]) == int(b0[-1]) + 1), f"cap {b0} -> {b1}")
        self.flag("bag_slot_paid", g0 - g1 == p0, f"gold {g0} -> {g1}, price {p0}")
        self.flag("bag_slot_price_rises", p1 > p0, f"{p0} -> {p1}")
        # buy to the full 32: the entry is then unavailable (greyed) and a press does nothing
        self.hwp("material gold 5000000")
        for _ in range(10):
            it = self.gl("shop")["items"][4]
            if not it.get("available", True):
                break
            self.gl("shop", "buy", 4)
            time.sleep(0.4)
        it = self.gl("shop")["items"][4]
        cap = re.findall(r"Bag: \d+/(\d+) items", self.hwp("bag", 0.3, until="Bag:"))
        g2 = self.gold()
        r = self.gl("shop", "buy", 4)
        time.sleep(0.4)
        cap2 = re.findall(r"Bag: \d+/(\d+) items", self.hwp("bag", 0.3, until="Bag:"))
        self.flag("bag_slot_full_greyed", it.get("available") is False and cap[-1:] == ["32"], f"{it}, cap {cap[-1:]}")
        self.flag("bag_slot_full_refused", cap2[-1:] == ["32"] and self.gold() == g2 and not r.get("changed"),
                  f"cap {cap2[-1:]}, gold {g2} -> {self.gold()}")
        self.g.key("escape")
        time.sleep(0.4)

    def traps(self):
        self.hwp("material gold 300000")
        paid, replies = [], []
        for i in range(4):
            g0 = self.gold()
            # a bought trap only takes the gold; the 4th gets the pirate's refusal
            replies.append(self.hwp("fishing buy trap", 0.5, until="traps in the water" if i == 3 else None))
            paid.append(g0 - self.gold())
        status = self.hwp("fishing traps", 0.3, until="[HWP] Fish traps")
        self.flag("traps_prices", paid == [500, 1000, 2000, 0], f"paid {paid}")
        refusal = re.findall(r"\[HWP\] (Ye've .*)", replies[3])
        self.flag("traps_fourth_refused", bool(refusal), refusal[0] if refusal else replies[3].strip()[-200:])
        self.flag("traps_listed", "Fish traps 3/3" in status, status.strip()[-200:])

    def full_bag(self):
        self.hwp("set fishing.debug 1")
        got = ""
        for _ in range(40):
            got = self.hwp("fishing catch 1", 0.4)
            if "Your bag is full" in got:
                break
        near = self.gl("near", 60, "items/base.unit")  # a dropped item is an items/base.unit
        self.flag("full_bag_feet", "Your bag is full" in got, got.strip()[-200:])
        units = near.get("units") or []
        self.flag("full_bag_fish_on_ground", bool(units) and units[0]["dist"] <= 60, json.dumps(units[:3]))
        self.hwp("sell")

    def mission(self):
        # locks roll when a floor's chests appear: every one locked, none ace
        self.hwp("set keys.lock_chance 1")
        self.hwp("set keys.ace_chance 0")
        self.flag("mission_started", self.start_floor(0))

    def start_floor(self, floor):
        r = self.gl("mission", "bandit_keep", floor)
        ok = bool(r.get("ok")) and self.wait_phase("mission")
        time.sleep(3)
        pl = self.gl("state").get("player", {})
        self.start = (pl.get("x", 0.0), pl.get("y", 0.0))
        self.used = []
        return ok

    def chest_spot(self):
        """Clear the enemies and teleport back to the mission start (opening a chest walks the player off), then
        pick an offset nobody used yet that the pathfinder can reach: a chest spawned into
        a wall can't be walked to."""
        # the keep's bandits walk in while the chests are opened; one killed the player
        # before the third chest (072156), so clear them first (a measurement step)
        self.gl("cull")
        sx, sy = getattr(self, "start", (None, None))
        if sx is not None:
            self.gl("teleport", sx, sy)
            time.sleep(0.4)
        else:
            pl = self.gl("state").get("player", {})
            sx, sy = pl.get("x", 0.0), pl.get("y", 0.0)
        # nodes > 0 is a path found; 0 is no path or a straight line, so it comes second
        spots = [(90, 0), (90, 45), (90, -45), (45, 60), (45, -60), (130, 0), (0, 70), (0, -70),
                 (-45, 60), (-45, -60), (-90, 0), (60, 100), (-60, 100)]
        maybe = []
        for dx, dy in spots:
            if (dx, dy) in self.used:
                continue
            pf = self.gl("pathfind", sx + dx, sy + dy)
            if pf.get("ok") and pf.get("nodes", 0) > 0:
                self.used.append((dx, dy))
                return dx, dy
            if pf.get("ok") and pf.get("nodes", -1) == 0:
                maybe.append((dx, dy))
        dx, dy = maybe[0] if maybe else (90, 0)
        self.used.append((dx, dy))
        return dx, dy

    def floor_chests(self):
        """keys s3: the floor's own reward chests are all locked; without the key a use does
        nothing, with it the chest opens and its loot appears."""
        # Bandit Keep floors roll 0 or 1 equipment chests (min-equipment "0 1"): next floor
        # until one has some
        self.hwp("set keys.debug 1")  # keygive is a debug command
        tiers = {"bronze": 0, "silver": 1, "gold": 2, "platinum": 2}
        for floor in range(5):
            if floor and not self.start_floor(floor):
                break
            self.gl("cull")
            st = self.hwp("keys", 0.3, until="locked chests this level")
            locked = re.findall(r"locked chests this level: (\d+)", st)
            counts = re.findall(r"Keys: bronze (\d+), silver (\d+), gold (\d+), ace (\d+)", st)
            chests = [u for u in self.gl("near", 5000, "items/chests/chest_").get("units", [])
                      if u.get("name", "").split("/")[-1].split("_")[1] in tiers]
            if chests:
                break
        names = sorted({u["name"].split("/")[-1] for u in chests})
        n = int(locked[-1]) if locked else -1
        self.flag("floor_all_locked", n > 0 and n == len(chests), f"floor {floor}: locked {n}, chests {len(chests)}: {names}")
        if not chests or not counts:
            self.notes.append(f"floor_chests: nothing to open ({st.strip()[-200:]})")
            return
        # the nearest chest can sit where the pathfinder finds no route (seen 080325): the
        # first chest the Pilot reaches, else teleport beside the nearest
        c = None
        for cand in chests:
            tier = cand["name"].split("/")[-1].split("_")[1]
            key = "gold" if tier == "platinum" else tier
            have = int(counts[-1][tiers[tier]])
            if have:
                continue
            mark = len(self.g.read_log())
            r = self.p.use(cand["unit"], timeout=40)
            if r.result != "no_route":
                c = cand
                break
            self.notes.append(f"floor: no route to {cand['name']} at {cand.get('x')},{cand.get('y')}")
        if c is None:
            c = chests[0]
            tier = c["name"].split("/")[-1].split("_")[1]
            key = "gold" if tier == "platinum" else tier
            have = int(counts[-1][tiers[tier]])
            self.gl("teleport", c["x"], c["y"] + 20)
            time.sleep(0.5)
            mark = len(self.g.read_log())
            r = self.p.use(c["unit"], timeout=20) if not have else None
        around = None
        if not have:
            time.sleep(1.5)
            log = self.g.read_log()[mark:]
            still = [u for u in self.gl("near", 5000, "items/chests/chest_").get("units", []) if u["unit"] == c["unit"]]
            self.flag("floor_no_key_nothing", "unlocked a" not in log and bool(still), f"{r.result}: {r.reason}")
            # standing at the chest now; items/ only: an unfiltered near hits its 64-unit cap
            around = len(self.gl("near", 80, "items/").get("units") or [])
        else:
            self.notes.append(f"floor_no_key_nothing: already had {have} {key} key(s)")
        give = self.hwp(f"keygive {key} 1", 0.3, until="key(s)")
        time.sleep(0.5)
        self.notes.append("floor keygive: " + " ".join(re.findall(r"\[HWP\] [^\n]*", give))[-160:])
        self.notes.append("floor keys: " + " ".join(re.findall(r"Keys: [^\n]*", self.hwp("keys", 0.3, until="Keys:")))[-200:])
        self.notes.append("floor usables: " + json.dumps(self.gl("usables"))[:600])
        mark = len(self.g.read_log())
        # a teleport spot can sit in a wall's corner the walk can't leave: try the
        # chest's other sides when the Pilot reports stuck
        for dx, dy in [(0, 0), (0, -24), (24, 0), (-24, 0), (0, 40)]:
            if (dx, dy) != (0, 0):
                self.gl("teleport", c["x"] + dx, c["y"] + dy)
                time.sleep(0.5)
            r = self.p.use(c["unit"], timeout=40)
            if "stuck" not in (r.reason or ""):
                break
        time.sleep(2.5)
        log = self.g.read_log()[mark:]
        after = len(self.gl("near", 80, "items/").get("units") or [])
        self.flag("floor_key_opens", f"unlocked a {key} chest" in log, f"{c['name']}: {r.result}: {r.reason}")
        self.flag("floor_loot_spawned", around is not None and after > around, f"units within 80: {around} -> {after}")

    def open_chest(self, unit_name, mark):
        units = self.gl("near", 300, unit_name).get("units") or []
        if not units:
            return "", f"no {unit_name} near"
        r = self.p.use(units[0]["unit"], timeout=15)
        time.sleep(2.5)
        return self.g.read_log()[mark:], f"{r.result}: {r.reason}"

    def chests(self):
        self.hwp("set keys.debug 1")
        self.hwp("set keys.lock_chance 1")
        # silver: the chest's own (silver) table
        if not hasattr(self, "used"):
            self.used = []
        self.hwp("keygive silver 1")
        dx, dy = self.chest_spot()
        self.gl("spawn", "items/chests/chest_silver_equipment.unit", dx, dy)
        time.sleep(1.5)
        before = self.gl("scan", 300)
        mark = len(self.g.read_log())
        log, r = self.open_chest("chest_silver", mark)
        after = self.gl("scan", 300)
        self.flag("silver_unlocked", "unlocked a silver chest" in log, r)
        self.notes.append("silver scan before: " + json.dumps({k: v for k, v in before.items() if k not in ("raw",)})[:400])
        self.notes.append("silver scan after: " + json.dumps({k: v for k, v in after.items() if k not in ("raw",)})[:400])
        # ace: every gold chest is red; the legendary half and the epic half
        self.hwp("set keys.ace_chance 1")
        for leg, tag in ((1, "legendary"), (0, "epic")):
            self.hwp(f"set keys.legendary_chance {leg}")
            self.hwp("keygive ace 1")
            dx, dy = self.chest_spot()
            self.gl("spawn", "items/chests/chest_gold_equipment.unit", dx, dy)
            self.notes.append(f"ace {tag} chest at +{dx},{dy}")
            time.sleep(1.5)
            mark = len(self.g.read_log())
            log, r = self.open_chest("chest_gold", mark)
            self.flag(f"ace_{tag}_unlocked", "unlocked a ace chest" in log, r)
            if leg:
                self.flag("ace_legendary_given", "ace chest: legendary for 1 player(s)" in log)
            else:
                self.flag("ace_epic_no_legendary", "unlocked a ace chest" in log and "ace chest: legendary" not in log)

    def swap(self):
        e0 = self.gl("inspect", "player", "equipped")["value"]
        self.g.key("x")
        time.sleep(0.6)
        e1 = self.gl("inspect", "player", "equipped")["value"]
        time.sleep(1.2)  # past the swap's 1 s cooldown
        self.g.key("x")
        time.sleep(0.1)
        self.g.key("x")  # spam: within the cooldown, ignored
        time.sleep(1.5)
        e2 = self.gl("inspect", "player", "equipped")["value"]
        st = self.hwp("swapkey")
        self.flag("swap_empty_hands", e0[0] is not None and e1[0] is None, f"{e0[0]} -> {e1[0]}")
        self.flag("swap_back_once", e2[0] == e0[0], f"{e2[0]}")
        self.notes.append("swap status: " + st.strip()[-200:])

    def status(self):
        """hwp swapkey's line: (set in hand, other main, other off)."""
        st = self.hwp("swapkey", 0.3, until="[HWP] Weapon set")
        m = re.findall(r"\[HWP\] Weapon set (\d) in hand; other set: (.*?) / (.*?); key", st)
        return m[-1] if m else ("", "", "")

    def alt_slots(self):
        """The character screen's other-set slots, opened with C: {id: item name, "" when
        empty, None when the slot widget isn't there}."""
        self.g.key("c")
        time.sleep(1.0)
        dump = self.gl("widgets", 20).get("roots", [])
        out = {}
        for k in ("hwp-alt-main", "hwp-alt-off"):
            out[k] = next((n for root in dump for n in root.get("nodes", []) if n.get("id") == k), None)
        window = "/".join(r.get("root", "") for r in dump if not r.get("root", "").startswith("HUD"))
        self.g.key("escape")
        time.sleep(0.6)
        return {k: (None if v is None else v.get("item", "")) for k, v in out.items()}, window, out

    def swap_sets(self):
        """weaponswap s1, s2, s6 on top of `swap` (which leaves set 1 in hand, the other empty)."""
        r = self.gl("equip", "mainhand_longsword_01", "common", 1)
        self.flag("sword_equipped", r.get("ok"), json.dumps(r)[:200])
        sword = self.main_hand()
        time.sleep(1.2)
        self.g.key("x")
        time.sleep(0.8)
        hands = self.main_hand()
        st = self.status()
        hud = [root for root in self.gl("widgets", 4).get("roots", []) if root.get("root") == "HUD:HWPWeaponSwapHUD"]
        tip_visible = bool(hud and hud[0].get("visible"))
        tip_text = json.dumps(hud[0].get("nodes", []))[:300] if hud else ""
        slots, window, raw = self.alt_slots()
        self.flag("s1_hands_empty", sword is not None and hands is None, f"{sword} -> {hands}")
        self.flag("s1_sword_stored", "Sword" in st[1] or "sword" in st[1].lower(), str(st))
        self.flag("s1_tip_shown", tip_visible and "press X to swap" in tip_text, tip_text)
        self.flag("s1_alt_slot_shows_sword", bool(slots["hwp-alt-main"]) and slots["hwp-alt-main"] == st[1],
                  f"{window}: {json.dumps(raw)[:300]}")

        # s2: a bow into the empty hands, X: the sword comes back, the bow goes to the other set
        r = self.gl("equip", "twohanded_longbow_01", "common", 1)
        self.flag("bow_equipped", r.get("ok"), json.dumps(r)[:200])
        bow = self.main_hand()
        time.sleep(1.2)
        self.g.key("x")
        time.sleep(0.8)
        back = self.main_hand()
        st2 = self.status()
        slots2, _, raw2 = self.alt_slots()
        self.flag("s2_sword_back", bool(back and sword and back[1] == sword[1]), f"{back}")
        self.flag("s2_bow_stored", bool(bow) and "bow" in st2[1].lower(), str(st2))
        # s5 (part): a two-hander shows in both other-set slots
        self.notes.append("two-hander in the other set, slots: " + json.dumps(raw2)[:300])
        self.flag("s5_twohander_both_slots", bool(slots2["hwp-alt-main"]) and slots2["hwp-alt-off"] == slots2["hwp-alt-main"],
                  json.dumps(slots2))

        # s6: R swaps instead of X; swapdrop puts the other set in the bag
        rep = self.hwp("swapkey 21 R", 0.3, until="[HWP]")
        time.sleep(1.2)
        mark = len(self.g.read_log())
        self.g.key("x")
        time.sleep(1.3)
        x_ignored = "[HWP:weaponswap] set" not in self.g.read_log()[mark:]
        self.g.key("r")
        time.sleep(0.8)
        r_swapped = "[HWP:weaponswap] set" in self.g.read_log()[mark:]
        self.flag("s6_r_swaps", r_swapped, rep.strip()[-160:])
        self.flag("s6_x_no_longer", x_ignored)
        self.hwp("swapkey 27 X", 0.3, until="[HWP]")
        bag0 = re.findall(r"Bag: (\d+)/", self.hwp("bag", 0.3, until="Bag:"))
        drop = self.hwp("swapdrop", 0.3, until="[HWP]")
        bag1 = re.findall(r"Bag: (\d+)/", self.hwp("bag", 0.3, until="Bag:"))
        st3 = self.status()
        slots3, _, _ = self.alt_slots()
        self.flag("s6_swapdrop", "moved to your inventory" in drop and bool(bag0 and bag1) and int(bag1[-1]) > int(bag0[-1]),
                  f"bag {bag0[-1:]} -> {bag1[-1:]}, {st3}")
        self.flag("s6_alt_slots_empty", slots3["hwp-alt-main"] == "" and slots3["hwp-alt-off"] == "", json.dumps(slots3))


    # --- plan-t9: bets, the farm, pets, the gold pet
    def set_gold(self, n):
        self.gl("material", "gold", n - self.gold())
        time.sleep(0.3)

    def bets(self):
        """gambler s1/s2: only affordable bets select (the rest greyed), flips pay what the
        result line says, Reshuffle clears the table; a flip over your gold is refused."""
        self.set_gold(5000)
        u = self.gl("use", "hwp_gambler")
        time.sleep(0.5)
        self.flag("bets_open", u.get("ok"), str(u.get("window")))
        en = [self.widget(f"bet-btn-{i}").get("enabled") for i in range(5)]
        self.flag("bets_affordable_enabled", en == [True, True, False, False, False], f"5000 gold: {en}")
        s0 = self.widget("selected-bet").get("text", "")
        self.gl("press", "bet-btn-3")
        time.sleep(0.3)
        s1 = self.widget("selected-bet").get("text", "")
        self.gl("press", "bet-btn-1")
        time.sleep(0.3)
        s2 = self.widget("selected-bet").get("text", "")
        self.flag("bets_unaffordable_not_selected", s1 == s0, f"{s0!r} -> {s1!r}")
        self.flag("bets_affordable_selected", s2.startswith("1K") or "1,000" in s2, s2)
        flips, good, drew, reset = [], True, True, True
        for _ in range(4):
            g0 = self.gold()
            # the press and a widget dump in one frame: the cards are out, face down, before
            # the 0.4 s flight ends (a dump of its own comes too late to see it)
            rs = self.g.gl_multi([["press", "play-btn"], ["widgets", 8]])
            nodes = [n for r in rs[1].get("roots", []) for n in r.get("nodes", [])]
            card = next((n.get("visible") for n in nodes if n.get("id") == "player-card-sprite"), None)
            mid = "Drawing" if card else ""
            end = time.time() + 6
            txt = mid
            while time.time() < end:
                time.sleep(0.3)
                txt = self.widget("result-text").get("text", "")
                if "Gold" in txt or "tie" in txt.lower():
                    break
            d = self.gold() - g0
            m = re.search(r"([+-])(\d[\d,]*) Gold", txt)
            want = 0 if not m else int(m.group(2).replace(",", "")) * (1 if m.group(1) == "+" else -1)
            if not m and "tie" not in txt.lower():
                good = False
            good = good and d == want
            drew = drew and "Drawing" in mid and card is True
            shown = self.widget("player-card-sprite").get("visible")
            self.gl("press", "play-btn")  # Reshuffle
            time.sleep(0.4)
            after = self.widget("result-text").get("text", "")
            hidden = self.widget("player-card-sprite").get("visible")
            reset = reset and "Place your bet" in after and hidden is False and shown is True
            flips.append(f"{mid[:14]!r}->{txt.strip()[-24:]!r} d{d}")
        self.flag("bets_flip_animates", drew, "; ".join(flips))
        self.flag("bets_gold_matches_result", good, "; ".join(flips))
        self.flag("bets_reshuffle_resets", reset)
        # the selected 1K bet with only 500 gold: still lit (selected), the flip is refused
        self.set_gold(1500)
        self.gl("press", "bet-btn-1")
        time.sleep(0.2)
        self.set_gold(500)
        g0 = self.gold()
        self.gl("press", "play-btn")
        time.sleep(0.8)
        msg = self.widget("result-text").get("text", "")
        en = [self.widget(f"bet-btn-{i}").get("enabled") for i in range(5)]
        self.flag("bets_poor_flip_refused", self.gold() == g0 and "Not enough gold" in msg, f"{msg!r}, buttons {en}")
        self.g.key("escape")
        time.sleep(0.4)

    def npc(self, name, unit):
        """The fixture's town is small (no farm fields, no pet shop house): when the NPC is
        missing it is spawned beside the player, and its own shop window is used."""
        if self.gl("near", 8000, name).get("units"):
            return
        self.gl("spawn", unit, 40, 0)
        time.sleep(0.6)
        self.notes.append(f"{name}: not in this town, spawned beside the player")

    def farm_say(self, mark):
        return re.findall(r"\[HWP:farming\] (?:say|error): (.*)", self.g.read_log()[mark:])

    def farm(self):
        """farming s2/s3/s5 in the fixture town's layout (no farm fields: soil patches by the
        pet bowl). The can, a seed, planting, watering twice, the well."""
        self.hwp("set farm.debug 1")
        st = self.hwp("farm", 0.5, until="Farm:")
        self.notes.append("farm status: " + " / ".join(re.findall(r"\[HWP\] (Farm: .*|.*Watering.*|No watering.*)", st))[:300])
        self.set_gold(5000)
        mark = len(self.g.read_log())
        self.gl("use", "farm_well")
        time.sleep(0.6)
        said = self.farm_say(mark)
        self.flag("well_no_can", any("need a watering can" in s for s in said), str(said))
        self.npc("npc_misc_farmer_man", "actors/npcs/town/npc_misc_farmer_man.unit")
        u = self.gl("use", "npc_misc_farmer_man")
        time.sleep(0.5)
        self.flag("farmer_open", u.get("ok"), str(u.get("window")))
        st0 = self.widget("state").get("text", "")
        g0 = self.gold()
        mark = len(self.g.read_log())
        self.gl("press", "row-0")
        time.sleep(0.5)
        g1 = self.gold()
        st1 = self.widget("state").get("text", "")
        self.gl("press", "row-1")  # the first seed: cabbage
        time.sleep(0.5)
        g2 = self.gold()
        said = self.farm_say(mark)
        self.g.key("escape")
        time.sleep(0.4)
        self.flag("can_bought", g0 - g1 == 200 and "4/4" in st1, f"{st0!r} -> {st1!r}, gold {g0} -> {g1}")
        self.flag("seed_bought", g1 - g2 == 20 and any("Cabbage seed" in s for s in said), f"gold {g1} -> {g2}, {said}")
        # plant on the first plot: stand on it, use it, pick the seed row
        plots = self.gl("near", 4000, "farm_plot").get("units") or []
        self.flag("plots_found", bool(plots), f"{len(plots)} plot units")
        if not plots:
            return
        p0 = plots[0]
        self.gl("teleport", p0["x"], p0["y"] + 4)
        time.sleep(0.4)
        v0 = re.findall(r"visuals (\d+)", self.hwp("farm units", 0.4, until="visuals"))
        self.gl("use", "farm_plot")
        time.sleep(0.5)
        state = self.widget("state").get("text", "")
        self.gl("press", "row-0")
        time.sleep(0.8)
        top = self.gl("state").get("window")
        st = self.hwp("farm", 0.5, until="Farm:")
        v1 = re.findall(r"visuals (\d+)", self.hwp("farm units", 0.4, until="visuals"))
        planted = re.findall(r"Planted: (.*)", st)
        self.flag("planted", bool(planted) and "Cabbage" in planted[-1] and "Empty soil" in state,
                  f"window {state!r}, then {top}; planted {planted[-1:]}")
        self.flag("sprouts_shown", bool(v0 and v1) and int(v1[-1]) > int(v0[-1]), f"visuals {v0[-1:]} -> {v1[-1:]}")
        # water: the can goes 4 -> 3, wet soil appears; again: already watered (the window says why)
        mark = len(self.g.read_log())
        self.gl("use", "farm_plot")
        time.sleep(0.8)
        st = self.hwp("farm", 0.5, until="Farm:")
        v2 = re.findall(r"visuals (\d+)", self.hwp("farm units", 0.4, until="visuals"))
        said = self.farm_say(mark)
        pl = re.findall(r"Planted: (.*)", st)
        self.flag("watered", "3/4 water" in st and "watered" in (pl or [""])[-1], f"{said}; {pl[-1:]}")
        self.flag("wet_soil_shown", bool(v1 and v2) and int(v2[-1]) > int(v1[-1]), f"visuals {v1[-1:]} -> {v2[-1:]}")
        mark = len(self.g.read_log())
        self.gl("use", "farm_plot")
        time.sleep(0.8)
        msg = self.widget("message").get("text", "")
        said = self.farm_say(mark)
        self.g.key("escape")
        time.sleep(0.3)
        self.flag("already_watered", "Already watered" in msg, f"{msg!r} {said}")
        # the well fills the can back up; hwp farm well moves it here
        mark = len(self.g.read_log())
        self.gl("use", "farm_well")
        time.sleep(0.6)
        st = self.hwp("farm", 0.5, until="Farm:")
        said = self.farm_say(mark)
        self.flag("well_refills", "4/4 water" in st and any("filled" in s for s in said), str(said))
        pl = self.gl("state").get("player", {})
        self.gl("teleport", pl.get("x", 0) + 150, pl.get("y", 0))
        time.sleep(0.3)
        r = self.hwp("farm well", 0.6, until="well moved")
        w = self.gl("near", 60, "farm_well").get("units") or []
        self.flag("well_moved", "well moved" in r and bool(w), f"{re.findall(r'well moved[^|]*', r)[-1:]}, near {w[:1]}")
        self.hwp("farm well reset", 0.4)

    def petshop(self):
        """pets s1: the Pet Shop lists the HoH1 pets with icons; buying one puts it out."""
        self.set_gold(60000)
        self.npc("npc_pets", "actors/npcs/town/npc_pets.unit")
        u = self.gl("use", "npc_pets")
        time.sleep(0.6)
        shop = self.gl("shop")
        items = shop.get("items") or []
        hoh1 = ["imp", "scarab", "beetle", "ladybug", "raven", "magpie", "parrot", "toucan", "cat", "dog",
                "collie", "corgi", "hound", "wyrm", "squire", "flame"]
        hits = [i for i, it in enumerate(items) if any(w in it.get("title", "").lower() for w in hoh1)]
        self.flag("petshop_open", u.get("ok") and bool(items), f"{u.get('window')}, {len(items)} entries")
        self.flag("petshop_hoh1_listed", len(hits) >= 15 and all(items[i].get("icon") for i in hits),
                  f"{len(hits)} HoH1-looking: " + ", ".join(items[i].get("title", "") for i in hits[:24]))
        pick = next((i for i in hits if "imp" in items[i].get("title", "").lower()), hits[0] if hits else None)
        if pick is None:
            self.g.key("escape")
            return
        price = items[pick]["gold"]
        g0 = self.gold()
        self.gl("shop", "buy", pick)
        time.sleep(1.5)
        if self.gl("state").get("window"):
            self.g.key("escape")
            time.sleep(0.3)
        g1 = self.gold()
        st = self.hwp("pet", 0.5, until="level")
        name = items[pick].get("title", "")
        out = self.gl("near", 250, "pets/").get("units") or []
        pet = [x for x in out if "pets/" in x.get("name", "")]
        self.flag("petshop_bought", g0 - g1 == price and price > 0, f"{name}: {g0} -> {g1}, price {price}")
        self.flag("pet_out", bool(pet) and name.split()[0].lower() in st.lower(), f"{pet[:1]}; {st.strip()[-160:]}")

    def wares_count(self, ware):
        m = re.findall(ware + r"\D{0,4}(\d+)|(\d+)x? " + ware, self.hwp("wares", 0.4, until="Bet tokens"))
        return m[-1] if m else None

    def petbowl(self):
        """pets s3/s6: debug XP gives a level-up line and points at the bowl; feeding a
        cabbage there uses it and adds XP."""
        self.hwp("set pets.debug true")
        r = self.hwp("pet xp 500", 0.8, until="reached level")
        line = re.findall(r"\[HWP\] (.*reached level.*)", r)
        self.flag("pet_levelup_line", bool(line), line[-1] if line else r.strip()[-160:])
        # a cabbage: a wild plot's harvest
        self.hwp("set farm.debug 1")
        self.hwp("farm wild cabbage", 1.5)
        self.gl("use", "wild/cabbage")
        time.sleep(0.8)
        n0 = self.wares_count("Cabbage")
        u = self.gl("use", "pet_bowl")
        time.sleep(0.6)
        pts = self.widget("points").get("text", "")
        xp0 = self.widget("xp").get("text", "")
        self.flag("bowl_points", u.get("ok") and re.search(r"Skill points: [1-9]", pts) is not None,
                  f"{u.get('window')}: {pts!r} {xp0!r}")
        # rows: 7 skills, then the feed rows (the cabbage only), then the pickup toggles
        self.gl("press", "row-7")
        time.sleep(0.6)
        xp1 = self.widget("xp").get("text", "")
        msg = self.widget("message").get("text", "")
        self.g.key("escape")
        time.sleep(0.3)
        n1 = self.wares_count("Cabbage")
        a = re.findall(r"(\d+) / ", xp0)
        b = re.findall(r"(\d+) / ", xp1)
        self.flag("bowl_feed", bool(a and b) and int(b[0]) > int(a[0]) and n0 != n1,
                  f"{xp0!r} -> {xp1!r}, {msg!r}, cabbages {n0} -> {n1}")

    def gold_drop(self, dist=150, amount=25):
        """A real drop (DropMaterial: an amount) `dist` px away, past the player's own reach
        and inside a pet's pickup range (200-300 from the owner), on a spot the pathfinder
        reaches (a drop behind a wall can't be fetched)."""
        if not hasattr(self, "drop_at"):
            self.drop_at = (dist, 0)
            for a in [45, 135, 225, 315, 90, 270, 0, 180]:
                if a in getattr(self, "bad_dirs", set()):
                    continue
                import math
                dx, dy = round(dist * math.cos(math.radians(a))), round(dist * math.sin(math.radians(a)))
                pl = self.gl("state").get("player", {})
                pf = self.gl("pathfind", pl.get("x", 0) + dx, pl.get("y", 0) + dy)
                # a near-straight path: a detour round a wall is past the pet's leash
                if pf.get("ok") and pf.get("nodes", 0) > 0 and pf.get("length", 1e9) <= dist * 1.25:
                    self.drop_at = (dx, dy)
                    self.drop_dir = a
                    break
        r = self.gl("drop", "gold", amount, *self.drop_at)
        time.sleep(0.3)
        self.dropped = [u for u in getattr(self, "dropped", []) + [r.get("unit")] if u is not None]
        return len(self.dropped)

    def gold_left(self, wait=6):
        """How many of our drops are still on the floor after up to `wait` s (the floor's
        own gold doesn't count)."""
        end = time.time() + wait
        n = -1
        while time.time() < end:
            ids = {u["unit"] for u in self.gl("near", 1000, "materials/gold").get("units") or []}
            self.dropped = [u for u in self.dropped if u in ids]
            n = len(self.dropped)
            if n == 0:
                break
            time.sleep(0.5)
        return n

    def petgold(self):
        """pets s1/s7 in a run: the pet picks gold up; with Gold off it leaves it; on again it
        picks it up."""
        self.start_floor(0)
        self.gl("cull")
        time.sleep(1.5)
        g0 = self.gold()
        # a spot the pathfinder reaches can still sit past a ledge the pet won't cross:
        # try the next direction when a drop isn't fetched
        for _ in range(3):
            n = self.gold_drop()
            left = self.gold_left(8)
            if left == 0 or not hasattr(self, "drop_dir"):
                break
            self.bad_dirs = getattr(self, "bad_dirs", set()) | {self.drop_dir}
            del self.drop_at
            self.dropped = []
        g1 = self.gold()
        pet = self.gl("near", 800, "pets/").get("units") or []
        self.flag("pet_picks_gold", n > 0 and left == 0 and g1 > g0,
                  f"{n} drop(s) at {self.drop_at} -> {left} left, gold {g0} -> {g1}, pet {pet[:1]}")
        self.hwp("pet gold off", 0.5)
        n = self.gold_drop()
        trace = []
        for _ in range(8):
            ps = self.gl("near", 800, "pets/").get("units") or []
            trace.append([(round(x["x"]), round(x["y"]), x["unit"]) for x in ps])
            time.sleep(0.25)
        left = self.gold_left(4)
        g2 = self.gold()
        self.flag("pet_gold_off_ignores", n > 0 and left > 0 and g2 == g1,
                  f"{n} -> {left} left, gold {g1} -> {g2}; pets {trace}")
        self.hwp("pet gold on", 0.5)
        left = self.gold_left(8)
        g3 = self.gold()
        self.flag("pet_gold_on_picks", left == 0 and g3 > g2, f"{left} left, gold {g2} -> {g3}")
        # it follows a walk (a teleport takes the pet along): 2 s of stick toward the
        # reachable drop direction
        import math
        pl = self.gl("state").get("player", {})
        x0, y0 = pl.get("x", 0), pl.get("y", 0)
        dx, dy = self.drop_at
        k = math.hypot(dx, dy) or 1
        self.gl("input", 2500, round(dx / k, 3), round(dy / k, 3))
        time.sleep(4)
        pl = self.gl("state").get("player", {})
        walked = math.hypot(pl.get("x", 0) - x0, pl.get("y", 0) - y0)
        near = self.gl("near", 800, "pets/").get("units") or []
        self.flag("pet_follows", walked > 60 and bool(near) and near[0]["dist"] < 90,
                  f"walked {walked:.0f} px; pet {near[0]['dist'] if near else None} px from the player after")

    def goldpet(self):
        """goldpet s1 (town half): the vendor in the Hunter's Lodge sells tier 1 for 10,000;
        tier 2 needs Lodge tier 2."""
        b = self.gl("build", "hunters_cabin")
        self.gl("townrefresh")
        time.sleep(3)
        v = self.gl("near", 8000, "hwp_pet_vendor").get("units") or []
        self.flag("vendor_spawned", bool(v), f"build {b.get('ok')}, vendor {v[:1]}")
        self.set_gold(9000)
        self.gl("use", "hwp_pet_vendor")
        time.sleep(0.5)
        req = self.widget("tier1-req").get("text", "")
        g0 = self.gold()
        self.gl("press", "buy-tier1")
        time.sleep(0.5)
        self.flag("goldpet_poor_refused", self.gold() == g0 and req != "", f"{req!r}, gold {g0} -> {self.gold()}")
        self.g.key("escape")
        time.sleep(0.3)
        self.set_gold(10000)
        self.gl("use", "hwp_pet_vendor")
        time.sleep(0.5)
        btn = self.widget("buy-tier1")
        self.gl("press", "buy-tier1")
        time.sleep(1.5)
        g1 = self.gold()
        if self.gl("state").get("window"):
            self.g.key("escape")
            time.sleep(0.3)
        cat = self.gl("near", 300, "hwp_gold_collector_pet").get("units") or []
        self.flag("goldpet_bought", g1 == 0 and bool(cat), f"button {btn}, gold 10000 -> {g1}, cat {cat[:1]}")
        self.set_gold(60000)
        self.gl("use", "hwp_pet_vendor")
        time.sleep(0.5)
        t2 = self.widget("buy-tier2")
        req2 = self.widget("tier2-req").get("text", "")
        g2 = self.gold()
        self.gl("press", "buy-tier2")
        time.sleep(0.5)
        self.flag("goldpet_tier2_gated", self.gold() == g2 and "odge" in req2,
                  f"{req2!r}, button {t2}, gold {g2} -> {self.gold()}")
        self.g.key("escape")
        time.sleep(0.3)

    def goldpet_run(self):
        """goldpet s1 (run half) and s3 (back after a floor change)."""
        self.start_floor(0)
        self.gl("cull")
        time.sleep(2)
        cat = self.gl("near", 400, "hwp_gold_collector_pet").get("units") or []
        g0 = self.gold()
        n = self.gold_drop(130)
        left = self.gold_left(8)
        g1 = self.gold()
        self.flag("goldpet_in_run", bool(cat), str(cat[:1]))
        self.flag("goldpet_picks_gold", n > 0 and left == 0 and g1 > g0, f"{n} -> {left} left, gold {g0} -> {g1}")
        self.start_floor(1)
        time.sleep(2)
        cat = self.gl("near", 400, "hwp_gold_collector_pet").get("units") or []
        self.flag("goldpet_after_floor_change", bool(cat), str(cat[:1]))

    def portal(self):
        """campaign s1 / hoh1floors s1: the town portal (a minimap sprite in its unit) offers
        The Forsaken Tower (18 floors) and the mission on the HoH1 floors once the story
        intro is done; before that it says it's dormant (no script exception)."""
        p = self.gl("near", 8000, "forsaken_portal").get("units") or []
        self.flag("portal_in_town", bool(p), f"{p[:1]}")
        if not p:
            return
        self.gl("teleport", p[0]["x"], p[0]["y"] + 50)
        time.sleep(1)
        mark = len(self.g.read_log())
        u = self.gl("use", "forsaken_portal")
        time.sleep(0.8)
        log = self.g.read_log()[mark:]
        st = self.gl("state")
        self.flag("portal_locked_says_why", u.get("ok") and not st.get("window") and "no mission for this character" in log
                  and "Script exception" not in log, f"use {u}, window {st.get('window')!r}")
        self.g.console("cht_set_flag mission_story_intro_find_npcs 1 0")
        time.sleep(0.5)
        u = self.gl("use", "forsaken_portal")
        time.sleep(0.8)
        items = self.gl("shop").get("items") or []
        titles = [(it.get("title", ""), it.get("sub", "")) for it in items]
        self.flag("portal_offers_tower", u.get("ok") and any("forsaken tower" in t.lower() and "18" in sub for t, sub in titles),
                  f"{u.get('window')}: {titles}")
        self.flag("portal_offers_hoh1", len(items) >= 2, f"{len(items)} missions")
        if u.get("window"):
            self.g.key("escape")
            time.sleep(0.5)

    def waverank(self):
        """wavemode s5: [hwp wave rank 5], then start at the statue: the arena is NG+5."""
        self.set_gold(60000)
        self.hwp("wave rank 5", 0.5)
        st = self.gl("near", 8000, "wave_statue").get("units") or []
        if st:
            self.gl("teleport", st[0]["x"], st[0]["y"] + 50)
            time.sleep(1)
        u = self.gl("use", "wave_statue")
        time.sleep(0.8)
        items = self.gl("shop").get("items") or []
        self.flag("statue_open", u.get("ok") and bool(items), f"{u.get('window')}: {[(i.get('title'), i.get('sub')) for i in items]}")
        if not items:
            return
        self.gl("shop", "buy", 0)
        time.sleep(1.5)
        w = self.gl("state").get("window")
        ngp_text = self.widget("ngp-text").get("text")
        self.flag("statue_loadout", "Loadout" in (w or ""), f"window {w}, ngp-text {ngp_text!r}")
        self.gl("func", "play")
        ok = self.wait_phase("mission")
        time.sleep(3)
        stt = self.gl("state")
        self.flag("wave_ngp5", ok and abs(stt.get("ngp", -1) - 5) < 0.01,
                  f"phase {stt.get('phase')}, level {stt.get('level')}, ngp {stt.get('ngp')}")


def run(p, sections="gambler,sell,merchant,traps,full_bag", **_):
    c = Checks(p)
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
