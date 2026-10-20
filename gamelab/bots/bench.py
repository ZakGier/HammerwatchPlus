"""Class damage bench for balance passes: builds a character of one class at each checkpoint
level, in each specialization and weapon build, at the start of a run and late in one (skill
orbs and trinkets), and measures its damage on target dummies with `gl bench`
(mods/gamelab-hands/scripts/GameLab/Verbs_bench.as).

The build at a checkpoint is what a player of that level would plausibly have:
- every level's skill points spent (`gl skill`, one level at a time, the specialization's
  skills first, round robin) and every attribute point in the class's main attribute
  (`gl assign`);
- the weapons the class starts with, of the tier that drops at that level (ilvl inside the
  base item's ilvl..ilvl-max, the highest such tier), and generated armour (`gl kit`: drop
  generation weighted by the character's attributes), all at ilvl = level and the checkpoint's
  quality, finalised mid-range;
- late in a run: skill orbs (`gl orb`, picked one level at a time in the specialization's
  order, mutually exclusive orbs skipped once one of them is taken, orbs that only touch health,
  armour, mana or movement left out) and class-neutral trinkets (paired attack and spell ones).

The dummies (target_dummy_normal: 10 million hp, no armour, never moves) stand as a pack: one
in front (the single-target number) and four around and behind it (the pack number). Each bench
holds the main attack and casts every active skill whenever it can; a second bench also holds
the off hand, and the better of the two counts. Every bench starts fresh (bench clears summons,
cooldowns and fills mana; the Firearms clip is refilled first).

run(p, cls="ranger", levels=(1, 12, 20, 25), ms=15000) -> {"rows": [...]} and writes
gamelab/results/bench/<cls>.json."""
import json
import re
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SDK = REPO / "gamecode" / "sdk" / "hoh2"
MOD_ROOTS = [REPO / "mods" / "firearms", SDK]
OUT = REPO / "gamelab" / "results" / "bench"

DUMMY = "doodads/generic/target_dummy_normal.unit"
# the front dummy first: it is the single-target figure
PACK = [(80, 0), (100, -18), (100, 18), (120, 0), (80, 26)]
CLIP = "players/hwp/firearms/stacks_firearms.sval:clip"

CLASSES = {
    "ranger": {"sval": "players/ranger/class_ranger.sval", "attr": "dex",
               "specs": ["ranger_marksman", "ranger_beasts", "ranger_nature"],
               "builds": {"bow": ["twohanded_shortbow_{t}"]}},
    "rogue": {"sval": "players/rogue/class_rogue.sval", "attr": "dex",
              "specs": ["rogue_blades", "rogue_poison", "rogue_demolitions"],
              "builds": {"daggers": ["twohanded_daggers_{t}"]}},
    "sorcerer": {"sval": "players/sorcerer/class_sorcerer.sval", "attr": "int",
                 "specs": ["sorcerer_fire", "sorcerer_ice", "sorcerer_lightning"],
                 "builds": {"staff": ["twohanded_staff_lightning_{t}"]}},
    "wizard": {"sval": "players/wizard/class_wizard.sval", "attr": "int",
               "specs": ["wizard_evocation", "wizard_conjuration", "wizard_transmutation"],
               "builds": {"wand_tome": ["mainhand_wand_fire_{t}", "offhand_tome_ice_{t}"]}},
    "warlock": {"sval": "players/warlock/class_warlock.sval", "attr": "int",
                "specs": ["warlock_summoning", "warlock_souls", "warlock_chaos"],
                "builds": {"dirk_tome": ["mainhand_dirk_{t}", "offhand_tome_fire_{t}"]}},
    "hwp_firearms": {"sval": "players/hwp/firearms/class_firearms.sval", "attr": "dex",
                     "specs": ["hwp_firearms_sniper", "hwp_firearms_demolitions", "hwp_firearms_assault",
                               "hwp_firearms_engineer"],
                     "builds": {"rifle": ["hwp_rifle_{t}"], "pistols": ["hwp_glock_mh_{t}", "hwp_glock_oh_{t}"]}},
}

# level, gear quality, weapon tier, NG+, stages: (name, orb levels, trinkets)
CHECKPOINTS = {
    1: ("common", "01", 0, [("start", 0, 0), ("run", 2, 1)]),
    12: ("uncommon", "02", 0, [("start", 0, 0), ("run", 6, 3)]),
    20: ("rare", "03", 0, [("start", 0, 0), ("run", 12, 5)]),
    25: ("rare", "03", 1, [("start", 0, 0), ("run", 16, 6)]),
}
# class-neutral: all damage, then attack and spell twins in turn
TRINKETS = ["crest_courage", "codex_power", "girdle_might", "pendant_prowess", "whetstone", "focus_crystal"]
# an orb whose description parameters are all about these is no damage orb
NON_DAMAGE = re.compile(r"health|heal|armor|armour|mana|regain|movement|mspeed|evade|block|resist|dash|potion|light",
                        re.I)


def read(rel):
    for root in MOD_ROOTS:
        f = root / rel
        if f.exists():
            return re.sub(r"<!--.*?-->", "", f.read_text(encoding="utf-8", errors="replace"), flags=re.S)
    raise FileNotFoundError(rel)


def class_skills(cls):
    """class id -> the skill svals it lists, for the class and each of its subclasses"""
    s = read(CLASSES[cls]["sval"])
    out = {}
    for cid, body in re.findall(r'<string name="id">([^<]+)</string>(.*?)%block SharedStats', s, re.S):
        out[cid] = [x for x in re.findall(r"<string>([^<]+\.sval)</string>", body) if not x.endswith("dash.sval")]
    return out


def skill_info(rel):
    """id, whether it is a passive (no button: the bench never casts it), and its orbs:
    (id, blocked-by, damage-related)"""
    s = read(rel)
    sid = re.search(r'<string name="id">([^<]+)</string>', s).group(1)
    orbs = []
    m = re.search(r'<array name="modifier-skills">(.*)', s, re.S)
    if m:
        body = m.group(1)
        for block in re.split(r'\n\t\t<dict>', body)[1:]:
            oid = re.search(r'<string name="id">([^<]+)</string>', block)
            if not oid:
                continue
            blocked = re.findall(r"<s>([^<]+)</s>", (re.search(r'<array name="blocked-by-skills">(.*?)</array>', block, re.S)
                                                      or [None, ""])[1]) if "blocked-by-skills" in block else []
            params = re.findall(r"<array><s>([^<]+)</s><s>([^<]*)</s>", block)
            damage = not params or any(not NON_DAMAGE.search(a + " " + b) for a, b in params)
            orbs.append({"id": oid.group(1), "blocked": blocked, "damage": damage})
    return {"id": sid, "orbs": orbs}


class Bench:
    def __init__(self, p, cls, ms):
        self.g = p.game
        self.cls = cls
        self.ms = ms
        self.spec_skills = {k: [skill_info(x) for x in v] for k, v in class_skills(cls).items()}
        self.rows = []
        self.orbs_taken = []
        self.trinkets = 0
        self.home = None

    def gl(self, *a, timeout=20):
        return self.g.gl_cmd(*a, timeout=timeout)

    def console(self, line):
        self.g.console(line)
        time.sleep(0.2)

    def spend_skills(self, spec):
        """every skill point, one level at a time, round robin over the spec's own skills first"""
        base = [s["id"] for s in self.spec_skills[self.cls]]
        mine = [s["id"] for s in self.spec_skills[spec] if s["id"] not in base]
        order = mine + base
        levels = {}
        progress = True
        while progress:
            progress = False
            for sid in order:
                r = self.gl("skill", sid, 1)
                if r.get("ok"):
                    progress = True
                    levels[sid] = r.get("level", levels.get(sid, 0) + 1)
        return levels

    def take_orbs(self, spec, n):
        base = [s for s in self.spec_skills[self.cls]]
        mine = [s for s in self.spec_skills[spec] if s["id"] not in {b["id"] for b in base}]
        pool = [o for s in mine + base for o in s["orbs"] if o["damage"]]
        taken = {}
        blocked = set()
        while len(self.orbs_taken) < n and pool:
            moved = False
            for o in list(pool):
                if len(self.orbs_taken) >= n:
                    break
                if o["id"] in blocked:
                    pool.remove(o)
                    continue
                r = self.gl("orb", o["id"], 1)
                if r.get("ok"):
                    self.orbs_taken.append(o["id"])
                    taken[o["id"]] = r.get("level", 1)
                    blocked.update(o["blocked"])
                    moved = True
                else:
                    pool.remove(o)
            if not moved:
                break
        return taken

    def clear_run(self):
        for oid in reversed(self.orbs_taken):
            self.gl("orb", oid, "down")
        self.orbs_taken = []
        if self.trinkets:
            self.console("cht_clear_trinkets")
            self.trinkets = 0

    def give_trinkets(self, n):
        for t in TRINKETS[:n]:
            self.console(f"cht_give_specific_trinket {t}")
        self.trinkets = n
        time.sleep(0.5)
        return self.gl("trinkets").get("trinkets", [])

    def bench(self, tag, off):
        self.gl("kill", 600, "target_dummy")
        # back to the spot of the first bench: a melee run chases the pack, and the next pack
        # (placed around the player) drifted into a town wall where nothing hit it (rogue bench
        # 20261020-010121: every stage after the first read 0)
        if self.home:
            self.gl("teleport", *self.home)
        time.sleep(0.3)
        for dx, dy in PACK:
            self.gl("spawn", DUMMY, dx, dy)
        if self.cls == "hwp_firearms":
            self.gl("givestacks", CLIP, 999)
        time.sleep(0.5)
        args = ["bench", tag, self.ms, 400] + (["off"] if off else [])
        old = len(self.g.gl)
        self.gl(*args)
        ev = self.g.wait_gl(lambda o: o.get("ev") == "bench" and o.get("tag") == tag, self.ms / 1000 + 30)
        self.gl("kill", 600, "target_dummy")
        return ev or {"error": "no bench event"}

    def checkpoint(self, level, spec, build, weapons, quality, tier, stage, orbs, trinkets):
        self.gl("kit", level, quality, ",".join(w.format(t=tier) for w in weapons))
        taken = self.take_orbs(spec, orbs) if orbs else {}
        owned = self.give_trinkets(trinkets) if trinkets else []
        stats = self.gl("benchstats")
        best = None
        runs = []
        for off in (False, True):
            tag = f"{spec}.{build}.L{level}.{stage}.{'off' if off else 'main'}"
            ev = self.bench(tag, off)
            dummies = ev.get("dummies", [])
            single = dummies[0]["dmg"] / (ev.get("ms", 1) / 1000) if dummies else 0
            run = {"off": off, "dps": ev.get("dps", 0), "single": single, "ev": ev}
            runs.append(run)
            if best is None or run["single"] > best["single"]:
                best = run
        self.clear_run()
        row = {"class": self.cls, "spec": spec, "build": build, "level": level, "stage": stage,
               "quality": quality, "orbs": taken, "trinkets": owned,
               "single": round(best["single"], 1), "pack": round(best["dps"], 1), "off": best["off"],
               "stats": stats, "runs": runs}
        self.rows.append(row)
        print(f"[bench] {spec:28} {build:9} L{level:<2} {stage:5} single {row['single']:8.1f} pack {row['pack']:8.1f}"
              f" off={best['off']}", flush=True)
        return row


def run(p, cls="ranger", levels=(1, 12, 20, 25), ms=15000):
    b = Bench(p, cls, ms)
    g = b.g
    g.console("e_cheats 1")
    time.sleep(0.3)
    b.gl("char", cls, "Bench", timeout=60)
    g.wait_gl(lambda o: o.get("ev") == "hb" and o.get("phase") == "town", 60, fresh=True)
    time.sleep(2)
    g.console("e_cheats 1")
    time.sleep(0.3)
    plr = b.gl("state").get("player") or {}
    if "x" in plr:
        b.home = (round(plr["x"], 1), round(plr["y"], 1))
    cfg = CLASSES[cls]
    have = 1
    for level in levels:
        quality, tier, ngp, stages = CHECKPOINTS[level]
        if level > have:
            b.gl("levelup", level - have, timeout=30)
            have = level
            time.sleep(1)
        b.gl("assign", cfg["attr"], "all")
        b.gl("kit", level, quality)
        specs = [cls] if level < 10 else cfg["specs"]
        for spec in specs:
            if spec != cls:
                b.gl("subclass", cls)
                b.gl("subclass", spec)
            skills = b.spend_skills(spec)
            for build, weapons in cfg["builds"].items():
                for stage, orbs, trinkets in stages:
                    row = b.checkpoint(level, spec, build, weapons, quality, tier, stage, orbs, trinkets)
                    row["skills"] = skills
                    row["ngp"] = ngp
        if level >= 10:
            b.gl("subclass", cls)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{cls}.json").write_text(json.dumps(b.rows, indent=1), encoding="utf-8")
    return {"rows": [{k: r[k] for k in ("spec", "build", "level", "stage", "single", "pack", "off")} for r in b.rows],
            "count": len(b.rows)}
