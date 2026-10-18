// The Subclass Picker's skill row by the skills' real types.
// The vanilla SubclassPickWindow (Town/SubclassPickShopContent.as:96-102)
// shows the class's second-to-last skill def as "Active" and its last as
// "Passive": right for the vanilla specs (one active, one passive at the end
// of the list), wrong for the HWP ones (Sniper: Flashbang and Decoy, both
// actives, Snipe never shown; Trickster: Caltrops, Slice never shown). Each
// frame the open picker's row is checked after the window took its input
// (module UpdateFrame runs after the window manager's Update, paused or not,
// so before the frame is drawn). When it shows another class, or the window
// rewrote the two slots (SetCurrSubclass, also on a pick), the row is laid out
// again: the spec's own skills (its defs the parent class does not have),
// actives then passives, each with its type's label: "Passive" for a skill
// whose targeting mode is Passive (no button, as GetSkillInput and the HUD
// tell), else "Active". More than two get copies of the first slot,
// the slots spread across the row. The window itself is not replaced: no
// window hook, and the shop content class sits in the vanilla NPC unit.
namespace HWP
{
	namespace SubclassPick
	{
		const int MAX_SLOTS = 4;
		const string LABEL_ID = "hwp-pick-label";   // + slot index, on every slot's type label
		const string NAME_ID = "hwp-pick-name";     // + slot index, from slot 2 (0 and 1 keep the vanilla ids)
		const string SKILL_ID = "hwp-pick-skill";

		SubclassPickWindow@ g_window;
		int g_index = -1;
		array<string> g_shown;      // the skill ids slots 0 and 1 showed after the last layout
		int g_count = -1;           // the slots shown by the last layout
		array<TextWidget@> g_names;
		array<SkillWidget@> g_skills;
		array<TextWidget@> g_labels;
		array<float> g_y;           // the y offsets of slot 0's name, skill and label

		PlayerClass@ ParentOf(PlayerClass@ cls)
		{
			if (cls is null || cls.parent == 0)
				return null;
			for (uint i = 0; i < PlayerClass::Instances.length(); i++)
			{
				if (PlayerClass::Instances[i].m_idHash == cls.parent)
					return PlayerClass::Instances[i];
			}
			return null;
		}

		bool HasDef(PlayerClass@ cls, uint idHash)
		{
			for (uint i = 0; cls !is null && i < cls.m_skillDefs.length(); i++)
			{
				if (cls.m_skillDefs[i].m_idHash == idHash)
					return true;
			}
			return false;
		}

		// what the vanilla bar gives a button: not TargetingMode::Passive (the test
		// GetSkillInput and HUDPlayer make). A def's m_type can't tell: PlayerSkillDef
		// makes an untyped def (every passive) a Spell (PlayerClass.as:91-92).
		bool IsActive(Skills::Skill@ skill)
		{
			return skill !is null && skill.GetTargetingMode() != Skills::TargetingMode::Passive;
		}

		// the spec's own skill defs (Spell defs its parent class lacks) and a temp skill of
		// each (the window's MakeSkillTemp, what the vanilla row shows), actives first, then
		// passives, class order in each
		void Row(SubclassPickWindow@ w, PlayerClass@ cls, array<PlayerSkillDef@>@ defs, array<Skills::Skill@>@ skills)
		{
			array<PlayerSkillDef@> own;
			auto parent = ParentOf(cls);
			for (uint i = 0; i < cls.m_skillDefs.length(); i++)
			{
				auto def = cls.m_skillDefs[i];
				if (def is null || def.m_type != PlayerSkillType::Spell || (parent !is null && HasDef(parent, def.m_idHash)))
					continue;
				own.insertLast(def);
			}
			if (own.length() == 0)
			{
				// nothing of its own: the two the vanilla row shows
				for (int i = max(0, int(cls.m_skillDefs.length()) - 2); i < int(cls.m_skillDefs.length()); i++)
					own.insertLast(cls.m_skillDefs[i]);
			}
			array<PlayerSkillDef@> passiveDefs;
			array<Skills::Skill@> passiveSkills;
			for (uint i = 0; i < own.length(); i++)
			{
				auto skill = w.MakeSkillTemp(own[i]);
				if (IsActive(skill))
				{
					defs.insertLast(own[i]);
					skills.insertLast(skill);
				}
				else
				{
					passiveDefs.insertLast(own[i]);
					passiveSkills.insertLast(skill);
				}
			}
			for (uint i = 0; i < passiveDefs.length(); i++)
			{
				defs.insertLast(passiveDefs[i]);
				skills.insertLast(passiveSkills[i]);
			}
			if (int(defs.length()) > MAX_SLOTS)
			{
				defs.resize(uint(MAX_SLOTS));
				skills.resize(uint(MAX_SLOTS));
			}
		}

		string ShownId(SkillWidget@ w)
		{
			if (w is null)
				return "";
			if (w.m_skill !is null)
				return w.m_skill.m_id;
			if (w.m_plrSkill !is null)
				return w.m_plrSkill.m_id;
			if (w.m_passiveSkill !is null)
				return w.m_passiveSkill.m_id;
			return "";
		}

		// the unnamed type label under a slot's skill (same x in subclass_picker.gui)
		TextWidget@ LabelUnder(Widget@ skill)
		{
			auto row = skill.m_parent;
			for (uint i = 0; row !is null && i < row.m_children.length(); i++)
			{
				auto t = cast<TextWidget>(row.m_children[i]);
				if (t !is null && t.m_id == "" && abs(t.m_offset.x - skill.m_offset.x) < 1 && t.m_offset.y > skill.m_offset.y)
					return t;
			}
			return null;
		}

		// a copy of a widget that does not share the original's built text
		// (Widget.CloneInto value-copies the fields, the BitmapString handle too)
		TextWidget@ CloneText(TextWidget@ t, const string &in id)
		{
			auto c = cast<TextWidget>(t.Clone());
			@c.m_text = null;
			c.SetID(id);
			return c;
		}

		bool Bind(SubclassPickWindow@ w)
		{
			g_names.resize(0);
			g_skills.resize(0);
			g_labels.resize(0);
			g_shown.resize(0);
			g_count = -1;
			g_index = -1;
			auto activeName = cast<TextWidget>(w.m_widget.GetWidgetById("skill-active-name"));
			auto active = cast<SkillWidget>(w.m_widget.GetWidgetById("skill-active"));
			auto passiveName = cast<TextWidget>(w.m_widget.GetWidgetById("skill-passive-name"));
			auto passive = cast<SkillWidget>(w.m_widget.GetWidgetById("skill-passive"));
			if (activeName is null || active is null || passiveName is null || passive is null)
				return false;
			auto activeLabel = LabelUnder(active);
			auto passiveLabel = LabelUnder(passive);
			if (activeLabel is null || passiveLabel is null || active.m_parent is null)
				return false;
			activeLabel.SetID(LABEL_ID + "0");
			passiveLabel.SetID(LABEL_ID + "1");
			g_names.insertLast(activeName);
			g_names.insertLast(passiveName);
			g_skills.insertLast(active);
			g_skills.insertLast(passive);
			g_labels.insertLast(activeLabel);
			g_labels.insertLast(passiveLabel);
			g_y = { activeName.m_offset.y, active.m_offset.y, activeLabel.m_offset.y };
			return true;
		}

		void AddSlot()
		{
			int i = int(g_skills.length());
			auto row = g_skills[0].m_parent;
			auto name = CloneText(g_names[0], NAME_ID + i);
			auto label = CloneText(g_labels[0], LABEL_ID + i);
			auto skill = cast<SkillWidget>(g_skills[0].Clone());
			skill.SetID(SKILL_ID + i);
			@skill.m_cost = null;
			skill.m_costCache = -1;
			@skill.m_shadow = g_skills[0].m_shadow;
			skill.m_shadowOffset = g_skills[0].m_shadowOffset;
			skill.m_showTooltip = g_skills[0].m_showTooltip;
			skill.m_drawSkillInfo = g_skills[0].m_drawSkillInfo;
			skill.m_navPos = ivec2(i, g_skills[0].m_navPos.y);
			row.AddChild(name);
			row.AddChild(skill);
			row.AddChild(label);
			g_names.insertLast(name);
			g_skills.insertLast(skill);
			g_labels.insertLast(label);
		}

		float SlotX(int i, int n)
		{
			float step = n <= 2 ? 120.0f : (n == 3 ? 105.0f : 78.0f);
			return (i - (n - 1) / 2.0f) * step;
		}

		void Layout(SubclassPickWindow@ w)
		{
			auto cls = w.m_classes[w.m_currPickedIndex];
			array<PlayerSkillDef@> defs;
			array<Skills::Skill@> skills;
			Row(w, cls, defs, skills);
			int n = int(defs.length());
			while (int(g_skills.length()) < n)
				AddSlot();
			string activeText = Resources::GetString(".menu.subclass.skill.active");
			string passiveText = Resources::GetString(".menu.subclass.skill.passive");
			for (int i = 0; i < int(g_skills.length()); i++)
			{
				bool shown = i < n;
				g_names[i].m_visible = shown;
				g_skills[i].m_visible = shown;
				g_labels[i].m_visible = shown;
				if (!shown)
					continue;
				float x = SlotX(i, n);
				g_names[i].m_offset = vec2(x, g_y[0]);
				g_skills[i].m_offset = vec2(x, g_y[1]);
				g_labels[i].m_offset = vec2(x, g_y[2]);
				g_names[i].SetText(Resources::GetString(defs[i].m_name));
				g_skills[i].SetSkill(skills[i]);
				g_labels[i].SetText(IsActive(skills[i]) ? activeText : passiveText);
			}
			if (n != g_count)
			{
				// the gamepad's slot list (it skips hidden ones); only on a count change,
				// as it puts the selection back on the first slot
				w.RefreshInteractableWidgets(w.m_widget);
				g_count = n;
			}
			g_skills[0].m_parent.Invalidate();
			g_index = w.m_currPickedIndex;
			g_shown = { ShownId(g_skills[0]), ShownId(g_skills[1]) };
		}

		SubclassPickWindow@ OpenPicker()
		{
			auto gm = cast<BaseGameMode>(g_gameMode);
			if (gm is null || gm.m_windowManager is null)
				return null;
			for (int i = int(gm.m_windowManager.m_objects.length()) - 1; i >= 0; i--)
			{
				auto w = cast<SubclassPickWindow>(gm.m_windowManager.m_objects[i]);
				if (w !is null)
					return w;
			}
			return null;
		}

		void Update()
		{
			auto w = OpenPicker();
			if (w is null)
			{
				if (g_window !is null)
				{
					@g_window = null;
					g_names.resize(0);
					g_skills.resize(0);
					g_labels.resize(0);
				}
				return;
			}
			if (w.m_classes.length() == 0 || w.m_currPickedIndex < 0 || w.m_currPickedIndex >= int(w.m_classes.length()))
				return;
			if (w !is g_window)
			{
				@g_window = w;
				if (!Bind(w))
				{
					HWP::LogError("subclasspick", "subclass_picker.gui not as expected; vanilla skill row kept");
					return;
				}
			}
			if (g_skills.length() < 2)
				return;
			if (g_index == w.m_currPickedIndex && g_shown.length() == 2
				&& g_shown[0] == ShownId(g_skills[0]) && g_shown[1] == ShownId(g_skills[1]))
				return;
			Layout(w);
		}
	}
}

namespace Modules
{
	class HWPSubclassPickModule : Module
	{
		HWPSubclassPickModule()
		{
			super("hwp-subclasspick");
		}

		void UpdateFrame(int ms, GameInput& gameInput, MenuInput& menuInput, bool paused) override
		{
			HWP::SubclassPick::Update();
		}
	}
}
