// Settings-backed town doodads. A Placeable is one unit the host places in
// town: its position lives in the town record as <prefix>_x / <prefix>_y, it is
// spawned shortly after a town load (host only) and 'hwp <cmd> here' moves it
// to where the host stands. Modules create one in their constructor:
//
//   @g_portal = HWP::Town::Placeable("campaign", "campaign.portal", PORTAL_UNIT, -1700, 250);
//   @g_portal.m_locate = LocatePortal;   (optional, see below)
//   Start:       g_portal.OnLoad();   (HWP::ModuleStart)
//   UpdateFrame: g_portal.Update(ms, g_enabled);
//   'hwp x here': g_portal.MoveHere();   'hwp x reset': g_portal.Reset();
//
// Without a saved spot the unit stands where m_locate finds one in this town
// (it runs on every machine when the unit is placed, so it can also hide a
// local vanilla doodad there), else at the fixed default. A building upgrade
// rebuilds the town without a new Start and takes our unit with it: once a
// second the host respawns it when it is gone, and every machine places again
// when m_stale says the town changed under it.
namespace HWP
{
	namespace Town
	{
		const int SPAWN_DELAY_MS = 600; // let the town finish placing its own units first
		const int WATCH_MS = 1000;
		const int UNSET = -99999;       // <prefix>_x/_y value of "no saved spot"

		// a spot found in this town (true), e.g. next to a vanilla unit
		funcdef bool PlaceableLocate(vec3 &out pos);
		// the town was rebuilt since the last placement (all machines)
		funcdef bool PlaceableStale();

		// The chapel's Pyre slot, where the unbuilt Pyre's campfire burns. Where
		// TownRecord::SpawnTown puts it: the base town segment (set
		// town_segment_base) places the chapel, any tier, at a grid cell of its
		// placed-prefabs; the chapel places pyre_tier_0.pfb (or the built Pyre)
		// at its unbuilt-placed-prefabs cell; cells are 16 px. The campaign
		// portal stands here, so modules can place things beside it.
		const vec2 FIRE_IN_PYRE = vec2(8, 8);

		bool IsBuildingPrefab(BuildingManagement::BuildingDef@ def, Prefab@ pfb)
		{
			if (def.m_unbuiltPrefab is pfb)
				return true;
			for (uint i = 0; i < def.m_variations.length(); i++)
			{
				if (def.m_variations[i].m_prefab is pfb)
					return true;
			}
			return false;
		}

		// world position of the chapel's Pyre slot (the campfire's spot); false
		// when this town layout has no chapel
		bool ChapelPyreSpot(vec2 &out pos)
		{
			BuildingManagement::BuildingDef@ chapel = null;
			for (uint i = 0; i < BuildingManagement::BuildingDef::Instances.length(); i++)
			{
				if (BuildingManagement::BuildingDef::Instances[i].m_id == "chapel")
					@chapel = BuildingManagement::BuildingDef::Instances[i];
			}
			if (chapel is null || chapel.m_unbuiltPlacedPrefabs.length() == 0)
				return false;
			uint baseSet = HashString("town_segment_base");
			for (uint i = 0; i < MissionPrefabDef::Instances.length(); i++)
			{
				auto seg = MissionPrefabDef::Instances[i];
				if (seg.m_set != baseSet)
					continue;
				for (uint j = 0; j < seg.m_placedPrefabs.length(); j++)
				{
					auto pfb = Resources::GetPrefab(seg.m_placedPrefabs[j].m_id);
					if (pfb is null || !IsBuildingPrefab(chapel, pfb))
						continue;
					ivec2 cell = seg.m_placedPrefabs[j].m_pos + seg.m_gridOffset + chapel.m_unbuiltPlacedPrefabs[0].m_pos;
					pos = vec2(float(cell.x * 16), float(cell.y * 16)) + FIRE_IN_PYRE;
					return true;
				}
			}
			return false;
		}

		// the local player pays gold for a town purchase; false (nothing paid)
		// when short
		bool PayGold(int price)
		{
			auto rec = GetLocalPlayerRecord();
			if (rec is null || price < 0 || rec.GetMaterial(MaterialType::Gold) < price)
				return false;
			rec.GiveMaterial(MaterialType::Gold, -price, true);
			return true;
		}

		// True when u is still a live HWP unit (its unit file is under an hwp
		// folder or named hwp_*). A building upgrade reloads the town level in the
		// same scene and reuses unit ids, so a UnitPtr kept from before can come
		// back valid on a vanilla tree or NPC: never Destroy() a kept pointer
		// without this check.
		bool Ours(UnitPtr u)
		{
			if (!u.IsValid() || u.IsDestroyed())
				return false;
			auto prod = u.GetUnitProducer();
			return prod !is null && prod.GetResourceName().findFirst("/hwp") >= 0;
		}

		// Ours, and still the unit file it was spawned from: a kept pointer whose id the
		// reloaded town gave to another of our units (a farm plot on the old pet vendor's
		// id) is not this one any more. For single fixed units (vendor, well, bowl).
		bool Is(UnitPtr u, const string &in unitPath)
		{
			if (!Ours(u))
				return false;
			return u.GetUnitProducer() is Resources::GetUnitProducer(unitPath);
		}

		// A unit a module spawns once per town load at a fixed spot (the gambler,
		// the notice board). A building upgrade reloads the town level without a
		// new Start and destroys it; Due() says, at most once a second while in
		// town, that it is gone. hostOnly: only the host spawns it (netsynced).
		// The reloaded level reuses unit ids, so the old UnitPtr can come back
		// valid on some other unit: the producer is checked too.
		class Kept
		{
			UnitPtr m_unit;
			UnitProducer@ m_prod;
			int m_ms = 0;
			bool m_hostOnly;

			Kept(bool hostOnly = true) { m_hostOnly = hostOnly; }

			void Reset() { m_unit = UnitPtr(); @m_prod = null; m_ms = 0; }

			void Set(UnitPtr unit)
			{
				m_unit = unit;
				@m_prod = unit.IsValid() ? unit.GetUnitProducer() : null;
			}

			bool Due(int ms)
			{
				if (!g_inTown || (m_hostOnly && !Network::IsServer()))
					return false;
				m_ms += ms;
				if (m_ms < WATCH_MS)
					return false;
				m_ms = 0;
				if (!m_unit.IsValid() || m_unit.IsDestroyed())
					return true;
				if (m_prod !is null && m_unit.GetUnitProducer() !is m_prod)
				{
					HWP::Log("core", "kept unit id " + m_unit.GetId() + " now holds "
						+ m_unit.GetUnitProducer().GetResourceName() + ": spawning "
						+ m_prod.GetResourceName() + " again");
					return true;
				}
				return false;
			}
		}

		class Placeable
		{
			string m_tag;      // log tag / module name
			string m_prefix;   // settings prefix, e.g. "wave.statue"
			string m_unitPath;
			int m_defX;
			int m_defY;
			UnitPtr m_unit;
			bool m_spawnDone = true;
			int m_delay = 0;
			int m_watchMs = 0;
			bool m_failed = false;  // the unit file is missing: don't retry every second
			PlaceableLocate@ m_locate;
			PlaceableStale@ m_stale;
			bool m_hasAuto = false;
			vec3 m_auto;

			Placeable(const string &in tag, const string &in prefix, const string &in unitPath, int defX, int defY)
			{
				m_tag = tag;
				m_prefix = prefix;
				m_unitPath = unitPath;
				m_defX = defX;
				m_defY = defY;
			}

			// the host saved a spot ('hwp <cmd> here')
			bool Custom()
			{
				return HWP::Settings::GetInt(m_prefix + "_x", UNSET) != UNSET
					&& HWP::Settings::GetInt(m_prefix + "_y", UNSET) != UNSET;
			}

			vec3 Pos()
			{
				if (Custom())
					return vec3(float(HWP::Settings::GetInt(m_prefix + "_x", m_defX)),
						float(HWP::Settings::GetInt(m_prefix + "_y", m_defY)), 0.0f);
				if (m_hasAuto)
					return m_auto;
				return vec3(float(m_defX), float(m_defY), 0.0f);
			}

			void Spawn(vec3 pos)
			{
				if (Ours(m_unit))
					m_unit.Destroy();
				auto prod = Resources::GetUnitProducer(m_unitPath);
				if (prod is null)
				{
					HWP::LogError(m_tag, "missing " + m_unitPath);
					m_failed = true;
					return;
				}
				m_unit = prod.Produce(g_scene, pos);
				HWP::Log(m_tag, m_unitPath + " spawned at " + pos.x + "," + pos.y);
			}

			// HWP::ModuleStart::Start
			void OnLoad()
			{
				m_unit = UnitPtr();
				m_spawnDone = false;
				m_delay = 0;
				m_watchMs = 0;
				m_hasAuto = false;
			}

			// Module::UpdateFrame: places once per town load (the unit on the
			// host, m_locate everywhere), then watches for town rebuilds
			void Update(int ms, bool enabled)
			{
				if (m_spawnDone)
				{
					Watch(ms, enabled);
					return;
				}
				m_delay += ms;
				if (m_delay < SPAWN_DELAY_MS)
					return;
				m_spawnDone = true;
				Place(enabled);
			}

			void Place(bool enabled)
			{
				if (!enabled || !g_inTown)
					return;
				m_hasAuto = m_locate !is null && m_locate(m_auto);
				if (Network::IsServer())
					Spawn(Pos());
			}

			void Watch(int ms, bool enabled)
			{
				m_watchMs += ms;
				if (m_watchMs < WATCH_MS)
					return;
				m_watchMs = 0;
				if (!enabled || !g_inTown || m_failed)
					return;
				bool gone = Network::IsServer() && (!m_unit.IsValid() || m_unit.IsDestroyed()
					|| m_unit.GetUnitProducer().GetResourceName() != m_unitPath); // a reused unit id
				if (gone || (m_stale !is null && m_stale()))
				{
					HWP::Log(m_tag, "the town was rebuilt, placing " + m_unitPath + " again");
					Place(enabled);
				}
			}

			// 'hwp <cmd> here' (host): save the local player's position and
			// respawn there when in town. Replies to the chat itself.
			void MoveHere()
			{
				if (!Network::IsServer())
				{
					HWP::Commands::Reply(Resources::GetString(".hwp.town.host_only"));
					return;
				}
				auto rec = GetLocalPlayerRecord();
				if (rec is null || rec.actor is null)
				{
					HWP::Commands::Reply(Resources::GetString(".hwp.town.no_actor"));
					return;
				}
				auto p = rec.actor.m_unit.GetPosition();
				int x = int(p.x);
				int y = int(p.y);
				HWP::Settings::SetInt(m_prefix + "_x", x);
				HWP::Settings::SetInt(m_prefix + "_y", y);
				HWP::Commands::NotifySettingChanged(m_prefix + "_x");
				HWP::Commands::NotifySettingChanged(m_prefix + "_y");
				if (g_inTown)
					Spawn(vec3(float(x), float(y), 0.0f));
				HWP::Commands::Reply(Resources::GetString(".hwp.town.moved", { { "what", m_tag }, { "x", x }, { "y", y } }));
			}

			// 'hwp <cmd> reset' (host): forget the saved spot, back to the
			// located (or default) one
			void Reset()
			{
				if (!Network::IsServer())
				{
					HWP::Commands::Reply(Resources::GetString(".hwp.town.host_only"));
					return;
				}
				HWP::Settings::SetInt(m_prefix + "_x", UNSET);
				HWP::Settings::SetInt(m_prefix + "_y", UNSET);
				HWP::Commands::NotifySettingChanged(m_prefix + "_x");
				HWP::Commands::NotifySettingChanged(m_prefix + "_y");
				if (g_inTown)
					Place(true);
				auto p = Pos();
				HWP::Commands::Reply(Resources::GetString(".hwp.town.reset", { { "what", m_tag }, { "x", int(p.x) }, { "y", int(p.y) } }));
			}
		}
	}
}

// Behaviour of town units a module spawns on every machine (netsync none:
// fishing spots, the pirate, farm plots, the well): a vanilla NPC that keeps
// its duplicates (vanilla removes all but one NPC of a unit type on the host).
class HWPLocalNPC : CompositeActorBehaviorNPC
{
	HWPLocalNPC(UnitPtr unit, SValue& params) { super(unit, params); }

	void CheckForExistance() override {}
}
