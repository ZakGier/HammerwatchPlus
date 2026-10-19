# firearms

A new class, the **Firearms Specialist**. Pure data (`PlayerClass`,
`ItemSkillDef`, `BaseItem`, `PlayerPortraitPiece`, `HeroTitle` loaders) plus a
tiny module that self-checks the loaders and answers `hwp firearms`.

- **The clip** (`players/hwp/firearms/stacks_firearms.sval`): a stack counted
  down from full, Warlock essence in reverse. Its `max` is 0; each gun adds its
  magazine through a marker buff (`buffs_firearms.sval`, re-applied every
  250 ms by the item's `Modifiers::Buff`) that carries `ModifyStack add-max`.
  An item can't carry the `ModifyStack` itself: `PlayerRecord.RefreshModifiers`
  applies stack modifiers before it adds equipment. The module fills the clip
  on spawn. Gun shots take rounds and no mana.
  At 0 rounds the **Reloading** stack starts (1.6 s timer; a dodge restarts it)
  and refills the clip when it ends. **Reload** (starting skill, 0.55 s cast,
  cooldown 2.0 s down to 1.2 s) refills at once and cancels the auto-reload.
  Mana pays for gadgets: the grenade launcher, grenades, rockets, bursts.
- **Rifles** `hwp_rifle_01/02/03` (`tweak/hwp/equipment_firearms.sval`):
  two-handed, 30 rounds, slow heavy piercing shot (560 ms, 160 %; epic 200 %).
  The secondary is an under-barrel grenade launcher: 4 mana, 1.5 s cooldown,
  no rounds. Dex-gated, crossbow anim set, tag `hwp_firearm`. The t1
  rifle is the starting weapon and sits in the armory pool.
- **Pistols:** `hwp_glock_mh_01/02/03` (main hand, wand anim set) and
  `hwp_glock_oh_01/02/03` (off hand, hand-crossbow anim), 10 rounds each.
  Each grants a marker buff the other pistol's attack checks for.
  - A main-hand pistol with any other off hand fires one accurate round twice
    a left-click cycle.
  - Dual pistols share a 20-round clip. Left click alternates muzzles with a
    blooming spread; right click fires both at once with a wide spread (2
    rounds, not on 1).
  - An off-hand pistol with another main-hand weapon fires one round on right
    click.
- **Base kit:** Reload and the Frag Grenade (targeted lob, `GroundBouncing` +
  `Explode` on landing, armor penetration). The two base passives are still to
  be designed; Scavenger and Steady Hands hold their places for now.
  - Reload orbs: **Dodge Reload Skip** (a dodge during the automatic reload
    finishes it), **Explosive Reload** (the old magazine is thrown 100 out and
    blows up for 5/8/12 per round left; dual pistols throw one magazine,
    then the other 100 ms later),
    **Over-Reload** (a gold mark on the reload ring. During the automatic
    reload, Reload inside it; during a manual Reload, press Reload again
    inside it. A perfect reload finishes at once and gives +6/9/12 rounds,
    never stacking, until the clip runs dry or a reload isn't perfect).
  - Frag orbs, mutually exclusive: **Stun Grenade** (lightning, stun and slow
    1/2/3 s), **Incendiary** (a burning, blinding fire patch), **Gas** (a
    poison cloud that fire ignites).
- **Marksman:** **Snipe** (both hands' damage, 200-600 %, armor penetration,
  10 rounds and 30-50 mana) and **Critical Aim** (passive: a gun round that
  hits gives Focus, crit chance and damage per stack; one that hits nothing
  loses it all). Orbs: Headshot (the first enemy a Snipe hits is crit),
  Piercing Bullet (2/4/6 more enemies), BOOM Headshot! and Elemental Exposure.
- **Demolitionist:** the **Rocket Launcher** (fire blast, mana, no rounds) and
  **Ordinance Hoarder** (passive: Frag and the rocket recharge faster and bank
  charges while ready; a charge clears the cooldown after a cast). Orbs: Fat
  Boy (slow heavy rocket, poison, blind), Magic Missile (ice then fire), Quad
  Missile Chambers (4 small missiles), Elemental Shrapnel, Overpacked.
- **Assault:** Burst Fire (3-5 round fan), Stun Grenade (1.5 s stun),
  Adrenaline (damage taken down, kills refill ammo). Unchanged.
- The orb scripts (Focus, Headshot, Exposure, Hoarder charges, Over-Reload's
  ring, the magazine throw) are in `scripts/HWP/Firearms/Combat.as`.
- **Art:** portrait piece and hero title reuse the ranger assets.
  - Held guns: voxel meshes in `players/models/equipment/` (`hwp_rifle`, with
    the under-barrel launcher; `hwp_glock_mh` on the right hand bone,
    `hwp_glock_oh` on the left). They sample vanilla `character.tif`: the
    item's `color` dye is the rifle's wood and the pistol's slide, and
    `color-secondary` is the rifle's metal.
  - Rounds and missiles in flight: `tools/make_bullet_art.py` draws
    `projectiles/rounds.png` and writes one effect per sprite. The rifle/turret
    round is `round_rifle`; the pistol round is the same idea a little smaller,
    `round_pistol`. Each comes in `_fire`, `_ice`, `_lightning` and `_poison`
    variants for Elemental Bullets, which has no units yet. The rest are
    `gl_shell` (the launcher's 40 mm shell) and `missile_rocket`, `_fatboy`,
    `_magic` and `_quad`. Edit the tool, not its output.
  - Ground sprites: `items/hwp/firearms_drops.unit`, one scene per gun and tier
    (`rifle_0N`, `glock_0N`), in `items/hwp/firearms_drops.png`.
  - Icons are built by `tools/make_firearms_icons.py` into
    `players/hwp/firearms/icons.png` (skills, orbs, attacks) and
    `items/hwp/firearms_items.png`. The items atlas has the guns in row 0 and
    the launcher close-ups `rifle_gl_0N`, meant for the off-hand slot, in
    row 1. Hand-drawn art in `art/firearms/override/` wins over the
    `art/firearms/sprites.txt` placeholders; a preview of both sheets goes in
    `art/firearms/preview.png`. To hand-draw one, save a 24x24 PNG
  as `art/firearms/override/<name>.png` (Aseprite, LibreSprite or Pixelorama)
  and re-run the tool. Atlases must be power-of-two sized: the game hangs on
  load otherwise.

Next, from the planner
(https://claude.ai/artifact/GUXggQqycAoQRiJ6G1Nwv3): the two base passives,
the 4th (turret) doctrine and the remaining orbs. See `docs/design/firearms.md`.

## Test checklist

1. `python -m gamelab run mod-firearms --mode lab`: `[HWP:firearms] class registered with 3 subclass(es)`, no
   "missing item/unit" lines, no script or sval errors.
2. Create a character: Firearms Specialist is in the class list with the
   round icon; the character spawns with the Flintlock Rifle equipped.
3. Clip: `python -m gamelab run plan-t14 --mode lab`. Covers the 30-round
   spawn fill, 1 round and no mana per shot, the launcher's mana cost, the empty
   clip (Reloading, won't fire, refills), the dodge restart and Reload.
4. Guns: `python -m gamelab run plan-firearms-guns --mode lab`. Covers
   magazines 10/20/30 and the rounds each loadout's clicks take.
5. Frag grenade lands where aimed and explodes; damage numbers appear.
6. Specializations and orbs: `plan-firearms-a` (Frag, the picker, Marksman),
   `plan-firearms-b` (Demolitionist, Assault) and `plan-firearms-orbs` (the
   Reload and Frag orbs). Orbs are taken with `gl orb <id>` (the sphere's
   SkillTempUp).
7. Over-Reload by hand: empty the clip, watch the ring, press Reload on the
   gold mark; the clip shows +6. Then Reload with rounds left and press
   Reload again on the mark: still +6, not +12.
8. Ordinance Hoarder by hand: wait 8 s with the rocket ready, fire twice in a
   row.
9. Co-op: a client sees the host's bullets, grenades and rockets, and the
   other way round.
