// gamelab-hands: the firearms demo's orb (gamelab/skill_sphere_endless.unit). A SkillSphere
// whose pick never uses it up: GiveSkillSphereMenu calls PickedSkill before SkillTempUp and
// only grants the orb when it returns true (GiveSkillSphereMenu.as:266-287). Instead of
// SetUsed (hidden, no collision), the rolled picks are cleared so the next use rolls three new.
class GameLabEndlessSphere : SkillSphere
{
	GameLabEndlessSphere(UnitPtr unit, SValue& params)
	{
		super(unit, params);
	}

	bool PickedSkill() override
	{
		skillPicks.removeRange(0, skillPicks.length());
		m_rerolled = false;
		print("[gamelab] endless orb: picked, stays for the next pick");
		return true;
	}
}
