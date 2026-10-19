// Ordinance Hoarder on the skill bar: while the Frag Grenade, the Grenade Launcher or the
// Rocket Launcher sits ready and banks its next charge (HoardedSkill.m_progress), the slot's
// cooldown ring shows the banking, and the icon stays bright. The slot itself can't: a
// cooldown dims its icon (SkillWidget.as:333) and a ready skill draws the whole ring (:362).
// So this component, drawn after HUDPlayer, darkens the part of that ring not banked yet,
// with the colour SkillWidget darkens an icon on cooldown with (:342).
class HWPFirearmsChargeHUD : HUDComponent
{
	HUD@ m_hud;
	bool m_logged = false;

	HWPFirearmsChargeHUD(GUIBuilder@ b)
	{
		super(b, "");
	}

	void DoLayout() override {}

	HUDPlayer@ Player()
	{
		for (uint i = 0; m_hud !is null && i < m_hud.m_components.length(); i++)
		{
			auto p = cast<HUDPlayer>(m_hud.m_components[i]);
			if (p !is null)
				return p;
		}
		return null;
	}

	float Progress(SkillWidget@ w)
	{
		uint id = 0;
		if (w.m_skill !is null)
			id = w.m_skill.m_skillId;
		else if (w.m_plrSkill !is null)
			id = w.m_plrSkill.m_skillId;
		else
			return -1;
		for (uint i = 0; i < HWP::Firearms::g_hoarded.length(); i++)
		{
			auto h = HWP::Firearms::g_hoarded[i];
			if (h.m_skillId == id)
				return h.m_progress;
		}
		return -1;
	}

	void DrawSlot(SpriteBatch& sb, Widget@ slot)
	{
		if (slot is null)
			return;
		for (uint i = 0; i < slot.m_children.length(); i++)
		{
			auto w = cast<SkillWidget>(slot.m_children[i]);
			if (w is null || !w.m_visible || w.m_frameCooldown is null)
				continue;
			float p = Progress(w);
			if (p < 0)
				continue;
			// the banked part [0, p] stays lit, filling from where a cooldown's ring fills (:360)
			sb.DrawSpriteRadial(w.m_origin, w.m_frameCooldown, g_menuTime, p, 1.0f, vec4(0.1, 0.1, 0.1, 1));
			if (!m_logged)
			{
				m_logged = true;
				HWP::Log("firearms", "hoarder: slot ring shows a charge banking, " + int(p * 100) + "%");
			}
		}
	}

	void Draw(SpriteBatch& sb, int idt) override
	{
		auto hp = Player();
		if (hp is null || !hp.IsVisible() || !GetVarBool("ui_hud_visible"))
			return;
		mat4 tform;
		tform *= g_gameMode.m_wndInvScaleTransform;
		tform *= mat::scale(mat4(), hp.m_scale * g_gameMode.m_wndScale);
		tform *= mat::translate(mat4(), vec3(hp.m_offset.x, hp.m_offset.y, 0.0f));
		sb.PushTransformation(tform);
		for (uint i = 0; i < hp.m_skillSlots.length(); i++)
			DrawSlot(sb, hp.m_skillSlots[i]);
		DrawSlot(sb, hp.m_wMainHandSkillSlot);
		DrawSlot(sb, hp.m_wOffHandSkillSlot);
		sb.PopTransformation();
	}
}

namespace HWPFirearmsHUD
{
	[Hook]
	void HUDConstructor(HUD@ hud, GUIBuilder@ b)
	{
		auto comp = HWPFirearmsChargeHUD(b);
		@comp.m_hud = hud;
		hud.m_components.insertLast(comp);
	}
}
