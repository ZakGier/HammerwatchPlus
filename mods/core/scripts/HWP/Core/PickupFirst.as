// Floor items before vendors. Player.GetTopUsable takes the first usable in m_usables that
// CanUse, and AddUsable keeps that list sorted by UsePriority, lowest first
// (Behaviors/Actors/Player/Player.as:135-167). A dropped item is 1 (Items/UnitBehavior.as:299)
// and NPCs, shops, chests and shrines are 0, so an item lying at a vendor's feet could not be
// picked up: the use key talked to the vendor. Each frame the local player's list is put in
// order as if an item were between -1 (revives, level exits) and 0.
//
// Not a class swap of Item::UnitBehavior: vanilla pets find items by the exact class name
// (FetchUnitsWithBehavior without includeInherited, Behaviors/MiniPet.as:284), so a subclass
// would never be picked up by a pet.
namespace HWP
{
	namespace PickupFirst
	{
		// UsePriority doubled, so an item can sit between -1 and 0
		int Rank(IUsable@ usable)
		{
			if (cast<Item::UnitBehavior>(usable) !is null)
				return -1;
			return usable.UsePriority() * 2;
		}

		void Update()
		{
			auto plr = GetLocalPlayer();
			if (plr is null)
				return;
			array<PlayerUsable@>@ list = plr.m_usables;
			// stable insertion sort: the list holds only what the player stands on
			bool moved = false;
			for (uint i = 1; i < list.length(); i++)
			{
				PlayerUsable@ cur = list[i];
				int rank = Rank(cur.m_usable);
				int j = int(i) - 1;
				while (j >= 0 && Rank(list[j].m_usable) > rank)
				{
					@list[j + 1] = list[j];
					j--;
				}
				if (j + 1 != int(i))
				{
					@list[j + 1] = cur;
					moved = true;
				}
			}
			if (moved)
				HWP::Log("core", "pickup first: an item moved ahead of " + list.length() + " usable(s)");
		}
	}
}
