"""The Firearms icon ideas as files and comparison sheets.
python render.py <group> [names...] -> out/firearms/<name>_<a|b|c>.png, out/sheet_<group>_<i>.png;
groups: fa1 (fa.py) fa2 fa3 all"""
import sys
import fa, fa2, fa3
from vpaint import sheet
GROUPS = {"fa1": fa.FA, "fa2": fa2.FA2, "fa3": fa3.FA3}
GROUPS["all"] = {**fa.FA, **fa2.FA2, **fa3.FA3}
g = sys.argv[1]
names = sys.argv[2:] or list(GROUPS[g])
rows = []
for n in names:
    ims = [ic.done() for ic in GROUPS[g][n]()]
    for k, im in zip("abc", ims):
        im.save(fa.OUT / f"{n}_{k}.png")
    cur = fa.current(n)
    rows.append((n, ims + ([cur] if cur else [])))
for i in range(0, len(rows), 14):
    sheet(rows[i:i + 14], str(fa.OUT.parent / f"sheet_{g}_{i // 14}.png"), z=5)
print(len(rows), "rows")
