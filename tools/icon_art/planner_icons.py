"""Builds the class planner's icon sheet: every skill and orb icon the planner shows, cut
from the game's icon atlases (vanilla and Firearms), packed 24x24 into icons.png, with
icons.json mapping each in-game id to its cell.
python planner_icons.py <dump> -> out/planner_pub/icons.png, icons.json; <dump> holds the
planner's data as planner/classes/*.json, planner/skills/*.json and planner/mods/*.json.
Needs gamecode/ (python -m gamelab doctor) for the vanilla atlases."""
import json, re, sys, glob
from pathlib import Path
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
S = Path(sys.argv[1])
ROOTS = [(REPO / "gamecode/sdk/hoh2", REPO / "gamecode/sdk/hoh2/players"),
         (REPO / "mods/firearms", REPO / "mods/firearms/players")]
ID = re.compile(r'<string name="id">([^<]+)</string>')
ICON = re.compile(r'<array name="icon">\s*<(?:string|s)>([^<]+)</(?:string|s)>\s*<(?:int|i)>\d+</(?:int|i)>\s*<vec4>([^<]+)</vec4>', re.S)

icons = {}   # id -> (texture file, rect)
for base, root in ROOTS:
    for f in root.rglob("*.sval"):
        s = f.read_text(encoding="utf-8", errors="replace")
        ev = sorted([(m.start(), "icon", m) for m in ICON.finditer(s)] + [(m.start(), "id", m) for m in ID.finditer(s)], key=lambda e: e[0])
        last = None
        for _, kind, m in ev:
            if kind == "icon":
                last = (base / m.group(1), tuple(int(float(x)) for x in m.group(2).split()))
            else:
                if last and m.group(1) not in icons:
                    icons[m.group(1)] = last
                last = None

# the ids the planner shows
want = set()
for f in glob.glob(str(S / "planner/classes/*.json")):
    c = json.load(open(f, encoding="utf-8")); c = c.get("data", c)
    for sk in c.get("base", []) + [x for sp in c.get("specs", []) for x in sp.get("skills", [])]:
        want.add(sk["id"]); want.update(m["id"] for m in sk.get("mods", []))
for coll in ("skills", "mods"):
    for f in glob.glob(str(S / f"planner/{coll}/*.json")):
        d = json.load(open(f, encoding="utf-8")); d = d.get("data", d)
        if (d.get("built") or "").startswith("hwp_"):
            want.add(d["built"])

found = {i: icons[i] for i in want if i in icons}
missing = sorted(want - set(found))
cells, index = [], {}
for i in sorted(found):
    key = (str(found[i][0]), found[i][1])
    if key not in index:
        index[key] = len(cells); cells.append(key)
COLS = 16
rows = (len(cells) + COLS - 1) // COLS
sheet = Image.new("RGBA", (COLS * 24, rows * 24), (0, 0, 0, 0))
tex = {}
sizes = set()
for n, (path, (x, y, w, h)) in enumerate(cells):
    im = tex.setdefault(path, Image.open(path).convert("RGBA"))
    cut = im.crop((x, y, x + w, y + h)); sizes.add((w, h))
    if (w, h) != (24, 24):
        cut = cut.resize((24, 24), Image.NEAREST)
    sheet.paste(cut, ((n % COLS) * 24, (n // COLS) * 24))
out = Path(__file__).resolve().parent / "out" / "planner_pub"
out.mkdir(parents=True, exist_ok=True)
sheet.save(out / "icons.png", optimize=True)
json.dump({"cell": 24, "cols": COLS, "icons": {i: index[(str(p), r)] for i, (p, r) in found.items()}},
          open(out / "icons.json", "w"), separators=(",", ":"))
print(len(want), "wanted,", len(found), "found,", len(cells), "cells,", sheet.size, "sizes", sizes)
print("missing:", missing)
