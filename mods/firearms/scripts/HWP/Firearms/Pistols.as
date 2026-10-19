// One pistol for either hand. Drops, shops and the bag only hold the main-hand pistols
// (hwp_glock_mh_0N). Clicking one in the bag while the main hand is full (and not
// two-handed) and the off hand is free swaps it for its off-hand twin (hwp_glock_oh_0N)
// first, through core's HWP::Bag::OnEquip, so it lands in the off hand. A twin back in the
// bag (unequipped, or bumped off by a two-handed weapon) turns into the main-hand pistol
// again. The twins never drop: spawn-chance 0 and an item level range nothing rolls.
namespace HWP
{
	namespace Firearms
	{
		const array<string> PISTOL_MAIN = { "hwp_glock_mh_01", "hwp_glock_mh_02", "hwp_glock_mh_03" };
		const array<string> PISTOL_OFF = { "hwp_glock_oh_01", "hwp_glock_oh_02", "hwp_glock_oh_03" };

		int g_pistolCheck = 0;

		// item's base item swapped for the same index in to, when it is in from; true when swapped
		bool SwapPistol(Equipment::Equipment@ item, const array<string>@ from, const array<string>@ to)
		{
			auto it = cast<Equipment::Item>(item);
			if (it is null || it.baseItem is null)
				return false;
			int i = from.find(it.baseItem.m_id);
			if (i < 0)
				return false;
			auto twin = Equipment::BaseItem::Get(to[i]);
			if (twin is null)
				return false;
			@it.baseItem = twin;
			return true;
		}

		void PistolEquip(PlayerRecord@ rec, Equipment::Equipment@ item)
		{
			if (rec is null || rec.equipped is null)
				return;
			auto mh = rec.equipped.m_items[EquippedItemsSlots::MainHand];
			auto oh = rec.equipped.m_items[EquippedItemsSlots::OffHand];
			if (mh is null || mh.GetSlot() == Equipment::Slot::TwoHanded || oh !is null)
				return;
			if (SwapPistol(item, PISTOL_MAIN, PISTOL_OFF))
				HWP::Log("firearms", "pistol to the off hand: " + cast<Equipment::Item>(item).baseItem.m_id);
		}

		// off-hand twins in the local bag back to main-hand pistols, a few times a second
		void UpdatePistols(int ms)
		{
			g_pistolCheck -= ms;
			if (g_pistolCheck > 0)
				return;
			g_pistolCheck = 250;
			auto rec = GetLocalPlayerRecord();
			if (rec is null || rec.equipInventory is null)
				return;
			for (uint i = 0; i < rec.equipInventory.m_items.length(); i++)
			{
				if (SwapPistol(rec.equipInventory.m_items[i], PISTOL_OFF, PISTOL_MAIN))
				{
					rec.equipInventory.m_isDirty = true;
					HWP::Log("firearms", "pistol back in the bag as " + cast<Equipment::Item>(rec.equipInventory.m_items[i]).baseItem.m_id);
				}
			}
		}
	}
}
