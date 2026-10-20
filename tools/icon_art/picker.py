"""Builds the icon picker page: python picker.py [r1] -> out/picker.html
The Firearms group is round 2 (fa_r2.py's out/firearms_r2/<id>_<a|b|c|now>.png, "now" being
the round-1 pick, with the round-1 note on the card); with r1, round 1 instead (fa.py, fa2.py
and fa3.py's out/firearms/, from render.py all, beside the current icon). Each vanilla
class's group comes from out/orbs/<cls>.json (orb_groups.py) and rorb.py's images."""
import base64, io, json, sys
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "firearms"
DEST = HERE / "out"
DEST.mkdir(exist_ok=True)

sys.path.insert(0, str(HERE))
import fa, fa2, fa3  # noqa: E402

FIREARMS_DESC = {
    "frag": "Frag Grenade", "stun_grenade": "Stun Grenade: blinding flash", "incendiary": "Incendiary Grenade: burning ground",
    "gas": "Gas Grenade: poison cloud", "rpg_jump": "Rocket Jump", "shrapnel": "Elemental Shrapnel",
    "exposure": "Exposure (Critical Aim orb)", "scavenger_blind": "Blinding Poison rounds (green)",
    "scavenger_slow": "Slowing Freeze rounds (blue)", "scavenger_lightning": "Shocking rounds (yellow)",
    "myturret_shared": "My Turret: teammates boost it", "boom_headshot": "Boom, Headshot (Critical Aim orb)",
    "overpacked": "Overpacked Explosives", "magic_missile": "Magic Missile: fire and frost",
    "hoarder": "Ordnance Hoarder", "over_reload": "Over-Reload: perfect reload ring",
    "reload": "Reload", "snipe": "Snipe", "critical_aim": "Critical Aim (Focus stacks)", "focus_hud": "Focus stacks (HUD)",
    "rocket": "Rocket", "scavenger": "Scavenger: elemental rounds", "dodge_skip": "Dodging finishes the reload",
    "explosive_reload": "Explosive Reload: throws the mag", "headshot": "Headshot: first hit crits",
    "piercing": "Piercing: passes through more enemies", "fat_boy": "Fat Boy: poison and blind",
    "quad_missile": "Quad Missile: four small missiles", "rifle_attack": "Rifle attack", "glock_attack": "Pistol attack",
    "glock_dual": "Dual pistols", "gl_attack": "Grenade launcher attack", "steady": "Extended Clip: crit damage per round left",
    "steady_crit": "Extended Clip: crit chance per round", "clip_hud": "Rounds in clip (HUD)", "reloading_hud": "Reloading (HUD)",
    "grenade_charges_hud": "Grenade charges (HUD)", "rocket_charges_hud": "Rocket charges (HUD)",
    "gl_charges_hud": "Launcher charges (HUD)", "burst": "Shotgun Burst", "burst_breath": "Dragon's Breath shells: fire",
    "burst_triple": "Three shells", "adrenaline": "Adrenaline: stacks heal", "adrenaline_crit": "Adrenaline: crit per stack",
    "adrenaline_epipen": "Epipen: dodging with no stacks grants stacks", "adrenaline_hud": "Adrenaline stacks (HUD)",
    "turret": "Turret", "my_turret": "My Turret: repair and boost nearby", "turret_reinforced": "Reinforced Turret: more health",
    "turret_second": "Second Turret", "myturret_feed": "My Turret: elemental rounds", "frag_shrapnel": "Frag: armor shred",
    "scavenger_fire": "Fire rounds", "scavenger_ice": "Ice rounds", "scavenger_poison": "Poison rounds",
    "scavenger_stun": "Stun rounds: lightning stuns",
}


def uri(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def firearms_group():
    items = []
    for n in list(fa.FA) + list(fa2.FA2) + list(fa3.FA3):
        imgs = {k: uri(Image.open(OUT / f"{n}_{k}.png")) for k in "abc"}
        cur = fa.current(n)
        if cur is not None:
            imgs["now"] = uri(cur)
        items.append({"id": "firearms." + n, "name": FIREARMS_DESC.get(n, n.replace("_", " ")), "key": n, "imgs": imgs})
    return {"id": "firearms", "title": "Firearms Specialist", "items": items}


R1 = {"a": "A", "b": "B", "c": "C", "keep": "the icon it had", "": "none"}


def firearms_r2_group():
    """Round 2: ids firearms2.<name>, so the round-1 picks (firearms.<name>) stay as they are."""
    import fa_r2
    d = HERE / "out" / "firearms_r2"
    r1 = json.loads((HERE / "out" / "picks_r1.json").read_text(encoding="utf-8"))
    items = []
    for n in sorted(fa_r2.FA_R2):
        imgs = {k: uri(Image.open(d / f"{n}_{k}.png")) for k in ("a", "b", "c", "now")}
        choice, note = r1.get(n, ["", ""])
        desc = f"Round 1: you picked {R1[choice]}" + (f'; "{note}"' if note else "") + "."
        if n.endswith("_hud"):
            desc += " A 14x14 buff-bar icon, shown at its size."
        items.append({"id": "firearms2." + n, "name": FIREARMS_DESC.get(n, n.replace("_", " ")), "key": n,
                      "desc": desc, "imgs": imgs})
    return {"id": "firearms2", "title": "Firearms Specialist, round 2", "items": items}


def extra_groups():
    """Vanilla orb groups written by orb_groups.py as out/orbs/<cls>.json (if present)."""
    groups = []
    d = HERE / "out" / "orbs"
    if d.exists():
        for f in sorted(d.glob("*.json")):
            g = json.loads(f.read_text(encoding="utf-8"))
            for it in g["items"]:
                it["imgs"] = {k: uri(Image.open(d / p)) for k, p in it["imgs"].items()}
            groups.append(g)
    return groups


def main():
    groups = [firearms_group() if "r1" in sys.argv[1:] else firearms_r2_group()] + extra_groups()
    tpl = (HERE / "picker_tpl.html").read_text(encoding="utf-8")
    html = tpl.replace("/*DATA*/null", json.dumps(groups, separators=(",", ":")))
    (DEST / "picker.html").write_text(html, encoding="utf-8")
    print(sum(len(g["items"]) for g in groups), "icons,", len(html) // 1024, "KB")


if __name__ == "__main__":
    main()
