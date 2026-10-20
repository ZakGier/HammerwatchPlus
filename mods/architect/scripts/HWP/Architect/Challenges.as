// HWP architect challenges: Heroes of Hammerwatch 1's "bad wishes" as free
// Architect alterations (tweak/hwp/architect_challenges.sval). They have no
// cost of their own; instead each one takes a fixed amount of gold and one
// material off the alterations you buy (DISCOUNT_*), shown in red in the
// picker's cost column. A material's total stops at 0: a run can become free,
// never profitable.
//
// Most challenges are plain modifiers on the mission buff. The two that change
// the level (Crowded Halls, Champions) are applied by ChallengeSetup, which the
// module ctor wraps around the first unconditional generation command of every
// dungeon generator: MissionGameMode.Generate loads the run's architect picks
// (LoadFlags) before it runs the generator, and the enemy placer it tunes is
// what both generation and the start-of-level EnemyPlacement spawns read.
// Wrapping instead of inserting keeps the generator's randf() per command, and
// so vanilla's levels for a seed, unchanged.
namespace HWP
{
	namespace Architect
	{
		const float CROWDED_DENSITY = 1.35f;

		// id -> discount: DISCOUNT_GOLD gold and DISCOUNT_MAT of DISCOUNT_TYPE
		const array<string> CHALLENGES = {
			"hwp_challenge_crowded", "hwp_challenge_champions", "hwp_challenge_lean_pickups",
			"hwp_challenge_bitter_draughts", "hwp_challenge_glass_bones", "hwp_challenge_sharp_traps",
			"hwp_challenge_slim_pickings"
		};
		const array<int> DISCOUNT_GOLD = { 1500, 1500, 1000, 1000, 2500, 1000, 1500 };
		const array<int> DISCOUNT_TYPE = {
			int(MaterialType::Stone), int(MaterialType::Wood), int(MaterialType::Wood),
			int(MaterialType::Stone), int(MaterialType::Stone), int(MaterialType::Wood),
			int(MaterialType::Wood)
		};
		const array<int> DISCOUNT_MAT = { 10, 10, 5, 5, 15, 5, 10 };

		array<uint> g_challengeHashes;

		// index into CHALLENGES, -1 when the id is not an HWP challenge
		int ChallengeIndex(uint id)
		{
			if (g_challengeHashes.length() == 0)
			{
				for (uint i = 0; i < CHALLENGES.length(); i++)
					g_challengeHashes.insertLast(HashString(CHALLENGES[i]));
			}
			return g_challengeHashes.find(id);
		}

		// what a challenge takes off the bill, as a positive cost; null for anything else
		ShopCost@ ChallengeDiscount(uint id)
		{
			int i = ChallengeIndex(id);
			if (i < 0)
				return null;
			auto cost = ShopCost(MaterialType::Gold, DISCOUNT_GOLD[i]);
			cost.AddCost(MaterialType(DISCOUNT_TYPE[i]), DISCOUNT_MAT[i]);
			return cost;
		}

		// the picker's cost column for a challenge: "-1.5k gold  -10 stone" in red
		// (gold in thousands: "-1500" runs off the row's right edge)
		string DiscountText(uint id)
		{
			int i = ChallengeIndex(id);
			if (i < 0)
				return "";
			int g = DISCOUNT_GOLD[i];
			string gold = "-" + (g / 1000) + (g % 1000 >= 100 ? "." + ((g % 1000) / 100) : "") + "k";
			string mat = DISCOUNT_TYPE[i] == int(MaterialType::Stone) ? ".tab.overlay.player.stone" : ".tab.overlay.player.wood";
			return "\\cff5050" + Resources::GetString(".tab.overlay.player.gold", {{ "amount", gold }})
				+ "  " + Resources::GetString(mat, {{ "amount", "-" + DISCOUNT_MAT[i] }}) + "\\d";
		}

		// The cost multiplier for a pick list: vanilla's curve over the bought
		// alterations (and vanilla's discount for any other free ones). The
		// challenges' discounts come off after it (MissionArchitect CalcMyCost).
		float CostMul(const array<uint> &in ids)
		{
			int numBuffs = 0;
			int numDebuffs = 0;
			for (uint i = 0; i < ids.length(); i++)
			{
				auto buff = MissionBuff::Get(ids[i]);
				if (buff is null || ChallengeIndex(ids[i]) >= 0)
					continue;
				if (buff.m_cost.GetTotalCost() == 0)
					numDebuffs++;
				else
					numBuffs++;
			}
			return CalcArchitectCostMul(numBuffs, numDebuffs);
		}

		bool Picked(const string &in id)
		{
			auto gm = cast<HWR2GameMode>(g_gameMode);
			return gm !is null && gm.HasArchitectBuff(id);
		}

		class ChallengeSetup : DungeonGenerationCommands
		{
			ALevelGenerator@ m_gen;
			DungeonGenerationCommands@ m_inner;   // the wrapped command, or null
			vec2 m_density;
			bool m_elites;
			bool m_minibosses;

			ChallengeSetup(ALevelGenerator@ gen, DungeonGenerationCommands@ inner)
			{
				@m_gen = gen;
				@m_inner = inner;
				m_execChance = inner is null ? 1.0f : inner.m_execChance;
				@m_conditionals = inner is null ? null : inner.m_conditionals;
				auto placer = gen.m_enemyPlacer;
				m_density = placer.m_densityMul;
				m_elites = placer.m_allowElites;
				m_minibosses = placer.m_allowMinibosses;
			}

			// Generate retries from scratch when a command fails, so this sets
			// the placer from the generator's own values every time
			bool Execute(DungeonBrush@ brush, PrefabPlacement@ pfbPlacer) override
			{
				auto placer = m_gen.m_enemyPlacer;
				bool crowded = Picked("hwp_challenge_crowded");
				bool champions = Picked("hwp_challenge_champions");
				placer.m_densityMul = crowded ? m_density * CROWDED_DENSITY : m_density;
				placer.m_allowElites = m_elites || champions;
				placer.m_allowMinibosses = m_minibosses || champions;
				if (crowded || champions)
					HWP::Log("architect", "challenges on this floor:" + (crowded ? " crowded" : "") + (champions ? " champions" : ""));
				return m_inner is null || m_inner.Execute(brush, pfbPlacer);
			}
		}

		// returns how many generators got the command (the mission defs, and
		// with them the generators, are rebuilt on every level load)
		int AddChallengeSetup()
		{
			int added = 0;
			for (uint i = 0; i < MissionDef::Instances.length(); i++)
			{
				auto mission = MissionDef::Instances[i];
				for (uint j = 0; j < mission.m_levels.length(); j++)
				{
					auto gen = cast<DungeonGenerator>(mission.m_levels[j].m_generator);
					if (gen is null || gen.m_enemyPlacer is null)
						continue;
					bool present = false;
					int at = -1;
					for (uint k = 0; k < gen.m_genCommands.length() && !present; k++)
					{
						auto cmd = gen.m_genCommands[k];
						present = cast<ChallengeSetup>(cmd) !is null;
						// (not a SpawnPrefabSet: the puzzles module looks for those by class)
						if (at < 0 && cmd.m_execChance >= 1.0f && cast<SpawnPrefabSet>(cmd) is null
							&& (cmd.m_conditionals is null || cmd.m_conditionals.isEmpty()))
							at = int(k);
					}
					if (present)
						continue;
					// always runs: an unconditional command, or a new first one
					if (at >= 0)
						@gen.m_genCommands[at] = ChallengeSetup(gen, gen.m_genCommands[at]);
					else
						gen.m_genCommands.insertAt(0, ChallengeSetup(gen, null));
					added++;
				}
			}
			return added;
		}
	}
}

namespace Modifiers
{
	// Sharpened Traps: trap damage taken times mul
	class HWPTrapDamage : Modifier
	{
		vec2 m_mul;

		HWPTrapDamage(UnitPtr unit, SValue& params)
		{
			m_mul = GetParamVec2(unit, params, "mul", false, 1);
		}

		ModDynamism HasTrapDamageMul() override { return ModDynamism::Dynamic; }
		float TrapDamageMul(PlayerRecord@ plr, float intensity) override { return lerp(m_mul, intensity); }
	}
}
