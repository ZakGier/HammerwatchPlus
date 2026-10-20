// Keys and ace chests: HoH1-style locked chests (HWPChest.as), key drops from
// enemies, the exit guard's key shop (GeneralMerchant.as), key counts in the
// bottom HUD and the ace chest's legendary payout.
//
//   keys.drop        client -> host   { x, y, tier, elite, boss }   a kill that may drop a key
//   keys.pool_add    client -> host   { tier, n }    a key found (the imp's offer)
//   keys.pool_spend  client -> host   { tier }       a chest opened with a party key
//   keys.pool_get    client -> host   {}             send me the pool
//   keys.pool        host -> all      { bronze, silver, gold, ace }
//
// Keys found in a run go into one party pool that the host owns: everyone
// sees the same counts and any player can open a chest with them. The pool is
// emptied when a new run starts. Keys bought from the General Merchant are the
// buyer's own (a vanilla PlayerRecord field, GetKeys, saved by the game,
// changed only through HWP::Keys::AddKeys / SetKeys: vanilla AddKeys corrupts
// the count); a chest takes a party key first.
//
// Drops follow a per-floor budget: for each tier, a share of the floor's
// locked chests (fewer than they need), minus the party keys already held.
// The killer's machine sends elite kills and a few normal ones as candidates
// (PlayerKilledActor only fires for the local Player) and the host drops keys
// from them while the floor's budget lasts.
// All keys.* settings are host-authoritative (HWP::Settings::Sync).
namespace HWP
{
	namespace Keys
	{
		const string DROP = "keys.drop";
		const string LOCK_UNIT = "doodads/hwp/chest_lock.unit";
		const string GUARD_UNIT = "actors/npcs/town/npc_misc_guard_exit.unit";
		const string KEY_UNIT_PREFIX = "items/hwp/keys/key_";
		const array<string> LEGENDARIES = {
			"hwp_descending_destruction", "hwp_dragons_tail", "hwp_medusas_charm",
			"hwp_sphere_of_heroes", "hwp_spirit_cloak", "hwp_soul_taker", "hwp_wand_of_chaos" };

		// ---- tiers (index = tier - 1) ------------------------------------------
		const array<string> TIERS = { "bronze", "silver", "gold", "ace" };
		const array<int> DEFAULT_PRICE = { 500, 2000, 8000, 50000 };
		// sprites in items/special/base.png (vanilla items/special/keys.unit)
		const array<vec4> ICON_FRAME = { vec4(0, 0, 16, 16), vec4(16, 0, 16, 16), vec4(32, 0, 16, 16), vec4(112, 16, 16, 16) };
		const array<vec4> TINT = { vec4(0.85f, 0.55f, 0.3f, 1.0f), vec4(0.85f, 0.88f, 0.95f, 1.0f), vec4(1.0f, 0.85f, 0.25f, 1.0f), vec4(1.0f, 0.25f, 0.2f, 1.0f) };
		const array<Item::Quality> QUALITY = { Item::Quality::Common, Item::Quality::Uncommon, Item::Quality::Rare, Item::Quality::Legendary };

		bool ValidTier(int tier) { return tier >= 1 && tier <= int(TIERS.length()); }

		// Vanilla PlayerRecord.AddKeys does keys.set(key, currNum + num), and the
		// engine's dictionary.set keeps a temporary by reference: the count reads
		// back as garbage (plan-t4 20261018-035113: "+2 gold" read 322810098; a
		// probe showed named locals survive, expressions do not). Every add and
		// spend goes through here, which stores a named local.
		void SetKeys(PlayerRecord@ rec, const string &in key, int count)
		{
			int stored = max(0, count);
			rec.keys.set(key, stored);
		}

		void AddKeys(PlayerRecord@ rec, const string &in key, int num)
		{
			SetKeys(rec, key, rec.GetKeys(key) + num);
		}

		// a save written while vanilla AddKeys was in use can hold such garbage
		void SanitizeKeys(PlayerRecord@ rec)
		{
			if (rec is null)
				return;
			for (uint t = 0; t < TIERS.length(); t++)
			{
				int n = rec.GetKeys(TIERS[t]);
				if (n < 0 || n > 999)
				{
					SetKeys(rec, TIERS[t], 0);
					HWP::Log("keys", "reset a corrupt " + TIERS[t] + " key count (" + n + ")");
				}
			}
		}

		int TierIndex(const string &in name)
		{
			for (uint i = 0; i < TIERS.length(); i++)
				if (TIERS[i] == name)
					return int(i) + 1;
			return 0;
		}

		int KeyPrice(int tier)
		{
			if (!ValidTier(tier))
				return 0;
			return HWP::Settings::GetInt("keys.price_" + TIERS[tier - 1], DEFAULT_PRICE[tier - 1]);
		}
		vec4 KeyIconFrame(int tier) { return ValidTier(tier) ? ICON_FRAME[tier - 1] : vec4(0, 0, 16, 16); }
		vec4 TierColor(int tier) { return ValidTier(tier) ? TINT[tier - 1] : vec4(1, 1, 1, 1); }
		Item::Quality TierQuality(int tier) { return ValidTier(tier) ? QUALITY[tier - 1] : Item::Quality::Common; }

		// ---- settings (host-authoritative, refreshed per level and on change) ----
		bool g_enabled = true;
		bool g_debug = false;
		float g_lockChance = 1.0f;
		float g_budgetShare = 0.5f;     // share of a floor's locked chests that get a key (solo)
		float g_budgetPerPlayer = 0.1f; // added per extra player
		float g_normalTry = 0.04f;      // share of normal kills sent as drop candidates
		float g_accept = 0.4f;          // host: chance a candidate drops a key while the budget lasts
		float g_aceChance = 0.15f;
		float g_legendaryChance = 0.5f;

		int g_chestsLocked = 0;     // this level, for hwp keys
		array<int> g_lockedTier(4, 0);     // this level's locked chests per tier (HWPChest.Decide)
		array<int> g_droppedTier(4, 0);    // host: budget keys dropped this level per tier
		array<int> g_floorStartPool(4, 0); // host: party keys held when the level started
		array<int> g_pool(4, 0);           // the party pool (host: the truth; clients: its copy)
		int g_bossKeyLevel = -1;    // level index whose boss already rolled its key (killer side)
		int g_hostBossLevel = -1;   // host: level index of the boss drops below
		int g_hostBossMask = 0;     // host: 1 = the boss key for g_hostBossLevel dropped

		// host: key counts the clients reported (keys.count), 4 per peer
		const string COUNT = "keys.count";
		array<int> g_peerKeys(256 * 4, 0);
		array<int> g_lastSent(4, -1); // client: counts last reported
		int g_countTimer = 0;
		HWPKeysHUD@ g_hud;

		// host: recent drop requests for the rate limit
		const int DROP_LIMIT = 10;
		const int DROP_WINDOW = 10000;
		array<int> g_dropPeer;
		array<int> g_dropTime;

		void RefreshSettings()
		{
			g_enabled = HWP::Settings::GetBool("keys.enabled", true);
			g_debug = HWP::Settings::GetBool("keys.debug", false);
			g_lockChance = clamp(HWP::Settings::GetFloat("keys.lock_chance", 1.0f), 0.0f, 1.0f);
			g_budgetShare = clamp(HWP::Settings::GetFloat("keys.budget_share", 0.5f), 0.0f, 1.0f);
			g_budgetPerPlayer = clamp(HWP::Settings::GetFloat("keys.budget_per_player", 0.1f), 0.0f, 1.0f);
			g_normalTry = clamp(HWP::Settings::GetFloat("keys.normal_try", 0.04f), 0.0f, 1.0f);
			g_accept = clamp(HWP::Settings::GetFloat("keys.accept", 0.4f), 0.0f, 1.0f);
			g_aceChance = clamp(HWP::Settings::GetFloat("keys.ace_chance", 0.15f), 0.0f, 1.0f);
			g_legendaryChance = clamp(HWP::Settings::GetFloat("keys.legendary_chance", 0.5f), 0.0f, 1.0f);
		}

		void OnSettingChanged(const string &in key)
		{
			if (key.findFirst("keys.") == 0)
				RefreshSettings();
		}

		void RefreshHUD()
		{
			if (g_hud !is null)
				g_hud.Refresh(GetLocalPlayerRecord());
		}

		int CurrentLevel()
		{
			if (MissionManager::g_module is null)
				return -1;
			return int(MissionManager::g_module.m_missionLevelIndex);
		}

		MissionLevel@ CurrentMissionLevel()
		{
			auto def = MissionManager::GetCurrentMission();
			int idx = CurrentLevel();
			if (def is null || idx < 0 || idx >= int(def.m_levels.length()))
				return null;
			return def.m_levels[idx];
		}

		bool IsBossLevel(MissionLevel@ lvl)
		{
			return lvl.m_level.findFirst("levels/boss_") == 0 || lvl.m_id.findFirst("_boss") >= 0;
		}

		// The floor's key tier, scaled by its diff-level (without new game+)
		// the way the imp's own offers scale: the Dark Citadel's floors go
		// 2..22, the side missions 8..15.
		int FloorTier()
		{
			auto lvl = CurrentMissionLevel();
			int diff = lvl is null ? 1 : lvl.m_diffLevel;
			if (diff <= 7)
				return 1;
			if (diff <= 13)
				return 2;
			return 3;
		}

		// Boss key tier: the floor's, but ace from the mission's second-to-last
		// boss on (Bone Serpent and Avatar in the Dark Citadel; single-boss
		// missions never qualify).
		int BossTier()
		{
			auto def = MissionManager::GetCurrentMission();
			auto lvl = CurrentMissionLevel();
			if (def is null || lvl is null)
				return FloorTier();
			int bosses = 0;
			int rank = -1;
			for (uint i = 0; i < def.m_levels.length(); i++)
			{
				if (!IsBossLevel(def.m_levels[i]))
					continue;
				if (def.m_levels[i] is lvl)
					rank = bosses;
				bosses++;
			}
			if (bosses >= 2 && rank >= bosses - 2)
				return 4;
			return FloorTier();
		}

		// ---- key counts on the host -------------------------------------------

		int HostKeyCount(int peer, const string &in key)
		{
			int tier = TierIndex(key);
			if (tier < 1 || peer < 0 || peer >= 256)
				return 0;
			return g_peerKeys[peer * 4 + tier - 1];
		}

		void ResetKeyCounts()
		{
			for (uint i = 0; i < g_peerKeys.length(); i++)
				g_peerKeys[i] = 0;
			for (uint i = 0; i < g_lastSent.length(); i++)
				g_lastSent[i] = -1;
			g_countTimer = 0;
		}

		// Client: report the local key counts to the host when they changed
		// (polled twice a second by the module, forced before a chest use).
		void SendKeyCounts(bool force)
		{
			if (Network::IsServer())
				return;
			auto rec = GetLocalPlayerRecord();
			if (rec is null)
				return;
			bool changed = force;
			array<int> cur(4, 0);
			for (uint t = 0; t < 4; t++)
			{
				cur[t] = rec.GetKeys(TIERS[t]);
				if (cur[t] != g_lastSent[t])
					changed = true;
			}
			if (!changed)
				return;
			SValueBuilder b;
			b.PushDictionary();
			for (uint t = 0; t < 4; t++)
			{
				g_lastSent[t] = cur[t];
				b.PushInteger(TIERS[t], cur[t]);
			}
			b.PopDictionary();
			HWP::Net::Request(COUNT, b.Build());
		}

		void OnCountRequest(uint8 peer, SValue@ data)
		{
			if (!Network::IsServer())
				return;
			for (uint t = 0; t < 4; t++)
			{
				int n = HWP::SV::Int(data, TIERS[t], 0);
				g_peerKeys[int(peer) * 4 + t] = n < 0 ? 0 : n;
			}
		}

		// ---- drops ---------------------------------------------------------------

		bool HasTag(Actor@ actor, const string &in tag)
		{
			return (actor.Tags & ApplyTag(0, g_actorTags.GetTag(tag))) != 0;
		}

		// tier 0: a budget candidate (the host picks the tier); with boss, the boss key's tier
		void RequestDrop(vec2 pos, int tier, bool elite, bool boss)
		{
			SValueBuilder b;
			b.PushDictionary();
			b.PushFloat("x", pos.x);
			b.PushFloat("y", pos.y);
			b.PushInteger("tier", tier);
			b.PushInteger("elite", elite ? 1 : 0);
			b.PushInteger("boss", boss ? 1 : 0);
			b.PopDictionary();
			HWP::Net::Request(DROP, b.Build());
		}

		// Local killer: the first boss-tagged kill on a level has a
		// keys.boss_chance (20%) roll for a BossTier() key, outside the budget;
		// later boss-tagged units of the same encounter count as elites. Elite
		// kills and keys.normal_try of the normal ones go to the host as
		// candidates for the floor's budget (OnDropRequest).
		void OnKill(Player@ player, Actor@ killed)
		{
			if (!g_enabled || g_inTown || player is null || killed is null)
				return;
			if (player.m_record is null || !player.m_record.local)
				return;
			if (!killed.m_unit.IsValid())
				return;

			vec2 pos = xy(killed.m_unit.GetPosition());
			bool elite = HasTag(killed, "elite");
			if (HasTag(killed, "boss"))
			{
				int level = CurrentLevel();
				if (g_bossKeyLevel != level)
				{
					g_bossKeyLevel = level;
					if (randf() < clamp(HWP::Settings::GetFloat("keys.boss_chance", 0.2f), 0.0f, 1.0f))
						RequestDrop(pos, BossTier(), false, true);
					return;
				}
				elite = true;
			}
			if (elite || randf() < g_normalTry)
				RequestDrop(pos, 0, elite, false);
		}

		// ---- the floor's key budget (host) ---------------------------------------

		int PartySize()
		{
			int n = 0;
			for (uint i = 0; i < g_players.length(); i++)
				if (g_players[i] !is null && g_players[i].peer != 255)
					n++;
			return max(1, n);
		}

		// Keys this floor may still drop of a tier: the floor's locked chests of
		// that tier times the party's share, its fraction rounded up or down by a
		// hash roll, minus the party keys of that tier held when the floor
		// started and the ones dropped since. Recomputed per call, so chests
		// that lock after the level starts still count.
		int BudgetTotal(int tier)
		{
			float share = clamp(g_budgetShare + g_budgetPerPlayer * (PartySize() - 1), 0.0f, 0.95f);
			float want = g_lockedTier[tier - 1] * share;
			int budget = int(floor(want));
			string seed = MissionManager::g_module is null ? "" : ("" + MissionManager::g_module.m_missionRewardSeed + ":" + CurrentLevel());
			if (float(HashString("keys.budget:" + seed + ":" + tier) % 10000) / 10000.0f < want - budget)
				budget++;
			return max(0, budget - g_floorStartPool[tier - 1]);
		}

		int BudgetLeft(int tier)
		{
			return max(0, BudgetTotal(tier) - g_droppedTier[tier - 1]);
		}

		// A tier with budget left, weighted by what is left; elites take the
		// highest such tier. 0 = the budget is spent.
		int PickBudgetTier(bool elite)
		{
			array<int> left(4, 0);
			int total = 0;
			for (int t = 1; t <= 4; t++)
			{
				left[t - 1] = BudgetLeft(t);
				total += left[t - 1];
			}
			if (total == 0)
				return 0;
			if (elite)
			{
				for (int t = 4; t >= 1; t--)
					if (left[t - 1] > 0)
						return t;
			}
			int r = randi(total);
			for (int t = 1; t <= 4; t++)
			{
				r -= left[t - 1];
				if (r < 0)
					return t;
			}
			return 0;
		}

		// ---- the party pool ------------------------------------------------------

		const string POOL = "keys.pool";
		const string POOL_ADD = "keys.pool_add";
		const string POOL_SPEND = "keys.pool_spend";
		const string POOL_GET = "keys.pool_get";
		const string BAG_POOL = "keys.pool";
		const string BAG_POOL_RUN = "keys.pool_run";

		int PoolCount(int tier) { return ValidTier(tier) ? g_pool[tier - 1] : 0; }

		// party keys plus the local player's own (bought) keys
		int UsableKeys(PlayerRecord@ rec, int tier)
		{
			return PoolCount(tier) + (rec is null ? 0 : rec.GetKeys(TIERS[tier - 1]));
		}

		// which run the pool belongs to: a new reward seed is a new run
		string RunId()
		{
			if (MissionManager::g_module is null)
				return "";
			return "" + MissionManager::g_module.m_missionRewardSeed;
		}

		SValue@ PoolData()
		{
			SValueBuilder b;
			b.PushDictionary();
			for (uint t = 0; t < 4; t++)
				b.PushInteger(TIERS[t], g_pool[t]);
			b.PopDictionary();
			return b.Build();
		}

		// host: keep the pool on the host's own record (it outlives the level)
		// and tell everyone
		void PoolChanged()
		{
			if (!Network::IsServer())
				return;
			auto rec = GetLocalPlayerRecord();
			if (rec !is null)
			{
				auto bag = HWP::SaveData::Player(rec);
				bag.SetString(BAG_POOL, g_pool[0] + "," + g_pool[1] + "," + g_pool[2] + "," + g_pool[3]);
				bag.SetString(BAG_POOL_RUN, RunId());
			}
			HWP::Net::Broadcast(POOL, PoolData());
		}

		// host, level start: the run's pool, or an empty one in town and when a
		// new run started
		void PoolLevelStart()
		{
			for (uint t = 0; t < 4; t++)
				g_pool[t] = 0;
			auto rec = GetLocalPlayerRecord();
			if (!g_inTown && rec !is null)
			{
				auto bag = HWP::SaveData::Player(rec);
				if (bag.GetString(BAG_POOL_RUN, "") == RunId())
				{
					auto parts = bag.GetString(BAG_POOL, "").split(",");
					for (uint t = 0; t < 4 && t < parts.length(); t++)
						g_pool[t] = max(0, min(999, parseInt(parts[t])));
				}
			}
			for (uint t = 0; t < 4; t++)
			{
				g_floorStartPool[t] = g_pool[t];
				g_droppedTier[t] = 0;
			}
			PoolChanged();
		}

		void PoolAdd(int tier, int n)
		{
			if (!ValidTier(tier) || n <= 0)
				return;
			if (!Network::IsServer())
			{
				SValueBuilder b;
				b.PushDictionary();
				b.PushInteger("tier", tier);
				b.PushInteger("n", n);
				b.PopDictionary();
				HWP::Net::Request(POOL_ADD, b.Build());
				return;
			}
			g_pool[tier - 1] = min(999, g_pool[tier - 1] + n);
			PoolChanged();
		}

		// host: take one party key; false when the pool has none of that tier
		bool PoolTake(int tier)
		{
			if (!Network::IsServer() || PoolCount(tier) <= 0)
				return false;
			g_pool[tier - 1]--;
			PoolChanged();
			return true;
		}

		void OnPoolEvent(SValue@ data)
		{
			for (uint t = 0; t < 4; t++)
				g_pool[t] = max(0, HWP::SV::Int(data, TIERS[t], 0));
			RefreshHUD();
		}

		void OnPoolAddRequest(uint8 peer, SValue@ data)
		{
			if (!Network::IsServer() || !g_enabled || RateLimited(peer))
				return;
			PoolAdd(HWP::SV::Int(data, "tier", 0), min(5, HWP::SV::Int(data, "n", 1)));
		}

		void OnPoolSpendRequest(uint8 peer, SValue@ data)
		{
			if (Network::IsServer())
				PoolTake(HWP::SV::Int(data, "tier", 0));
		}

		void OnPoolGetRequest(uint8 peer, SValue@ data)
		{
			if (Network::IsServer())
				HWP::Net::Send(peer, POOL, PoolData());
		}

		// A key picked up or given in a run goes to the pool (only the host
		// adds: a secure pickup is applied there), in town to the record.
		void GiveFoundKey(PlayerRecord@ rec, int tier, int n)
		{
			if (g_inTown)
			{
				if (rec !is null && rec.local)
					AddKeys(rec, TIERS[tier - 1], n);
				return;
			}
			if (Network::IsServer())
				PoolAdd(tier, n);
		}

		// host: a flood guard, not a fairness rule - honest play stays far
		// below DROP_LIMIT requests per DROP_WINDOW even on a boss kill
		bool RateLimited(uint8 peer)
		{
			int now = g_scene.GetTime();
			for (int i = int(g_dropTime.length()) - 1; i >= 0; i--)
			{
				if (now - g_dropTime[i] > DROP_WINDOW)
				{
					g_dropTime.removeAt(i);
					g_dropPeer.removeAt(i);
				}
			}
			int n = 0;
			for (uint i = 0; i < g_dropPeer.length(); i++)
				if (g_dropPeer[i] == int(peer))
					n++;
			if (n >= DROP_LIMIT)
				return true;
			g_dropPeer.insertLast(int(peer));
			g_dropTime.insertLast(now);
			return false;
		}

		void OnDropRequest(uint8 peer, SValue@ data)
		{
			if (!Network::IsServer() || !g_enabled)
				return;
			int tier = HWP::SV::Int(data, "tier", 0);
			bool boss = HWP::SV::Int(data, "boss", 0) != 0;
			if (boss ? !ValidTier(tier) : tier != 0)
				return;
			if (RateLimited(peer))
			{
				HWP::Log("keys", "drop request from peer " + peer + " rate limited (" + DROP_LIMIT + " per " + (DROP_WINDOW / 1000) + " s)");
				return;
			}
			// the boss drops are once per level for the whole lobby, whoever
			// landed the killing blow (every killer's machine asks)
			if (boss)
			{
				int level = CurrentLevel();
				if (g_hostBossLevel != level)
				{
					g_hostBossLevel = level;
					g_hostBossMask = 0;
				}
				if (g_hostBossMask != 0)
					return;
				g_hostBossMask = 1;
			}
			else
			{
				if (randf() >= g_accept)
					return;
				tier = PickBudgetTier(HWP::SV::Int(data, "elite", 0) != 0);
				if (tier == 0)
					return;
				g_droppedTier[tier - 1]++;
			}
			SpawnKey(vec2(HWP::SV::Float(data, "x"), HWP::SV::Float(data, "y")), tier);
		}

		// Server only. Same pattern as LootDef::Spawn: produce here, tell the
		// clients to produce the same unit (key pickups are not netsynced).
		void SpawnKey(vec2 pos, int tier)
		{
			auto prod = Resources::GetUnitProducer(KEY_UNIT_PREFIX + TIERS[tier - 1] + ".unit");
			if (prod is null)
			{
				HWP::LogError("keys", "missing key unit for tier " + tier);
				return;
			}
			prod.Produce(g_scene, vec3(pos.x, pos.y, 0));
			if (!IsNetsyncedExistance(prod.GetNetSyncMode()))
			{
				SValueBuilder sval;
				sval.PushArray();
				sval.PushInteger(prod.GetResourceHash());
				sval.PushVector2(pos);
				sval.PopArray();
				(Network::Message("SpawnLoot") << sval.Build()).SendToAll();
			}
			HWP::Log("keys", "dropped a " + TIERS[tier - 1] + " key at " + int(pos.x) + "," + int(pos.y));
		}

		// ---- chests --------------------------------------------------------------

		// Runs on every machine (UseUnit broadcast); only the opener's own
		// machine books the stat, like vanilla Chest::Use.
		void OnUnlocked(PlayerBase@ player, int tier)
		{
			if (player is null || player.m_record is null || !player.m_record.local)
				return;
			Stats::Add(HashString("hwp-chest-unlocked-" + TIERS[tier - 1]), 1, player.m_record);
			RefreshHUD();
			HWP::Log("keys", player.m_record.GetName() + " unlocked a " + TIERS[tier - 1] + " chest");
		}

		// Server. Half of the ace chests give every player in the lobby their
		// own (instanced) legendary; the other half an epic piece of equipment
		// from the regular table on top of the chest's own loot.
		void SpawnAceBonus(PlayerBase@ opener, vec3 pos)
		{
			if (randf() >= g_legendaryChance)
			{
				auto table = Item::GetLootTable("hwp_chest_ace_epic");
				if (table !is null)
					table.SpawnLoot(opener, pos);
				return;
			}

			int given = 0;
			for (uint i = 0; i < g_players.length(); i++)
			{
				auto record = g_players[i];
				if (record is null || record.peer == 255)
					continue;
				auto item = Item::Get(LEGENDARIES[randi(LEGENDARIES.length())]);
				if (item is null)
				{
					HWP::LogError("keys", "legendary definitions missing (tweak/hwp/legendaries.sval)");
					return;
				}
				vec3 p = pos + vec3((randf() * 2 - 1) * 12, (randf() * 2 - 1) * 12, 0);
				Item::DropItem(item, p, 1, true, record);
				given++;
			}
			HWP::Log("keys", "ace chest: legendary for " + given + " player(s)");
		}

		// Logged once per gameplay load so dev_check shows whether the loaders
		// picked the loot tables, the legendaries and the units up.
		void SelfCheck()
		{
			if (Item::GetLootTable("hwp_chest_ace") is null || Item::GetLootTable("hwp_chest_ace_epic") is null)
				HWP::LogError("keys", "loot tables missing (tweak/hwp/loot_chests_ace.sval)");
			int legendaries = 0;
			for (uint i = 0; i < LEGENDARIES.length(); i++)
				if (Item::Get(LEGENDARIES[i]) !is null)
					legendaries++;
			if (legendaries != int(LEGENDARIES.length()))
				HWP::LogError("keys", "only " + legendaries + "/" + LEGENDARIES.length() + " legendaries registered (tweak/hwp/legendaries.sval)");
			array<string> units = { LOCK_UNIT, GUARD_UNIT };
			for (uint i = 0; i < TIERS.length(); i++)
				units.insertLast(KEY_UNIT_PREFIX + TIERS[i] + ".unit");
			HWP::CheckUnits("keys", units);
			HWP::Log("keys", "self-check done: " + legendaries + " legendaries");
		}

		// ---- commands ------------------------------------------------------------

		string Counts(PlayerRecord@ rec, const string &in key)
		{
			return Resources::GetString(key, {
				{ "bronze", "" + rec.GetKeys("bronze") }, { "silver", "" + rec.GetKeys("silver") },
				{ "gold", "" + rec.GetKeys("gold") }, { "ace", "" + rec.GetKeys("ace") },
				{ "lock", "" + g_lockChance }, { "acechance", "" + g_aceChance } });
		}

		void CmdKeys(array<string>@ args)
		{
			auto rec = GetLocalPlayerRecord();
			if (rec is null)
				return;
			string info = Counts(rec, ".hwp.keys.status") + "; party pool";
			for (int t = 1; t <= 4; t++)
				info += " " + TIERS[t - 1] + " " + PoolCount(t);
			info += "; locked chests this level: " + g_chestsLocked;
			for (int t = 1; t <= 4; t++)
				info += " " + TIERS[t - 1] + " " + g_lockedTier[t - 1];
			if (Network::IsServer())
			{
				info += "; budget (left/total)";
				for (int t = 1; t <= 4; t++)
					info += " " + TIERS[t - 1] + " " + BudgetLeft(t) + "/" + BudgetTotal(t);
				info += ", party " + PartySize();
			}
			HWP::Commands::Reply(info);
		}

		// debug: hwp keygive <tier> [n]  and  hwp keydrop <tier>
		void CmdKeyGive(array<string>@ args)
		{
			if (!g_debug)
			{
				HWP::Commands::Reply(Resources::GetString(".hwp.keys.debug_off"));
				return;
			}
			int tier = args.length() > 0 ? TierIndex(args[0]) : 0;
			if (tier == 0)
			{
				HWP::Commands::Reply("usage: hwp keygive bronze|silver|gold|ace [count]");
				return;
			}
			auto rec = GetLocalPlayerRecord();
			if (rec is null)
			{
				HWP::Commands::Reply("no character loaded");
				return;
			}
			int n = args.length() > 1 ? max(1, parseInt(args[1])) : 1;
			AddKeys(rec, TIERS[tier - 1], n);
			RefreshHUD();
			HWP::Commands::Reply("+" + n + " " + TIERS[tier - 1] + " key(s)");
		}

		void CmdKeyDrop(array<string>@ args)
		{
			if (!g_debug)
			{
				HWP::Commands::Reply(Resources::GetString(".hwp.keys.debug_off"));
				return;
			}
			int tier = args.length() > 0 ? TierIndex(args[0]) : 1;
			auto rec = GetLocalPlayerRecord();
			if (tier == 0 || rec is null || rec.actor is null)
				return;
			if (Network::IsServer())
				SpawnKey(xy(rec.actor.m_unit.GetPosition()) + vec2(0, 20), tier);
			else
				RequestDrop(xy(rec.actor.m_unit.GetPosition()) + vec2(0, 20), tier, false, true);
		}
	}
}

// Key counts left of the bottom bar: one key icon per tier you can use (party
// pool + your own), with its count.
class HWPKeysHUD : HUDComponent
{
	array<Widget@> m_slots;
	array<TextWidget@> m_counts;
	int m_acc = 0;

	HWPKeysHUD(GUIBuilder@ b)
	{
		super(b, "gui/hwp_keys.gui");
		for (uint t = 0; t < HWP::Keys::TIERS.length(); t++)
		{
			m_slots.insertLast(m_widget.GetWidgetById("slot-" + HWP::Keys::TIERS[t]));
			m_counts.insertLast(cast<TextWidget>(m_widget.GetWidgetById("count-" + HWP::Keys::TIERS[t])));
		}
		m_visible = false;
	}

	void Refresh(PlayerRecord@ record) override
	{
		if (record is null)
		{
			m_visible = false;
			return;
		}
		// shown tiers pack to the right, against the bar
		int shown = 0;
		for (int t = int(m_slots.length()); t >= 1; t--)
		{
			auto slot = m_slots[t - 1];
			auto count = m_counts[t - 1];
			if (slot is null || count is null)
				continue;
			int n = HWP::Keys::UsableKeys(record, t);
			slot.m_visible = n > 0;
			if (n <= 0)
				continue;
			count.SetText("" + n);
			slot.m_offset = vec2(-shown * 30, 0);
			slot.Invalidate();
			shown++;
		}
		m_visible = shown > 0;
	}

	void Update(int dt, PlayerRecord@ record) override
	{
		m_acc += dt;
		if (m_acc >= 500)
		{
			m_acc = 0;
			Refresh(record);
		}
		HUDComponent::Update(dt, record);
	}
}

namespace HWPKeys
{
	[Hook]
	void PlayerKilledActor(Player@ player, Actor@ killed, DamageInfo@ di)
	{
		HWP::Keys::OnKill(player, killed);
	}

	[Hook]
	void HUDConstructor(HUD@ hud, GUIBuilder@ b)
	{
		auto comp = HWPKeysHUD(b);
		hud.m_components.insertLast(comp);
		@HWP::Keys::g_hud = comp;
	}
}

namespace Modules
{
	class HWPKeysModule : Module, HWP::ModuleStart
	{
		HWPKeysModule()
		{
			super("hwp-keys");
			// per level, before the scene's chests count themselves (they lock
			// while the level loads, ahead of ModuleStart::Start)
			HWP::Keys::g_chestsLocked = 0;
			for (uint t = 0; t < 4; t++)
				HWP::Keys::g_lockedTier[t] = 0;
			HWP::Settings::Sync("keys.");
			HWP::Keys::RefreshSettings();
			HWP::Net::OnRequest(HWP::Keys::DROP, HWP::Net::RequestHandler(HWP::Keys::OnDropRequest));
			HWP::Net::OnRequest(HWP::Keys::COUNT, HWP::Net::RequestHandler(HWP::Keys::OnCountRequest));
			HWP::Net::OnRequest(HWP::Keys::POOL_ADD, HWP::Net::RequestHandler(HWP::Keys::OnPoolAddRequest));
			HWP::Net::OnRequest(HWP::Keys::POOL_SPEND, HWP::Net::RequestHandler(HWP::Keys::OnPoolSpendRequest));
			HWP::Net::OnRequest(HWP::Keys::POOL_GET, HWP::Net::RequestHandler(HWP::Keys::OnPoolGetRequest));
			HWP::Net::OnEvent(HWP::Keys::POOL, HWP::Net::EventHandler(HWP::Keys::OnPoolEvent));
			HWP::Commands::Register("keys", " show your keys and the chest lock settings", HWP::Commands::Handler(HWP::Keys::CmdKeys));
			HWP::Commands::Register("keygive", "<tier> [n]  (debug) give yourself keys", HWP::Commands::Handler(HWP::Keys::CmdKeyGive));
			HWP::Commands::Register("keydrop", "<tier>  (debug) drop a key at your feet", HWP::Commands::Handler(HWP::Keys::CmdKeyDrop));
			HWP::Commands::OnSettingChanged(HWP::Commands::SettingListener(HWP::Keys::OnSettingChanged));
		}

		void Start(StartMode sMode)
		{
			HWP::Keys::RefreshSettings();
			HWP::Keys::SanitizeKeys(GetLocalPlayerRecord());
			HWP::Keys::g_bossKeyLevel = -1;
			HWP::Keys::g_hostBossLevel = -1;
			HWP::Keys::g_hostBossMask = 0;
			HWP::Keys::ResetKeyCounts();
			HWP::Keys::g_dropPeer.removeRange(0, HWP::Keys::g_dropPeer.length());
			HWP::Keys::g_dropTime.removeRange(0, HWP::Keys::g_dropTime.length());
			HWP::Keys::SelfCheck();
			HWP::Keys::TrinketsLevelStart();
			if (Network::IsServer())
				HWP::Keys::PoolLevelStart();
			else
				HWP::Net::Request(HWP::Keys::POOL_GET);
		}

		void UpdateFrame(int ms, GameInput& gameInput, MenuInput& menuInput, bool paused) override
		{
			// clients keep the host's copy of their key counts fresh
			if (!Network::IsServer())
			{
				HWP::Keys::g_countTimer += ms;
				if (HWP::Keys::g_countTimer >= 500)
				{
					HWP::Keys::g_countTimer = 0;
					HWP::Keys::SendKeyCounts(false);
				}
			}
		}
	}
}

// One of the imp's random offers (WorldScript/Imp.as reflects over every
// ImpEffect): a key of the floor's tier for the party pool. Imp::Use runs on
// the user's own machine; a client asks the host to add it (keys.pool_add).
class HWPImpKeyEffect : ImpEffect
{
	bool IsAllowed(Player@ plr, float diffLvl)
	{
		return HWP::Keys::g_enabled && !g_inTown && plr !is null && plr.m_record !is null;
	}

	string Apply(Player@ plr, float diffLvl, UnitPtr impUnit)
	{
		int tier = HWP::Keys::FloorTier();
		string key = HWP::Keys::TIERS[tier - 1];
		HWP::Keys::PoolAdd(tier, 1);
		string name = Resources::GetString(".item.key." + key);
		LootLog::PresentPickup(plr.m_record, name, 1);
		HWP::Keys::RefreshHUD();
		HWP::Log("keys", "imp gave a " + key + " key");
		return Resources::GetString(".menu.imp.givemats", { { "mats", name } });
	}
}
