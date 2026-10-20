"""A vanilla class's orb icon ideas (vo_<cls>.py) as files and comparison sheets, with the
icon the orb shows now (from planner_icons.py's sheet) beside each.
python rorb.py <cls> [orb ids] -> out/orbs/<cls>/<id>_<a|b|c|now>.png, out/osheet_<cls>_<i>.png"""
import sys, json, importlib
from pathlib import Path
from PIL import Image
from vpaint import sheet
HERE = Path(__file__).resolve().parent
PUB = HERE.parents[1] / "planner" / "web"
cls = sys.argv[1]
mod = importlib.import_module("vo_" + cls)
names = sys.argv[2:] or list(mod.ORBS)
out = HERE / "out" / "orbs" / cls
out.mkdir(parents=True, exist_ok=True)
idx = json.load(open(PUB / "icons.json"))
atlas = Image.open(PUB / "icons.png").convert("RGBA")
def now(i):
    k = idx["icons"].get(i)
    if k is None: return None
    c, n = idx["cell"], idx["cols"]
    return atlas.crop(((k % n) * c, (k // n) * c, (k % n) * c + c, (k // n) * c + c))
rows = []
for n in names:
    ims = [ic.done() for ic in mod.ORBS[n]()]
    for k, im in zip("abc", ims):
        im.save(out / f"{n}_{k}.png")
    cur = now(n)
    if cur: cur.save(out / f"{n}_now.png")
    rows.append((n[-20:], ims + ([cur] if cur else [])))
for i in range(0, len(rows), 13):
    sheet(rows[i:i + 13], str(HERE / "out" / f"osheet_{cls}_{i // 13}.png"), z=4)
print(len(rows), "rows")
