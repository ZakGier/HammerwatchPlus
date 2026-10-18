// HWP architect challenges: Heroes of Hammerwatch 1's "bad wishes" as free
// Architect alterations (tweak/hwp/architect_challenges.sval). They have no
// cost, so the picker treats them as vanilla debuffs; instead of vanilla's
// count-based discount each one takes its own share off the alterations you
// buy (CHALLENGES), summed and capped at 100%: a run can become free, never
// profitable.
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

		// id -> discount (fraction of the alterations' cost)
		const array<string> CHALLENGES = {
			"hwp_challenge_crowded", "hwp_challenge_champions", "hwp_challenge_lean_pickups",
			"hwp_challenge_bitter_draughts", "hwp_challenge_glass_bones", "hwp_challenge_sharp_traps",
			"hwp_challenge_slim_pickings"
		};
		const array<float> DISCOUNTS = { 0.15f, 0.15f, 0.10f, 0.10f, 0.25f, 0.10f, 0.15f };

		array<uint> g_challengeHashes;

		// -1 when the id is not an HWP challenge
		float ChallengeDiscount(uint id)
		{
			if (g_challengeHashes.length() == 0)
			{
				for (uint i = 0; i < CHALLENGES.length(); i++)
					g_challengeHashes.insertLast(HashString(CHALLENGES[i]));
			}
			int i = g_challengeHashes.find(id);
			return i < 0 ? -1.0f : DISCOUNTS[i];
		}

		// The cost multiplier for a pick list: vanilla's curve over the bought
		// alterations (and vanilla's discount for any other free ones), times
		// what the challenges leave of it.
		float CostMul(const array<uint> &in ids)
		{
			int numBuffs = 0;
			int numDebuffs = 0;
			float discount = 0;
			for (uint i = 0; i < ids.length(); i++)
			{
				auto buff = MissionBuff::Get(ids[i]);
				if (buff is null)
					continue;
				float d = ChallengeDiscount(ids[i]);
				if (d >= 0)
					discount += d;
				else if (buff.m_cost.GetTotalCost() == 0)
					numDebuffs++;
				else
					numBuffs++;
			}
			return CalcArchitectCostMul(numBuffs, numDebuffs) * max(0.0f, 1.0f - discount);
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
