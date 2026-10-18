// HoH1's NG+ unit swap (its scripts/UnitMap.as): from NG+ 1, 3, 5 and 10 a
// spawned boss, miniboss or enemy is a harder copy, and the bosses' copies add
// attacks (the Warden's bomb fan, the Vampire's Bat Spray). HoH1 swapped inside
// its spawn scripts; HoH2's are its own, so the swap rewrites their UnitType
// once per level instead. The map is tools/import_hoh1.py's copy of HoH1's
// tweak/dungeons/unitmap_base.sval, limited to the units the levels reach.
namespace HWP
{
	namespace HoH1
	{
		const string UNIT_MAP = "hoh1/tweak/hwp_unitmap.sval";

		class TierStep
		{
			int m_ng;
			UnitProducer@ m_prod;
		}

		class TierEntry
		{
			uint m_hash;
			array<TierStep@> m_steps;
		}

		array<TierEntry@>@ g_unitMap;

		array<TierEntry@>@ UnitMap()
		{
			if (g_unitMap !is null)
				return g_unitMap;
			@g_unitMap = array<TierEntry@>();
			SValue@ sv = Resources::GetSValue(UNIT_MAP);
			if (sv is null || sv.GetType() != SValueType::Array)
				return g_unitMap;
			auto entries = sv.GetArray();
			for (uint i = 0; i < entries.length(); i++)
			{
				if (entries[i].GetType() != SValueType::Dictionary)
					continue;
				auto base = Resources::GetUnitProducer(GetParamString(UnitPtr(), entries[i], "unit", false));
				auto ngs = GetParamArray(UnitPtr(), entries[i], "ngs", false);
				if (base is null || ngs is null)
					continue;
				auto entry = TierEntry();
				entry.m_hash = base.GetResourceHash();
				for (uint j = 0; j + 1 < ngs.length(); j += 2)
				{
					auto step = TierStep();
					step.m_ng = ngs[j].GetInteger();
					@step.m_prod = Resources::GetUnitProducer(ngs[j + 1].GetString());
					if (step.m_prod !is null)
						entry.m_steps.insertLast(step);
				}
				if (entry.m_steps.length() > 0)
					g_unitMap.insertLast(entry);
			}
			return g_unitMap;
		}

		// the copy for this NG+ (the base below the first threshold, or if unmapped)
		UnitProducer@ TierFor(UnitProducer@ prod)
		{
			if (prod is null)
				return null;
			auto entries = UnitMap();
			uint hash = prod.GetResourceHash();
			int ngp = int(g_ngp);
			for (uint i = 0; i < entries.length(); i++)
			{
				if (entries[i].m_hash != hash)
					continue;
				UnitProducer@ cur = prod;
				for (uint j = 0; j < entries[i].m_steps.length(); j++)
				{
					if (ngp >= entries[i].m_steps[j].m_ng)
						@cur = entries[i].m_steps[j].m_prod;
				}
				return cur;
			}
			return prod;
		}

		// Swap the loaded level's spawn scripts; a second call finds nothing left
		// to swap. Returns how many changed.
		int ApplyUnitMap()
		{
			if (UnitMap().length() == 0)
				return 0;
			int swapped = 0;
			array<string> types = { "SpawnUnit", "SpawnUnitWithEffect", "SpawnDropUnit" };
			for (uint t = 0; t < types.length(); t++)
			{
				auto res = g_scene.FetchAllWorldScripts(types[t]);
				for (uint i = 0; i < res.length(); i++)
				{
					auto behavior = res[i].GetUnit().GetScriptBehavior();
					auto spawn = cast<SpawnUnitBase>(behavior);
					auto drop = cast<WorldScript::SpawnDropUnit>(behavior);
					UnitProducer@ prod = spawn !is null ? spawn.UnitType : (drop !is null ? drop.UnitType : null);
					UnitProducer@ tier = TierFor(prod);
					if (tier is prod)
						continue;
					if (spawn !is null)
						@spawn.UnitType = tier;
					else
						@drop.UnitType = tier;
					swapped++;
				}
			}
			if (swapped > 0)
				HWP::Log("campaign", "NG+" + int(g_ngp) + ": " + swapped + " HoH1 spawn units swapped for their tier copies");
			return swapped;
		}
	}
}
