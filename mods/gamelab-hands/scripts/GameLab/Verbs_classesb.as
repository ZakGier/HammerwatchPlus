// gamelab-hands: verbs for the class/mastery checks (plan_classesb). buffs and skills only
// read the local player's actor; hurt writes the health fraction the way Block.as does.
namespace GameLab
{
	const uint CLASSESB_CAP = 32;

	// the button a learned skill listens on: the same walk as
	// PlayerTargetingHelper.GetSkillInput (Behaviors/Actors/Player/PlayerTargetingHelper.as:713-750):
	// spells that are not passive count from m_skills[1] on; the 3rd is Skill3, the 4th to 6th
	// core's extra keys hwp_skill4..6 (SpellButton, Input.as; all Skill3 without core)
	string SkillButton(PlayerBase@ plr, Skills::Skill@ skill)
	{
		if (skill.m_type == PlayerSkillType::MainHand)
			return "main";
		if (skill.m_type == PlayerSkillType::OffHand)
			return "off";
		if (skill.m_type == PlayerSkillType::Dash)
			return "dash";
		if (skill.GetTargetingMode() == Skills::TargetingMode::Passive)
			return "";
		int idx = 0;
		for (uint i = 1; i < plr.m_skills.length(); i++)
		{
			if (plr.m_skills[i].GetTargetingMode() == Skills::TargetingMode::Passive)
				continue;
			if (plr.m_skills[i].m_type != PlayerSkillType::Spell)
				continue;
			if (plr.m_skills[i] is skill)
				break;
			idx++;
		}
		return SpellButton(plr, idx);
	}

	// buffs: the local player's active buffs (ActorBuffList.m_buffs): name key, the def's
	// duration, the ms left (ActorBuff.m_duration), whether the def has a HUD icon
	// (ActorBuffDef.m_hud) and whether HUD.ShowBuffIcon gave it a visible widget, with that
	// widget's "num" text (ActorBuff.UpdateHudIcon: seconds left); now = g_scene.GetTime().
	// Read-only, capped.
	void VerbBuffs(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		array<string> items;
		uint n = plr.m_buffs.m_buffs.length();
		for (uint i = 0; i < n && items.length() < CLASSESB_CAP; i++)
		{
			auto b = plr.m_buffs.m_buffs[i];
			if (b is null || b.m_def is null)
				continue;
			string num = "";
			bool icon = b.m_hudIcon !is null && b.m_hudIcon.m_visible;
			if (b.m_hudIcon !is null)
			{
				auto t = cast<TextWidget>(b.m_hudIcon.GetWidgetById("num"));
				if (t !is null)
					num = t.m_str;
			}
			Json j;
			j.Str("name", b.m_def.m_name).Int("dur", b.m_def.m_duration).Int("left", b.m_duration)
				.Bool("hud", b.m_def.m_hud !is null).Bool("icon", icon).Str("num", num);
			items.insertLast(j.Close());
		}
		Emit(Reply(id, true).Int("now", int(g_scene.GetTime())).Raw("buffs", RawArray(items))
			.Int("count", n).Bool("truncated", n > CLASSESB_CAP));
	}

	// skills: the local player's live skills (PlayerBase.m_skills, built by LoadSkills from
	// the learned class skills and the equipment): id, type, targeting mode, cooldown left
	// (PlayerSkill.m_cooldownC, the class PlayerSkillDirectional/Position/Leap derive from;
	// else ActiveSkill.m_cooldownC; -1 for neither) and the button it listens on
	// (SkillButton, as GetSkillInput). Read-only, capped.
	void VerbSkills(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		array<string> items;
		uint n = plr.m_skills.length();
		for (uint i = 0; i < n && items.length() < CLASSESB_CAP; i++)
		{
			auto s = plr.m_skills[i];
			if (s is null)
				continue;
			int cd = -1;
			auto ps = cast<Skills::PlayerSkill>(s);
			if (ps !is null)
				cd = ps.m_cooldownC;
			else
			{
				auto act = cast<Skills::ActiveSkill>(s);
				if (act !is null)
					cd = act.m_cooldownC;
			}
			Json j;
			j.Str("id", s.m_id).Int("type", int(s.m_type)).Int("mode", int(s.GetTargetingMode()))
				.Int("cd", cd).Str("button", SkillButton(plr, s));
			items.insertLast(j.Close());
		}
		Emit(Reply(id, true).Int("now", int(g_scene.GetTime())).Int("mana", plr.m_record.CurrentMana())
			.Raw("skills", RawArray(items)).Int("count", n).Bool("truncated", n > CLASSESB_CAP));
	}

	// hurt <fraction>: set the local player's health fraction (PlayerRecord.hp), the direct
	// write Block.as makes for a health-cost block (Behaviors/Actors/Modifiers/Block.as:218);
	// not a damage path, so no hit, no regen delay and no kill hooks.
	void VerbHurt(const string &in id, array<string>@ args)
	{
		auto rec = GetLocalPlayerRecord();
		if (rec is null || args.length() < 1)
		{
			Fail(id, rec is null ? "no local character" : "usage: hurt <fraction>");
			return;
		}
		float f = float(parseFloat(args[0]));
		rec.hp = max(0.01f, min(1.0f, f));
		Emit(Reply(id, true).Int("hp", rec.CurrentHealth()).Int("hpMax", rec.MaxHealth()));
	}

	void Register_classesb()
	{
		RegisterVerb("buffs", "", Verb(VerbBuffs));
		RegisterVerb("skills", "", Verb(VerbSkills));
		RegisterVerb("hurt", "<fraction>", Verb(VerbHurt));
	}
}
