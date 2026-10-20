# icon_art: skill and orb icon ideas in the vanilla style

Generators for 24x24 skill icons painted the way the vanilla HoH2 skill icons are: no
outlines, 4-6 step ramps lit from the upper left, a bright rim and a dark core shadow,
big cropped subjects, glowing energy with a white-hot core, near-black tinted grounds
(vpaint.py's docstring has the full list). Each icon function returns three ideas,
A (the gear up close), B (the moment it happens) and C (an abstract mark), for the user
to pick from; nothing here writes to a mod. A picked Firearms icon goes into the game
through `art/firearms/override/` and `tools/make_firearms_icons.py`.

| file | what |
|---|---|
| vpaint.py | the painter: ramps, SDF shapes, grounds, glows, `sheet()` |
| motifs.py | Firearms objects: guns, rounds, mags, rockets, turrets |
| vm.py | vanilla-class objects: blades, shields, bows, books, elements, bodies |
| fa.py, fa2.py, fa3.py | the Firearms Specialist's icons (skills, orbs, attacks, HUD) |
| vo_<class>.py | each vanilla class's orb icons |
| planner_icons.py | the class planner's icon sheet, cut from the game's atlases |
| orb_groups.py | the picker's per-class orb lists, from the planner's data |
| render.py, rorb.py | write the ideas and comparison sheets |
| picker.py, picker_tpl.html | the picker page (every idea, the current icon beside it) |

Everything is written under `tools/icon_art/out/` (git-ignored):

```
python tools/icon_art/render.py all            # Firearms ideas -> out/firearms/, out/sheet_all_*.png
python tools/icon_art/planner_icons.py <dump>  # out/planner_pub/icons.png (the "now" column)
python tools/icon_art/rorb.py warrior          # one class's orb ideas -> out/orbs/warrior/
python tools/icon_art/orb_groups.py <dump>     # out/orbs/<cls>.json
python tools/icon_art/picker.py                # out/picker.html
```

`<dump>` is a folder with the class planner's data as `planner/classes/*.json`,
`planner/skills/*.json` and `planner/mods/*.json` (the planner artifact's database
collections). Needs Pillow, and `gamecode/` for the vanilla atlases.
