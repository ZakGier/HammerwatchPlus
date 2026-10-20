// gamelab-hands: menu verbs the gear plan checks need (gamelab/bots/plan_gear.py): select
// a widget of the open window the way keyboard navigation does (hover), read and click the
// key hint bar (navbar), hold the menu's context / additional binding (hold), and list the
// item pickups lying around the player (items). Each drives the window's own handlers,
// never a screen coordinate.
namespace GameLab
{
	AWindowObject@ GearTopWindow()
	{
		auto gm = cast<BaseGameMode>(g_gameMode);
		if (gm is null || gm.m_windowManager is null)
			return null;
		return gm.m_windowManager.GetCurrentWindow();
	}

	// the window whose input and widgets the player navigates: a tabbed window's open tab
	// (the character screen's widgets live in PlayerMenuCharacterTab, GUI/MenuTabSystem.as)
	AWindowObject@ GearInputWindow(AWindowObject@ wnd)
	{
		auto tabs = TabsOf(wnd);
		if (tabs is null || tabs.m_currentIndex < 0 || tabs.m_currentIndex >= int(tabs.m_tabs.length()))
			return wnd;
		return tabs.m_tabs[tabs.m_currentIndex];
	}

	// [row, column] of w in the input's interactables (WindowInput.m_interactables), or -1, -1
	ivec2 GearIndexOf(WindowInput@ input, AInteractableWidget@ w)
	{
		for (uint x = 0; x < input.m_interactables.length(); x++)
		{
			for (uint y = 0; y < input.m_interactables[x].length(); y++)
			{
				if (input.m_interactables[x][y] is w)
					return ivec2(int(x), int(y));
			}
		}
		return ivec2(-1, -1);
	}

	// what AWindowObject.Update does when an arrow key moves the selection to index
	// (GUI/WindowObject.as "Set new hover"): Leave the old interactable, Hover the new one
	void GearSelect(WindowInput@ input, ivec2 index)
	{
		auto old = input.GetCurrentInteractable();
		input.m_usingMouse = false;
		input.m_interactableIndex = index;
		input.m_interactableIndexNonMouseHover = index;
		auto now = input.GetCurrentInteractable();
		if (old !is null && old !is now)
		{
			old.Leave();
			old.LostNonHoverFocus();
			now.GotNonHoverFocus();
		}
		now.Hover();
	}

	// the key hint bar's texts (KeyNavigationBar.m_texts, Back first)
	array<string>@ GearNavTexts(AWindowObject@ wnd)
	{
		array<string>@ texts = array<string>();
		if (wnd is null || wnd.m_navigationBar is null)
			return texts;
		for (uint i = 0; i < wnd.m_navigationBar.m_texts.length(); i++)
		{
			auto t = wnd.m_navigationBar.m_texts[i];
			texts.insertLast(t is null || t.m_text is null ? "" : t.m_text.GetText());
		}
		return texts;
	}

	// which hints have a click handler (KeyNavigationText.m_func)
	string GearNavClickable(AWindowObject@ wnd)
	{
		array<string> flags;
		if (wnd !is null && wnd.m_navigationBar !is null)
		{
			for (uint i = 0; i < wnd.m_navigationBar.m_texts.length(); i++)
				flags.insertLast(wnd.m_navigationBar.m_texts[i] !is null && wnd.m_navigationBar.m_texts[i].m_func !is null ? "true" : "false");
		}
		return RawArray(flags);
	}

	string GearTooltip()
	{
		auto gm = cast<BaseGameMode>(g_gameMode);
		if (gm is null || gm.m_windowManager is null || gm.m_windowManager.m_tooltip is null)
			return "";
		return Reflect::GetTypeName(gm.m_windowManager.m_tooltip);
	}

	// hover <widgetId> [child]: select a widget of the top window (its open tab first) the way
	// the arrow keys do (AWindowObject.Update: Leave the old interactable, Hover the new one,
	// OnInteractableIndexChanged rebuilds the key hints). [child] picks that child of the
	// widget (equipment-inventory 0 = the first bag slot, whose clones have no id). A widget
	// inside a scrollbar is selected in the scrollbar's own input (ScrollbarWidget.Hover hovers
	// its current child), as moving into the bag does. Replies with the widget, its item (name,
	// quality, colour code, ItemWidgetType, mirrored, shade), the widget's child count, the
	// open tooltip's type and the hint bar texts.
	void VerbGearHover(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: hover <widgetId> [child]");
			return;
		}
		auto wnd = GearTopWindow();
		if (wnd is null || wnd.m_widget is null)
		{
			Fail(id, "no open window");
			return;
		}
		auto win = GearInputWindow(wnd);
		Widget@ w = win.m_widget.GetWidgetById(args[0]);
		if (w is null && win !is wnd)
		{
			@win = wnd;
			@w = wnd.m_widget.GetWidgetById(args[0]);
		}
		if (w is null)
		{
			Fail(id, "no widget '" + args[0] + "' in " + Reflect::GetTypeName(GearInputWindow(wnd)));
			return;
		}
		int children = w.m_children is null ? 0 : int(w.m_children.length());
		if (args.length() > 1)
		{
			int k = int(parseInt(args[1]));
			if (k < 0 || k >= children)
			{
				Fail(id, "'" + args[0] + "' has " + children + " children");
				return;
			}
			@w = w.m_children[k];
		}
		auto target = cast<AInteractableWidget>(w);
		if (target is null)
		{
			Fail(id, "'" + args[0] + "' is a " + Reflect::GetTypeName(w) + ", not interactable");
			return;
		}
		ivec2 at = GearIndexOf(win.m_input, target);
		ScrollbarWidget@ sb = null;
		if (at.x < 0)
		{
			for (Widget@ p = w.m_parent; p !is null && sb is null; @p = p.m_parent)
				@sb = cast<ScrollbarWidget>(p);
			if (sb !is null)
				at = GearIndexOf(win.m_input, sb);
			if (at.x < 0)
			{
				Fail(id, "'" + args[0] + "' is not in " + Reflect::GetTypeName(win) + "'s input (hidden?)");
				return;
			}
			// the scrollbar refreshes its input on layout while hovered; it may not have yet
			ivec2 inner = GearIndexOf(sb.m_input, target);
			if (inner.x < 0)
			{
				sb.m_input.RefreshInteractableWidgets(sb);
				inner = GearIndexOf(sb.m_input, target);
			}
			if (inner.x < 0)
			{
				Fail(id, "'" + args[0] + "' is not in its scrollbar's input (hidden?)");
				return;
			}
			auto old = sb.m_input.GetCurrentInteractable();
			sb.m_input.m_usingMouse = false;
			sb.m_input.m_interactableIndex = inner;
			sb.m_input.m_interactableIndexNonMouseHover = inner;
			if (old !is null && old !is target)
				old.Leave();
		}
		GearSelect(win.m_input, at);
		win.OnInteractableIndexChanged();

		Json@ r = Reply(id, true).Str("window", Reflect::GetTypeName(wnd)).Str("input", Reflect::GetTypeName(win))
			.Str("widget", Reflect::GetTypeName(target)).Int("children", children).Bool("scrolled", sb !is null);
		auto slot = cast<ItemWidgetBase>(target);
		if (slot !is null && slot.m_item !is null)
			r.Str("item", slot.m_item.GetName()).Str("quality", Item::QualityToString(slot.m_item.GetQuality()))
				.Str("color", Item::QualityColorString(slot.m_item.GetQuality()));
		else
			r.Str("item", "");
		// mirrored: drawn flipped (a two-hander in the off-hand slot); shade: the icon colour's red
		// channel (core HWPGearSlotWidget draws a mirrored item with m_disabledColor, 0.1)
		r.Int("type", slot is null ? -1 : int(slot.m_type)).Bool("mirrored", slot !is null && slot.m_mirroredIcon)
			.Num("shade", slot is null ? 1.0f : slot.m_color.x);
		r.Str("tooltip", GearTooltip()).Raw("nav", StrArray(GearNavTexts(wnd))).Raw("clickable", GearNavClickable(wnd));
		Emit(r);
	}

	// navbar [click <index>]: the top window's key hint bar (KeyNavigationBar, Back first):
	// texts, which have a click handler, and the keys of the menu bindings the hints name.
	// "click <index>" does what KeyNavigationBar.Update does with the cursor on that hint and
	// the Forward button pressed and released: Hover, OnClickDown, OnClickUp (which calls the
	// hint's m_func). Replies with the top window after.
	void VerbGearNavbar(const string &in id, array<string>@ args)
	{
		auto wnd = GearTopWindow();
		if (wnd is null || wnd.m_navigationBar is null)
		{
			Fail(id, "no open window with a key hint bar");
			return;
		}
		int clicked = -1;
		bool handler = false;
		if (args.length() >= 2 && args[0] == "click")
		{
			clicked = int(parseInt(args[1]));
			if (clicked < 0 || clicked >= int(wnd.m_navigationBar.m_texts.length()))
			{
				Fail(id, "no hint " + clicked + " (" + wnd.m_navigationBar.m_texts.length() + ")");
				return;
			}
			auto t = wnd.m_navigationBar.m_texts[clicked];
			handler = t.m_func !is null;
			t.Hover();
			t.OnClickDown();
			t.OnClickUp();
		}
		auto now = GearTopWindow();
		Emit(Reply(id, true).Str("window", Reflect::GetTypeName(wnd)).Str("top", now is null ? "" : Reflect::GetTypeName(now))
			.Int("clicked", clicked).Bool("handler", handler)
			.Raw("nav", StrArray(GearNavTexts(now is null ? wnd : now))).Raw("clickable", GearNavClickable(now is null ? wnd : now))
			.Str("forward", FormatKeyName(GetActionBinding("MenuForward")))
			.Str("context", FormatKeyName(GetActionBinding("MenuContext")))
			.Str("additional", FormatKeyName(GetActionBinding("MenuAdditional")))
			.Str("tooltip", GearTooltip()));
	}

	// hold <context|additional> [ms]: the open window's (tab's) handlers for that menu binding
	// in the order AWindowObject.Update calls them while the key is held: OnPressed on the
	// press, OnDown(ms) while down (here one call with the whole hold, default 1100), OnUp on
	// the release. The character tab links the hovered bag item when the context key is held
	// 1000 ms (Character.as MenuContextUp).
	void VerbGearHold(const string &in id, array<string>@ args)
	{
		if (args.length() < 1 || (args[0] != "context" && args[0] != "additional"))
		{
			Fail(id, "usage: hold <context|additional> [ms]");
			return;
		}
		auto wnd = GearTopWindow();
		if (wnd is null)
		{
			Fail(id, "no open window");
			return;
		}
		auto win = GearInputWindow(wnd);
		int ms = args.length() > 1 ? int(parseInt(args[1])) : 1100;
		auto input = win.m_input;
		bool context = args[0] == "context";
		WindowInput::OnFunc@ pressed = context ? input.m_menuContextOnPressed : input.m_menuAdditionalOnPressed;
		WindowInput::OnFuncInt@ down = context ? input.m_menuContextOnDown : input.m_menuAdditionalOnDown;
		WindowInput::OnFunc@ up = context ? input.m_menuContextOnUp : input.m_menuAdditionalOnUp;
		if (pressed !is null)
			pressed();
		if (down !is null)
			down(ms);
		if (up !is null)
			up();
		auto now = GearTopWindow();
		Emit(Reply(id, true).Str("input", Reflect::GetTypeName(win)).Str("binding", args[0]).Int("ms", ms)
			.Bool("pressed", pressed !is null).Bool("down", down !is null).Bool("up", up !is null)
			.Str("top", now is null ? "" : Reflect::GetTypeName(now)));
	}

	const uint GEAR_ITEMS_CAP = 32;

	// items [radius]: read-only. Item pickups (Item::UnitBehavior, what Item::DropItem spawns)
	// within radius (default 120) of the player: unit, item name, quality, owner ("shared":
	// anyone may take it, "me": only the local player, "other"), picked, hidden (a pickup owned
	// by someone else is hidden on this machine), drop animation ms left, distance. Capped at
	// GEAR_ITEMS_CAP; "count" is every match. "my_id_shared": the local character's id is the
	// zeroed Guid that marks shared items, so "shared" may also mean "me".
	void VerbGearItems(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		auto rec = GetLocalPlayerRecord();
		int radius = args.length() > 0 ? int(parseInt(args[0])) : 120;
		vec2 center = xy(plr.m_unit.GetPosition());
		auto units = g_scene.FetchAllUnits(~0, center, radius);
		array<string> items;
		uint count = 0;
		for (uint i = 0; i < units.length(); i++)
		{
			if (!units[i].IsValid() || units[i].IsDestroyed())
				continue;
			float d = dist(center, xy(units[i].GetPosition()));
			if (d > radius)
				continue;
			auto b = cast<Item::UnitBehavior>(units[i].GetScriptBehavior());
			if (b is null || b.m_item is null)
				continue;
			count++;
			if (items.length() >= GEAR_ITEMS_CAP)
				continue;
			string owner = "other";
			if (b.m_playerOwner == Item::g_sharedItem)
				owner = "shared";
			else if (rec !is null && b.m_playerOwner == rec.id)
				owner = "me";
			Json e;
			e.Int("unit", units[i].GetId()).Str("item", b.m_item.GetName()).Str("quality", Item::QualityToString(b.m_item.GetQuality()))
				.Str("owner", owner).Bool("picked", b.m_picked).Bool("hidden", units[i].IsHidden()).Int("anim", b.m_dropAnimC)
				.Num("dist", d);
			items.insertLast(e.Close());
		}
		// my_id_shared: this character's id is the zeroed "shared" Guid, so an item kept for
		// it can't be told from a shared one by its owner
		Emit(Reply(id, true).Int("radius", radius).Int("count", count).Int("truncated", count > items.length() ? int(count - items.length()) : 0)
			.Bool("my_id_shared", rec !is null && rec.id == Item::g_sharedItem).Raw("items", RawArray(items)));
	}

	void Register_gear()
	{
		RegisterVerb("hover", "<widgetId> [child]", Verb(VerbGearHover));
		RegisterVerb("navbar", "[click <index>]", Verb(VerbGearNavbar));
		RegisterVerb("hold", "<context|additional> [ms]", Verb(VerbGearHold));
		RegisterVerb("items", "[radius]", Verb(VerbGearItems));
	}
}
