// HWP puzzles: puzzle rooms back in the dungeons, plus HoH1's Constellation.
//
// HoH2 ships 88 puzzle rooms (prefabs/<biome>/special/puzzle_room_*, theme
// <biome>_puzzle in tweak/missions/prefabs/<biome>_special.sval) but no theme
// places them: temple and crypt have the SpawnPrefabSet commented out, cave_dark
// and barracks ask for "<biome>_puzzles", a set no prefab is in, and the rest
// never mention them. Each mission level's generator is built when the
// missions load, before any module, so the module ctor (every level, ahead of
// MissionGameMode.Generate) adds the command to every dungeon-style generator
// whose theme has puzzle rooms: at most one, skipped on no_special floors like
// the shrine and skill rooms, and placed just before those. Its chance is
// puzzles.room_chance percent (default 33, the commented-out vanilla value),
// rolled in Execute: the settings live in the town record, which Generate
// loads after the module ctor has run.
//
// The Constellation itself joins the larger rooms' picks in the PrefabPicker
// override (scripts/WorldScript/Prefabs/PrefabPicker.as).
namespace HWP
{
	namespace Puzzles
	{
		const int ROOM_CHANCE = 33;   // percent, the vanilla temple/crypt value

		// themes (theme_<biome>, theme_generic_<biome>) with a <biome>_puzzle prefab set
		const array<string> ROOM_BIOMES = {
			"barracks", "cave_dark", "cave_light", "cave_light_inhabited", "cave_spider", "courts",
			"crypt", "dark_halls", "dungeon", "keep", "prison", "temple"
		};

		string RoomSet(MissionThemeDef@ theme)
		{
			if (theme is null)
				return "";
			string biome = theme.m_id;
			if (biome.findFirst("theme_") != 0)
				return "";
			biome = biome.substr(6);
			if (biome.findFirst("generic_") == 0)
				biome = biome.substr(8);
			if (ROOM_BIOMES.find(biome) < 0)
				return "";
			return biome + "_puzzle";
		}

		int RoomChance()
		{
			return clamp(HWP::Settings::GetInt("puzzles.room_chance", ROOM_CHANCE), 0, 100);
		}

		// SpawnPrefabSet with the chance read when the level is generated
		class PuzzleRoomSpawn : SpawnPrefabSet
		{
			bool Execute(DungeonBrush@ brush, PrefabPlacement@ pfbPlacer) override
			{
				int chance = RoomChance();
				if (randi(100) >= chance)
				{
					HWP::Log("puzzles", m_set + " not rolled (" + chance + "%)");
					return true;
				}
				return SpawnPrefabSet::Execute(brush, pfbPlacer);
			}
		}

		SValue@ RoomCommandData(const string &in set)
		{
			SValueBuilder sb;
			sb.PushDictionary();
			sb.PushString("class", "SpawnPrefabSet");
			sb.PushString("theme", set);
			sb.PushInteger("max", 1);
			sb.PushArray("conditionals");
			sb.PushArray();
			sb.PushString("flag");
			sb.PushString("isnt");
			sb.PushString("no_special");
			sb.PopArray();
			sb.PopArray();
			sb.PopDictionary();
			return sb.Build();
		}

		bool EndsWith(const string &in s, const string &in suffix)
		{
			return s.length() >= suffix.length() && s.substr(s.length() - suffix.length()) == suffix;
		}

		// returns how many generators got the command (0 when an earlier level
		// already added it: the generators outlive the level)
		int AddPuzzleRooms()
		{
			int added = 0;
			for (uint i = 0; i < MissionDef::Instances.length(); i++)
			{
				auto mission = MissionDef::Instances[i];
				for (uint j = 0; j < mission.m_levels.length(); j++)
				{
					auto level = mission.m_levels[j];
					auto gen = cast<DungeonGenerator>(level.m_generator);
					string set = RoomSet(level.m_themeDef);
					if (gen is null || set == "")
						continue;

					int at = -1;
					bool present = false;
					for (uint k = 0; k < gen.m_genCommands.length(); k++)
					{
						auto spawn = cast<SpawnPrefabSet>(gen.m_genCommands[k]);
						if (spawn is null)
							continue;
						if (spawn.m_set == set)
							present = true;
						if (at < 0 && (EndsWith(spawn.m_set, "_shrine") || EndsWith(spawn.m_set, "_skill")))
							at = k;
					}
					if (present)
						continue;

					PuzzleRoomSpawn cmd;
					array<SValue@> params = { RoomCommandData(set) };
					cmd.LoadParams(params);
					if (at < 0)
						gen.m_genCommands.insertLast(cmd);
					else
						gen.m_genCommands.insertAt(at, cmd);
					added++;
				}
			}
			return added;
		}
	}
}

namespace Modules
{
	class HWPPuzzlesModule : Module
	{
		HWPPuzzlesModule()
		{
			super("hwp-puzzles");
			int n = HWP::Puzzles::AddPuzzleRooms();
			if (n > 0)
				HWP::Log("puzzles", "puzzle rooms added to " + n + " mission level generator(s)");
		}
	}
}
