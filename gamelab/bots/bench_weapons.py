"""Weapon damage bench for balance passes: one Firearms Specialist (every attribute point in
dexterity, no skills cast) holds the main attack of each ranged weapon on one target dummy for
`ms` of gameplay, reloads included, so the guns read against the bow and the crossbow on the
same character (`gl bench ... noskills`, mods/gamelab-hands/scripts/GameLab/Verbs_bench.as).
Equipment requirements are waived (dbg_cht_ignore_equipment_requirements): the longbow and the
crossbow ask for strength, which adds armour and armour penetration (Modifiers.as 496-497),
not weapon damage, and the dummy has no armour; dexterity's crit counts for every weapon alike.
The dummy stands below the player, clear of the horse in a new character's clearing.

run(p, levels=(1, 12), ms=15000) -> {"rows": [{level, weapon, dps, hits}]} and writes
gamelab/results/bench/weapons.json."""
import json
import time

from gamelab.bots.bench import CLIP, DUMMY, OUT

# per level: (weapon build name, items for `gl kit`)
WEAPONS = {
    1: [("shortbow", "twohanded_shortbow_01"), ("longbow", "twohanded_longbow_01"),
        ("crossbow", "twohanded_crossbow_01"), ("rifle", "hwp_rifle_01"),
        ("pistol", "hwp_glock_mh_01"), ("pistols", "hwp_glock_mh_01,hwp_glock_oh_01")],
    12: [("shortbow", "twohanded_shortbow_02"), ("longbow", "twohanded_longbow_02"),
         ("crossbow", "twohanded_crossbow_01"), ("rifle", "hwp_rifle_02"),
         ("pistol", "hwp_glock_mh_02"), ("pistols", "hwp_glock_mh_02,hwp_glock_oh_02")],
}


def run(p, levels=(1, 12), ms=15000, only=""):
    g = p.game

    def gl(*a, timeout=20):
        return g.gl_cmd(*a, timeout=timeout)

    g.console("e_cheats 1")
    time.sleep(0.3)
    gl("char", "hwp_firearms", "Bench", timeout=60)
    g.wait_gl(lambda o: o.get("ev") == "hb" and o.get("phase") == "town", 60, fresh=True)
    time.sleep(2)
    g.console("e_cheats 1")
    time.sleep(0.3)
    g.console("dbg_cht_ignore_equipment_requirements 1")
    time.sleep(0.3)
    rows = []
    have = 1
    for level in levels:
        if level > have:
            gl("levelup", level - have, timeout=30)
            have = level
            time.sleep(1)
        gl("assign", "dex", "all")
        for name, items in WEAPONS[level]:
            if only and name not in only.split(","):
                continue
            kit = gl("kit", level, "common", items)
            time.sleep(0.5)
            stats = gl("benchstats")
            gl("kill", 600, "target_dummy")
            time.sleep(0.3)
            gl("spawn", DUMMY, 0, 80)
            gl("givestacks", CLIP, 999)
            time.sleep(0.5)
            tag = f"{name}.L{level}"
            gl("bench", tag, ms, 400, "noskills")
            ev = g.wait_gl(lambda o: o.get("ev") == "bench" and o.get("tag") == tag, ms / 1000 + 30) or {}
            gl("kill", 600, "target_dummy")
            dummies = ev.get("dummies", [])
            dps = dummies[0]["dmg"] / (ev.get("ms", ms) / 1000) if dummies else 0
            used = [w.get("weapon") for w in ev.get("weapons", [])]
            row = {"level": level, "weapon": name, "items": items, "dps": round(dps, 1), "kit": kit, "attacks": used,
                   "hits": ev.get("hits"), "stats": stats.get("main") or stats, "ev": ev}
            rows.append(row)
            print(f"[bench] L{level:<2} {name:9} dps {dps:8.1f} {used}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "weapons.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return {"rows": [{k: r[k] for k in ("level", "weapon", "dps", "attacks")} for r in rows], "count": len(rows)}
