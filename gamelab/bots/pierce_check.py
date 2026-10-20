"""Pierce check: one trigger pull fired down a row of four target dummies (bench verb, no
skills). Neither gun pierces: the rifle's three-round burst and a Glock round all stop at the
first dummy (penetration 0 since 4b528ea; before it the rifle hit the second at 50% and the
third at 25%). Only Snipe's Piercing Bullet orb goes through enemies. Flags: rifle_no_pierce,
glock_no_pierce."""
import time

DUMMY = "doodads/generic/target_dummy_normal.unit"
CLIP = "players/hwp/firearms/stacks_firearms.sval:clip"
ROW = [22, 40, 58, 76]


def shot(g, tag, off=False):
    g.gl_cmd("kill", 600, "target_dummy")
    time.sleep(0.3)
    for x in ROW:
        g.gl_cmd("spawn", DUMMY, x, 0)
    g.gl_cmd("givestacks", CLIP, 999)
    time.sleep(0.5)
    g.gl_cmd("bench", tag, 300, 200, "noskills", *(["off"] if off else []))
    ev = g.wait_gl(lambda o: o.get("ev") == "bench" and o.get("tag") == tag, 20)
    g.gl_cmd("kill", 600, "target_dummy")
    rows = sorted((ev or {}).get("dummies", []), key=lambda d: d.get("dist", 0))
    return [round(d.get("dmg", 0), 1) for d in rows]


def run(p, **kw):
    g = p.game
    flags = {}
    g.gl_cmd("equip", "hwp_rifle_01", 1, 1)
    time.sleep(1.5)
    r = shot(g, "pierce_rifle")
    ok = len(r) == 4 and r[0] > 0 and r[1] == 0 and r[2] == 0 and r[3] == 0
    flags["rifle_no_pierce"] = {"ok": ok, "detail": f"damage by distance 22/40/58/76: {r}"}
    g.gl_cmd("equip", "hwp_glock_mh_01", 1, 1)
    g.gl_cmd("equip", "hwp_glock_oh_01", 1, 1)
    time.sleep(1.5)
    r = shot(g, "pierce_glock")
    ok = len(r) == 4 and r[0] > 0 and r[1] == 0 and r[2] == 0 and r[3] == 0
    flags["glock_no_pierce"] = {"ok": ok, "detail": f"damage by distance 22/40/58/76: {r}"}
    for k, v in flags.items():
        print(("PASS " if v["ok"] else "FAIL ") + k + ": " + v["detail"])
    out = {k: v["ok"] for k, v in flags.items()}
    out["terminal"] = "; ".join(f"{k}: {v['detail']}" for k, v in flags.items())
    return out
