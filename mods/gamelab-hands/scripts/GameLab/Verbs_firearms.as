// gamelab-hands: read-outs the firearms plan checks need (gamelab/bots/plan_firearms.py):
// where the mouse cursor points in the world, the floating combat texts on screen, and the
// live skill bar with the button each skill answers to, and orb, which grants a skill orb.
namespace GameLab
{
	// cursor [dx dy]: the current GameInput's mouse position in world space, the point a
	// targeted skill lands on (PlayerTargetingHelper.as:264, CalcMouseTargetPos(ToWorldspace(
	// input.MousePos))), with the player's position. With dx dy it first writes MousePos =
	// ToScreenspace(player + (dx, dy)) into every GameInput seen (Input.as SeeInput); the
	// engine may overwrite it from the OS cursor, so the reply reads it back.
	void VerbCursor(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		vec3 ppos = plr.m_unit.GetPosition();
		bool doSet = args.length() >= 2;
		if (doSet)
		{
			vec2 screen = ToScreenspace(ppos + vec3(parseFloat(args[0]), parseFloat(args[1]), 0));
			for (uint i = 0; i < g_inputs.length(); i++)
				g_inputs[i].MousePos = screen;
			auto cur = GetInput();
			if (cur !is null)
				cur.MousePos = screen;
		}
		auto gi = GetInput();
		if (gi is null)
		{
			Fail(id, "no current GameInput");
			return;
		}
		vec2 mouse = gi.MousePos;
		vec3 w = ToWorldspace(mouse);
		Emit(Reply(id, true).Bool("set", doSet).Num("px", ppos.x).Num("py", ppos.y)
			.Num("sx", mouse.x).Num("sy", mouse.y).Num("x", w.x).Num("y", w.y)
			.Num("dx", w.x - ppos.x).Num("dy", w.y - ppos.y)
			.Bool("gamepad", gi.UsingGamepad).Int("inputs", g_inputs.length()));
	}

	const uint FLOATS_CAP = 48;

	// floats: the floating texts alive now (g_floatingTexts, FloatingText.as: AddFloatingText,
	// what damage numbers are): type (FloatingTextType: 8 EnemyHurtLocal, 9 EnemyHurtHusk, 11 a
	// crit "n!"; Actor.AddFloatingHurt), text, number, world position, ms lived. Read-only,
	// capped at FLOATS_CAP, oldest first.
	void VerbFloats(const string &in id, array<string>@ args)
	{
		array<string> items;
		uint alive = 0;
		for (uint i = 0; i < g_floatingTexts.length(); i++)
		{
			auto ft = g_floatingTexts[i];
			if (ft is null || !ft.m_alive)
				continue;
			alive++;
			if (items.length() >= FLOATS_CAP)
				continue;
			Json e;
			e.Int("type", int(ft.m_type)).Str("text", ft.m_floatingText).Int("num", ft.m_num)
				.Num("x", ft.m_pos.x).Num("y", ft.m_pos.y).Int("lived", ft.m_timeLived);
			items.insertLast(e.Close());
		}
		int truncated = alive > FLOATS_CAP ? int(alive - FLOATS_CAP) : 0;
		Emit(Reply(id, true).Int("count", alive).Int("truncated", truncated).Raw("texts", RawArray(items)));
	}

	// skillbar: the local player's live skills (PlayerBase.m_skills) in order: id, type
	// (PlayerSkillType), targeting mode (Skills::TargetingMode: 0 Passive, 1 Direction,
	// 4 TargetAOE), flat mana cost (GetCost), cooldown progress, and the button the input
	// helper reads it from: PlayerTargetingHelper.GetSkillInput (744-749) counts the non-passive
	// spells after the dash, 0 Skill1, 1 Skill2, 2 Skill3, 3-5 core's extra keys hwp_skill4..6
	// (SpellButton, Input.as; Skill3 without core). With mana as a fraction
	// of the record (m_record.mana) times the maximum, unrounded.
	void VerbSkillbar(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		array<string> items;
		int spell = 0;
		for (uint i = 0; i < plr.m_skills.length(); i++)
		{
			auto sk = plr.m_skills[i];
			if (sk is null)
				continue;
			auto mode = sk.GetTargetingMode();
			string button = "";
			if (sk.m_type == PlayerSkillType::MainHand)
				button = "main";
			else if (sk.m_type == PlayerSkillType::OffHand)
				button = "off";
			else if (sk.m_type == PlayerSkillType::Dash)
				button = "dash";
			else if (i >= 1 && mode != Skills::TargetingMode::Passive && sk.m_type == PlayerSkillType::Spell)
			{
				button = SpellButton(plr, spell);
				spell++;
			}
			auto cost = sk.GetCost();
			Json e;
			e.Str("id", sk.m_id).Int("type", int(sk.m_type)).Int("mode", int(mode)).Str("button", button)
				.Int("mana", cost is null ? 0 : cost.flatCost.y).Num("cd", sk.GetCooldownProgess(0));
			items.insertLast(e.Close());
		}
		float mana = plr.GetMana() * plr.GetMaxMana();
		Emit(Reply(id, true).Num("mana", mana).Int("manaMax", plr.GetMaxMana()).Int("spells", spell)
			.Raw("skills", RawArray(items)));
	}

	const uint TARGETS_CAP = 24;

	// targets [radius] [filter]: who each CompositeActorBehavior within radius (default 400) of the
	// player is after: its m_target (unit, name; 0 / "" for none) and m_targetAggro, the value a
	// new SetTarget must reach to take over (CompositeActorBehavior.SetTarget; a taunt's aggro -1
	// always does). Filter as near (behaviour or .unit path). Read-only, capped at TARGETS_CAP:
	// count is every match, truncated the matches left out.
	void VerbTargets(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		int radius = args.length() > 0 ? int(parseInt(args[0])) : 400;
		string filter = args.length() > 1 ? args[1] : "";
		vec2 center = xy(plr.m_unit.GetPosition());
		auto units = g_scene.FetchAllUnits(~0, center, radius);
		array<string> items;
		uint matched = 0;
		for (uint i = 0; i < units.length(); i++)
		{
			UnitPtr u = units[i];
			if (!u.IsValid() || u.IsDestroyed())
				continue;
			auto a = cast<CompositeActorBehavior>(u.GetScriptBehavior());
			if (a is null || a.IsDead())
				continue;
			vec3 pos = u.GetPosition();
			if (dist(center, xy(pos)) > radius)
				continue;
			if (filter != "" && Reflect::GetTypeName(a).findFirst(filter) < 0 && u.GetDebugName().findFirst(filter) < 0)
				continue;
			if (++matched > TARGETS_CAP)
				continue;
			int tid = 0;
			string tname = "";
			if (a.m_target !is null && a.m_target.m_unit.IsValid())
			{
				tid = a.m_target.m_unit.GetId();
				tname = a.m_target.m_unit.GetDebugName();
			}
			Json e;
			e.Int("unit", u.GetId()).Str("name", u.GetDebugName()).Num("x", pos.x).Num("y", pos.y)
				.Int("target", tid).Str("targetName", tname).Num("aggro", a.m_targetAggro);
			items.insertLast(e.Close());
		}
		int truncated = matched > TARGETS_CAP ? int(matched - TARGETS_CAP) : 0;
		Emit(Reply(id, true).Int("count", matched).Int("truncated", truncated).Raw("units", RawArray(items)));
	}

	// orb <orbId> [times|down]: PlayerRecord.SkillTempUp on an orb (a skill's modifier-skills
	// entry, PlayerClass.GetSkillDef) times times (default 1), as a picked-up skill sphere does
	// (Cheats.as:669); "down" takes one level off (SkillTempDown). Does not check
	// blocked-by-skills: the sphere menu filters those. Replies the orb's temp level after.
	void VerbOrb(const string &in id, array<string>@ args)
	{
		auto rec = GetLocalPlayerRecord();
		if (rec is null || rec.playerClass is null)
		{
			Fail(id, "no local character");
			return;
		}
		if (args.length() < 1)
		{
			Fail(id, "usage: orb <orbId> [times|down]");
			return;
		}
		auto def = rec.playerClass.GetSkillDef(HashString(args[0]));
		if (def is null)
		{
			Fail(id, "no skill " + args[0] + " in " + rec.playerClass.m_id);
			return;
		}
		bool down = args.length() > 1 && args[1] == "down";
		int times = down ? 1 : (args.length() > 1 ? int(parseInt(args[1])) : 1);
		int done = 0;
		for (int i = 0; i < times; i++)
		{
			if (down ? rec.SkillTempDown(def) : rec.SkillTempUp(def))
				done++;
		}
		int level = 0;
		if (!rec.pickedTempSkills.get(def.m_id, level))
			level = 0;
		Emit(Reply(id, done == times).Str("orb", args[0]).Int("changed", done).Int("level", level));
	}

	const int CRITPROBE_MAX = 20000;

	// critprobe <rolls> <radius> <filter> [skillId]: read-only. What a hit on the nearest live
	// actor matching filter would roll, as PlayerBase.DamageDealt does (PlayerBase.as:855-900):
	// modifiers.Crit(player, actor, skill) > 0 counted over rolls calls (the dynamic crits:
	// HWPFirearmsStackCrit, Exposure, Headshot), modifiers.DamageMul(player, actor), the
	// static crit stats (currStats MainHand/OffHand/Spell CritChance and CritDamage), the
	// skill's m_modCritChance/m_modCritDamage/m_modDamageMul (SkillCrit, BaseSkillModifier),
	// and every custom stat. Rolls are capped at CRITPROBE_MAX.
	void VerbCritProbe(const string &in id, array<string>@ args)
	{
		auto plr = cast<Player>(GetLocalPlayer());
		if (plr is null || args.length() < 3)
		{
			Fail(id, plr is null ? "no spawned local player" : "usage: critprobe <rolls> <radius> <filter> [skillId]");
			return;
		}
		int rolls = min(CRITPROBE_MAX, max(0, int(parseInt(args[0]))));
		float radius = parseFloat(args[1]);
		vec2 center = xy(plr.m_unit.GetPosition());
		auto units = g_scene.FetchAllUnits(~0, center, int(radius));
		Actor@ target = null;
		float best = radius + 1;
		for (uint i = 0; i < units.length(); i++)
		{
			if (!units[i].IsValid() || units[i].IsDestroyed() || units[i] == plr.m_unit)
				continue;
			auto actor = cast<Actor>(units[i].GetScriptBehavior());
			if (actor is null || actor.IsDead() || units[i].GetDebugName().findFirst(args[2]) < 0)
				continue;
			float d = dist(center, xy(units[i].GetPosition()));
			if (d < best)
			{
				best = d;
				@target = actor;
			}
		}
		if (target is null)
		{
			Fail(id, "no live actor matching " + args[2] + " within " + args[1]);
			return;
		}
		Skills::Skill@ skill = null;
		if (args.length() > 3)
		{
			uint sid = HashString(args[3]);
			for (uint i = 0; i < plr.m_skills.length() && skill is null; i++)
			{
				if (plr.m_skills[i] !is null && plr.m_skills[i].m_skillId == sid)
					@skill = plr.m_skills[i];
			}
			if (skill is null)
			{
				Fail(id, "the player has no skill " + args[3]);
				return;
			}
		}
		auto mods = plr.m_record.GetModifiers();
		int crits = 0;
		for (int i = 0; i < rolls; i++)
		{
			if (mods.Crit(plr, target, skill) > 0)
				crits++;
		}
		vec2 dmul = mods.DamageMul(plr, target);
		auto st = plr.m_record.currStats;
		array<string> custom;
		for (uint i = 0; i < st.m_customStats.length(); i++)
		{
			auto cs = st.m_customStats[i];
			if (cs.svalue is null)
				continue;
			Json c;
			c.Str("id", cs.id).Raw("value", formatFloat(cs.svalue.GetFloat(), "", 0, 4));
			custom.insertLast(c.Close());
		}
		auto j = Reply(id, true);
		j.Str("target", target.m_unit.GetDebugName()).Num("dist", best).Int("rolls", rolls).Int("crits", crits)
			.Raw("damageMul", "[" + formatFloat(dmul.x, "", 0, 4) + "," + formatFloat(dmul.y, "", 0, 4) + "]")
			.Raw("mainCrit", formatFloat(st.MainHand.CritChance, "", 0, 4)).Raw("mainCritDmg", formatFloat(st.MainHand.CritDamage, "", 0, 4))
			.Raw("offCrit", formatFloat(st.OffHand.CritChance, "", 0, 4)).Raw("offCritDmg", formatFloat(st.OffHand.CritDamage, "", 0, 4))
			.Raw("spellCrit", formatFloat(st.SpellCritChance, "", 0, 4)).Raw("spellCritDmg", formatFloat(st.SpellCritDamage, "", 0, 4));
		if (skill !is null)
			j.Str("skill", args[3]).Raw("skillCrit", formatFloat(skill.m_modCritChance, "", 0, 4))
				.Raw("skillCritDmg", formatFloat(skill.m_modCritDamage, "", 0, 4)).Raw("skillDmgMul", formatFloat(skill.m_modDamageMul, "", 0, 4));
		j.Raw("custom", RawArray(custom));
		Emit(j);
	}

	void Register_firearms()
	{
		RegisterVerb("orb", "<orbId> [times|down]", Verb(VerbOrb));
		RegisterVerb("cursor", "[dx dy]", Verb(VerbCursor));
		RegisterVerb("floats", "", Verb(VerbFloats));
		RegisterVerb("skillbar", "", Verb(VerbSkillbar));
		RegisterVerb("targets", "[radius] [filter]", Verb(VerbTargets));
		RegisterVerb("critprobe", "<rolls> <radius> <filter> [skillId]", Verb(VerbCritProbe));
	}
}
