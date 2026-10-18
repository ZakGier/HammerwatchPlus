# HammerwatchPlus

A modular co-op mod for **Heroes of Hammerwatch II**: quality-of-life and
co-op systems, a gambler in the tavern, pets that level up, Heroes of
Hammerwatch 1 content (ace chests, legendaries, the Forsaken Tower campaign,
HoH1 classes and pets), new classes, fishing and farming in town.

Every module ships as its own mod package, plus an all-in-one build. Everyone
in a lobby should run the same version of the same modules.

## Modules

| Module | What it does |
|---|---|
| `core` | Shared library: settings, save-data extension, networking helper, pet pickup logic. Required by every other module. Also extra skill keys: a class with more than three active skills casts the 4th, 5th and 6th on their own keys (default 4, 5, 6; rebind in the Plus tab). The Subclass Picker lists a spec's own skills labelled Active / Passive by their real type. |
| `gambler` | Higher/Lower card gambler NPC in the tavern. His Sell button buys crops and herbs for gold and fish for bet tokens; he rerolls equipped gear for 2000 gold x item level, or 1 bet token per 5 item levels. |
| `droptrade` | Drop equipment on the ground for friends: a Drop button / Q key next to Destroy in the inventory. |
| `goldpet` | Pet vendor in the Hunter's Lodge selling the Gold Collector cat, with two upgrades (materials and scrolls, then valuables). |
| `laststats` | Last run's stats for the whole party on a notice board by the town fountain. |
| `deathrecap` | Who killed you: top damage sources from the last 10 s, on screen and in chat. |
| `bufftips` | Hover a buff icon to see what it does and how many seconds it has left. |
| `legacy` | HoH1-style class legacy: your best hero of each class buffs every character; one "Title Bonuses" buff lists them, Guild Hall > Titles shows every class. |
| `pets` | Pets level up (kills, pickups, farm crops at the feeding bowl) and learn utility skills; per-pet pickup toggles; all Heroes of Hammerwatch 1 pets in the Pet Shop (imported from your own HoH1 install); pet dyes at the tailor; pets wait outside puzzle rooms. |
| `architect` | Any player can pick and pay for Architect alterations; the host's picks are split across the party. Seven HoH1 challenges discount them, down to free. |
| `chatlinks` | Linked items stay in chat with slot and item level; `hwp link`. |
| `colors` | Colour-blind / high-contrast tints for enemy and friendly projectiles (player menu > Plus tab). |
| `groupcombo` | Party-wide combo bonus that scales with how many players are in combo; brief invulnerability when everyone is. |
| `weaponswap` | A second weapon set on a hotkey (default X). |
| `puzzles` | Puzzle rooms are back in the dungeons (HoH2 ships 88 but never places them), and Heroes of Hammerwatch 1's Constellation puzzle is one of the puzzles they can roll. |
| `stash` | A Sort button on the town stash: by class, then weapon type, then item level. |
| `keys` | HoH1-style keys: every chest but the cursed ones needs one; key drops, the exit guard's General Merchant (keys, bag slots, six trinkets to take into your next run), ace chests, seven red legendaries. |
| `firearms` | The Firearms Specialist class: mana is ammo, reload, grenades; Sniper / Demolitions / Assault doctrines. A doctrine has up to five actives: reload, frag and the doctrine's first skill sit on the game's three skill buttons, the 4th and 5th on core's extra keys (default 4 and 5). |
| `fishing` | Six fishing spots on the town coast (timing minigame), more at the potion wells of run floors. A pirate sells bait, rods and fish traps. Fish are swords and sell for bet tokens. |
| `farming` | The town's field grooves become farm plots: food crops and four Holy Herb strains grow per completed run, faster when watered (the farmer sells the can and seeds, the well refills it). Smoke a herb for a next-run buff. |
| `weapons` | Twelve new weapons (ilvl 35, all slots/classes) with fresh modifier profiles on the vanilla visuals and skills. |
| `strongbox` | PoE-style strongboxes: open one, a biome-correct pack (elites possible) spawns, clear it for the box's loot. |
| `abyss` | Abyss cracks: step close and waves crawl out, ending in an elite; clear them for a reward and the crack closes. |
| `maps` | Three new layouts for the equipment map drops: Goblin Warrens, Sunken Dungeon, The High Court. |
| `mercenary` | Heroes of Hammerwatch 1's mercenary mode: once a class has a level-20 hero, a fresh character of it can enlist, climb the ranks from Private to General for more gold and experience, and die for good. |
| `summons` | Priest Crusaders (and optionally all summons) persist through the loading screen between floors. |
| `campaign` | The Forsaken Tower: the HoH1 campaign (Mines to Battlements, 18 floors, 6 bosses) started from a portal in town. With HoH1 installed, a second version plays the real HoH1 boss rooms and Battlements (`tools/import_hoh1.py campaign`). |
| `wavemode` | Wave Arena: a survival arena started from a statue in town; boss kills raise your arena rank. |
| `classes` | The HoH1 classes HoH2 lacks: Thief, Gladiator, Witch Hunter, three masteries each. Also HoH1-style masteries for the Priest (Smiter) and Paladin (Holy Storm). The Thief's Slice and Dice / Cloak of Shadows and the Holy Storm Paladin's Zealous Charge are 4th actives, cast on core's Skill 4 key (default 4). |

Each module's spec and test checklist is in `mods/<id>/README.md`.

`mods/gamelab-*` are GameLab test harnesses, not player content. `build.py` never packs
them; they are only linked into the GameLab environment.

| Harness | What it does |
|---|---|
| `gamelab-probe` | The `gl` console command channel, read-only state probes, heartbeat. |
| `gamelab-hands` | Action verbs for the `gl` channel (start a mission floor, ...). Requires probe. |
| `gamelab-pilot` | Bot API for the Pilot. Requires probe and hands. |
| `gamelab-reload` | Logs a mark from its constructor, so the `reload-mark` scenario can tell whether an edited script was picked up without a restart. |

## Installing (players)

1. Download the `.bin` files you want from Releases (or `HammerwatchPlus-All.bin`).
2. Drop them into `<Steam>/steamapps/common/Heroes of Hammerwatch 2/mods/`.
3. Start the game, open **Resource Mods** and enable them. Everyone in the lobby does the same.
4. In game, open the console (the key left of 1) and type `hwp help` for the commands and settings.

Workshop uploads will follow once the modules stabilise.

## GameLab

GameLab is the test harness: it boots a sandboxed copy of the game hidden and muted,
drives it through its own scripts (no real input, no focus steals, never touching your
config or saves), and scores what happened. Use the `gamelab` skill to run it.
Before merging to main, run `python -m gamelab run mod-all --mode lab` (every content
mod loaded together; GUI textures must be power-of-two sized or the game won't boot).

The in-game test plan's steps each have a `gamelab/scenarios/plan-*.json` scenario. As of
2026-10-18, every solo step passes in GameLab except Weapon Swap's "only you can pick it up",
which needs a real lobby. The Forsaken Tower now swaps HoH1's bosses and enemies for their
NG+ copies as HoH1 did (the Warden's bomb fan from NG+1, the Vampire Lord's Bat Spray from
NG+2), and HoH1 burst attacks that never fired (the ice trolls', ballista towers', the NG+
Warden's club and ballista) now do. The co-op steps need two players:
GameLab runs one game, and HoH2 only connects through Steam/GOG lobbies. Repeat runs of the
pet scenarios found three more bugs, now fixed: a pet could stall after waiting by a
puzzle, the Gold Collector cat froze on an unreachable pickup, and a farming wild plot
nearby kept Morale off. A later code review fixed 15 smaller issues: town units tracked after a
town reload, the troll groups and HoH1-floor strongboxes on NG+, the cat giving up while
walking around a wall, and the wave statue's spot differing between machines
(`docs/RE_NOTES.md`).
The HoH1-to-HoH2 trinket comparison (missing, modified, new and flat-value trinkets,
grouped by HoH2 set, with shared verdicts) is a private web app outside the repo; its link
is in `docs/RE_NOTES.md`.

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
python tools/import_hoh1.py pets|levels|campaign|classes   # HoH1 content by hand (doctor --fix runs all four)
```

Mods live in `mods/<id>/`. Conventions are in `docs/modules.md`, the archive format in
`docs/archive-format.md`, the script hooks in `docs/hooks.md`.

HoH1 assets are never committed. `tools/import_hoh1.py` writes into gitignored
`hoh1_import/`, and `build.py` leaves it out of packages unless `--with-local`, so each
player imports it themselves.

## License

MIT. Game assets belong to Crackshell.
