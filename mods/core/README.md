# core

Shared library every other HammerwatchPlus module depends on. It adds no gameplay.

| File | Provides |
|---|---|
| `scripts/HWP/Core/Log.as` | `HWP::Log(module, msg)` / `HWP::LogError`, `HWP::VERSION` |
| `scripts/HWP/Core/Net.as` | `HWP::Net` request/event bus (`OnRequest`, `OnEvent`, `Request`, `Broadcast`, `Send`) |
| `scripts/HWP/Core/SaveData.as` | `HWP::SaveData::Player/Local/Town/MyTown()` data bags saved under the record's `hwp` key; a bag lives in the record's `userdata`, so it dies with the record |
| `scripts/HWP/Core/Settings.as` | `HWP::Settings::Get*/Set*` local preferences, stored in `g_myTownRecord` (the only town record the game saves; clients only get a copy of the host's `g_currTownRecord`) |
| `scripts/HWP/Core/Commands.as` | `HWP::Commands`: the `hwp` console command. `hwp help`, `hwp version`, `hwp settings`, `hwp get <key>`, `hwp set <key> <value>`; modules add their own with `Register(name, help, handler)` and listen for setting changes with `OnSettingChanged` |
| `scripts/HWP/Core/GearSlots.as` + `gui/playermenu/character.gui` | `HWP::Gear`: extra gear slots in the character screen. The vanilla equipment is a 3x3 grid (main hand, head, off hand / hands, chest, back / rod, feet, can), with the bottom corners and the alt-weapon pair as `hwp-gear-slot` widgets; a module registers a `HWP::Gear::Slot` provider by widget id (`Register`), slots without a provider are hidden. Providers call `Changed()` when what they show changes (a level load does too); the slots reload only then |
| `scripts/HWP/Core/Town.as` | `HWP::Town::Placeable` (a settings-backed town doodad the host spawns; optional `m_locate` finds its spot in this town on every machine, it is placed again after a town rebuild, `Reset()` drops the saved spot), `HWP::Town::ChapelPyreSpot` (the chapel Pyre slot, where the campaign portal and the wave statue stand), `HWP::Town::Kept` (a once-per-load unit to spawn again after a rebuild; `Set(unit)` remembers its producer), `HWP::Town::Ours(u)` (a kept pointer still names a live HWP unit: a rebuild reuses unit ids, so check this before trusting or destroying one), `HWP::Town::PayGold`, and `HWPLocalNPC`, the behaviour of town units every machine spawns for itself (fishing spots, the pirate, farm plots, the well) |
| `scripts/HWP/Core/PickupFirst.as` | `HWP::PickupFirst`: the use key picks up a dropped item before it talks to an NPC or opens a shop, chest or shrine underfoot. The local player's usables are re-sorted every frame with items between -1 (revives, exits) and 0 (vanilla puts items at 1, last) |
| `scripts/HWP/Core/BagSlots.as` | `HWP::Bag`: bought equipment bag slots, 24 + up to 8 per character (`bag.extra` in the HWP data; 1000 g rising to 20000 g, sold by the keys module's exit guard shop or `hwp bag buy`). The character screen's `<hwp-equipmentinventory>` draws every slot you can fill. `HWP::Bag::OnEquip(f)` runs `f(record, item)` before a bag click equips the item (firearms uses it to put a pistol in the off hand) |
| `system/messages.net` | base file + `HWPRequest` / `HWPEvent` messages (declared override, see `module.json`) |
| `scripts/HWP/Core/Cheats.as` | `hwp unlockflags`, `material`, `levelup`, `xp`, `statpoints`, `skillpoints`, `equip`, `spawnmaps`, `finishlevel`, `boss`, `killall`, `god`, `tokens` (bet tokens): copies of the vanilla `cht_*` cheats that work in a level (need `e_cheats 1`) |
| `scripts/HWP/Core/Generator.as` | `HWPOutdoorGenerator`: vanilla `OutdoorGenerator` that picks its base level again on every retry and sets aside a base that failed 10 times in a row (see below) |
| `scripts/HWP/Core/Market.as` | `HWP::Market`: wares (crops, herbs, fish) registered by modules, counted from your HWP data and bag items, sold for gold or **bet tokens** (`bet_tokens` per character; `Tokens`, `AddTokens`, `SpendTokens`, `Sell`, `Price`); `hwp wares`, `hwp sell` |
| `scripts/HWP/Core/MapIcons.as` + `gui/hwp/map_icons.png` | Minimap icons: a dye-pot marker over every dye bucket of a floor (`mapicons.dyes`, default on); the sheet also has the fish and crop icons the fishing and farming units use (`tools/make_map_icons.py`; textures must be power-of-two sized) |
| `scripts/HWP/Core/Materials.as` + `gui/playermenu/character.gui` | `HWP::Materials`: a "Supplies" section in the materials tab for things a module keeps per character (gambler bet tokens, the three fishing baits, farming seeds). Cells are `hwp-material` widgets inside `hwp-materials` (a wrapping grid that grows to as many rows as it needs); a module registers a `HWP::Materials::Material` (icon, count, tooltip title and text) by cell id. Cells without one, or with none in stock, are hidden; hovering a cell shows its tooltip at the mouse (the player menu's tooltip anchor would put it top centre) |
| `scripts/HWP/Core/Options.as` + `gui/hwp/options.gui` + `gui/playermenu/playermenu.gui` | `HWP::Options`: the player menu's **Plus** tab, our settings screen. `playermenu.gui` (declared override) adds the tab button (tab padding 12 -> 8 so four fit) and an `hwp-options-hook` widget that adds `HWPOptionsTab` to the PlayerMenu on its first update. The tab has a row per option id (`hwp-opt-<id>`); a module registers an `HWP::Options::Option` (title, value, `Next()` on click) or a `KeyOption` (click: an `HWPKeyCaptureWindow` (`gui/hwp/keycapture.gui`) goes over the menu, so the menu gets no input, and binds the next key pressed; Esc cancels) under that id, and rows without one hide. A search field at the top filters the rows by title or value as you type (Esc clears it; the console key's ` and ~ are refused). `HWP::Options::TabOpen()` is true while the tab (or a capture) is up: a module polling a raw key skips it then. Tab id `HashString("hwp_options")`. Rows now: `colors`, `swapkey`, `skill4`-`skill6` |
| `scripts/HWP/Core/SubclassPick.as` | **Subclass Picker skill row by type.** The vanilla picker shows a spec's last two skill defs as "Active" and "Passive", wrong for the HWP specs (Sniper's Flashbang and Decoy are both actives, Snipe never shows). Core patches the open picker in place each time it shows another class: the spec's own skills (those its parent class lacks), actives first then passives, each labelled by its real type, up to four slots across the row. Vanilla specs look the same as before. GameLab: slots are `skill-active-name`, `skill-passive-name`, `hwp-pick-name2`..; labels `hwp-pick-label0`..; `gl classskills <classId>` lists the defs it is checked against |
| `scripts/HWP/Core/SkillKeys.as` + `SkillKeysHUD.as` | **Extra skill keys.** The game has three skill buttons and gives the 3rd and every later active spell Skill3, so they all fire on one press. Core swaps the local player's `PlayerTargetingHelper` for `HWPSkillKeysHelper`, whose `GetSkillInput` override gives the 4th, 5th and 6th active their own raw key (Plus tab rows `skill4`-`skill6`, settings `skillkeys.skill4`-`6`, default the 4, 5, 6 keys; vanilla binds 1 2 3 Q E V). The vanilla targeting code then serves them like any skill button; Skill3 fires only the 3rd. Keys are ignored while a text field or the chat has the keyboard and on the Plus tab. `HWPSkillKeysHUDPlayer` replaces the HUD's player bar: more than four skill slots, the extra key's name above each extra skill. Keyboard only (no gamepad buttons are left). `hwp skillkeys` lists the keys and what each casts. GameLab: `gl input ... hwp_skill4` holds the key (GlobalCache `hwp_skillkeys_held`) |
| `scripts/HWP/Core/CoreModule.as` | boot self-checks; prints every mod id's save hash for `gamelab/hps.py` |

## Why character.gui is overridden

The gear grid needs new widgets in the character screen, and a gui file cannot
be merged. Core owns `gui/playermenu/character.gui` (declared in
`module.json`): the vanilla file with the equipment moved into a 3x3 grid and
four `hwp-gear-slot` widgets added (`hwp-gear-rod`, `hwp-gear-can` below the
gloves and the cape, `hwp-alt-main`/`hwp-alt-off` for the other weapon set).
They sit outside `<equipment>` because `EquipmentWidget.DoLayout` fills every
item slot inside it by id. `hwp-gear-label` text widgets (`HWP::Gear::RegisterLabel`) caption the
other set. The file also drops the "Inventory" title bar, moving the tabs up,
and gives the bag view a fourth row (every grid height +27; the window had
22 px spare); a materials-tab Supplies row (`hwp-materials`). Providers: fishing (rod), farming (watering can),
weaponswap (the other set); Supplies: gambler (bet tokens), fishing (bait), farming (seeds). Each module still works without the others; its
slot just stays hidden.

## Settings: the Plus tab and the console

The game's Options menu (main menu and pause menu) runs in the menu script,
which never loads mod scripts or mod gui files, so a mod cannot add to it
(GameLab `probe-options-menu`: a `gui/options/game.gui` override never shows),
and its Controls list is a fixed action table in the exe. Settings with a
row in the player menu's Plus tab (`Options.as`) are changed there; the rest
by console. `hwp set <key> <value>` writes a
`HWP::Settings` value (`true`/`false` -> bool, number -> int, else string) and
notifies every listener, so modules pick the change up live. Replies print
to the console prefixed `[HWP]` (and to the chat log, which shows in a lobby).

Why the console and not `/hwp` in chat: the in-game chat and the pause menu
run in the main menu's script, which loads only the unmodded base scripts and
has no town or players. The console calls `hwp` in the game's script, and a
one-string console function receives the whole rest of the line. The vanilla
`cht_*` cheats are registered by both scripts and the console runs the menu's
copy, which is why `cht_give_material` and friends fail with a null pointer in
a level; `Cheats.as` has working copies.

## Why the outdoor themes are overridden

Vanilla `OutdoorGenerator` picks the base level prefab once and keeps it across
"Failed generation commands, retrying from scratch". When a required prefab set
can never fit on that base (seen: `forest_2` on `base_levels/level_6.pfb` with
`forest_skill`), the game retries the same layout forever until the lobby times
out. `gen-class` is created with `InstantiateClass`, which ignores info.xml
classmaps, so `tweak/missions/themes_{forest,heaven,keep,prison}.sval` and
`themes_heaven.inc` are copied with only `gen-class` changed to
`HWPOutdoorGenerator` (the `.orig` copies are the base files for `build.py --check`).
The boot log shows `generator safety net: HWPOutdoorGenerator`.

## Why messages.net is overridden

HoH2 declares all network messages in one file. There is no merge mechanism, so
the core module ships a copy with two generic messages appended. `tools/build.py
--check` flags the day a game update changes the original.

## Testing

`python -m gamelab run mod-core --mode lab` (`gamelab/scenarios/mod-core.json`) boots
core in town on the `town-paladin` fixture. It asserts these lines and no script errors
in our files:

- `[HWP:core] module created, version ...`
- `[HWP:core] lang check: HammerwatchPlus language file loaded` (not the raw key)
- `[HWP:core] modhash 'core' <n> enabled unpacked`. One `modhash` line is logged per installed mod.
- `[HWP:core] gameplay started; server=yes town=yes ...`

Not asserted yet: `[HWP:core] town record loaded, N hwp key(s)`. The fixture's town has
no save data, so `TownRecordLoad` never fires (`docs/RE_NOTES.md`, 2026-10-17). It needs
a fixture with a saved town.

Extra skill keys (manual / plan checks):

- `[HWP:skillkeys] input helper installed, N active skill(s)` on every spawn of the local
  player (the mod-core run shows it with N = the paladin's actives).
- `gamelab/bots/plan_firearms.py`: `sniper_own_buttons`, `demo_own_buttons`,
  `assault_own_buttons` press Skill3 and each extra key and expect that skill alone to cast.
  `gamelab/bots/plan_classesb.py`: `slice_own_button`, `cloak_own_button`,
  `charge_own_button`.
- By hand: a Sniper with all three doctrine skills casts Snipe on 3 (or V), Flashbang on 4,
  Decoy on 5, each alone; the HUD shows five skill slots with "4" and "5" above the last
  two; rebinding Skill 4 in the Plus tab relabels it.

Subclass Picker skill row (plan checks): `picker_skill_labels` (plan_firearms.py, the three
doctrines) and `<class>_picker_skill_labels` (plan_classesb.py: thief, gladiator,
witchhunter, and the priest / paladin 4th spec) read the row from `gl widgets` and compare
it with `gl classskills` (gamelab/bots/picker_skills.py).
