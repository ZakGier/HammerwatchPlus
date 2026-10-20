# Class planner

A local web page for designing the HammerwatchPlus classes: every vanilla class's base kit,
specs and orbs (read from the game data, with each level's quality and numbers), the three
ported HoH1 classes, the Firearms Specialist's full design (doctrines, orbs, grenade,
arsenal, clip and reload, gun attributes, budget), and a 4th specialization slot for every
other class.

## Open it

Double-click `planner.cmd` in the repo root, or from the repo root run:

```
python -m planner                 # opens http://127.0.0.1:8737/ in your browser
python -m planner --port 9000     # another port (0 picks a free one)
python -m planner --no-browser
```

Python 3.10+ and nothing else: no packages, no game install, no `gamecode/`. Keep the
window open while you use the page; Ctrl+C (or closing it) stops the server.
`#<class id>` at the end of the address opens one class, for example `#ranger`.

## Where edits go

Every record is one file, `planner/data/<collection>/<id>.json`, and a Save in the page
writes it straight away. Commit those files like any other change, and pull to get other
people's. The page checks for changes every 2 s, so a `git pull` or a hand edit shows up
without a reload.

| Collection | Holds |
|---|---|
| `classes` | each class: stats, gear, base kit, specs and their orbs (read-only game data); the class notes field |
| `doctrines` | specializations you design: the Firearms doctrines and each class's 4th (`spec4: true`) |
| `skills` | skills in those specializations |
| `mods` | new orbs, on a new skill or on a vanilla one (`skill` is its id) |
| `weapons`, `stacks`, `attributes`, `reference` | Firearms only: arsenal, clip and reload, gun attributes, budget targets |

A record with no `cls` belongs to the Firearms Specialist.

## Icons

`web/icons.png` and `web/icons.json` are the skill and orb icons, cut from the game's
atlases (vanilla and Firearms) and the local HoH1 art. `tools/icon_art/planner_icons.py`
rebuilds the vanilla and Firearms part from `planner/data` (it needs `gamecode/`).
