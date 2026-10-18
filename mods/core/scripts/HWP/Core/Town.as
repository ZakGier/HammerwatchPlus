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
				if (m_unit.IsValid())
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
				bool gone = Network::IsServer() && (!m_unit.IsValid() || m_unit.IsDestroyed());
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
