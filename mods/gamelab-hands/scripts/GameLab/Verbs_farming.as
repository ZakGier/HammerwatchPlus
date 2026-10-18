// gamelab-hands: verbs the farming plan checks need (gamelab/bots/plan_farming.py): a town
// grown big enough for the farm's crop fields and farmer (buildup), and the tooltip a widget
// shows when it is hovered, read back as text (tooltip).
namespace GameLab
{
	// buildup <buildingId> [steps]: the town builder's upgrade (Town/BuildingBuilder.as
	// "variation": IncrementVariationOnBuilding, then SavePlayerAndTown) without the cost and
	// the cutscene. steps > 1 sets the tiers below the target first, so the town reloads once.
	// Replies with the tier before and after, the last tier, and the town's building steps
	// (the sum of variation + 1, what "town num building steps" conditionals count).
	void VerbFarmBuildUp(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: buildup <buildingId> [steps]");
			return;
		}
		auto gm = cast<AGameplayGameMode>(g_gameMode);
		if (gm is null || g_myTownRecord is null || !g_inTown || !Network::IsServer())
		{
			Fail(id, "not the host in town");
			return;
		}
		auto def = BuildingManagement::BuildingDef::Get(HashString(args[0]));
		if (def is null)
		{
			Fail(id, "no building '" + args[0] + "'");
			return;
		}
		BuildingManagement::PlacedBuilding@ placed = null;
		for (uint i = 0; i < g_myTownRecord.m_buildings.length() && placed is null; i++)
		{
			if (g_myTownRecord.m_buildings[i].buildingDef is def)
				@placed = g_myTownRecord.m_buildings[i];
		}
		if (placed is null)
		{
			Fail(id, "'" + args[0] + "' is not built (build it first)");
			return;
		}
		int steps = args.length() > 1 ? int(parseInt(args[1])) : 1;
		if (steps < 1)
			steps = 1;
		int last = int(def.m_variations.length()) - 1;
		int before = int(placed.variation);
		int target = before + steps;
		if (target > last)
			target = last;
		if (target > before)
		{
			if (target - 1 > before)
				placed.variation = uint(target - 1);
			g_myTownRecord.IncrementVariationOnBuilding(def);
			gm.SavePlayerAndTown();
		}
		int total = 0;
		for (uint i = 0; i < g_myTownRecord.m_buildings.length(); i++)
			total += int(g_myTownRecord.m_buildings[i].variation) + 1;
		Emit(Reply(id, true).Str("building", args[0]).Int("from", before).Int("variation", int(placed.variation))
			.Int("last", last).Int("townSteps", total));
	}

	// the widget with this id in the top window, else in its open tab (and that tab's open
	// tab): the character screen's gear slots live in PlayerMenuCharacterTab
	Widget@ FarmFindWidget(const string &in wid, string &out where)
	{
		where = "";
		auto gm = cast<BaseGameMode>(g_gameMode);
		if (gm is null || gm.m_windowManager is null)
			return null;
		AWindowObject@ wnd = gm.m_windowManager.GetCurrentWindow();
		for (int depth = 0; depth < 4 && wnd !is null; depth++)
		{
			if (wnd.m_widget !is null)
			{
				Widget@ w = wnd.m_widget.GetWidgetById(wid);
				if (w !is null)
				{
					where = Reflect::GetTypeName(wnd);
					return w;
				}
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

	// tooltip <widgetId>: the widget's own ShowTooltip(), what hovering it does
	// (EquipmentItemWidget.Hover / Highlight), then the open tooltip's text blocks
	// (ToolTip.m_blocks: a TextBlock's m_sText, a TitleBlock's title and subtitle) are read
	// and the tooltip is closed again. Replies with the widget's type, whether it is visible,
	// the tooltip's type ("" for none) and its texts, title first.
	void VerbFarmTooltip(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: tooltip <widgetId>");
			return;
		}
		auto gm = cast<BaseGameMode>(g_gameMode);
		if (gm is null || gm.m_windowManager is null)
		{
			Fail(id, "no window manager");
			return;
		}
		string where;
		Widget@ w = FarmFindWidget(args[0], where);
		if (w is null)
		{
			Fail(id, "no widget '" + args[0] + "' in the open window or its tabs");
			return;
		}
		gm.m_windowManager.CloseTooltip();
		w.ShowTooltip();
		array<string> texts;
		ITooltip@ itt = gm.m_windowManager.m_tooltip;
		string ttType = itt is null ? "" : Reflect::GetTypeName(itt);
		auto tt = cast<ToolTip>(itt);
		if (tt !is null && tt.m_blocks !is null && tt.m_blocks.m_blocks !is null)
		{
			for (uint i = 0; i < tt.m_blocks.m_blocks.length(); i++)
			{
				auto text = cast<ScalableBlocks::TextBlock>(tt.m_blocks.m_blocks[i]);
				if (text !is null)
				{
					texts.insertLast(text.m_sText);
					continue;
				}
				auto title = cast<ScalableBlocks::TitleBlock>(tt.m_blocks.m_blocks[i]);
				if (title !is null)
				{
					texts.insertLast(title.m_sTitle);
					if (!title.m_sSubTitle.isEmpty())
						texts.insertLast(title.m_sSubTitle);
				}
			}
		}
		gm.m_windowManager.CloseTooltip();
		Emit(Reply(id, true).Str("window", where).Str("widget", Reflect::GetTypeName(w)).Bool("visible", w.m_visible)
			.Str("tooltip", ttType).Raw("texts", StrArray(texts)));
	}

	void Register_farming()
	{
		RegisterVerb("buildup", "<buildingId> [steps]", Verb(VerbFarmBuildUp));
		RegisterVerb("tooltip", "<widgetId>", Verb(VerbFarmTooltip));
	}
}
