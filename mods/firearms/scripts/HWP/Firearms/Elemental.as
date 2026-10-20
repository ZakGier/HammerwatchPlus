// Elemental Bullets (fs_scavenger.sval) and Extended Clip Crit (fs_steady.sval).
// - HWPFirearmsGunShot: the guns' ShootProjectile. Each shot rolls hwp-ele-chance (a custom
//   stat: the passive's level) to be elemental; the element is picked by weight, 1 each plus
//   the bullet-type orb's hwp-ele-<element>. An elemental shot fires that element's round
//   (round_<gun>_<element>.unit). The roll goes to the other clients with the shot.
//   A turret's shot (Turret.as) rolls its Elemental Belt-Feed chance instead, with its
//   owner's weights.
// - HWPFirearmsElementalDamage: the weapon damage, all as the round's element, without the
//   armor penetration of a plain round.
// - HWPFirearmsBulletRider: the orbs riding on elemental rounds: poison blinds (hwp-ele-blind),
//   ice slows (hwp-ele-slow), lightning stuns for hwp-ele-stun ms. Each hit adds its time to
//   what is left, up to RIDER_CAP.
// - Modifiers::HWPFirearmsExtendedClip: pct more rounds in each gun's magazine.
namespace HWP
{
	namespace Firearms
	{
		const array<string> ELEMENTS = { "fire", "ice", "lightning", "poison" };
		const int RIDER_CAP = 3000;

		float CustomStat(PlayerBase@ plr, const string &in name)
		{
			if (plr is null || plr.m_record is null)
				return 0;
			auto stats = plr.m_record.currStats.m_customStats;
			for (uint i = 0; i < stats.length(); i++)
			{
				if (stats[i].id == name && stats[i].svalue !is null)
					return stats[i].svalue.GetFloat();
			}
			return 0;
		}

		// -1 for a plain round, else an index into ELEMENTS
		int RollElement(PlayerBase@ plr, float chance)
		{
			if (plr is null || chance <= 0 || randf() >= chance)
				return -1;
			array<float> weights;
			float total = 0;
			for (uint i = 0; i < ELEMENTS.length(); i++)
			{
				weights.insertLast(1 + CustomStat(plr, "hwp-ele-" + ELEMENTS[i]));
				total += weights[i];
			}
			float r = randf() * total;
			for (uint i = 0; i < weights.length(); i++)
			{
				r -= weights[i];
				if (r < 0)
					return i;
			}
			return ELEMENTS.length() - 1;
		}

		// adds dur to what is left of buff on the actor, up to RIDER_CAP
		void ApplyStacking(Actor@ owner, Actor@ actor, const string &in buff, int dur)
		{
			auto def = LoadActorBuff(BUFFS + buff);
			auto list = actor.GetBuffList();
			if (def is null || list is null || dur <= 0)
				return;
			int left = 0;
			for (uint i = 0; i < list.m_buffs.length(); i++)
			{
				if (list.m_buffs[i].m_def is def)
					left = max(left, list.m_buffs[i].m_duration);
			}
			actor.ApplyBuff(ActorBuff(owner, def, 1.0f, false, 0, min(RIDER_CAP, left + dur)));
		}
	}
}

// where the last gun round of the local player started, in the aim's frame: x ahead of the
// player's position, y to the aim's right ("hwp firearms muzzle")
namespace HWP { namespace Firearms { vec2 g_lastMuzzle; float g_lastRange; } }
// g_lastRange: how far the local player's last gun round flew before it ran out
// g_shotTimes: when (g_scene.GetTime) the local player's last SHOT_TIMES gun rounds started
// ("hwp firearms shots")
namespace HWP { namespace Firearms { const uint SHOT_TIMES = 16; array<int> g_shotTimes; } }
// g_eleRolls: the local player's gun shots by roll, plain first then ELEMENTS ("hwp firearms
// elements"; "elements reset" zeroes it)
namespace HWP { namespace Firearms { array<int> g_eleRolls = { 0, 0, 0, 0, 0 }; } }

class HWPFirearmsGunShot : ShootProjectile
{
	UnitProducer@ m_plain;
	array<UnitProducer@> m_rounds;
	Actor@ m_shooter;
	vec2 m_aim;

	HWPFirearmsGunShot(UnitPtr unit, SValue& params)
	{
		super(unit, params);
		@m_plain = m_projectile;
		m_converge = GetParamInt(unit, params, "converge", false, 0);
		for (uint i = 0; i < HWP::Firearms::ELEMENTS.length(); i++)
		{
			string path = GetParamString(unit, params, HWP::Firearms::ELEMENTS[i], false, "");
			m_rounds.insertLast(path == "" ? null : Resources::GetUnitProducer(path));
		}
	}

	// "converge" (px): a round leaving a gun held off the aim line (rotate-offset) is angled to
	// cross the line that far out, instead of flying parallel to it 6 px aside. Parallel rounds
	// grazed past small targets: a lone pistol hit a target dummy (radius 4) with 8 of ~26
	// rounds (probe-pistol 20261020-002514).
	int m_converge;

	vec2 GetShootDir(vec2 dir, int i, bool allowRandom) override
	{
		vec2 d = ShootProjectile::GetShootDir(dir, i, allowRandom);
		if (m_converge <= 0 || !m_rotateOffset || m_offset.y == 0)
			return d;
		float ang = atan(d.y, d.x) - atan(m_offset.y, float(m_converge));
		return vec2(cos(ang), sin(ang));
	}

	void Pick(int e)
	{
		@m_projectile = (e >= 0 && e < int(m_rounds.length()) && m_rounds[e] !is null) ? m_rounds[e] : m_plain;
	}

	bool DoAction(SValueBuilder@ builder, Actor@ owner, Actor@ target, vec2 pos, vec2 dir, float intensity) override
	{
		int e;
		auto turret = cast<HWPFirearmsTurret>(owner);
		if (turret !is null)
			e = HWP::Firearms::RollElement(turret.OwnerPlayer(), turret.m_feed);
		else
		{
			auto plr = cast<PlayerBase>(owner);
			e = HWP::Firearms::RollElement(plr, HWP::Firearms::CustomStat(plr, "hwp-ele-chance"));
			if (plr !is null && plr is cast<PlayerBase>(GetLocalPlayer()))
				HWP::Firearms::g_eleRolls[e + 1]++;
		}
		builder.PushArray();
		builder.PushInteger(e);
		Pick(e);
		@m_shooter = owner;
		m_aim = normalize(dir);
		bool shot = ShootProjectile::DoAction(builder, owner, target, pos, dir, intensity);
		@m_shooter = null;
		Pick(-1);
		builder.PopArray();
		return shot;
	}

	UnitPtr ProduceProjectile(vec2 shootPos, int id = 0) override
	{
		if (m_shooter !is null && cast<Player>(m_shooter) !is null)
		{
			vec2 d = shootPos - xy(m_shooter.m_unit.GetPosition());
			HWP::Firearms::g_lastMuzzle = vec2(dot(d, m_aim), dot(d, vec2(-m_aim.y, m_aim.x)));
			HWP::Firearms::g_shotTimes.insertLast(g_scene.GetTime());
			if (HWP::Firearms::g_shotTimes.length() > HWP::Firearms::SHOT_TIMES)
				HWP::Firearms::g_shotTimes.removeAt(0);
		}
		return ShootProjectile::ProduceProjectile(shootPos, id);
	}

	bool NetDoAction(SValue@ param, Actor@ owner, vec2 pos, vec2 dir) override
	{
		auto arr = param.GetArray();
		if (arr is null || arr.length() < 2)
			return true;
		Pick(arr[0].GetInteger());
		bool ret = ShootProjectile::NetDoAction(arr[1], owner, pos, dir);
		Pick(-1);
		return ret;
	}
}

class HWPFirearmsElementalDamage : PlayerDamage
{
	int m_element;

	HWPFirearmsElementalDamage(UnitPtr unit, SValue& params)
	{
		super(unit, params);
		m_element = HWP::Firearms::ELEMENTS.find(GetParamString(unit, params, "element", true));
	}

	void FillDamage(Actor@ owner, IDamageTaker@ target, DamageInfo@ di, float intensity) override
	{
		uint p = di.PhysicalDamage;
		uint f = di.FireDamage;
		uint i = di.IceDamage;
		uint l = di.LightningDamage;
		uint o = di.PoisonDamage;
		PlayerDamage::FillDamage(owner, target, di, intensity);
		uint add = (di.PhysicalDamage - p) + (di.FireDamage - f) + (di.IceDamage - i)
			+ (di.LightningDamage - l) + (di.PoisonDamage - o);
		di.PhysicalDamage = p;
		di.FireDamage = f + (m_element == 0 ? add : 0);
		di.IceDamage = i + (m_element == 1 ? add : 0);
		di.LightningDamage = l + (m_element == 2 ? add : 0);
		di.PoisonDamage = o + (m_element == 3 ? add : 0);
	}
}

class HWPFirearmsBulletRider : IEffect
{
	int m_element;

	HWPFirearmsBulletRider(UnitPtr unit, SValue& params)
	{
		m_element = HWP::Firearms::ELEMENTS.find(GetParamString(unit, params, "element", true));
	}

	CanEvade IsEvadable(Actor@ attacker) { return CanEvade::Neither; }
	void SetWeaponInformation(uint weapon) {}

	bool CanApply(Actor@ owner, UnitPtr target, vec2 pos, vec2 dir, float intensity) override
	{
		return target.IsValid() && cast<Actor>(target.GetScriptBehavior()) !is null;
	}

	bool Apply(Actor@ owner, UnitPtr target, vec2 pos, vec2 dir, float intensity, bool husk)
	{
		auto plr = GetPlayerOwner(owner);
		auto actor = cast<Actor>(target.GetScriptBehavior());
		if (husk || plr is null || actor is null || actor.IsDead())
			return false;
		if (m_element == 3 && HWP::Firearms::CustomStat(plr, "hwp-ele-blind") > 0)
			HWP::Firearms::ApplyStacking(owner, actor, "ele_blind", 1000);
		else if (m_element == 1 && HWP::Firearms::CustomStat(plr, "hwp-ele-slow") > 0)
			HWP::Firearms::ApplyStacking(owner, actor, "ele_slow", 1000);
		else if (m_element == 2)
			HWP::Firearms::ApplyStacking(owner, actor, "ele_stun", int(HWP::Firearms::CustomStat(plr, "hwp-ele-stun")));
		return true;
	}
}

namespace Modifiers
{
	// Extended Clip Crit: each gun worn (its marker, buffs_firearms.sval) holds pct more rounds,
	// rounded, so dual pistols gain per pistol. A gun's magazine is its marker's add-max on
	// the clip (GunMarker), read once.
	class HWPFirearmsExtendedClip : Modifier
	{
		vec2 m_pct;
		array<string> m_markers = { "rifle", "glock_main", "glock_off" };
		array<int> m_mags;
		array<uint> m_hashes;

		HWPFirearmsExtendedClip(UnitPtr unit, SValue& params)
		{
			m_pct = GetParamVec2(unit, params, "pct", true, 0);
		}

		int MarkerMag(const string &in name)
		{
			auto def = LoadActorBuff(HWP::Firearms::BUFFS + name);
			if (def is null)
				return 0;
			for (uint i = 0; i < def.m_modifiers.length(); i++)
			{
				auto mod = cast<ModifyStack>(def.m_modifiers[i]);
				if (mod !is null && mod.m_buffName == HWP::Firearms::CLIP)
					return mod.m_addMaxStacks.x;
			}
			HWP::LogError("firearms", "extended clip: marker " + name + " carries no magazine");
			return 0;
		}

		ModDynamism HasModifyStacks() override { return ModDynamism::Dynamic; }
		void ModifyStacks(PlayerBase@ player, float intensity) override
		{
			auto def = ActorBuffStackDef::Get(HWP::Firearms::CLIP);
			if (def is null)
				return;
			if (m_mags.length() == 0)
			{
				for (uint i = 0; i < m_markers.length(); i++)
				{
					m_mags.insertLast(MarkerMag(m_markers[i]));
					m_hashes.insertLast(HashString(HWP::Firearms::BUFFS + m_markers[i]));
				}
			}
			float pct = lerp(m_pct, intensity);
			int add = 0;
			for (uint i = 0; i < m_markers.length(); i++)
			{
				if (player.HasBuff(m_hashes[i]))
					add += int(m_mags[i] * pct + 0.5f);
			}
			player.m_record.GetModifiedStack(def, true).m_maxStacks += add;
		}
	}
}
