// gamelab-hands: a widget-text read for the newb test plan (mods/architect challenges).
// The Architect picker sits over the mission loadout menu, whose tree can use up the
// widgets dump's character budget (WIDGET_CHARS) before the picker's own lines are
// reached; wtext reads just the named widgets of the top window.
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

	void Register_newb()
	{
		RegisterVerb("wtext", "<widgetId...>", Verb(VerbWText));
	}
}
