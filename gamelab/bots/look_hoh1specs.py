"""Look only, not evidence of play: pictures of the classes mod's HoH1-style 4th specs, the
Priest's Smiter and the Paladin's Holy Storm. For each: the Subclass Picker on the spec, then
each active cast at target dummies on a cleared Bandit Keep floor at timescale 0.25 with a
run of shots through the cast, and for Last Rites a credited kill while hurt. Reuses
plan_classesb's character, picker and floor steps.

Sections: priest, paladin."""
import time

from gamelab.bots.plan_classesb import Checks as Base

TARGET = "doodads/generic/target_dummy_normal.unit"
BRUTE = "actors/humans/bandits/bandit_brute.unit"


class Look(Base):
    def picker_shot(self, spec_name, tag):
        """The Subclass Picker stepped to `spec_name`, shot, closed."""
        self.npc("npc_subclass_picker", "actors/npcs/town/npc_subclass_picker.unit")
        self.gl("use", "npc_subclass_picker")
        time.sleep(0.8)
        shown = []
        for _ in range(6):
            roots = self.gl("widgets", 12).get("roots", [])
            curr = next((n.get("text", "") for r in roots for n in r.get("nodes", []) if n.get("id") == "class-curr"), "")
            shown.append(curr)
            if curr == spec_name:
                break
            self.gl("func", "nextclass")
            time.sleep(0.3)
        time.sleep(0.5)
        self.g.shot(f"{tag} 0 picker")
        self.notes.append(f"{tag} picker: {shown}")
        if self.gl("state").get("window"):
            self.g.key("escape")
            time.sleep(0.5)

    def setup(self, tag, cls, spec_id, spec_name, skills):
        self.new_char(cls, "Look" + tag.capitalize())
        self.picker_shot(spec_name, tag)
        self.gl("subclass", spec_id)
        self.hwp("skillpoints 30")
        for s in skills:
            self.gl("skill", s, 5)  # top rank: the most blades, the biggest numbers
        return self.enter_floor(tag)

    def targets(self, *at):
        self.gl("kill", 600, "target_dummy")
        self.gl("kill", 600, "bandit_brute")
        time.sleep(0.3)
        for x, y in at:
            self.gl("spawn", TARGET, x, y)
        time.sleep(0.4)

    def cast_shots(self, name, button, times=(0.1, 0.35, 0.7, 1.1, 1.6, 2.2), aim=(1, 0)):
        """Press `button` at timescale 0.25 and shoot at these real-time offsets."""
        self.console_mana()
        self.gl("timescale", 0.25)
        time.sleep(0.2)
        self.gl("input", 320, 0, 0, aim[0], aim[1], button)
        t0 = time.time()
        for k, t in enumerate(times):
            time.sleep(max(0.0, t0 + t - time.time()))
            self.g.shot(f"{name} {k + 1}", settle=False)
        self.gl("timescale", 1)
        time.sleep(0.5)

    def console_mana(self):
        self.g.console("cht_give_mana 999")
        time.sleep(0.2)

    def priest(self):
        skills = ["hwp_priest_hoh1_smite", "hwp_priest_hoh1_divine_hammer", "hwp_priest_hoh1_last_rites"]
        if not self.setup("priest", "priest", "hwp_priest_hoh1", "Smiter", skills):
            return
        self.targets((30, -8), (34, 10))
        self.cast_shots("priest 1 smite", self.button_for("smite", skills[0], "skill2"))
        time.sleep(1.5)
        self.targets((60, 0), (90, 20))
        self.cast_shots("priest 2 divine hammer", self.button_for("hammer", skills[1], "skill3"),
                        times=(0.2, 0.6, 1.0, 1.5, 2.1, 2.8, 3.6))
        # Last Rites: hurt, then a credited kill beside you; the heal on the kill
        self.targets()
        self.gl("spawn", BRUTE, 40, 0)
        time.sleep(0.6)
        self.gl("hurt", 0.5)
        time.sleep(0.4)
        self.g.shot("priest 3 last rites 1 hurt", settle=False)
        self.gl("timescale", 0.25)
        self.gl("kill", 300, "bandit_brute", "me")
        for k in range(3):
            time.sleep(0.25)
            self.g.shot(f"priest 3 last rites {k + 2} kill", settle=False)
        self.gl("timescale", 1)
        self.gl("hurt", 1)
        self.to_town()

    def paladin(self):
        skills = ["hwp_paladin_hoh1_holy_storm", "hwp_paladin_hoh1_shield_of_faith", "hwp_paladin_hoh1_zealous_charge"]
        if not self.setup("paladin", "paladin", "hwp_paladin_hoh1", "Holy Storm", skills):
            return
        self.targets((50, 0), (0, 50), (-50, 0), (0, -50), (40, 40))
        self.cast_shots("paladin 1 holy storm", self.button_for("holy_storm", skills[0], "skill2"),
                        times=(0.2, 0.6, 1.0, 1.5, 2.1, 2.8, 3.6))
        time.sleep(1.0)
        self.targets()
        self.cast_shots("paladin 2 shield of faith", self.button_for("sof", skills[1], "skill3"),
                        times=(0.2, 0.6, 1.2))
        self.targets((90, 0))
        self.gl("cursor", 90, 0)
        self.cast_shots("paladin 3 zealous charge", self.button_for("charge", skills[2], "hwp_skill4"),
                        times=(0.1, 0.4, 0.8, 1.2, 1.7, 2.3))
        self.to_town()


def run(p, sections="priest,paladin", **_):
    c = Look(p)
    for s in sections.split(","):
        try:
            getattr(c, s)()
        except Exception as e:
            c.flag(f"{s}_crashed", False, repr(e))
    c.out["notes"] = c.notes
    c.out["terminal"] = " | ".join(c.notes)[-3000:]
    return c.out
