# mercenary

Heroes of Hammerwatch 1's mercenary mode: a hero whose death is permanent, in
return for prestige ranks that pay more gold and experience.

- **Enlisting.** In town, on a fresh level-1 character: `hwp merc enlist`, then
  `hwp merc enlist confirm`. As in HoH1, the class needs a veteran first: another
  character of the same class at `mercenary.unlock_level` (default 20, HoH1's
  unlock and HoH2's level cap). The character is levelled to
  `mercenary.start_level` (default 10). HoH1 started mercenaries at 20, but HoH2
  caps at 20, so that would skip all the levelling.
- **Prestige** uses HoH1's formula (`PlayerRecord.GetPrestige`, hardcore build):
  - 1 per mission floor entered (once per floor; a resumed floor does not count again);
  - 10 per boss floor cleared: a mission's `levels/boss_*` level, or a module with a boss
    (the heaven trials). One per floor; any party member's kill counts, through the
    host. Boss-tagged actors elsewhere, such as the keep's bandit boss encounter, don't count;
  - 75 × (new game+ earned as a mercenary)².
- **Ranks** are HoH1's `tweak/titles/mercenary.sval`: Private 0, Corporal 50,
  Sergeant 200, Lieutenant 500, Captain 1000, Major 2500, Colonel 5000,
  General 10000.
  - Each rank, Private included, adds +15% gold and +15% experience. HoH1's
    `inc-modifiers` with `extra-inc-modifiers 1` gave the same.
  - The bonus is a `Modifiers::MaterialGain` (gold-mul) plus a
    `Modifiers::Experience` added in the `PlayerRecordRefreshModifiers` hook. It
    shows in the stat breakdowns as "Mercenary rank".
- **Death.** A mercenary falls when it dies on a mission floor. With
  `mercenary.revivable` on (host setting, default off), it falls only when the run
  fails or is abandoned while it is down, so a co-op revive saves it. The run's end
  state is read in the `PlayerRecordLoad` hook, because the town's `MissionEndMenu`
  clears it before `Start`. Once fallen:
  - the fall is announced to the party;
  - the character goes into this town's ledger of the fallen (`hwp merc ledger`);
  - in town the character picker opens whenever no other menu is up, so it can
    no longer be played. Its save is kept, and the picker can delete it;
  - its mission setup closes as it opens, so it cannot start a run;
  - on a floor it stays dead: a party revive, or entering a floor alive, kills it again.
- `hwp merc` shows the rank, prestige, next rank, floors, bosses and the gold and
  experience multipliers as the game currently computes them.
- Cheats (`e_cheats 1`):
  - `hwp merc enlist force [confirm]` skips the veteran check;
  - `hwp merc prestige <n>` adds n floors;
  - `hwp merc fall` and `hwp merc revive` set and clear the fallen state.

Not ported from HoH1:
- **The 25,000 starting gold.** HoH2 keeps gold in the town's shared store, so it
  would go to every character.
- **Life insurance and the Master at Arms trainer.**
- **Mercenary-only lobbies.** Mercenaries and regular heroes can play together.
- **The HUD "MERCENARY" indicator.** It is replaced by a chat reminder on a
  mission's first floor.
- **Legacy points on death.** HoH2 has none.

A fallen mercenary that is in a mission when it falls (co-op, before the run
ends) stays in that mission, dead, until the party leaves; the picker takes over in
town. Shops stay open to it, which is harmless: gold is the town's.
Closing the game in the moment of death can dodge a fall: the game only saves at
level changes.

Settings (`hwp set`, host-synced): `mercenary.start_level`,
`mercenary.unlock_level`, `mercenary.revivable`.

Test: `gamelab/scenarios/mod-mercenary.json` covers:
- enlisting: locked without a veteran, then forced, confirmed and levelled to 10;
- ranks at 49 and 50 prestige, with the x1.15 and x1.30 multipliers;
- the data reaching the floor, and the floor counting;
- a death on the floor being a fall, and the fall being announced;
- the picker being forced open back in town, and the ledger entry.

The boss-kill path is not covered.
