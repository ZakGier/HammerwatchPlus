# summons

Priest improvement: **Crusader summons persist between floors**. The pikemen,
crossbowmen and boon pikemen that were alive when you took the exit are there
next to you on the next floor, with the HP they had.

**The current game does this itself** (verified in GameLab, probe-summons-off
2026-10-18: with this module off, 2 damaged crusaders came through a floor
change at the HP they had). `Player`'s constructor produces the record's
summons from their save data. The module was built on the belief that the
game drops them (never checked then), and it now only fills a shortfall:
per kind, the snapshot count minus what is already live. Before that fix it
produced every snapshot entry on top of the game's own, giving one crusader
too many (plan-t12: 2 in, 3 out).

- **How.** Every 500 ms during a run, the local player's tracked summons are
  snapshotted with the game's own `SaveUnit()` (the same data a save game
  stores). On the next floor's `GameModeSpawnPlayer` for the local player,
  the snapshot is produced again next to the player the same way `Player`'s
  constructor restores summons from a save game: the host produces directly,
  a client sends the vanilla `SpawnPlayerSummon` message to the host. The
  skill's `max-summoned` cap is still enforced by `Player::Update`.
- Town clears the snapshot (nothing follows you home). Summons that died
  before the exit are not restored.
- Tracked units: `players/priest/units/crusader_pikeman.unit`,
  `crusader_crossbowman.unit`, `crusader_pikeman_boon.unit`. Setting
  `summons.all` (default off) tracks every saveable summon instead (wolves,
  Warlock minions, ...). `summons.enabled` turns it off. Both host-synced.
- `hwp summons` shows the state, snapshot size and how many were restored on
  this floor.

## Test checklist

1. `python -m gamelab run mod-summons --mode lab`: `[HWP:summons] self-check done: 3/3 tracked units`.
2. Priest with Call Crusaders: summon 2-3 crusaders, take the exit. On the
   next floor the same number are next to you at once, with their HP, and
   no more than that (`hwp summons`: "0 restored" while the game carries
   them). `python -m gamelab run plan-t12 --mode lab` runs steps 2-4.
3. Let them all die before the exit: nothing is restored.
4. Return to town: no crusaders in town on arrival (the passive skill
   summons a fresh one in town a second later, as in vanilla).
5. Co-op: a client Priest's crusaders also come through (host produces them).
