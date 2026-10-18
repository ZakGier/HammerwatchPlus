# colors

Accessibility colours for projectiles.

- `module.json` **class_swaps** `NewProjectile`, `RayProjectile` and
  `BeamProjectile` to `HWP*` subclasses that call
  `HWP::Colors::Tint(m_unit, owner)` after the base `Initialize`
  (`tools/class_units.py` copies the 184 base projectile units with our class
  in; info.xml classmaps are ignored by the engine, which is why the tints
  never applied before). Projectiles that other HWP mods add (HoH1 bosses,
  firearms) keep their own class and are not tinted. Friendly = the owner
  resolves through `GetPlayerOwner` (players, summons, turrets); everything
  else is enemy. The tint is `UnitPtr.SetMultiplyColor`, so it multiplies the
  sprite: dark sprites get darker, white/pale ones take the colour best. The
  first tinted shot of a level is logged (`[HWP:colors] tinted <unit> enemy #...`).
- Presets: `default` (no tint), `contrast` (red vs light blue),
  `deuteranopia` (orange vs blue), `protanopia` (yellow vs blue),
  `tritanopia` (red vs teal). Per-team overrides as hex.
- The preset is picked in the player menu's **Plus** tab (core
  `HWP::Options`, row `colors`): click the button for the next preset (it
  clears custom colours). The game's own Options menu cannot take it: it runs
  in the menu script, without mod scripts or gui files (GameLab
  `probe-options-menu`). Stored as the HWP setting `colors.preset`.
- Custom per-team colours (per machine, in your own town record):
  `colors.enemy`, `colors.friendly`. Commands:
  `hwp colors` (show), `hwp colors deuteranopia`,
  `hwp colors enemy ff8800`, `hwp colors friendly 44aaff`, `hwp colors off`.

Open question: whether effects/AoE telegraphs should be tinted too (they
are `EffectBehavior` units, not projectiles).

## Test checklist

1. `python -m gamelab run mod-colors --mode lab`: a spawned guard sentry's
   crossbow bolt is tinted (`tinted actors/undead/guard/projectiles/crossbow_bolt.unit
   enemy #ff5959`), no script errors. `mod-options-tab`: the Plus tab row cycles presets.
2. `hwp colors contrast`, fire a ranged skill: your projectiles are blue-ish;
   ranged enemies' projectiles are red-ish. Beams (wizard) and ray projectiles
   also tint.
3. `hwp colors enemy 00ff00`: enemy shots go green; `hwp colors off` restores.
4. Player menu > Plus: "Projectile colors" shows the preset; clicking it
   steps through them, tints change right away, and `hwp colors` shows the new preset.
5. Leave and re-enter town: the choice persists (`[HWP:colors] preset ...` in the log).
6. Co-op: a client's choice only changes that client's screen.
