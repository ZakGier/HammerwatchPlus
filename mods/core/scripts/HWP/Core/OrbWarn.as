// What an orb pick closes off. Some orbs are mutually exclusive (a mod skill's
// "blocked-by-skills": the Firearms grenade types, the RPG's warheads, vanilla
// ones too); once you own one, the others never show up again (the
// GiveSkillSphereMenu's FillPossibleSkills skips a def with an owned blocker).
// The vanilla picker never says so. Each frame the open picker (any
// GiveSkillSphereMenu, gui/skill_spheres.gui) is checked; under each pick's
// description box (its rect leaves 20 px under the 88 px desc) a row in red:
// "Makes unavailable:" and every orb it would close, icon and name (icons
// only when the names don't fit). No window hook; the vanilla window is kept.
namespace HWP
{
	namespace OrbWarn
	{
		const string ROW_ID = "hwp-orb-warn";

		GiveSkillSphereMenu@ g_window;
		array<PlayerSkillDef@> g_shown = { null, null, null };

		GiveSkillSphereMenu@ OpenPicker()
		{
			auto gm = cast<BaseGameMode>(g_gameMode);
			if (gm is null || gm.m_windowManager is null)
				return null;
			for (int i = int(gm.m_windowManager.m_objects.length()) - 1; i >= 0; i--)
			{
				auto w = cast<GiveSkillSphereMenu>(gm.m_windowManager.m_objects[i]);
				if (w !is null)
					return w;
			}
			return null;
		}

		void AllDefs(PlayerSkillDef@ def, array<PlayerSkillDef@>@ all)
		{
			if (def is null || all.findByRef(def) >= 0)
				return;
			all.insertLast(def);
			for (uint i = 0; i < def.m_modSkills.length(); i++)
				AllDefs(def.m_modSkills[i], all);
		}

		// the orbs picking `pick` would close: not owned yet, and blocked by it (either
		// side lists the other; the vanilla data lists both)
		array<PlayerSkillDef@>@ Closes(PlayerRecord@ ply, PlayerSkillDef@ pick)
		{
			array<PlayerSkillDef@> closes;
			if (ply is null || ply.playerClass is null || pick is null || ply.GetSkillLevel(pick) > 0)
				return closes;
			array<PlayerSkillDef@> all;
			for (uint i = 0; i < ply.playerClass.m_skillDefs.length(); i++)
				AllDefs(ply.playerClass.m_skillDefs[i], all);
			if (ply.librarySkill !is null)
				AllDefs(ply.librarySkill.m_plrSkill, all);
			for (uint i = 0; i < all.length(); i++)
			{
				auto d = all[i];
				if (d is pick || ply.GetSkillLevel(d) > 0)
					continue;
				if (d.m_blockerSkills.find(pick.m_id) >= 0 || pick.m_blockerSkills.find(d.m_id) >= 0)
					closes.insertLast(d);
			}
			return closes;
		}

		HWPOrbWarnWidget@ Row(Widget@ perk)
		{
			auto row = cast<HWPOrbWarnWidget>(perk.GetWidgetById(ROW_ID));
			if (row !is null)
				return row;
			auto desc = perk.GetWidgetById("desc");
			if (desc is null || desc.m_parent is null)
				return null;
			@row = HWPOrbWarnWidget();
			row.SetID(ROW_ID);
			row.m_width = desc.m_width;
			row.m_height = 18;
			// under the desc text, inside its box
			row.m_offset = vec2(desc.m_offset.x, desc.m_offset.y + desc.m_height + 1);
			desc.m_parent.AddChild(row);
			return row;
		}

		void Update()
		{
			auto w = OpenPicker();
			if (w is null)
			{
				@g_window = null;
				return;
			}
			if (w !is g_window)
			{
				@g_window = w;
				for (uint i = 0; i < g_shown.length(); i++)
					@g_shown[i] = null;
			}
			array<PlayerSkillDef@> picks = { w.m_skill1, w.m_skill2, w.m_skill3 };
			for (uint i = 0; i < picks.length(); i++)
			{
				auto perk = w.m_widget.GetWidgetById("perk" + (i + 1));
				if (perk is null)
					continue;
				auto row = Row(perk);
				if (row is null)
					continue;
				// a reroll changes the picks
				if (picks[i] is g_shown[i] && row.m_ready)
					continue;
				@g_shown[i] = picks[i];
				row.Set(Closes(GetLocalPlayerRecord(), picks[i]));
				if (picks[i] !is null)
					HWP::Log("orbwarn", "pick " + (i + 1) + " (" + picks[i].m_id + ") makes unavailable "
						+ (row.m_orbs.length() > 0 ? row.Names() : "nothing"));
			}
		}
	}
}

class HWPOrbWarnWidget : Widget
{
	array<PlayerSkillDef@> m_orbs;
	BitmapString@ m_label;
	array<BitmapString@> m_names;
	bool m_withNames = true;
	bool m_ready = false;

	HWPOrbWarnWidget()
	{
		super();
	}

	string Names()
	{
		string s;
		for (uint i = 0; i < m_orbs.length(); i++)
			s += (i > 0 ? ", " : "") + m_orbs[i].m_id;
		return s;
	}

	void Set(array<PlayerSkillDef@>@ orbs)
	{
		m_ready = true;
		m_orbs = orbs;
		m_names.resize(0);
		m_visible = orbs.length() > 0;
		if (!m_visible)
			return;
		auto font = Resources::GetBitmapFont("gui/fonts/arial11.fnt");
		vec4 red = vec4(1.0f, 0.3f, 0.25f, 1.0f);
		@m_label = font.BuildText(Resources::GetString(".hwp.orbwarn.closes"), -1, TextAlignment::Left, red);
		int w = m_label.GetWidth();
		for (uint i = 0; i < orbs.length(); i++)
		{
			auto name = font.BuildText(Resources::GetString(orbs[i].m_name), -1, TextAlignment::Left, red);
			m_names.insertLast(name);
			w += 4 + 16 + 2 + name.GetWidth();
		}
		m_withNames = w <= m_width;
	}

	void DoDraw(SpriteBatch& sb, vec2 pos) override
	{
		if (m_label is null || m_orbs.length() == 0)
			return;
		int ty = int(pos.y + (m_height - m_label.GetHeight()) / 2);
		sb.DrawString(vec2(int(pos.x), ty), m_label);
		float x = pos.x + m_label.GetWidth();
		for (uint i = 0; i < m_orbs.length(); i++)
		{
			x += 4;
			auto icon = m_orbs[i].m_icon;
			if (icon !is null && icon.m_texture !is null && icon.m_frames.length() > 0)
				sb.DrawSprite(icon.m_texture, vec4(int(x), int(pos.y + 1), 16, 16), icon.m_frames[0].frame);
			x += 16;
			if (m_withNames)
			{
				x += 2;
				sb.DrawString(vec2(int(x), ty), m_names[i]);
				x += m_names[i].GetWidth();
			}
		}
	}
}

namespace Modules
{
	class HWPOrbWarnModule : Module
	{
		HWPOrbWarnModule()
		{
			super("hwp-orbwarn");
		}

		void UpdateFrame(int ms, GameInput& gameInput, MenuInput& menuInput, bool paused) override
		{
			HWP::OrbWarn::Update();
		}
	}
}
