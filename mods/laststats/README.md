# laststats

Keeps the end-of-run statistics screen around after you are back in town, for
everyone in the party, on a **notice board** next to the town fountain.

- A `PlayerRecordLoad` hook snapshots the local player's `statsRun` when a
  town loads the character with a finished mission state (Succeeded / Failed /
  Aborted). The module's `Start` stores the snapshot. That hook is the only point
  that sees the result: module constructors run before the character loads, and
  `PostStart` opens the vanilla `MissionEndMenu`, which resets the state and
  `statsRun` before any `Start` (docs/RE_NOTES.md). (`Module::Load` only runs when a
  level is restored from a save, so it can't be used.)
- The snapshot (mission, result, every visible non-zero stat, pre-formatted)
  lives in the player record under the `hwp` bag, key `laststats.mine`, and is
  sent to the host (`laststats.report`) two seconds after load. The host keeps
  one snapshot per player name and rebroadcasts the list (`laststats.sync`).
- The board (`doodads/hwp/laststats_board.unit`, reuses the base
  `mission_board.png`) is produced by the host when a town loads, at world
  (-440, 110); move it with `hwp set laststats.board_x <n>` and `board_y`
  until the spot is right. Interact opens `HWPLastStatsMenu`
  (`gui/hwp_laststats.gui`): `<` `>` page through players, categories match the
  mission-end screen (`.menu.stats.cat.*`).
- `hwp laststats` prints what is stored.

Not in the snapshot: per-skill damage lines (they need the player actor, which
does not exist at Load time) and the death recap (the `deathrecap` module keeps
its own).

- The board comes back after a building upgrade, which rebuilds the town and
  destroys it; the host notices within a second and spawns it again
  (`HWP::Town::Kept`; test: `mod-town-rebuild`).

## Test checklist

1. `python -m gamelab run mod-laststats --mode lab`: no script errors; `[HWP:laststats] spawned the notice board`
   when entering the town as host.
2. Solo: run any mission, die or abandon it, return to town. Log shows
   `snapshot of <name>: N stats, Defeated`. The board by the fountain opens a
   window listing the same categories/values the mission-end screen showed.
3. Reload the save: the board still shows the run (bag persisted).
4. Co-op: after a run both players appear on the board on both machines; a
   player joining later gets the list once their own report triggers a sync.
5. Fresh save: the board shows the "No run recorded yet" text.
