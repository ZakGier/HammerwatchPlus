# wavemode

**Wave Arena**: a Hammerwatch 1 Survival / HoH1 Arena style mode on top of
the vanilla `SurvivalMission` level module (the one the Celestial Ruins
DLC uses). A statue in town starts it; every boss kill raises your arena
rank, and the rank is the arena's NG+ level next time.

- **Mission** `hwp_wave_arena` (set `hwp_wave`): one generated keep floor
  (bandits, elites, density 1.2) with the survival module: 10 minute clock,
  XP goal 15000, 4 spawn events (the vanilla shade / phantom / cult / wisp
  events from `missions_heaven_actions.sval`), boss =
  `prefabs/hwp/wave_boss_spawner.pfb`. The survival module loads `boss` with
  `Resources::GetPrefab`, so it must be a spawner prefab: a `.unit` there left
  the prefab null and the champion never came (fixed 2026-10-18).
  `tools/make_wave_boss_prefab.py` copies the valor trial's
  `heaven_warrior_spawner.pfb` (intro, music, enemy clear-out, exit portal) with
  the boss swapped for `actors/hwp/wave_boss.unit` and the trial's achievement
  and `boss_warrior` character flag unlinked; rerun it (`--check` reports a stale
  copy) after patches. `wave_boss.unit` is
  a copy of the valor spirit warrior with its `stat-reward valor` removed so
  arena clears never raise the heaven DLC valor rank (keep it in sync with
  `actors/bosses/spirits/warrior/boss_spirit_warrior.unit` after patches),
  `progress-rank-multiplier` 0.25 so the XP goal grows with rank,
  `max-rank-reward` 3.
- **Statue** `doodads/hwp/wave_statue.unit` (the vanilla valor statue
  sprite) with interact class `HWPWaveShopContent`, a
  `MissionSurvivalShopContent` subclass: the rank it offers is the HWP
  setting `wave.rank` (host-synced) instead of the heaven `valor` stat, the
  entry is never NG+-gated, and `GetBoonDetails` does not append a boon
  skill (the vanilla one null-derefs on a boon without a skill). Host:
  `MissionManager::SetMission` + the loadout menu with
  `MissionSpecSurvival(rank)`; client: HWP request `wave.start`, the host
  gets the vanilla "X wants to start" yes/no dialog and `HWPWaveClientStarter`
  opens the loadout menu at the host's rank (the vanilla `RequestStartingMap`
  only treats the number as NG+ for the heaven set, ours would be rescaled
  from an item level).
- **Boon** `hwp_wave_boon` (`tweak/hwp/buffs_wave_boon.sval`): shown in the
  survival window; same valor armour bonus as the vanilla warrior boon.
- **Rank up.** The killer's machine sees `PlayerKilledActor` for an actor
  with the `boss` tag while the current mission is `hwp_wave_arena`; the
  host awards `max(1, g_survivalReward)` (the survival module's own 1..3
  speed reward) once per floor, saves `wave.rank` in the town record and
  broadcasts `wave.awarded`; a client sends `wave.bosskill` and the host
  checks the mission before awarding.
- Host spawns the statue (`HWP::Town::Placeable`) 0.6 s after the town loads, beside
  the campaign portal: 112 px left of the chapel's Pyre slot
  (`HWP::Town::ChapelPyreSpot`, 872,-232 in the default town), or 72 px lower
  when that is blocked (a built Pyre). It used to default to -1500,250, inside
  the trading post's plot and 64 px from a beach fishing spot, so pressing use
  there could open the fishing window instead (seen in GameLab, 2026-10-18).
  A spot saved with `hwp wave here` (`wave.statue_x/y`) wins; `hwp wave here`
  moves it, `hwp wave rank <n>` sets the rank (host), `hwp wave goal [percent]`
  (cheats, host, in the arena) fills the survival bar so the next kill brings
  the champion (with a percent, part way: past a checkpoint, the next kill fires
  that spawn event), `hwp wave` shows
  the state. `wave.enabled` turns it off.
- Known limits for the morning: the arena uses heaven enemies for the
  spawn events (they exist for everyone, the DLC only gates the missions);
  the boss is the valor spirit, not an arena champion of its own; the
  rank has no cap.

## Test checklist

1. `python -m gamelab run mod-wavemode --mode lab`: `[HWP:wave] self-check done: mission ok, boon ok, 4/4 spawn
   actions, rank 0`; no missing unit lines.
2. Town: the statue stands left of the campaign portal in the chapel courtyard (872,-232). Interact opens the survival
   window with "Wave Arena", the Arena Champion boon and rank 0; Start
   opens the loadout menu and the run begins on a keep floor with the
   survival bar on the HUD.
3. Kill until the bar fills: spawn events fire at the checkpoints, the
   spirit warrior appears; kill it -> chat shows "Arena rank up! Rank N"
   and `hwp wave` agrees back in town; the statue now offers rank N.
4. Let the clock run out: everyone dies (vanilla survival rule); no rank.
5. `hwp wave rank 5` then start: the arena is NG+5 (enemy levels up).
6. Co-op: a client can start the arena (request to the host) and a client
   boss kill still raises the host's rank.
