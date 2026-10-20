// Valuables (Item::Valuable: vases, chalices, gems, wolf fur, scarab scales)
// turn straight into gold when picked up: PlayerRecord's pickup gives
// GetPrice() gold (PlayerRecord.as, the Item::Valuable branch). Each one's
// m_price is set to its vanilla price times valuables.gold_mult (2), and its
// pickup text with it. The vanilla price is kept, so setting the multiplier
// again (or the module being built again) never compounds. Every machine
// applies the host-synced multiplier, since each picker's own record pays out.
namespace HWP
{
	namespace Valuables
	{
		// tweak/items/items_valuables.sval; Item::Valuable has no list of its own
		array<string> IDS = {
			"scale_green", "wolf_fur", "chalice_bronze", "ceramic_vase", "copper_tankard",
			"brass_statuette", "fine_painting", "silver_goblet", "chalice_silver", "silver_mirror",
			"silver_plate", "ivory_figurine", "crystal_pitcher", "silk_handkerchief", "chalice_gold",
			"gold_statuette", "embroidered_tapestry", "jade_game_board", "jewelry_box", "gold_music_box",
			"masterpiece_painting", "adamant_statuette", "emerald", "sapphire", "ruby", "diamond" };

		dictionary g_base;   // id -> vanilla price
		float g_mult = 2.0f;
		int g_count = 0;

		void Apply()
		{
			g_mult = clamp(HWP::Settings::GetFloat("valuables.gold_mult", 2.0f), 0.0f, 20.0f);
			g_count = 0;
			for (uint i = 0; i < IDS.length(); i++)
			{
				auto v = Item::Valuable::Get(HashString(IDS[i]));
				if (v is null)
				{
					HWP::LogError("valuables", "missing valuable " + IDS[i]);
					continue;
				}
				int base;
				if (!g_base.get(IDS[i], base))
				{
					base = v.m_price;
					g_base.set(IDS[i], base);
				}
				v.m_price = int(base * g_mult + 0.5f);
				v.m_pickupTxt = v.m_name + " " + Resources::GetString(".hud.pickup.gold", {{ "amount", v.m_price }});
				g_count++;
			}
		}

		void OnSettingChanged(const string &in key)
		{
			if (key.findFirst("valuables.") == 0)
				Apply();
		}

		void CmdValuables(array<string>@ args)
		{
			// drop <id>: a valuable at your feet (host, in a run), for testing
			if (args.length() >= 1 && args[0] == "drop")
			{
				auto rec = GetLocalPlayerRecord();
				if (!Network::IsServer() || g_inTown || rec is null || rec.actor is null)
					return;
				string id = args.length() >= 2 ? args[1] : "ceramic_vase";
				auto d = Item::Valuable::Get(HashString(id));
				if (d is null)
				{
					HWP::LogError("valuables", "missing valuable " + id);
					return;
				}
				Item::DropItem(d, rec.actor.m_unit.GetPosition() + vec3(30, 0, 0), 1, false, null);
				HWP::Log("valuables", "dropped " + id + " worth " + d.m_price);
				return;
			}
			string example = "-";
			auto v = Item::Valuable::Get(HashString("ceramic_vase"));
			int base;
			if (v !is null && g_base.get("ceramic_vase", base))
				example = v.m_name + " " + base + " -> " + v.m_price;
			HWP::Commands::Reply(Resources::GetString(".hwp.valuables.status", {
				{ "mult", "" + g_mult }, { "count", g_count }, { "example", example } }));
		}
	}
}

namespace Modules
{
	class HWPValuablesModule : Module, HWP::ModuleStart
	{
		HWPValuablesModule()
		{
			super("hwp-valuables");
			HWP::Commands::OnSettingChanged(HWP::Commands::SettingListener(HWP::Valuables::OnSettingChanged));
			HWP::Commands::Register("valuables", " valuables' gold multiplier; 'drop <id>' drops one (host)", HWP::Commands::Handler(HWP::Valuables::CmdValuables));
			HWP::Valuables::Apply();
			HWP::Log("valuables", "self-check done: " + HWP::Valuables::g_count + " valuables at " + HWP::Valuables::g_mult + "x");
		}

		void Start(StartMode sMode)
		{
			HWP::Settings::Sync("valuables.");
			HWP::Valuables::Apply();
		}
	}
}
