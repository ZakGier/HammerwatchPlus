// Engineer: Deploy Turret (engineer_turret.sval) and My Turret! (engineer_myturret.sval).
// - HWPFirearmsTurret: the turret (units/turret.unit), the game's PlayerOwnedActor with the
//   Heavy Ballista's look. Its HP, fire rate and Reinforced Turret share come from the
//   skill's binds (a summon's binds resolve through its owner, PlayerOwnedActor.FetchData).
//   It loses a full health bar over decay ms. Second Turret is the game's summon cap
//   (Modifiers::ModifySummons; Player.Update destroys the oldest above it).
// - My Turret!: while its owner stands within NEAR of it (any player, with Our Turret!) it
//   gains hwp-turret-repair HP a second, deals hwp-turret-dmg more damage and glows
//   (turret_glow). Elemental Belt-Feed (hwp-turret-feed) is then its elemental chance; the
//   element weights and riders are the owner's Elemental Bullets orbs (Elemental.as).
namespace HWP
{
	namespace Firearms
	{
		const int NEAR = 160;
	}
}

class HWPFirearmsTurret : PlayerOwnedActor
{
	float m_hpPct;
	int m_decay;
	float m_boost;
	float m_feed;
	int m_glowC;
	string m_booster;

	HWPFirearmsTurret(UnitPtr unit, SValue& params)
	{
		super(unit, params);
	}

	void Initialize(Actor@ owner, float intensity, bool husk, uint weaponInfo = 0) override
	{
		PlayerOwnedActor::Initialize(owner, intensity, husk, weaponInfo);
		m_hpPct = GetParamFloat(m_unit, m_params, "hp-pct", false, 0);
		m_decay = max(1, GetParamInt(m_unit, m_params, "decay", false, 30000));
		int rate = 0;
		if (m_skills.length() > 0)
		{
			auto skill = cast<CompositeActorSkill>(m_skills[0]);
			if (skill !is null)
				rate = skill.m_cooldown.x;
		}
		HWP::Log("firearms", "turret: placed, " + GetMaxHp() + " hp (+" + int(m_hpPct * 100)
			+ "% of the owner's), a shot every " + rate + " ms, " + m_decay + " ms to decay");
	}

	PlayerBase@ OwnerPlayer() { return cast<PlayerBase>(GetOwner()); }

	int GetMaxHp() override
	{
		int hp = PlayerOwnedActor::GetMaxHp();
		auto plr = OwnerPlayer();
		if (plr !is null && m_hpPct > 0)
			hp += int(m_hpPct * plr.GetMaxHp());
		return max(1, hp);
	}

	// the player whose presence boosts the turret, or "" for none
	string FindBooster(PlayerBase@ owner)
	{
		bool shared = HWP::Firearms::CustomStat(owner, "hwp-turret-shared") > 0;
		int nearSq = HWP::Firearms::NEAR * HWP::Firearms::NEAR;
		if (!owner.IsDead() && distsq(owner.m_unit, m_unit) <= nearSq)
			return owner.m_record.GetName();
		if (!shared)
			return "";
		for (uint i = 0; i < g_players.length(); i++)
		{
			auto rec = g_players[i];
			if (rec.peer == 255 || rec.actor is null || rec.IsDead() || rec.actor is owner)
				continue;
			if (distsq(rec.actor.m_unit, m_unit) <= nearSq)
				return rec.GetName();
		}
		return "";
	}

	void Update(int dt) override
	{
		PlayerOwnedActor::Update(dt);
		if (IsDead() || m_unit.IsDestroyed())
			return;
		auto owner = OwnerPlayer();
		if (owner is null)
			return;

		float repair = HWP::Firearms::CustomStat(owner, "hwp-turret-repair");
		string booster = repair > 0 ? FindBooster(owner) : "";
		if (booster != m_booster)
		{
			HWP::Log("firearms", booster == "" ? "turret: unboosted"
				: "turret: boosted by " + booster + ", +" + int(repair) + " hp/s, +"
				+ int(HWP::Firearms::CustomStat(owner, "hwp-turret-dmg") * 100 + 0.5f) + "% damage, "
				+ int(HWP::Firearms::CustomStat(owner, "hwp-turret-feed") * 100 + 0.5f) + "% elemental");
			m_booster = booster;
		}

		float hp = m_hp - dt / float(m_decay);
		if (booster != "")
		{
			hp += repair * dt / 1000.0f / GetMaxHp();
			m_boost = HWP::Firearms::CustomStat(owner, "hwp-turret-dmg");
			m_feed = HWP::Firearms::CustomStat(owner, "hwp-turret-feed");
			m_glowC -= dt;
			if (m_glowC <= 0)
			{
				m_glowC = 200;
				auto glow = LoadActorBuff(HWP::Firearms::BUFFS + "turret_glow");
				if (glow !is null)
					ApplyBuff(ActorBuff(owner, glow, 1.0f, false));
			}
		}
		else
		{
			m_boost = 0;
			m_feed = 0;
		}
		m_hp = min(1.0f, hp);
		if (m_hp <= 0)
		{
			HWP::Log("firearms", "turret: decayed");
			OnDeath(DamageInfo(), vec2(1, 0));
		}
	}

	DamageInfo DamageActor(Actor@ actor, DamageInfo di) override
	{
		if (m_boost > 0)
		{
			float mul = 1 + m_boost;
			di.PhysicalDamage = damage_round(di.PhysicalDamage * mul);
			di.FireDamage = damage_round(di.FireDamage * mul);
			di.IceDamage = damage_round(di.IceDamage * mul);
			di.LightningDamage = damage_round(di.LightningDamage * mul);
			di.PoisonDamage = damage_round(di.PoisonDamage * mul);
			di.PureDamage = damage_round(di.PureDamage * mul);
		}
		return PlayerOwnedActor::DamageActor(actor, di);
	}
}
