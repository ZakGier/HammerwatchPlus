// Double Barrel Burst's shell (assault_burst.sval): every enemy in the cone in front of the
// player, out to the radius, takes the shell's effects once, as an explosion with no falloff
// would. Within close-range the hit's intensity is close-mul (the level's close-range bonus).
// Cover blocks a hit as it blocks an explosion (Explode.as raycast). With ground-ttl above 0
// (Dragon's Breath) the ground-effects run at points spread over the cone: the burning ground.
class HWPFirearmsShotgun : Explode
{
	float m_arcCos;
	float m_arc;
	int m_closeRange;
	float m_closeMul;
	int m_groundTtl;
	EffectList@ m_groundEffects;

	HWPFirearmsShotgun(UnitPtr unit, SValue& params)
	{
		super(unit, params);
		m_arc = GetParamInt(unit, params, "arc", false, 50) * PI / 180.0f;
		m_arcCos = cos(m_arc / 2);
		m_closeRange = GetParamInt(unit, params, "close-range", false, 0);
		m_closeMul = GetParamFloat(unit, params, "close-mul", false, 1);
		m_groundTtl = GetParamInt(unit, params, "ground-ttl", false, 0);
		@m_groundEffects = LoadEffects(unit, params, "ground-");
	}

	// the burning ground is spawned by the skill, so it reads the skill's binds
	void SetWeaponInformation(uint weapon) override
	{
		Explode::SetWeaponInformation(weapon);
		PropagateWeaponInformation(m_groundEffects, weapon);
	}

	bool DoExplosion(Actor@ owner, vec2 pos, vec2 dir, float intensity, bool husk) override
	{
		if (m_fx != "")
		{
			dictionary ePs = { { 'radius', m_radius }, { 'angle', atan(dir.y, dir.x) } };
			PlayEffect(m_fx, pos, ePs);
		}

		uint ownerTeam = owner !is null ? owner.Team : 0;
		int hit = 0;
		int close = 0;
		auto results = g_scene.QueryCircle(pos, m_radius, ~0, RaycastType::Shot, true);
		for (uint i = 0; i < results.length(); i++)
		{
			UnitPtr unit = results[i];
			if (owner !is null && unit == owner.m_unit)
				continue;
			Actor@ taker = cast<Actor>(unit.GetScriptBehavior());
			if (taker is null || taker.Team == ownerTeam)
				continue;

			vec2 upos = xy(unit.GetPosition());
			float dist = length(upos - pos);
			if (dist > 0.5f && dot(dir, (upos - pos) / dist) < m_arcCos)
				continue;

			bool visible = true;
			auto rays = g_scene.Raycast(pos, upos, ~0, RaycastType::Shot);
			for (uint j = 0; j < rays.length(); j++)
			{
				UnitPtr ru = rays[j].FetchUnit(g_scene);
				if (ru == unit)
				{
					upos = rays[j].point;
					break;
				}
				auto d = cast<IDamageTaker>(ru.GetScriptBehavior());
				if (d is null || d.Impenetrable())
				{
					visible = false;
					break;
				}
			}
			if (!visible)
				continue;

			bool near = dist <= m_closeRange;
			hit++;
			if (near)
				close++;
			ApplyEffects(m_effectList, owner, unit, upos, dir, intensity * (near ? m_closeMul : 1.0f), husk);
		}

		if (m_groundTtl > 0)
		{
			// six patches: one near, two in the middle, three at the far edge of the cone
			array<vec2> spots = { vec2(0.3f, 0), vec2(0.6f, -0.28f), vec2(0.6f, 0.28f),
				vec2(0.88f, -0.4f), vec2(0.88f, 0), vec2(0.88f, 0.4f) };
			float ang = atan(dir.y, dir.x);
			for (uint i = 0; i < spots.length(); i++)
			{
				float a = ang + spots[i].y * m_arc / 2 / 0.4f;
				vec2 at = pos + vec2(cos(a), sin(a)) * (m_radius * spots[i].x);
				ApplyEffects(m_groundEffects, owner, UnitPtr(), at, dir, intensity, husk);
			}
		}

		if (!husk)
			HWP::Log("firearms", "shotgun: " + hit + " hit, " + close + " within " + m_closeRange
				+ " at x" + m_closeMul + (m_groundTtl > 0 ? ", burning ground " + m_groundTtl + " ms" : ""));
		return true;
	}
}
