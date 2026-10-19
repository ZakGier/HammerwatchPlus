// gamelab-hands: NPC and shop verbs. use walks the real interaction path
// (IUsable.Use, as the use key does); shop reads or buys from the open
// ShopWindow through its own OnFunc("buy"); trinkets lists the run bag.
namespace GameLab
{
	// shoplevel <filter> <level>: sets ShopLevel on every NPC within 3000 px whose unit or
	// behaviour name contains filter, as a town building's placement does (the [Editable]
	// field of CompositeActorBehaviorNPC / StateActorBehaviorNPC, NPCBehavior.as:244/431, which
	// NPCBehavior passes to Interact). A spawned Skill Trainer starts at 0: tier 0 only
	// (WindowSkillTrainer.as:192); 4 opens every tier.
	void VerbShopLevel(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null || args.length() < 2)
		{
			Fail(id, plr is null ? "no spawned local player" : "usage: shoplevel <filter> <level>");
			return;
		}
		int level = int(parseInt(args[1]));
		auto units = g_scene.FetchAllUnits(~0, xy(plr.m_unit.GetPosition()), 3000);
		int n = 0;
		for (uint i = 0; i < units.length(); i++)
		{
			if (!units[i].IsValid() || units[i].IsDestroyed())
				continue;
			ref@ b = units[i].GetScriptBehavior();
			if (units[i].GetDebugName().findFirst(args[0]) < 0 && Reflect::GetTypeName(b).findFirst(args[0]) < 0)
				continue;
			auto c = cast<CompositeActorBehaviorNPC>(b);
			auto st = cast<StateActorBehaviorNPC>(b);
			if (c !is null)
				c.ShopLevel = level;
			else if (st !is null)
				st.ShopLevel = level;
			else
				continue;
			n++;
		}
		if (n == 0)
		{
			Fail(id, "no NPC matching '" + args[0] + "'");
			return;
		}
		Emit(Reply(id, true).Int("n", n).Int("level", level));
	}

	// use <filter>: IUsable.Use of the nearest usable unit whose unit path or
	// behaviour matches, from wherever the player stands
	void VerbUse(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null || args.length() < 1)
		{
			Fail(id, plr is null ? "no spawned local player" : "usage: use <filter>");
			return;
		}
		vec2 center = xy(plr.m_unit.GetPosition());
		auto units = g_scene.FetchAllUnits(~0, center, 3000);
		IUsable@ best;
		UnitPtr bestUnit;
		float bestDist = 0;
		for (uint i = 0; i < units.length(); i++)
		{
			if (!units[i].IsValid() || units[i].IsDestroyed())
				continue;
			ref@ b = units[i].GetScriptBehavior();
			auto npc = cast<IUsable>(b);
			if (npc is null || (units[i].GetDebugName().findFirst(args[0]) < 0 && Reflect::GetTypeName(b).findFirst(args[0]) < 0))
				continue;
			float d = dist(center, xy(units[i].GetPosition()));
			if (best is null || d < bestDist)
			{
				@best = npc;
				bestUnit = units[i];
				bestDist = d;
			}
		}
		if (best is null)
		{
			Fail(id, "no usable unit matching '" + args[0] + "'");
			return;
		}
		best.Use(plr);
		auto gm = cast<BaseGameMode>(g_gameMode);
		AWindowObject@ wnd;
		if (gm !is null && gm.m_windowManager !is null)
			@wnd = gm.m_windowManager.GetCurrentWindow();
		Emit(Reply(id, true).Str("unit", bestUnit.GetDebugName()).Str("window", wnd is null ? "" : Reflect::GetTypeName(wnd)));
	}

	ShopWindow@ TopShop(const string &in id)
	{
		auto gm = cast<BaseGameMode>(g_gameMode);
		ShopWindow@ shop;
		if (gm !is null && gm.m_windowManager !is null)
			@shop = cast<ShopWindow>(gm.m_windowManager.GetCurrentWindow());
		if (shop is null)
			Fail(id, "the top window is not a ShopWindow");
		return shop;
	}

	const uint SHOP_TEXT = 60;

	string Cut(const string &in text)
	{
		return text.length() <= SHOP_TEXT ? text : text.substr(0, SHOP_TEXT);
	}

	string ShopJson(ShopWindow@ shop)
	{
		array<string> items;
		auto rec = GetLocalPlayerRecord();
		for (uint i = 0; i < shop.m_shopItems.length(); i++)
		{
			auto it = shop.m_shopItems[i];
			auto cost = it.GetCost();
			Json e;
			// title and subtitle cut to SHOP_TEXT chars: a pet shop's 40 entries stay under the reply cap
			e.Str("id", it.GetID()).Str("title", Cut(it.GetTitle())).Int("gold", cost is null ? 0 : cost.GetCost(MaterialType::Gold))
				.Bool("available", it.IsAvailable(rec)).Bool("icon", it.GetIcon() !is null).Str("sub", Cut(it.GetSubTitle()));
			items.insertLast(e.Close());
		}
		return RawArray(items);
	}

	// shop [buy <index>]: the open shop's entries (id, title, gold price, IsAvailable, icon, subtitle); buy presses
	// entry <index> the way a click does (ShopWindow.OnFunc "buy")
	void VerbShop(const string &in id, array<string>@ args)
	{
		auto shop = TopShop(id);
		if (shop is null)
			return;
		bool bought = false;
		if (args.length() >= 2 && args[0] == "buy")
		{
			int index = int(parseInt(args[1]));
			if (index < 0 || index >= int(shop.m_itemList.m_children.length()))
			{
				Fail(id, "no entry " + index + " (" + shop.m_itemList.m_children.length() + ")");
				return;
			}
			uint before = shop.m_shopItems.length();
			string what = shop.m_shopItems[index].GetID();
			shop.OnFunc(shop.m_itemList.m_children[index], "buy");
			bought = shop.m_shopItems.length() != before || shop.m_shopItems[index].GetID() != what;
		}
		auto rec = GetLocalPlayerRecord();
		Emit(Reply(id, true).Str("window", Reflect::GetTypeName(shop)).Bool("changed", bought).Int("count", shop.m_shopItems.length())
			.Int("gold", rec is null ? 0 : rec.GetMaterial(MaterialType::Gold)).Raw("items", ShopJson(shop)));
	}

	// trinkets: the local character's run trinkets, by id
	void VerbTrinkets(const string &in id, array<string>@ args)
	{
		auto rec = GetLocalPlayerRecord();
		if (rec is null)
		{
			Fail(id, "no local player record");
			return;
		}
		array<string> ids;
		for (uint i = 0; i < rec.trinketInventory.m_items.length(); i++)
			ids.insertLast(rec.trinketInventory.m_items[i].m_id);
		Emit(Reply(id, true).Int("count", ids.length()).Raw("ids", StrArray(ids)));
	}
}
