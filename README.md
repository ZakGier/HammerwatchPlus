# HammerwatchPlus

A modular co-op mod for **Heroes of Hammerwatch II**: a new class (the Firearms Specialist)
and the three HoH1 classes HoH2 lacks, Heroes of Hammerwatch 1 content (the Forsaken Tower
campaign, keys and ace chests, legendaries, mercenaries, titles, pets), new things to find in
the dungeons, fishing and farming in town, and co-op and quality-of-life fixes.

Every module ships as its own mod package, plus an all-in-one build. Everyone in a lobby
should run the same version of the same modules. Every module needs `core`; `goldpet` also
needs `pets`.

## Modules

### Classes and combat

| Module | What it does |
|---|---|
| `firearms` | The **Firearms Specialist**, a new class. Guns fire from a clip that counts down per shot and reloads (automatically at 0, or with the Reload skill, which a dodge cancels); mana pays for gadgets. A rifle (30 rounds, 3-round bursts, an under-barrel grenade launcher) or pistols, one or two (10 rounds each, 20 dual). Base kit: Reload and Frag Grenade, whose orbs give Explosive Reload, Over-Reload's timed perfect reload, and Stun, Incendiary or Gas grenades. Four specializations, each with orbs: **Marksman** (Snipe, Critical Aim), **Demolitionist** (Rocket Launcher, Ordinance Hoarder), **Assault** (Double Barrel Burst, Adrenaline) and **Engineer** (Deploy Turret, My Turret!). New characters start with a Service Pistol. Details: `mods/firearms/README.md`; design: `docs/design/firearms.md`. |
| `classes` | The HoH1 classes HoH2 lacks: **Thief**, **Gladiator** and **Witch Hunter**, three masteries each. The Thief's extra actives cast on core's Skill 4 key. The real HoH1 art comes from your own HoH1 install (`tools/import_hoh1.py classes`). |
| `weapons` | Twelve new endgame weapons (ilvl 35, four per slot) with new modifier profiles on vanilla visuals and attacks. |
| `weaponswap` | A second weapon set on a hotkey (default X): a 2 s channel standing still, cancelled by a dodge or a second press. |
| `summons` | Summons come through a floor change with the HP they had. The game already carries the Priest's Crusaders; this tops up any that go missing, and the `summons.all` setting covers every summon (wolves, Warlock minions). |

### Heroes of Hammerwatch 1

| Module | What it does |
|---|---|
| `campaign` | **The Forsaken Tower**: the HoH1 campaign (Mines to Battlements, 18 floors, 6 bosses), started from a portal in town. NG+ swaps in HoH1's NG+ bosses and enemies. With HoH1 installed, a second version plays the real HoH1 boss rooms and Battlements (`tools/import_hoh1.py campaign`). |
| `keys` | HoH1-style keys: every chest but the cursed ones needs a key of its tier. Keys drop in runs (a party can share a key pool), and the exit guard's General Merchant sells keys, bag slots and six trinkets to take into your next run. Also ace chests and seven red legendaries. |
| `mercenary` | HoH1's mercenary mode: once a class has a level-20 hero, a fresh character of it can enlist (`hwp merc enlist`), climb the ranks from Private to General for more gold and experience, and die for good. |
| `legacy` | HoH1-style class titles: your best hero of each class buffs every character. One "Title Bonuses" buff lists them, and Guild Hall > Titles shows every class. |
| `pets` | Pets level up (from kills, pickups, and farm crops at the feeding bowl) and learn utility skills. Per-pet pickup toggles, pet dyes at the tailor, pets wait outside puzzle rooms, and every HoH1 pet is in the Pet Shop (imported from your own HoH1 install). |

### Runs and dungeons

| Module | What it does |
|---|---|
| `puzzles` | Puzzle rooms are back on most floors (HoH2 ships 88 but never places them), and HoH1's Constellation puzzle is one they can roll, also in a clearing on forest and heaven floors. |
| `strongbox` | Path of Exile-style strongboxes: open one, a pack of the floor's enemies spawns (elites possible), clear it for the box's loot. |
| `abyss` | Abyss cracks: step close and waves crawl out, ending in elites (more in a bigger party). Clear them for a reward that grows the deeper the run goes. |
| `maps` | Three new layouts for the equipment-map drops: Goblin Warrens, Sunken Dungeon, The High Court. |
| `valuables` | Valuables (vases, chalices, gems, furs, scales: the pickups that turn straight into gold) are worth twice their vanilla gold. |
| `wavemode` | **Wave Arena**: a survival arena started from a statue in town; every boss kill raises your arena rank, which is the arena's NG+ level next time. |

### Town

| Module | What it does |
|---|---|
| `fishing` | Six fishing spots on the town coast (a timing minigame), more in the water of run floors' potion wells (always one in a boss room), greyed on the map once fished out. A pirate sells bait, rods and fish traps from the trading post's wreck, later its boat. Fish are swords, sell for bet tokens and can be eaten (100 HP per star). |
| `farming` | The town's field grooves become farm plots: food crops and four Holy Herb strains grow with each completed run, faster when watered (the farmer sells the can and seeds; the well refills it). Smoke a herb for a buff that lasts 10 floors, or roll it into a joint: an off-hand with 5 puffs that a friend can take from you, with smoke that fills the room. |
| `gambler` | A gambler in the tavern plays Higher/Lower for gold. He buys crops and herbs for gold and fish for bet tokens, and rerolls equipped gear for 2000 gold × item level, or 1 bet token per 5 item levels. |
| `goldpet` | A pet vendor in the Hunter's Lodge sells the Gold Collector cat, with two upgrades (materials and scrolls, then valuables). |
| `stash` | A Sort button on the town stash: by class, then weapon type, then item level. |
| `laststats` | The last run's stats for the whole party, on a notice board by the town fountain. |

### Co-op and quality of life

| Module | What it does |
|---|---|
| `groupcombo` | A party-wide combo bonus that grows with how many players are in combo, and brief invulnerability when everyone is. |
| `architect` | Any player can pick and pay for Architect alterations; the host's picks are split across the party. Seven HoH1 challenges discount them, down to free. |
| `droptrade` | Drop equipment on the ground for friends: a Drop button (Q) next to Destroy in the inventory. |
| `deathrecap` | Who killed you: the top damage sources of the last 10 s, on screen and in chat. |
| `bufftips` | Hover a buff icon to see what it does and how many seconds it has left. |
| `chatlinks` | Linked items stay in chat with their slot and item level; `hwp link` links an equipped item. |
| `colors` | Colour-blind and high-contrast tints for enemy and friendly projectiles (player menu > Plus tab). |
| `core` | Required by every module: settings (the Plus tab and the `hwp` console command), save data and networking. It also adds keys 4, 5 and 6 for a class's 4th to 6th active skill, a Plants & Herbs section in the Materials tab with Eat and Roll actions, a warning on orbs that close off other orbs, the use key picking up a dropped item before it talks to an NPC, and "Mm-hmm!" hats (a quarter of rare and epic hats play the Material Trader's "mm-hmm" on every crit, for everyone). |

Each module's full spec and test checklist is in `mods/<id>/README.md`.

`mods/gamelab-*` are GameLab test harnesses, not player content. `build.py` never packs
them; they are only linked into the GameLab environment.

| Harness | What it does |
|---|---|
| `gamelab-probe` | The `gl` console command channel, read-only state probes, heartbeat. |
| `gamelab-hands` | Action verbs for the `gl` channel (start a mission floor, ...). Requires probe. |
| `gamelab-pilot` | Bot API for the Pilot. Requires probe and hands. |
| `gamelab-reload` | Logs a mark from its constructor, so the `reload-mark` scenario can tell whether an edited script was picked up without a restart. |

## Installing (players)

No releases are published yet; until then, build the packages yourself (see Developing,
`python tools/build.py`).

1. Take the `.bin` files you want from `dist/` (or `HammerwatchPlus-All.bin` for everything).
2. Drop them into `<Steam>/steamapps/common/Heroes of Hammerwatch 2/mods/`.
3. Start the game, open **Resource Mods** and enable them. Everyone in the lobby does the same.
4. In game, open the console (the key left of 1) and type `hwp help` for the commands and settings.

Workshop uploads will follow once the modules settle.

## Class planner

The class designs live in a local web page: every class's kit, specs and orbs from the game
data, the Firearms Specialist's full design, and a 4th specialization for each of the other
classes. The 4th specs of the six vanilla classes are being designed now (Rogue and
Sorcerer: Zak; Warrior and Warlock: Colin; Ranger and Wizard: Noah); the brief is at the top
of each class's page.

It needs only Python 3 (no game, no packages):
- **Windows:** double-click `planner.cmd`.
- **Linux / macOS:** `./planner.sh`.
- **Anywhere:** `python -m planner` (or `python3`) from the repo root.

Edits are saved as JSON files under `planner/data/`; commit and push them. More in
`planner/README.md`.

## Status

- Every solo step of the in-game test plan has a `gamelab/scenarios/plan-*.json` scenario.
  As of 2026-10-18 they all pass in GameLab except Weapon Swap's "only you can pick it up",
  which needs a real lobby. The Firearms Specialist's checks (`plan-t14`, `plan-firearms-*`)
  last passed on 2026-10-19 and 2026-10-20.
- The co-op steps need two players: GameLab runs one game, and HoH2 only connects through
  Steam/GOG lobbies.
- GameLab is pinned to build 25932569 (since 2026-10-19).
- Firearms still to do: the two base passives (the old Scavenger and Steady Hands stand in)
  and final icons (the current ones are placeholders from `tools/make_firearms_icons.py`).
- The vanilla classes' 4th specs are being designed in the class planner.
- What each session changed, with the GameLab run behind every claim, is in
  `docs/RE_NOTES.md`. The HoH1-to-HoH2 trinket comparison is a private web app outside the
  repo; its link is there too.

## GameLab

GameLab is the test harness: it boots a sandboxed copy of the game hidden and muted,
drives it through its own scripts (no real input, no focus steals, never touching your
config or saves), and scores what happened. Use the `gamelab` skill to run it.
Before merging to main, run `python -m gamelab run mod-all --mode lab` (every content
mod loaded together; GUI textures must be power-of-two sized or the game won't boot).

## Developing

Requirements:
- Windows, with Steam running.
- Python 3.10+ with [uv](https://docs.astral.sh/uv/).
- gcc from mingw-w64 (x86_64), which builds the GameLab capture shim.
- HoH2 installed.
- HoH1 optional: with it, doctor imports the HoH1 content (pets, levels, campaign, class art).

```
python -m gamelab doctor              # first thing on a new clone: checks every prerequisite
python -m gamelab doctor --fix        # uv sync, back up + verify your saves, bootstrap.py (gamecode/, tools/bin/),
                                      # env_link.py, class_units.py, the HoH1 imports when HoH1 is found,
                                      # make_pet_dyes.py, then one smoke boot (null-payload, hidden)
python -m gamelab doctor --confirm-saves   # only if --fix printed AMBIGUOUS save lines and the backup is still what you want
python -m gamelab doctor --hoh1 "D:\Games\Heroes of Hammerwatch" --fix   # HoH1 not found automatically: say where it is
python -m gamelab doctor --no-hoh1    # you don't own HoH1: skip its content, stop asking
python -m gamelab doctor --smoke      # boot null-payload again; a failure names its cause (antivirus, GPU, cores)
python tools/build.py                 # pack dist/HWP-<module>.bin + dist/HammerwatchPlus-All.bin
python tools/hwr_archive.py --help    # low-level archive tool (list/extract/pack HW2R and HWRR)
python tools/icon_art/render.py all   # skill icon ideas in the vanilla style (tools/icon_art/README.md)
python -m planner                     # the class planner in your browser (or planner.cmd / ./planner.sh; planner/README.md)
python tools/import_hoh1.py pets|levels|campaign|classes   # HoH1 content by hand (doctor --fix runs all four)
```

Mods live in `mods/<id>/`. Conventions are in `docs/modules.md`, the archive format in
`docs/archive-format.md`, the script hooks in `docs/hooks.md`.

HoH1 assets are never committed. `tools/import_hoh1.py` writes into gitignored
`hoh1_import/`, and `build.py` leaves it out of packages unless `--with-local`, so each
player imports it themselves.

## License

MIT. Game assets belong to Crackshell.
