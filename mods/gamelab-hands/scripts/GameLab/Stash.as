// gamelab-hands: town stash verbs. stashitem fills tab 0 with generated items the
// way VerbEquip makes them; stash reads a tab's order back; press clicks a widget
// in the top window (ClickDown then ClickUp, as a keyboard confirm would).
namespace GameLab
{
	TownStashTab@ StashTab(const string &in id, int index)
	{
		if (g_myTownRecord is null || g_myTownRecord.m_townStash is null)
		{
			Fail(id, "no town stash");
			return null;
		}
		array<TownStashTab@>@ tabs = g_myTownRecord.m_townStash.m_tabs;
		if (index < 0 || index >= int(tabs.length()))
		{
			Fail(id, "no stash tab " + index + " (" + tabs.length() + " tabs)");
			return null;
		}
		return tabs[index];
	}

	// stashitem <baseItemId> <quality> [ilvl]: Equipment::Generator into stash tab 0
	void VerbStashItem(const string &in id, array<string>@ args)
	{
		if (args.length() < 2)
		{
			Fail(id, "usage: stashitem <baseItemId> <quality> [ilvl]");
			return;
		}
		auto tab = StashTab(id, 0);
		if (tab is null)
			return;
		auto baseItem = Equipment::BaseItem::Get(args[0]);
		if (baseItem is null)
		{
			Fail(id, "no base item '" + args[0] + "'");
			return;
		}
		auto rec = GetLocalPlayerRecord();
		Equipment::Generator gen;
		gen.m_ilvl = args.length() > 2 ? int(parseInt(args[2])) : (rec is null ? 1 : rec.level);
		gen.m_qualities = Item::ParseQuality(args[1]);
		auto item = gen.GenerateItem(baseItem);
		if (item is null)
		{
			Fail(id, "GenerateItem returned null for " + args[0] + " " + args[1]);
			return;
		}
		tab.Add(item);
		Emit(Reply(id, true).Str("item", args[0]).Int("ilvl", gen.m_ilvl).Int("count", tab.m_items.length()));
	}

	// stash [tab]: the tab's items in order, "<baseId>@<ilvl>"
	void VerbStash(const string &in id, array<string>@ args)
	{
		auto tab = StashTab(id, args.length() > 0 ? int(parseInt(args[0])) : 0);
		if (tab is null)
			return;
		array<string> items;
		for (uint i = 0; i < tab.m_items.length(); i++)
		{
			auto it = cast<Equipment::Item>(tab.m_items[i]);
			items.insertLast(it is null ? "?" : it.baseItem.m_id + "@" + it.GetItemLevel());
		}
		Emit(Reply(id, true).Str("name", tab.m_name).Raw("items", StrArray(items)));
	}

	// press <widgetId>: click an interactable widget of the top window
	void VerbPress(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: press <widgetId>");
			return;
		}
		auto gm = cast<BaseGameMode>(g_gameMode);
		AWindowObject@ wnd;
		if (gm !is null && gm.m_windowManager !is null)
			@wnd = gm.m_windowManager.GetCurrentWindow();
		if (wnd is null || wnd.m_widget is null)
		{
			Fail(id, "no open window");
			return;
		}
		auto iw = cast<AInteractableWidget>(wnd.m_widget.GetWidgetById(args[0]));
		if (iw is null)
		{
			Fail(id, "no interactable widget '" + args[0] + "' in " + Reflect::GetTypeName(wnd));
			return;
		}
		iw.ClickDown(false, vec2());
		iw.ClickUp(false, vec2());
		Emit(Reply(id, true).Str("window", Reflect::GetTypeName(wnd)).Str("widget", Reflect::GetTypeName(iw)));
	}

	// func <name...>: the top window's own OnFunc(null, name), the handler its buttons and
	// key bindings call (MissionLoadoutMenu.Play is OnFunc "play"), for a window whose
	// button has no widget id to press
	void VerbFunc(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: func <name...>");
			return;
		}
		auto gm = cast<BaseGameMode>(g_gameMode);
		AWindowObject@ wnd;
		if (gm !is null && gm.m_windowManager !is null)
			@wnd = gm.m_windowManager.GetCurrentWindow();
		if (wnd is null)
		{
			Fail(id, "no open window");
			return;
		}
		string name = args[0];
		for (uint i = 1; i < args.length(); i++)
			name += " " + args[i];
		Emit(Reply(id, true).Str("window", Reflect::GetTypeName(wnd)).Str("func", name));
		wnd.OnFunc(null, name);
	}
}
