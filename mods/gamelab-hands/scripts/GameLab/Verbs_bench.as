// gamelab-hands: a damage bench for class balance (gamelab/bots/bench.py). bench holds the
// main attack (and optionally the off hand) at the target dummies and casts every active
// skill the way the input helper would whenever it can, for ms of gameplay frames, then
// reports the damage the dummies took. Registered by its own module so the verb list in
// Hands.as stays as it is.
namespace GameLab
{
	const string BENCH_FILTER = "target_dummy";

	const uint BENCH_RELOAD = HashString("hwp_fs_reload");
	const string BENCH_CLIP = "players/hwp/firearms/stacks_firearms.sval:clip";

	class BenchSkill
	{
		Skills::Skill@ skill;
		int mode;
		int casts = 0;
		int chargeMs = -1;       // >= 0 while a DirectionCharge skill is being charged
		int channelMs = 0;
	}

	bool g_benchOn = false;
	dictionary g_benchDamage;    // weapon (skill id, or "other") -> damage of direct hits
	dictionary g_benchHits;

	class BenchTask : QueuedTasks::UpdatingTask
	{
		string m_tag;
		int m_msLeft;
		int m_t = 0;
		int m_radius;
		bool m_off;
		bool m_skills;
		uint m_frames = 0;
		array<UnitPtr> m_dummies;
		array<float> m_hp0;
		array<BenchSkill@> m_bench;
		int m_manaLowMs = 0;

		void Start(PlayerBase@ plr)
		{
			// every bench starts the same way: no summons left from the last one, every
			// cooldown ready, a full mana bar
			plr.m_record.ClearSummons();
			for (uint i = 0; i < plr.m_skills.length(); i++)
			{
				if (plr.m_skills[i] !is null)
					plr.m_skills[i].ResetCooldown();
			}
			plr.m_record.mana = 1.0f;
			vec2 c = xy(plr.m_unit.GetPosition());
			auto units = g_scene.FetchAllUnits(~0, c, m_radius);
			for (uint i = 0; i < units.length(); i++)
			{
				auto a = cast<Actor>(units[i].GetScriptBehavior());
				if (a is null || a is plr || a.IsDead())
					continue;
				if (units[i].GetDebugName().findFirst(BENCH_FILTER) < 0)
					continue;
				m_dummies.insertLast(units[i]);
				m_hp0.insertLast(a.GetHealth());
			}
			for (uint i = 0; i < plr.m_skills.length(); i++)
			{
				auto s = plr.m_skills[i];
				if (s is null || s.m_type != PlayerSkillType::Spell)
					continue;
				int mode = int(s.GetTargetingMode());
				if (mode == int(Skills::TargetingMode::Passive))
					continue;
				BenchSkill b;
				@b.skill = s;
				b.mode = mode;
				m_bench.insertLast(b);
			}
			g_benchDamage.deleteAll();
			g_benchHits.deleteAll();
			g_benchOn = true;
		}

		vec2 Centre(vec2 from)
		{
			vec2 sum;
			int n = 0;
			for (uint i = 0; i < m_dummies.length(); i++)
			{
				if (!m_dummies[i].IsValid())
					continue;
				sum += xy(m_dummies[i].GetPosition());
				n++;
			}
			return n == 0 ? from + vec2(1, 0) : sum / float(n);
		}

		void Cast(Player@ plr, BenchSkill@ b, vec2 pos, vec2 goal, int ms)
		{
			auto s = b.skill;
			auto helper = plr.m_targetHelper;
			vec2 rel = goal - pos;
			float len = length(rel);
			vec2 dir = len > 0 ? rel / len : vec2(1, 0);

			// Firearms Reload as a player uses it: on an empty clip, not whenever the clip isn't
			// full (each cast stops the gun for the whole reload)
			if (s.m_skillId == BENCH_RELOAD)
			{
				auto clip = ActorBuffStackDef::Get(BENCH_CLIP);
				if (clip is null || plr.GetStacks(clip) > 0)
					return;
			}

			if (b.mode == int(Skills::TargetingMode::Toggle))
			{
				if (!s.m_isActive && !helper.CheckSkillBlocked(s) && s.Activate(vec2(), 1.0f))
				{
					s.m_isActive = true;
					helper.TriggerModifierEffects(s);
					b.casts++;
				}
				return;
			}
			if (b.mode == int(Skills::TargetingMode::Channeling))
			{
				if (s.IsActive())
				{
					b.channelMs += ms;
					if (b.channelMs >= 3000)
					{
						s.Release(dir);
						s.m_isActive = false;
						b.channelMs = 0;
					}
					return;
				}
				if (!helper.CheckSkillBlocked(s) && s.CanActivate(false) && s.Activate(dir, 1.0f))
				{
					helper.TriggerModifierEffects(s);
					b.casts++;
					b.channelMs = 0;
				}
				return;
			}
			if (b.mode == int(Skills::TargetingMode::DirectionCharge))
			{
				Skills::TargetingParams params;
				s.GetTargetingMode(params);
				if (b.chargeMs >= 0)
				{
					b.chargeMs += int(s.GetTotalSkillCastSpeed() * ms);
					if (b.chargeMs >= max(1, params.chargeTime))
					{
						b.chargeMs = -1;
						if (s.Activate(dir, 1.0f))
						{
							helper.TriggerModifierEffects(s);
							b.casts++;
						}
					}
					return;
				}
				if (!helper.CheckSkillBlocked(s) && s.CanActivate(false))
					b.chargeMs = 0;
				return;
			}
			if (s.IsActive() || helper.CheckSkillBlocked(s) || !s.CanActivate(false))
				return;
			vec2 target = dir;
			if (b.mode == int(Skills::TargetingMode::TargetAOE))
			{
				Skills::TargetingParams params;
				s.GetTargetingMode(params);
				target = pos + dir * min(params.rangeMax, max(params.rangeMin, len));
			}
			if (s.Activate(target, 1.0f))
			{
				helper.TriggerModifierEffects(s);
				b.casts++;
			}
		}

		bool Charging()
		{
			for (uint i = 0; i < m_bench.length(); i++)
			{
				if (m_bench[i].chargeMs >= 0)
					return true;
			}
			return false;
		}

		bool UpdateFrame(int ms) override
		{
			auto plr = cast<Player>(GetLocalPlayer());
			if (plr is null)
			{
				g_benchOn = false;
				Json j;
				Emit(j.Str("ev", "bench").Str("tag", m_tag).Str("error", "no local player"));
				return true;
			}
			if (m_frames == 0)
				Start(plr);
			m_frames++;
			m_t += ms;
			m_msLeft -= ms;

			vec2 pos = xy(plr.m_unit.GetPosition());
			vec2 goal = Centre(pos);
			vec2 aim = normalize(goal - pos);
			if (float(plr.m_record.mana) < 0.05f)
				m_manaLowMs += ms;

			if (m_msLeft > 0)
			{
				if (m_skills)
				{
					for (uint i = 0; i < m_bench.length(); i++)
						Cast(plr, m_bench[i], pos, goal, ms);
				}
				array<string> buttons;
				if (!Charging())
				{
					buttons.insertLast("main");
					if (m_off)
						buttons.insertLast("off");
				}
				Hold("bench", 200, vec2(), true, aim, buttons);
				return false;
			}

			Release();
			g_benchOn = false;
			for (uint i = 0; i < m_bench.length(); i++)
			{
				auto s = m_bench[i].skill;
				if (m_bench[i].mode == int(Skills::TargetingMode::Toggle) && s.m_isActive)
				{
					s.m_isActive = false;
					s.Deactivate();
				}
				else if (m_bench[i].mode == int(Skills::TargetingMode::Channeling) && s.IsActive())
				{
					s.Release(aim);
					s.m_isActive = false;
				}
			}

			double total = 0;
			array<string> dummies;
			for (uint i = 0; i < m_dummies.length(); i++)
			{
				Actor@ a = null;
				if (m_dummies[i].IsValid())
					@a = cast<Actor>(m_dummies[i].GetScriptBehavior());
				if (a is null)
					continue;
				double dmg = double(m_hp0[i] - a.GetHealth()) * double(a.GetMaxHp());
				total += dmg;
				Json e;
				e.Str("name", m_dummies[i].GetDebugName()).Num("dmg", dmg).Num("dist", dist(pos, xy(m_dummies[i].GetPosition())));
				dummies.insertLast(e.Close());
			}
			array<string> weapons;
			auto keys = g_benchDamage.getKeys();
			double hooked = 0;
			for (uint i = 0; i < keys.length(); i++)
			{
				double d = 0;
				int n = 0;
				g_benchDamage.get(keys[i], d);
				g_benchHits.get(keys[i], n);
				hooked += d;
				Json e;
				e.Str("weapon", keys[i]).Num("dmg", d).Int("hits", n);
				weapons.insertLast(e.Close());
			}
			array<string> casts;
			for (uint i = 0; i < m_bench.length(); i++)
			{
				Json e;
				e.Str("skill", m_bench[i].skill.m_id).Int("mode", m_bench[i].mode).Int("casts", m_bench[i].casts);
				casts.insertLast(e.Close());
			}
			float secs = max(0.001f, m_t / 1000.0f);
			Json j;
			Emit(j.Str("ev", "bench").Str("tag", m_tag).Int("ms", m_t).Int("frames", m_frames)
				.Num("total", total).Num("dps", total / secs).Num("hooked", hooked)
				.Num("manaEnd", float(plr.m_record.mana)).Int("manaLowMs", m_manaLowMs).Int("dummyCount", m_dummies.length())
				.Raw("dummies", RawArray(dummies)).Raw("weapons", RawArray(weapons)).Raw("casts", RawArray(casts)));
			return true;
		}
	}

	void BenchRecord(Player@ player, DamageInfo@ di)
	{
		if (!g_benchOn || di is null)
			return;
		string key = "other";
		if (di.Weapon != 0)
		{
			auto skill = player.GetSkill(di.Weapon);
			key = skill is null ? ("#" + di.Weapon) : skill.m_id;
		}
		double d = 0;
		int n = 0;
		g_benchDamage.get(key, d);
		g_benchHits.get(key, n);
		g_benchDamage.set(key, d + di.Damage);
		g_benchHits.set(key, n + 1);
	}

	// bench <tag> <ms> [radius] [off] [noskills]: hold the main attack (and the off hand with
	// "off") at the centre of the target dummies within radius (default 400) of the player and
	// cast every active spell whenever it may (Toggle once, TargetAOE at the centre, Channeling
	// for up to 3 s at a time, DirectionCharge after its charge time), for ms of gameplay frames.
	// One {"ev":"bench"} event at the end: the dummies' hp lost (every source: hits, DoT,
	// summons), the direct hits by weapon (PlayerDamagedActor), casts per skill and the mana left.
	void VerbBench(const string &in id, array<string>@ args)
	{
		if (args.length() < 2)
		{
			Fail(id, "usage: bench <tag> <ms> [radius] [off] [noskills]");
			return;
		}
		if (QueuedTasks::g_instance is null)
		{
			Fail(id, "no QueuedTasks module");
			return;
		}
		BenchTask task;
		task.m_tag = args[0];
		task.m_msLeft = int(parseInt(args[1]));
		task.m_radius = 400;
		if (args.length() > 2 && args[2] != "off" && args[2] != "noskills")
			task.m_radius = int(parseInt(args[2]));
		task.m_off = args.find("off") >= 0;
		task.m_skills = args.find("noskills") < 0;
		QueuedTasks::Queue(task);
		Emit(Reply(id, true).Str("tag", task.m_tag).Int("ms", task.m_msLeft));
	}

	// kit <ilvl> <quality> [entry,entry]: gear as a drop would give it. An entry that names a
	// slot (head, chest, hands, feet, back; the default is all five) is
	// Equipment::Generator.GenerateItem(slot, quality, ilvl, ..., record), which picks the base
	// item weighted by the character's attributes (EquipmentGenerator.as GenerateBaseItem); any
	// other entry is a base item id, made as GenerateItem(baseItem) does but at the asked
	// quality (equip's RollQuality only honours a mask with Common in it). Each item rolls its
	// quality's modifiers and is finalised at the middle of its value ranges (intensity 0.5)
	// so two kits differ only in which modifiers they rolled, then equipped as equip does. An
	// item the character may not wear (MayEquip) is rerolled, up to KIT_TRIES times.
	const int KIT_TRIES = 12;

	Equipment::Item@ KitItem(Equipment::Generator@ gen, const string &in entry, Equipment::Slot slot, Item::Quality quality,
		int ilvl, PlayerRecord@ rec)
	{
		Equipment::Item@ item = null;
		if (slot != Equipment::Slot::None)
			@item = cast<Equipment::Item>(gen.GenerateItem(slot, quality, ilvl, null, null, rec));
		else
		{
			auto baseItem = Equipment::BaseItem::Get(entry);
			if (baseItem is null || !gen.VerifyItem(baseItem, quality))
				return null;
			@item = Equipment::Item();
			item.quality = quality;
			@item.baseItem = baseItem;
			gen.GenerateItemMods(item, ilvl, null);
		}
		if (item !is null)
			item.Finalize(0.5f, ilvl, 0, null, null);
		return item;
	}

	void VerbKit(const string &in id, array<string>@ args)
	{
		auto rec = FixtureRecord(id);
		if (rec is null)
			return;
		if (args.length() < 2)
		{
			Fail(id, "usage: kit <ilvl> <quality> [entry,entry]");
			return;
		}
		int ilvl = int(parseInt(args[0]));
		auto quality = Item::ParseQuality(args[1]);
		array<string> names = { "head", "chest", "hands", "feet", "back" };
		array<Equipment::Slot> slots = { Equipment::Slot::Head, Equipment::Slot::Chest, Equipment::Slot::Hands,
			Equipment::Slot::Feet, Equipment::Slot::Back };
		array<string> want = args.length() > 2 ? args[2].split(",") : names;
		Equipment::Generator gen;
		gen.m_ilvl = ilvl;
		array<string> got;
		array<string> failed;
		for (uint i = 0; i < want.length(); i++)
		{
			int k = names.find(want[i]);
			auto slot = k < 0 ? Equipment::Slot::None : slots[k];
			bool done = false;
			for (int t = 0; t < KIT_TRIES && !done; t++)
			{
				auto item = KitItem(gen, want[i], slot, quality, ilvl, rec);
				if (item is null)
				{
					if (k < 0)
						break;
					continue;
				}
				auto unequipped = rec.equipped.Equip(item);
				if (unequipped is item)
					continue;
				done = true;
				Json e;
				e.Str("entry", want[i]).Str("item", item.baseItem.m_id).Int("quality", int(item.quality)).Int("mods", item.mods.length());
				got.insertLast(e.Close());
			}
			if (!done)
				failed.insertLast(want[i]);
		}
		rec.RefreshStats();
		auto plr = cast<PlayerBase>(rec.actor);
		if (plr !is null)
			plr.RefreshModifiers();
		Emit(Reply(id, failed.length() == 0).Int("ilvl", ilvl).Raw("items", RawArray(got)).Raw("failed", StrArray(failed)));
	}

	// benchstats: read-only. What the record's current stats make of the weapons and spells
	// (PlayerRecord.currStats): each hand's damage by type, crit chance and damage, attack
	// speed, spell power, spell crit, the attributes and the mana pool, so a bench can be read
	// against the character it ran with.
	void VerbBenchStats(const string &in id, array<string>@ args)
	{
		auto rec = FixtureRecord(id);
		if (rec is null)
			return;
		auto st = rec.currStats;
		auto mh = st.MainHand;
		auto oh = st.OffHand;
		Json@ j = Reply(id, true);
		j.Str("class", rec.playerClass is null ? "" : rec.playerClass.m_id).Int("level", rec.level)
			.Int("str", int(st.Str)).Int("dex", int(st.Dex)).Int("int", int(st.Int)).Int("foc", int(st.Foc)).Int("vit", int(st.Vit))
			.Int("mana", int(st.Mana)).Num("manaRegen", float(st.ManaRegen)).Int("spellPower", int(st.SpellPower))
			.Int("attackPower", int(st.AttackPower)).Num("damageMul", float(st.DamageMul)).Num("castSpeed", float(st.CastSpeed))
			.Num("spellCrit", float(st.SpellCritChance)).Num("spellCritDmg", float(st.SpellCritDamage))
			.Int("mhPhys", int(mh.DamagePhysical)).Int("mhFire", int(mh.DamageFire)).Int("mhIce", int(mh.DamageIce))
			.Int("mhLight", int(mh.DamageLightning)).Int("mhPoison", int(mh.DamagePoison))
			.Num("mhCrit", float(mh.CritChance)).Num("mhCritDmg", float(mh.CritDamage)).Num("mhSpeed", float(mh.AttackSpeed))
			.Int("ohPhys", int(oh.DamagePhysical)).Num("armorPen", float(st.ArmorPenetration));
		Emit(j);
	}
}

namespace GameLabBench
{
	[Hook]
	void PlayerDamagedActor(Player@ player, Actor@ actor, DamageInfo@ di)
	{
		GameLab::BenchRecord(player, di);
	}
}

namespace Modules
{
	class GameLabBenchModule : Module
	{
		GameLabBenchModule()
		{
			super("gamelab-bench");
			GameLab::RegisterVerb("bench", "<tag> <ms> [radius] [off] [noskills]", GameLab::Verb(GameLab::VerbBench));
			GameLab::RegisterVerb("kit", "<ilvl> <quality> [slot,slot]", GameLab::Verb(GameLab::VerbKit));
			GameLab::RegisterVerb("benchstats", "", GameLab::Verb(GameLab::VerbBenchStats));
		}
	}
}
