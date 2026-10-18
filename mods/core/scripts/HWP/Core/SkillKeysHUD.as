// The skill bar for more than four actives, with the extra keys (SkillKeys.as).
// The vanilla HUDPlayer (GUI/HUD/Components/HUDPlayer.as, gui/hud_components/
// player_info.gui) has bar backgrounds for 2, 3 and 4 skills and drops the
// rest. HWPSkillKeysHUDPlayer replaces it in the HUD (HUDConstructor) and,
// before the vanilla RefreshSkills, widens the 4-skill group in place: one
// more "skill-mid" sprite and skill-slot rect per extra skill, the end cap
// moved right. RefreshSkills then fills every skill-slot it finds. After it,
// each skill on an extra key gets the key name in its (vanilla, unused)
// "binding" text, moved above the slot.
class HWPSkillKeysHUDPlayer : HUDPlayer
{
	Widget@ m_hwpLast;           // the 4-skill group's end cap sprite
	Widget@ m_hwpMidTpl;         // a copy of its middle sprite, before any skill went in
	Widget@ m_hwpSlotTpl;        // a copy of its last skill-slot rect, empty
	float m_hwpLastX;
	float m_hwpSlotX;
	int m_hwpBaseWidth;
	int m_hwpSlots = 4;
	array<Widget@> m_hwpAdded;
	int m_hwpVersion;

	HWPSkillKeysHUDPlayer(GUIBuilder@ b)
	{
		super(b);
		m_hwpVersion = HWP::SkillKeys::g_version;
		auto g = m_wLeftBackground4;
		if (g is null)
			return;
		array<Widget@> sprites;
		Widget@ slot;
		uint slotHash = HashString("skill-slot");
		for (uint i = 0; i < g.m_children.length(); i++)
		{
			auto c = g.m_children[i];
			if (cast<SpriteWidget>(c) !is null)
				sprites.insertLast(c);
			else if (c.m_idHash == slotHash)
				@slot = c;
		}
		if (sprites.length() < 3 || slot is null)
		{
			HWP::LogError("skillkeys", "player_info.gui skill4 group not as expected; no extra HUD slots");
			return;
		}
		@m_hwpLast = sprites[sprites.length() - 1];
		@m_hwpMidTpl = sprites[1].Clone();
		@m_hwpSlotTpl = slot.Clone();
		m_hwpLastX = m_hwpLast.m_offset.x;
		m_hwpSlotX = slot.m_offset.x;
		m_hwpBaseWidth = g.m_width;
	}

	// the slots' spacing in player_info.gui (3, 34, 65, 96)
	int Step() { return 31; }

	void SetSlots(int n)
	{
		auto g = m_wLeftBackground4;
		if (g is null || m_hwpLast is null)
			return;
		n = max(4, min(4 + HWP::SkillKeys::COUNT, n));
		if (n == m_hwpSlots)
			return;
		for (uint i = 0; i < m_hwpAdded.length(); i++)
			m_hwpAdded[i].RemoveFromParent();
		m_hwpAdded.resize(0);
		for (int j = 0; j < n - 4; j++)
		{
			auto mid = m_hwpMidTpl.Clone();
			mid.m_offset = vec2(m_hwpLastX + Step() * j, m_hwpMidTpl.m_offset.y);
			// under the slots (they come after the sprites), before the end cap
			g.AddChild(mid, g.m_children.findByRef(m_hwpLast));
			m_hwpAdded.insertLast(mid);

			auto slot = m_hwpSlotTpl.Clone();
			slot.m_offset = vec2(m_hwpSlotX + Step() * (j + 1), m_hwpSlotTpl.m_offset.y);
			g.AddChild(slot);
			m_hwpAdded.insertLast(slot);
		}
		m_hwpLast.m_offset = vec2(m_hwpLastX + Step() * (n - 4), m_hwpLast.m_offset.y);
		g.m_width = m_hwpBaseWidth + Step() * (n - 4);
		m_hwpSlots = n;
	}

	array<Skills::Skill@>@ PlayerSkills(PlayerRecord@ record)
	{
		array<Skills::Skill@>@ skills;
		auto player = cast<PlayerBase>(record.actor);
		if (player !is null)
			@skills = player.m_skills;
		else
			@skills = PlayerHelper::GetDeadSkillList(record);
		return skills;
	}

	// the skills the vanilla bar shows, in its order
	array<Skills::Skill@>@ BarSkills(array<Skills::Skill@>@ all)
	{
		array<Skills::Skill@> ret;
		for (uint i = 0; all !is null && i < all.length(); i++)
		{
			auto s = all[i];
			if (s is null || s.GetTargetingMode() == Skills::TargetingMode::Passive)
				continue;
			if (s.m_type == PlayerSkillType::MainHand || s.m_type == PlayerSkillType::OffHand || s.m_type == PlayerSkillType::Dash)
				continue;
			ret.insertLast(s);
		}
		return ret;
	}

	void RefreshSkills(PlayerRecord@ record) override
	{
		if (record is null)
		{
			HUDPlayer::RefreshSkills(record);
			return;
		}
		auto all = PlayerSkills(record);
		auto bar = BarSkills(all);
		SetSlots(int(bar.length()));
		HUDPlayer::RefreshSkills(record);

		for (uint i = 0; i < m_skillSlots.length() && i < bar.length(); i++)
		{
			int k = HWP::SkillKeys::Extra(all, bar[i]);
			if (k < 0 || m_skillSlots[i].m_children.length() == 0)
				continue;
			auto binding = cast<TextWidget>(m_skillSlots[i].m_children[0].GetWidgetById("binding"));
			if (binding is null)
				continue;
			binding.m_offset = vec2(1, -29);
			binding.SetText(HWP::SkillKeys::KeyName(k));
		}
		Invalidate();
	}

	void Update(int dt, PlayerRecord@ record) override
	{
		if (m_hwpVersion != HWP::SkillKeys::g_version && record !is null && record.equipped !is null)
		{
			m_hwpVersion = HWP::SkillKeys::g_version;
			RefreshSkills(record);
		}
		HUDPlayer::Update(dt, record);
	}
}

namespace HWPSkillKeys
{
	[Hook]
	void HUDConstructor(HUD@ hud, GUIBuilder@ b)
	{
		for (uint i = 0; i < hud.m_components.length(); i++)
		{
			if (cast<HUDPlayer>(hud.m_components[i]) is null || cast<HWPSkillKeysHUDPlayer>(hud.m_components[i]) !is null)
				continue;
			@hud.m_components[i] = HWPSkillKeysHUDPlayer(b);
			return;
		}
	}
}
