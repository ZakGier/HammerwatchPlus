# valuables

Valuables are worth twice their vanilla gold.

- **What counts.** Every `Item::Valuable` (`tweak/items/items_valuables.sval`,
  26 of them): the world pickups that turn straight into gold, from the scarab
  scale (30) and wolf fur (75) through the ceramic vase (150) to the diamond
  (800). Gold coins, materials and inventory items are untouched.
- **How.** The vanilla pickup pays `GetPrice()` gold (`PlayerRecord.as`, the
  `Item::Valuable` branch), so the module sets each valuable's `m_price` to its
  vanilla price times `valuables.gold_mult` (default 2) and rebuilds its pickup
  text. The vanilla price is kept, so changing the setting never compounds.
  Every machine applies it (each picker's own record pays out); the setting is
  host-synced at level start.
- `hwp valuables` shows the multiplier and the ceramic vase's old and new
  price; `hwp valuables drop [id]` drops a valuable at the host's feet (test
  aid, in a run).
- Settings: `valuables.gold_mult` (0-20).

## Test checklist

1. `python -m gamelab run mod-valuables --mode lab`: `[HWP:valuables]
   self-check done: 26 valuables at 2x`; a dropped ceramic vase is worth 300
   and picking it up adds 300 gold; `valuables.gold_mult 1` puts it back to
   150 and 2 to 300 again.
2. In a run, smash pots and pick up valuables: the pickup line shows the
   doubled amount and the gold counter rises by it.
3. Co-op: the client's pickups pay double too.
