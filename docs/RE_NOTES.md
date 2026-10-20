# RE notes: Heroes of Hammerwatch II

Dated findings log. Each entry says how it was measured; "assumed" marks anything not yet
measured. Newest entries at the bottom of each date.

NOTE: PATHS/ENV SPECIFIC NOTES ONLY APPLY TO A SINGLE DEVELOPERS SETUP, OTHER DEVS MAY HAVE
DIFFERENT SETUPS OR INSTALL LOCATIONS.

## 2026-10-17: recon (P1)

**Install.** `C:\Program Files (x86)\Steam\steamapps\common\Heroes of Hammerwatch 2`
(found through the Steam registry key and `libraryfolders.vdf`; `tools/gamepaths.py`).

**Ids and version.** Steam app id `619820`. Build id `25509441`
(`steamapps/appmanifest_619820.acf::buildid`). The game logs
`Build 170: ARCH_64 USING_STEAM RELEASE FINAL` as its second line (`HWR2.exe.log`), and the
window title is `Heroes of Hammerwatch II - B170`. `HWR2.exe` sha256 `6ddd9e7d8fe3…`,
PE timestamp 1790265044. Pinned in `gamelab/build_id.json`; `tools/pin_build.py --show`
compares live to pin, and every GameLab launch refuses with exit 3 on mismatch.

**Engine.** Crackshell's own C++ engine: `HWR2.exe`, `PACKAGER.exe`, `EDITOR.exe`,
`HWR2Toolkit.exe`, all game content in `res/assets.bin`, AngelScript game scripts inside the
archive (extracted to `gamecode/sdk/hoh2/scripts/`). Libraries by file version: SDL2
2.30.7, FMOD / FMOD Studio 2.2.11 (build 130436), steam_api64 1.0.0.1, ozz-animation,
libde265, TinyTIFF. Renderer from the log: `Starting BGFX renderer OpenGL 3.2`.

**Anti-cheat.** None. No `EasyAntiCheat/`, `BattlEye/` or other anti-cheat directory or
launcher wrapper in the install; the only third-party runtime is `steam_api64.dll`.
Consequence: in-process DLL injection is usable (GameLab injects
`tools/bin/hwr2_capture.dll`, below), and scripted mods are the game's own supported path.

**Logs.** `<exe dir>/HWR2.exe.log`, rotated into `<exe dir>/logs/HWR2.exe_<date>_<time>.log`
at the next start. Crash dumps: `<exe dir>/HWR2_<build>_crash_<date>_T<time>__<n>.mdmp`.
Script `print()` goes to the same log.

## 2026-10-17: isolation (P6 item 9)

All measured with copies of the game run from a scratch directory, the user's saves backed
up first (`tools/saves.py backup`) and compared after every run.

- **The exe's directory is the user-data root.** HWR2.exe reads `HWR2.exe.cfg`, writes
  `HWR2.exe.log`, and keeps local saves in `saves/` next to the exe it was started from,
  not the working directory and not the install. A copy of `HWR2.exe` and its DLLs in
  another directory, with the install's `res/` linked in, runs as a fully separate
  install. The log line `Launch options: 1: <exe path>` names the exe that ran.
  First probe, launched from the install exe with a different cwd: it read the install's
  cfg and overwrote the install's `HWR2.exe.log` (no save writes, checked by mtime).
- **Launching the exe directly does not relaunch through Steam.** The game stays a direct
  child of the launcher (Steam already running), so the hidden desktop and job object reach it.
- **`g_save_slot_cloud 0`** keeps saves off Steam Remote Storage. The real cloud saves are
  `Steam\userdata\<account>\619820\remote\saves\`.
- **Save backups leak to the user's profile.** On each save the game also writes
  `%LOCALAPPDATA%\HeroesofHammerwatch2\save_backups\slot_<n>_<date>.hps` (throttled: not on
  every save). It resolves the folder with `shell32!SHGetKnownFolderPath`
  (FOLDERID_LocalAppData), not the `LOCALAPPDATA` environment variable: the exe imports
  `SHGetKnownFolderPath` and contains no `LOCALAPPDATA` string, and a run with
  `LOCALAPPDATA` overridden still wrote to the real folder. One probe file leaked there:
  `slot_7_2026_10_17_T05_58_31.hps` (a lab profile, never the user's data; the user
  decides whether to delete it). Fix: `hwr2_capture.dll` replaces the exe's
  `SHGetKnownFolderPath` import and answers FOLDERID_LocalAppData with
  `GAMELAB_LOCALAPPDATA`. The exe starts suspended, the DLL is injected through
  `CreateRemoteThread(LoadLibraryW)`, and then the process resumes (`NtResumeProcess`).
  Verified: the backup then landed in `<game dir>/appdata/HeroesofHammerwatch2/save_backups/`
  and the real folder was unchanged.
- **`res/controls.cfg` is written into `res/`.** The exe has `res/controls.cfg` and
  `res/controls_default.cfg` strings and a "Saved controls config" message; the log shows
  `Loading control bindings from 'res/controls_default.cfg'`. The install has no
  `controls.cfg`, so nothing has been written there yet. Because a junctioned `res/`
  would carry that write into the install, the GameLab `res/` is a real directory:
  `assets.bin` is hard-linked (`os.path.samefile`), small files are sha256-verified
  copies, and subdirectories are junctions. Every run asserts the install's `res/` is
  unchanged.
- **Workshop subscriptions are still listed** in GameLab runs (`Workshop: Subscribed
  items: 1`, `Resource mod: drop_me.bin`). They are listed but never enabled: mods are
  enabled per save, and the GameLab profile enables exactly the GameLab set (asserted by
  the `mods` probe every run).

## 2026-10-17: windows, input, capture (P3 topology, P6 items 2 and 8)

- **Window topology.** One visible top-level `SDL_app` window titled
  `Heroes of Hammerwatch II - B170`, plus `__wglDummyWindowFodder` and IME windows.
  `v_fullscreen false` opens it windowed at the configured size.
- **`v_resolution` is `WxH`** (`GUI/Options/ResolutionsWindow.as`). `v_resolution 800 450`
  crashed the game with 0xC0000005; `640x360` works (GameLab lab profile).
- **Focus-free input works.** `PostMessage` of `WM_KEYDOWN`/`WM_KEYUP` to the `SDL_app`
  window on a hidden desktop:
  - **Enter** at the main menu starts Singleplayer/Continue;
  - **VK 0xC0** opens the console, `WM_CHAR` types into it, and Enter runs the line (the log echoes `> <line>`);
  - **F** (the default `Use` binding, `res/controls_default.cfg`) opens a chest.

  All of it also works with the window minimized (`ShowWindow(SW_SHOWMINNOACTIVE)`):
  scenario `open-chest-minimized` passed. The real foreground window was sampled every
  50 ms through every run and never changed.
- **PrintWindow returns a blank image** for the OpenGL window on a hidden desktop (no
  compositor). Frame capture is in-process instead: `hwr2_capture.dll` replaces the exe's
  `gdi32!SwapBuffers` import, and on a request file reads `GL_BACK` with `glReadPixels`
  just before the swap (`tools/capture_shim/hwr2_capture.c`). It produced correct 640x360
  and 1024x768 frames.
- ~~Mods do not run in the main menu.~~ **Corrected the same day, see "mod lifecycle"
  below.** Mod modules are constructed at the menu, but nothing ticks there. The front door
  (main menu to session) is still the Enter key, and everything after it goes through the
  `gl` console command.

## 2026-10-17: saves and mods (P6 item 3)

- **`HashString` is MurmurHash3_x86_32, seed `0xf808409c`.** It was read from HWR2.exe build
  25509441 as follows:
  1. The script declaration `uint HashString(const string &in str)` is registered next to a
     function pointer `0x1401b4560`.
  2. That native gets the string and calls `0x1400176f0`.
  3. `0x1400176f0` is the MurmurHash3 x86_32 body with `r8d = 0xf808409c` as the seed
     (`C:\tmp\claude\re\find_hashstring.py` and `disasm_at.py` were the scratch scripts).

  Checked against 57 mod-id/hash pairs the game printed: 57/57. `gamelab/hps.py hash <id>`
  computes it.
- **Mods are enabled per save.** The save header holds a list of `HashString(mod id)`
  (`gamelab/hps.py` documents the layout). The id of an unpacked mod is its folder name:
  the log shows `Adding unpacked mod 'gamelab-probe'`, and `PersistentSaves::IsModEnabled`
  is true after enabling that hash.
- **A graceful quit saves.** `WM_CLOSE` to the game window writes the profile
  (`Saving persistent data for profile <n> to file 'saves/<n>.hps'`) and the process exits 0.
  A brand-new profile after a null-save session is 1714 bytes, version 3, no characters.

## 2026-10-17: script API facts used by GameLab

- **Console commands from a module:** `AddFunction("gl", { cvar_type::String }, fn, 0, help)`.
  A one-string function receives the rest of the line.
- **Materials:** `PlayerRecord.GetMaterial(type)` reads the **town's** store
  (`g_myTownRecord`) while in town, and the character's own `materials[]` on a mission
  (`Behaviors/Actors/Player/PlayerRecord.as` `GiveMaterial`/`GetMaterial`). A probe
  reading `record.materials[]` in town sees zeros after looting (measured, open-chest run 1).
- **No generic reflective getter:** `Reflect::` has types, properties and
  `PropertyInfo.Set`, but no way to read an arbitrary property's value. The inspector must
  be code-generated from the class sources (P6, open).
- **Loot table `cache_wood` does not exist** in this build (`items/chests/cache_wood.unit`
  names it; no `tweak/loot/*.sval` defines it). GameLab uses `cache_bronze`.

## 2026-10-17: mod lifecycle (correction) and town saves

- **When mod code runs.** Measured on run `20261017-063419-mod-core-lab`, with a profile
  that enables `core` and the GameLab mods.
  - The engine logs `Adding unpacked mod '<id>'` at boot and again at `StartLoadMenu
    levels/town.lvl`. The main menu is the town level.
  - The module constructors run while the menu level loads (`Making Module ...`). The probe's
    `boot` event and `[HWP:core] module created` were both logged before `Started menu level`.
  - `UpdateFrame` ticks only once the gameplay session starts. The probe's first heartbeat
    follows `Starting session` (after the posted Enter).
  - An earlier note said mods do not run in the menu. That came from a profile with no mods
    enabled, and it is wrong: constructors run there, frames do not.
- **A fresh character's town has no save data.** On the `town-paladin` fixture the session
  logs `Started with null save`. `TownRecord.Load` returns before `Hooks::Call("TownRecordLoad")`
  when the save is null (`gamecode/sdk/hoh2/scripts/Town/TownRecord.as`). So core's
  `town record loaded` line cannot appear on that fixture. Assumed: it appears once a town
  save exists (after a run or a town save point); not measured yet.

- **`Modules::Module.Load` is gated on a session save.** `AGameplayGameMode.Start` calls
  `m_modules[i].Load(modData, sMode)` only when the session save is non-null and holds a
  dictionary under that module's `m_id` (`gamecode/sdk/hoh2/scripts/GameModes/AGameplayGameMode.as`,
  lines 143-154). A fresh town session logs `Started with null save`, so `Load` never runs.
  Consequence measured on `mod-campaign` (run `20261017-064110-mod-campaign-lab`):
  `mods/campaign` runs its self-check from `Load`, so on a fresh town it never logs
  `self-check done`. The same holds for any HWP self-check placed in `Load`.

## 2026-10-17: mod load checks (`gamelab/scenarios/mod-<id>.json`)

These replace `dev_check`. Each one boots one mod plus its `requires` on the
`town-paladin` fixture and asserts:
- the self-check lines its README names;
- still in town;
- no script errors in our files (`gamelab/logparse.py`).

The checks were validated against a deliberately broken mod: the run fails and names
`Broken.as:5:11 No matching symbol`.

- **PASS (20 of 26):** abyss, architect, bufftips, chatlinks, classes, colors, core, deathrecap,
  droptrade, farming, firearms, fishing, goldpet, groupcombo, keys, legacy, pets,
  strongbox, summons, weaponswap. The keys README named `Making Module hwp-keys`; the
  engine logs `Making Module HWPKeysModule`. README and scenario are fixed.
- **FAIL, self-check never fires on a fresh town (verified gate, see above):**
  - campaign, maps, weapons and wavemode run their self-check from `Module.Load`.
  - None of the 24 scenarios logged a script error. These four mods may well be fine,
    but they cannot report it on this fixture.
  - Fix options, the user's call: move the checks to the constructor, or add a fixture
    with a saved session.
- **FAIL, fixture content:** gambler spawns only when the town has a tavern
  (`GetVariationOnBuilding(HashString("tavern")) >= 0`). Assumed: the fresh fixture town
  has none, and that branch returns without a log line.
- **FAIL, unexplained:** laststats. `SpawnBoard` logs `spawned the notice board` 500 ms of
  frames after start when `g_inTown && Network::IsServer()`, and the line never appeared.
  Not diagnosed. Next step: probe `g_inTown` per heartbeat from tick one, rather than
  guess. Candidate: the first frames tick on `PickCharacterWindow` before town is set up.

## 2026-10-17: the Pilot, the pathfinder, the console channel

Verified means measured on the pinned build (run id or source line). Assumed is labelled.

**Input and the run loop**
- **The engine hands out more than one `GameInput`.** Measured `buffers: 2` with the
  `controller` verb. A hold written into one object kept moving the player whenever the
  other became current again (hands-release 20261017-150922..151323). gamelab-hands writes
  every object it has seen (`mods/gamelab-hands/scripts/GameLab/Input.as:55-60`).
- **The next floor is preloaded in its own script context, which constructs every mod
  module again.** Those log lines carry `[preload]` (pilot-consumables 20261017-152746),
  and `session.py` tags them so a preload `boot` is not read as the level change.
- **The game steps a fixed ~33 ms of scene time per frame, at ~30 frames a second in the
  lab box** (timescale 20261017-175222: 3663 scene ms over 111 frames), although
  `v_fps_limit` is 60.
- **`g_timescale` only changes with `e_cheats` on**, which the engine allows in modded
  games (timescale 20261017-175329: 4x gave 14.8 s of scene time in 3.7 s).
  - It is not a test accelerator. At 4x, game-ms timers ran 4x but the player moved no
    farther per frame (0.6-3.6 units, against ~3.2 at 1x): the exit intent timed out four
    times (floor-soak 20261017-175501).
  - The `timescale` verb stays, labelled measurement-only.
- **Setting `CVars::ChtGodmode` from a mod did not stop damage** (20261017-155134).
  Cause not diagnosed. Assumed: the mod's `CVars` namespace is a separate copy of the
  game's.

**Character facts used by the fixtures**
- **The level cap is 20**, reached at 1301032 xp (fixture-ranger 20261017-163304 reads
  back level 20).
- **Enemies scale with NG+ only, not with player level**
  (`Behaviors/Actors/Enemies/CompositeActorBehavior.as:335-337, 718-719`).
- **Potion charges come from the apothecary's `potion-charges` upgrade.** Steps 0-4 take
  the player from 1 charge to 5 (`Town/UpgradeShop.as:139-150`; fixture readback
  `potionCharges 5`).
- **`RollQuality` never rolls a quality on a mask without the Common bit.** It tests
  `mask & Common != 0`, which binds as `mask & (Common != 0)`
  (`EquipmentGenerator.as:15`). Measured: rare asked, quality 2 given
  (fixture-ranger 20261017-151727).
- **A refused `Equip` returns the item itself** (`MayEquip`: level or attribute
  requirements). The `equip` verb treats that as failure.

**Exits**
- **`LevelExitAreaNext` triggers only for a player inside one of its `Areas`.** Each area
  is a sensor (`:Physics_Circle`) offset from the exit unit. Measured offsets:
  - (-72,-120) on one exit (exit-areas 20261017-162406, -162451);
  - (+134,-74) on another (exit-probe 20261017-170654).

  So the offset depends on the exit's orientation. The unit's own position is not
  walkable. Standing in the sensor makes the exit the top usable, and Use loads the next
  floor.
- **Every floor sampled had exactly one enabled exit**, plus one disabled one
  (exit-probe 20261017-170654, -170727).

**The engine pathfinder (`g_scene.Pathfind`), synchronous**
- **No per-frame budget.** 2000 identical calls in one frame all answered, also after
  2000 failing far calls in the same frame (pathfind-budget 20261017-170150).
- **The diameter argument (0, 4, 8, 12, 24) changed no answer** (pathfind-budget
  20261017-170356). Neither did maxDistance or maxRange (pathfind-probe 20261017-153815).
- **Answers are geometric.** A target inside trees or water fails at any distance. A long
  route can fail although both of its halves answer (pathfind-probe 20261017-153509).
  The Pilot's `NavRoute` (A* over short Pathfind legs) covers that case.
- **The Pilot's planner routes from every physically free point it samples.** Measured
  on four layouts (route-sweep 20261017-180034, -180109, -180142, -180225). Points that
  overlap a solid body are skipped, since a player cannot stand there; unit-0 hits are
  level collision without a unit.
- **Two planner bugs were found and fixed:**
  - The search grid was too small for a 6850-unit spawn-to-exit distance
    (pilot-crosslevel 20261017-171409).
  - A player on a pond bank sat in a nav pocket (3 expansions), and stepped out of it
    (pilot-crosslevel 20261017-171446).
- **Mid-floor routing can fail after fights where it worked from the spawn.** In
  pilot-crosslevel 20261017-172902, spawn -> exit no longer routed and neither did
  here -> spawn. The same layout's answers held steady when idle for 30 s and after
  cull (nav-drift 20261017-173940).
  - Assumed cause: units standing in passages. Not verified.
  - Seen again in floor-soak 20261017-184334 sample 1. At (2042,617), 200 units south of
    the exit's stand point, nothing routed:
    - stand → anywhere: 3 expansions;
    - spawn → stand: failed;
    - here → spawn: failed, along the way the player had just walked.
    No enemy was within kite range.
  - **What can change the graph (verified from data, not yet tied to a run):** a unit's
    `<collision static="true">` blocks nav unless it says `nav-block="false"`. In the
    hoh2 units, 1408 static collisions carry no nav-block attribute, 18 say false and 2
    say true. The exe also has a `dirty_nav_graph` string (`hwr2_api_strings.txt`).
  - Assumed: static-collision units that spawn or die mid-floor rebuild the graph. Not
    yet measured; floor_runner now records the units near the cut and waits 5 s
    between retries, to tell a pending rebuild from a lasting blocker.
  - The exit intent now walks to the reached point nearest the exit and plans again
    (partial routes).

**The console channel**
- **Every gl line goes through the console: open, type, Enter, close.**
  - The console key is read per frame. Opening, typing and closing inside one frame does
    nothing at all (console-bench 20261017-181238).
  - The console also slides shut over more than 70 ms (console-trace 20261017-183130).
    An opening key during the slide is lost: every second line vanished at 70 ms
    (console-bench 20261017-182614), none of 90 at 150 ms (-183226).
- **Timing now used:** two frames after opening and after Enter, and 150 ms before the
  next opening. That is 291 ms per line, against 770 ms with the old fixed sleeps.
- **The faster timing put the console into the screenshots.** The blind observer of
  open-chest 20261017-190827 read a console panel over the top fifth of `end.png`, which
  no probe reports.
  - Measured on top-band luminance: about 25 in every shot of that run, against 73-77 in
    the older runs (20261017-140030, -064949).
  - Two plain town frames 0.5 s apart "differed by 31%" in watch-overlays 20261017-190809
    for the same reason. That was the console, not the scene.
  - Fix: `Session.shot` waits 0.25 s after the last console close.
    - console-slide 20261017-191646: the panel is in a shot taken as the reply arrives
      (top band 26.5) and gone 100 ms later (77.6).
  200 lines, 0 lost (console-bench 20261017-183348).
- **A line typed while a level loads can vanish.** The game echoes every line it runs
  (`> gl <id> ...`), so `gl_cmd` retypes a line that went unechoed for two heartbeats.
  This happened once per mission re-entry and was recovered each time (-183348).
- **One typed line of 1985 characters ran whole** (console-bench 20261017-183645).
  The fixture readback now goes out as one `multi` line: 0.5 s, down from ~15 s.

## 2026-10-17 (evening): breakables, travel, death
- **Breakable debris closes passages.** Verified from source and telemetry:
  - `doodads/terrain/castle_debris_pile_wood_noloot.unit` has a `Breakable` behaviour. Each of its
    scenes has `<collision static="true">` with no `nav-block` opt-out, so it blocks nav.
  - `m_health` defaults to -1 (`Breakable.as:31`): one hit breaks it.
  - floor-soak 20261017-192513 sample 0: every route ended near -125,971. The `bodies` probe
    toward the exit found that debris pile at 0,904. Four 20 s kites and a far-enemy kite later the
    passage was still cut.
  - Change: `TargetGone` counts a live Breakable as a target, so `attack <unit>` smashes it. A new
    read-only verb `breakables [radius]` lists them, and floor_runner attacks the nearest three
    within 250 before kiting.
  - **Assumed, not yet verified:** that the ranger's projectile hits the debris (its circles are
    `aim-through="true"`). The next soak measures it (`retries[].broke`).
- **Idle packs cutting the graph: not supported.** The far-enemy kite killed its target
  (boar, sample 0) and the route stayed cut. Sample 3 of the same run: every far enemy was
  "unreachable (stuck at 290,329)". The beetle-pack hypothesis from floor-soak 20261017-191104
  is unconfirmed; the far kite remains as a fallback.
- **Travel graph.** `learned.json` is written only by `"explore": true` runs. pilot-explore
  20261017-191702 learned forest_1 -> forest_2 (graph 1511afe5 -> 199da2bc). Scenario runs
  report `new_edge` without writing (pilot-crosslevel 20261017-191834). An unknown transition
  is `no_route` in 19 s (20261017-190905).
- **Death.** `DeadMenu`'s MenuAccept (Return) calls `Revive`: ResetPlayerHealthMana, SpawnPlayer,
  AbortMission -> town (decompiled). floor-soak 20261017-192111 stopped with "no mission
  heartbeat" after a death because nothing pressed it. `floor_soak.enter()` now presses Return
  on DeadMenu. Not yet exercised: 192513 had no deaths.
- **Ruled out:** the loot toast missing from end frames. The probe reports two `loot_log`
  announces at the end of open-chest 20261017-192415, and the blind observer saw none. A crop
  shows a faint grey "Got" at the style's anchor (bottom-right, grey 0.5, 11 px). Low contrast,
  not absence.
- **Debris breaking verified** (supersedes "assumed" above). In floor-soak 20261017-193859 the
  ranger broke `castle_debris_pile_wood` and the route moved on (sample 1, 476,-1651 -> 730,-1722).
  The soak passed 3 of 4. Crates and chairs were mostly "unreachable", so debris is now tried
  first and failed units are skipped. pilot-floor 20261017-194552 PASS. The next soak
  (20261017-194740) was interrupted by the user, leaving a stale lock: no process was alive, so
  `gamelab reset`.
- **Mod load checks: 27 of 27 pass** (20261017-194937 … -195451). The six earlier failures pass
  with their self-check log lines present. Cause not traced.
- **P6b paused** at the user's request (2026-10-17), to be walked through together.

## 2026-10-17 (night): watch-mode focus (P6 items 1 and 1′)
- **Who took the foreground in 20261017-195821.** pid 25096 was `HWR2.exe` itself, the
  `harness.start` pid. The empty image name was a sampler bug: it resolved names at
  `report()` time, after the game had exited. `ForegroundSampler` now records at each switch
  the image, window class and title, wall-clock time, the window under the cursor and which
  mouse buttons are down.
- **The game makes no activating call after its window is shown.** HWR2.exe imports none of
  ShowWindow, SetWindowPos, SetForegroundWindow, SetActiveWindow, SetFocus or CreateWindowExW.
  SDL2.dll (2.30.7) imports all of them (`objdump -p`). The shim now hooks them in SDL2.dll's
  import table and logs each call with the foreground before and after.
  - In 20261017-200502 (logging only, old behaviour) SDL made exactly one activating-capable
    call: `ShowWindow(hwnd, SW_SHOW)` 0.5 s after injection. The foreground did not change,
    because this launcher (a non-foreground agent shell) has no foreground rights.
  - The only other call was `ShowWindow(0)` at exit.
  - In 195821 the two switches to the game came 15 ms and 31 ms after real input, at about
    +3 s and +12 s after injection. That is not when SDL's call happens.
  - The game log of 195821 shows the human drove the menu: `MainMenuGameMode::MenuBack` at
    19:58:37 and :45, then `Starting session` at :46. So the foreground went to the game
    through the user's own input to its window or taskbar button. Which input it was is
    inferred, not measured: the sampler did not record the cursor then.
- **Measured once the cursor was recorded: 20261017-200812.** At 20:08:27.323 there was a
  left click on `explorer.exe` (the taskbar) and the foreground went to 0. At 27.579 it became
  the game's `SDL_app`. No hooked call took the foreground. So the shell activated the
  window on a taskbar click, even though the window was already `WS_EX_NOACTIVATE`
  (with `WS_EX_APPWINDOW` added, which gave it a taskbar button).
- **Fix** (`tools/capture_shim/hwr2_capture.c`, `gamelab/session.py`, `gamelab/runner.py`,
  `gamelab/winproc.py`). Watch mode sets `GAMELAB_NO_ACTIVATE=1` for the game.
  - The shim gives SDL's top-level windows `WS_EX_NOACTIVATE`. With no `WS_EX_APPWINDOW`
    they get no taskbar button, so there is nothing for the shell to activate.
  - SDL then shows the window `SW_SHOWNOACTIVATE`: the shim log shows `ShowWindow(..., 4)`,
    where it was 5 before.
  - Whenever another process owns the foreground, the shim rewrites activating
    ShowWindow commands to their NOACTIVATE/NA forms, adds `SWP_NOACTIVATE` to SetWindowPos,
    and refuses SetForegroundWindow and SetActiveWindow. This covers foreground rights
    inherited from a console launch, and SDL raise calls later in the run.
  - At the first frame (the first heartbeat) the runner clears `WS_EX_NOACTIVATE` and adds the
    taskbar button with `ITaskbarList::AddTab`. Nothing is activated or raised
    (`harness.allow_activation`: `ex 0x8000110 -> 0x110`, `taskbar_button: true`).
  - Lab mode is unchanged (`no_activate=0`); the hooks only log there.
- **Runs.**
  - null-payload watch 20261017-201214 and -201234: PASS, zero foreground switches for the
    whole run, first frame at 9.8 s and 9.3 s.
  - null-payload lab 20261017-201253: PASS.
  - open-chest lab 20261017-201305: PASS.
- **Assumed:** a real click on the loading window does not activate it. That is the documented
  `WS_EX_NOACTIVATE` behaviour, untested here because GameLab sends no real input. Also
  assumed: the taskbar button appears after AddTab (it returned S_OK).
- **Posted Enter lost at the main menu.** Seen in 195821 and 200812, the two runs where the
  human was using other windows: no `Starting session` followed it, and 200812 failed
  "never reached phase town". Cause not established; assumed to be long frames while the
  window is occluded. `Runner.boot` now waits up to 5 s for `] Starting session` and re-sends
  Enter up to 3 times (`harness.enter_lost`). The retry has not fired in a run yet.

## 2026-10-17 (night): fresh-clone readiness (`python -m gamelab doctor`)

- **No managed code to decompile.** All 12 PE files in the install root (HWR2.exe,
  EDITOR.exe, HWR2Toolkit.exe, PACKAGER.exe and the DLLs) have an empty CLR data
  directory (pefile, `DATA_DIRECTORY[14]`), so they are native and ILSpy does not apply.
  The readable game logic is the AngelScript that `bootstrap.py` unpacks with the
  patched PACKAGER copy in `tools/bin/`.
- **The manifest no longer hashes the shim stamp.** `tools/bin/hwr2_capture.build.json`
  records the gcc version, so `bootstrap.py --verify` failed on any machine with a
  different gcc. It is now excluded from the hash, like the DLL. `--verify` instead checks
  that the stamp's `source_sha256` matches `tools/capture_shim/hwr2_capture.c`.
  `gamelab/manifest.json` was re-recorded: only the `tools/bin/.` group changed
  (10 to 9 files), build 25509441.
- **Save backups are confirmed per machine.** `saves.verify()` compares the real saves
  against the manifest and never re-reads the copies. The new `saves.intact()` re-hashes
  the copies; `restore` refuses a damaged backup. Confirming runs the following, then
  writes `saves-backup/confirmed.json`:
  - the sandboxed selftest;
  - a backup;
  - `intact` on that backup;
  - `verify` against the real saves.

  The launcher preflight and `deploy.py modded-prod` refuse until the stamp exists, the
  save dirs still resolve to the same paths and the stamped backup re-hashes.
  `tools/saves_selftest.py` covers all three cases. It also creates `C:\tmp\claude`,
  which it used to assume existed.
- **Confirmation is automatic unless it is ambiguous.** `doctor --fix` confirms by itself
  when `assess_saves()` finds nothing ambiguous:
  - files exist;
  - the dir the player's config writes (`g_save_slot_cloud`) has files;
  - no other Steam account holds HoH2 saves;
  - no unknown `save*` dir in the install holds files.

  Anything else prints `AMBIGUOUS:` and needs a person (`--confirm-saves`). A person
  asked on an unambiguous machine adds nothing and learns to click yes.
  - `tools/doctor_selftest.py` covers seven cases on a sandbox Steam root (20 checks,
    green). The new overrides `HWP_STEAM_DIR` and `HWP_LOCALAPPDATA` exist for it.
  - The install's empty `save/` dir is not ambiguous; it would be if it held files.
    Which dir the game uses with `g_save_slot_cloud 0` is still measured only for
    GameLab's own copy (`saves/`).
- **Hazards on a new machine, checked by doctor, assumed and not hit here.**
  - A repo on another drive from the Steam library: `os.link` of `res/assets.bin`
    fails across volumes.
  - Steam not running: the directly launched exe needs the client (see above).
  - Saves under a second Steam account on the same PC: only the install's LastOwner
    account is backed up. doctor lists the others as uncovered.

## 2026-10-17 (night): doctor makes the local content too (HoH1, class units)

- **HoH1 discovery goes further, then asks.** `gamepaths.find_hoh1()` order:
  `HWP_HOH1_DIR`, then the Steam appmanifest 677120 in any library, then the path the
  user gave (`tools/paths.local.json`, gitignored), then a sibling of the HoH2 install,
  then every library's `steamapps/common/`. Every candidate except the env override must
  have `HWR.exe` + `res/assets.bin`. bootstrap and import_hoh1 use the same function.
  On this PC HoH1 is in another library (`G:\SteamLibrary`) and is found by its
  appmanifest (verified: `python -m gamelab doctor`, real repo).
- **Not found and no answer means doctor is NOT green.** The HoH1 row says `ASK THE USER`
  and names the two answers: `doctor --hoh1 "<dir>"` (validated, persisted) or
  `doctor --no-hoh1` (persisted; HoH1 content is then reported as skipped).
- **`--fix` makes the gitignored content a fresh clone lacks.** It reruns bootstrap when
  HoH1 is known but `gamecode/sdk/hoh1/` is missing (`--verify` treats that tree as
  optional). It runs `tools/class_units.py` when a copy differs from what it would write.
  It runs `import_hoh1.py pets|levels|campaign|classes`, each only when its output files
  are missing and never with `--force`. The importers do not read each other's output.
  A `mods/campaign/hoh1/` without the `.hwp-generated` marker is reported and left alone.
- **Fixed: `import_hoh1.py levels` crashed on the PACKAGER base.** Its HoH2 probe level
  (`levels/boss_arista.lvl`) is SValue XML in the PACKAGER unpack, not binary
  (`unsupported SValue tag 0x3c at offset 8`). `decode_level` now parses XML when the
  data starts with `<`. Verified: 32 probe script types, 0 unresolved; the import writes
  48 files.
- **Verified on a fresh clone** (`C:\tmp\claude\doctor_e2e\run_e2e_hoh1.py`, 30/30
  checks). Setup: a sandbox Steam with no HoH1 appmanifest and no library list, the real
  HoH2 install, and copies of the saves.
  - `--fix` exits 2 with only the HoH1 question open (bootstrap and class_units ran).
  - `--hoh1 G:\...\Heroes of Hammerwatch` persists the path. `--hoh1 <HoH2 dir>` is
    rejected.
  - `--fix` exits 0 in 55 s: hoh1 extraction (10990 files, matches the manifest) and all
    four imports.
  - A second `--fix` changes none of the 29257 files.
  - Real saves, the real `tools/paths.local.json` and the HoH1 install are unchanged.
- `tools/doctor_selftest.py`: 40 checks, green (21 new HoH1 discovery checks, sandboxed
  through `HWP_PATHS_LOCAL`).
- **Independently re-verified, in the game** (`C:\tmp\claude\doctor_e2e\validate_hoh1.py`,
  34/34 checks). It used another fresh clone with the same sandbox setup and repeated the
  flow above. It then went further:
  - `--hoh1` with a missing dir or the HoH2 dir saves nothing.
  - The generated files are all gitignored.
  - The imported content loads in the game. mod-pets 20261017-215458, mod-campaign
    20261017-215510 and mod-classes 20261017-215522 all PASS in lab mode with the HoH1
    files in the mod folders. Their game logs have no error lines on `hoh1` or `hwp`
    paths. The runs were in the clone, which is deleted.
  - `build.py --with-local` packs `hoh1/` into HWP-campaign.bin,
    `players/pets/hwp/` into HWP-pets.bin and the class art into HWP-classes.bin.
  - The levels fix is equivalent to the binary path: `level_refs` of `boss_arista.lvl`
    decoded from the install's binary archive equals the result from the XML unpack
    (1441 placed, 112 scripts).
  - **Assumed:** the game *uses* each imported item. No scenario opens the Pet Shop or
    plays a HoH1 floor; the scenarios prove a clean load only.
- **Assumed, not tested:** the sibling and library searches against a real Steam layout
  (only sandboxed); a HoH1 version other than this machine's. Its `gamecode/sdk/hoh1`
  hash would differ from `gamelab/manifest.json`, so `bootstrap.py --verify` would fail
  there.
- ~~**Not covered:** `tools/make_pet_dyes.py` output~~: covered since, see the next section.

## 2026-10-17 (night): doctor makes the pet dyes and smoke-boots the machine

- **Pet dyes.** `tools/make_pet_dyes.py` now writes `dye/.hwp-generated.json` with its own
  sha256, the pets it made and the sha256 of every source unit and sheet. `--verify` (and
  `problems()`) reports missing copies, a changed generator, a changed source or a pet
  whose source appeared since (the HoH1 import adds 21). The dotfile never packs
  (`packable_files` skips dot-parts). doctor runs it after class_units and the HoH1
  imports, also when HoH1 is declined (the 7 vanilla pets only need `gamecode/sdk/hoh2`).
- **Smoke boot.** Once every non-content row is green, `doctor --fix` runs `null-payload`
  in lab mode (`--smoke` forces it). A pass goes to `gamelab/smoke.local.json` (gitignored)
  keyed by build id, shim source hash, `os.cpu_count()` and the display adapters
  (registry display class `DriverDesc`). A change to any of them asks for a new boot.
  `explain_smoke()` maps a failure to a plain cause: a refused shim (antivirus), the
  renderer not starting (log has `Opening SDL window`, no `BGFX initialized`), blank
  shots, a deadline (shown with "N of M cores"), a window leaking to the input desktop,
  no game log, the probe not booting, isolation checks, or user files changed.
- **A failed boot leaves the lock dirty.** Verified: with a garbage shim the game is
  killed and `teardown.json` records `pass 1 exited cleanly: exit code 1`, so the next run
  is refused with exit 4. doctor records the failed run in the smoke stamp. Before its
  next boot it runs `python -m gamelab reset` only if the dirty teardown is that same run
  and no lock is held. Any other dirty teardown is still left for a person.
- **Verified on a fresh clone** (`C:\tmp\claude\doctor_e2e\run_e2e_smoke_dyes.py`, 28/28;
  sandbox Steam with copies of the saves; the first attempt, 23/27, found the two bugs
  fixed above: the dye row hid its reason, and the dirty teardown blocked every later boot):
  - `--fix` with HoH1 unanswered: dyes for 7 pets, smoke PASS in 14 s on the hidden desktop
    (run 20261017-222209: focus and no-leak assertions and `shot town` pass).
  - `--hoh1` + `--fix`: dyes regenerated for 28 pets, no second boot; a second `--fix`
    rewrites nothing and boots nothing; generated files all gitignored.
  - An edited HoH1 pet unit: plain doctor says `1 sources changed`, `--fix` remakes them.
  - A garbage `hwr2_capture.dll`: `--smoke` reports the refused shim and names antivirus
    and the dll. Shim restored, `--fix` resets its own dirty teardown and passes.
  - A scenario with an already-passed deadline: reported as too slow, "gets 14 of 16 cores".
  - Real saves byte-identical, HoH1 install and the real repo's stamp unchanged.
- `tools/doctor_selftest.py`: 78 checks, green (every `explain_smoke` branch, the stamp,
  the gating, the reset rule, the dye staleness cases on a sandbox).
- **Assumed, not tested:** the GPU branches (no-GL, blank frames) and the window-leak
  branch on a machine that actually fails them. The causes are mapped from the log lines
  and assertions a passing run shows, plus the selftest. The real antivirus case
  (a refused LoadLibraryW) was reproduced only through a broken dll.

## Merge of main into gamelab-pilot (2026-10-17): what GameLab caught

- **A non-power-of-two GUI texture is fatal at boot.** Verified (run
  20261017-225009-mod-fishing-lab, `pass1.HWR2.exe.log`): `gui/hwp/bait.png (class
  TextureLoader): Texture sizes (48x16) should be power of two`, then `main menu never
  loaded`. Fixed by padding right/bottom with transparency so sprite rects are unchanged:
  `mods/fishing/gui/hwp/bait.png` 48x16 -> 64x16, `mods/farming/gui/hwp_seeds.png`
  117x13 -> 128x16. Both PASS afterwards (225242 fishing, 225254 farming).
- **Malformed `.gui` XML is fatal too.** Verified (run 20261017-224728-mod-fishing-lab):
  `gui/hwp_pirate.gui (class GUILoader): XML error! invalid closing tag name`. main had a
  stale copy of the old button layout plus an extra `</panel>` after the new one; removed.
- `mods/colors/gui/options/game.gui` has a duplicate attribute on one `entry-selector`
  (a strict XML parser rejects it); the game's loader accepts it (mod-colors PASS, 225344).
- New `mod-all` scenario: all 26 content mods together in town, clean log. PASS
  (20261017-225415-mod-all-lab). Run it before merging to main.
- **Second merge (ddf944c, pirate follows trading post).** Checked against the pinned
  prefabs: `trading_post.sval` uses `tier_0.pfb` as `unbuilt-prefab` (variation -1) and
  `tier_N.pfb` for variation N-1, so `GetVariationOnBuilding + 1` is the prefab tier.
  `tier_0`-`tier_2` have `boat_small_wreck` at 320,-112; `tier_3`+ have none. The
  material trader is at ~380,-66.8 in `tier_1`-`tier_5` (absent from `tier_0`, where the
  code falls back to the plot origin). In run 20261017-230737-mod-fishing-lab the
  unbuilt fixture town puts the pirate at -1222,142 = plot + (314,-114), on the wreck.
  **Assumed, not tested:** the re-place after an upgrade (`WatchCoast`), since no fixture builds
  the trading post. `import_hoh1.py pets --force` produced the candle body
  (flame origin y +9, lights -9); mod-pets and mod-all PASS (230749, 230812).

## 2026-10-18: test-plan pass findings

- **A new profile's town is not saved, and HWP settings with it.** `TownRecord.Save`
  returns false when the town has no buildings, no town flags and no materials
  (`scripts/Town/TownRecord.as:333`), so `SavePlayerAndTown` writes no town and the
  `TownRecordSave` hook never runs. Measured on `plan-t2` (20261018-033859): a preset set
  in town was gone on the first floor, and `deathrecap.chat` was unset after a restart.
  Core now writes settings through `HWP::SaveData::MyTownForWrite()`, which sets an
  `hwp_town_data` town flag first (not net-synced; vanilla never reads it). After the fix
  both survive (20261018-034519).
- **Posted mouse messages do not reach the game.** A posted `WM_MOUSEMOVE` and click
  left `GameInput` unchanged: aim, mouse position and the death recap's hover test all
  stayed the same (probe 20261018-034929). The engine reads the cursor itself. Steps that
  need a hover or a click therefore stay manual.
- **`dictionary.set` keeps a temporary by reference.** Measured with a probe on
  `plan-t4` (20261018-035113): `d.set(key, a + b)` or `d.set(key, true)` stores a value that
  later reads as garbage (a key count of 322810098 after "+2 gold"), while
  `int n = a + b; d.set(key, n);` stores 2 and survives function calls. Vanilla
  `PlayerRecord.AddKeys` does `keys.set(key, currNum + num)`, so every vanilla key change
  (`Chest::Use`, the `GiveKey` effect) corrupts the count. The keys module has its own
  `HWP::Keys::AddKeys`/`SetKeys` with named locals, and resets corrupt counts at level
  start. Summons and GoldPet were changed to the same pattern. Vanilla `Save`/`Load` use
  named locals and are unaffected.
- **A run's end state is gone by the time Start runs.** Back in town the order is:
  - module constructors, before the character loads;
  - `PlayerRecord.Load` sets `currMissionState` (~line 902) and `statsRun` (1288), then
    calls `Hooks::Call("PlayerRecordLoad")` (1299);
  - `TownGameMode.PostStart` builds `MissionEndMenu`, whose constructor sets
    `currMissionState` to None and calls `ResetForNewMission`;
  - `GameModeStart`, where HWP's `ModuleStart.Start` runs.

  So only `PlayerRecordLoad` sees how the run ended. Before this was found, a failed run
  gave no laststats snapshot, and farming logged "the run was not finished (state 0)".
  laststats, farming and mercenary now read the state there. A revive from the death
  menu ends the run with `AbortMission(Failed)`.
- **SValue compact tags 0x67/0x68 are true/false** (fixed in faaddf2; they were swapped).
  Converted HoH1 levels made before that fix had every boolean inverted.
  `hwr_archive.CONVERTER_VERSION` (now 2) is stamped on each `import_hoh1.py` output
  (`hoh1_import/stamps/`). An import over older output regenerates it, and `build.py`
  warns about stale imports.
- **The mission defs and their level generators are rebuilt on every level load**,
  before any module constructor. A command added to `m_genCommands` in a ctor is
  therefore gone on the next level and must be added again; it never piles up.
  `DungeonGenerator` calls `randf()` once per command (against `m_execChance`), so
  inserting a command shifts every later roll and changes the level vanilla makes for a
  seed. The architect's `ChallengeSetup` wraps an unconditional command instead of
  inserting one.
- **`Item::GetRandomTrinket` sets `m_seen` on the trinket it returns**
  (`scripts/Items/Trinkets.as:46`), and later rolls treat seen trinkets as duplicates.
  Vanilla shops and the sarcophagus clear it again for picks nobody took. The General
  Merchant's trinket stock roll saves every trinket's `m_seen` and restores it afterwards.
  Assumed, not measured: whether `Trinket` instances reload per level, which would reset
  it anyway.
- **Escape on the character picker closes it.** `WindowManager.Back` closes the top
  window when its `Back()` returns true, and `PickCharacterWindow.Back` always does (only
  setting the in-game menu when no class is picked). A forced picker therefore has to be
  reopened: mercenary reopens it after `PICKER_DELAY_MS` while a fallen mercenary is in
  town.
- **God mode lives in the `cht_god` cvar, not in `CVars::ChtGodmode`.** The vanilla
  `cht_god` is registered with `AddVar("cht_god", false, SetGodmodeCVar, Cheat |
  TriggerChanged)` (`scripts/Console/Cheats.as:22`), and `SetGodmodeCVar` copies it into
  `CVars::ChtGodmode`, which `Player.as` reads. Setting only `CVars::ChtGodmode` did not
  hold: in GameLab (probe-god) the player still took damage. HWP's `hwp god` therefore
  toggles the cvar with `SetVar("cht_god", on)` and reads it with `GetVarBool("cht_god")`.
  Verified: with the cvar set, HP stays full under damage. Assumed, not traced: what
  resets the script global (the cvar being re-applied on a level or script load).
- **A building upgrade destroys every unit a mod spawned in town.** `TownRecord.Refresh`
  (what runs when an upgrade's cutscene ends) does `QuickReloadLevel` and `SpawnTown` in
  the same scene, with no new module `Start`. Verified with `gl townrefresh`
  (mod-town-rebuild): before the fix, the gambler, the last-run board, the pet bowl and
  the pet vendor were gone afterwards. Modules that spawn once per load now keep the
  unit in `HWP::Town::Kept` and re-spawn it when it is invalid or destroyed (checked
  every `WATCH_MS`, in town only, host-only unless told otherwise). Placeable, fishing
  and farming already did this.
- **The vanilla close button is `<spritebutton spriteset="close">`**, with the sprites
  from `gui/closebutton_sprites.inc` (close, close-hover, close-down, close-disabled).
  `spriteset="close-button"` does not exist: the button draws nothing and the log says
  "Couldn't load SpriteRect, sval does not exist". Eight HWP windows had it. GameLab's
  `log_clean` now fails on that line.
- **`g_scene.FetchAllUnits` (GameLab `near`, `use`) misses units with no solid
  collision**, such as the campaign portal and the abyss crack (sensor only). Assumed
  from what `near` does and does not find, not traced in the engine. Scenarios find those
  units by their logged position (`log_capture`) instead.
- **The campaign needs the story flag `mission_story_intro_find_npcs`** (vanilla
  `cht_set_flag mission_story_intro_find_npcs 1 1`); `hwp unlockflags` does not set it.
- **Vanilla's `theme_prison` never generates.** Its only uses in `missions_story.sval`
  are commented out, and a floor using it loops forever on "Couldn't find two
  appropriate spots for prison_start, and prison_exit" (`DungeonGenerationCommands.as:146`),
  hanging the game. Verified in plan-t6c (Forsaken Tower floor 4). The campaign's Prison
  floors now use `theme_dungeon` with Dark Citadel's dungeon sizes.
- **`cht_kill_all` (GameLab `cull`) kills with no killer**, so `PlayerKilledActor`
  hooks, XP and kill stats do not run. `CompositeActorBehavior.Kill(killer, w)` calls
  `OnDeath`, which calls `killer.KilledActor`, so `gl cull mine` (the local player as
  killer) runs them. The survival arena's bar (`SurvivalMission.m_experienceC`) still
  counts culled kills, through `OnEventActorDestroyed`.
- **Escape with no window open opens the pause menu**, and a paused game does not run
  module `UpdateFrame`. A scenario that pressed Escape after a failed `gl use` stalled
  every timer behind it for 15 s.
- **Strongbox packs and abyss waves could hold unkillable members.** Both copy their
  enemy kinds from the live actors around them (`HWP::Spawner::SampleProducers`,
  `FetchActorsWithOtherTeam`). Farming's wild plot is an `HWPLocalNPC`
  (`CompositeActorBehaviorNPC`) on a non-player team, so it was sampled as a kind and
  spawned as onion plots. Nothing kills those (cull skips untargetable actors, and so
  does combat), so the strongbox never opened and the crack never reached wave 2.
  Verified in plan-t4 run 050719: every cull skipped `doodads/hwp/wild/onion.unit`
  copies around the box and the crack. This was also the "abyss wave stall" seen once
  in run 043107. `IsSpawnable` now takes only targetable, non-NPC actors whose unit is
  under `actors/`.
- **`SurvivalMission`'s `boss` must be a prefab.** `Missions/SurvivalMission.as` loads it
  with `Resources::GetPrefab` and, once the bar is full, fabricates it at the player's
  position + (0,-100). The heaven trials pass a spawner prefab
  (`prefabs/heaven/seg_heaven/boss_spawners/heaven_*_spawner.pfb`): an intro, a
  `SpawnUnit` of the boss, and a `BossDefeated` ScriptLink that unlocks the trial's
  achievement, sets its character flag and opens the exit. The wave arena passed
  `actors/hwp/wave_boss.unit`, so the prefab was null and filling the bar threw "Null
  pointer access" (`SurvivalMission.as:126`): the arena champion never spawned. Verified
  in plan-t6b run 051540. `tools/make_wave_boss_prefab.py` now writes a copy of the
  warrior spawner for the arena. Worldscript rows decode as `[type, id, pos, enabled,
  triggerTimes, ?, (comment), params, (links)]`; a ScriptLink's links are flat
  `id, delay` pairs.
- **The wave statue's old default (-1500,250) was on the beach**, inside the trading post's
  plot (-1536,256) and 64 px from coast fishing spot 3 (-1436,272). In plan-t6b run 052747
  a use there opened `HWPFishingMenu`, not the survival window. The statue now stands left of
  the chapel's Pyre slot (`HWP::Town::ChapelPyreSpot`, moved to core from the campaign):
  872,-232 with the Pyre unbuilt, 872,-160 once a built Pyre blocks that spot. Verified with
  the Pyre unbuilt and built (`gl build pyre` + `townrefresh`) in probe run 053923: use opens
  `WindowSurvivalMission` both times.
- **Survival spawn events sit at k/(n+1) of the bar** (`SurvivalMission.OnEventActorDestroyed`):
  with 4 events, at 20/40/60/80%. A kill past a checkpoint fires one event. Once the bar
  passes the goal the boss spawns and no more events fire, so jumping the bar straight to
  full skips all of them. `hwp wave goal 21` then one kill fired "Spawning Event 1" in
  plan-t6b run 052403.
- **Start gear goes through the normal equip checks.** `PlayerRecord` (~line 452) gives each
  `starting-equipment` id a Common roll at level 1 and calls `EquippedItems.Equip`, which
  starts with `MayEquip`: a stat requirement the fresh character can't meet makes it return
  null, and the item is simply lost (not put in the inventory). The Witch Hunter (5 STR) listed
  the vanilla `twohanded_crossbow_01` (ilvl 10, `req-str 10 25`) and started unarmed. Verified
  by decoding `gl inspect player equipped` in plan-t7 run 061824 (slot 0 null). It now starts
  with `hwp_crossbow_01` (ilvl 1, `req-dex 8 18`, DEX-scaled), and plan-t7 asserts slot 0 for
  all four HWP classes (run 062639: daggers, trident, crossbow, rifle).
- **Herbs need two watered runs.** A plot gets +2 growth per run when watered, +1 when not
  (`CountRun`); food crops are ripe at 2, herbs at 4. plan-t7 waters and grows twice before the
  Lucky Leaf harvest.
- **The Pilot's `use` reach.** A solid target (a chest) can't be walked onto, so walking to
  within a few px of its centre never ends. `use` now stops once the target is the player's
  top usable (`GetTopUsable().GetUseUnit()`), and the stuck check treats an approaching `use`
  as moving. A path from inside an obstacle's footprint (where an opened chest stood) comes
  back empty; `Repath` then retries from eight points 24 px out. Verified in plan-t7 run
  061824 (two chests opened in a row).
- **The Pilot finds no route from the town arrival point (1984,598) into town.** Both
  `Pathfind` and the partial `NavRoute` end in the forest. Town scenarios teleport near the
  target first. Not traced further.
- **`Scene.FetchAllUnits(mask, center, radius)` doesn't bound what it returns by the radius.**
  First seen as "`near <r> <filter>` ignores the radius"; it was the same without a filter
  (`near 60` in town: 764 units, plan-t8 075319), so every `near` count was the whole level.
  `near` now drops units past the radius itself. mod-puzzle-rooms' reward check counted the
  whole level that way and now counts `near 6000 items/`; the other 14 scenarios that use
  `near` pass unchanged (081413-082914).
- **The dark column over a window in the lower-left is the in-game chat history panel**
  (x 19-250, y 136-360 at 640x360). It shows while recent chat lines are up (any `[HWP]`
  message) and fades with them. It isn't part of the HWP window under it (probe 063142).
- **A town rebuild reuses unit ids.** `TownRecord.Refresh` reloads the level in the same
  scene, and the new level's units get the old ids back. A `UnitPtr` kept from before then
  reads `IsValid()` and not `IsDestroyed()`, but names a different unit. Measured in
  mod-town-rebuild run 064132: id 923 (the notice board) came back as `tree_oak.unit` and
  924 (the gambler) as `beetle_green_small.unit`, so neither was spawned again (run 063819
  failed on both). The pet bowl's id happened not to be reused. Core now has
  `HWP::Town::Ours(u)` (live, and the unit file is an HWP one), `Kept.Set` remembers the
  producer, and `Placeable` compares the unit path. Every destroy or "still there" check
  on a kept town unit (gambler, board, bowl, pet vendor, pirate, coast spots, traps, farm
  plots, visuals, well, hidden crops, dye markers) goes through them. Assumed, not
  measured: before this, a rebuild could make `ClearLocal`, `ClearVisuals` or
  `Placeable.Spawn` destroy (or `SetCropsHidden` hide) whatever vanilla unit took the id.
- **The Gambler's result line was overwritten right away.** `UpdateUI()` sets the line to
  the bet prompt (no hand) or the last hand's result, and the sell and reroll handlers
  call it after writing their message, so "Rerolled ...", "Not enough gold ..." and "Sold
  your wares ..." were never on screen (plan-t8 070630: the line read "Place your bet and
  draw!" after every press). They now go to `m_notice`, which `UpdateUI` shows until the
  next hand or bet. The reroll buttons are never disabled; the refusal is that line.
- **A low item level has a small modifier pool.** A rare mace at ilvl 3 rerolled to the
  same modifier it had (plan-t8 072725: token spent, item unchanged), and the same few
  modifier ids came up across runs. A reroll now rolls up to 8 times for a set the item
  didn't have.
- **GameLab's `widgets` dump can't read a button's caption.** `ScalableSpriteButtonWidget`
  text is a `BitmapString`; only `TextWidget.m_str` is dumped. The dump now also gives
  `enabled` for `AInteractableWidget`s.
- **GameLab `pathfind` answers `nodes: 0` both for "no path" and for some straight lines.**
  A chest at +90,0 from the Bandit Keep start answered 0 in one run and 2 in the next, and
  opened both times. `plan_checks.chest_spot` prefers `nodes > 0` spots.
- **Bot timing.** The weapon swap has a 1 s cooldown, so a check that presses X again
  sooner sees nothing (072156). A posted console line once arrived as "`hwp bag" (stray
  backtick) and did nothing; `plan_checks.hwp(..., until=)` resends once when the reply
  doesn't come. The Bandit Keep's bandits killed the player during the third chest, so the
  chest checks `cull` first.
- **A log line over 16 KB looks fatal.** The game exited with 0xE06D7363 right after printing
  a 16,401-char `widgets` reply (plan-t8 074605); no earlier reply was over 14,596. Assumed
  from that one case, not reproduced. GameLab's `Emit` now replaces a reply over 15,000 chars
  with a short failure that keeps its id, and `widgets` stops at 13,000 chars of nodes.
- **A tabbed window's open tab is its own window object.** `PlayerMenu`, `GuildHall`,
  `WindowOptionsMenu` and `CreateCharacterWindow` keep their tabs in a `MenuTabSystem`; each
  `MenuTab` is an `AWindowObject` whose widget tree isn't under the window's, and its own
  `m_tabSystem` is the one it sits in. `widgets` now dumps the open tab as a root named
  `PlayerMenu:PlayerMenuCharacterTab`, which is where the gear and alt-weapon slots are.
- **A locked chest is not usable without its key.** Vanilla `Chest.CanUse` is false while
  `GetKeys(m_key) <= 0`, so a use attempt finds the chest as the top usable but can't use it
  (the Pilot reports "top usable is not the target"). With the key it opens (plan-t8 081413).
- **open-chest and open-chest-minimized fail before and after this session's probe changes**
  (081200 with the old probe): the "f" key press doesn't open the spawned cache. Those are
  GameLab self-tests of real key input, not HWP features; not traced.
- **`WindowManager.CloseWindow` doesn't set `m_closing`; `Back()` / Escape does.** An NPC
  window (`AShopContent.IsDone()`) only counts as done once `m_window.m_closing` is set, and
  vanilla `NPCSharedBehavior.Use` closes the open window instead of interacting while
  `m_current` is set. So after an HWP window closed itself with `CloseWindow(this)`, the next
  use of that NPC or object did nothing: planting at a farm plot then using it again to water
  needed two uses (plan-t9, 2026-10-18 morning). Seven HWP windows close themselves (farm,
  pet bowl, pet dye, fishing, pirate, pet vendor, last-stats board); each now sets
  `m_closing = true` first. The watering check passes on the first use since.
- **`Town::Ours` alone can be fooled by an id reused for another HWP unit.** After a town
  rebuild, the gold pet vendor's old id came back as a different `/hwp` unit, so "still
  ours" was true and the vendor wasn't spawned again (plan-t10, fixed). `HWP::Town::Is(u,
  unitPath)` also compares the producer; the vendor, well, bowl and pirate checks use it.
  mod-town-rebuild and plan-t10 pass with it (090120, 090404).
- **Re-running `import_hoh1.py pets` put the HoH1 pets back on the vanilla classes.** The
  importer wrote `MiniPetWalking`/`MiniPetFlying`, and only `make_pet_dyes.py` (run by
  doctor) rewrote them to the HWP classes. After a re-import at 04:06 all 22 HoH1 pet units
  were vanilla again: no pickup toggles (vanilla always passes 319), no Fetch, skills,
  dyes or puzzle-room waiting. `gl near` showed `behavior: MiniPetWalking`, and the Elf
  Imp fetched gold with Gold off (plan-t9 090855-091950). Earlier "off" passes were drops
  the pet happened not to reach. The importer now applies the pets module's `class_swaps`
  itself, and `make_pet_dyes.py --verify` (doctor) reports any HoH1 unit still on a
  vanilla class. plan-t9 092312: `HWPMiniPetWalking`, Gold off leaves the drop, on fetches it.
- **A gold drop the pathfinder reaches can still be one the pet won't fetch.** A drop at
  (150, 0) from the Bandit Keep start stayed put while (±106, 106) and (0, 150) were
  fetched. `plan_checks.gold_drop` now wants a near-straight path (length ≤ 1.25 × the
  distance), tries the diagonals first, and moves to the next direction when a drop isn't
  fetched within 8 s.
- **`Material::DropMaterial(type, amount, pos, shared, dropAnim)`** gives a pickup that
  carries its amount. `gl spawn items/materials/gold.unit` gives one worth 0 (its behaviour
  is never `Initialize`d). GameLab's new `drop` verb uses DropMaterial with no drop animation.
- **`array.sort(callback)` on an empty array throws "Index out of bounds"** (reported on
  the sort line). `MissionShopContent.GetItems` sorts its missions, and
  `MissionDef::FetchMissionsFromSet` returns none while the set's conditionals fail (the
  campaign set needs `mission_story_intro_find_npcs`, unset on a fresh character), so using
  the town portal threw before any window opened (plan-t11 094100). `HWPCampaignShopContent`
  says the portal is dormant instead and sorts only lists longer than one. plan-t11 094708:
  dormant first, then two missions after `cht_set_flag mission_story_intro_find_npcs 1 0`.
- **Escape with no window open opens the pause menu**, and a paused game ignores the next
  steps (the wave statue run sat in the pause menu after a failed portal use). Bots only
  press Escape when `state.window` is set.
- **The game carries a player's summons through a floor change** (with their HP): the
  record keeps each summon's `SaveUnit` data and `Player`'s constructor produces them on
  the new floor. GameLab probe-summons-off 095747: with mods/summons off, 2 damaged
  crusaders came through. The summons module produced its own snapshot on top, so 2 went
  in and 3 came out (plan-t12 095531). It now produces only what is missing per kind.
  Call Crusaders is a passive skill: below its cap it summons one about 1 s after a level
  loads (town too) and at once when its 15 s timer has already run out.
- **Kills without a killer run no kill hooks.** `cht_killall` (and `hwp killall`) calls
  `Kill(null, 0)`; only `Kill(player, ...)` reaches `OnDeath` -> `KilledActor` ->
  `PlayerKilledActor`, so key drops, XP and kill stats need the player as the killer
  (GameLab `kill <r> <filter> me`). Elites are their own units (`bandit_brute_elite.unit`
  etc., tag `elite`), not a modifier on normal ones; a Bandit Keep floor 1 had none (probe-keys
  102702). Boss floors spawn the boss from an encounter, so it isn't there on arrival.
- **A `gl` line typed while the next level preloads can find the probe's verb registry
  null** (Script exception at Probe.as `RunVerb`, probe-keys2 103121, during a Dark Citadel
  load). ConsoleGl now catches it and fails the command so the caller polls again.
- **Combo needs a combo skill.** `PlayerStats.ComboCountMax` is 0 until a combo skill
  (`combo_kills` / `combo_dash` / `combo_parry`, tier 1, cost 0) is picked through
  `SkillUp(id, true)`; until then `Player.GiveCombo` does nothing.

## Skill aim follows the mouse after the emulated input ends (2026-10-18)
- `gl input` sets `GameInput.AimDir` only while held. A skill with `update-aim 0 N` keeps
  re-reading the aim until N ms; released earlier, the aim falls back to the real mouse
  cursor, and the round flies there. The firearms aimed shot (castpoint 420) missed every
  target with a 60-300 ms press and hit three brutes in a line with a 500 ms hold
  (plan-t14 20261018-114725). Verified.
- One `gl` command per ~0.3 s: three spawns plus a shot gave the brutes time to walk in and
  steer around each other; `gl multi` puts them in one frame. Verified.
- `cht_plr_hidden` only hides the player unit; enemies still aggro. Goblin totems took no
  projectile hits. Verified (plan-t14 runs 111904, 113007).
- Player mana costs: `Player.UsePoints` takes flat cost x `GetModifiers().SkillCostMul` off a
  float mana; `CurrentMana()` truncates, so integer read-backs alternate 1/0 for a 1-mana
  shot under regen. The probe now reports `manaExact` and `manaCostMul`. Verified.

## Enchanter assumes quality-matching mods (2026-10-18)
- `Town/EquipmentEnchantShopContent.as`: the Enchant view (`EnchantEquipmentWindow.Refresh`)
  shows `modifier-1` for quality >= Uncommon and `modifier-2` for Rare, and reads
  `mods[GetCurrEncSlotIdx(shop, 0|1)]` for their text; the list entries and the `modify`
  func index the same way. `GetCurrEncSlotIdx` looks for a Common-quality mod (slot 0) or a
  Rare one / a second Common one (slot 1) and returns -1 when there is none, so an
  uncommon or rare item without its modifiers throws "Index out of bounds" (inside a
  `gl pressin` the probe reports `exception in verb 'pressin'` and the heartbeat's
  exceptions count rises; no "Script exception" line). Vanilla items always have them:
  `Generator.GenerateItemMods` gives `EquipmentModifiersPerQuality` (0 / 1 / 2 / 3 / 4)
  mods, the first from the Common pool (no vanilla mod is Uncommon quality). Fishing built
  fish items directly with none; fixed by rolling them at the catch. Verified for the
  crash (plan-fishing-a 20261018-121447: fresh Salmon, heartbeat exceptions 0 -> 1); the
  fix not yet run.
- The Enchant list only shows modifiers whose blueprint the town owns
  (`GetItems`: `m_blueprintHash != 0 && !HasBlueprint` skips it). Every mod in
  `tweak/items/modifiers_equipment*.sval` has one (`blueprint` defaults true), so a
  fresh town lists none for any item ("Num item mods: 8" printed, 0 shown). GameLab:
  `cht_add_all_blueprints` (cheat). Verified (same run).
- `Generator.ModifyItem` (the enchanter's Upgrade) calls `GenerateItemMods`, which keeps
  `mods[n]` only when its quality is `IndexToQuality(n + 2)` (Uncommon for the first);
  the first mod is always Common quality, so an upgrade rerolls every modifier.
  From source; assumed.

## Three skill buttons; extra skill keys (2026-10-18)
- **The engine has only Skill1-3.** `GameInput` exposes `Skill1`, `Skill2`, `Skill3`
  (`hwr2_api_strings.txt` has no `Skill4`; the editor stub `system/engine.as` lists one, but
  it is stale). `PlayerTargetingHelper.GetSkillInput` (PlayerTargetingHelper.as:713-750)
  counts the non-passive `Spell` skills from `m_skills[1]` and returns `Skill3` for the 3rd
  and every later one, and `CheckUseSkill` (515) activates every skill whose button is
  Pressed, so a 4th active fires together with the 3rd. Verified in game by the main
  session (GameLab, firearms and classes plans, 2026-10-18). Vanilla keyboard defaults
  (`res/controls_default.cfg`): Skill1 = 1, Q, mouse 4; Skill2 = 2, E, mouse 5; Skill3 = 3, V;
  free digits 4-0. Gamepad: RB, LB, Y. `RadialMenuController` has a skill wheel
  (`ExpandPlayerSkill` -> `TryUseSkill`), but `RadialMenu` only adds emotes and the ping, so
  a gamepad has no way to a 4th active; the extra keys are keyboard only. From source.
- **Fix (core `SkillKeys.as`):** `Player.m_targetHelper` is a public `PlayerTargetingHelper@`
  and script methods are virtual, so core swaps the local player's helper for a subclass,
  `HWPSkillKeysHelper`, from a module `UpdateFrame` (only when no targeting is open). Its
  `GetSkillInput` override takes the vanilla answer and, for the 4th-6th active, rewrites
  `Down` / `Pressed` / `Released` of that `ButtonState` copy from a raw-key poll
  (`Platform::IsKeyDown`, scancodes from the Plus tab, default 4/5/6), sampled once per
  player frame in an `Update` override. Every other path (targeting modes, input buffer,
  `GetSkillCanceledInput`, quickcast) is vanilla and reads the new keys through the
  override. Assumed until measured: a `ButtonState` local copy is writable
  (gamelab-hands already writes `gi.Skill3.Down`, verified) and `Base::Method()` calls from an
  override compile here as they do for HWP widgets.
- **HUD:** `HUDPlayer` (player_info.gui) has backgrounds for 2-4 skills. Core replaces it in
  `HUDConstructor` with `HWPSkillKeysHUDPlayer`, which widens the 4-skill group in place
  (a `skill-mid` sprite and a `skill-slot` rect per extra skill, end cap moved 31 px) before
  the vanilla `RefreshSkills`, then writes the key name into the extra skills' unused
  `binding` text, moved above the slot. Assumed until a screenshot.
- **Subclass picker** (`Town/SubclassPickShopContent.as:96-102`) shows `m_skillDefs[len-2]` as
  the spec's active and `[len-1]` as its passive. Sniper (snipe, flashbang, decoy) and
  Demolitions (tube, rpg, jetpack) have three actives, so the picker shows flashbang / rpg as
  "active" and decoy / jetpack as "passive", and never snipe / tube. Display only; from source.
  Fixed in core (`HWP/Core/SubclassPick.as`): no window hook exists (`OpenShopWindow` adds the
  window straight to the `WindowManager`) and the shop content class is named in the vanilla
  NPC unit, so the open vanilla window is patched in place. Module `UpdateFrame` runs after
  `BaseGameMode.UpdateFrame`'s window-manager update, paused or not
  (`AGameplayGameMode.as:319/333`), so the patch lands before that frame is drawn. The row
  shows the spec's own defs (not in the parent class), actives then passives, each labelled
  by type, spread over up to four slots (copies of
  slot 0, ids `hwp-pick-name<i>` / `hwp-pick-skill<i>`, labels `hwp-pick-label<i>`). It
  relays out when the shown class changes or when `SetCurrSubclass` rewrites slots 0/1 (on
  a pick), seen as a skill id change. Vanilla specs (one active + one passive at the end)
  look exactly as before. Gotcha: `Widget.CloneInto` value-copies the fields, so a cloned
  `TextWidget` shares the original's `BitmapString`, and its `SetText` would `Cleanup()` the
  original's text; the copy's `m_text` is nulled first (same for `SkillWidget.m_cost`).
  Assumed until a run: the layout and the label spacing (105 px for three slots).
- **A def's type does not say passive.** `PlayerSkillDef` turns an untyped def into `Spell`
  (`PlayerClass.as:91-92`), so every class skill def, passives included, has `m_type` 4
  (measured: `gl classskills hwp_priest_hoh1` gave Last Rites type 4, run
  20261018-125750-plan-classesb-b). Passive is the skill's `GetTargetingMode()` ==
  `TargetingMode::Passive` (the default of `Skill.as:83`, which `PassiveSkill` keeps), the
  test `GetSkillInput` and `HUDPlayer` make: those skills get no button (`gl skills` button
  ""). The picker row and `gl classskills` (`mode`, `passive`) classify by a temp skill
  built as `MakeSkillTemp` builds one. The vanilla row's labels are static gui text
  (Active under slot 0, Passive under slot 1); a first version of the fix set them from
  `m_type` and so labelled every passive Active, the vanilla specs' included.
- **GameLab:** `gl input` takes `hwp_skill4`..`hwp_skill6`; gamelab-hands writes the held
  ones to `GlobalCache` `hwp_skillkeys_held` ("4,5") and core's poll ORs them in (no shared
  symbol, so hands still loads without core). `gl skills` / `gl skillbar` report the
  extra key once the helper is installed (`Reflect::GetTypeName` of `m_targetHelper`).

## Test-plan rounds 2-6 (2026-10-18)

- **`ParseColorRGBA` returns linear colour.** A dye's sval hex (sRGB) comes back
  linearised, so writing `m_colors[i]` straight into a `\c` text code shows it darker
  (Midnight 222270 showed as 040429). `PetDye.Hex2` encodes back to sRGB (measured: the
  round trip gives the authored hex, plan-pets-a 20261018-141404).
- **HoH1 level script rows are `[type, id, pos, Enabled, TriggerTimes, ExecuteOnStart, ...]`.**
  Checked against vanilla HoH2 `boss_arista.lvl` (index 3 true on nearly every script,
  index 5 only on PlayMusic). `hoh1_convert.py` used to clear index 3 on level exits,
  which disabled both Battlements 1 exits and boss_archives exit 4949. The rule now
  clears index 5 (no HoH1 exit sets it). Re-import the HoH1 levels to pick this up.
- **HoH1 `SpawnEnemyGroup` is how the Battlements get their enemies** (53 points on floor
  1, 60 on floor 2; the levels place none). HoH1 called the generator's
  `EnemyPlacement.PlaceGroup`; the port now spawns `int(2*PI*Radius/40*0.5)` ice trolls
  plus one shaman per group at weight 0.8 (measured: 19 trolls, 4 shamans on floor 1,
  plan-runs-d 20261018-141935). The ice trolls are on the NG+ map too (below).
- **The Warden's bomb fan and the Vampire Lord's Bat Spray are NG+ attacks.** The base
  units leave them out (warden.unit defines NORMAL and the fan is `%if !NORMAL`;
  vampire.unit has `BATCHARGES 0`), and HoH1 swaps each boss for a tier copy by NG+ level
  (`tweak/dungeons/unitmap_base.sval`: `_t2` at NG+1, `_t3` at 3, `_t4` at 5, `_t5` at 10;
  warden_t2 sets `WHIRLBOMBS 4`, vampire_t2..t5 1/3/5/7 bat charges). The Golem and the
  three Wraiths get the same swap. (An earlier version of this note called the attacks off
  at any NG: wrong, the tier files were missed.)
- **HoH1's NG+ swap is in its spawners, and the port does it the same way (2026-10-18).**
  HoH1 `UnitMap::Replace` runs inside SpawnUnit, SpawnUnitWithEffect, SpawnDropUnit and
  EnemyPlacement, not on placed units; every mapped unit in our levels comes from the first
  three (76 SpawnUnit, 20 SpawnDropUnit, 9 SpawnUnitWithEffect references). `import_hoh1.py
  campaign` now imports the tier copies of the 21 mapped units the levels reach and writes
  the map, without HoH1's loader, to `hoh1/tweak/hwp_unitmap.sval`;
  `HWP/Campaign/HoH1/UnitMap.as` rewrites those scripts' `UnitType` once per level by
  `g_ngp`, the thresholds HoH1 uses. Verified, plan-runs-ng 20261018-171057: NG+1 spawns
  warden_t2, whose whirlwind threw 80 bombs and whose ballista shot; NG+2 spawns
  vampire_t2, whose Bat Spray (needs NG+2, under 20% health, within 120 px; HoH2's
  conditionals handle `ngp`) fired 11 bats. GameLab's `mission` verb takes an `ngp`.
- **HoH2's `CompositeActorBurstSkill` never fires without an `anim-begin`.** HoH2 added
  `if (m_restrictions.AttemptUse()) { cooldown; return; }` to the no-begin path, and
  AttemptUse is true unless the fail-chance roll hits, so the burst is skipped every time
  (HoH1's version has no such check). Vanilla's two burst skills both have an anim-begin;
  HoH1's six (ice troll melee, ice elemental ranged, both ballista towers, the big arrow
  turret, the Warden's NG+ club and ballista) do not, so none of them attacked. The import
  maps them to `HoH1BurstSkill`, which inverts the fail chance when there is no begin
  anim. Verified: warden_t2 clubs and shoots (plan-runs-ng 20261018-171057, 'attack-2' and
  'shoot-4' scenes); plan-runs-b and plan-runs-d still pass. A burst skill also restarts
  its cooldown at every check out of range, so a fast boss that closes in rarely shoots
  (HoH1 does the same).
- **The firearms decoy taunts through `AlertActors make-aggro`**: `SetTarget(decoy, -1,
  true)`, and aggro < 0 always replaces the target unless the enemy is mid-attack
  (`CompositeActorBehavior.SetTarget`). Measured: all three brutes targeted it and two
  beat it to 19 % hp (plan-firearms-a 20261018-140742). A first failure was the test:
  brutes spawned behind a wall never saw anything.
- **`deploy.py modded-prod` never rebuilds `dist/HammerwatchPlus-All.bin`** (it calls
  build.py with `--no-all` and a module list). Copying the All bin after a deploy shipped
  the 2026-10-18 02:20 build until 17:20 that day; run `tools/build.py` (no arguments, no
  `--with-local`) first, then copy.
- **GameLab gotchas:**
  - A `[GL]` line over 15000 chars is dropped (Json.as EMIT_MAX). `trail` now sends its
    report in parts ("part"/"parts") and keeps up to 128 units; the NG+1 Warden's bombs
    overflowed both the old single event and the old 32-unit cap.
  - `e_cheats` is per process: after a scenario's `restart` step every `cht_*` command
    is refused ("can only be executed with e_cheats = 1") until it is set again.
  - When the console misses a line, the typed characters and Enter go to the game as
    hotkeys and can close an open menu; bots that use a window reopen it and retry.
  - `use npc_dyer` needs the town flag `mission_story_unlocked_dyer`; without it the
    unit's conditionals destroy a spawned dyer.
  - The Three Councilors' scythe casts whenever the player is within 100 px and then
    stands still; a node-to-node test keeps the player away from it.

## Pet follow, cat targets, Morale foes (2026-10-18)

- **Vanilla walking pets idle inside `range-idle` (100 px) and only chase past the
  `leash-range` (350 px).** An Idle pet whose pathfind fails picks a new idle target and
  never falls back to a straight walk (only `MovingToPlayer` does, and a failed search in
  that state puts the pet on the owner). PetWait parks the pet on the owner's last
  puzzle-free spot, often a corner of their path against a wall, where the pet's own
  search can fail: after the wait it stood 200 px off for 9 s (plan-pets-b
  20261018-144852). `PetWait::Rejoin` now sends it off in `MovingToPlayer` when a wait or
  a candle hover ends. Verified over 8 later pets-b runs.
- **The Gold Collector cat took the nearest pickup even when unreachable** and stood still
  on it, hiding every other pickup. Reproduced: gold dropped on a point with no route,
  nearer than the wood, and the old code never fetched the wood (pets-c 154346, 154624).
  A target it gets no closer to in 1.5 s is now skipped for 10 s (same decoy, 3/3 pass).
- **The farming wild plots are actors on another team** (`HWPLocalNPC`, `targetable
  false`). Morale counted any live other-team actor as combat, so a plot near the owner
  kept it off (pets-b 155331; reproduced with a plot spawned 70 px off, 160733). Morale
  and Stun now take only targetable, live, non-hazard actors within the radius
  (`Pets::Foe`, the same filter as vanilla `RandomEnemyApplyEffects`).
- **GameLab:** an object spawned on the player is gone at once (the smash pot landed on
  the player when the pet stood 24 px to its left); `pathfind ... nodes 0` does not always
  mean the cat cannot get there.
- **GameLab, unexplained:** a `teleport` onto the onion field's left groove (x -374) is
  followed by about 1.5 s of movement by (+52, -112) from every start point on it, with no
  pilot intent running and nothing in our scripts moving the player. The farming bot now
  tries the groove's plot units until a stand holds (plan-farming-a 163358, 163815,
  164143). Not seen with a walking player; not explained.

## Review fixes after the NG+ port (2026-10-18)

A /code-review xhigh on the work since 28b14c8 gave 15 findings, all fixed:

- **A reloaded town reuses unit ids, so a list of town units can point at another
  unit.** `HWP::Town::Units` keeps each unit's producer from when it was added, and
  `Live(i)` checks that the unit still has it. It replaces bare `Ours()` checks in the
  map markers, farming's plot visuals and fishing's traps. `Kept.Due` and `Placeable`
  accept a unit with no producer (a prefab child holding the id) without a null deref.
- **The pet bowl's `Kept` was `Set` every frame,** so it took on whatever unit held the
  id and `Due` never fired. It is now set only when `SpawnBowl` makes a new unit.
- **`Kept.Set` of an invalid unit** (the unit file is missing) now marks it failed. `Due`
  stays quiet until `Reset`, so the board isn't respawned and logged every 500 ms. The
  pet vendor has the same flag.
- **NG+ tiers:** `SpawnEnemyGroup` (the troll groups) now goes through
  `HoH1::TierFor` like the other spawners. NG+ is rounded with `int(g_ngp + 0.5f)`, as the
  game rounds it.
- **`Spawner::IsSpawnable` rejected `hoh1/actors/...`,** so strongboxes and abyss
  cracks on HoH1 floors found no pack members. The `hoh1/` prefix is now stripped before
  the checks.
- **Gold Collector cat:** moving more than 4 px also counts as progress. A path around
  a wall leads away from the target for a while, and the old check (distance only)
  skipped targets the cat was reaching.
- **Wave statue spot:** the clear-spot check ignores actors, pets and pickups. They move
  around, so each machine could pick a different spot.
- **`Market::Migrate`** marks worn items dirty and calls `SyncEquipment` when it rolls
  their modifiers. Fishing remembers a fish's signature only when the fish goes into the
  bag or is dropped for you.
- **Extra skill keys:** rebinding sets the key's held state from the keyboard, so there
  is no phantom Released.
- **GameLab:** `Emit` reads a too-long reply's id up to its closing quote, since an id
  may hold a comma. The `cursor` verb's local is renamed off `set`. `docs/generated/verbs.md` is regenerated.

- Verified in GameLab after the fixes (20261018): mod-all 175043, mod-core 175056,
  mod-wavemode 175108, mod-goldpet 175121, mod-fishing 175133, plan-pets-a 175146,
  plan-pets-c 175727, plan-farming-a 175932, plan-farming-b 180259, plan-fishing-a 180605,
  plan-fishing-d 180735, plan-runs-ng 183037, plan-runs-d 183341, plan-pets-b 183535,
  plan-runs-b 183829. Two first tries failed on bot geometry, not on the fixes, and passed
  on retry: in pets-b 175413 the pet followed (2.5 px off) but no clear 150 px walk was
  found; in runs-b 183228 every spike hit the player or timed out before a wall.
- **Trinket map web app** (https://claude.ai/artifact/5BP7XozLjkK9N445LKCYw9, built from
  scratchpad files outside the repo) was reviewed too. Its data was clean: no duplicate ids,
  set items all resolve, and every grouping set exists. Four page bugs were fixed and checked
  in jsdom against the old build. (1) Another viewer's verdicts were dropped while you typed
  a note. (2) Two quick edits lost the first one. (3) A partial saved filter in localStorage
  left the page empty. (4) Without the shared store, the verdict dropdown dropped changes
  silently. Orb of Restoration is now flagged as flat (+10 mana regen).
- **Trinket map, second review** (`/code-review xhigh`, 15 findings, all fixed; page version 3).
  Verdict writes now run one at a time per trinket, so a Reset can no longer race a change.
  A change that fails to save is rolled back instead of staying on screen. Live updates
  wait while a pointer is down or a note is being typed, and focus returns to the rebuilt
  control. Saved filters accept only known keys. Notes are capped at 2000 characters and
  flattened to one line in the copied to-do. A failed copy is reported. The "Note added" label
  shows only when there is a note. Three HoH1 set pieces with no HoH2 trinket (Circlet of
  Willpower, Wizard's Wand, Steady Greaves) now sit under their HoH1 set, not under
  "Missing, no set". Markham's Amulet/Mace/Wand, Decaying Hand and Pickled Eye are now
  flagged flat (52 HoH2 trinkets with flat values). The lang files now decode strictly
  (no U+FFFD patching), with identical output. 43 jsdom checks pass on the new build.

## Firearms clip and guns (2026-10-18)

Built the firearms clip, the reload rework, the rifle rework and the pistols
(`mods/firearms/README.md`, design in `docs/design/firearms.md`). Facts found on the way:

- **An item's `ModifyStack` never applies; a buff's does.** `PlayerRecord.RefreshModifiers`
  runs `modList.ModifyStacks(player)` (PlayerRecord.as:1886) after buffs, stacks and skills
  are in the list but before the equipment loop. A gun therefore grants a marker buff
  (`Modifiers::Buff`, freq 250) that carries the `add-max`. Verified: the rifle clip reads
  30/30 and the pistols 12, 24 dual (GameLab `plan-firearms-guns`, 20261018-181338).
- **`ActorBuffStacked` keeps the def it was built with** (ActorBuff.as:466). The modified
  def must exist before the first stack is made. The Reload skill carries a
  `ModifyStack add-max 0 0` for that.
- **Lose-effects at 0 stacks run at intensity 0, and `AddStacks.Apply` returns false at
  intensity ≤ 0** (AddStacks.as:59). Before the fix, an empty clip never started its reload.
  An effect-list dict `<vec2 name="intensity-set">1 1</vec2>` placed first fixes it
  (verified, `plan-t14`).
- **`conditionals` is an OR of groups; the tokens of one `conditional` array are ANDed**
  (Conditional.as:770-795, `CheckConditionals` returns true on the first passing group).
  A two-group "has marker" + "clip ge 1" gate fired whatever the marker said: 4 rounds a
  cycle instead of 2. Flattened into one array, it measures 2.
- **Dash restarts a stack timer.** A `TriggerEffect` with `trigger: dash` on the
  Reloading buff adds a stack at max. With `add-reset` that restarts the 1.6 s timer.
  Measured: refill 1.75 s without a dodge, 2.92 s with a dodge 0.9 s in (`plan-t14`).
- **`dbg_cht_ignore_equipment_requirements` doesn't survive a level load.** The cvar
  still reads 1, but the script global it sets (`g_dbg_ignore_equipment_requirements`,
  EquippedItems.as:1) is back to false, so `equip` refused a shield. Set it after the level
  loads, 0 then 1 so the callback runs (verified: set at scenario start, it refused;
  set this way on the floor, it took).
- **`equip <id> 1` gave GenerateItem null for `offhand_lantern_01`.** Pass the quality
  by name (`common`), as the other checks do.
- **GameLab latency:** one `gl` call takes about 0.3 s. Clip checks hold the trigger
  briefly and poll; one-frame checks use `gl multi`.
- **Flaky checks, not regressions:** one t14 read of a no-dodge reload took 3.61 s
  (beside 1.75 s), so the check now compares medians of 3 trials. `plan-firearms-a/b`
  failed once on the decoy pull, the jetpack landing (22 px off, beside a wall) and one
  missed frag damage text. They had failed the same way before this work (13:09, 13:11,
  13:48 runs) and passed on rerun (20261018-182344, -182615).
- **Assumed, not measured:** the shot spread (only rounds were counted), how often the
  "cant" voice plays when holding fire on an empty clip, and how the clip's HUD icon looks.
- **Purple orbs are skill spheres** (Behaviors/SkillSphere.as, GUI/Menus/GiveSkillSphereMenu.as;
  read from source, not run). A sphere offers 3 picks from the `modifier-skills` of learned
  skills, each at its next level, and no two share a parent. A reroll costs Shadow Curse
  `min(100, ScaleShadowCurse(12 + 7 × rerolls used))`. Across all 196 vanilla orbs the
  levels are Uncommon or Rare, never Epic (counted from the class data by the planner seed
  script). So a new orb only enters the pool once its parent skill is learned.
- **The class planner** (https://claude.ai/artifact/GUXggQqycAoQRiJ6G1Nwv3) now holds every
  vanilla class's kit and orbs, read from `gamecode/datatables`: 198 orbs, 499 orb levels and
  400 skill levels, each with its quality and `description-params` values. Each class also gets a draft
  4th spec with 2 orbs, all at status "idea". Nine skill files no class lists are cut content
  (see `docs/design/firearms.md`).
- **How orb levels read** (PlayerClass.as LoadParams and LoadSkillDescriptionParams, from
  source). A level with no `quality` takes the orb's own `quality` (default common), not the
  level before it. A `description-params` entry is `[key, (formatting bool), label, v1, v2…]`.
  Level L shows `v[min(L, n) - 1]` (Modifications.as AppendSkillDesc). Two entries can share
  a key: the label list shows both, and the `%key%` in the text gets the last.

## Firearms specializations (2026-10-19)

Built the Marksman and Demolitionist specializations and the base kit's orbs from the
planner's records (`mods/firearms/README.md`). The two base passives are left to the owner.
Checks: `plan-firearms-a` 20261019-020024, `-b` 20261019-015752, `-orbs` 20261019-015546,
`-guns` 20261019-020328, `plan-t14` 20261019-020430, `mod-firearms` 20261019-020613, all PASS.

- **Textures must be power-of-two** (verified). A 216x24 icon atlas logged
  `[ERR] Texture sizes (216x24) should be power of two`, and the game then hung after script
  compile: no main menu, exit 1, no crash dump (run 20261019-010915). Padded to 256x128 and
  256x32, it passed (20261019-011513). `tools/make_firearms_icons.py` pads every atlas.
- **Skill tag bits are below 31** (verified, the module logs them): `hwp_firearm` and
  `hwp_explosive` are bits 21 and 22 with the plan scenarios' mods, 18 and 19 with
  `mod-firearms`'s. The bit depends on which mods are loaded.
- **`castat` doesn't aim a skill with `update-aim`.** `PlayerSkillDirectional.Update`
  re-reads the player's aim every frame up to the castpoint, so the shot leaves along the
  idle aim. Run 20261019-013119: `castat` Snipe hit nothing; a held skill3 press hit the same
  dummy (106). With the aim held by `gl input` (no button), `castat` still missed
  (20261019-013510, cause not found). The bot presses the skill's button instead
  (`aimed_cast`). The same applies to a press shorter than the castpoint: the rifle's 80 ms
  castpoint against a 60 ms press sent the round the wrong way (Focus never rose).
- **A projectile thrown along a direction lands 100 out** (IProjectile.as:49-57: GetTargetPos
  is from + dir × 100, which GroundBouncing `hit-target` flies to). Explosive Reload's
  magazine missed a dummy at 45 with its 48 radius; one at 100 is hit.
- **A round that stops at its first hit stops on anything between.** The old Snipe pierced
  6, the new one 0 without its orb. On one floor it hit nothing on a wall-free line, so the
  bot's `clear_dir` now also rejects a line with a `Breakable` or actor within 12 of it
  (gl `near`). The `shootproj` bisect (20261019-012906) showed the round itself was fine.
- **Over-Reload bug, fixed.** A perfect is judged when the Reload cast starts, while the clip
  is still empty, and the dry-clip clear removed the bonus on the next frame. Before: clip
  30/30 after a logged perfect; after: 36/36 (`-orbs` runs 014544 and 015016).
- **Shared unit regression, fixed.** Assault's Stun Grenade fired `grenade_stun.unit`, which
  had become the Frag Stun orb's include and lost its damage. The Frag orb now has
  `grenade_frag_stun.unit` and Assault's file is back as it was (`-b` PASS).
- **Timing in checks:** a level 1 stun lasts 1 s from the landing, about 0.8 s after the throw.
  Reading the dummy's buffs from about 1.5 s saw nothing; watching from 0.2 s sees stun and
  slow.
- **New verb** `gl orb <orbId> [times|down]`: the skill sphere's `SkillTempUp` /
  `SkillTempDown` (Verbs_firearms.as). `SkillTempUp` ignores `blocked-by-skills`, so the bot
  takes each grenade orb back down before the next one.
- **Interpretations to confirm with the owner** (the planner left these open):
  - The rocket costs 6 mana, no rounds.
  - Quad means 4 missiles in quick succession at a fraction of the damage and radius.
  - Over-Reload on a manual Reload (owner, 2026-10-19): see the follow-up below.
  - Headshot keys on a global "next hit" flag set by the Snipe round.
  - Elemental Shrapnel is a custom stat that every explosive reads, but not the magazine:
    penetration scales with intensity, and the magazine's intensity is its round count.
  - Ordinance Hoarder: cooldowns run 1/(1+x) faster. It banks a charge per full cooldown
    while the skill is ready.
  - Gas is ignited by fire.
  - The Stun grenade stuns and slows (bosses immune to stun are still slowed).
  - Overpacked's planner record repeats an uncommon level.
  - Magic Missile reuses the ice and fire effects; there is no blue-fire asset.
  - Dual pistols throw the two magazines one after the other (owner, 2026-10-19), half
    the rounds each.
  - The old doctrine skill files (flashbang, decoy, tube, jetpack) stayed on disk, unlisted.
    Removed after the review below.
- **Assumed, not measured:** how Focus and Hoarder charges look on the HUD, and how the
  Over-Reload ring reads at a glance (only its log lines were checked).

### Follow-up: manual Over-Reload, dual magazine throw (2026-10-19)
The owner asked for Over-Reload on a manual Reload too, capped at what a perfect reload of an
empty clip gives, and for dual pistols to throw their magazines one after the other.
- **Manual Over-Reload.** A Reload cast that starts outside the automatic reload is itself the
  timed reload: a 200 ms window in the second half of its castpoint (550 ms), on the same
  ring. A second press inside it is perfect and jumps the cast to its castpoint
  (`m_castingT = m_castpoint - 1`, so the cast lands the next frame). A press outside it, or
  no second press, is not perfect and clears any bonus. The bonus buff replaces the one held,
  so the clip max stays magazine + 6/9/12 (measured: 36/36 after two perfects in a row).
- **A press during a cast never reaches the skill** (`PlayerTargetingHelper.as`: an active
  skill returns before `Activate`). So the module reads the button itself:
  `Player.m_targetHelper.GetSkillInput(skill).Down`, edge-detected, since `Pressed` lasts one
  frame and gamelab-hands writes input from its own `UpdateFrame`. Verified: the bot's second
  `gl input ... skill1` lands as "manual perfect at 462/550 ms".
- **Fixed:** after Reload was pressed during the automatic reload, the ring reopened with a
  new window until the cast landed (the reloading stack drops at the castpoint, not at the
  cast's start). The window no longer opens while a Reload cast is under way.
- **Dual magazines in turn.** The Reload timeline has a second entry, `650 cast2`, holding
  a `HWPFirearmsThrowMag` with `second`. The cast throws the main hand's magazine and keeps
  the other half of the rounds per owner unit for it; the two land 8° either side of the aim.
  Measured gap: 99 ms (scene 26136 → 26235 ms).
- Runs, all PASS: plan-firearms-orbs 20261019-091445 (new flags
  `explosive_reload_dual_in_turn`, `over_reload_manual_perfect`, `over_reload_capped`,
  `over_reload_plain_clears`), plan-t14 20261019-091715.
- **Pistol magazine 12 → 10** (owner, 2026-10-19): `GunMarker glock_main/glock_off 10` in
  buffs_firearms.sval, so dual pistols share 20. plan-firearms-guns 20261019-095245 PASS
  (clip max 10 / 20 / 10, rifle 30); the planner's weapon records are updated to match.

### Code review fixes (2026-10-19, /code-review high on all the firearms work)
- **Over-Reload gave Explosive Reload a free magazine.** A perfect on the automatic reload
  topped the clip up two frames after the Reload cast started, so the magazine thrown at
  the castpoint held a full clip. Now every perfect jumps the cast to its castpoint
  (`OverReloadState.Perfect`), so the cast's list (the throw first) reads the clip before the
  top-up. New flag `over_reload_no_free_mag`: no magazine thrown by a perfect auto-reload
  with Explosive Reload on (plan-firearms-orbs 20261019-102349).
- **Critical Aim lost Focus on a blocked round.** `NewProjectile.HitUnit` destroys a round an
  actor's `BlockProjectile` stops without `OnHit`, so counting every hitless `OnDestroyed` as
  a miss wiped Focus. Focus is now lost only on `OnMiss` (range out) and `OnCollide` (a
  non-actor). **Ordering found in the fix:** a range-out runs `m_unit.Destroy()`, and so
  `OnDestroyed`, *before* the `OnMiss` loop (NewProjectile.Update), so `OnDestroyed` must not
  mark the round done. The first try did, and `focus_lost_on_miss` failed (run
  20261019-101136); fixed, PASS 20261019-101525.
- **The Over-Reload bonus expired after 120 s.** A buff always counts down (ActorBuff.Update
  `m_duration -= dt`), so `perfect_reload_N` now lasts 2 000 000 000 ms (about 23 days).
- The per-frame ClearPerfect on an empty clip is gone: the clip's lose-effects already remove
  the bonus (`over_reload_lost_when_dry` still PASS). Marker and skill ids are hashed once.
- `gl targets` reports `count` (all matches) and `truncated`, as CLAUDE.md asks.
- Bot: log waits read from a byte offset and sleep 20 ms between polls instead of re-reading
  the whole log in a busy loop; the automatic-reload press no longer subtracts the elapsed
  time twice; the frag test picks its second spot as far round as the open directions allow
  (the blast is 128, not 56); a duplicate dummy clear and a crash on an empty cost list fixed.
- **Removed** the unused Flashbang, Decoy, Jetpack and Grenade Tube skills, their units
  (`decoy.unit`, `grenade_flash.unit`, `tube_shell.unit`), lang strings and icon entries;
  `info.xml` describes the current specs. They remain in git history (a8d9803).
- Not changed: stack defs are still looked up by path each frame (cheap next to the buff
  scan that was removed).
- Runs, all PASS: mod-firearms 20261019-101106, plan-firearms-a 20261019-101525, -b
  20261019-102052, -orbs 20261019-102349, -guns 20261019-102615, plan-t14 20261019-102717.

## Re-pin to 25932569; firearms bullets and the clip across floors (2026-10-19)

- **Steam updated HoH2 to build 25932569.** Re-pinned at the owner's request
  (`tools/pin_build.py --reason`), `bootstrap.py --force`, then `bootstrap.py --record` to
  rewrite `gamelab/manifest.json` (the verify step fails on every changed tree until then),
  `env_link.py`. Doctor green; smoke null-payload 20261019-121048 and mod-firearms
  20261019-121105 PASS on the new build. Verified: `GameModeSpawnPlayer` unchanged
  (`AGameplayGameMode.as:1079`).
- **A texture that isn't a power of two hangs the boot.** A 6x6 `bullet.png` logged
  `Texture sizes (6x6) should be power of two` and the game never reached the main menu
  (look-firearms-anims 20261019-122919, `main menu never loaded`). 8x8 boots.
- **Effect params named `r`/`g`/`b` don't work as sprite colors.** `color-r="r"` rendered the
  slug cyan (red 0, look-firearms-anims 20261019-124336); renamed `colr`/`colg`/`colb`, brass
  as intended (20261019-124614). `tr`/`tg`/`tb` worked for the trail. A projectile passes
  params to its effect through the behavior's `effect-params` dict.
- **Player buff stacks carry across floors.** Going from floor 1 to 2 of `dark_citadel`
  (`hwp finishlevel`) the new player unit already held the clip's 25 stacks
  (mod-firearms-clip 20261019-124230: `clip kept 25/30 (had 25, level 2)`). So the old
  fill-on-every-spawn was a free reload per floor. The module now fills only in the village
  and on the first spawn of a run's first floor (`MissionManager::GetCurrentLevelNum() == 1`,
  `g_inTown`), else keeps the count.
- **The spawn hook missed a new character's town spawn.** After `gl char hwp_firearms` in
  town no fill was logged and the clip read 0/30 (look-firearms-anims 20261019-123319). A
  unit-id watch also missed it (the new unit took the old id, mod-firearms-clip
  20261019-123825); watching the `PlayerBase` handle plus the record's class id catches it
  (20261019-124230: `clip filled 30/30 (had 0, level town)`). Assumed, not measured: at the
  new unit's first frame the record still names the old class.
- **A failed `log_has`/`log_lacks` step doesn't stop a scenario**, and both scan the whole
  pass log, so `log_lacks` after an earlier legitimate match fails. A watch run's long
  `sleep` doesn't notice the game closing; stop the runner and `gamelab reset`.
- Instant shots: `PlayerSkillDirectional` fires timeline events at 0 ms on the first update
  (`PlayerSkillDirectional.as:88-97`); every gun's castpoint and first timeline entry are 0.
- Reload's mana cost is 0 in data and measured: `mana 60/60` before and after a Reload cast.
- **Sound events: names in the data aren't proof they exist.** Seven of 28 candidate firing
  sounds named in the game's own files did not resolve (`Resources::GetSoundEvent` returned
  null), every one an uppercase `event:/SFX/...` path (e.g. `SFX/Character/Classes/rogue/flashbang`,
  `SFX/UI/UI_Click`); the lowercase `event:/sfx/...` ones did (mod-firearms-sound
  20261019-125628, then all 28 after the swap in 20261019-125819). A mod can't add a sound
  (no FMOD banks in the unpack), so `hwp firearms sound` (cheat) plays the candidates as a
  three-shot burst in watch mode for picking by ear; lab mode is muted.
- **Assault's Stun Grenade removed.** The reworked Assault is Double Barrel Burst plus
  Adrenaline; the old stun grenade was still in the subclass list, a fourth active on the bar.
  plan-firearms-b 20261019-130113: Assault's actives are reload, frag and burst. Frag's Stun
  Grenade orb keeps the stun buffs and `grenade_stun_flash.unit`.
- **No pitch control for a sound.** `SoundInstance` exposes Play, PlayTracked, Stop,
  SetPosition, SetVolume, SetParameter, SetPaused, SetLooped and SetTimelinePosition, and
  nothing else (`gamecode/assets/hwr2_api_strings.txt`), so a mod can't pitch a game sound down.
  SetParameter only drives the parameters an event was authored with (assumed: none checked).
- **Gun sounds are the user's picks** from the game's banks (heard on a web page of the
  decoded samples): rifle and Burst `bandit_rogue_bomb_bounce`, pistols `grenade_bounce`,
  grenade launcher `grenade_throw`, sniper `ballista_shoot_hit`, launcher `fire_ball_cast` (Quad:
  `magic_missiles_cast` on each of its 4 timeline casts), rocket blasts `fire_ball_explode`,
  Fat Boy `fire_blast`, round hits `item_metal_small_2`. All resolve (mod-firearms-sound
  20261019-134648). Reload sounds are script (`Combat.as` ReloadSounds): `doors/unlock` when a
  reload starts (the reloading stack or a Reload cast short of its castpoint), then
  `buttons/lever_on` 250 ms before it ends, held back while an Over-Reload window is still to
  come, or `buttons/lever_off` on a perfect reload and no lever on. Measured in
  plan-firearms-orbs 20261019-134726: every reload logged an unlock and then one lever, off for
  each of the 3 perfects, on for the misses and plain reloads, including Dodge Reload Skip.
- **More picks (2026-10-19, from the sound page):** EpiPen plays `rogue/grenade/grenade_fuse`,
  full for 1 s, faded to 0 by 2 s and stopped (`Combat.as` StartEpipenSound; the fuse runs 3.9 s);
  the Frag Grenade throws with `bandit_rogue_throw_bomb` (its old `throwing_knives_throw` is not
  in the bank's event list, so it was likely silent: assumed, from the list, not heard); placing
  a turret plays `ui/build`. The fade is measured: the hiss stopped at 2013 ms
  (plan-firearms-orbs2 20261019-205713). All three events are in the bank's event list; none was heard in game. Still Claude's picks, not the user's: the
  grenade, Explosive Reload and shell blasts, the incendiary fire, the frag bounce, the gas loop,
  the turret's shot (the rifle's sound).

## Firearms Engineer, Assault checks, the pistol arm (2026-10-19)

- **The Engineer subclass** (`hwp_firearms_engineer`): Deploy Turret (`engineer_turret.sval`,
  `Skills::PlayerSkillPosition`, a TargetAOE cast that spawns `units/turret.unit` where aimed)
  and My Turret! (`engineer_myturret.sval`, passive). The turret is `HWPFirearmsTurret`
  (`Turret.as`, a `PlayerOwnedActor`): it wears down over `decay` (30 s for the whole bar),
  and the owner within 10 m repairs it, raises its damage and feeds it elemental rounds
  (Elemental Belt-Feed), with a `turret_glow` buff as the look.
- **A summon reads its owner's skill binds through `-bind` keys.** `PlayerOwnedActor.FetchData`
  goes to the owner after `PrepareSkillFetchData(weaponInfo)` (the crusader's `hp-bind` does
  the same). Verified: the turret logged `100 hp`, `a shot every 600 ms` from Deploy Turret's
  binds (plan-firearms-b 20261019-144539).
- **One summon of a kind unless a modifier says more.** `Player.Update` resets
  `m_maxSummons = 1` for each unit producer every frame, then destroys the oldest above the
  cap. `Modifiers::ModifySummons` (`unit`, `add-max-num`) raises it: Second Turret keeps two,
  and a third placement replaces the oldest (plan-firearms-b 20261019-144539).
- **`CompositeActorBehavior.m_hp` is a fraction (0..1)**, and its `Damage()` calls
  `dmg.Attacker.DamageActor(this, dmg)`. `PlayerOwnedActorImpl.DamageActor` forwards to the
  player and skips the buff `DamageMul`, so the turret's boost scales its own damage in a
  `DamageActor` override.
- **`AnimationLoopType::Hold` at the end of a shot is the rest pose.** The wand shot
  (`attack_wand.anim`, 0.45 s, read from the ozz header) has the arm out on its first frame
  and down by its last. Holding the end looked the same as lowered (plan-firearms-arm
  20261019-143933 frames). `PlayAnimation3D` takes a trailing `animSpeedScale`, so the hold now
  replays the shot from its start at speed 0.0001: the arm stays up, and comes down by playing
  on at full speed (plan-firearms-arm 20261019-144417, the "arm held" and "arm lowered" frames differ:
  gun raised vs at the side). Assumed: the off-hand's `attack_offhand_handcrossbow.anim`
  (0.6 s) also starts arm-out; only the main hand was looked at.
- **The pistol arm comes down** 2.0 s after the last shot, at once on a dodge (logged
  `skill 1404514473`) or a reload (plan-firearms-arm 20261019-144417).
- **Bots: hold a press past the timeline.** Burst's second shell aims at 200 ms, where the
  press points; a 121 ms press sent it nowhere (plan-firearms-b 20261019-143401). The bot holds
  for max(castpoint, last timeline entry) + 120 ms. Deploy Turret's 50 mana regenerates at
  1.1/s, so the bot gives mana (`cht_give_mana`) between placements.
- **`actorbuffs` gives no name for a buff without one**; the turret glow is found as the
  300 ms buff.
- Assumed, not measured: 1 m = 16 px; the turret's base 100 hp, 0.6 of the rifle round's
  damage, armor 20 and 200 px range; NEAR = 10 m. Our Turret! (any player near) needs a
  second player and is not run.
- **Over-Reload is now +5/+10/+15 rounds** (the planner's numbers; it was +6/+9/+12). The
  bot still expected +6 and plan-firearms-orbs 20261019-145155 failed on 35/35; the game was
  right and the bot was fixed (plan-firearms-orbs 20261019-145513 PASS).
- Runs on this work: mod-firearms 20261019-144527, plan-firearms-a 20261019-144935 (the
  picker shows four doctrines), plan-firearms-b 20261019-144539 (Engineer, Assault: two
  shells at x1.2 within 80 px, Triple Barrel three, Dragon's Breath ground, a kill gives
  Adrenaline), plan-firearms-guns 20261019-145404, plan-firearms-arm 20261019-144417.
- Against a fresh planner dump after the user's orb-level changes: every
  firearms orb's level qualities match the svals (`orb_levels` check against a fresh
  dump), and Assault is Double Barrel Burst (2 shells, 200 each, +20..100% within
  5/5/7/7/10 m, 5/5/6/6/7 mana, 5 s) plus Adrenaline.

## Firearms reload rework, faster rounds, drops in the demo (2026-10-19)

- **The Reload cast is now the reload.** Before, it refilled at a 550 ms castpoint and the
  2 s cooldown came afterwards. The user wanted the whole recharge to pass before the refill,
  a dodge to cancel the reload, and no reload on a full mag. `fs_reload.sval` is now
  `HWPFirearmsReload` (Combat.as), a `PlayerSkillDirectional` subclass:
  - The castpoint is the level's recharge, 2000/1800/1600/1400/1200 ms.
  - Each upgrade sets castpoint, blocking, update-aim and timeline to match.
  - The cast list, Explosive Reload's throw and then the refill, lands at the castpoint;
    the dual Glocks' second magazine follows 100 ms later.
  - While the cast runs, `m_cooldownC` holds the time left, so the HUD icon sweeps over the
    reload. Any end of the cast sets it to 0.
- **Skill facts this rests on** (decompiled source):
  - `PlayerSkillDirectional.Deactivate` starts the cooldown only when the castpoint was
    reached, so a cancelled cast sets none.
  - `PlayerSkill.m_cooldown` is not clamped to the castpoint; `ActiveSkill.Initialize` is the
    one that does `max(castpoint, cooldown)`.
  - The dash has `ignore-blocking` (`players/attacks/dash.sval`).
    `PlayerTargetingHelper.CheckUseSkill` activates it, then `CancelOther` calls
    `Deactivate()` on every other active skill. That is how a dodge cancels the Reload cast.
  - `ActiveSkill.Activate` sets `m_castingC` (at least 1) before `CancelOther` runs. So when
    the Reload's `Deactivate` sees a casting skill of type Dash, the cancel came from a dodge.
  - Skill upgrades are per-level param layers (`PlayerClass.as`, `m_levelParams`).
- **Dodge rules:**
  - A dodge during a manual Reload cancels it and leaves the clip as it was.
  - With Dodge Reload Skip, the dodge runs the rest of the timeline (`m_timeline.Update(GetLength() + 1)`)
    and refills at once.
  - An empty clip's automatic reload (the `reloading` stack, 1.6 s) still restarts on a
    dodge. That is the planner's "if you are out of bullets, it will automatically start
    reloading again".
- **No Reload on a full clip:** `CanActivate` refuses when the clip is at its modified max,
  and plays the class's `cant` voice line.
  - It also refuses during the automatic reload unless Over-Reload is learned. Then the
    press is that reload's timing try. A missed try now ends the cast, because the full-length
    cast would outlast the automatic reload.
  - Assumed, not measured: cooldown reduction (`m_modCooldownMul`) no longer shortens the
    reload. Skill and cast speed do, because the castpoint is in skill time.
- **Bullets fly 2x as fast, same range.** Every gun round has its speed doubled and its ttl
  halved: rifle 52/240, pistol 44/180, sniper 64/300, turret 52/240, shotgun pellet 40/132,
  and the 24 elemental rounds through `%block Round`. Hits were checked at 50-90 px and by
  the turret (plan-firearms-a 20261019-152511, plan-firearms-b 20261019-152730 PASS).
- **The rounds have no trail now** (`tools/make_bullet_art.py`). Missiles and the GL shell
  keep theirs.
- **Console item cheats can't give mod items.** `cht_spawn_specific_equipment` runs in the
  [menu] script context, where there is no player and the mod's BaseItems are not loaded.
  Character creation also resets `e_cheats`. The demo therefore turns cheats on after
  `wait_phase`. It drops every firearms gun with the new `gl dropitem <baseItemId> <quality> [dx dy]`
  verb (gamelab-hands, `Item::DropItem` on an `Equipment::Generator` item).
- **The earlier demo's setup silently did nothing:** level-up, materials and spare guns all
  ran with cheats off.
- **A castpoint of 0 skips the mana cost.** `PlayerSkillDirectional.Update` calls
  `UsePoints` only when `m_castingT` moves from below the castpoint to at or above it. A cast
  starts at 0, so with castpoint 0 that never happens, while the timeline still fires its
  entry at 0. The rifle launchers had been firing free since 68551d8 ("instant shots").
  - plan-t14's `launcher_costs_mana` caught it (20261019-153855 and 20261019-154500).
  - A probe with only the launcher kept mana at 60.000, both on HEAD and with the new work
    (probe-launcher 20261019-155204, 20261019-155045).
  - The launchers now use castpoint 1: 60.000 -> 56.436 after a press (probe-launcher 20261019-155332).
  - The other castpoint-0 firearms skills cost no mana.
- **Bot lesson:** a gl call sent right after an `hwp` console line can take about 3 s. The
  manual Dodge Reload Skip check now reads the clip max first, and passes on the game's
  `reload: dodge at N/M ms finishes it` line.

## One pistol for either hand, the reload icon, quiet held trigger (2026-10-19)

- **An item's slot is its base item's.** `Equipment::Item.GetSlot()` is `baseItem.slot`
  (Items/Equipment.as:145), and the bag click equips by that slot
  (EquipmentInventoryWidget.OnClick -> EquippedItems.Equip(item), EquippedItems.as:161-190).
  No slot means "either hand". So the off-hand pistols `hwp_glock_oh_0N` stay, as twins
  that never drop or sell: spawn-chance 0, ilvl 999-999 (GenerateBaseItem filters on ilvl,
  EquipmentGenerator.as:197), no `armory` tag. `gl equip` still makes them
  (Generator.GenerateItem skips both filters).
  - A bag click runs core's new `HWP::Bag::OnEquip` callbacks first (BagSlots.as,
    `HWPEquipmentInventoryWidget.OnClick`). Firearms swaps `item.baseItem` for the twin
    when the main hand is full and not two-handed and the off hand is free.
  - The swap is safe after Finalize. `GetModifiers` picks an item mod's main- or
    off-hand list from `baseItem.slot` on every call (Equipment.as:147-161), and
    `ItemModifier` loads both lists for any handed mod (Equipment.as:540-551).
  - Back in the bag, a twin turns into the main-hand pistol (Pistols.as, 4 times a
    second). That covers an unequip and a two-hander bumping it off.
  - Verified: mod-firearms-pistols 20261019-162530. Two pistols clicked in the bag went
    rifle -> main hand -> off hand (`hwp_attack_glock` + `_off`). Unequipped, the off-hand
    one came back as `hwp_glock_mh_01` and went back on the off hand.
- **Equipping is a menu accept on the bag slot.** The Equip hint isn't clickable
  (`navbar` clickable `[true,false,...]`). A bot hovers `equipment-inventory <i>` and
  posts Enter. A slot's index is its place in `EquipmentInventory.m_items`, and an
  unequipped item is appended.
- **The automatic reload's look for the Reload cast.** The HUD sweep on the reloading
  icon is the stack's `display-timer-radius`: `GetBuffIconDuration` = `m_timerTickC`,
  max = `m_defMod.m_timerTime` (ActorBuff.as:811-823). The new `reload_cast` stack uses
  the same icon. HWPFirearmsReload holds one stack while it casts and sets `m_timerTickC`
  to the time left each frame, with `m_defMod` pointed at its own copy whose timer is the
  whole cast. Verified: "cast icon on, 1967/2000 ms" and the HUD frame (mod-firearms-pistols
  20261019-162257, shot reload_icon).
- **Why a held trigger said "cant".** A repeating attack held down calls
  `skill.Activate` every frame (PlayerTargetingHelper.as:631-645). Activate calls
  `CanActivate()` with warn on (PlayerSkillDirectional.as:49), and the clip conditional's
  failure plays "cant" (PlayerSkill.as:344-349). `HWPFirearmsGun` (the 4 gun attacks)
  warns only while armed. It arms whenever the button is up (`GetSkillInput(this).Down`
  false, in Update) and disarms at the first warned check, shot or warning. Verified:
  7 s held through the clip running dry and the reload gave no warning, and a fresh click
  during a reload warned once (mod-firearms-pistols 20261019-162530).
- **Muzzles.** The pistols sit about 5-6 px either side of the unit's position, the main
  hand on the right (look-firearms-muzzles 20261019-161736, zoomed frames, six aims).
  `rotate-offset` turns (0, +y) to the aim's right (ShootProjectile.as:96-97:
  `addrot(offset, aim angle)`). So main-hand rounds use (0 6) and off-hand rounds (0 -6).
  The old offsets were ±2 and had the main hand's rounds on the left.
- **Gun sounds with a volume.** `HWPFirearmsSound` is a PlaySound whose instance
  (`SoundEvent.PlayTracked`) gets `SetVolume`. The pistols now use the rifle's
  `bandit_rogue_bomb_bounce` at 1. The rifle is at 1.4. Assumed, not measured: FMOD
  treats an instance volume above 1 as gain (the lab is muted).
- **The lab town has no Skill Trainer.** Skills are learned at its `npc_skill_trainer.unit`
  (Town/SkillTrainer.as:19, `SkillUp`). Without one, a new Sniper's Sniper Shot can't be
  learned in the demo. The demo spawns the trainer next to the Subclass Picker. Verified:
  it opens with all six Marksman skills (probe-subclass 20261019-162631). Through `gl skill`,
  Sniper Shot lands on skill key 2 (probe-subclass 20261019-161323).
- **Demo:** watch mode is 2560x1440 now (`gamelab/env/settings/watch/HWR2.exe.cfg`). The demo
  also has five training dummies (normal x2, armored, magic, breakable) and two of each
  pistol tier.
- **A one-off crash on quit.** mod-firearms 20261019-162710 passed every step, then the
  game exited with 0xC0000005 while saving on quit. That left a dirty teardown. The same
  code then passed 3 times with clean exits (20261019-162913, -162925, -162937). One
  earlier run had the same exit code, with no firearms code involved (plan-pets-b
  20261018-132915). Treated as an intermittent engine crash at shutdown, not a bug in the mod.

## Items before vendors, the demo in one command (2026-10-19)

- **Why a vendor blocked a pickup.** `Player.GetTopUsable` returns the first usable in
  `m_usables` that CanUse. `AddUsable` keeps that list sorted by `UsePriority`, lowest first
  (Behaviors/Actors/Player/Player.as:135-167). A dropped item is 1 (Items/UnitBehavior.as:299),
  while NPCs, shops, chests, shrines and wells are 0. Revives and level exits are -1, and pyres
  and beacons are -5. So with a vendor and an item both underfoot, Use always talked to the vendor.
- **Fix: core reorders, no class swap.** `HWP::PickupFirst` (mods/core/scripts/HWP/Core/PickupFirst.as,
  run from CoreModule.UpdateFrame) re-sorts the local player's list each frame. It uses a stable
  sort that ranks an item between -1 and 0. A subclass of `Item::UnitBehavior` would not work:
  vanilla pets find items with `FetchUnitsWithBehavior("Item::UnitBehavior", ...)`, and that
  call's `includeInherited` defaults to false (api strings, MiniPet.as:284).
  - The same default means `mods/pets`' `FetchUnitsWithBehavior("Chest", ...)` (Pets.as:993)
    misses keys' `HWPChest`. Assumed, not yet measured.
  - Verified: mod-core-pickup 20261019-163842. With a Skill Trainer and a dropped rifle at the
    player's feet, `usables` listed `items/base.unit` on top, ahead of the
    `CompositeActorBehaviorNPC`. Use put the rifle in the bag and opened no window.
- **The demo setup is one typed command.** Typed console lines garble when the player presses
  keys while the harness types (demo-firearms 20261019-163131: `.unit` arrived as `.sunist`, then
  every line had a stray leading backtick, "No such cvar: `gl"). The runner gave up on a line
  with no reply and closed the game. The script API has no way to run a console line, so
  gamelab-hands has new verbs:
  - `setup <file>` runs every line of an sval array of verb lines in one frame
    (`gamelab/setup_demo_firearms.sval`, 27 lines). It replies with `failed` and the failed lines.
    The probe's `Fail()` counts failures (`g_fails`).
  - `cheats`, `levelup` and `points <skill|stat>` mirror core's `hwp` cheats.
  - `material all <n>` gives n of each material.
  - Verified: mod-core-pickup 20261019-163842 (`failed` 0). demo-firearms 20261019-163941
    (watch, 27 lines, 0 failed).
- `hwp levelup 20` from level 1 gives level 20, not 21. The old demo's "level 21" was wrong
  (its 16:31:48 log line says "now level 20").
- **Dummies hidden in the barricade.** The demo's dummies at dy -80..-100 stood inside the log
  barricade north of the lab-town start (mod-core-pickup 20261019-163842, shot after_use). They
  now stand in a row on the open road east of it, dx 110..230 (20261019-164119, shot after_use).
- **Rounds start at the gun tip.** ShootProjectile starts a round at
  `pos + dir * dist + offset` and clamps it to the first wall on the way (`RaycastClosest`,
  ShootProjectile.as:121-128). The guns' `dist` was 5, the body. Measured from frames, the
  rifle's tip is about 13 px ahead of the player's centre, the pistols' about 8-9 px, and both
  are held about 10-12 px up (look-firearms-muzzles 20261019-161736, look-firearms-tips
  20261019-164426).
  - First values: the rifle, its launcher, Burst and Snipe dist 14, the pistols 9. Every gun
    round's `effect-params height` is 11, up from 8.
  - Assumed, not seen: the frames show the guns, but every round had already left the frame
    by the time it was taken, even at timescale 0.1.
  - The rifle's round still looked as if it started too close in play. The round sprite is centred
    on its spawn point (rifle round origin "9 3.5", about 10 px long), so half of it was drawn
    behind the tip. Now: the rifle, its launcher, Burst and Snipe use dist 22, the pistols 12.
    `HWPFirearmsGunShot.ProduceProjectile` (Elemental.as) records where the last round started,
    relative to the aim, and `hwp firearms muzzle` prints it. Measured: rifle 22.0 ahead, pistols
    12.0 ahead and 5.2 to the side (look-firearms-tips 20261019-165353). Verified.
- **Snipe uses mana, not rounds.** sniper_snipe.sval lost its clip conditional and its
  `AddStacks -10`; it still costs 30/30/40/40/50 mana. Measured: clip 27 before and after one
  Snipe, mana 60 to 32 (look-firearms-tips 20261019-165353). Verified.
- **Snipe's laser dot.** Snipe is a PlayerSkillDirectional whose castpoint (650 ms) is the
  charge. `HWPFirearmsSnipe` (Combat.as) overrides `Update`: while `0 <= m_castingT < m_castpoint`
  it raycasts (`RaycastType::Shot`) from the player along `m_timeline.m_dirTarget`, up to
  `SNIPE_REACH` 300, and keeps `effects/laser_dot.effect` at the hit point or the end of
  reach. It destroys the dot when the cast ends and in `Deactivate`.
  - The texture is vanilla's 64x1 `player_white_singlepixel_gradient.png`, whose pixels 0-1 are
    only 15% opaque (alpha 38), so the dot was invisible until its frame moved to x 32.
  - Measured: "snipe: laser dot on, 199.5 out (hit)", and the frame shows a red dot on the tree
    trunk that the aim line hits (look-firearms-tips 20261019-165939). Verified.
  - Assumed: 300 is about the rifle round's range. The range record stayed 0.0 because every
    round in the measurement hit something.

## Gun hold, even pistols, turret radius, Hoarder HUD, demo orb and trainer (2026-10-19)

Status: measured where a run is cited; the rest says which run checks it.

- **The game's metre is 6 px** (`Tweak::PixelsPerMeter`, Data/Misc.as:15; `formatMeters`
  divides by it, Utils/Functions.as:777). The firearms notes assumed 16 px. That is wrong, so
  "10 m" was 160 px, about 27 m.
  - My Turret!'s `NEAR` is now 60 px, a true 10 m. The user saw the boost stay on after walking
    away. The demo's log shows it did switch off ("turret: unboosted" at 17:05:08, 17:05:14 and
    17:05:27, demo-firearms 20261019-170119), just far out.
  - plan-firearms-b's `myturret_only_near` places a turret 120 px out, sees no boost, then walks
    up and sees one (20261019-191214 PASS). Walking off at once failed (20261019-183730): no
    "unboosted" within 2 s of a 1.5 s walk, so the check now walks in.
  - Double Barrel Burst's close ranges (80/112/160 px, labelled 5/7/10 m) are left as tuned.
- **The arm hold covers every gun.** `AimHold` (Combat.as) only listed the two pistol attacks,
  so the rifle lowered after each shot. `GUNS` now lists the rifle, the epic rifle, both grenade
  launchers and both pistols, and `HOLD_MS` is 1000.
  - The rifle's `crossbow-2h` set plays `attack_2h_crossbow.anim`. Assumed: its first frame has
    the rifle up, as the wand shot has the arm out. plan-firearms-arm takes frames for both guns.
- **A held repeating attack drops the overshoot.** PlayerSkillDirectional.Update deactivates
  at `m_castingT >= m_skillLen` (:99), and the next activation starts at 0. So the cycle runs up to
  a frame long, and the right gun's gap back to the left one is longer than left to right.
  - Measured before the fix: gaps alternated 264/330 ms (look-firearms-batch 20261019-183547).
    PlayerTargetingHelper's restart of a held repeating skill (:629-646) comes a frame after the
    deactivation, so the shot at 0 fired a frame late.
  - `HWPFirearmsGun.Update` now restarts the held skill itself, in the same frame it ends. It
    carries the overshoot, capped at 100 ms (`CARRY_MAX`), into `NetActivate`, then calls
    `CancelOther`, `TriggerModifierEffects` and `m_timeline.Update` as the helper does. A `const`
    class property doesn't compile in AngelScript, so `CARRY_MAX` is a plain `int`.
  - The pistol cycle is now 600 ms, with shots at 0 and 300; it was 520 and 260.
  - `hwp firearms shots` prints the gaps between the local player's last 16 rounds. After the fix:
    `264 297 297 297 297 264 297 297 297 297 297` (look-firearms-batch 20261019-190049). Mostly
    18 frames, with a 16-frame gap about one in five, where it used to alternate 16 and 20.
- **Ordinance Hoarder on the HUD.**
  - SkillWidget dims the icon whenever its frame ring shows a cooldown (:333), and draws the
    whole ring when the skill is ready (:362).
  - `HWPFirearmsChargeHUD` (ChargeHUD.as, added by a `HUDConstructor` hook and drawn after
    HUDPlayer with its transform) darkens the part of the ring not banked yet. It uses the
    two-ended `DrawSpriteRadial(pos, sprite, time, a, b, color)` (the engine's API strings),
    from `HoardedSkill.m_progress`.
  - The charges' icon is now `<id>_shown`: every use ready, the stored charges plus one when the
    skill is off cooldown, removed at 0. `<id>` keeps the store with no icon.
  - Measured: plan-firearms-b `hoarder_icon_counts_all` (icon 2 ready, 0 on cooldown,
    20261019-191214). In look-firearms-batch 20261019-191742 the icon goes 2 -> 1 when a rocket
    spends the stored charge, and the ring starts banking ("slot ring shows a charge banking, 0%").
    Frame `ring_banking` (640x360) shows the rocket slot's ring dark with its icon bright; frame
    `ring_full` shows the whole ring.
- **Demo orb** (verified: two picks from one sphere, look-firearms-batch 20261019-183547 frame
  `orb_second`). `GameLabEndlessSphere` (gamelab-hands DemoSphere.as) is a SkillSphere whose
  `PickedSkill` clears the rolled picks and returns true instead of hiding the sphere.
  GiveSkillSphereMenu grants the orb only when it returns true (:266-287).
  The unit is gamelab/skill_sphere_endless.unit.
- **A spawned Skill Trainer sells tier 0 only.** NPCs get `ShopLevel` (an `[Editable]` field,
  NPCBehavior.as:244/431) from their town building, and the trainer opens tiers up to it
  (WindowSkillTrainer.as:192/255; tiers 0-4). The new verb `shoplevel <filter> <level>` sets it;
  the demo setup sets 4. Frame `trainer` (look-firearms-batch 20261019-183547) shows no locked tier.
- **Double Barrel Burst's close bonus** is now x1.5/2/2.5/3/3.5, up from x1.2-2.0, because the
  user asked for much more. It is still a step at close-range.
- **A unit spawned on a standing player is not a usable** until a collision starts: usables are
  added in the unit's `Collide` (SkillSphere.as:6-17, NPCBehavior.as:341) and dropped by the
  player's 250 ms `IsInside` sentinel (Player.as:1009-1019). After the demo setup, a trainer and
  a rifle dropped at the player's feet gave `usables []` until the player stepped off and back
  (diag-usables 20261019-185932). mod-core-pickup now takes that step (20261019-190009 PASS).
- **`hwp levelup` and `hwp skillpoints` need `e_cheats 1`** ("cheats are off",
  look-firearms-batch 20261019-190049); `gl setup`'s `cheats on` line is what the demo uses.
- **The demo's watch run ends after its 3600 s sleep** (demo-firearms 20261019-170119, 3638 s).
  The game closes then, even mid-play.

## Firearms class showcase (2026-10-20)

- **The class list draws one 32x32 figure per class** from the class's `class_showcase.png`
  (vanilla packs all classes in one 128x128 sheet of 32x32 cells, each a figure facing the
  camera on a 16x16 shadow disc of (0,0,0,126), feet at y 30). The Firearms one was a gun in a
  ring; it is now the starting outfit with a pistol.
- **The character screen's paperdoll is close to 2x** in a 640x360 lab shot (2x2 blocks agree
  about 80 %), so a 2x2 mode downsample gives a 12x23 figure, the size of vanilla's. The town
  view is too small to use (look-firearms-showcase 20261020-001654, frames `charscreen`,
  `town_down`).
- **The create-character window opens from town** through `HWR2GameMode.OpenCreateCharWindow()`
  (HWR2GameMode.as:260), what PickCharacterWindow's new-character button calls (:261). The new
  gamelab-hands verb `charcreate` calls it. look-class-list 20261020-002117 frame `classlist`
  shows the Firearms Specialist selected among the vanilla figures, the same size as theirs.

## Party key pool and floor key budget (2026-10-20)

- **Found keys go into one party pool on the host** (`HWP::Keys::g_pool`), kept in the host
  record's bag (`keys.pool`, plus `keys.pool_run` = `m_missionRewardSeed`, so a new run or
  town clears it) and broadcast as the `keys.pool` event. Clients ask for it at level start
  (`keys.pool_get`) and ask the host to spend one (`keys.pool_spend`) when they open a chest
  with it. Bought keys stay on the buyer's record, as in vanilla.
- **The budget is per floor and per tier:** `floor(locked × share)` plus the fraction rounded by
  a hash roll, minus the party keys of that tier held when the floor started, where share =
  `keys.budget_share` 0.5 + `keys.budget_per_player` 0.1 × (players − 1), at most 0.95. The
  floor's locked chests are counted as `HWPChest` locks them (`g_lockedTier`).
- **mod-keys-pool 20261020-003440 (bandit_keep floor 1, solo):** 3 locked bronze chests, budget
  bronze 2. With `keys.accept 1`, culling the floor dropped exactly 2 bronze keys, then no more
  (budget 0/2). A key from `hwp keydrop` went into the pool (record bronze 0, pool bronze 1),
  and opening a bronze chest took the pool key and left the 2 bought gold keys alone. Shots
  `hud` and `hud_after` show the key icons left of the skill bar (bronze 1 and gold 2, then
  gold 2).
