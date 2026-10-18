// HWP mercenary: Heroes of Hammerwatch 1's mercenary mode. A fresh level-1
// character whose class already has a veteran (another character of that
// class at mercenary.unlock_level, default 20, HoH1's unlock) can enlist in
// town ('hwp merc enlist confirm'): it jumps to mercenary.start_level (default
// 10: HoH2 caps at 20 where HoH1 did not, so HoH1's level 20 start would skip
// all of the levelling) and from then on its death is permanent.
//
// Prestige is HoH1's formula: 1 per mission floor entered, 10 per boss floor
// cleared, 75 * (new game+ earned as a mercenary)^2. The ranks are HoH1's
// (Private 0 ... General 10000) and so is the bonus: +15% gold and experience
// per rank, from Private on (TitleList inc-modifiers with extra-inc-modifiers
// 1), added in the PlayerRecordRefreshModifiers hook.
//
// A mercenary falls when it dies on a mission floor, or, with
// mercenary.revivable (host setting, default off) only when the run fails.
// A fallen mercenary goes into the town's ledger of the fallen and can no
// longer be played: in town the character picker opens as soon as no other
// menu is up. Its save is kept (the picker can delete it).
//
//   merc.fallen   client -> host -> all   { n, r, l, c }  announce a fall
//   merc.boss     client -> host -> all   { k }           a boss died on floor k
//
// PlayerKilledActor only fires on the killer's machine, so a boss kill goes
// through the host to every mercenary in the party.
namespace HWP
{
	namespace Mercenary
	{
		const string FALLEN = "merc.fallen";
		const string BOSS = "merc.boss";

		const array<int> RANK_POINTS = { 0, 50, 200, 500, 1000, 2500, 5000, 10000 };
		const float RANK_BONUS = 0.15f;  // gold and experience per rank, Private included
		const int FLOOR_POINTS = 1;
		const int BOSS_POINTS = 10;
		const int NGP_POINTS = 75;
		const int UNLOCK_LEVEL = 20;
		const int START_LEVEL = 10;
		const int LEDGER_MAX = 50;
		const int PICKER_DELAY_MS = 1500;

		bool g_wasDead = false;
		int g_pickerMs = PICKER_DELAY_MS;
		array<array<Modifiers::IModifier@>@> g_rankMods;  // index = rank
		ModifierProvider@ g_provider;

		void Reply(const string &in text) { HWP::Commands::Reply(text); }

		DataBag@ Bag(PlayerRecord@ rec) { return HWP::SaveData::Player(rec); }
		bool IsMerc(PlayerRecord@ rec) { return rec !is null && Bag(rec).GetBool("merc.on"); }
		bool IsFallen(PlayerRecord@ rec) { return IsMerc(rec) && Bag(rec).GetBool("merc.dead"); }

		bool InTown() { return cast<TownGameMode>(g_gameMode) !is null; }
		bool InMission() { return !InTown() && MissionManager::GetCurrentMission() !is null; }

		// ---- prestige and rank ---------------------------------------------------

		int Prestige(PlayerRecord@ rec)
		{
			auto bag = Bag(rec);
			int ngp = max(0, int(rec.ngp) - bag.GetInt("merc.ngp0"));
			return bag.GetInt("merc.floors") * FLOOR_POINTS + bag.GetInt("merc.bosses") * BOSS_POINTS + ngp * ngp * NGP_POINTS;
		}

		int RankOf(int prestige)
		{
			int rank = 0;
			for (uint i = 0; i < RANK_POINTS.length(); i++)
				if (prestige >= RANK_POINTS[i])
					rank = int(i);
			return rank;
		}

		string RankName(int rank) { return Resources::GetString(".hwp.mercenary.rank." + rank); }
		int BonusPercent(int rank) { return int(RANK_BONUS * 100 * (rank + 1) + 0.5f); }

		array<Modifiers::IModifier@>@ RankModifiers(int rank)
		{
			while (int(g_rankMods.length()) <= rank)
			{
				float mul = 1.0f + RANK_BONUS * (g_rankMods.length() + 1);
				SValueBuilder gold;
				gold.PushDictionary();
				gold.PushFloat("gold-mul", mul);
				gold.PopDictionary();
				auto goldData = gold.Build();
				SValueBuilder xp;
				xp.PushDictionary();
				xp.PushFloat("mul", mul);
				xp.PopDictionary();
				auto xpData = xp.Build();
				array<Modifiers::IModifier@> mods = {
					Modifiers::MaterialGain(UnitPtr(), goldData),
					Modifiers::Experience(UnitPtr(), xpData)
				};
				g_rankMods.insertLast(mods);
			}
			return g_rankMods[rank];
		}

		// rank-up message and modifiers when the prestige crossed a threshold
		void CheckRank(PlayerRecord@ rec)
		{
			auto bag = Bag(rec);
			int rank = RankOf(Prestige(rec));
			if (rank == bag.GetInt("merc.rank"))
				return;
			bool up = rank > bag.GetInt("merc.rank");
			bag.SetInt("merc.rank", rank);
			rec.RefreshModifiers();
			if (up)
				Reply(Resources::GetString(".hwp.mercenary.rankup", { { "rank", RankName(rank) }, { "bonus", BonusPercent(rank) } }));
		}

		void AddPrestige(PlayerRecord@ rec, const string &in counter, int n)
		{
			auto bag = Bag(rec);
			bag.SetInt(counter, bag.GetInt(counter) + n);
			CheckRank(rec);
		}

		// ---- floors and bosses ---------------------------------------------------

		string FloorKey()
		{
			auto mm = MissionManager::g_module;
			if (mm is null)
				return "";
			return "" + mm.m_missionDefHash + ":" + mm.m_missionLevelIndex + ":" + mm.m_missionRewardSeed;
		}

		string FloorName(uint missionHash, int levelIndex)
		{
			auto def = MissionDef::Get(missionHash);
			string name = def is null ? "a mission" : def.m_name;
			if (levelIndex >= 0)
				name += " floor " + (levelIndex + 1);
			return name;
		}

		// once per mission floor (resuming a floor does not count it again)
		void CountFloor(PlayerRecord@ rec)
		{
			string key = FloorKey();
			auto bag = Bag(rec);
			if (key == "" || bag.GetString("merc.floor_key") == key)
				return;
			bag.SetString("merc.floor_key", key);
			if (MissionManager::g_module.m_missionLevelIndex == 0)
				Reply(Resources::GetString(".hwp.mercenary.reminder", { { "rank", RankName(bag.GetInt("merc.rank")) } }));
			AddPrestige(rec, "merc.floors", 1);
		}

		// a mission's boss level: a fixed levels/boss_*.lvl map, or a module with a
		// boss (the heaven trials). Boss-tagged actors also show up elsewhere, such
		// as the bandit boss encounter in the keep's special rooms.
		bool IsBossFloor()
		{
			auto mm = MissionManager::g_module;
			if (mm is null)
				return false;
			auto def = MissionDef::Get(mm.m_missionDefHash);
			if (def is null || mm.m_missionLevelIndex < 0 || uint(mm.m_missionLevelIndex) >= def.m_levels.length())
				return false;
			auto level = def.m_levels[mm.m_missionLevelIndex];
			if (level.m_level.findFirst("levels/boss_") == 0)
				return true;
			return level.m_moduleData !is null && level.m_moduleData.GetDictionaryEntry("boss") !is null;
		}

		bool HasTag(Actor@ actor, const string &in tag)
		{
			return (actor.Tags & ApplyTag(0, g_actorTags.GetTag(tag))) != 0;
		}

		void OnKill(Player@ player, Actor@ killed)
		{
			if (player is null || killed is null || player.m_record is null || !player.m_record.local)
				return;
			if (!InMission() || !HasTag(killed, "boss") || !IsBossFloor())
				return;
			SValueBuilder b;
			b.PushDictionary();
			b.PushString("k", FloorKey());
			b.PopDictionary();
			HWP::Net::Request(BOSS, b.Build());
		}

		// host: pass a boss kill on to everyone
		void OnBossRequest(uint8 peer, SValue@ data)
		{
			HWP::Net::Broadcast(BOSS, data.Copy());
		}

		// every machine: one boss per floor for a living local mercenary
		void OnBoss(SValue@ data)
		{
			auto rec = GetLocalPlayerRecord();
			if (!IsMerc(rec) || IsFallen(rec))
				return;
			string key = HWP::SV::Str(data, "k", "");
			auto bag = Bag(rec);
			if (key == "" || key != FloorKey() || bag.GetString("merc.boss_key") == key || !IsBossFloor())
				return;
			bag.SetString("merc.boss_key", key);
			AddPrestige(rec, "merc.bosses", 1);
		}

		// ---- falling ---------------------------------------------------------------

		string Clean(const string &in s, uint maxLen = 40)
		{
			string r = s.length() > maxLen ? s.substr(0, maxLen) : s;
			return strReplace(strReplace(r, "|", "/"), "\n", " ");
		}

		string ClassName(PlayerRecord@ rec)
		{
			return rec.playerClass is null ? "?" : Resources::GetString(rec.playerClass.m_name);
		}

		// The ledger of the fallen, newest first, one name|class|level|rank|prestige|where
		// line per mercenary, in the local player's own town. A fall on a floor
		// leaves its line on the character and the next town moves it here.
		void FlushLedger(PlayerRecord@ rec)
		{
			auto bag = Bag(rec);
			string entry = bag.GetString("merc.ledger_pending");
			if (entry == "")
				return;
			auto town = HWP::SaveData::MyTownForWrite();
			auto lines = town.GetString("merc.ledger").split("\n");
			string ledger = entry;
			for (uint i = 0; i < lines.length() && i + 1 < LEDGER_MAX; i++)
				if (lines[i] != "")
					ledger += "\n" + lines[i];
			town.SetString("merc.ledger", ledger);
			bag.Remove("merc.ledger_pending");
		}

		void Fall(PlayerRecord@ rec, const string &in where)
		{
			auto bag = Bag(rec);
			if (bag.GetBool("merc.dead"))
				return;
			int prestige = Prestige(rec);
			int rank = RankOf(prestige);
			bag.SetBool("merc.dead", true);
			bag.SetString("merc.fell", where);

			// the ledger entry waits on the character until the town is loaded
			bag.SetString("merc.ledger_pending", Clean(rec.name) + "|" + Clean(ClassName(rec)) + "|" + int(rec.level) + "|" + rank + "|" + prestige + "|" + Clean(where, 80));
			if (InTown())
				FlushLedger(rec);

			rec.RefreshModifiers();
			HWP::Log("mercenary", rec.name + " fell (" + where + "), rank " + rank + ", prestige " + prestige);

			SValueBuilder b;
			b.PushDictionary();
			b.PushString("n", Clean(rec.name));
			b.PushString("r", RankName(rank));
			b.PushInteger("l", rec.level);
			b.PushString("c", Clean(ClassName(rec)));
			b.PopDictionary();
			HWP::Net::Request(FALLEN, b.Build());
		}

		void OnFallenRequest(uint8 peer, SValue@ data)
		{
			HWP::Net::Broadcast(FALLEN, data.Copy());
		}

		void OnFallen(SValue@ data)
		{
			Reply(Resources::GetString(".hwp.mercenary.fallen", {
				{ "name", Clean(HWP::SV::Str(data, "n", "?")) },
				{ "rank", Clean(HWP::SV::Str(data, "r", "?")) },
				{ "level", HWP::SV::Int(data, "l", 0) },
				{ "class", Clean(HWP::SV::Str(data, "c", "?")) } }));
		}

		bool Revivable() { return HWP::Settings::GetBool("mercenary.revivable", false); }

		// a mission floor: a living mercenary that dies falls (unless revivable;
		// then "merc.down" remembers it for a run that is abandoned while down)
		void WatchDeath()
		{
			auto rec = GetLocalPlayerRecord();
			if (!IsMerc(rec) || !InMission())
			{
				g_wasDead = false;
				return;
			}
			bool dead = rec.IsDead();
			if (IsFallen(rec))
			{
				// a fallen mercenary cannot play on: one that is alive here
				// (revived by the party, or brought into a mission) dies again
				if (!dead && rec.actor !is null)
				{
					HWP::Log("mercenary", "fallen mercenary " + rec.name + " is alive on a floor, killing it");
					rec.actor.Kill(null, 0);
				}
				g_wasDead = dead;
				return;
			}
			if (dead != g_wasDead && Revivable())
				Bag(rec).SetBool("merc.down", dead);
			if (dead && !g_wasDead && !Revivable())
				Fall(rec, FloorName(MissionManager::g_module.m_missionDefHash, int(MissionManager::g_module.m_missionLevelIndex)));
			g_wasDead = dead;
		}

		// The run's end state as the town loads the character (PlayerRecordLoad):
		// the town's MissionEndMenu clears it before Start runs.
		MissionManager::MissionState g_loadState = MissionManager::MissionState::None;
		string g_loadKey;

		// back in town from a failed run (the revivable rule, or a fall the
		// floor did not see), or with revivable on, from a run abandoned while down
		void CheckFailedRun(PlayerRecord@ rec)
		{
			auto state = g_loadState;
			g_loadState = MissionManager::MissionState::None;
			if (!IsMerc(rec) || IsFallen(rec))
				return;
			auto bag = Bag(rec);
			bool down = bag.GetBool("merc.down");
			bag.Remove("merc.down");
			bool failed = state == MissionManager::MissionState::Failed
				|| (state == MissionManager::MissionState::Aborted && Revivable() && down);
			if (!failed || bag.GetString("merc.failed_key") == g_loadKey)
				return;
			bag.SetString("merc.failed_key", g_loadKey);
			Fall(rec, FloorName(rec.currMission, -1) + (state == MissionManager::MissionState::Failed ? " (run failed)" : " (run abandoned)"));
		}

		void OnRecordLoad(PlayerRecord@ rec)
		{
			if (rec is null || !rec.local)
				return;
			g_loadState = rec.currMissionState;
			g_loadKey = "" + rec.currMission + ":" + rec.currMissionRewardSeed;
		}

		bool BlockingWindowOpen()
		{
			auto gm = cast<BaseGameMode>(g_gameMode);
			if (gm is null || gm.m_windowManager is null)
				return true;
			auto windows = gm.m_windowManager.m_objects;
			for (uint i = 0; i < windows.length(); i++)
			{
				if (cast<MissionEndMenu>(windows[i]) !is null || cast<PickCharacterWindow>(windows[i]) !is null
					|| cast<CreateCharacterWindow>(windows[i]) !is null || cast<DeadMenu>(windows[i]) !is null)
					return true;
			}
			return false;
		}

		// a fallen mercenary cannot start a run: its mission setup closes
		bool CloseLoadout()
		{
			auto gm = cast<BaseGameMode>(g_gameMode);
			if (gm is null || gm.m_windowManager is null)
				return false;
			auto windows = gm.m_windowManager.m_objects;
			for (uint i = 0; i < windows.length(); i++)
			{
				auto loadout = cast<MissionLoadoutMenu>(windows[i]);
				if (loadout is null)
					continue;
				gm.m_windowManager.CloseWindow(loadout);
				return true;
			}
			return false;
		}

		// town: a fallen mercenary cannot be played, the picker comes back up
		void EnforceFallen(int ms)
		{
			if (InTown() && IsFallen(GetLocalPlayerRecord()) && CloseLoadout())
			{
				HWP::Log("mercenary", "closed the mission setup of a fallen mercenary");
				g_pickerMs = 0;
			}
			if (!InTown() || !IsFallen(GetLocalPlayerRecord()) || BlockingWindowOpen())
			{
				g_pickerMs = PICKER_DELAY_MS;
				return;
			}
			g_pickerMs -= ms;
			if (g_pickerMs > 0)
				return;
			g_pickerMs = PICKER_DELAY_MS;
			auto rec = GetLocalPlayerRecord();
			Reply(Resources::GetString(".hwp.mercenary.pick_another", { { "name", Clean(rec.name) } }));
			HWP::Log("mercenary", "fallen mercenary " + rec.name + " in town, opening the character picker");
			GlobalCache::Set("main_pick_character", "1");
		}

		// ---- enlisting ---------------------------------------------------------------

		// another character of this class at the unlock level
		bool HasVeteran(PlayerRecord@ rec, int unlock)
		{
			if (rec.playerClass is null)
				return false;
			UnitPtr u;
			auto characters = PersistentSaves::GetCharacterList();
			for (uint c = 0; c < characters.length(); c++)
			{
				if (characters[c] == 0 || characters[c] == rec.uniqueKey)
					continue;
				SValue@ data = PersistentSaves::GetCharacter(characters[c]);
				if (data is null)
					continue;
				if (GetParamString(u, data, "class", false, "") == rec.playerClass.m_id && GetParamInt(u, data, "level", false, 1) >= unlock)
					return true;
			}
			return false;
		}

		void Enlist(PlayerRecord@ rec)
		{
			auto bag = Bag(rec);
			bag.SetBool("merc.on", true);
			bag.SetBool("merc.dead", false);
			bag.SetInt("merc.floors", 0);
			bag.SetInt("merc.bosses", 0);
			bag.SetInt("merc.rank", 0);
			bag.SetInt("merc.ngp0", rec.ngp);

			int target = clamp(HWP::Settings::GetInt("mercenary.start_level", START_LEVEL), 1, rec.GetLevelCap());
			for (int i = 0; i < 100 && rec.level < target; i++) // as cht_levelup
			{
				int level = rec.level;
				rec.GiveExperience(int(rec.LevelExperience(level) - rec.LevelExperience(level - 1)), true);
			}
			rec.RefreshModifiers();
			auto gm = cast<AGameplayGameMode>(g_gameMode);
			if (gm !is null)
				gm.SavePlayerAndTown();
			HWP::Log("mercenary", rec.name + " enlisted at level " + int(rec.level));
			Reply(Resources::GetString(".hwp.mercenary.enlisted", { { "name", Clean(rec.name) }, { "level", int(rec.level) }, { "rank", RankName(0) }, { "bonus", BonusPercent(0) } }));
		}

		// ---- commands ------------------------------------------------------------------

		void CmdMerc(array<string>@ args)
		{
			string sub = args.length() > 0 ? args[0] : "";
			auto rec = GetLocalPlayerRecord();
			if (rec is null || rec.playerClass is null)
			{
				Reply("no character loaded");
				return;
			}
			auto bag = Bag(rec);

			if (sub == "enlist")
			{
				bool force = args.find("force") >= 0;
				if (force && !HWP::Cheats::On())
					return;
				if (IsMerc(rec))
					Reply(rec.name + " is already a mercenary");
				else if (!InTown())
					Reply("enlist in town");
				else if (rec.level > 1)
					Reply("only a fresh level-1 character can enlist (" + rec.name + " is level " + int(rec.level) + ")");
				else if (!force && !HasVeteran(rec, HWP::Settings::GetInt("mercenary.unlock_level", UNLOCK_LEVEL)))
					Reply(Resources::GetString(".hwp.mercenary.locked", { { "level", HWP::Settings::GetInt("mercenary.unlock_level", UNLOCK_LEVEL) }, { "class", ClassName(rec) } }));
				else if (args.find("confirm") < 0)
					Reply(Resources::GetString(".hwp.mercenary.confirm", { { "level", clamp(HWP::Settings::GetInt("mercenary.start_level", START_LEVEL), 1, rec.GetLevelCap()) } }));
				else
					Enlist(rec);
				return;
			}

			if (sub == "ledger")
			{
				auto lines = HWP::SaveData::MyTown().GetString("merc.ledger").split("\n");
				int shown = 0;
				for (uint i = 0; i < lines.length(); i++)
				{
					auto f = lines[i].split("|");
					if (f.length() < 6)
						continue;
					if (shown == 0)
						Reply("Ledger of the fallen:");
					Reply("- " + f[0] + ", " + RankName(parseInt(f[3])) + ", level " + f[2] + " " + f[1] + ", " + f[4] + " prestige, fell in " + f[5]);
					shown++;
				}
				if (shown == 0)
					Reply("the ledger of the fallen is empty");
				return;
			}

			// cheats, for testing
			if (sub == "prestige" || sub == "fall" || sub == "revive")
			{
				if (!HWP::Cheats::On())
					return;
				if (!IsMerc(rec))
				{
					Reply(rec.name + " is not a mercenary");
					return;
				}
				if (sub == "prestige")
					AddPrestige(rec, "merc.floors", args.length() > 1 ? parseInt(args[1]) : 50);
				else if (sub == "fall")
					Fall(rec, "a console command");
				else
				{
					bag.SetBool("merc.dead", false);
					rec.RefreshModifiers();
					Reply(rec.name + " is back from the dead");
				}
				return;
			}

			if (sub != "")
			{
				Reply("usage: hwp merc [enlist [confirm] | ledger]");
				return;
			}
			if (!IsMerc(rec))
			{
				Reply(Resources::GetString(".hwp.mercenary.not_merc", { { "name", Clean(rec.name) }, { "level", HWP::Settings::GetInt("mercenary.unlock_level", UNLOCK_LEVEL) } }));
				return;
			}
			int prestige = Prestige(rec);
			int rank = RankOf(prestige);
			string next = rank + 1 < int(RANK_POINTS.length()) ? ", next " + RankName(rank + 1) + " at " + RANK_POINTS[rank + 1] : "";
			Reply(rec.name + ": mercenary " + RankName(rank) + (IsFallen(rec) ? " (FALLEN in " + bag.GetString("merc.fell") + ")" : "")
				+ ", " + prestige + " prestige" + next + "; " + bag.GetInt("merc.floors") + " floor(s), " + bag.GetInt("merc.bosses")
				+ " boss(es); +" + BonusPercent(rank) + "% gold and experience (now: gold gain x"
				+ formatFloat(rec.GetMaterialModifier(MaterialType::Gold), "", 0, 2) + ", experience x" + formatFloat(rec.currStats.ExperienceMul, "", 0, 2) + ")");
		}
	}
}

namespace HWPMercenary
{
	[Hook]
	void PlayerKilledActor(Player@ player, Actor@ killed, DamageInfo@ di)
	{
		HWP::Mercenary::OnKill(player, killed);
	}

	[Hook]
	void PlayerRecordLoad(PlayerRecord@ record, SValue@ data)
	{
		HWP::Mercenary::OnRecordLoad(record);
	}

	// the rank bonus, on the local living mercenary (gold and experience are
	// given on the owner's machine)
	[Hook]
	void PlayerRecordRefreshModifiers(PlayerRecord@ record)
	{
		if (record is null || !record.local || !HWP::Mercenary::IsMerc(record) || HWP::Mercenary::IsFallen(record))
			return;
		int rank = HWP::Mercenary::RankOf(HWP::Mercenary::Prestige(record));
		if (HWP::Mercenary::g_provider is null)
			@HWP::Mercenary::g_provider = ModifierProvider(Resources::GetString(".hwp.mercenary.provider"));
		record.modifiers.AddModifiers(HWP::Mercenary::RankModifiers(rank), 1.0f, HWP::Mercenary::g_provider);
	}
}

namespace Modules
{
	class HWPMercenaryModule : Module, HWP::ModuleStart
	{
		HWPMercenaryModule()
		{
			super("hwp-mercenary");
			HWP::Settings::Sync("mercenary.");
			HWP::Net::OnRequest(HWP::Mercenary::FALLEN, HWP::Net::RequestHandler(HWP::Mercenary::OnFallenRequest));
			HWP::Net::OnEvent(HWP::Mercenary::FALLEN, HWP::Net::EventHandler(HWP::Mercenary::OnFallen));
			HWP::Net::OnRequest(HWP::Mercenary::BOSS, HWP::Net::RequestHandler(HWP::Mercenary::OnBossRequest));
			HWP::Net::OnEvent(HWP::Mercenary::BOSS, HWP::Net::EventHandler(HWP::Mercenary::OnBoss));
			HWP::Commands::Register("merc", " [enlist [confirm] | ledger] mercenary mode: permadeath, prestige ranks (cheats: prestige <n> | fall | revive)", HWP::Commands::Handler(HWP::Mercenary::CmdMerc));
		}

		void Start(StartMode sMode)
		{
			HWP::Mercenary::g_pickerMs = HWP::Mercenary::PICKER_DELAY_MS;
			auto rec = GetLocalPlayerRecord();
			HWP::Mercenary::g_wasDead = rec !is null && rec.IsDead();
			if (!HWP::Mercenary::IsMerc(rec))
				return;
			// the bag loads after the record's own RefreshModifiers: the rank bonus needs another
			rec.RefreshModifiers();
			if (HWP::Mercenary::InTown())
			{
				HWP::Mercenary::CheckFailedRun(rec);
				HWP::Mercenary::FlushLedger(rec);
			}
			else if (HWP::Mercenary::IsFallen(rec))
				HWP::Mercenary::Reply(Resources::GetString(".hwp.mercenary.fallen_here", { { "name", HWP::Mercenary::Clean(rec.name) } }));
			else if (HWP::Mercenary::InMission())
				HWP::Mercenary::CountFloor(rec);
			HWP::Mercenary::CheckRank(rec);
		}

		void UpdateFrame(int ms, GameInput& gameInput, MenuInput& menuInput, bool paused) override
		{
			HWP::Mercenary::WatchDeath();
			HWP::Mercenary::EnforceFallen(ms);
		}
	}
}
