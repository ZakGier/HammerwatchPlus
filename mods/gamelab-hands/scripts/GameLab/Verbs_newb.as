// gamelab-hands: widget reads for the newb test plan (mods/architect challenges).
// The Architect picker sits over the mission loadout menu, whose tree can use up the
// widgets dump's character budget (WIDGET_CHARS) before the picker's own lines are
// reached; wtext reads just the named widgets of the top window. The picker's rows set
// their tooltip from their func-hover (SelectArchitectSelector.OnFunc "hover"), not from
// ShowTooltip, so hovertip hovers the row itself and reads the tooltip that opened.
namespace GameLab
{
	// wtext <widgetId...>: read-only. The text (TextWidget.m_str) of each named widget of the top window, "" for a widget that is not a TextWidget; ids not found are listed in "missing"
	void VerbWText(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: wtext <widgetId...>");
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
		Json texts;
		string missing;
		for (uint i = 0; i < args.length() && i < 32; i++)
		{
			Widget@ w = wnd.m_widget.GetWidgetById(args[i]);
			if (w is null)
			{
				missing += (missing.length() > 0 ? " " : "") + args[i];
				continue;
			}
			auto t = cast<TextWidget>(w);
			texts.Str(args[i], t is null ? "" : t.m_str);
		}
		Emit(Reply(id, true).Str("window", Reflect::GetTypeName(wnd)).Raw("texts", texts.Close())
			.Str("missing", missing).Bool("truncated", args.length() > 32));
	}

	// hovertip <widgetId>: the interactable widget of the top window hovered (its Hover(),
	// which runs its func-hover like the mouse does), then the open tooltip's text blocks
	// (title first) and the widget's own TextWidget children by id; the widget is left and
	// the tooltip closed again
	void VerbHoverTip(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: hovertip <widgetId>");
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
		auto target = cast<AInteractableWidget>(wnd.m_widget.GetWidgetById(args[0]));
		if (target is null)
		{
			Fail(id, "no interactable widget '" + args[0] + "' in " + Reflect::GetTypeName(wnd));
			return;
		}
		gm.m_windowManager.CloseTooltip();
		target.Hover();
		array<string> lines;
		ITooltip@ itt = gm.m_windowManager.m_tooltip;
		string ttType = itt is null ? "" : Reflect::GetTypeName(itt);
		auto tt = cast<ToolTip>(itt);
		if (tt !is null && tt.m_blocks !is null && tt.m_blocks.m_blocks !is null)
		{
			for (uint i = 0; i < tt.m_blocks.m_blocks.length(); i++)
			{
				auto tb = cast<ScalableBlocks::TextBlock>(tt.m_blocks.m_blocks[i]);
				if (tb !is null)
				{
					lines.insertLast(tb.m_sText);
					continue;
				}
				auto title = cast<ScalableBlocks::TitleBlock>(tt.m_blocks.m_blocks[i]);
				if (title !is null)
				{
					lines.insertLast(title.m_sTitle);
					if (!title.m_sSubTitle.isEmpty())
						lines.insertLast(title.m_sSubTitle);
				}
			}
		}
		Json kids;
		if (target.m_children !is null)
		{
			for (uint i = 0; i < target.m_children.length(); i++)
			{
				auto t = cast<TextWidget>(target.m_children[i]);
				if (t !is null && !t.m_id.isEmpty())
					kids.Str(t.m_id, t.m_str);
			}
		}
		target.Leave();
		gm.m_windowManager.CloseTooltip();
		Emit(Reply(id, true).Str("window", Reflect::GetTypeName(wnd)).Str("tooltip", ttType)
			.Raw("texts", StrArray(lines)).Raw("children", kids.Close()));
	}

	void Register_newb()
	{
		RegisterVerb("wtext", "<widgetId...>", Verb(VerbWText));
		RegisterVerb("hovertip", "<widgetId>", Verb(VerbHoverTip));
	}
}
