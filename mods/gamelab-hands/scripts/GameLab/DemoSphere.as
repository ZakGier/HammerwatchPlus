// gamelab-hands: the firearms demo's orb (gamelab/skill_sphere_endless.unit). A SkillSphere
// whose pick never uses it up: GiveSkillSphereMenu calls PickedSkill before SkillTempUp and
// only grants the orb when it returns true (GiveSkillSphereMenu.as:266-287). Instead of
// SetUsed (hidden, no collision), the rolled picks are cleared so the next use rolls three new.
class GameLabEndlessSphere : SkillSphere
{
	GameLabEndlessSphere(UnitPtr unit, SValue& params)
	{
		super(unit, params);
		@GameLab::g_endlessSphere = this;
	}

	bool PickedSkill() override
	{
		skillPicks.removeRange(0, skillPicks.length());
		m_rerolled = false;
		print("[gamelab] endless orb: picked, stays for the next pick");
		return true;
	}
}

namespace GameLab
{
	GameLabEndlessSphere@ g_endlessSphere;

	// spherepicks <skillId> [skillId] [skillId]: the next use of the last spawned endless orb
	// (gamelab/skill_sphere_endless.unit) offers these orbs of the local player's class, not a
	// roll: GiveSkillSphereMenu shows a sphere's skillPicks as they are when it has any
	// (GiveSkillSphereMenu.as:103-110). For checking what one orb's pick shows.
	void VerbSpherePicks(const string &in id, array<string>@ args)
	{
		auto rec = GetLocalPlayerRecord();
		if (g_endlessSphere is null || rec is null || args.length() < 1 || args.length() > 3)
		{
			Fail(id, "usage: spherepicks <skillId> [skillId] [skillId], after spawning gamelab/skill_sphere_endless.unit");
			return;
		}
		array<PlayerSkillDef@> picks;
		for (uint i = 0; i < args.length(); i++)
		{
			auto def = rec.playerClass.GetSkillDef(HashString(args[i]));
			if (def is null)
			{
				Fail(id, "no skill " + args[i] + " in " + rec.playerClass.m_id);
				return;
			}
			picks.insertLast(def);
		}
		g_endlessSphere.skillPicks = picks;
		Emit(Reply(id, true).Int("picks", picks.length()));
	}
}
