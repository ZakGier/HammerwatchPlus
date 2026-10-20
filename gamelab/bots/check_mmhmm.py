"""Core's Mm-hmm! hat bonus (scripts/HWP/Core/MmHmm.as, tweak/hwp/modifiers_mmhmm.sval).

Rare item-level-1 head items from the `kit` verb (ilvl 20 ones ask for more attributes than
the lab character has, so `kit` could not put them on) (Equipment::Generator mods, as a drop rolls them), one
after another: each one that qualifies (25 %, a function of the item) gets the bonus on top
of its rolled modifiers, the others never do; a common hat never does. Then the worn hat
gets it (`hwp mmhmm give`) and the Service Pistol shoots a target dummy (`bench`): the crits made while
wearing it are counted. The voice itself is the modifier's crit TriggerEffect; GameLab is
muted, so the sound is not measured."""
import re
import time

from gamelab.bots.bench import CLIP, DUMMY
from gamelab.bots.plan_checks import Checks as Base

LINE = r"mmhmm: hat (\S+)(?: \((.*?)\))?, bonus (yes|no), qualifies (yes|no), added (\d+), crits with it (\d+)"


class Checks(Base):
    def status(self):
        m = re.findall(LINE, self.hwp("mmhmm", 0.4, until="mmhmm: hat"))
        return m[-1] if m else None

    def hats(self, n=16):
        self.gl("char", "hwp_firearms", "Hat")
        self.wait_phase("town", 60)
        time.sleep(2)
        self.g.console("e_cheats 1")
        self.hwp("levelup 20", 1.0)
        seen, bad = [], []
        for _ in range(n):
            self.gl("kit", 1, "rare", "head")
            time.sleep(1.2)  # checked twice a second
            st = self.status()
            if not st:
                bad.append("no status")
                continue
            hat, name, bonus, qual, _, _ = st
            seen.append((hat, bonus, qual))
            if bonus != qual:
                bad.append(f"{name}: bonus {bonus}, qualifies {qual}")
        yes = sum(1 for _, b, _ in seen if b == "yes")
        self.flag("mmhmm_rare_rule", len(seen) == n and not bad and 0 < yes < n,
                  f"{yes} of {len(seen)} rare hats with it; {bad}")
        self.gl("kit", 1, "common", "head")
        time.sleep(1.2)
        st = self.status()
        self.flag("mmhmm_common_never", bool(st) and st[2] == "no" and st[3] == "no", f"{st}")
        # a rerolled check never takes it off or adds it twice
        before = st[4] if st else "?"
        time.sleep(1.5)
        st2 = self.status()
        self.flag("mmhmm_stable", bool(st2) and st2[4] == before, f"added {before} -> {st2[4] if st2 else '?'}")

    def crits(self, ms=40000):  # ~100 pistol hits at a few % crit
        st = self.status()
        self.hwp("mmhmm give", 0.4, until="mmhmm: hat")
        st = self.status()
        self.flag("mmhmm_given", bool(st) and st[2] == "yes", f"{st}")
        c0 = int(st[5]) if st else 0
        # the character's Service Pistol shoots (an ilvl 20 rifle asks for more Dexterity)
        self.gl("kill", 600, "target_dummy")
        self.gl("spawn", DUMMY, 0, 80)
        self.gl("givestacks", CLIP, 999)
        time.sleep(0.5)
        self.gl("bench", "mmhmm", ms, 400, "noskills")
        ev = self.g.wait_gl(lambda o: o.get("ev") == "bench" and o.get("tag") == "mmhmm", ms / 1000 + 30) or {}
        st = self.status()
        c1 = int(st[5]) if st else 0
        self.flag("mmhmm_crits", c1 > c0, f"crits with it {c0} -> {c1}; bench {str(ev)[:200]}")


def run(p, sections="hats,crits", **_):
    c = Checks(p)
    for s in sections.split(","):
        if not s:
            continue
        try:
            getattr(c, s)()
        except Exception as e:
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
