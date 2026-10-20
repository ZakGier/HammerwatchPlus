"""Grenade launcher point-blank slug check (rifle_gl_shell.unit, Launcher.as HWPFirearmsArm):
one launcher shot at a lone target dummy 30 px away (the shell leaves 22 px out and arms after
40 px of flight, so this one is unarmed) and one at 100 px (armed), each from a short bench
holding the off hand only (`gl bench ... offonly`), which reports the launcher's own hits. Flags:
- slug_half: the close hit deals about half of the armed one (median of three shots each; crits
  make single shots noisy);
- slug_stuns: the close dummy wears a stun (stun_gl, players/hwp/firearms/buffs_firearms.sval) right after;
- blast_no_stun: the armed blast stuns nothing."""
import statistics
import time

DUMMY = "doodads/generic/target_dummy_normal.unit"
GL = "hwp_attack_rifle_gl"


def shot(g, tag, x, ms):
    """one launcher shot (bench offonly: the off hand alone, so no rifle burst blocks it) at a
    lone dummy x px to the right; the launcher's own hits (weapons: hwp_attack_rifle_gl) and the
    dummy's buffs just after."""
    g.gl_cmd("kill", 600, "target_dummy")
    time.sleep(0.3)
    g.gl_cmd("spawn", DUMMY, x, 0)
    g.console("cht_give_mana 999")
    time.sleep(0.5)
    g.gl_cmd("bench", tag, ms, 200, "noskills", "offonly")
    ev = g.wait_gl(lambda o: o.get("ev") == "bench" and o.get("tag") == tag, 20) or {}
    # the stun lasts 500 ms: read the dummy while it is on
    buffs = g.gl_cmd("actorbuffs", 200, "target_dummy").get("actors", [])
    g.gl_cmd("kill", 600, "target_dummy")
    hits = [w for w in ev.get("weapons", []) if w.get("weapon") == GL]
    dmg = round(sum(w.get("dmg", 0) for w in hits), 1)
    n = sum(w.get("hits", 0) for w in hits)
    # a buff's name (m_def.m_name) reads "" for these; its tags tell the stun (stun_gl: debuff, stun)
    return dmg, n, [b.get("tags", []) for a in buffs for b in a.get("buffs", [])]


def run(p, **kw):
    g = p.game
    g.console("e_cheats 1")
    time.sleep(0.3)
    g.gl_cmd("char", "hwp_firearms", "Slug", timeout=60)
    g.wait_gl(lambda o: o.get("ev") == "hb" and o.get("phase") == "town", 60, fresh=True)
    time.sleep(2)
    g.console("e_cheats 1")
    time.sleep(0.3)
    g.gl_cmd("equip", "hwp_rifle_01", 1, 1)
    time.sleep(1.5)
    near, far = [], []
    near_buffs, far_buffs = [], []
    hits = []
    for i in range(3):
        # one shot each: the launcher's cooldown is 1.5 s; the far shell needs ~260 ms to arrive
        d, n, b = shot(g, f"slug_near_{i}", 30, 200)
        near.append(d)
        near_buffs.append(b)
        hits.append(n)
        d, n, b = shot(g, f"slug_far_{i}", 100, 400)
        far.append(d)
        far_buffs.append(b)
        hits.append(n)
    mn, mf = statistics.median(near), statistics.median(far)
    ratio = mn / mf if mf else 0
    flags = {
        "slug_half": {"ok": mf > 0 and 0.4 <= ratio <= 0.6 and all(n == 1 for n in hits),
                      "detail": f"30 px {near} vs 100 px {far} (hits {hits}): median ratio {ratio:.2f} (want 0.5)"},
        "slug_stuns": {"ok": all(any("stun" in t for t in b) for b in near_buffs),
                       "detail": f"buff tags on the 30 px dummy after each shot: {near_buffs}"},
        "blast_no_stun": {"ok": not any(any("stun" in t for t in b) for b in far_buffs),
                          "detail": f"buff tags on the 100 px dummy after each shot: {far_buffs}"},
    }
    for k, v in flags.items():
        print(("PASS " if v["ok"] else "FAIL ") + k + ": " + v["detail"])
    out = {k: v["ok"] for k, v in flags.items()}
    out["terminal"] = "; ".join(f"{k}: {v['detail']}" for k, v in flags.items())
    return out
