"""The picker's vanilla orb groups: for each class with a vo_<cls>.py, out/orbs/<cls>.json
naming every orb it draws (name, parent skill, description, the images rorb.py wrote).
python orb_groups.py <dump>; <dump> as for planner_icons.py (planner/classes/*.json)."""
import importlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
CLASSES = ["paladin", "priest", "ranger", "rogue", "sorcerer", "warlock", "warrior", "wizard"]


def main(dump):
    out = HERE / "out" / "orbs"
    for cls in CLASSES:
        d = json.load(open(Path(dump) / "planner/classes" / f"{cls}.json", encoding="utf-8"))
        d = d.get("data", d)
        info = {}
        for g in [d["base"]] + [s.get("skills", []) for s in d.get("specs", [])]:
            for sk in g:
                for m in sk.get("mods", []):
                    info[m["id"]] = (m.get("name", m["id"]), m["desc"], sk.get("name", sk["id"]))
        mod = importlib.import_module("vo_" + cls)
        items, miss = [], []
        for oid in mod.ORBS:
            if oid not in info:
                miss.append(oid)
                continue
            nm, desc, parent = info[oid]
            imgs = {k: f"{cls}/{oid}_{k}.png" for k in "abc"}
            if (out / cls / f"{oid}_now.png").exists():
                imgs["now"] = f"{cls}/{oid}_now.png"
            items.append({"id": f"{cls}.{oid}", "name": f"{nm} ({parent})", "key": oid, "desc": desc, "imgs": imgs})
        out.mkdir(parents=True, exist_ok=True)
        json.dump({"id": cls, "title": d.get("name", cls.title()) + " orbs", "items": items},
                  open(out / f"{cls}.json", "w", encoding="utf-8"))
        print(cls, len(items), "orbs; not in the planner:", miss, "; not drawn:", sorted(set(info) - set(mod.ORBS)))


if __name__ == "__main__":
    main(sys.argv[1])
