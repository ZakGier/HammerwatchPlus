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
		const string RELOAD_CAST = "players/hwp/firearms/stacks_firearms.sval:reload_cast";
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
			"players/hwp/firearms/projectiles/grenade_frag_stun.unit",
			"players/hwp/firearms/projectiles/grenade_stun_flash.unit",
			"players/hwp/firearms/projectiles/grenade_incendiary.unit",
			"players/hwp/firearms/projectiles/grenade_incendiary_area.unit",
			"players/hwp/firearms/projectiles/grenade_gas.unit",
			"players/hwp/firearms/projectiles/grenade_gas_cloud.unit",
			"players/hwp/firearms/projectiles/reload_mag_pistol.unit",
			"players/hwp/firearms/projectiles/reload_mag_rifle.unit",
			"players/hwp/firearms/projectiles/rocket.unit",
			"players/hwp/firearms/projectiles/rocket_fatboy.unit",
			"players/hwp/firearms/projectiles/rocket_magic.unit",
			"players/hwp/firearms/projectiles/rocket_magic_burn.unit",
			"players/hwp/firearms/projectiles/rocket_quad.unit",
			"players/hwp/firearms/projectiles/turret_round.unit",
			"players/hwp/firearms/units/turret.unit" };

		bool g_checked = false;

		// Set when a new local player unit shows up (any spawn path: a new character in town,
		// a level load, a respawn). Once the gun's marker buff has given the clip a size (the
		// item re-applies it on its first update) the clip is set: full in the village and on
		// the first spawn of a run's first floor, else the rounds it held when the last unit
		// went (g_lastClip), so going down a floor reloads nothing. The GameModeSpawnPlayer
		// hook missed the town spawn of a new character (look-firearms-anims 20261019-123319:
		// clip 0/30), so the player is watched instead: the PlayerBase and the record's class,
		// not the unit id (a new character's unit in town took the old one's id,
		// mod-firearms-clip 20261019-123825). g_filledFor is reset in Start, and g_levelStart
		// marks the first player of a level.
		bool g_fillPending = false;
		bool g_fillFull = false;
		int g_fillWaited = 0;
		PlayerBase@ g_filledFor;
		string g_filledClass;
		int g_lastClip = 0;
		bool g_levelStart = true;
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
			auto plr = GetLocalPlayer();
			auto def = ActorBuffStackDef::Get(CLIP);
			if (plr is null || def is null)
				return;
			auto rec = GetLocalPlayerRecord();
			string cls = (rec is null || rec.playerClass is null) ? "" : rec.playerClass.m_id;
			if (plr !is g_filledFor || cls != g_filledClass)
			{
				@g_filledFor = plr;
				g_filledClass = cls;
				g_fillPending = IsFirearms(rec);
				g_fillFull = g_inTown || (g_levelStart && MissionManager::GetCurrentLevelNum() == 1);
				g_levelStart = false;
				g_fillWaited = 0;
			}
			if (!g_fillPending)
			{
				g_lastClip = plr.GetStacks(def);
				return;
			}
			g_fillWaited += ms;
			int mx = ClipMax(plr, def);
			if (mx > 0)
			{
				g_fillPending = false;
				int had = plr.GetStacks(def);
				int want = g_fillFull ? mx : min(g_lastClip, mx);
				if (want > had)
					plr.AddStacks(plr, def, want - had);
				g_lastClip = plr.GetStacks(def);
				HWP::Log("firearms", (g_fillFull ? "clip filled " : "clip kept ") + g_lastClip + "/" + mx
					+ " (had " + had + ", level " + (g_inTown ? "town" : "" + MissionManager::GetCurrentLevelNum()) + ") after " + g_fillWaited + " ms");
			}
			else if (g_fillWaited >= FILL_TIMEOUT)
			{
				g_fillPending = false;
				HWP::Log("firearms", "no gun gave the clip a size within " + FILL_TIMEOUT + " ms; clip left empty");
			}
		}

		// Pulling the trigger on an empty clip starts the reload. The clip's lose-effects only
		// start it when the last round is spent, so a clip that is empty some other way (a gun
		// swapped in, a fill that timed out) would otherwise stay empty until Reload is cast.
		void UpdateEmptyTrigger(GameInput& input)
		{
			if (!input.MainHandAttack.Down && !input.OffHandAttack.Down)
				return;
			auto plr = GetLocalPlayer();
			auto clip = ActorBuffStackDef::Get(CLIP);
			auto reloading = ActorBuffStackDef::Get(RELOADING);
			if (plr is null || clip is null || reloading is null || !IsFirearms(GetLocalPlayerRecord()))
				return;
			if (ClipMax(plr, clip) <= 0 || plr.GetStacks(clip) > 0 || plr.GetStacks(reloading) > 0)
				return;
			plr.AddStacks(plr, reloading, 1);
			HWP::Log("firearms", "trigger on an empty clip: reloading");
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
				"players/hwp/firearms/stacks_firearms.sval:rocket_charges",
				"players/hwp/firearms/stacks_firearms.sval:gl_charges", ADRENALINE };
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
			{
				// the pistols from the lists their hand swap uses (Pistols.as)
				array<string> ids = { "hwp_rifle_01", "hwp_rifle_02", "hwp_rifle_03" };
				for (uint i = 0; i < PISTOL_MAIN.length(); i++)
					ids.insertLast(PISTOL_MAIN[i]);
				for (uint i = 0; i < PISTOL_OFF.length(); i++)
					ids.insertLast(PISTOL_OFF[i]);
				if (PISTOL_MAIN.length() != PISTOL_OFF.length())
					HWP::LogError("firearms", "PISTOL_MAIN and PISTOL_OFF differ in length: a pistol has no twin");
				HWP::CheckEquipment("firearms", ids);
			}
			HWP::CheckUnits("firearms", UNITS);
			HWP::Log("firearms", "self-check done");
		}

		void CmdStatus(array<string>@ args)
		{
			if (args.length() > 0 && args[0] == "sound")
			{
				CmdSound(args);
				return;
			}
			// "muzzle": where the last gun round started, ahead of the player and to the aim's right
			if (args.length() > 0 && args[0] == "muzzle")
			{
				auto m = HWP::Firearms::g_lastMuzzle;
				HWP::Commands::Reply("muzzle: ahead " + formatFloat(m.x, "", 0, 1) + " right " + formatFloat(m.y, "", 0, 1)
					+ ", last miss flew " + formatFloat(HWP::Firearms::g_lastRange, "", 0, 1));
				return;
			}
			// "shots": the gaps between the local player's last gun rounds, in ms, oldest first
			if (args.length() > 0 && args[0] == "shots")
			{
				string gaps = "";
				auto t = HWP::Firearms::g_shotTimes;
				for (uint i = 1; i < t.length(); i++)
					gaps += (i > 1 ? " " : "") + (t[i] - t[i - 1]);
				HWP::Commands::Reply("shots: " + t.length() + " rounds, gaps " + gaps);
				return;
			}
			// "elements [reset]": the local player's gun shots since the last reset, by roll
			if (args.length() > 0 && args[0] == "elements")
			{
				auto r = HWP::Firearms::g_eleRolls;
				// "elements roll <n>": RollElement n times on the local player's stats, the roll
				// every gun shot makes (HWPFirearmsGunShot.DoAction), to measure its weights
				if (args.length() > 2 && args[1] == "roll")
				{
					auto plr = cast<PlayerBase>(GetLocalPlayer());
					int n = min(100000, max(0, int(parseInt(args[2]))));
					array<int> c = { 0, 0, 0, 0, 0 };
					float chance = HWP::Firearms::CustomStat(plr, "hwp-ele-chance");
					for (int i = 0; i < n; i++)
						c[HWP::Firearms::RollElement(plr, chance) + 1]++;
					HWP::Commands::Reply("elements rolled " + n + " at chance " + formatFloat(chance, "", 0, 3) + ": plain " + c[0]
						+ " fire " + c[1] + " ice " + c[2] + " lightning " + c[3] + " poison " + c[4]);
					return;
				}
				if (args.length() > 1 && args[1] == "reset")
				{
					for (uint i = 0; i < r.length(); i++)
						HWP::Firearms::g_eleRolls[i] = 0;
					HWP::Commands::Reply("elements: reset");
					return;
				}
				HWP::Commands::Reply("elements: plain " + r[0] + " fire " + r[1] + " ice " + r[2] + " lightning " + r[3] + " poison " + r[4]);
				return;
			}
			// "empty" (cheat): the clip at 0 with no reload running, as after going down a
			// floor with every round spent. The count is set, not spent, so the clip's
			// lose-effects (the automatic reload) don't run: for trying the empty trigger.
			if (args.length() > 0 && args[0] == "empty")
			{
				if (!HWP::Cheats::On())
					return;
				auto st = FindStack(GetLocalPlayer(), ActorBuffStackDef::Get(CLIP));
				if (st is null)
				{
					HWP::Commands::Reply("no clip");
					return;
				}
				st.m_stacks = 0;
				g_lastClip = 0;
				HWP::Commands::Reply("clip emptied, no reload");
				return;
			}
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

namespace Modules
{
	class HWPFirearmsModule : Module, HWP::ModuleStart
	{
		HWPFirearmsModule()
		{
			super("hwp-firearms");
			HWP::Commands::Register("firearms", "[empty|shots|elements [reset|roll n]|sound [n|next|prev|again|list]]  Firearms Specialist status; empty (cheat) empties the clip without reloading; sound (cheat) plays a firing-sound candidate", HWP::Commands::Handler(HWP::Firearms::CmdStatus));
			HWP::Firearms::SelfCheck(false);
			HWP::Bag::OnEquip(HWP::Bag::EquipPrepare(HWP::Firearms::PistolEquip));
		}

		void Start(StartMode sMode)
		{
			HWP::Firearms::g_checked = false;
			HWP::Firearms::SelfCheck(true);
			@HWP::Firearms::g_filledFor = null;
			HWP::Firearms::g_filledClass = "";
			HWP::Firearms::g_levelStart = true;
			HWP::Firearms::g_headshot = false;
			HWP::Firearms::g_headshotEnd = false;
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
			HWP::Firearms::UpdateEmptyTrigger(gameInput);
			HWP::Firearms::UpdateCombat(ms);
			HWP::Firearms::UpdatePistols(ms);
			HWP::Firearms::UpdateAudition(ms);
			HWP::Firearms::UpdateLaserDot();
		}

		void RenderFrame(int idt, SpriteBatch& sb) override
		{
			HWP::Firearms::RenderCombat(idt, sb);
		}
	}
}
