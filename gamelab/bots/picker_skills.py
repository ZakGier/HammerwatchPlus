"""The Subclass Picker's skill row, read from a `gl widgets` dump and checked against the
spec's skill defs (`gl classskills <classId>`, mods/gamelab-hands/scripts/GameLab/Build.as).

The row is core's (mods/core/scripts/HWP/Core/SubclassPick.as): slot 0 and 1 keep the
vanilla ids (skill-active-name, skill-passive-name), slots from 2 on are hwp-pick-name<i>,
and every slot's type label is hwp-pick-label<i>. Without core's layout the labels have no
id and the row reads as no slots."""

ACTIVE = "Active"  # menu.subclass.skill.active / .passive, English (the lab profile's language)
PASSIVE = "Passive"
SPELL = 4  # PlayerSkillType Spell: every class skill def, passives too (PlayerClass.as:91-92
           # makes an untyped def a Spell), so the type can't tell; `passive` (targeting mode
           # Passive, no button) does
MAX_SLOTS = 4


def read_row(roots):
    """[(name, label)] of the visible slots, slot order."""
    nodes = {}
    for root in roots or []:
        for n in root.get("nodes", []):
            if n.get("id") and n["id"] not in nodes:
                nodes[n["id"]] = n
    row = []
    for i in range(MAX_SLOTS):
        name_id = {0: "skill-active-name", 1: "skill-passive-name"}.get(i, f"hwp-pick-name{i}")
        name, label = nodes.get(name_id), nodes.get(f"hwp-pick-label{i}")
        if not name or not label or not name.get("visible", True) or not label.get("visible", True):
            continue
        row.append((name.get("text", ""), label.get("text", "")))
    return row


def own_skills(reply):
    """The spec's own skills (Spell defs its parent class lacks) that the row shows, as
    [(name, label)] in class order: Passive for a def whose skill has no button
    (classskills `passive`), else Active."""
    own = [s for s in reply.get("skills") or [] if not s.get("inherited") and s.get("type") == SPELL]
    return [(s.get("name", ""), PASSIVE if s.get("passive") else ACTIVE) for s in own]


def row_problems(row, reply):
    """Why the shown row is not the spec's skills by their real types ([] when it is):
    every own active and passive shown once, each labelled by its type, an active first
    when the spec has one."""
    want = own_skills(reply)[:MAX_SLOTS]
    probs = []
    own = [s for s in reply.get("skills") or [] if not s.get("inherited") and s.get("type") == SPELL]
    if any("passive" not in s for s in own):
        probs.append("classskills gave no passive field (an old gamelab-hands): types unknown")
    if sorted(row) != sorted(want):
        probs.append(f"shown {row}, the spec's own {want}")
    if any(lab == ACTIVE for _, lab in want) and (not row or row[0][1] != ACTIVE):
        probs.append(f"first slot {row[:1]} is not an active")
    return probs
