# stash

A **Sort** button on the town stash, next to the tab picker.

- Sorts the open tab by class (the item's largest requirement: str, dex, int,
  foc, vit; items with none last), then by type: two-handed, main-hand and
  off-hand weapons (each grouped by family: maces with maces, wands with
  wands), then head, chest, hands, feet, back. Within a type the highest item
  level comes first, then the better quality, then the name.
- The sort is stable and only saves when the order changed; a second press
  logs `(already in order)`.
- The stash is your own town record, so the button sorts your stash on your
  machine only; nothing is sent to the lobby.
- Overrides `gui/player_stash/player_stash.gui` (the tab row is 50 px
  narrower to make room); the button is the widget `hwp-stash-sort`
  (`HWPStashSortButton`, a `ScalableSpriteButtonWidget` that sorts on click:
  the stash window's own `OnFunc` would treat an unknown func as Refresh).

## Test checklist

1. `python -m gamelab run mod-stash --mode lab`: 8 mixed items in tab 0, the
   Sort button orders them class > slot > family > ilvl and logs
   `[HWP:stash] sorted 8 item(s)`; a second press logs `(already in order)`.
2. Solo: put a few weapons and armour of different classes in a tab, press
   Sort: the order follows the rule above and survives leaving and reopening
   the stash (it is saved).
3. Several tabs: Sort only reorders the tab on screen.
