"""make_constellation.py - writes HoH1's Constellation puzzle as a HoH2 prefab.

    python tools/make_constellation.py            # (re)write the prefab
    python tools/make_constellation.py --check    # exit 1 when the committed prefab is stale

HoH1 (puzzle_constellation.pfb) picks one of eight class constellations, shows the
class sigil on a pedestal and asks for exactly those stars on a 5x5 field. Press a
wrong star and the puzzle fails; press them all and an item drops. HoH2 has no
sigil art, so a small 5x5 chart of lit dots above the field shows the shape
instead (the HoH1 sigils are drawn the same way). The star patterns are HoH1's.

Everything is vanilla HoH2 worldscripts, so co-op sync, the use prompt and the
room reward are the engine's own:

    RandomCount (startup) -> one pattern ScriptLink -> ToggleScripts enables the
        "correct" link of each pattern star and the "wrong" link of every other star,
        ChangeVariables sets the remaining-star count, SetUnitScene lights the chart
    UseTrigger per star (once) -> light the star, then correct (-1, solved at 0)
        or wrong (failed)
    solved -> lock, sound, RewardSpot (forced, high quality, no materials/pickups),
        announce;   failed -> lock, fail sound, announce

Comments name the scripts GameLab drives (hwp_star_<r>_<c>, hwp_correct_<r>_<c>,
hwp_pattern_<class>, hwp_remaining, hwp_solved, hwp_failed). The output is the
game's SValue XML; tools/build.py compiles it.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hwr_archive as hwr  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "mods/puzzles/prefabs/puzzles/hwp/puzzle_constellation.pfb"

# HoH1 doodads/generic constellation patterns, rows top to bottom.
PATTERNS = {
    "paladin":   ["*****", "*...*", "*...*", ".*.*.", "..*.."],
    "thief":     ["....*", "...*.", "*.*..", ".*...", "*.*.."],
    "ranger":    ["..*..", ".*...", "*.***", ".*...", "..*.."],
    "priest":    ["..*..", ".***.", "..*..", "..*..", "..*.."],
    "warlock":   [".*...", "..*..", ".***.", "..*..", "...*."],
    "wizard":    ["*....", ".*...", "..**.", "..*.*", "...**"],
    "sorcerer":  ["..*..", ".*.*.", ".*.*.", ".*.*.", "..*.."],
    "gladiator": ["*.*.*", "*.*.*", ".***.", "..*..", "..*.."],
}

STAR_UNIT = "doodads/buttons/button_magic.unit"
DOT_UNIT = "doodads/hwp/puzzle_constellation_dot.unit"
MARKER_UNIT = "doodads/generic/marker_target_16.unit"

STAR_STEP, STAR_X0, STAR_Y0 = 20, -40, -28   # field: x -40..40, y -28..52
DOT_STEP, DOT_X0, DOT_Y0 = 7, -14, -80       # chart: x -14..14, y -80..-52
REWARD_POS = (36.0, -66.0)
AREA_SIZE = 14

SND_SOLVED = "event:/misc/sequence_complete"
SND_FAILED = "event:/SFX/UI/puzzle/puzzle_fail"
TXT_SOLVED = ".hwp.puzzles.constellation.solved"
TXT_FAILED = ".hwp.puzzles.constellation.failed"


def V(*xs):
    return hwr.Vec([float(x) for x in xs])


def cells():
    return [(r, c) for r in range(5) for c in range(5)]


def build() -> dict:
    ids = iter(range(1, 100000))
    area = {rc: next(ids) for rc in cells()}
    star = {rc: next(ids) for rc in cells()}
    dot = {rc: next(ids) for rc in cells()}
    marker = next(ids)

    def star_pos(r, c):
        return (STAR_X0 + c * STAR_STEP, STAR_Y0 + r * STAR_STEP)

    def dot_pos(r, c):
        return (DOT_X0 + c * DOT_STEP, DOT_Y0 + r * DOT_STEP)

    units = {
        ":Physics_Rectangle": [
            [V(*star_pos(*rc)), area[rc], {
                "active": True, "jam-through": True, "sensor": True,
                "shot-through": True, "aim-through": True, "size": V(AREA_SIZE, AREA_SIZE)}]
            for rc in cells()],
        STAR_UNIT: [x for rc in cells() for x in (V(*star_pos(*rc)), star[rc])],
        DOT_UNIT: [x for rc in cells() for x in (V(*dot_pos(*rc)), dot[rc])],
        MARKER_UNIT: [V(*REWARD_POS), marker],
    }

    scripts = []

    # editor positions only matter for RewardSpot / PlaySound / AnnounceText; the
    # rest sit off to the side in columns so the editor view stays readable
    def add(kind, sid, pos, enabled=True, times=-1, startup=False, comment=None, params=None, links=None):
        s = [kind, sid, V(pos[0], pos[1], 0), enabled, times, startup]
        if comment is not None:
            s.append(comment)
        if params is not None:
            s.append(params)
        if links:
            s.append([x for link in links for x in (link, 0)])
        scripts.append(s)

    sid = {name: next(ids) for name in (
        "remaining", "pick", "dec", "check", "solved", "failed", "lock",
        "snd_ok", "snd_fail", "reward", "ann_ok", "ann_fail")}
    use, lit, ok, bad = ({rc: next(ids) for rc in cells()} for _ in range(4))
    pat = {name: (next(ids), next(ids), next(ids), next(ids)) for name in PATTERNS}

    add("Variable", sid["remaining"], (-200, -160), comment="hwp_remaining")
    add("RandomCount", sid["pick"], (-200, -120), startup=True, comment="hwp_pick",
        params={"NumToExecute": 1, "ToExecute": [pat[n][0] for n in PATTERNS]})
    for i, (name, rows) in enumerate(PATTERNS.items()):
        link, toggle, count, show = pat[name]
        on = [rc for rc in cells() if rows[rc[0]][rc[1]] == "*"]
        x = -320 + 40 * i
        add("ScriptLink", link, (x, -240), comment="hwp_pattern_" + name, links=[toggle, count, show])
        add("ToggleScripts", toggle, (x, -280), params={
            "State": 1, "Scripts": [ok[rc] if rc in on else bad[rc] for rc in cells()]})
        add("ChangeVariables", count, (x, -320), params={
            "Function": 1, "Use": 1, "ModConstant": len(on), "Variables": [sid["remaining"]]})
        add("SetUnitScene", show, (x, -360), comment="on", params={"State": "on", "Units": [dot[rc] for rc in on]})

    for rc in cells():
        r, c = rc
        tag = f"{r}_{c}"
        x, y = 200 + c * 40, -200 + r * 120
        add("UseTrigger", use[rc], (x, y), times=1, comment="hwp_star_" + tag,
            params={"Areas": [area[rc]]}, links=[lit[rc], ok[rc], bad[rc]])
        add("SetUnitScene", lit[rc], (x, y + 30), comment="on", params={"State": "on", "Units": [star[rc]]})
        add("ScriptLink", ok[rc], (x, y + 60), enabled=False, comment="hwp_correct_" + tag, links=[sid["dec"]])
        add("ScriptLink", bad[rc], (x, y + 90), enabled=False, comment="hwp_wrong_" + tag, links=[sid["failed"]])

    add("ChangeVariables", sid["dec"], (480, -160), params={
        "Function": 3, "Use": 1, "ModConstant": 1, "Variables": [sid["remaining"]]}, links=[sid["check"]])
    add("CheckVariables", sid["check"], (480, -120), comment="0", params={
        "Function": 1, "Value": 0, "Variable": [sid["remaining"]], "OnTrue": [sid["solved"]]})
    add("ScriptLink", sid["solved"], (480, -80), times=1, comment="hwp_solved",
        links=[sid["lock"], sid["snd_ok"], sid["reward"], sid["ann_ok"]])
    add("ScriptLink", sid["failed"], (480, -40), times=1, comment="hwp_failed",
        links=[sid["lock"], sid["snd_fail"], sid["ann_fail"]])
    add("ToggleScripts", sid["lock"], (480, 0), comment="lock", params={
        "State": 2, "Scripts": [use[rc] for rc in cells()] + [sid["solved"], sid["failed"]]})
    add("PlaySound", sid["snd_ok"], (0, 0), comment="SequenceComplete", params={"Sound": SND_SOLVED})
    add("PlaySound", sid["snd_fail"], (0, 0), comment="SequenceFailed", params={"Sound": SND_FAILED})
    add("RewardSpot", sid["reward"], REWARD_POS, comment="constellation", params={
        "Materials": False, "Pickups": False, "Quality": 2, "Forced": True, "Secret": True, "Delayed": True})
    add("AnnounceText", sid["ann_ok"], (0, -100), params={"Text": TXT_SOLVED})
    add("AnnounceText", sid["ann_fail"], (0, -100), params={"Text": TXT_FAILED})

    return {"version": 1, "units": units, "scripts": scripts}


def render() -> bytes:
    head = "<!-- generated by tools/make_constellation.py; edit the generator, not this file -->\n"
    return (head + hwr.svalue_to_xml(build()) + "\n").encode("utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="fail when the committed prefab differs")
    args = ap.parse_args(argv)
    data = render()
    if args.check:
        if not OUT.exists() or OUT.read_bytes() != data:
            print(f"{OUT.relative_to(ROOT).as_posix()} is stale: run python tools/make_constellation.py")
            return 1
        print("constellation prefab up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(data)
    print(f"wrote {OUT.relative_to(ROOT).as_posix()} ({len(PATTERNS)} patterns, {len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
