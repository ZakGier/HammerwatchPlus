namespace Projectile
{
	// The rifle's grenade launcher shell (rifle_gl_shell.unit) arms after arm-dist px of flight,
	// as a real 40 mm round does. Until then an enemy it hits takes its slug-effects (half the
	// blast's damage and a short stun) and nothing explodes. A wall sets it off armed or not:
	// walls take the collide effects (NewProjectile.OnHit), which stay the blast.
	class HWPFirearmsArm : ProjectileModifier
	{
		NewProjectile@ m_proj;
		EffectList@ m_slug;
		EffectList@ m_blast;
		float m_armDistSq;
		bool m_armed;

		HWPFirearmsArm(UnitPtr unit, SValue& params)
		{
			@m_slug = LoadEffects(unit, params, "slug-");
			float d = GetParamFloat(unit, params, "arm-dist", false, 40);
			m_armDistSq = d * d;
		}

		void Initialize(NewProjectile@ behavior, SValue& params, Actor@ owner, ProjectileTarget@ target, uint weapon) override
		{
			@m_proj = behavior;
			PropagateWeaponInformation(m_slug, weapon);
			@m_blast = behavior.m_hitEffects;
			@behavior.m_hitEffects = m_slug;
			m_armed = false;
		}

		// after the move's hits (NewProjectile.Update raycasts first), so a hit on the frame
		// that crosses arm-dist is still the slug
		void Update(int dt, vec2 from, vec2 to) override
		{
			if (m_armed)
				return;
			vec2 d = to - m_proj.m_startPos;
			if (dot(d, d) < m_armDistSq)
				return;
			m_armed = true;
			@m_proj.m_hitEffects = m_blast;
		}
	}
}
