// The town stash's Sort button (gui/player_stash/player_stash.gui, declared
// override): sorts the open stash tab by class (the item's main requirement:
// str, dex, int, foc, vit), then by type (weapons by family - two-handed,
// main hand, off hand - then head, chest, hands, feet, back), then by item
// level (highest first), quality and name. The stash is the local player's
// own town record, so this runs on every machine for itself.
namespace HWP
{
	namespace Stash
	{
		// the requirement stat that matters most (largest value); 5 = none
		int ClassRank(Equipment::Item@ item)
		{
			auto req = item.GetRequirements();
			array<int> vals = { req.m_str, req.m_dex, req.m_int, req.m_foc, req.m_vit };
			int best = 5;
			int bestVal = 0;
			for (uint i = 0; i < vals.length(); i++)
			{
				if (vals[i] > bestVal)
				{
					best = int(i);
					bestVal = vals[i];
				}
			}
			return best;
		}

		int SlotRank(Equipment::Slot slot)
		{
			switch (slot)
			{
				case Equipment::Slot::TwoHanded: return 0;
				case Equipment::Slot::MainHand: return 1;
				case Equipment::Slot::OffHand: return 2;
				case Equipment::Slot::Head: return 3;
				case Equipment::Slot::Chest: return 4;
				case Equipment::Slot::Hands: return 5;
				case Equipment::Slot::Feet: return 6;
				case Equipment::Slot::Back: return 7;
			}
			return 8;
		}

		// a weapon's family from its id: mainhand_mace_01 -> mace
		string Family(Equipment::Item@ item)
		{
			auto parts = item.baseItem.m_id.split("_");
			return parts.length() > 1 ? parts[1] : item.baseItem.m_id;
		}

		bool IsWeapon(Equipment::Slot slot)
		{
			return slot == Equipment::Slot::TwoHanded || slot == Equipment::Slot::MainHand || slot == Equipment::Slot::OffHand;
		}

		// -1, 0, 1: a before b, same, b before a
		int Compare(Equipment::Equipment@ a, Equipment::Equipment@ b)
		{
			auto ia = cast<Equipment::Item>(a);
			auto ib = cast<Equipment::Item>(b);
			if (ia is null || ib is null)
				return ia !is null ? -1 : (ib !is null ? 1 : 0); // other kinds last
			int d = ClassRank(ia) - ClassRank(ib);
			if (d == 0)
				d = SlotRank(ia.GetSlot()) - SlotRank(ib.GetSlot());
			if (d == 0 && IsWeapon(ia.GetSlot()))
			{
				string fa = Family(ia);
				string fb = Family(ib);
				d = fa < fb ? -1 : (fa > fb ? 1 : 0);
			}
			if (d == 0)
				d = ib.GetItemLevel() - ia.GetItemLevel();
			if (d == 0)
				d = int(ib.GetQuality()) - int(ia.GetQuality());
			if (d == 0)
			{
				string na = ia.GetName();
				string nb = ib.GetName();
				d = na < nb ? -1 : (na > nb ? 1 : 0);
			}
			return d < 0 ? -1 : (d > 0 ? 1 : 0);
		}

		// stable insertion sort (a stash tab holds a few hundred items at most);
		// true when the order changed
		bool Sort(array<Equipment::Equipment@>@ items)
		{
			bool moved = false;
			for (uint i = 1; i < items.length(); i++)
			{
				Equipment::Equipment@ cur = items[i];
				int j = int(i) - 1;
				while (j >= 0 && Compare(items[j], cur) > 0)
				{
					@items[j + 1] = items[j];
					j--;
					moved = true;
				}
				@items[j + 1] = cur;
			}
			return moved;
		}

		void SortWindow(PlayerStashWindow@ wnd)
		{
			if (wnd is null || wnd.m_townStash is null || wnd.m_tabIndex >= wnd.m_townStash.m_tabs.length())
				return;
			auto tab = wnd.m_townStash.m_tabs[wnd.m_tabIndex];
			bool moved = Sort(tab.m_items);
			HWP::Log("stash", "sorted " + tab.m_items.length() + " item(s) in tab '" + tab.m_name + "'" + (moved ? "" : " (already in order)"));
			if (!moved)
				return;
			wnd.Refresh();
			wnd.SaveStash();
		}
	}
}

// The game's scalable button, minus the func: the stash window's OnFunc sends
// every func it does not know to Refresh, so the click sorts here instead.
class HWPStashSortButton : ScalableSpriteButtonWidget
{
	Widget@ Clone() override
	{
		HWPStashSortButton@ w = HWPStashSortButton();
		CloneInto(w);
		return w;
	}

	void ClickUp(bool usingMouse, vec2 mousePos) override
	{
		// the press counts as the base button decides: released over it (mouse)
		vec2 mp = mousePos - m_origin;
		bool fire = m_buttonDown && (!usingMouse || (mp.x >= 0.0f && mp.y >= 0.0f && mp.x < m_width && mp.y < m_height));
		ScalableSpriteButtonWidget::ClickUp(usingMouse, mousePos);
		if (fire)
			HWP::Stash::SortWindow(cast<PlayerStashWindow>(m_host));
	}
}

ref@ LoadHWPStashSortButton(WidgetLoadingContext &ctx)
{
	HWPStashSortButton@ w = HWPStashSortButton();
	w.Load(ctx);
	return w;
}

namespace HWPStash
{
	[Hook]
	void LoadWidgetProducers(GUIBuilder@ builder)
	{
		builder.AddWidgetProducer("hwp-stash-sort", LoadHWPStashSortButton);
	}
}
