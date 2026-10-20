# keys

HoH1-style locked chests, keys, the exit guard's General Merchant (keys, bag
slots, trinkets for the next run) and red legendaries.

- **Locked chests.** `Chest` is swapped for `HWPChest` (module.json `class_swaps`: `tools/class_units.py` copies the chest units with our class). Every reward chest
  (`items/chests/chest_<bronze|silver|gold>_<trinket|equipment>.unit`, and the
  treasury rooms' `chest_platinum`, which takes a gold key) locks on its first
  tick and needs a key of its own tier; without one it shows a cross and a
  "Needs a Bronze Key" tooltip and does not open. Cursed chests and resource
  caches need no key. A locked chest shows a padlock tinted by tier and pays
  its own vanilla loot. `keys.lock_chance` (default 1) can make it a share;
  the roll is a hash of the chest's position, the mission reward seed and the
  level index, so host and clients agree without a message.
- **Ace chests.** 15 % of gold chests (`keys.ace_chance`) turn red and
  need an ace key. Opening one spawns the chest's own loot plus, 50/50
  (`keys.legendary_chance`), either an epic equipment drop or one red
  legendary **per player in the lobby** (instanced through `Item::DropItem`;
  tables in `tweak/hwp/loot_chests_ace.sval`).
- **Party key pool.** Keys found in a run (drops, the imp's offer) go into
  one pool for the whole party, held by the host (`HWP::Keys::g_pool`, kept on
  the host's record so it outlives the level, broadcast as `keys.pool`). Every
  player sees the same counts and anyone can open a chest with them. A new run
  starts with an empty pool, so unspent found keys don't pile up across runs.
- **Own keys.** Keys bought from the General Merchant are the buyer's:
  vanilla `PlayerRecord.GetKeys` and the record's `keys` dictionary, changed
  only through `HWP::Keys::AddKeys/SetKeys`. Vanilla `AddKeys` stores a
  temporary in the dictionary, which the engine keeps by reference, so its
  counts turn to garbage (docs/RE_NOTES.md). A chest takes a party key first,
  then the opener's own; it puts the count back after `Chest::Use` spends the
  key, and level start resets counts outside 0-999.
- **Key budget per floor.** A floor drops fewer keys than its locked chests
  need: per tier, `keys.budget_share` (0.5) of its locked chests, plus
  `keys.budget_per_player` (0.1) per extra player (at most 0.95), the
  fraction rounded by a hash roll, minus the party keys of that tier held when
  the floor started. The killer's machine (`PlayerKilledActor` is local-only)
  sends every elite kill and `keys.normal_try` (4 %) of normal kills as
  candidates (`keys.drop`, flood-guarded at 10 per peer per 10 s); the host
  drops a key for `keys.accept` (40 %) of them while the budget lasts, elites
  taking the highest tier left. The first boss-tagged kill on a level has a
  20 % (`keys.boss_chance`) key drop outside the budget; its tier follows the
  floor's diff-level (up to 7 bronze, up to 13 silver, then gold), and from
  the mission's second-to-last boss on it is an ace key (Bone Serpent and
  Avatar in the Dark Citadel). `hwp keys` shows the pool, the floor's locked
  chests and the budget left per tier.
- **Imp offer.** `HWPImpKeyEffect` adds "a key" to the vanilla imp's random
  offers (`ImpEffect`), the tier scaled by the floor the same way.
- **General Merchant.** The exit guard by the run start (our copy of
  `actors/npcs/town/npc_misc_guard_exit.unit`, a declared override) opens the
  shop first (`HWPGeneralMerchant`, `HWPMerchantWindow`: the stock
  `ShopWindow` on `gui/hwp_merchant.gui`, with a Keys & Bags / Trinkets tab
  row); when it closes,
  NPCBehavior moves on to his vanilla speech bubble. Each key lists the loot
  quality of its chests. Prices `keys.price_<tier>` (500 / 2000 / 8000 /
  50000); only one ace key can be held at a time.
  He also sells **bag slots** (core `HWP::Bag`): one more equipment bag slot
  per purchase for the buyer's character, 1000 g rising to 20000 g, up to a
  full extra row (32 slots).
- **Trinkets tab.** Six trinkets per character (2 common, 2 uncommon, 2 rare;
  `Item::GetRandomTrinket`, no repeats; the roll puts back the `m_seen` flags it
  sets) at a run trinket shop's price
  (`GetPrice()` x 1.2, the ShopLevel 1 the dungeon shop rooms use: 240 /
  900 / 3600 g at base prices). A bought trinket is *packed*: the run's setup
  (`ResetForNewMission`) empties the trinket bag, so packed trinkets are
  handed over when the next run's first level starts: straight into the trinket
  bag, locally like every vanilla trinket shop. They don't go through `GiveItem`,
  which would count them in the trinket-found statistics. The stock rerolls after every run; the
  footer shows how many are packed. Stock and packed list are the buyer's own
  HWP save data (`keys.trinket_stock`, `keys.trinket_packed`,
  `keys.trinket_stale`).
- **Legendaries.** `tweak/hwp/legendaries.sval` ports the seven HoH1 red items
  with HoH2 modifiers (meteor on hit, gold-scaled damage, slowing gaze,
  nova on attack, invulnerability on hurt, kill-same-type, chaos bolts),
  quality `Legendary`, drop-rate 0 so they only come from ace chests.
- All `keys.*` settings are host-authoritative: clients read the host's
  values (core `settings.sync`), so every machine rolls the same locks.
- HUD: left of the bottom bar, one key icon per tier you can use (party pool
  plus your own) with its count, while you can use any.
- Commands: `hwp keys` (counts + settings), `hwp keygive <tier> [n]` and
  `hwp keydrop <tier>` when `keys.debug` is on.

Open decisions: the budget share (`keys.budget_share`), legendary balance and slots,
whether resource caches should want keys too.

## Test checklist

1. `python -m gamelab run mod-keys --mode lab`: no script errors, `Making Module hwp-keys`, lang check OK.
2. Town: talking to the exit guard by the run start opens the key shop: four
   keys, each subtitled with its loot quality; buying a bronze key deducts
   gold, logs the pickup and a bronze key icon appears left of the bottom bar. Closing the shop
   shows his speech bubble.
   The fifth entry, Bag Slot, shows your bag size; buying it adds an empty
   slot (the fourth inventory row fills) and the price rises; at 32 slots it
   is greyed out. `hwp bag` shows the same.
   `python -m gamelab run mod-merchant-trinkets --mode lab` covers the tabs:
   Trinkets lists 6 (2/2/2), two bought are packed (not in the run bag in
   town), both are in the run bag on the first floor, and after the run the
   stock rerolls to 6.
3. `hwp set keys.debug 1`, `hwp keygive gold 2`, `hwp keygive ace`: HUD
   updates; `hwp keydrop silver` drops a pickup that, walked over in a run,
   adds a silver key to the party pool (host and client see it).
   `python -m gamelab run mod-keys-pool --mode lab` covers the pool, the
   budget report and a chest opened with a party key.
4. Run: every reward chest has a padlock; without the key the use icon is a
   cross, the tooltip names the key and the chest does not open; with the key
   the padlock vanishes, the key count drops, the chest's own loot spawns.
   Cursed chests and caches open without a key.
5. `hwp set keys.ace_chance 1`: gold chests are red; opening with an ace key
   gives everyone a legendary or an epic; the legendary tooltip is red.
6. Kill elites: keys drop until the floor's budget (`hwp keys`) is spent. `hwp set keys.boss_chance 1`, kill a
   boss: one key of the floor's tier (ace on the Bone Serpent / Avatar).
   Talk to imps until one hands over a key of the floor's tier.
7. Co-op: the client sees the same chests locked as the host; client kills
   drop keys the host spawned into the shared pool; either player can open a
   chest with a party key, and the client with their own bought key.
8. Disable the module: vanilla saves still load, keys remain in the record.
