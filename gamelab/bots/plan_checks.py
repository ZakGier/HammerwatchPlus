"""Test-plan checks that need arithmetic between game reads (gold before and after, an
item's roll before and after), which a scenario's expect can't do. Each section returns
its own flags; the scenario asserts them. Everything goes through gl verbs, HWP console
commands and the game's own windows (gl use / press / shop), never real input.

Sections: gambler (reroll gold/tokens/refusals), sell (wares at the Gambler), merchant
(bag slot), traps (pirate fish traps), full_bag (a catch with a full bag), mission (start
Bandit Keep), chests (silver key loot, ace chest legendary and epic), swap (weapon sets
with the X key)."""
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

    def widget(self, wid):
        """The first open widget with this id (the widgets dump: type, visible, text for
        TextWidgets, enabled for buttons), or {}. A button's own caption is a BitmapString
        the dump can't read back."""
        for root in self.gl("widgets", 12).get("roots", []):
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
        near = self.gl("near", 60)
        self.flag("full_bag_feet", "Your bag is full" in got, got.strip()[-200:])
        self.flag("full_bag_fish_on_ground", near.get("count", 0) > 0, json.dumps(near.get("units", [])[:3]))
        self.hwp("sell")

    def mission(self):
        r = self.gl("mission", "bandit_keep", 0)
        self.flag("mission_started", r.get("ok") and self.wait_phase("mission"))
        time.sleep(3)
        pl = self.gl("state").get("player", {})
        self.start = (pl.get("x", 0.0), pl.get("y", 0.0))
        self.used = []

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
