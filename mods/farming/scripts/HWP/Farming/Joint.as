// Joints. A Holy Herb is rolled into an off-hand item from the materials tab (Plants & Herbs:
// click a herb, "Roll J?" -> "Huzzah!"; RollJoint). An item saves only its base item, quality,
// level and mods, so the puffs left are the base item: hwp_joint_<strain>_<n>, n = 5..1
// (tweak/hwp/equipment_joints.sval), each with its own icon and model.
//
// - Held, it smoulders: the item re-applies a buff whose fx is a thin wisp.
// - Right click is its off-hand skill (players/hwp/farming/attacks_joint.sval). At the cast
//   point HWPJointPuff runs on every machine: the tip turns cherry red for LIT_MS (the
//   _lit model, swapped into the item's cached model the way Firearms' HeldModel.as swaps a
//   gun in) and, in a run room or a town building, a haze is left that thins out over a
//   minute (puffs stack). On the smoker's machine it also gives the strain's buff for
//   HERB_FLOORS floors (FarmingModule.as ApplyHerb) and, once the tip cools, burns the joint
//   down a stage; the last puff uses it up.
// - Someone with a free off hand next to a player holding a joint takes it with the
//   interact key, no questions asked (the host relays: JOINT_TAKE -> JOINT_HAND -> JOINT_GIVE
//   -> JOINT_GET).
namespace HWP
{
	namespace Farming
	{
		const int JOINT_USES = 5;
		const int LIT_MS = 1500;
		const float TAKE_RANGE = 26.0f;
		const string JOINT_PREFIX = "hwp_joint_";
		const string LIT_MODEL = "players/models/equipment/hwp_joint_%n%_lit.model";
		const string HAZE_FX = "effects/hwp/joint_haze.effect";
		const string JOINT_TAKE = "farm.joint_take"; // taker -> host: { holder }
		const string JOINT_HAND = "farm.joint_hand"; // host -> holder: { taker }
		const string JOINT_GIVE = "farm.joint_give"; // holder -> host: { taker, id }
		const string JOINT_GET = "farm.joint_get";   // host -> taker: { id }

		int g_rolled = 0;
		int g_puffs = 0;
		int g_hazes = 0;
		int g_taken = 0;
		int g_given = 0;

		string JointId(const string &in strain, int uses) { return JOINT_PREFIX + strain + "_" + uses; }

		// hwp_joint_<strain>_<n> -> strain and n; false for anything else
		bool ParseJointId(const string &in id, string &out strain, int &out uses)
		{
			if (id.findFirst(JOINT_PREFIX) != 0)
				return false;
			int us = id.findLast("_");
			if (us <= int(JOINT_PREFIX.length()))
				return false;
			strain = id.substr(JOINT_PREFIX.length(), us - JOINT_PREFIX.length());
			uses = int(parseInt(id.substr(us + 1)));
			return uses >= 1 && uses <= JOINT_USES && GetSeed(strain) !is null;
		}

		bool ParseJoint(Equipment::Equipment@ eq, string &out strain, int &out uses)
		{
			auto item = cast<Equipment::Item>(eq);
			if (item is null || item.baseItem is null)
				return false;
			return ParseJointId(item.baseItem.m_id, strain, uses);
		}

		bool IsJoint(Equipment::Equipment@ eq)
		{
			string strain;
			int uses;
			return ParseJoint(eq, strain, uses);
		}

		Equipment::Item@ MakeJointById(const string &in id)
		{
			auto base = Equipment::BaseItem::Get(id);
			if (base is null)
			{
				HWP::LogError("farming", "no joint item " + id + " (tweak/hwp/equipment_joints.sval)");
				return null;
			}
			// as Generator.GenerateItem(BaseItem) (EquipmentGenerator.as:331) without its
			// VerifyItem: the joints' never-set conditional keeps them out of random drops
			Equipment::Generator gen;
			gen.m_ilvl = 1;
			Equipment::Item item;
			item.quality = Item::Quality::Common;
			@item.baseItem = base;
			gen.GenerateItemMods(item, 1, null);
			item.Finalize(randf(), 1, 0, null, null);
			return item;
		}

		Equipment::Equipment@ OffHand(PlayerRecord@ rec)
		{
			if (rec is null || rec.equipped is null)
				return null;
			return rec.equipped.m_items[int(EquippedItemsSlots::OffHand)];
		}

		void RefreshGear(PlayerRecord@ rec)
		{
			rec.RefreshStats();
			auto plr = cast<PlayerBase>(rec.actor);
			if (plr !is null)
				plr.RefreshModifiers();
		}

		// ---- rolling (the materials tab) ----------------------------------------

		bool RollJoint(const string &in strain)
		{
			auto rec = GetLocalPlayerRecord();
			auto seed = GetSeed(strain);
			if (rec is null || seed is null || !seed.herb)
				return false;
			if (HWP::Market::Count(rec, strain) <= 0)
			{
				Say(Resources::GetString(".hwp.farming.no_herb", { { "name", seed.Name() } }));
				return false;
			}
			if (!rec.equipInventory.CanAdd())
			{
				Say(Resources::GetString(".hwp.farming.joint.bag_full"));
				return false;
			}
			auto joint = MakeJointById(JointId(strain, JOINT_USES));
			if (joint is null)
				return false;
			HWP::Market::Take(rec, strain, 1);
			rec.equipInventory.Add(joint);
			g_rolled++;
			string text = Resources::GetString(".hwp.farming.joint.rolled", { { "name", joint.GetName() } });
			Say(text);
			HWP::Commands::Reply(text);
			HWP::Log("farming", "rolled a " + strain + " joint (" + HWP::Market::Count(rec, strain) + " left)");
			return true;
		}

		// ---- the red tip (every machine) ----------------------------------------

		class LitJoint
		{
			PlayerBase@ m_player;
			Equipment::Equipment@ m_item;
			CustomUnitModel@ m_was;
			int m_ms;
		}
		array<LitJoint@> g_lit;
		dictionary g_litModels;

		CustomUnitModel@ LitModel(int uses)
		{
			string path = LIT_MODEL.replace("%n%", "" + uses);
			CustomUnitModel@ model;
			if (g_litModels.get(path, @model))
				return model;
			auto res = Resources::GetModel(path);
			if (res is null)
			{
				HWP::Log("farming", "lit joint model missing: " + path);
				return null;
			}
			@model = CustomUnitModel(res, g_plrMat);
			g_litModels.set(path, @model);
			return model;
		}

		void Unlight(LitJoint@ lit)
		{
			@lit.m_item.m_modelTmp = lit.m_was;
			if (lit.m_player !is null && lit.m_player.m_unit.IsValid())
				lit.m_player.RefreshScene();
		}

		void LightUp(PlayerBase@ player)
		{
			if (player is null)
				return;
			auto off = player.GetEquipment(EquippedItemsSlots::OffHand);
			string strain;
			int uses;
			if (!ParseJoint(off, strain, uses))
				return;
			auto model = LitModel(uses);
			if (model is null)
				return;
			for (uint i = 0; i < g_lit.length(); i++)
			{
				if (g_lit[i].m_player is player && g_lit[i].m_item is off)
				{
					g_lit[i].m_ms = LIT_MS;
					return;
				}
			}
			LitJoint lit;
			@lit.m_player = player;
			@lit.m_item = off;
			@lit.m_was = off.m_modelTmp;
			lit.m_ms = LIT_MS;
			g_lit.insertLast(lit);
			@off.m_modelTmp = model;
			player.RefreshScene();
		}

		// ---- the haze (every machine) -------------------------------------------

		// In town only inside a building: the vanilla interiors are edged with
		// env_mask_ceiling_inside_* tiles, so there are some on every side of you.
		bool Indoors(vec2 pos)
		{
			bool l = false, r = false, u = false, d = false;
			auto units = g_scene.FetchAllUnits(~0, pos, 220);
			for (uint i = 0; i < units.length(); i++)
			{
				if (!units[i].IsValid() || units[i].GetDebugName().findFirst("env_mask_ceiling_inside") < 0)
					continue;
				vec2 at = xy(units[i].GetPosition());
				if (dist(pos, at) > 220)
					continue;
				if (at.x < pos.x) l = true; else r = true;
				if (at.y < pos.y) u = true; else d = true;
			}
			return l && r && u && d;
		}

		void SpawnHaze(PlayerBase@ player)
		{
			if (player is null || !player.m_unit.IsValid())
				return;
			vec2 pos = xy(player.m_unit.GetPosition());
			if (g_inTown && !Indoors(pos))
				return;
			PlayEffect(HAZE_FX, pos);
			g_hazes++;
		}

		// ---- puffing --------------------------------------------------------------

		// the smoker's own machine: the joint to burn down once its tip cools
		PlayerBase@ g_burnPlayer;
		Equipment::Equipment@ g_burnItem;
		int g_burnMs = 0;

		void Puffed(PlayerBase@ player)
		{
			LightUp(player);
			SpawnHaze(player);
			if (player is null || player.m_record is null || !player.m_record.local)
				return;
			auto rec = player.m_record;
			auto off = OffHand(rec);
			string strain;
			int uses;
			if (!ParseJoint(off, strain, uses))
				return;
			g_puffs++;
			ApplyHerb(rec, strain);
			@g_burnPlayer = player;
			@g_burnItem = off;
			g_burnMs = LIT_MS;
			HWP::Log("farming", "puffed a " + strain + " joint (" + uses + " -> " + (uses - 1) + " puffs)");
		}

		void BurnDown()
		{
			auto player = g_burnPlayer;
			auto item = g_burnItem;
			@g_burnPlayer = null;
			@g_burnItem = null;
			if (player is null || player.m_record is null)
				return;
			auto rec = player.m_record;
			auto off = OffHand(rec);
			string strain;
			int uses;
			// taken, swapped or dropped meanwhile: it is someone else's now
			if (off !is item || !ParseJoint(off, strain, uses))
				return;
			if (uses <= 1)
			{
				rec.equipped.Unequip(EquippedItemsSlots::OffHand);
				RefreshGear(rec);
				Say(Resources::GetString(".hwp.farming.joint.done"));
				HWP::Log("farming", "the " + strain + " joint is smoked down");
				return;
			}
			auto next = MakeJointById(JointId(strain, uses - 1));
			if (next is null)
				return;
			rec.equipped.Equip(next, EquippedItemsSlots::OffHand);
			RefreshGear(rec);
		}

		void UpdateJoints(int ms)
		{
			for (int i = int(g_lit.length()) - 1; i >= 0; i--)
			{
				auto lit = g_lit[i];
				lit.m_ms -= ms;
				if (lit.m_ms > 0 && lit.m_player.m_unit.IsValid())
					continue;
				Unlight(lit);
				g_lit.removeAt(i);
			}
			if (g_burnItem !is null)
			{
				g_burnMs -= ms;
				if (g_burnMs <= 0)
					BurnDown();
			}
		}

		void ClearJoints()
		{
			for (uint i = 0; i < g_lit.length(); i++)
				Unlight(g_lit[i]);
			g_lit.removeRange(0, g_lit.length());
			// a level change mid-puff: the stage still burns
			if (g_burnItem !is null)
				BurnDown();
		}

		// ---- passing it on --------------------------------------------------------

		PlayerRecord@ g_offerFrom; // the holder whose joint the hint was shown for

		bool FreeOffHand(PlayerRecord@ rec)
		{
			if (rec is null || rec.equipped is null || rec.IsDead())
				return false;
			auto main = rec.equipped.m_items[int(EquippedItemsSlots::MainHand)];
			if (main !is null && main.GetSlot() == Equipment::Slot::TwoHanded)
				return false;
			return OffHand(rec) is null;
		}

		// the nearest other player holding a joint within reach of mine, or null
		PlayerRecord@ JointHolderNear(PlayerRecord@ me)
		{
			auto plr = cast<PlayerBase>(me.actor);
			if (plr is null || !plr.m_unit.IsValid())
				return null;
			vec2 at = xy(plr.m_unit.GetPosition());
			PlayerRecord@ best = null;
			float bestD = TAKE_RANGE;
			for (uint i = 0; i < g_players.length(); i++)
			{
				auto other = g_players[i];
				if (other is null || other is me || other.peer == 255 || other.IsDead() || !IsJoint(OffHand(other)))
					continue;
				auto op = cast<PlayerBase>(other.actor);
				if (op is null || !op.m_unit.IsValid())
					continue;
				float d = dist(at, xy(op.m_unit.GetPosition()));
				if (d <= bestD)
				{
					bestD = d;
					@best = other;
				}
			}
			return best;
		}

		void PollTake(GameInput& gameInput)
		{
			auto me = GetLocalPlayerRecord();
			auto holder = FreeOffHand(me) ? JointHolderNear(me) : null;
			if (holder is null)
			{
				@g_offerFrom = null;
				return;
			}
			if (holder !is g_offerFrom)
			{
				@g_offerFrom = holder;
				auto op = cast<PlayerBase>(holder.actor);
				AddFloatingText(FloatingTextType::Pickup, Resources::GetString(".hwp.farming.joint.take_hint", {
					{ "key", FormatKeyName(GetActionBinding("Use")) }, { "name", holder.GetName() } }), op.m_unit.GetPosition());
			}
			if (!gameInput.Use.Pressed)
				return;
			SValueBuilder b;
			b.PushDictionary();
			b.PushInteger("holder", holder.peer);
			b.PopDictionary();
			HWP::Net::Request(JOINT_TAKE, b.Build());
			HWP::Log("farming", "asked " + holder.GetName() + " for the joint");
		}

		// host
		void OnJointTake(uint8 peer, SValue@ data)
		{
			int holder = HWP::SV::Int(data, "holder", -1);
			if (holder < 0 || holder == int(peer))
				return;
			SValueBuilder b;
			b.PushDictionary();
			b.PushInteger("taker", peer);
			b.PopDictionary();
			HWP::Net::Send(uint8(holder), JOINT_HAND, b.Build());
		}

		// the holder: hand it over if it is still in my hand
		void OnJointHand(SValue@ data)
		{
			int taker = HWP::SV::Int(data, "taker", -1);
			auto rec = GetLocalPlayerRecord();
			auto off = OffHand(rec);
			auto item = cast<Equipment::Item>(off);
			if (taker < 0 || item is null || !IsJoint(off))
				return;
			if (g_burnItem is off)
			{
				BurnDown(); // the stage burns first; what is left goes over
				@off = OffHand(rec);
				@item = cast<Equipment::Item>(off);
				if (item is null || !IsJoint(off))
					return;
			}
			string id = item.baseItem.m_id;
			rec.equipped.Unequip(EquippedItemsSlots::OffHand);
			RefreshGear(rec);
			g_given++;
			auto taker_ = GetPlayerRecordByPeer(uint8(taker));
			Say(Resources::GetString(".hwp.farming.joint.taken_from", { { "name", taker_ is null ? "?" : taker_.GetName() } }));
			HWP::Log("farming", "handed the joint (" + id + ") to peer " + taker);
			SValueBuilder b;
			b.PushDictionary();
			b.PushInteger("taker", taker);
			b.PushString("id", id);
			b.PopDictionary();
			HWP::Net::Request(JOINT_GIVE, b.Build());
		}

		// host
		void OnJointGive(uint8 peer, SValue@ data)
		{
			int taker = HWP::SV::Int(data, "taker", -1);
			string id = HWP::SV::Str(data, "id");
			if (taker < 0 || id.isEmpty())
				return;
			SValueBuilder b;
			b.PushDictionary();
			b.PushString("id", id);
			b.PopDictionary();
			HWP::Net::Send(uint8(taker), JOINT_GET, b.Build());
		}

		// the taker: into the off hand, or the bag if it was filled meanwhile
		void OnJointGet(SValue@ data)
		{
			string id = HWP::SV::Str(data, "id");
			string strain;
			int uses;
			auto rec = GetLocalPlayerRecord();
			if (rec is null || !ParseJointId(id, strain, uses))
				return;
			auto joint = MakeJointById(id);
			if (joint is null)
				return;
			g_taken++;
			if (FreeOffHand(rec) && rec.equipped.Equip(joint, EquippedItemsSlots::OffHand) !is joint)
			{
				RefreshGear(rec);
				HWP::Log("farming", "took a joint (" + id + ") into the off hand");
			}
			else if (rec.equipInventory.CanAdd())
			{
				rec.equipInventory.Add(joint);
				HWP::Log("farming", "took a joint (" + id + ") into the bag");
			}
			else
			{
				auto plr = cast<PlayerBase>(rec.actor);
				if (plr !is null)
					Item::DropItem(joint, plr.m_unit.GetPosition(), 1, true, rec);
				HWP::Log("farming", "took a joint (" + id + "); hands and bag full, at my feet");
			}
			Say(Resources::GetString(".hwp.farming.joint.took", { { "name", joint.GetName() } }));
		}

		string JointStatus()
		{
			auto rec = GetLocalPlayerRecord();
			string strain;
			int uses;
			string held = ParseJoint(OffHand(rec), strain, uses) ? strain + " " + uses + "/" + JOINT_USES : "none";
			return "joint: held " + held + ", rolled " + g_rolled + ", puffs " + g_puffs + ", hazes " + g_hazes
				+ ", lit " + g_lit.length() + ", taken " + g_taken + ", given " + g_given + "; " + HerbStatus();
		}
	}
}

// the cast-point action of hwp_joint_puff (attacks_joint.sval)
class HWPJointPuff : IAction
{
	HWPJointPuff(UnitPtr unit, SValue& params) {}

	void CancelAction() {}
	void SetWeaponInformation(uint weapon) {}
	bool NeedNetParams() { return false; }
	void Update(int dt, int cooldown) {}

	bool DoAction(SValueBuilder@ builder, Actor@ owner, Actor@ target, vec2 pos, vec2 dir, float intensity)
	{
		HWP::Farming::Puffed(cast<PlayerBase>(owner));
		return true;
	}

	bool NetDoAction(SValue@ param, Actor@ owner, vec2 pos, vec2 dir)
	{
		HWP::Farming::Puffed(cast<PlayerBase>(owner));
		return true;
	}
}

// "Roll J?" -> "Huzzah!" (HWPHarvestMaterial.Click)
class HWPRollJointHost : IWidgetHoster
{
	string m_strain;
	HWPRollJointHost(const string &in strain) { m_strain = strain; }

	void OnFunc(Widget@ sender, const string &in name) override
	{
		if (name == "hwproll yes")
			HWP::Farming::RollJoint(m_strain);
	}
}
