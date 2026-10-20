# Firearms Specialist: design

The live design is the class planner, a local web app in the repo whose records are read
back before each build step: double-click `planner.cmd` or run `python -m planner`
(`planner/README.md`); the records are `planner/data/<collection>/<id>.json`.
Its tabs are the class tree, orbs, grenade, arsenal, clip and reload, attributes and budget.
It also holds a 4th specialization slot for every other class (a placeholder until designed). Each class's base
kit, three specs and every vanilla orb are prepopulated from the game data, and an
"All classes" view tracks progress.
This file holds the settled decisions and where each one is built.

## Settled
- **Ammo is a clip, mana pays for gadgets.** The clip is a stack that starts full and
  counts down per shot (Warlock essence in reverse). At 0 an automatic reload starts. It
  takes 1.6 s, and a dodge restarts it. The Reload skill refills at once.
  Built: `mods/firearms/players/hwp/firearms/stacks_firearms.sval`, `skills/fs_reload.sval`.
- **Magazines:** rifle 30, pistol 10, dual pistols 20 (10 each, one shared clip).
  Built: marker buffs in `buffs_firearms.sval`, one per gun.
- **Rifle:** two-handed, slow and heavy, pierces. Its secondary is a grenade launcher
  that costs mana and no rounds.
- **Pistol:** one-handed, made as two items (main hand, off hand), since an item has
  exactly one slot.
  - Paired with a non-pistol off hand: accurate.
  - Dual: left click alternates hands with a blooming spread and slightly lower DPS.
    Right click fires both at once with a wide spread.
- **Rocket launcher:** a doctrine active (a bonus weapon like Snipe), not an item.
- **Class shape (vanilla):**
  - Base: 2 actives and 2 passives.
  - **4 doctrines**, each adding 1 active and 1 passive. One doctrine places **turrets**
    in the world (a stationary summon).
  - About 24 orb mods (about 60 mod levels).
- **Grenade:** the base Frag Grenade. Mutually exclusive orbs turn it into a Stun,
  Incendiary or Gas grenade (`blocked-by-skills`, like Paladin's fire xor lightning).
  Built: `skills/fs_frag.sval`, `projectiles/grenade.inc` (one unit per type).

## Built (2026-10-19, from the planner's records)
- **Base kit:** Reload with Dodge Reload Skip, Explosive Reload (dual magazines thrown in
  turn) and Over-Reload (automatic and manual reloads; the bonus never stacks); the Frag
  Grenade with its three type orbs. The two base passives are the owner's to design; the
  old Scavenger and Steady Hands stay in place until then.
- **Marksman:** Snipe and Critical Aim (Focus stacks), with Headshot, Piercing Bullet,
  BOOM Headshot! and Elemental Exposure.
- **Demolitionist:** the Rocket Launcher and Ordinance Hoarder (charges), with Fat Boy,
  Magic Missile, Quad Missile Chambers, Elemental Shrapnel and Overpacked.
- **Assault:** Double Barrel Burst and Adrenaline, with their orbs (Triple Barrel, Dragon's
  Breath, ...). **Engineer:** Deploy Turret and My Turret!, with Second Turret, Reinforced
  Turret and Belt Feed (`plan-firearms-b`, `mods/firearms/README.md`).
- Scripted parts: `mods/firearms/scripts/HWP/Firearms/Combat.as`. Checks:
  `plan-firearms-a`, `-b` and `-orbs` (all PASS 2026-10-19).
- Interpretations made where the planner was open: see the session report in
  `docs/RE_NOTES.md` ("Firearms specializations").

## Not built yet (refine in the planner first)
- The two base passives.
- Firearm trinkets.
- A 4th spec for every other class: placeholders in the class planner, being designed.

## Engine facts this design relies on (verified on the pinned build)
- **Item modifiers can't change a stack.** `PlayerRecord.RefreshModifiers` runs
  `ModifyStacks` (PlayerRecord.as:1886) before it adds equipment modifiers. Buff modifiers
  are added earlier, so they can. Hence the marker buffs.
- **Lose-effects at 0 stacks run at intensity 0, and `AddStacks` skips intensity ≤ 0**
  (AddStacks.as:59). The lists open with an `intensity-set 1 1` dict to get around this.
- **`conditionals` is an OR of groups; one `conditional` array is an AND**
  (Conditional.as CheckConditionals).
- **Textures must be power-of-two.** A 216x24 atlas logs `Texture sizes (216x24) should be
  power of two` and the game hangs after script compile (GameLab run 20261019-010915).
- **A projectile thrown along a direction lands 100 out** (`IProjectile.as` GetTargetPos,
  which GroundBouncing `hit-target` flies to).
- **A dash `TriggerEffect` on the Reloading buff restarts its timer.** Measured: 1.75 s
  reload without a dodge vs 2.92 s with a dodge at 0.9 s (GameLab plan-t14).
- **Purple orbs are skill spheres** (`Behaviors/SkillSphere.as`, `GUI/Menus/GiveSkillSphereMenu.as`).
  A sphere offers 3 picks from the orb mods (`modifier-skills`) of skills the player has
  learned, each at its next level, weighted by `GetSkillDropRateChance`. Two picks never
  share a parent skill, and `blocker`/`req` skills filter the pool. A reroll costs Shadow
  Curse (`min(100, ScaleShadowCurse(12 + 7 × rerolls used))`) up to the town's reroll charges.
  So a new orb only shows up once its parent skill is learned. Vanilla orb ladders are
  Uncommon/Rare (none Epic); the commonest is Uncommon, Uncommon, Rare (59 of 196).
- **Unused vanilla skills in the game data:** Zealous Charge and Zealous Onslaught
  (paladin), Grappling Hook (rogue), Flame Step (sorcerer), Charge (warrior), Phantasmal
  Force (wizard), and the shared Heavy Ballista, Battle Banner and First Aid. No class lists
  them; whether they work is untested. Heavy Ballista is a candidate base for the turret doctrine.
