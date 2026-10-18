# architect

Architect alterations for the whole party.

- **Everyone can pick.** The Architect row in the run-start loadout is enabled
  for every player (vanilla: host only). Picks go to the host
  (`architect.pick`), which keeps one merged list with the payer of each pick
  and syncs it to everyone (`architect.sync`); the list shows `- name (payer)`
  and only the payer can remove their own pick.
- **Who pays what** (`SelectArchitectLoadout.CalcMyCost`): a sponsor pays the
  full price of their picks; the host's picks are **split evenly** (rounded
  up) across all players when the host setting `architect.split` is on
  (default). The vanilla cost multiplier counts every pick regardless of payer.
  `GetCost()` now returns the local share on clients too, so a player who
  cannot afford their share cannot ready up, and the share is deducted on each
  machine when the host starts (`OnPlay`).
- Override: `scripts/Missions/MissionArchitect.as` (declared in
  `module.json`, pristine `.orig` next to it, every change marked `HWP`).
  Vanilla's `SyncMissionLoadoutArchitect` message keeps working (host pays).
- **Challenges** (HoH1's fountain "bad wishes"): seven free alterations in the
  Architect list (`tweak/hwp/architect_challenges.sval`). Each one takes its share
  off the cost of the alterations you buy. The shares are summed and capped at
  100%, so a run can become free, but challenges never pay out gold or materials
  (`HWP::Architect::CostMul`, in `scripts/HWP/Architect/Challenges.as`):

  | Challenge | HoH1 wish | Effect | Discount |
  |---|---|---|---|
  | Crowded Halls | more_enemies | enemy density x1.35 | 15% |
  | Champions | more_elites, minibosses_everywhere | elites and minibosses allowed on every floor | 15% |
  | Lean Pickups | bad_pickups | health/mana pickups x0.5 | 10% |
  | Bitter Draughts | potion_confuse | drinking a potion confuses you (5 s) | 10% |
  | Glass Bones | 1_hp | damage taken x1.4 | 25% |
  | Sharpened Traps | more_trap_damage | trap damage x2 (`Modifiers::HWPTrapDamage`) | 10% |
  | Slim Pickings | no_ore | wood/stone/iron/crystals/dust/ore x0.5 | 15% |

  Crowded Halls and Champions change the level. `ChallengeSetup` is a generation
  command the module ctor puts first in every dungeon generator. It sets the
  enemy placer from the generator's own values each time it runs, because Generate
  retries from scratch. The others are modifiers on the mission buff; like every
  architect pick, the host's apply to the whole party.
  The other HoH1 wishes (no shops, wells, secrets, elevators or loot drops; faster
  enemies; titles off; less luck) have no clean HoH2 hook and are left out.
- Commands: `hwp architect` (list picks + payers), `hwp set architect.split
  false` (host only; rebroadcast immediately), `hwp architect challenges [id...]` (the
  challenges and the cost multiplier of a pick list), `hwp architect try <id...>`
  (cheats, host: these picks for the next level).

Morning decisions:
- The **town fountain** as a second entry point for sponsoring (open the
  picker in town, outside the loadout screen). The well/fountain unit sits at
  local offset (104,16) of the `town_square_*` prefabs (square 4 is at world
  -608,128); it needs an interact behaviour added by code or a classmap on the
  well unit. Not done yet.
- "Host approval required" mode and refunds on cancel (currently nothing is
  charged until the run actually starts, so cancel costs nothing).

## Test checklist

1. `python -m gamelab run mod-architect --mode lab`: no script errors; `python tools/build.py --check` reports the
   override as `OK`.
2. Solo (Dark Citadel / Mega Dungeon board): architect row is clickable, picks
   work, cost and multiplier match vanilla, gold is deducted on start.
3. Co-op: client opens its loadout, sees the architect row enabled, picks an
   alteration; both see `- name (client)` in the list. Host picks one; both
   see `(host)` and the client's cost shows half of the host's pick plus the
   client's full pick. Start: each pays their share (check gold before/after).
4. Client tries to unselect the host's pick: nothing happens; unselecting its
   own pick works and the host's list updates.
5. `hwp set architect.split false` on the host: the client's cost drops to its
   own picks only.
