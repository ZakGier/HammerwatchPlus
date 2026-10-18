// The HammerwatchPlus tab of the player menu: our settings, since the game's
// own Options menu runs in the menu script, which never loads mod scripts or
// mod gui files (GameLab probe-options-menu), and its keybind list is a fixed
// table in the exe. gui/playermenu/playermenu.gui adds the tab button and an
// hwp-options-hook widget that hands the PlayerMenu an HWPOptionsTab
// (gui/hwp/options.gui) on its first update.
//
// The gui has one row per option id ("hwp-opt-<id>"); a module fills its row
// by registering an Option under that id in its module ctor (script globals
// reset every level). A row without one hides. Values are read every frame
// while the tab is open, so providers need no change calls.
namespace HWP
{
	namespace Options
	{
		class Option
		{
			string Title() { return ""; }
			string Value() { return ""; }
			// clicking the row's button: usually the next choice
			void Next() {}
		}

		// a keyboard key: clicking the button waits for the next key press
		class KeyOption : Option
		{
			int Scancode() { return 0; }
			void SetScancode(int scancode) {}
			string Value() override { return KeyName(Scancode()); }
		}

		dictionary g_options;

		void Register(const string &in id, Option@ option)
		{
			g_options.set(id, @option);
		}

		Option@ Get(const string &in id)
		{
			Option@ option;
			if (g_options.get(id, @option))
				return option;
			return null;
		}

		const int SC_ESCAPE = 41;
		const int SC_FIRST = 4;
		const int SC_LAST = 231;

		// SDL scancode names (USB HID usage ids), as the keys are printed
		string KeyName(int sc)
		{
			if (sc >= 4 && sc <= 29)
				return "ABCDEFGHIJKLMNOPQRSTUVWXYZ".substr(sc - 4, 1);
			if (sc >= 30 && sc <= 39)
				return "1234567890".substr(sc - 30, 1);
			if (sc >= 58 && sc <= 69)
				return "F" + (sc - 57);
			if (sc >= 89 && sc <= 98)
				return "Num " + "1234567890".substr(sc - 89, 1);
			switch (sc)
			{
				case 40: return "Enter";
				case 41: return "Esc";
				case 42: return "Backspace";
				case 43: return "Tab";
				case 44: return "Space";
				case 45: return "-";
				case 46: return "=";
				case 47: return "[";
				case 48: return "]";
				case 49: return "\\";
				case 51: return ";";
				case 52: return "'";
				case 53: return "`";
				case 54: return ",";
				case 55: return ".";
				case 56: return "/";
				case 57: return "Caps Lock";
				case 73: return "Insert";
				case 74: return "Home";
				case 75: return "Page Up";
				case 76: return "Delete";
				case 77: return "End";
				case 78: return "Page Down";
				case 79: return "Right";
				case 80: return "Left";
				case 81: return "Down";
				case 82: return "Up";
				case 224: return "Left Ctrl";
				case 225: return "Left Shift";
				case 226: return "Left Alt";
				case 228: return "Right Ctrl";
				case 229: return "Right Shift";
				case 230: return "Right Alt";
			}
			return "Key " + sc;
		}

		bool KeyDown(int sc) { return Platform::IsKeyDown(ControllerType::Keyboard, 0, sc); }

		// the first key held down, or -1
		int AnyKeyDown()
		{
			for (int sc = SC_FIRST; sc <= SC_LAST; sc++)
			{
				if (KeyDown(sc))
					return sc;
			}
			return -1;
		}

		// the HammerwatchPlus tab is the current tab of the open character menu
		// (a key a module polls should not fire while it is being set there)
		bool TabOpen()
		{
			auto gm = cast<BaseGameMode>(g_gameMode);
			if (gm is null || gm.m_windowManager is null)
				return false;
			for (uint i = 0; i < gm.m_windowManager.m_objects.length(); i++)
			{
				auto w = gm.m_windowManager.m_objects[i];
				if (cast<HWPKeyCaptureWindow>(w) !is null)
					return true;
				auto menu = cast<PlayerMenu>(w);
				if (menu !is null && menu.m_tabSystem.m_tabs.length() > 0
					&& cast<HWPOptionsTab>(menu.m_tabSystem.GetCurrentTab()) !is null)
					return true;
			}
			return false;
		}
	}
}

// Over the Plus tab while a KeyOption waits for its key. Only the top window
// gets input (WindowManager), so the menu underneath cannot switch tabs or
// close on the key being bound, and the character-menu toggle is refused
// while another window is on top. Esc is the game's menu back, which closes
// only this top window (Back): that cancels.
class HWPKeyCaptureWindow : AWindowObject
{
	HWPOptionsTab@ m_tab;
	string m_id;
	bool m_armed;      // every key was up since the capture started

	HWPKeyCaptureWindow(GUIBuilder@ b, HWPOptionsTab@ tab, const string &in id)
	{
		super(b, "gui/hwp/keycapture.gui");
		@m_tab = tab;
		m_id = id;
		auto opt = HWP::Options::Get(id);
		auto text = cast<TextWidget>(m_widget.GetWidgetById("text"));
		if (text !is null && opt !is null)
			text.SetText(Resources::GetString(".hwp.options.capture", { { "what", opt.Title() } }));
	}

	// no AWindowObject::Update: no navigation, and Esc must not close the menu
	bool Update(int ms, GameInput& gameInput, MenuInput& menuInput) override
	{
		IWidgetHoster::Update(ms);
		auto opt = cast<HWP::Options::KeyOption>(HWP::Options::Get(m_id));
		if (opt is null)
			return Done();
		int sc = HWP::Options::AnyKeyDown();
		if (!m_armed)
		{
			// the key that pressed the row's button (Enter) must come up first
			m_armed = sc < 0;
			return false;
		}
		if (sc < 0 || sc == HWP::Options::SC_ESCAPE)
			return false;
		opt.SetScancode(sc);
		HWP::Log("options", m_id + " key set to " + sc + " (" + HWP::Options::KeyName(sc) + ")");
		return Done();
	}

	bool Back() override
	{
		HWP::Log("options", m_id + " key capture cancelled");
		return true; // the window manager closes us (Cleanup ends the capture)
	}

	bool Done()
	{
		if (m_tab !is null)
			m_tab.CaptureEnded();
		@m_tab = null;
		return true;
	}

	void Cleanup() override
	{
		// closed from outside (the menu force-closed): the tab stops showing it
		if (m_tab !is null)
			m_tab.CaptureEnded();
		@m_tab = null;
		AWindowObject::Cleanup();
	}
}

class HWPOptionsTab : MenuTab
{
	array<Widget@> m_rows;
	TextWidget@ m_hint;
	TextInputWidget@ m_search;
	TextWidget@ m_searchHint;
	string m_query;            // the search text, lower case
	bool m_relist;             // rows changed while typing: rebuild the navigation list after
	string m_capture;          // id of the KeyOption waiting for a key (HWPKeyCaptureWindow), or ""

	HWPOptionsTab(GUIBuilder@ b, uint id)
	{
		super(b, id, "gui/hwp/options.gui");
		@m_hint = cast<TextWidget>(m_widget.GetWidgetById("hint"));
		@m_search = cast<TextInputWidget>(m_widget.GetWidgetById("search"));
		@m_searchHint = cast<TextWidget>(m_widget.GetWidgetById("search-hint"));
		// the console key's char: it opens the console, it is never part of a search
		if (m_search !is null)
		{
			m_search.m_forbiddenCharacters.insertLast("`");
			m_search.m_forbiddenCharacters.insertLast("~");
		}
		auto list = m_widget.GetWidgetById("rows");
		if (list !is null)
		{
			for (uint i = 0; i < list.m_children.length(); i++)
				m_rows.insertLast(list.m_children[i]);
		}
	}

	void Initialize() override
	{
		Refresh();
		RefreshInteractableWidgets(m_widget);
	}

	string RowId(Widget@ row) { return row.m_id.substr(8); } // "hwp-opt-<id>"

	void SetText(Widget@ parent, const string &in id, const string &in text)
	{
		auto t = cast<TextWidget>(parent.GetWidgetById(id));
		if (t !is null && t.m_str != text)
			t.SetText(text);
	}

	// a row matches when its title or value holds the search text
	bool Matches(HWP::Options::Option@ opt)
	{
		if (m_query.isEmpty())
			return true;
		return opt.Title().toLower().findFirst(m_query) >= 0 || opt.Value().toLower().findFirst(m_query) >= 0;
	}

	void SetQuery(const string &in text)
	{
		string q = text.toLower();
		// (trimmed: a trailing space should not hide everything)
		while (q.length() > 0 && q.substr(q.length() - 1) == " ")
			q = q.substr(0, q.length() - 1);
		while (q.length() > 0 && q.substr(0, 1) == " ")
			q = q.substr(1);
		if (q == m_query)
			return;
		m_query = q;
		Refresh();
	}

	void Refresh()
	{
		bool relist = false;
		int shown = 0;
		for (uint i = 0; i < m_rows.length(); i++)
		{
			auto row = m_rows[i];
			string id = RowId(row);
			auto opt = HWP::Options::Get(id);
			bool show = opt !is null && (id == m_capture || Matches(opt));
			if (show)
				shown++;
			if (row.m_visible != show)
			{
				row.m_visible = show;
				relist = true;
				Invalidate();
			}
			if (!show)
				continue;
			SetText(row, "title", opt.Title());
			SetText(row, "value", id == m_capture ? Resources::GetString(".hwp.options.press") : opt.Value());
		}
		if (m_hint !is null)
		{
			string hint = Resources::GetString(".hwp.options.hint");
			auto opt = HWP::Options::Get(m_capture);
			if (opt !is null)
				hint = Resources::GetString(".hwp.options.capture", { { "what", opt.Title() } });
			else if (shown == 0 && !m_query.isEmpty())
				hint = Resources::GetString(".hwp.options.nomatch", { { "q", m_query } });
			if (m_hint.m_str != hint)
				m_hint.SetText(hint);
		}
		// hidden rows' buttons leave the keyboard/gamepad navigation; not while
		// typing in the search (rebuilding the list takes the field's focus and
		// ends the typing after the first letter that hides a row)
		if (relist)
			m_relist = true;
		if (m_relist && (m_search is null || !m_search.m_typing))
		{
			m_relist = false;
			RefreshInteractableWidgets(m_widget);
		}
		if (m_searchHint !is null)
		{
			bool empty = m_search is null || (m_search.m_text.length() == 0 && !m_search.m_typing);
			if (m_searchHint.m_visible != empty)
				m_searchHint.m_visible = empty;
		}
	}

	void CaptureEnded()
	{
		m_capture = "";
		Refresh();
	}

	void StartCapture(const string &in id)
	{
		if (m_manager is null)
			return;
		m_capture = id;
		m_manager.AddWindowObject(HWPKeyCaptureWindow(m_builder, this, id));
	}

	bool Update(int ms, GameInput& gameInput, MenuInput& menuInput) override
	{
		Refresh();
		return AWindowObject::Update(ms, gameInput, menuInput);
	}

	void OnFunc(Widget@ sender, const string &in name) override
	{
		if (name == "hwp-search" && m_search !is null)
		{
			SetQuery(m_search.m_text.plain());
			return;
		}
		if (name == "hwp-search-clear" && m_search !is null)
		{
			m_search.SetText("");
			SetQuery("");
			return;
		}
		auto parse = name.split(" ");
		if (parse.length() < 2 || parse[0] != "hwp-opt")
			return;
		string id = parse[1];
		auto opt = HWP::Options::Get(id);
		if (opt is null)
			return;
		if (cast<HWP::Options::KeyOption>(opt) !is null)
		{
			if (m_capture.isEmpty())
				StartCapture(id);
		}
		else
		{
			opt.Next();
			HWP::Log("options", id + " -> " + opt.Value());
		}
		Refresh();
	}
}

// In playermenu.gui: on its first update, finds the PlayerMenu it belongs to
// and adds the HammerwatchPlus tab (last, matching the last tab button).
class HWPOptionsHookWidget : GroupWidget
{
	bool m_done;

	HWPOptionsHookWidget()
	{
		super();
	}

	Widget@ Clone() override
	{
		HWPOptionsHookWidget@ w = HWPOptionsHookWidget();
		CloneInto(w);
		return w;
	}

	void Update(int dt) override
	{
		GroupWidget::Update(dt);
		if (m_done)
			return;
		auto gm = cast<BaseGameMode>(g_gameMode);
		if (gm is null || gm.m_windowManager is null)
			return;
		Widget@ root = this;
		while (root.m_parent !is null)
			@root = root.m_parent;
		for (uint i = 0; i < gm.m_windowManager.m_objects.length(); i++)
		{
			auto menu = cast<PlayerMenu>(gm.m_windowManager.m_objects[i]);
			if (menu is null || menu.m_widget !is root)
				continue;
			m_done = true;
			uint id = HashString("hwp_options");
			for (uint j = 0; j < menu.m_tabSystem.m_tabs.length(); j++)
			{
				if (menu.m_tabSystem.m_tabs[j].m_id == id)
					return;
			}
			menu.m_tabSystem.AddTab(HWPOptionsTab(menu.m_builder, id));
			return;
		}
	}
}

ref@ LoadHWPOptionsHookWidget(WidgetLoadingContext &ctx)
{
	HWPOptionsHookWidget@ w = HWPOptionsHookWidget();
	w.Load(ctx);
	return w;
}

namespace HWPOptions
{
	[Hook]
	void LoadWidgetProducers(GUIBuilder@ builder)
	{
		builder.AddWidgetProducer("hwp-options-hook", LoadHWPOptionsHookWidget);
	}
}
