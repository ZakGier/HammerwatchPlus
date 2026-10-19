// Firearms Specialist: the class is data (players/hwp/firearms,
// tweak/hwp/equipment_firearms.sval). This module self-checks that the data
// registered, fills the clip when the player spawns, ticks the skill logic in
// Combat.as, and offers hwp firearms for a status line.
namespace HWP
{
	namespace Firearms
	{
		const string CLASS_ID = "hwp_firearms";
		const string CLIP = "players/hwp/firearms/stacks_firearms.sval:clip";
		const string RELOADING = "players/hwp/firearms/stacks_firearms.sval:reloading";
		const array<string> UNITS = {
			"players/hwp/firearms/projectiles/bullet.unit",
			"players/hwp/firearms/projectiles/rifle_round.unit",
			"players/hwp/firearms/projectiles/rifle_round_epic.unit",
			"players/hwp/firearms/projectiles/rifle_gl_shell.unit",
			"players/hwp/firearms/projectiles/glock_round.unit",
			"players/hwp/firearms/projectiles/glock_round_dual.unit",
			"players/hwp/firearms/projectiles/glock_round_off.unit",
			"players/hwp/firearms/projectiles/bullet_snipe.unit",
			"players/hwp/firearms/projectiles/grenade_frag.unit",
			"players/hwp/firearms/projectiles/grenade_stun.unit",
			"players/hwp/firearms/projectiles/grenade_frag_stun.unit",
			"players/hwp/firearms/projectiles/grenade_stun_flash.unit",
			"players/hwp/firearms/projectiles/grenade_incendiary.unit",
			"players/hwp/firearms/projectiles/grenade_incendiary_area.unit",
			"players/hwp/firearms/projectiles/grenade_gas.unit",
			"players/hwp/firearms/projectiles/grenade_gas_cloud.unit",
			"players/hwp/firearms/projectiles/reload_mag.unit",
			"players/hwp/firearms/projectiles/rocket.unit",
			"players/hwp/firearms/projectiles/rocket_fatboy.unit",
			"players/hwp/firearms/projectiles/rocket_magic.unit",
			"players/hwp/firearms/projectiles/rocket_magic_burn.unit",
			"players/hwp/firearms/projectiles/rocket_quad.unit" };

		bool g_checked = false;

		// Set when the local Firearms Specialist spawns; the clip is filled once the gun's
		// marker buff has given it a size (the item re-applies it on its first update).
		bool g_fillPending = false;
		int g_fillWaited = 0;
		const int FILL_TIMEOUT = 3000;

		bool IsFirearms(PlayerRecord@ rec)
		{
			if (rec is null || rec.playerClass is null)
				return false;
			return rec.playerClass.m_id == CLASS_ID || rec.playerClass.parent == HashString(CLASS_ID);
		}

		int ClipMax(PlayerBase@ plr, ActorBuffStackDef@ def)
		{
			auto mod = plr.GetModifiedStack(def);
			return mod is null ? def.m_maxStacks : mod.m_maxStacks;
		}

		void UpdateFill(int ms)
		{
			if (!g_fillPending)
				return;
			auto plr = GetLocalPlayer();
			auto def = ActorBuffStackDef::Get(CLIP);
			if (plr is null || def is null)
				return;
			g_fillWaited += ms;
			int mx = ClipMax(plr, def);
			if (mx > 0)
			{
				g_fillPending = false;
				plr.AddStacks(plr, def, mx);
				HWP::Log("firearms", "clip filled " + plr.GetStacks(def) + "/" + mx + " after " + g_fillWaited + " ms");
			}
			else if (g_fillWaited >= FILL_TIMEOUT)
			{
				g_fillPending = false;
				HWP::Log("firearms", "no gun gave the clip a size within " + FILL_TIMEOUT + " ms; clip left empty");
			}
		}

		// Logged at boot (module constructor, for dev_check) and once per
		// gameplay load (g_checked is reset in Start): did the loaders pick the
		// class, the subclasses, the rifles and the units up? Items are only
		// registered after the modules are made, so the rifles are checked at
		// gameplay load.
		void SelfCheck(bool items)
		{
			if (g_checked)
				return;
			g_checked = true;

			int subclasses = 0;
			bool found = false;
			uint hash = HashString(CLASS_ID);
			for (uint i = 0; i < PlayerClass::Instances.length(); i++)
			{
				if (PlayerClass::Instances[i].m_id == CLASS_ID)
					found = true;
				if (PlayerClass::Instances[i].parent == hash)
					subclasses++;
			}
			if (!found)
				HWP::LogError("firearms", "class " + CLASS_ID + " not registered (players/hwp/firearms/class_firearms.sval)");
			else
				HWP::Log("firearms", "class registered with " + subclasses + " subclass(es)");

			array<string> stacks = { CLIP, RELOADING, FOCUS,
				"players/hwp/firearms/stacks_firearms.sval:grenade_charges",
				"players/hwp/firearms/stacks_firearms.sval:rocket_charges" };
			for (uint i = 0; i < stacks.length(); i++)
			{
				if (ActorBuffStackDef::Get(stacks[i]) is null)
					HWP::LogError("firearms", "stack not registered: " + stacks[i]);
			}

			// TagList.ApplyTag shifts an int, so a skill tag past bit 30 sets the wrong bits
			// and skill-tags filters on it (Overpacked Explosives) would misfire.
			array<string> tags = { "hwp_firearm", "hwp_explosive" };
			for (uint i = 0; i < tags.length(); i++)
			{
				int bit = g_skillTags.m_tags.find(tags[i]) + 1;
				if (bit <= 0)
					HWP::Log("firearms", "skill tag " + tags[i] + " not loaded yet");
				else if (bit >= 31)
					HWP::LogError("firearms", "skill tag " + tags[i] + " is bit " + bit + " (>= 31): tag filters on it misfire");
				else
					HWP::Log("firearms", "skill tag " + tags[i] + " is bit " + bit);
			}
			if (items)
				HWP::CheckEquipment("firearms", { "hwp_rifle_01", "hwp_rifle_02", "hwp_rifle_03",
					"hwp_glock_mh_01", "hwp_glock_mh_02", "hwp_glock_mh_03",
					"hwp_glock_oh_01", "hwp_glock_oh_02", "hwp_glock_oh_03" });
			HWP::CheckUnits("firearms", UNITS);
			HWP::Log("firearms", "self-check done");
		}

		void CmdStatus(array<string>@ args)
		{
			auto rec = GetLocalPlayerRecord();
			if (rec is null || rec.playerClass is null)
			{
				HWP::Commands::Reply("no character loaded");
				return;
			}
			string rifle = "-";
			if (rec.equipped !is null)
			{
				auto item = rec.equipped.GetEquipment(EquippedItemsSlots::MainHand);
				if (item !is null)
					rifle = item.GetName();
			}
			string mana = "" + int(rec.mana * float(rec.MaxMana())); // mana is a 0..1 ratio
			string maxMana = "" + rec.MaxMana();
			string clip = "-", clipMax = "-";
			auto plr = GetLocalPlayer();
			auto def = ActorBuffStackDef::Get(CLIP);
			if (plr !is null && def !is null)
			{
				clip = "" + plr.GetStacks(def);
				clipMax = "" + ClipMax(plr, def);
			}
			HWP::Commands::Reply(Resources::GetString(".hwp.firearms.status", {
				{ "cls", rec.playerClass.m_id }, { "rifle", rifle }, { "clip", clip }, { "clipmax", clipMax },
				{ "mana", mana }, { "max", maxMana } }));
		}
	}
}

namespace HWPFirearms
{
	[Hook]
	void GameModeSpawnPlayer(AGameplayGameMode@ gm, PlayerRecord@ rec)
	{
		if (rec is null || !rec.local || !HWP::Firearms::IsFirearms(rec))
			return;
		HWP::Firearms::g_fillPending = true;
		HWP::Firearms::g_fillWaited = 0;
	}
}

namespace Modules
{
	class HWPFirearmsModule : Module, HWP::ModuleStart
	{
		HWPFirearmsModule()
		{
			super("hwp-firearms");
			HWP::Commands::Register("firearms", " Firearms Specialist status", HWP::Commands::Handler(HWP::Firearms::CmdStatus));
			HWP::Firearms::SelfCheck(false);
		}

		void Start(StartMode sMode)
		{
			HWP::Firearms::g_checked = false;
			HWP::Firearms::SelfCheck(true);
			HWP::Firearms::g_headshot = false;
			HWP::Firearms::g_overReload = HWP::Firearms::OverReloadState();
			for (uint i = 0; i < HWP::Firearms::g_hoarded.length(); i++)
			{
				HWP::Firearms::g_hoarded[i].m_readyMs = 0;
				HWP::Firearms::g_hoarded[i].m_spend = false;
				HWP::Firearms::g_hoarded[i].m_wasCooling = false;
			}
		}

		void UpdateFrame(int ms, GameInput& gameInput, MenuInput& menuInput, bool paused) override
		{
			if (paused)
				return;
			HWP::Firearms::UpdateFill(ms);
			HWP::Firearms::UpdateCombat(ms);
		}

		void RenderFrame(int idt, SpriteBatch& sb) override
		{
			HWP::Firearms::RenderCombat(idt, sb);
		}
	}
}
