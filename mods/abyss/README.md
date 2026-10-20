# abyss

Path of Exile's Abyss, scaled down to a HoH2 level.

- **Placement.** Host, once per run level (3 s in), `abyss.chance` (30 %):
  `doodads/hwp/abyss_crack.unit` (vanilla shadow-rift effect, purple light,
  `netsync="position"`) at the position of a random live enemy at least 800 px
  from every player. `hwp abyss here` opens one next to the host.
- **Waves.** `HWPAbyssCrack` (host): dormant until a player is within
  `abyss.trigger` px (130). It then samples up to five enemy producers from the
  live enemies within 1600 px and runs `abyss.waves` (3) waves of
  `abyss.wave_base` (3) + `abyss.wave_per_player` × players + wave index
  enemies. Each wave erupts 70 px further along a random line and leaves a
  smaller fissure behind (`abyss_fissure.unit`). A line that runs into or behind
  a wall is re-rolled (up to 8 times, then the wave erupts at the crack), so late
  waves don't lose their members to blocked spots. The last wave adds one
  `_elite` variant per two players (1, 1, 2, 2; two extra normals for each
  when none exists), and with three or more players waves 2 and up get one
  too, so the party size sets the difficulty. A wave ends when all
  its enemies are dead or after 2 minutes; 1.5 s pause between waves.
- **Payout.** After the last wave the host spawns `hwp_abyss_reward_<tier>`
  (`tweak/hwp/loot_abyss.sval`: gold, a valuable, a trinket and an equipment
  piece) at the crack for the nearest player and removes the crack and
  fissures. The tier follows the floor's diff-level (`g_diffLevel`, new game+
  included), on the key tiers' breakpoints, so the reward grows with the run:

  | Tier | Diff-level | Gold | Valuable | Trinket | Equipment |
  |---|---|---|---|---|---|
  | 1 | up to 7 (Dark Citadel's first floors) | 40-90 | 60 % | uncommon, 20 % rare | uncommon, 30 % rare, ilvl +0-1 |
  | 2 | 8-13 (mid run, side missions) | 90-180 | yes | rare, 10 % epic | rare, 15 % epic, ilvl +0-2 |
  | 3 | 14+ (late floors, new game+) | 250-450 | yes | rare, 40 % epic | rare, 35 % epic, ilvl +1-3 |

  Tier 1 is about a silver chest, tier 2 a gold one, tier 3 a little more than
  a platinum one. `hwp abyss` shows the tier of the current floor.
- **Messages.** `abyss.wave {n,total}` and `abyss.done` are broadcast and shown
  as chat lines on every machine.
- Settings: `abyss.enabled`, `abyss.chance`, `abyss.waves`, `abyss.wave_base`,
  `abyss.wave_per_player`, `abyss.trigger` (host-synced).

## Test checklist

1. `python -m gamelab run mod-abyss --mode lab`: `[HWP:abyss] self-check done`, no missing unit/loot errors.
2. Host a run, `hwp abyss here`, walk onto it: "The ground cracks open! Wave
   1 of 3"; waves advance as you clear them; the third has an elite; loot
   drops and the crack vanishes.
3. `abyss.chance 100`: the log shows `placed a crack at ...` on each level and
   it sits away from the start.
4. Co-op: the client sees the crack, the waves and the chat lines; with three
   players waves 2 and 3 have elites, the last one two.
5. `python -m gamelab run mod-abyss-tiers --mode lab`: Dark Citadel floor 1
   pays `hwp_abyss_reward_1`, its new game+ floor 1 `hwp_abyss_reward_3`.

Timeout: a wave that is still alive after 2 minutes closes the crack without
a reward (no next wave, no loot). Wave members only spawn on free spots; a
wave with no free spot at all closes the crack too.
