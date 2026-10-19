// Held-only guns: the Rocket Launcher, Fat Boy and Quad skills and Sniper Shot put a gun in
// the character's hands while they fire (players/models/equipment/hwp_<gun>.model). These
// are not items. A skill's timeline runs HWPFirearmsHoldModel at 0: it points the equipped
// main-hand item's cached model (Equipment::m_modelTmp, which PlayerVisuals::GetModel draws
// in place of the item's own) at the gun, and the off hand's at an empty model, then
// rebuilds the player's scene. After "duration" ms the module below puts the cached models
// back. Timeline actions reach the other players too (PlayerSkillExecuteActions), so
// everyone sees the gun. The gun's path is the skill's held-model bind, so an orb (Fat
// Boy, Quad) swaps the gun the way it swaps the missile.
namespace HWP
{
	namespace Firearms
	{
		const string HELD_NONE = "players/models/equipment/hwp_held_none.model";

		class HeldGun
		{
			PlayerBase@ m_player;
			Equipment::Equipment@ m_main;
			Equipment::Equipment@ m_off;
			CustomUnitModel@ m_mainWas;
			CustomUnitModel@ m_offWas;
			int m_ms;
		}

		array<HeldGun@> g_heldGuns;
		dictionary g_heldModels;

		CustomUnitModel@ HeldModel(const string &in path)
		{
			CustomUnitModel@ model;
			if (g_heldModels.get(path, @model))
				return model;
			auto res = Resources::GetModel(path);
			if (res is null)
			{
				HWP::Log("firearms", "held model missing: " + path);
				return null;
			}
			@model = CustomUnitModel(res, g_plrMat);
			g_heldModels.set(path, @model);
			return model;
		}

		void RestoreHeld(HeldGun@ held)
		{
			if (held.m_main !is null)
				@held.m_main.m_modelTmp = held.m_mainWas;
			if (held.m_off !is null)
				@held.m_off.m_modelTmp = held.m_offWas;
			if (held.m_player !is null && held.m_player.m_unit.IsValid())
				held.m_player.RefreshScene();
		}

		void HoldGun(Actor@ owner, const string &in path, int ms)
		{
			auto player = cast<PlayerBase>(owner);
			if (player is null || path == "")
				return;
			auto gun = HeldModel(path);
			if (gun is null)
				return;
			auto main = player.GetEquipment(EquippedItemsSlots::MainHand);
			auto off = player.GetEquipment(EquippedItemsSlots::OffHand);
			if (main is null)
				return;

			HeldGun@ held = null;
			for (uint i = 0; i < g_heldGuns.length(); i++)
			{
				if (g_heldGuns[i].m_player is player)
				{
					@held = g_heldGuns[i];
					break;
				}
			}
			// already holding one: keep the cached models saved the first time, unless the
			// weapons were swapped meanwhile
			if (held !is null && (held.m_main !is main || held.m_off !is off))
			{
				RestoreHeld(held);
				g_heldGuns.removeAt(g_heldGuns.findByRef(held));
				@held = null;
			}
			if (held is null)
			{
				@held = HeldGun();
				@held.m_player = player;
				@held.m_main = main;
				@held.m_off = off;
				@held.m_mainWas = main.m_modelTmp;
				@held.m_offWas = off is null ? null : off.m_modelTmp;
				g_heldGuns.insertLast(held);
			}
			held.m_ms = ms;
			@main.m_modelTmp = gun;
			if (off !is null && off.GetModel() !is null)
			{
				auto none = HeldModel(HELD_NONE);
				if (none !is null)
					@off.m_modelTmp = none;
			}
			player.RefreshScene();
		}

		void UpdateHeld(int ms)
		{
			for (int i = int(g_heldGuns.length()) - 1; i >= 0; i--)
			{
				auto held = g_heldGuns[i];
				held.m_ms -= ms;
				if (held.m_ms > 0 && held.m_player.m_unit.IsValid())
					continue;
				RestoreHeld(held);
				g_heldGuns.removeAt(i);
			}
		}

		void ClearHeld()
		{
			for (uint i = 0; i < g_heldGuns.length(); i++)
				RestoreHeld(g_heldGuns[i]);
			g_heldGuns.removeRange(0, g_heldGuns.length());
		}
	}
}

// <dict><string name="class">HWPFirearmsHoldModel</string><string name="model-bind">held-model</string>
// <int name="duration">700</int></dict>
class HWPFirearmsHoldModel : IAction
{
	string m_model;
	int m_duration;

	HWPFirearmsHoldModel(UnitPtr unit, SValue& params)
	{
		m_model = GetParamString(unit, params, "model", false, "");
		m_duration = GetParamInt(unit, params, "duration", false, 700);
	}

	void CancelAction() {}
	void SetWeaponInformation(uint weapon) {}
	bool NeedNetParams() { return false; }
	void Update(int dt, int cooldown) {}

	bool DoAction(SValueBuilder@ builder, Actor@ owner, Actor@ target, vec2 pos, vec2 dir, float intensity)
	{
		HWP::Firearms::HoldGun(owner, m_model, m_duration);
		return true;
	}

	bool NetDoAction(SValue@ param, Actor@ owner, vec2 pos, vec2 dir)
	{
		HWP::Firearms::HoldGun(owner, m_model, m_duration);
		return true;
	}
}

namespace Modules
{
	class HWPFirearmsHeldModule : Module, HWP::ModuleStart
	{
		HWPFirearmsHeldModule()
		{
			super("hwp-firearms-held");
		}

		void Start(StartMode sMode)
		{
			// the items outlive the level: a gun still held when it ended goes back now
			HWP::Firearms::ClearHeld();
		}

		void UpdateFrame(int ms, GameInput& gameInput, MenuInput& menuInput, bool paused) override
		{
			if (!paused)
				HWP::Firearms::UpdateHeld(ms);
		}
	}
}
