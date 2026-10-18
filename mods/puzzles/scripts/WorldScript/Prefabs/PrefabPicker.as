// HWP puzzles: wholesale override of the vanilla PrefabPicker (the .orig next to
// this file is the base copy). The only change: in a puzzle room big enough for
// it (one that can also pick a large vanilla puzzle, see HWP::Puzzles::BIG),
// HoH1's Constellation (prefabs/puzzles/hwp/puzzle_constellation.pfb) joins the
// candidates with weight puzzles.constellation (default 10, the vanilla weight
// of each candidate; 0 turns it off). Everything else is the vanilla pick.
namespace HWP
{
	namespace Puzzles
	{
		const string CONSTELLATION = "prefabs/puzzles/hwp/puzzle_constellation.pfb";

		// rooms offering one of these have the floor space for the 96x146 constellation
		const array<string> BIG = {
			"prefabs/puzzles/puzzle_chance/puzzle_chance.pfb",
			"prefabs/puzzles/maze_path/maze_path.pfb",
			"prefabs/puzzles/puzzle_memory_big.pfb",
			"prefabs/puzzles/puzzle_lights_out_big.pfb"
		};

		array<Prefab@> g_big;

		bool IsBig(Prefab@ prefab)
		{
			if (g_big.length() == 0)
			{
				for (uint i = 0; i < BIG.length(); i++)
				{
					auto pfb = Resources::GetPrefab(BIG[i]);
					if (pfb !is null)
						g_big.insertLast(pfb);
				}
			}
			for (uint i = 0; i < g_big.length(); i++)
			{
				if (g_big[i] is prefab)
					return true;
			}
			return false;
		}
	}
}

namespace WorldScript
{
	[WorldScript color="50 127 255" icon="system/icons.png;448;224;32;32"]
	class PrefabPicker
	{
		vec3 Position;

		[Editable validation=IsPickedPrefab]
		UnitFeed PickedPrefabs;


		bool IsPickedPrefab(UnitPtr unit)
		{
			return cast<PickedPrefab>(unit.GetScriptBehavior()) !is null;
		}

		SValue@ ServerExecute()
		{
			array<PickedPrefab@> scripts;

			int totChance = 0;
			bool big = false;
			auto pfbs = PickedPrefabs.FetchAll();
			for (uint i = 0; i < pfbs.length(); i++)
			{
				WorldScript@ script = WorldScript::GetWorldScript(pfbs[i]);
				if (script !is null && script.CanExecuteNow())
				{
					auto prefab = cast<PickedPrefab>(pfbs[i].GetScriptBehavior());
					if (prefab.Prefab is null)
						continue;

					if (prefab.Flag == "" || !g_flags.IsSet(prefab.Flag))
					{
						scripts.insertLast(prefab);
						totChance += prefab.Chance;
						if (HWP::Puzzles::IsBig(prefab.Prefab))
							big = true;
					}
				}
			}

			// HWP: the constellation as one more candidate, after the vanilla ones
			// (once per floor, like the flagged vanilla picks)
			int hwpChance = 0;
			Prefab@ hwpPrefab;
			if (big && !g_flags.IsSet(HWP::Puzzles::CONSTELLATION_FLAG))
			{
				hwpChance = max(0, HWP::Settings::GetInt("puzzles.constellation", 10));
				if (hwpChance > 0)
					@hwpPrefab = Resources::GetPrefab(HWP::Puzzles::CONSTELLATION);
				if (hwpPrefab is null)
					hwpChance = 0;
			}

			if (scripts.length() <= 0)
				return null;

			int n = randi(totChance + hwpChance);
			if (hwpChance > 0 && n >= totChance)
			{
				HWP::Log("puzzles", "constellation picked (" + scripts.length() + " vanilla candidates)");
				g_flags.Set(HWP::Puzzles::CONSTELLATION_FLAG, FlagState::Level);
				hwpPrefab.Fabricate(g_scene, Position);
				return null;
			}
			if (hwpChance > 0)
				HWP::Log("puzzles", "constellation offered, vanilla puzzle picked");

			for (uint i = 0; i < scripts.length(); i++)
			{
				n -= scripts[i].Chance;
				if (n < 0)
				{
					if (scripts[i].Flag != "")
						g_flags.Set(scripts[i].Flag, FlagState::Level);

					scripts[i].Prefab.Fabricate(g_scene, Position);
					WorldScript::GetWorldScript(g_scene, scripts[i]).Execute();
					break;
				}
			}

			return null;
		}
	}
}
