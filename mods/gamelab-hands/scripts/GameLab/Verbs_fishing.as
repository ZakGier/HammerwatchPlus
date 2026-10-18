// gamelab-hands: verbs the fishing plan checks need (gamelab/bots/plan_fishing.py): the
// local main hand and bag as items (bagitems), equipping a bag item the way a click on it
// does (wield), an NPC's shop level (shoplevel), a click on a widget inside another one
// (pressin: an enchanter entry's own button), a widget's children with their captions
// (wchildren), button captions (wcaption) and the fishing window's reel, timed off its own
// bar widgets (sweepclick). The tooltip read is Verbs_farming's tooltip verb.
namespace GameLab
{
	// an equipment item as JSON: base id, name, quality bits, item level (base, upgrade,
	// the tooltip's text), modifier ids, attack skill, slot
	string FishItemJson(Equipment::Equipment@ eq, int index)
	{
		Json e;
		e.Int("index", index);
		auto it = cast<Equipment::Item>(eq);
		if (it is null)
		{
			e.Str("id", "").Str("type", eq is null ? "" : Reflect::GetTypeName(eq));
			return e.Close();
		}
		array<string> mods;
		for (uint i = 0; i < it.mods.length(); i++)
			mods.insertLast(it.mods[i] is null ? "?" : it.mods[i].m_id);
		e.Str("id", it.baseItem is null ? "" : it.baseItem.m_id).Str("name", it.GetName())
			.Int("quality", int(it.quality)).Int("ilvl", int(it.itemLevel)).Int("upgrade", int(it.upgradeLevel))
			.Str("ilvlText", it.GetItemLevelText()).Raw("mods", StrArray(mods))
			.Str("skill", it.baseItem is null || it.baseItem.skill is null ? "" : it.baseItem.skill.m_id)
			.Str("slot", Equipment::SlotToString(it.GetSlot()));
		return e.Close();
	}

	// bagitems: read-only. The local main hand and the bag (EquipmentInventory.m_items, at
	// most 32), each as FishItemJson, plus the floor's g_diffLevel and g_ngp (what a floor's
	// drops and catches are levelled by) and GetEquipmentDropLevelCap
	void VerbFishBagItems(const string &in id, array<string>@ args)
	{
		auto rec = GetLocalPlayerRecord();
		if (rec is null || rec.equipInventory is null || rec.equipped is null)
		{
			Fail(id, "no local player record");
			return;
		}
		array<string> items;
		for (uint i = 0; i < rec.equipInventory.m_items.length() && i < 32; i++)
			items.insertLast(FishItemJson(rec.equipInventory.m_items[i], int(i)));
		float diff = g_diffLevel;
		float ngp = g_ngp;
		Emit(Reply(id, true).Raw("main", FishItemJson(rec.equipped.m_items[EquippedItemsSlots::MainHand], -1))
			.Raw("bag", RawArray(items)).Int("count", rec.equipInventory.m_items.length()).Int("max", rec.equipInventory.m_maxItems)
			.Num("diffLevel", diff).Num("ngp", ngp).Int("dropCap", rec.GetEquipmentDropLevelCap()).Int("level", rec.level));
	}

	// wield <baseIdFilter>: the newest bag item whose base item id contains the filter, put
	// on the way a click on it in the bag does (EquipmentInventoryWidget.OnClick: MayEquip,
	// Remove from the bag, EquippedItems.Equip, the item it replaced back into the bag), then
	// the stats refresh VerbEquip does. Replies with the main hand after.
	void VerbFishWield(const string &in id, array<string>@ args)
	{
		auto rec = GetLocalPlayerRecord();
		if (rec is null || rec.equipInventory is null || rec.equipped is null)
		{
			Fail(id, "no local player record");
			return;
		}
		if (args.length() < 1)
		{
			Fail(id, "usage: wield <baseIdFilter>");
			return;
		}
		Equipment::Item@ pick = null;
		for (int i = int(rec.equipInventory.m_items.length()) - 1; i >= 0 && pick is null; i--)
		{
			auto it = cast<Equipment::Item>(rec.equipInventory.m_items[i]);
			if (it !is null && it.baseItem !is null && it.baseItem.m_id.findFirst(args[0]) >= 0)
				@pick = it;
		}
		if (pick is null)
		{
			Fail(id, "no bag item matching '" + args[0] + "'");
			return;
		}
		if (!rec.equipped.MayEquip(pick))
		{
			Fail(id, "MayEquip refused " + pick.baseItem.m_id + " (ilvl " + int(pick.itemLevel) + ", level " + rec.level + ")");
			return;
		}
		if (!rec.equipInventory.Remove(pick))
		{
			Fail(id, "the bag did not give up " + pick.baseItem.m_id);
			return;
		}
		auto got = rec.equipped.Equip(pick);
		if (got is pick)
		{
			rec.equipInventory.Add(pick);
			Fail(id, "equipped.Equip refused " + pick.baseItem.m_id);
			return;
		}
		if (got !is null)
			rec.equipInventory.Add(got);
		rec.RefreshStats();
		auto plr = cast<PlayerBase>(rec.actor);
		if (plr !is null)
			plr.RefreshModifiers();
		auto old = cast<Equipment::Item>(got);
		Emit(Reply(id, true).Raw("main", FishItemJson(rec.equipped.m_items[EquippedItemsSlots::MainHand], -1))
			.Str("replaced", old is null || old.baseItem is null ? "" : old.baseItem.m_id));
	}

	// shoplevel <filter> <level>: the ShopLevel field (what Use passes to the NPC's
	// interaction as its shop level; the town's prefabs set it) of the nearest
	// CompositeActorBehaviorNPC whose unit path contains the filter. A spawned enchanter has
	// ShopLevel 0, which offers no enchanting.
	void VerbFishShopLevel(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null || args.length() < 2)
		{
			Fail(id, plr is null ? "no spawned local player" : "usage: shoplevel <filter> <level>");
			return;
		}
		vec2 center = xy(plr.m_unit.GetPosition());
		auto units = g_scene.FetchAllUnits(~0, center, 3000);
		CompositeActorBehaviorNPC@ best = null;
		UnitPtr bestUnit;
		float bestDist = 0;
		for (uint i = 0; i < units.length(); i++)
		{
			if (!units[i].IsValid() || units[i].IsDestroyed() || units[i].GetDebugName().findFirst(args[0]) < 0)
				continue;
			auto npc = cast<CompositeActorBehaviorNPC>(units[i].GetScriptBehavior());
			if (npc is null)
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
			Fail(id, "no NPC matching '" + args[0] + "'");
			return;
		}
		int before = best.ShopLevel;
		best.ShopLevel = int(parseInt(args[1]));
		Emit(Reply(id, true).Str("unit", bestUnit.GetDebugName()).Int("before", before).Int("level", best.ShopLevel));
	}

	AWindowObject@ FishTopWindow()
	{
		auto gm = cast<BaseGameMode>(g_gameMode);
		if (gm is null || gm.m_windowManager is null)
			return null;
		return gm.m_windowManager.GetCurrentWindow();
	}

	// the widget with this id in the top window, else in its open tab (and that tab's open tab)
	Widget@ FishFindWidget(const string &in wid)
	{
		AWindowObject@ wnd = FishTopWindow();
		for (int depth = 0; depth < 4 && wnd !is null; depth++)
		{
			if (wnd.m_widget !is null)
			{
				Widget@ w = wnd.m_widget.GetWidgetById(wid);
				if (w !is null)
					return w;
			}
			auto tabs = TabsOf(wnd);
			if (tabs is null || tabs.m_currentIndex < 0 || tabs.m_currentIndex >= int(tabs.m_tabs.length()))
				break;
			AWindowObject@ next = tabs.m_tabs[tabs.m_currentIndex];
			if (next is wnd)
				break;
			@wnd = next;
		}
		return null;
	}

	// what a widget shows as text: a TextWidget's string, a button's caption (a BitmapString,
	// read back with GetText), an enchanter entry's or entry option's title
	string FishCaption(Widget@ w)
	{
		auto t = cast<TextWidget>(w);
		if (t !is null)
			return t.m_str;
		auto b = cast<ScalableSpriteButtonWidget>(w);
		if (b !is null)
			return b.m_text is null ? "" : b.m_text.GetText();
		auto entry = cast<EnchantEquipmentItem>(w);
		if (entry !is null)
			return entry.m_titleText is null ? "" : entry.m_titleText.GetText();
		auto eb = cast<EntryBaseWidget>(w);
		if (eb !is null)
			return eb.m_titleText is null ? "" : eb.m_titleText.GetText();
		return "";
	}

	// wcaption <widgetId...>: read-only. FishCaption of each named widget of the top window or
	// its open tab; ids not found are listed in "missing"
	void VerbFishCaption(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: wcaption <widgetId...>");
			return;
		}
		Json texts;
		string missing;
		for (uint i = 0; i < args.length() && i < 32; i++)
		{
			Widget@ w = FishFindWidget(args[i]);
			if (w is null)
			{
				missing += (missing.length() > 0 ? " " : "") + args[i];
				continue;
			}
			texts.Str(args[i], FishCaption(w));
		}
		Emit(Reply(id, true).Raw("texts", texts.Close()).Str("missing", missing));
	}

	void FishChildNodes(Widget@ w, int depth, int maxDepth, array<string>@ nodes)
	{
		if (w.m_children is null)
			return;
		for (uint i = 0; i < w.m_children.length() && nodes.length() < 60; i++)
		{
			Widget@ c = w.m_children[i];
			Json n;
			n.Int("depth", depth).Str("id", c.m_id).Str("type", Reflect::GetTypeName(c)).Bool("visible", c.m_visible)
				.Int("x", int(c.m_origin.x)).Int("y", int(c.m_origin.y)).Int("w", c.m_width).Int("h", c.m_height)
				.Str("caption", FishCaption(c));
			auto iw = cast<AInteractableWidget>(c);
			if (iw !is null)
				n.Bool("enabled", iw.m_enabled).Str("func", iw.m_func);
			auto opt = cast<EntryShopEnchantEquipmentItemOption>(c);
			if (opt !is null)
				n.Str("confirm", opt.m_funcConfirm);
			nodes.insertLast(n.Close());
			if (depth < maxDepth)
				FishChildNodes(c, depth + 1, maxDepth, nodes);
		}
	}

	// wchildren <widgetId|^widgetId> [depth]: read-only. The widget's children (default 2
	// levels, at most 60 nodes): id, type, visible, screen origin and size, caption, and for
	// interactables enabled and func (an enchanter entry option adds its confirm func:
	// "upgrade" / "enchant"). "^id": the children of that widget's parent (its siblings).
	void VerbFishChildren(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: wchildren <widgetId> [depth]");
			return;
		}
		bool up = args[0].substr(0, 1) == "^";
		string wid = up ? args[0].substr(1) : args[0];
		Widget@ w = FishFindWidget(wid);
		if (w !is null && up)
			@w = w.m_parent;
		if (w is null)
		{
			Fail(id, "no widget '" + args[0] + "' in the open window or its tabs");
			return;
		}
		int maxDepth = args.length() > 1 ? int(parseInt(args[1])) : 2;
		array<string> nodes;
		FishChildNodes(w, 1, maxDepth, nodes);
		Emit(Reply(id, true).Str("widget", Reflect::GetTypeName(w)).Bool("visible", w.m_visible).Raw("nodes", RawArray(nodes)));
	}

	// pressin <parentId> <childId>: click (ClickDown, ClickUp, as press does) the interactable
	// childId inside parentId of the top window: an enchanter entry (id = its equipment slot,
	// "0" the main hand) has its own button-1 / button-2. The reply goes out before the click,
	// so a script exception in the click's handler still leaves a reply.
	void VerbFishPressIn(const string &in id, array<string>@ args)
	{
		if (args.length() < 2)
		{
			Fail(id, "usage: pressin <parentId> <childId>");
			return;
		}
		Widget@ parent = FishFindWidget(args[0]);
		if (parent is null)
		{
			Fail(id, "no widget '" + args[0] + "' in the open window");
			return;
		}
		auto iw = cast<AInteractableWidget>(parent.GetWidgetById(args[1]));
		if (iw is null)
		{
			Fail(id, "no interactable widget '" + args[1] + "' in '" + args[0] + "'");
			return;
		}
		Json@ r = Reply(id, true).Str("widget", Reflect::GetTypeName(iw)).Bool("visible", iw.m_visible).Str("caption", FishCaption(iw));
		auto opt = cast<EntryShopEnchantEquipmentItemOption>(iw);
		if (opt !is null)
			r.Str("confirm", opt.m_funcConfirm);
		Emit(r);
		iw.ClickDown(false, vec2());
		iw.ClickUp(false, vec2());
	}

	// ---- sweepclick: one watch at a time, ticked by Modules::GameLabFishingVerbs

	bool g_sweepOn = false;
	string g_sweepId;
	string g_sweepButton;
	string g_sweepZone;
	array<string> g_sweepReport;
	int g_sweepBarW = 240;
	int g_sweepMarkerW = 3;
	array<int> g_sweepWidths;
	array<float> g_sweepSpeeds;
	int g_sweepMsLeft = 0;
	int g_sweepWindow = 2500;
	bool g_sweepSeen = false;
	float g_sweepPos = 0;
	int g_sweepDir = 1;
	float g_sweepSpeed = 0;
	int g_sweepMs = 0;
	int g_sweepFrames = 0;

	float FishSpeedFor(int width)
	{
		float best = 0;
		int bestGap = -1;
		for (uint i = 0; i < g_sweepWidths.length(); i++)
		{
			int gap = g_sweepWidths[i] - width;
			if (gap < 0)
				gap = -gap;
			if (bestGap < 0 || gap < bestGap)
			{
				bestGap = gap;
				best = g_sweepSpeeds[i];
			}
		}
		return best;
	}

	void FishSweepDone(const string &in result, AWindowObject@ wnd, int zx, int zw)
	{
		g_sweepOn = false;
		Json texts;
		for (uint i = 0; i < g_sweepReport.length(); i++)
		{
			Widget@ w = wnd is null || wnd.m_widget is null ? null : wnd.m_widget.GetWidgetById(g_sweepReport[i]);
			texts.Str(g_sweepReport[i], w is null ? "" : FishCaption(w));
		}
		Json j;
		Emit(j.Str("ev", "sweepclick").Str("id", g_sweepId).Str("result", result).Int("zx", zx).Int("zw", zw)
			.Num("p", g_sweepPos).Num("speed", g_sweepSpeed).Int("ms", g_sweepMs).Int("frames", g_sweepFrames)
			.Raw("texts", texts.Close()));
	}

	// every frame, paused ones too (the fishing window pauses the game): from the frame the
	// zone widget turns visible the marker is integrated as the window's Update moves it
	// (speed x ms, bouncing at barW - markerW; that Update runs before the modules'
	// UpdateFrame with the same ms: AGameplayGameMode.UpdatePausedFrame), and the button is
	// clicked on the first frame the marker lies inside the zone (a margin of up to 2 px)
	void FishTickSweep(int ms)
	{
		if (!g_sweepOn)
			return;
		g_sweepMsLeft -= ms;
		g_sweepFrames++;
		auto wnd = FishTopWindow();
		Widget@ zone = wnd is null || wnd.m_widget is null ? null : wnd.m_widget.GetWidgetById(g_sweepZone);
		if (zone is null)
		{
			FishSweepDone("closed", wnd, 0, 0);
			return;
		}
		int zx = int(zone.m_offset.x);
		int zw = zone.m_width;
		if (!zone.m_visible)
		{
			if (g_sweepSeen)
				FishSweepDone("gone", wnd, zx, zw);
			else if (g_sweepMsLeft <= 0)
				FishSweepDone("timeout", wnd, zx, zw);
			return;
		}
		if (!g_sweepSeen)
		{
			g_sweepSeen = true;
			g_sweepPos = 0;
			g_sweepDir = 1;
			g_sweepMs = 0;
			g_sweepSpeed = FishSpeedFor(zw);
		}
		else
		{
			float maxX = float(g_sweepBarW - g_sweepMarkerW);
			g_sweepPos += g_sweepSpeed * float(ms) * float(g_sweepDir);
			if (g_sweepPos >= maxX)
			{
				g_sweepPos = 2.0f * maxX - g_sweepPos;
				g_sweepDir = -1;
			}
			else if (g_sweepPos <= 0)
			{
				g_sweepPos = -g_sweepPos;
				g_sweepDir = 1;
			}
			g_sweepPos = clamp(g_sweepPos, 0.0f, maxX);
			g_sweepMs += ms;
		}
		if (g_sweepMs >= g_sweepWindow - 50)
		{
			FishSweepDone("late", wnd, zx, zw);
			return;
		}
		float margin = min(2.0f, float(zw) / 4.0f);
		if (g_sweepPos + float(g_sweepMarkerW) >= float(zx) + margin && g_sweepPos <= float(zx + zw) - margin)
		{
			auto btn = cast<AInteractableWidget>(wnd.m_widget.GetWidgetById(g_sweepButton));
			if (btn is null)
			{
				FishSweepDone("nobutton", wnd, zx, zw);
				return;
			}
			g_sweepOn = false;
			btn.ClickDown(false, vec2());
			btn.ClickUp(false, vec2());
			FishSweepDone("clicked", wnd, zx, zw);
		}
	}

	// sweepclick <buttonId> <zoneId> <barW> <markerW> <width:speed[,width:speed...]> [timeoutMs] [windowMs] [reportId,reportId...]:
	// clicks buttonId now (the fishing window's Cast), then watches zoneId (the catch zone:
	// its width and m_offset.x) and clicks buttonId again while the moving marker is inside it
	// (Reel). The speed (px per ms) is the table entry nearest the zone's width (the zone's
	// width gives the fish tier). The reply comes at once; the outcome arrives as
	// {"ev":"sweepclick","id":<this id>,"result":"clicked"|"timeout"|"gone"|"late"|"closed",
	// "zx","zw","p","speed","ms","frames","texts":{reportId: caption}}, texts read right after.
	void VerbFishSweepClick(const string &in id, array<string>@ args)
	{
		if (args.length() < 5)
		{
			Fail(id, "usage: sweepclick <buttonId> <zoneId> <barW> <markerW> <width:speed,...> [timeoutMs] [windowMs] [reportIds]");
			return;
		}
		auto wnd = FishTopWindow();
		AInteractableWidget@ btn = null;
		if (wnd !is null && wnd.m_widget !is null)
			@btn = cast<AInteractableWidget>(wnd.m_widget.GetWidgetById(args[0]));
		if (btn is null)
		{
			Fail(id, "no interactable widget '" + args[0] + "' in the top window");
			return;
		}
		if (wnd.m_widget.GetWidgetById(args[1]) is null)
		{
			Fail(id, "no widget '" + args[1] + "' in the top window");
			return;
		}
		g_sweepWidths.removeRange(0, g_sweepWidths.length());
		g_sweepSpeeds.removeRange(0, g_sweepSpeeds.length());
		auto pairs = args[4].split(",");
		for (uint i = 0; i < pairs.length(); i++)
		{
			auto kv = pairs[i].split(":");
			if (kv.length() != 2)
				continue;
			g_sweepWidths.insertLast(int(parseInt(kv[0])));
			g_sweepSpeeds.insertLast(float(parseFloat(kv[1])));
		}
		if (g_sweepWidths.length() == 0)
		{
			Fail(id, "no width:speed pairs in '" + args[4] + "'");
			return;
		}
		g_sweepId = id;
		g_sweepButton = args[0];
		g_sweepZone = args[1];
		g_sweepBarW = int(parseInt(args[2]));
		g_sweepMarkerW = int(parseInt(args[3]));
		g_sweepMsLeft = args.length() > 5 ? int(parseInt(args[5])) : 8000;
		g_sweepWindow = args.length() > 6 ? int(parseInt(args[6])) : 2500;
		g_sweepReport.removeRange(0, g_sweepReport.length());
		if (args.length() > 7)
			g_sweepReport = args[7].split(",");
		g_sweepSeen = false;
		g_sweepPos = 0;
		g_sweepDir = 1;
		g_sweepSpeed = 0;
		g_sweepMs = 0;
		g_sweepFrames = 0;
		Emit(Reply(id, true).Str("window", Reflect::GetTypeName(wnd)).Int("pairs", g_sweepWidths.length()));
		btn.ClickDown(false, vec2());
		btn.ClickUp(false, vec2());
		g_sweepOn = true;
	}

	void Register_fishing()
	{
		RegisterVerb("bagitems", "", Verb(VerbFishBagItems));
		RegisterVerb("wield", "<baseIdFilter>", Verb(VerbFishWield));
		RegisterVerb("shoplevel", "<filter> <level>", Verb(VerbFishShopLevel));
		RegisterVerb("wcaption", "<widgetId...>", Verb(VerbFishCaption));
		RegisterVerb("wchildren", "<widgetId> [depth]", Verb(VerbFishChildren));
		RegisterVerb("pressin", "<parentId> <childId>", Verb(VerbFishPressIn));
		RegisterVerb("sweepclick", "<buttonId> <zoneId> <barW> <markerW> <width:speed,...> [timeoutMs] [windowMs] [reportIds]", Verb(VerbFishSweepClick));
	}
}

namespace Modules
{
	// ticks sweepclick on every frame, paused ones included (QueuedTasks skips paused frames)
	class GameLabFishingVerbs : Module
	{
		GameLabFishingVerbs()
		{
			super("gamelab-fishing-verbs");
		}

		void UpdateFrame(int ms, GameInput& gameInput, MenuInput& menuInput, bool paused) override
		{
			GameLab::FishTickSweep(ms);
		}
	}
}
