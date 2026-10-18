// gamelab-hands: stash verbs for the newa test plan (mods/stash Sort on more than one
// tab). stashput fills any tab, making the tabs up to it the way the stash's own "new
// tab" does (TownStash.CreateTab); stashclear empties one, so a check starts from a
// known tab whatever the fixture's town held.
namespace GameLab
{
	// stashput <tab> <baseItemId> <quality> [ilvl]: Equipment::Generator into stash tab <tab> (as stashitem), creating tabs "tab N" up to it (TownStash.CreateTab)
	void VerbStashPut(const string &in id, array<string>@ args)
	{
		if (args.length() < 3)
		{
			Fail(id, "usage: stashput <tab> <baseItemId> <quality> [ilvl]");
			return;
		}
		if (g_myTownRecord is null || g_myTownRecord.m_townStash is null)
		{
			Fail(id, "no town stash");
			return;
		}
		int index = int(parseInt(args[0]));
		if (index < 0 || index > 7)
		{
			Fail(id, "tab " + index + " out of range (0-7)");
			return;
		}
		auto stash = g_myTownRecord.m_townStash;
		while (int(stash.m_tabs.length()) <= index)
			stash.CreateTab("tab " + (stash.m_tabs.length() + 1));
		auto baseItem = Equipment::BaseItem::Get(args[1]);
		if (baseItem is null)
		{
			Fail(id, "no base item '" + args[1] + "'");
			return;
		}
		auto rec = GetLocalPlayerRecord();
		Equipment::Generator gen;
		gen.m_ilvl = args.length() > 3 ? int(parseInt(args[3])) : (rec is null ? 1 : rec.level);
		gen.m_qualities = Item::ParseQuality(args[2]);
		auto item = gen.GenerateItem(baseItem);
		if (item is null)
		{
			Fail(id, "GenerateItem returned null for " + args[1] + " " + args[2]);
			return;
		}
		auto tab = stash.m_tabs[index];
		tab.Add(item);
		Emit(Reply(id, true).Str("item", args[1]).Int("tab", index).Str("name", tab.m_name).Int("ilvl", gen.m_ilvl)
			.Int("count", tab.m_items.length()).Int("tabs", stash.m_tabs.length()));
	}

	// stashclear <tab>: empty stash tab <tab> (TownStashTab.m_items), the tab itself stays
	void VerbStashClear(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: stashclear <tab>");
			return;
		}
		auto tab = StashTab(id, int(parseInt(args[0])));
		if (tab is null)
			return;
		int removed = int(tab.m_items.length());
		tab.m_items.resize(0);
		Emit(Reply(id, true).Str("name", tab.m_name).Int("removed", removed));
	}

	void Register_newa()
	{
		RegisterVerb("stashput", "<tab> <baseItemId> <quality> [ilvl]", Verb(VerbStashPut));
		RegisterVerb("stashclear", "<tab>", Verb(VerbStashClear));
	}
}
