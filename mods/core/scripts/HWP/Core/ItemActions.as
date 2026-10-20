// Extra actions on a bag item (eat a fish, ...). A module registers an Action in
// its ctor (script globals reset every level); the inventory shows the first one
// that has a label for the hovered item as one more key hint, clickable, and its
// key does it (droptrade's Character tab and EquipmentItemWidget, which own the
// hints). Without droptrade the actions are still there for `hwp` commands.
namespace HWP
{
	namespace ItemActions
	{
		class Action
		{
			// the hint's verb for this item ("Eat"), or "" when it isn't for this item
			string Label(Equipment::Equipment@ item) { return ""; }
			// do it to the local player's item; the action takes the item out of the bag
			// itself when it is used up
			void Do(PlayerRecord@ record, Equipment::Equipment@ item) {}
		}

		array<Action@> g_actions;

		void Register(Action@ action)
		{
			g_actions.insertLast(action);
		}

		Action@ For(Equipment::Equipment@ item)
		{
			if (item is null)
				return null;
			for (uint i = 0; i < g_actions.length(); i++)
				if (g_actions[i].Label(item) != "")
					return g_actions[i];
			return null;
		}

		string Label(Equipment::Equipment@ item)
		{
			auto a = For(item);
			return a is null ? "" : a.Label(item);
		}

		// true when an action ran
		bool Do(PlayerRecord@ record, Equipment::Equipment@ item)
		{
			auto a = For(item);
			if (a is null || record is null)
				return false;
			a.Do(record, item);
			HWP::Gear::Changed();
			return true;
		}
	}
}
