"""Test-plan checks for the HUD and visual group (bufftips, colors, core map icons,
deathrecap), run by gamelab/scenarios/plan-ui-a.json and plan-ui-b.json.

Hover: posted mouse messages never reach the game, so `gl mouse` (Verbs_ui.as) pins the
game mode's cursor (BaseGameMode.m_mice[0], what HUD components read) on a buff bar icon.
The tooltip itself is a BitmapString inside bufftips' HUD component, so it is measured in
screenshots: the same pinned cursor with `bufftips.enabled` false and true, the difference
in the box above and right of the cursor where bufftips draws it, its "Ns left" header's
orange (1, 0.65, 0.05) and a debuff name's red (\\cff6666) counted among the new pixels.
Two "off" shots give the background's own change (torches, the player's idle) as a noise
floor. The buff bar's data (name, description, ms left, stacks) comes from `gl buffbar`.

Sections: bufftips_timed (s1), bufftips_debuff (s2), bufftips_crown (s3), bufftips_menu (s4),
mapicons (core s9), colors_tint (colors s1), colors_option (colors s5), hazard_death
(deathrecap s2)."""
import re
import time

from gamelab.bots.plan_checks import Checks as Base

SHRINE = "tweak/buffs/shrine_buffs.sval:damage"      # 120 s, hud icon (Shrine.as:157 applies it)
SLOW = "tweak/buffs/status_effects.sval:slow"        # a vanilla debuff, no hud icon
STACKS = "players/paladin/stacks_paladin.sval:inner_flame"
MORALE = "tweak/hwp/buffs_pets.sval:hwp_morale_1"
SHIELD_WALL = "tweak/hwp/buffs_classes.sval:hwp_glad_shield_wall"
CROWN_KEY = ".hwp.legacy.buff"

# the two dyes the check spawns (DyeBucket units; the level may hold others of other types)
DYES = ["items/dyes/dye_bucket_cloth_common.unit", "items/consumables/dye_pot.unit"]
DYE_MARK = "doodads/hwp/map_icon_dye.unit"

SENTRY = "actors/undead/guard/guard_sentry.unit"
BEAM = "doodads/traps/projectiles/beam_fire.unit"            # BeamProjectile (traps only)
TRAP_RAY = "doodads/traps/projectiles/arrow.unit"            # RayProjectile
HYDRA_RAY = "players/wizard/projectiles/hydra_breath_fire.unit"  # a player RayProjectile
CLOUD = "doodads/traps/misc/mushroom_poison_big_area.unit"   # DangerArea, no owner, 10 poison/s
FLOOR_FIRE = "doodads/traps/floors/floor_fire.unit"          # ProximityTrap, no owner

# mods/colors ColorsModule.as InitPresets: (enemy, friendly)
PRESETS = {
    "contrast": ((1.0, 0.35, 0.35), (0.45, 0.8, 1.0)),
    "deuteranopia": ((1.0, 0.6, 0.1), (0.3, 0.6, 1.0)),
    "protanopia": ((1.0, 0.85, 0.2), (0.35, 0.55, 1.0)),
    "tritanopia": ((1.0, 0.3, 0.3), (0.2, 0.9, 0.8)),
}


def orange(p):
    r, g, b = p
    return r >= 200 and 115 <= g <= 210 and b <= 90


def red(p):
    r, g, b = p
    return r >= 200 and 60 <= g <= 150 and 60 <= b <= 150 and abs(g - b) <= 30


def light(p):
    return min(p) >= 170


def near_color(c, want, tol=0.03):
    return all(abs(c.get(k, -1) - w) <= tol for k, w in zip("rgb", want))


class Checks(Base):
    # --- plumbing
    def cvar(self, name):
        return self.gl("cvars", name).get("cvars", {}).get(name)

    def god(self, on):
        if bool(self.cvar("cht_god")) != on:
            self.hwp("god", 0.4)

    def log_since(self, mark):
        return self.g.read_log()[mark:]

    def ensure_run(self, cls, name):
        """A fresh character in Bandit Keep floor 0 with the floor cleared, once per scenario
        (a later bot step finds the run still going and keeps it)."""
        st = self.gl("state")
        if st.get("phase") == "mission" and st.get("player", {}).get("name") == name:
            return True
        self.gl("char", cls, name)
        ok = self.wait_phase("town", 60)
        time.sleep(2)
        # a hero above level 1, for the Title Bonuses (legacy README Testing 2)
        self.hwp("levelup 4", 1.0, until="level")
        ok = self.start_floor(0) and ok
        self.god(True)
        self.gl("kill", 6000, "tag:enemy")
        time.sleep(1)
        self.flag(f"{name}_run", ok, f"phase {self.gl('state').get('phase')}")
        return ok

    def bar(self):
        return self.gl("buffbar")

    def icon(self, bar, pred):
        for e in bar.get("icons") or []:
            if e.get("shown") and pred(e):
                return e
        return None

    # --- screenshots
    def snap(self, name):
        from PIL import Image
        path = self.g.shot(name)
        return Image.open(path).convert("RGB") if path else None

    def tip_box(self, img, m, ic):
        """Pixel box where bufftips draws the tooltip for the cursor m (gl mouse reply): above
        and right of the cursor (BuffTips.as Draw: m_mouse + (8, -size.y - 6)), header over it,
        stopping above the hovered icon (its timer changes on its own)."""
        kx = img.width / max(m.get("wndW", img.width), 1)
        ky = img.height / max(m.get("wndH", img.height), 1)
        mx, my = m.get("mx", 0), m.get("my", 0)
        half = (ic.get("h", 14) if ic else 14) / 2
        x0, x1 = max(0, mx + 4), min(m.get("wndW", 640), mx + 330)
        y0, y1 = max(0, my - 240), max(1, my - half - 2)
        return (int(x0 * kx), int(y0 * ky), int(x1 * kx), int(y1 * ky)), kx * ky

    @staticmethod
    def changed(a, b, box):
        """Pixels that changed between a and b in box (any channel by more than 24: a dark
        panel over a dark floor moves little in luminance), eroded 3x3 (a drawn panel
        survives, single-pixel shimmer does not): (count, bounding box or None)."""
        from PIL import ImageChops, ImageFilter
        r, g, bl = ImageChops.difference(a.crop(box), b.crop(box)).split()
        d = ImageChops.lighter(ImageChops.lighter(r, g), bl).point(lambda v: 255 if v > 24 else 0)
        d = d.filter(ImageFilter.MinFilter(3))
        n = sum(1 for v in d.getdata() if v)
        return n, d.getbbox()

    @staticmethod
    def new_px(on, off, box, pred):
        """Pixels in box that match pred in `on` and not in `off`."""
        a, b = list(on.crop(box).getdata()), list(off.crop(box).getdata())
        return sum(1 for p, q in zip(a, b) if pred(p) and not pred(q))

    @staticmethod
    def flip_px(a, b, box, pred):
        """Pixels in box that match pred in exactly one of a, b (a text that changed)."""
        x, y = list(a.crop(box).getdata()), list(b.crop(box).getdata())
        return sum(1 for p, q in zip(x, y) if pred(p) != pred(q))

    @staticmethod
    def tip_frame(on, off, box):
        """The tooltip's top border in box: the first row whose new orange run (orange in `on`,
        not in `off`) is at least 60% of the longest. (x0, top, x1) or None. The frame itself
        is orange, so orange counts over the whole box say nothing about the header."""
        rows = []
        for y in range(box[1], box[3]):
            xs = [x for x in range(box[0], box[2]) if orange(on.getpixel((x, y))) and not orange(off.getpixel((x, y)))]
            rows.append((y, xs))
        best = max((len(xs) for _, xs in rows), default=0)
        if best < 30:
            return None
        y, xs = next((y, xs) for y, xs in rows if len(xs) >= 0.6 * best)
        return min(xs), y, max(xs)

    @staticmethod
    def header_strip(fr, above, below):
        """Rows `above` over to `below` under the top border, the middle 60% of its width (the
        corner ornaments left out): where ToolTip.Draw puts the header (pos.y - 7, centred)."""
        x0, top, x1 = fr
        w = x1 - x0
        return (x0 + int(w * 0.2), top - above, x1 - int(w * 0.2) + 1, top + below + 1)

    @staticmethod
    def moved_px(a, b, box):
        """Pixels in box that moved by more than 40 in some channel between a and b, uneroded
        (a digit that changed is a few 1 px strokes)."""
        from PIL import ImageChops
        r, g, bl = ImageChops.difference(a.crop(box), b.crop(box)).split()
        d = ImageChops.lighter(ImageChops.lighter(r, g), bl)
        return sum(1 for v in d.getdata() if v > 40)

    def tip_measure(self, tag, ic, countdown=False):
        """The cursor stays pinned; two shots with bufftips off, then on (two more 2 s apart
        with countdown). Measures in the tooltip box: changed (off vs on, eroded), noise (off vs
        off), new orange / red / light pixels; over the box's top border (tip_frame): header,
        the new orange pixels in the rows above it (bg_header the same between the off shots),
        and with countdown tick, the pixels of the header line that moved between the on shots
        (bg_tick between the off shots)."""
        m = self.gl("mouse")
        self.hwp("set bufftips.enabled false", 0.4, until="bufftips.enabled = false")
        time.sleep(0.5)
        off1 = self.snap(f"ui-{tag}-off1")
        time.sleep(0.4)
        off2 = self.snap(f"ui-{tag}-off2")
        self.hwp("set bufftips.enabled true", 0.4, until="bufftips.enabled = true")
        time.sleep(0.5)
        on1 = self.snap(f"ui-{tag}-on")
        on2 = None
        if countdown:
            time.sleep(2.0)
            on2 = self.snap(f"ui-{tag}-on2")
        if not (off1 and off2 and on1):
            return {"ok": False}
        box, area = self.tip_box(on1, m, ic)
        ch, bbox = self.changed(off1, on1, box)
        noise, _ = self.changed(off1, off2, box)
        r = {"ok": True, "box": box, "changed": ch, "noise": noise, "bbox": bbox,
             "shown": ch >= max(250 * area, 4 * noise + 60),
             "orange": self.new_px(on1, off1, box, orange), "red": self.new_px(on1, off1, box, red),
             "light": self.new_px(on1, off1, box, light),
             "bg_orange": self.flip_px(off1, off2, box, orange), "bg_red": self.flip_px(off1, off2, box, red),
             "bg_light": self.flip_px(off1, off2, box, light)}
        fr = self.tip_frame(on1, off1, box)
        r["frame"] = fr
        if fr:
            above = self.header_strip(fr, 4, -1)
            r["header"] = self.new_px(on1, off1, above, orange)
            r["bg_header"] = self.new_px(off2, off1, above, orange)
            if on2 is not None:
                line = self.header_strip(fr, 4, 4)
                r["tick"] = self.moved_px(on1, on2, line)
                r["bg_tick"] = self.moved_px(off1, off2, line)
        return r

    @staticmethod
    def fmt(r):
        keys = ("changed", "noise", "orange", "red", "light", "bg_orange", "bg_red", "bg_light", "bbox",
                "frame", "header", "bg_header", "tick", "bg_tick")
        return ", ".join(f"{k} {r[k]}" for k in keys if k in r)

    def hover(self, match):
        r = self.gl("mouse", "buff", match)
        time.sleep(0.3)
        m = self.gl("mouse")
        ok = bool(r.get("ok")) and abs(m.get("mx", -9) - m.get("x", 0)) < 1 and abs(m.get("my", -9) - m.get("y", 0)) < 1
        return ok, m

    # --- bufftips s1: a shrine buff, hovered: "Ns left" over name and description, counting down
    def bufftips_timed(self):
        if not self.ensure_run("paladin", "LabTips"):
            return
        g = self.gl("givebuff", SHRINE, -1)
        time.sleep(0.5)
        b0 = self.bar()
        self.flag("tips_hud", "HWPBuffTipsHUD" in (b0.get("components") or []), str(b0.get("components")))
        ic = self.icon(b0, lambda e: e.get("key") == ".blessing.damage.name")
        self.flag("shrine_icon", bool(g.get("applied")) and ic is not None and ic.get("max", 0) > 0,
                  f"applied {g.get('applied')}, icon {ic}")
        if not ic:
            return
        ok, m = self.hover(".blessing.damage")
        self.flag("cursor_pinned", ok, f"pin {m.get('x')},{m.get('y')} now {m.get('mx')},{m.get('my')}, "
                  f"window {m.get('wndW')}x{m.get('wndH')} scale {m.get('scale')}")
        r = self.tip_measure("shrine", ic, countdown=True)
        self.notes.append("shrine tip: " + self.fmt(r))
        self.flag("tip_shown", r.get("shown"), self.fmt(r))
        self.flag("tip_header_line", r.get("header", 0) >= max(5, 3 * r.get("bg_header", 0) + 3)
                  and r.get("red", 99) <= max(5, 2 * r.get("bg_red", 0) + 2),
                  f"header px over the border {r.get('header')} (bg {r.get('bg_header')}), frame {r.get('frame')}, red {r.get('red')}")
        self.flag("tip_name_desc", r.get("light", 0) >= max(30, 3 * r.get("bg_light", 0) + 10)
                  and bool(ic.get("name")) and bool(ic.get("desc")),
                  f"light px {r.get('light')}; name {ic.get('name')!r}, desc {ic.get('desc')!r}")
        # the countdown: the header line changed between the two "on" shots (2 s apart), beyond
        # what it did between the "off" ones; the buff's own ms left went down
        b1 = self.bar()
        ic1 = self.icon(b1, lambda e: e.get("key") == ".blessing.damage.name") or {}
        secs0, secs1 = -(-ic.get("left", 0) // 1000), -(-ic1.get("left", 0) // 1000)
        self.flag("tip_counts_down", r.get("tick", 0) >= max(3, 2 * r.get("bg_tick", 0) + 2)
                  and secs0 - secs1 >= 2,
                  f"header line px changed {r.get('tick')} (bg {r.get('bg_tick')}), secs {secs0} -> {secs1}")
        self.snap("ui-shrine-tip")

    # --- bufftips s2: a debuff's name is red; a stacking buff says "x N"
    def bufftips_debuff(self):
        if not self.ensure_run("paladin", "LabTips"):
            return
        g = self.gl("givebuff", SLOW, 20000)
        time.sleep(0.5)
        b = self.bar()
        vanilla = self.icon(b, lambda e: e.get("debuff"))
        # the plan has a vanilla debuff (slow, poison) in the buff bar to hover, but no vanilla or
        # HWP debuff def has a "hud" sprite (the only hud arrays, shrine_buffs.sval and
        # players/*/stacks_*.sval, are all debuff false) and HUD.ShowBuffIcon skips defs without
        # one: slow is applied, has no icon and none shows. Not bufftips dropping it.
        self.flag("vanilla_debuffs_have_no_icon", bool(g.get("applied")) and g.get("hud") is False and vanilla is None,
                  f"slow applied {g.get('applied')}, hud {g.get('hud')}, debuff icons {vanilla}")
        # bufftips' own red path, with a test-only copy of slow that has an icon
        g2 = self.gl("givebuff", SLOW, 20000, "icon")
        time.sleep(0.5)
        b = self.bar()
        ic = self.icon(b, lambda e: e.get("debuff"))
        self.flag("debuff_icon", bool(g2.get("applied")) and ic is not None, f"{g2} -> {ic}")
        if ic:
            ok, m = self.hover(str(ic["i"]))
            r = self.tip_measure("debuff", ic)
            self.notes.append("debuff tip: " + self.fmt(r) + f"; name {ic.get('name')!r}")
            self.flag("debuff_tip_shown", ok and r.get("shown"), self.fmt(r))
            self.flag("debuff_name_red", r.get("red", 0) >= max(6, 3 * r.get("bg_red", 0) + 4), f"new red px {r.get('red')}")
        # stacks: Inner Flame x3 (ActorBuffStacked.GetBuffIconCount = stacks)
        s = self.gl("givestacks", STACKS, 3)
        time.sleep(0.4)
        b = self.bar()
        st = self.icon(b, lambda e: e.get("kind") == "stacks")
        self.flag("stacks_count", st is not None and st.get("count") == 3,
                  f"givestacks {s}, icon {st}: the tooltip names it '{(st or {}).get('name')} x{(st or {}).get('count')}'")
        if st:
            ok, m = self.hover(str(st["i"]))
            r = self.tip_measure("stacks", st)
            self.notes.append("stacks tip: " + self.fmt(r))
            self.flag("stacks_tip_shown", ok and r.get("shown"), self.fmt(r))
        self.gl("mouse", "off")

    # --- bufftips s3: the crown (Title Bonuses) lists the bonuses, no countdown line
    def bufftips_crown(self):
        if not self.ensure_run("paladin", "LabTips"):
            return
        b = self.bar()
        ic = None
        for _ in range(6):
            ic = self.icon(b, lambda e: e.get("key") == CROWN_KEY)
            if ic:
                break
            time.sleep(1)
            b = self.bar()
        lines = [x for x in (ic or {}).get("desc", "").split("\n") if x.strip()]
        self.flag("crown_icon", ic is not None and ic.get("name") == "Title Bonuses",
                  f"icon {ic}")
        if not ic:
            return
        left, mx = ic.get("left", 0), ic.get("max", 0)
        secs = -(-left // 1000) if (0 < left < 3600000 and mx > 0) else 0
        self.flag("crown_lists_bonuses", len(lines) >= 1, f"{len(lines)} lines: {lines[:4]}")
        ok, m = self.hover(CROWN_KEY)
        r = self.tip_measure("crown", ic)
        self.notes.append("crown tip: " + self.fmt(r))
        self.flag("crown_tip_shown", ok and r.get("shown"), self.fmt(r))
        self.flag("crown_no_countdown", secs == 0 and r.get("frame") is not None
                  and r.get("header", 99) <= max(1, r.get("bg_header", 0)),
                  f"secs {secs} (left {left}, max {mx}), header px over the border {r.get('header')} "
                  f"(bg {r.get('bg_header')}), frame {r.get('frame')}")
        self.gl("mouse", "off")

    # --- bufftips s4: no buff tooltip over the character menu; Effects lists HWP buffs with text
    def bufftips_menu(self):
        if not self.ensure_run("paladin", "LabTips"):
            return
        self.gl("givebuff", SHRINE, -1)
        self.gl("givebuff", MORALE, 120000)
        self.gl("givebuff", SHIELD_WALL, 120000)
        time.sleep(0.5)
        b = self.bar()
        ic = self.icon(b, lambda e: e.get("key") == ".blessing.damage.name")
        ok, m = self.hover(".blessing.damage") if ic else (False, {})
        r = self.gl("menu", "mods", "effects-content", "effects-list")
        time.sleep(0.8)
        m2 = self.gl("mouse")
        texts = [t.strip() for t in r.get("texts", "").split(" | ")]
        self.notes.append(f"effects: {texts[:24]}")
        if ic:
            t = self.tip_measure("menu", ic)
            self.notes.append("menu tip: " + self.fmt(t))
            self.flag("menu_no_tip", ok and m2.get("menu") and t.get("ok")
                      and t.get("changed", 999) <= max(40, 2 * t.get("noise", 0))
                      and t.get("orange", 99) <= max(3, 2 * t.get("bg_orange", 0) + 2),
                      f"menu {m2.get('menu')}, " + self.fmt(t))
        else:
            self.flag("menu_no_tip", False, "no shrine icon to hover")

        def described(title):
            if title not in texts:
                return False, ""
            i = texts.index(title)
            d = texts[i + 1] if i + 1 < len(texts) else ""
            return bool(d) and d not in ("desc", "title") and d not in (".", title), d
        for flag, title in (("effects_title_bonuses", "Title Bonuses"), ("effects_morale", "Morale"),
                            ("effects_class_buff", "Shield Wall")):
            okd, d = described(title)
            self.flag(flag, r.get("ok") and okd, f"{title}: {d[:80]!r}")
        self.gl("mouse", "off")
        self.g.key("escape")
        time.sleep(0.6)
        if self.gl("state").get("window"):
            self.g.key("escape")
            time.sleep(0.5)

    # --- core s9: a dye pot on the floor has a map marker until picked up; mapicons.dyes 0 hides them
    def dye_state(self):
        r = self.gl("unitsof", *DYES, DYE_MARK)
        dyes = [u for f in DYES for u in (r.get(f) or {}).get("units", []) if not u.get("hidden")]
        marks = (r.get(DYE_MARK) or {}).get("units", [])
        return dyes, marks

    @staticmethod
    def marked(dye, marks):
        return any(abs(m["x"] - dye["x"]) < 1 and abs(m["y"] - dye["y"]) < 1 for m in marks)

    def mapicons(self):
        if not self.ensure_run("paladin", "LabTips"):
            return
        self.hwp("set mapicons.dyes 1", 0.4, until="mapicons.dyes = 1")
        a = self.gl("spawn", DYES[0], 70, 0)
        c = self.gl("spawn", DYES[1], -70, 0)
        time.sleep(2.5)
        dyes, marks = self.dye_state()
        ours = [d for d in dyes if d["unit"] in (a.get("unit"), c.get("unit"))]
        self.flag("dye_marker_shown", len(ours) == 2 and all(self.marked(d, marks) for d in ours),
                  f"{len(dyes)} dyes of these types, {len(marks)} markers in the level; "
                  f"ours {[(d['unit'], round(d['x']), round(d['y'])) for d in ours]}")
        pot = next((d for d in ours if d["unit"] == c.get("unit")), None)
        # pick the first up: stand next to it and walk over it
        target = next((d for d in ours if d["unit"] == a.get("unit")), None)
        if target:
            # walk over it first (teleport 20 left, hold right past it); if the walk misses it,
            # run the dye's own Collide handler with the player (gl pickup), as touching it does
            t = self.gl("teleport", target["x"] - 20, target["y"])
            time.sleep(0.3)
            self.gl("input", 900, 1, 0)
            time.sleep(1.5)
            p = self.gl("state").get("player") or {}
            walked = f"teleported to {t.get('x')},{t.get('y')}, walked to {p.get('x')},{p.get('y')}"
            dyes2, _ = self.dye_state()
            how = "walking"
            if any(d["unit"] == target["unit"] for d in dyes2):
                pk = self.gl("pickup", target["unit"])
                how = f"gl pickup ({pk})"
                time.sleep(1.5)
            dyes2, marks2 = self.dye_state()
            gone = all(d["unit"] != target["unit"] for d in dyes2)
            self.notes.append(f"dye pickup: {walked}; picked by {how}")
            self.flag("dye_marker_gone_on_pickup", gone and not self.marked(target, marks2)
                      and pot is not None and self.marked(pot, marks2),
                      f"dye picked {gone} by {how}; {len(marks) - len(marks2)} markers fewer, the pot's kept "
                      f"{pot is not None and self.marked(pot, marks2)}; {walked}")
        else:
            self.flag("dye_marker_gone_on_pickup", False, "the spawned dye is not there")
        self.hwp("set mapicons.dyes 0", 0.4, until="mapicons.dyes = 0")
        time.sleep(2.0)
        dyes3, marks3 = self.dye_state()
        self.flag("dye_markers_hidden_setting", len(marks3) == 0 and pot is not None
                  and any(d["unit"] == pot["unit"] for d in dyes3),
                  f"{len(dyes3)} dyes, {len(marks3)} markers")
        self.hwp("set mapicons.dyes 1", 0.4, until="mapicons.dyes = 1")
        time.sleep(2.0)
        dyes4, marks4 = self.dye_state()
        self.flag("dye_markers_back", pot is not None and self.marked(pot, marks4), f"{len(dyes4)} dyes, {len(marks4)} markers")

    # --- colors s1: contrast; your shots bluish, theirs reddish; beams and rays too
    def colors_tint(self):
        if not self.ensure_run("ranger", "LabTint"):
            return
        r = self.hwp("colors contrast", 0.5, until="preset contrast")
        self.flag("contrast_set", "Projectile colours: preset contrast" in r, r.strip()[-160:])
        enemy, friendly = PRESETS["contrast"]
        mark = len(self.g.read_log())
        tag = f"ui{int(time.time() * 1000) % 100000000}"
        self.gl("tintwatch", tag, 7000)
        self.gl("spawn", SENTRY, 80, 0)
        # the ranger's own shots go the other way, so the sentry lives to shoot back; each press
        # is held past the castpoint, or the aim follows the real mouse once it lets go
        for button in ("main", "main", "skill1", "main", "main"):
            self.shoot(button, 600, (-1, 0))
        self.snap("ui-colors-contrast")
        ev = self.g.wait_gl(lambda o: o.get("ev") == "tintwatch" and o.get("tag") == tag, 15) or {}
        projs = ev.get("projectiles") or []
        mine = [p for p in projs if p.get("friendly")]
        theirs = [p for p in projs if not p.get("friendly")]
        brief = [(p.get("name", "").split("/")[-1], p.get("behavior"), p.get("friendly"),
                  tuple(round(p["color"].get(k, 0), 2) for k in "rgb")) for p in projs[:10]]
        self.notes.append(f"tintwatch: {len(projs)} projectiles {brief}")
        self.flag("own_shots_bluish", bool(mine) and all(near_color(p["color"], friendly) for p in mine),
                  f"{len(mine)} friendly")
        self.flag("enemy_shots_reddish", bool(theirs) and all(near_color(p["color"], enemy) for p in theirs),
                  f"{len(theirs)} enemy")
        self.flag("tint_logged", "[HWP:colors] tinted" in self.log_since(mark) or "[HWP:colors] tinted" in self.g.read_log(),
                  re.findall(r"\[HWP:colors\] tinted [^\n]*", self.g.read_log())[-1:])
        self.gl("cull")
        # beams (trap beams are the only BeamProjectile units) and rays, by owner
        got = {}
        for key, unit, owner, d in (("beam_enemy", BEAM, "none", (0, 1)), ("beam_own", BEAM, "me", (0, -1)),
                                    ("ray_enemy", TRAP_RAY, "none", (0, 1)), ("ray_own", HYDRA_RAY, "me", (0, -1))):
            s = self.gl("shootproj", unit, owner, *d)
            got[key] = s.get("projectile") or {}
            time.sleep(0.3)
        def ok(key, want, cls):
            p = got[key]
            return p.get("behavior") == cls and near_color(p.get("color") or {}, want)
        self.flag("beams_tinted", ok("beam_enemy", enemy, "HWPBeamProjectile") and ok("beam_own", friendly, "HWPBeamProjectile"),
                  str({k: (v.get("behavior"), v.get("color")) for k, v in got.items() if k.startswith("beam")}))
        self.flag("rays_tinted", ok("ray_enemy", enemy, "HWPRayProjectile") and ok("ray_own", friendly, "HWPRayProjectile"),
                  str({k: (v.get("behavior"), v.get("color")) for k, v in got.items() if k.startswith("ray")}))

    # --- colors s5: the option switches the tints right away and hwp colors agrees
    def colors_option(self):
        if not self.ensure_run("ranger", "LabTint"):
            return
        self.hwp("colors contrast", 0.5, until="preset contrast")
        # the first `gl menu` opens the player menu and asks for the tab, but looks the widget up
        # in the tab that was open (plan-ui-b 20261018-125222: "no widget 'hwp-opt-colors' in
        # PlayerMenuCharacterTab"; the same call a frame later found it): ask until it answers
        row0 = {}
        for _ in range(4):
            row0 = self.gl("menu", "hwp_options", "-", "hwp-opt-colors")
            if row0.get("ok"):
                break
            time.sleep(0.5)
        title, _, v0 = row0.get("texts", "").partition(" | ")
        self.flag("option_row", row0.get("shown") and title == "Projectile colors",
                  f"tab {row0.get('tab')}, texts {row0.get('texts')!r}, error {row0.get('error')!r}")
        mark = len(self.g.read_log())
        self.gl("menu", "hwp_options", "-", "hwp-opt-colors", "hwp-opt", "colors")
        time.sleep(0.5)
        v1 = self.gl("menu", "hwp_options", "-", "hwp-opt-colors").get("texts", "").partition(" | ")[2]
        said = re.findall(r"\[HWP:options\] colors -> ([^\n]*)", self.log_since(mark))
        self.flag("option_switches", v1 and v1 != v0 and bool(said), f"{v0!r} -> {v1!r}, log {said}")
        self.g.key("escape")
        time.sleep(0.6)
        r = self.hwp("colors", 0.5, until="Projectile colours")
        cur = re.findall(r"Projectile colours: preset (\w+)", r)
        said = re.findall(r"Projectile colours: [^\n]*", r)
        preset = cur[-1] if cur else ""
        # contrast's next preset in InitPresets order
        self.flag("option_command_agrees", preset == "deuteranopia", f"hwp colors: {said[-1:]}")
        enemy, friendly = PRESETS.get(preset, PRESETS["deuteranopia"])
        s1 = (self.gl("shootproj", TRAP_RAY, "none", 0, 1).get("projectile") or {}).get("color") or {}
        s2 = (self.gl("shootproj", HYDRA_RAY, "me", 0, -1).get("projectile") or {}).get("color") or {}
        self.flag("option_tints_now", near_color(s1, enemy) and near_color(s2, friendly),
                  f"enemy {s1}, friendly {s2} for {preset}")
        self.hwp("colors off", 0.4)

    # --- deathrecap s2: die in a poison cloud / fire trap; the source reads "Hazards"
    def hazard_death(self):
        if not self.ensure_run("ranger", "LabTint"):
            return
        self.gl("kill", 6000, "tag:enemy")
        self.gl("cull")
        self.god(False)
        god = self.cvar("cht_god")
        mark = len(self.g.read_log())
        # hazards spawned on a player who stands still never touch it (plan-ui-b
        # 20261018-125222: 80 s in a floor fire and 6 poison clouds, hp 166/166 throughout,
        # "No damage recorded"): the static sensors only report a contact with a body that
        # moves. So the player steps left and right inside them (the fire's damage rect is
        # +-14, a cloud's radius 16), which also re-enters them.
        self.gl("spawn", FLOOR_FIRE, 0, 0)
        died, hps = [], []
        end = time.time() + 75
        while time.time() < end and not died:
            for _ in range(6):
                self.gl("spawn", CLOUD, 0, 0)
            for _ in range(4):
                self.gl("input", 200, 1, 0)
                time.sleep(0.3)
                self.gl("input", 200, -1, 0)
                time.sleep(0.3)
            p = self.gl("state").get("player") or {}
            hps.append((p.get("hp"), round(p.get("x", 0))))
            if p.get("dead"):
                time.sleep(1.5)
            died = re.findall(r"\[HWP:deathrecap\] (\S+) died: ([^\n|]*)\|([^\n]*)", self.log_since(mark))
            if p.get("dead"):
                break
        self.flag("hazard_death", bool(died), f"{died[-1:]}; cht_god {god}, (hp, x) over time {hps}")
        if died:
            summary = died[-1][1].strip()
            sources = [s.strip() for s in re.split(r",\s*", summary) if s.strip()]
            self.flag("recap_hazards", bool(sources) and all(s.startswith("Hazards") for s in sources), summary)
        else:
            self.flag("recap_hazards", False, "no death line")
        time.sleep(2)
        self.snap("ui-recap-hazards")
        r = self.hwp("recap", 0.5, until="Last death")
        said = re.findall(r"\[HWP\] ((?:Last death|No damage recorded)[^\n]*)", r)
        self.flag("recap_cmd_hazards", bool(said) and "Hazards" in said[-1], f"hwp recap: {said}")
        self.g.key("enter")
        self.wait_phase("town", 120)
        time.sleep(2)
        if self.gl("state").get("window"):
            self.g.key("escape")
            time.sleep(0.5)


def run(p, sections="bufftips_timed", **_):
    c = Checks(p)
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:  # a section's crash is its own failure, not the bot's
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
