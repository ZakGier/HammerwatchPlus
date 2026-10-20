# farming

Farm plots in town. Crops grow while you run the dungeon, twice as fast when
watered.

- **Plots are the field grooves.** In a town with the farm segment, the
  vanilla onion, wheat, cabbage, potato (and carrot) crops are hidden and
  every groove they stood on becomes an empty plot until someone plants it:
  farm level 4 has 8 onion columns, 9 wheat rows, 8 cabbage and 8 potato
  columns (33 plots; up to 48). Onions and wheat come first so plots saved
  before the other fields keep their index. Only crops on a groove are hidden
  (not the tavern's small patch). Every machine reads the grooves from the
  same town prefab (`DetectFields`: crop units grouped by column / row, in a
  fixed order) and spawns its own sensor units along them
  (`doodads/hwp/farm_groove_v/h.unit`, one per 48 px, netsync none). A
  plot's index is the groove nearest to the player who interacts, so no unit
  ids go over the network. Without fields (farm level 0) the plots fall back
  to `farm.plots` (default 4) soil patches in a row from `farm.x/y`;
  `hwp farm here` (host) moves them to you and turns the fields off,
  `hwp farm fields` turns them back on.
- **Apple tree.** The apple tree below the wheat field is moved just above
  the field's top fence (local `SetPosition` on every machine).
- **Town rebuilds.** A building upgrade rebuilds the town: our plot, well and
  visual units go and fresh vanilla crops appear. Once a second the module
  checks for that (`FieldsStale`: a hidden crop, plot or visual unit gone, or
  a different vanilla crop count) and lays everything out again
  (`RebuildTown`), so the fields stay empty and the plots stay planted.
- **Interact.** On a plot: empty -> pick one of your seeds; growing -> water
  it (one charge of your watering can, once per run; bigger cans pour on
  neighbouring rows too); ready -> harvest. A
  growing plot with an empty can only shows a red "Watering can is empty"
  toast (no window). One that cannot be watered for another reason (already
  watered, no can) opens the plot window instead, with the reason. In the
  soil-patch layout the plot unit you touch decides the plot, not the nearest
  patch centre.
- **Farmer.** The vanilla farmer (`npc_misc_farmer_man.unit`, overridden;
  `.orig` kept) stands between the two fields instead of walking through them
  and runs a shop (rows are just the name and price). You start without a
  can and buy them in order, each replacing the last and coming full:

  | Can | Price | Water | Area (rows per pour) |
  |---|---|---|---|
  | Mahogany | 200 g | 4 | 1x1 (1) |
  | Tin | 1,500 g | 6 | 2x2 (2) |
  | Iron | 5,000 g | 8 | 3x3 (3) |
  | Gold | 15,000 g | 10 | 4x4 (4) |
  | Diamond | 50,000 g | 12 | 5x5 (5) |

  A plot is a whole groove, so the area is in grooves: one pour waters the
  target row and its nearest rows of the same field (`WaterArea`; the soil
  patch layout: the nearest patches), for one charge. The host waters what
  is planted, growing and still dry in that area, and refuses when nothing
  is. Seeds cost 15-250 g each. The farmer has a sprout icon on the minimap
  (`gui/hwp/map_farmer.png`).
- **Well.** A well (`doodads/hwp/farm_well.unit`, vanilla well sprites) just
  under the bottom left corner of the field beside the farmhouse (the cabbage
  field), south-east of the house: placed from the wheat field's corner, so it
  stands in the same spot at every farm level (`WellPos`). Without fields it
  goes next to the pet feeding bowl. `hwp farm well` moves it to you (saved as
  `farm.well_x/y`, which then wins; `hwp farm well reset` clears it). It refills the can.
- **Seeds and growth.** Food crops (cabbage, carrot, onion, potato, wheat)
  need 2 growth, Holy Herb strains (Lucky Leaf, Ember Kush, Saint's Sage) 4.
  (Gambler's Gold is gone: its seeds and herbs in an older save become Lucky
  Leaf when the character loads, `MigrateGone`.) A completed run (succeeded or failed: the host's mission state
  as the town loads its character, in the `PlayerRecordLoad` hook) adds 1 growth, 2
  if the plot was watered since the last run: food takes 2 runs (1 watered), herbs 4 (2 watered).
  Your seeds and what you harvested show in the materials tab's **Plants &
  Herbs** section (core `HWP::Materials`, 8 cells across): a cell per seed
  (`gui/hwp_seeds.png`, tooltip: growth time and yield) and a cell per
  harvested crop or herb (`gui/hwp_harvest.png`, `HWPHarvestMaterial`).
  The herb plants and buff icons are drawn as cannabis in each strain's colour.
  A harvest yields one per plant drawn on the plot (`CropSpots`: what you see
  is what you get) as wares (`HWP::Market`, sold at the Gambler or with
  `hwp sell`), plus a 25 % chance of a seed back (5 % of the time two).
- **Network.** The host owns the plot state (seed, growth, watered) in its
  own TownRecord (`farm.plots`, `farm.runs`, `farm.pending`) and broadcasts
  every change (`farm.sync`); clients pull it when they load (`farm.pull`).
  Plant / water / harvest are requests to the host (`farm.plant`,
  `farm.water`, `farm.harvest`); the host answers `farm.planted`,
  `farm.watered`, `farm.yield` and only then the requester uses the seed or
  the water, or `farm.refused` (plot taken, already watered, not ready),
  which costs nothing. One plant or water request is in flight at a time
  (until the answer, at most 3 s), so a seed or a charge cannot be spent
  twice before the host answers. Can tier, water and seeds are per character
  (`farm.can`, `farm.water`, `farm.seed.<id>` in the player's HWP data).
- **Gear grid.** The watering can shows in the character screen's 3x3 gear
  grid (bottom right, core `hwp-gear-can` slot) in its tier's colour
  (`doodads/hwp/farm.png`): empty without a can (new characters start without one); the tooltip shows its name,
  water and area.
- **Run counting.** A gameplay load outside town sets pending, the next town
  load counts the run. Saves from before watering ("at" = planted on run N)
  convert to growth on load.
- **Herbs and joints** (`Joint.as`). Click a harvested herb under Plants &
  Herbs: "Roll J?" -> "Huzzah!" rolls it into a joint (`hwp joint roll
  <herb>` does the same), an off-hand item in your bag
  (`tweak/hwp/equipment_joints.sval`, `hwp_joint_<strain>_<5..1>`: the puffs
  left, each stage with its own icon and model). Held, it smoulders (a thin
  wisp). Right click (its off-hand skill) is a puff: the tip glows cherry red,
  the smoker gets the strain's `hwp_herb` mission buff
  (`tweak/hwp/buffs_herbs.sval`) for 10 floors counting boss floors
  (`KEY_HERB_FLOORS`, counted down per level by `KeepHerb`; a puff in town
  gives the next 10), and the joint burns down a stage; the fifth puff uses it
  up. In a run room or a town building each puff leaves a haze that thins over
  a minute; puffs stack. A player with a free off hand next to you takes your
  joint with the interact key, no questions asked (host relays it,
  `farm.joint_*`). Lucky Leaf also makes the Gambler redraw a losing dealer
  card once (25 %). Harvesting a plot never smokes or rolls anything.
  `hwp joint` lists what you hold, rolled, puffed and the hazes.
- Visuals, local on every machine: a sprout right after planting, a bigger
  sprout once it grew, the vanilla crop sprite (or a herb sprite) when ready,
  repeated on every spot of the groove; dark wet soil under watered plots.
- **Wild plots in runs.** On `farm.run_chance` % of run floors (default 35;
  never a boss room) the host places one ripe plot (`doodads/hwp/wild/<seed>.unit`,
  made by `tools/make_wild_plots.py`) a little way from a random pot, crate or
  chest: 85 % a food crop, 15 % a Holy Herb. The unit is netsynced, but every
  player harvests it once for themselves (`HWPWildPlot`, local yield): one
  per plant drawn (3, `WILD_PLANTS`) and **twice** the farm's seed odds (50 %
  one seed back, 10 % two). Nothing can be planted on it; after your harvest it disappears
  for you. It has a crop icon on the minimap.
- `farm.*` settings are host-synced. `farm.debug` enables `hwp farm grow`
  (counts a run) and `hwp farm wild [seed]` (a wild plot beside you; `hwp
  farm wild pick` harvests the last one placed).

## Test checklist

1. `python -m gamelab run mod-farming --mode lab`: `[HWP:farming] self-check done: 8 seeds, 3 herb buffs`, no
   script issues.
2. Town: the onion, wheat, cabbage and potato crops are gone, the log says
   `fields: 8 onion grooves, 9 wheat grooves, 8 cabbage grooves, 8 potato
   grooves` and `spawned N plot units`; the
   apple tree stands above the wheat field's top fence and nothing collides
   where it used to be.
3. Farmer between the fields (sprout icon on the minimap): the rows read
   "Mahogany Watering Can (1x1) - 200 g" and "Cabbage - 20 g". Buy the can
   ("Mahogany Watering Can: 4/4 water") and a cabbage seed. Interact on an onion groove -> the window lists the seed;
   plant it -> sprouts along the whole groove.
4. Interact again -> watered (can 3/4, wet soil under the sprouts); again ->
   "Already watered". With a tin can or better, plant two neighbouring rows
   and water one: "Watered 2 rows", one charge. Upgrade any building: the
   log says `the town was rebuilt`, the fields are still empty and the
   plots keep their crops. `farm.debug 1`, `hwp farm grow` -> the crop is ready
   (2 growth); interact -> harvested as many cabbages as the groove shows, sometimes +1/+2 seeds.
5. Well just under the bottom left corner of the field beside the farmhouse
   refills the can; without a can it says so.
   `hwp farm well` moves it.
6. Real cycle: plant without watering, run a mission, return -> half grown
   (bigger sprout); run again -> ready.
7. Herbs: plant Lucky Leaf, grow, harvest; the herb shows under Plants &
   Herbs. Click it -> "Roll J?" -> "Huzzah!": a Lucky Leaf Joint (5/5) in the
   bag. Equip it in the off hand (a wisp of smoke), right click five times:
   the tip glows, 4/5 .. 1/5, then it is gone; the buff shows in the loadout
   screen for 10 floors. Inside a building the puffs leave a haze.
8. 2-player lobby: both see the same plots, sprouts and wet soil; the client
   plants, waters (its own can) and harvests (yield on the client); two
   players planting the same groove at once leaves one with the seed back.
9. Character screen: the can slot (bottom right of the gear grid) is empty
   before you buy a can; afterwards its tooltip shows the tier and water,
   and watering a crop lowers the count.
