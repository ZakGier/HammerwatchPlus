"""Reads the class damage bench results (gamelab/results/bench/<class>.json, written by
bench.py) and prints, for each checkpoint (level and run stage), every build's single-target
and pack damage per second and where the Firearms builds stand against the vanilla damage
classes: the ratio to the median of the vanilla specializations' numbers.

python -m gamelab.bots.bench_report [--md out.md]"""
import json
import statistics
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "gamelab" / "results" / "bench"
FIREARMS = "hwp_firearms"


def load():
    rows = []
    for f in sorted(OUT.glob("*.json")):
        rows += json.loads(f.read_text(encoding="utf-8"))
    return rows


def table(rows):
    lines = []
    keys = sorted({(r["level"], r["stage"]) for r in rows}, key=lambda k: (k[0], k[1] != "start"))
    for level, stage in keys:
        here = [r for r in rows if r["level"] == level and r["stage"] == stage]
        vanilla = [r for r in here if r["class"] != FIREARMS]
        if not vanilla:
            continue
        med_s = statistics.median(r["single"] for r in vanilla)
        med_p = statistics.median(r["pack"] for r in vanilla)
        top_s = max(r["single"] for r in vanilla)
        lines.append(f"\n## Level {level}, {stage} of run  (vanilla median: single {med_s:.0f}, pack {med_p:.0f};"
                     f" vanilla best single {top_s:.0f})")
        lines.append(f"| build | single | x median | pack | x median |")
        lines.append("|---|---:|---:|---:|---:|")
        for r in sorted(here, key=lambda r: -r["single"]):
            name = f"{r['spec']} ({r['build']})"
            if r["class"] == FIREARMS:
                name = f"**{name}**"
            lines.append(f"| {name} | {r['single']:.0f} | {r['single'] / med_s:.2f} | {r['pack']:.0f} | {r['pack'] / med_p:.2f} |")
    return "\n".join(lines)


def main(argv):
    text = table(load())
    print(text)
    if "--md" in argv:
        Path(argv[argv.index("--md") + 1]).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
