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
| `core` | Shared library: settings, save-data extension, networking helper, pet pickup logic. Required by every other module. It also adds a Plants & Herbs section to the Materials tab (seeds and harvested herbs, 8 across), an Eat/Roll action on materials and fish, a warning on orbs that close off other orbs ("Makes unavailable ..." with their icons), and the Mm-hmm! bonus on rare and better hats (every crit plays the merchant's "mm-hmm", for everyone). Extra skill keys: a class with more than three active skills casts the 4th, 5th and 6th on their own keys (default 4, 5, 6; rebind in the Plus tab). The Subclass Picker lists a spec's own skills labelled Active / Passive by their real type. |
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
| `weaponswap` | A second weapon set on a hotkey (default X): a 2 s channel standing still, cancelled by a dodge or a second press. |
| `puzzles` | Puzzle rooms are back in the dungeons (HoH2 ships 88 but never places them), and Heroes of Hammerwatch 1's Constellation puzzle is one of the puzzles they can roll. |
| `stash` | A Sort button on the town stash: by class, then weapon type, then item level. |
| `keys` | HoH1-style keys: every chest but the cursed ones needs one; key drops, the exit guard's General Merchant (keys, bag slots, six trinkets to take into your next run), ace chests, seven red legendaries. |
| `firearms` | The Firearms Specialist class. Guns use a clip that counts down per shot and auto-reloads at 0 (1.6 s; a dodge restarts it); the Reload skill refills it at the end of a cast as long as its recharge (2.0-1.2 s), which a dodge cancels and a full clip refuses, and shows the same icon sweep; mana pays for gadgets. Weapons: rifle (30 rounds, 3-round bursts, no pierce, grenade-launcher secondary) and one pistol item that fits either hand (10 each, 20 dual; a lone pistol fires single shots, dual pistols alternate; rounds leave each gun, 6 px either side). The last 3 rounds (6 dual) click. New characters start with one Service Pistol. Base kit Reload and Frag Grenade (radius 64) with orbs (Explosive Reload, Over-Reload's timed perfect reload on a bar above the health bar, hit with Reload or left click, Stun/Incendiary/Gas grenades); Marksman (Snipe, Critical Aim's Focus stacks) and Demolitionist (Rocket Launcher, Ordinance Hoarder's charges) specializations with their orbs; Assault (Double Barrel Burst, Adrenaline) and Engineer (Deploy Turret, My Turret!) specializations with their orbs. Plan: `docs/design/firearms.md`. |
| `fishing` | Six fishing spots on the town coast (timing minigame), more in the water of run floors' potion wells (a bucket in boss rooms), greyed on the map once fished out. A pirate sells bait, rods and fish traps from the trading post's wreck, later its boat. Fish are swords, sell for bet tokens and can be eaten (100 HP per star). New characters start with no rod or can. |
| `farming` | The town's field grooves become farm plots: food crops and four Holy Herb strains grow per completed run, faster when watered (the farmer sells the can and seeds, the well refills it). Smoke a herb for a buff lasting 10 floors, or roll one into a joint (Materials > Plants & Herbs): an offhand with 5 puffs that a friend with a free offhand can take from you, and smoke that fills the room. |
| `weapons` | Twelve new weapons (ilvl 35, all slots/classes) with fresh modifier profiles on the vanilla visuals and skills. |
| `strongbox` | PoE-style strongboxes: open one, a biome-correct pack (elites possible) spawns, clear it for the box's loot. |
| `abyss` | Abyss cracks: step close and waves crawl out, ending in elites (more in a bigger party); clear them for a reward that grows as the run goes deeper, and the crack closes. |
| `valuables` | Valuables (vases, chalices, gems, furs, scales: the pickups that turn straight into gold) are worth twice their vanilla gold. |
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
nearby kept Morale off.
The Firearms Specialist's clip, reload and guns pass `plan-t14` and `plan-firearms-guns`
(magazines 30/10/20, rounds per click for each loadout, dodge-interrupted reload). Its class
planner also drafts a 4th spec and new orbs for every vanilla class (`docs/design/firearms.md`).
Its Marksman and Demolitionist specializations and the base kit's orbs followed (2026-10-19),
checked by `plan-firearms-a`, `-b` and `-orbs` through a new `gl orb` verb. Placeholder
icons come from `tools/make_firearms_icons.py`. Over-Reload now works on a manual Reload too
(a second press on the mark), and dual pistols throw their magazines one after the other.
Rounds are now small tinted bullets fired on the attack's first frame, and the clip fills
only in the village and on a run's first floor, carrying its count between floors; a
trigger pull on an empty clip reloads (`mod-firearms-clip`). Assault's old Stun Grenade is gone (Double Barrel Burst and Adrenaline remain), and `hwp
firearms sound` auditions firing sounds by ear; the guns, rockets and reload use the sounds
picked that way (reload: unlock, then lever on, or lever off on a perfect). GameLab is pinned to build
25932569 since 2026-10-19. The Engineer (a turret that wears down and that you repair and boost by standing near it)
and Assault's checks pass `plan-firearms-b`; after a rifle or pistol shot the arm stays raised until 1 s without a shot (`plan-firearms-arm`).
The Reload cast is now the whole 2.0-1.2 s recharge (a dodge cancels it, a full clip refuses it) and shows the
automatic reload's icon sweep; one pistol item fits either hand, rounds leave each gun 6 px out, and a held trigger
no longer says "cant" (`mod-firearms-pistols`). The demo has a Skill Trainer, training dummies and a 2560x1440 window, and its whole setup is one
`gl setup` line. Core now puts a dropped item ahead of a vendor for the use key (`mod-core-pickup`).
Rounds now leave the gun's tip (rifle 22 px out, pistols 12), and Snipe costs mana only and shows a red laser dot while it charges (`look-firearms-tips`).
Dual pistols fire every 300 ms with even gaps, My Turret! boosts only within 10 m (60 px: the game's metre is 6 px), Double Barrel Burst hits x1.5-3.5 up close, and Ordinance Hoarder's icon counts every use ready while the slot's ring shows the next charge banking (`look-firearms-batch`, `plan-firearms-b`). The demo has an orb that stays after each pick, its trainer sells every tier, and it stays open four hours, closing early when the game does.
On 2026-10-20 the play-test list was worked through: rifle bursts, single pistol shots, the
Over-Reload bar, a rooted weapon swap, joints, eating fish, fish spots in the wells' water, the
pirate in the boat, a party key pool, abyss rewards by depth, double valuables and puzzle rooms
on most floors (`docs/RE_NOTES.md`, every run cited there). A code review of that work fixed
ten issues, among them co-op keys, a joint puff lost to a level change, and dual pistols
whose spread threw every round off the aim line (they now match the rifle,
`bench-weapons`).
A later code review fixed 15 smaller issues: town units tracked after a
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
python tools/icon_art/render.py all   # skill icon ideas in the vanilla style (tools/icon_art/README.md)
python tools/import_hoh1.py pets|levels|campaign|classes   # HoH1 content by hand (doctor --fix runs all four)
```

Mods live in `mods/<id>/`. Conventions are in `docs/modules.md`, the archive format in
`docs/archive-format.md`, the script hooks in `docs/hooks.md`.

HoH1 assets are never committed. `tools/import_hoh1.py` writes into gitignored
`hoh1_import/`, and `build.py` leaves it out of packages unless `--with-local`, so each
player imports it themselves.

## License

MIT. Game assets belong to Crackshell.
