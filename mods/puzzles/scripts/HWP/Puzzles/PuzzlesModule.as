// HWP puzzles: puzzle rooms back in the dungeons, plus HoH1's Constellation.
//
// HoH2 ships 88 puzzle rooms (prefabs/<biome>/special/puzzle_room_*, theme
// <biome>_puzzle in tweak/missions/prefabs/<biome>_special.sval) but no theme
// places them: temple and crypt have the SpawnPrefabSet commented out, cave_dark
// and barracks ask for "<biome>_puzzles", a set no prefab is in, and the rest
// never mention them. The mission defs, and with them each level's generator,
// are rebuilt on every level load, before any module, so the module ctor
// (every level, ahead of MissionGameMode.Generate) adds one PuzzleRoomSpawn to
// every level generator: at most one room a floor, skipped on no_special floors
// like the shrine and skill rooms, and placed after those so a puzzle room never
// takes the space a mandatory room needs. Its chance is puzzles.room_chance
// percent (default 60), rolled in Execute: the settings live in the town record,
// which Generate loads after the module ctor has run.
//
// A room first tries the vanilla way (a spot whose cells already match its
// pattern: a solid wall block with a corridor end at its door). Most floors have
// no such spot, so then it is forced onto the map's outskirts: the free wall
// block farthest from the middle whose door can reach the level, by a straight
// corridor carved through solid wall, in under MAX_CORRIDOR cells. DungeonBrush
// paints tiles from the cells, so the corridor and the room's frame look like
// the rest of the floor.
//
// Biomes without puzzle rooms borrow a near one (cave_spider: cave_dark).
// Forest and heaven floors (ForestBrush) are one authored prefab and paint
// nothing from the cells, so they have no wall to carve a room into. They get
// the Constellation in an open clearing instead (set hwp_puzzle_open,
// tweak/missions/hwp_puzzles_open.sval: walkable all over, reserved as floor),
// placed the vanilla way before the forest's edges and fillers take the space.
// The keep is an OutdoorGenerator as well, but its DungeonInstanceBrush paints
// from the cells like any dungeon.
//
// The Constellation itself joins the larger rooms' picks in the PrefabPicker
// override (scripts/WorldScript/Prefabs/PrefabPicker.as).
namespace HWP
{
	namespace Puzzles
	{
		const int ROOM_CHANCE = 60;    // percent a floor
		const int MAX_CORRIDOR = 40;   // cells
		const string CONSTELLATION_FLAG = "hwp_constellation_placed";
		const string OPEN_SET = "hwp_puzzle_open";   // tweak/missions/hwp_puzzles_open.sval

		// themes (theme_<biome>, theme_generic_<biome>) with a <biome>_puzzle prefab set
		const array<string> ROOM_BIOMES = {
			"barracks", "cave_dark", "cave_light", "cave_light_inhabited", "courts",
			"crypt", "dark_halls", "dungeon", "keep", "prison", "temple"
		};

		string Biome(MissionThemeDef@ theme)
		{
			if (theme is null)
				return "";
			string biome = theme.m_id;
			if (biome.findFirst("theme_") != 0)
				return "";
			biome = biome.substr(6);
			if (biome.findFirst("generic_") == 0)
				biome = biome.substr(8);
			return biome;
		}

		string RoomSet(MissionThemeDef@ theme)
		{
			string biome = Biome(theme);
			if (biome == "cave_spider")
				biome = "cave_dark";
			if (ROOM_BIOMES.find(biome) < 0)
				return "";
			return biome + "_puzzle";
		}

		int RoomChance()
		{
			return clamp(HWP::Settings::GetInt("puzzles.room_chance", ROOM_CHANCE), 0, 100);
		}

		bool Walkable(CellGrid@ grid, int x, int y)
		{
			Cell c = grid.GetCell(x, y);
			return c == Cell::Floor || c == Cell::Breakables || c == Cell::Bridge;
		}

		// a cell the room or its corridor may take: in the grid, not consumed, not floor
		bool Free(CellGrid@ grid, int x, int y)
		{
			if (grid.IsConsumed(x, y))
				return false;
			Cell c = grid.GetCell(x, y);
			return c == Cell::Wall || c == Cell::Nothing || c == Cell::Cliff;
		}

		// the room's door: the junction cells on one edge of its pattern, and the way out
		class Door
		{
			ivec2 m_from;    // first door cell on the pattern edge
			ivec2 m_along;   // step along the door
			ivec2 m_out;     // step out of the room
			int m_width;
		}

		bool GetDoor(MissionPrefabDef@ def, Door@ door)
		{
			ivec3 j;
			if (def.m_junctionsUp.length() > 0)
			{
				j = def.m_junctionsUp[0];
				door.m_along = ivec2(1, 0);
				door.m_out = ivec2(0, -1);
			}
			else if (def.m_junctionsDown.length() > 0)
			{
				j = def.m_junctionsDown[0];
				door.m_along = ivec2(1, 0);
				door.m_out = ivec2(0, 1);
			}
			else if (def.m_junctionsLeft.length() > 0)
			{
				j = def.m_junctionsLeft[0];
				door.m_along = ivec2(0, 1);
				door.m_out = ivec2(-1, 0);
			}
			else if (def.m_junctionsRight.length() > 0)
			{
				j = def.m_junctionsRight[0];
				door.m_along = ivec2(0, 1);
				door.m_out = ivec2(1, 0);
			}
			else
				return false;
			door.m_width = max(2, j.z);
			door.m_from = ivec2(j.x, j.y) - door.m_along * (door.m_width / 2);
			return true;
		}

		// cells out of the door until the corridor meets the level, or -1
		int CorridorLength(CellGrid@ grid, ivec2 pos, Door@ door)
		{
			ivec2 base = pos + door.m_from;
			for (int k = 1; k <= MAX_CORRIDOR; k++)
			{
				bool all = true;
				for (int w = 0; w < door.m_width; w++)
				{
					ivec2 c = base + door.m_out * k + door.m_along * w;
					if (!Walkable(grid, c.x, c.y))
					{
						all = false;
						if (!Free(grid, c.x, c.y))
							return -1;
					}
				}
				if (all)
					return k;
			}
			return -1;
		}

		// summed-area table of the cells a room may not take (not Free)
		array<array<int>>@ BlockedSums(CellGrid@ grid)
		{
			int w = grid.m_width;
			int h = grid.m_height;
			array<array<int>> s(w + 1, array<int>(h + 1, 0));
			for (int x = 0; x < w; x++)
				for (int y = 0; y < h; y++)
					s[x + 1][y + 1] = (Free(grid, x, y) ? 0 : 1) + s[x][y + 1] + s[x + 1][y] - s[x][y];
			return s;
		}

		int Blocked(array<array<int>>@ s, int x, int y, int w, int h)
		{
			return s[x + w][y + h] - s[x][y + h] - s[x + w][y] + s[x][y];
		}

		// a def the set may still give out: CanGet (max count, conditionals, run-unique
		// flags), minus the failed PlacePrefabs' m_foundNoPlacement, which only says
		// the vanilla spot search found nothing
		bool Available(MissionPrefabDef@ def)
		{
			// CanGet clears the flag itself on a def's first look in a new generation
			// (MissionPrefabDef.as:71-76); a flag from an earlier level must not come back
			bool current = def.m_currGenNumId == g_genNumId;
			bool none = def.m_foundNoPlacement;
			def.m_foundNoPlacement = false;
			bool ok = def.CanGet();
			if (current)
				def.m_foundNoPlacement = none;
			return ok;
		}

		class Spot
		{
			MissionPrefabDef@ m_def;
			ivec2 m_pos;
			Door m_door;
			int m_len;
			float m_score;
		}

		// a def's best spot on the grid: the farthest from the middle, a short corridor
		// breaking ties; null if none fits
		Spot@ BestSpot(CellGrid@ grid, array<array<int>>@ sums, MissionPrefabDef@ def)
		{
			def.UnpackGrid();
			Door door;
			if (def.m_gridPattern is null || !GetDoor(def, door))
				return null;
			float cx = grid.m_width / 2.0f;
			float cy = grid.m_height / 2.0f;
			Spot@ best = null;
			ivec2 sz = def.m_gridSz;
			for (int y = 1; y + sz.y < grid.m_height - 1; y++)
			{
				for (int x = 1; x + sz.x < grid.m_width - 1; x++)
				{
					if (Blocked(sums, x, y, sz.x, sz.y) > 0)
						continue;
					int len = CorridorLength(grid, ivec2(x, y), door);
					if (len < 0)
						continue;
					float dx = (x + sz.x / 2.0f - cx) / cx;
					float dy = (y + sz.y / 2.0f - cy) / cy;
					float score = dx * dx + dy * dy - len * 0.01f;
					if (best is null || score > best.m_score)
					{
						if (best is null)
							@best = Spot();
						@best.m_def = def;
						best.m_pos = ivec2(x, y);
						best.m_door = door;
						best.m_len = len;
						best.m_score = score;
					}
				}
			}
			return best;
		}

		// the vanilla way failed: put the room on the outskirts and carve its corridor
		string ForcePlace(CellGrid@ grid, PrefabPlacement@ placer, const string &in set)
		{
			uint setHash = HashString(set);
			array<MissionPrefabDef@> defs;
			for (uint i = 0; i < MissionPrefabDef::Instances.length(); i++)
			{
				auto def = MissionPrefabDef::Instances[i];
				if (def.m_set == setHash && def.m_prefab !is null && Available(def))
					defs.insertAt(randi(defs.length() + 1), def);
			}
			if (defs.length() == 0)
				return "no rooms left in " + set;

			auto sums = BlockedSums(grid);

			// each def's best spot. UsePrefab may hand back any of the def's variations, whose
			// size or door can differ, and it uses the room up (count, run flags) as it does: a
			// def is only a candidate when every variation has a spot of its own too
			array<Spot@> spots;
			for (uint i = 0; i < defs.length(); i++)
			{
				auto best = BestSpot(grid, sums, defs[i]);
				if (best is null)
					continue;
				bool all = true;
				for (uint v = 0; v < defs[i].m_variations.length() && all; v++)
					all = BestSpot(grid, sums, defs[i].m_variations[v]) !is null;
				if (all)
					spots.insertLast(best);
			}
			if (spots.length() == 0)
				return "no free wall block on the outskirts";

			// best first; a def UsePrefab turns down (used up meanwhile) passes to the next
			MissionPrefabDef@ room = null;
			Spot@ spot = null;
			while (room is null && spots.length() > 0)
			{
				uint top = 0;
				for (uint i = 1; i < spots.length(); i++)
					if (spots[i].m_score > spots[top].m_score)
						top = i;
				@spot = spots[top];
				spots.removeAt(top);
				@room = spot.m_def.UsePrefab();
			}
			if (room is null)
				return "every fitting room used up";
			// a variation gets its own spot (the def's could overlap or face a wall); the
			// candidate check above made sure it has one
			if (room !is spot.m_def)
			{
				@spot = BestSpot(grid, sums, room);
				if (spot is null)
					return "variation " + room.m_id + " has no free wall block on the outskirts";
			}
			ivec2 bestPos = spot.m_pos;
			Door@ bestDoor = spot.m_door;
			int bestLen = spot.m_len;
			room.UnpackGrid();
			placer.PlacePrefabAt(room, bestPos);

			// the doorway cells the pattern wants walkable, then the corridor out
			for (int y = 0; y < room.m_gridSz.y; y++)
				for (int x = 0; x < room.m_gridSz.x; x++)
					if (Pattern(room.m_gridPattern[y * room.m_gridSz.x + x]) == Pattern::Walkable)
						grid.SetCellIfNotConsumed(bestPos.x + x, bestPos.y + y, Cell::Floor);
			ivec2 base = bestPos + bestDoor.m_from;
			for (int k = 1; k < bestLen; k++)
			{
				for (int w = 0; w < bestDoor.m_width; w++)
				{
					ivec2 c = base + bestDoor.m_out * k + bestDoor.m_along * w;
					grid.SetCellIfNotConsumed(c.x, c.y, Cell::Floor);
				}
			}
			return "forced " + room.m_id + " at " + bestPos.x + "," + bestPos.y + " of " + grid.m_width + "x" + grid.m_height + ", corridor " + (bestLen - 1);
		}

		// puzzles.debug_grid: the floor's cells in the log, one row a line
		void DumpGrid(CellGrid@ grid)
		{
			for (int y = 0; y < grid.m_height; y++)
			{
				string row = "";
				for (int x = 0; x < grid.m_width; x++)
				{
					Cell c = grid.GetCell(x, y);
					bool used = grid.m_gridConsumed[x][y];
					string ch = "?";
					if (c == Cell::Floor) ch = used ? "o" : ".";
					else if (c == Cell::Wall) ch = used ? "X" : "#";
					else if (c == Cell::Nothing) ch = " ";
					else if (c == Cell::Cliff) ch = "~";
					else if (c == Cell::Breakables) ch = "%";
					row += ch;
				}
				HWP::Log("puzzles", "grid " + formatInt(y, "0", 3) + " " + row);
			}
		}

		// SpawnPrefabSet with the chance read when the level is generated
		class PuzzleRoomSpawn : SpawnPrefabSet
		{
			bool Execute(DungeonBrush@ brush, PrefabPlacement@ pfbPlacer) override
			{
				if (HWP::Settings::GetBool("puzzles.debug_grid"))
					DumpGrid(brush);
				int chance = RoomChance();
				if (randi(100) >= chance)
				{
					HWP::Log("puzzles", m_set + " not rolled (" + chance + "%)");
					return true;
				}
				// an outdoor floor: any open clearing, nothing to carve
				if (m_set == OPEN_SET)
				{
					int placed = pfbPlacer.PlacePrefabs(HashString(m_set), 1, m_numBoost, m_typeMinLimit);
					HWP::Log("puzzles", m_set + " rolled (" + chance + "%): " + (placed > 0 ? "placed in a clearing" : "no open clearing"));
					return true;
				}
				// puzzles.debug_force: skip the vanilla way, so a test lands on the forced one
				int n = 0;
				if (!HWP::Settings::GetBool("puzzles.debug_force"))
					n = pfbPlacer.PlacePrefabs(HashString(m_set), 1, m_numBoost, m_typeMinLimit);
				if (n > 0)
				{
					HWP::Log("puzzles", m_set + " rolled (" + chance + "%): placed in a matching spot");
					return true;
				}
				HWP::Log("puzzles", m_set + " rolled (" + chance + "%): " + ForcePlace(brush, pfbPlacer, m_set));
				return true;
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

		// returns how many generators got the command
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
					if (gen is null)
						continue;
					// ForestBrush paints nothing from the cells; the keep is an
					// OutdoorGenerator too, but its DungeonInstanceBrush does
					bool outdoor = cast<ForestBrush>(gen.m_brush) !is null;
					string set = outdoor ? OPEN_SET : RoomSet(level.m_themeDef);
					if (set == "")
						continue;

					int at = -1;
					bool present = false;
					for (uint k = 0; k < gen.m_genCommands.length(); k++)
					{
						if (cast<PuzzleRoomSpawn>(gen.m_genCommands[k]) !is null)
							present = true;
						auto spawn = cast<SpawnPrefabSet>(gen.m_genCommands[k]);
						if (spawn is null)
							continue;
						if (EndsWith(spawn.m_set, "_shrine") || EndsWith(spawn.m_set, "_skill"))
							at = k + 1;
						// outdoors: right after the first special set (forest_special,
						// heaven_special_arenas_1), before the edges and fillers
						if (outdoor && at < 0 && spawn.m_set.findFirst("_special") >= 0)
							at = k + 1;
					}
					if (present)
						continue;

					PuzzleRoomSpawn cmd;
					array<SValue@> params = { RoomCommandData(set) };
					cmd.LoadParams(params);
					if (at < 0 || uint(at) >= gen.m_genCommands.length())
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
