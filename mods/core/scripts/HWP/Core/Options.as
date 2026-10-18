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
	}
}

class HWPOptionsTab : MenuTab
{
	array<Widget@> m_rows;
	TextWidget@ m_hint;
	string m_capture;          // id of the KeyOption waiting for a key, or ""
	bool m_captureArmed;       // every key was up since the capture started

	HWPOptionsTab(GUIBuilder@ b, uint id)
	{
		super(b, id, "gui/hwp/options.gui");
		@m_hint = cast<TextWidget>(m_widget.GetWidgetById("hint"));
		auto list = m_widget.GetWidgetById("rows");
		if (list !is null)
		{
			for (uint i = 0; i < list.m_children.length(); i++)
				m_rows.insertLast(list.m_children[i]);
		}
	}

	void Initialize() override
	{
		RefreshInteractableWidgets(m_widget);
		Refresh();
	}

	string RowId(Widget@ row) { return row.m_id.substr(8); } // "hwp-opt-<id>"

	void SetText(Widget@ parent, const string &in id, const string &in text)
	{
		auto t = cast<TextWidget>(parent.GetWidgetById(id));
		if (t !is null && t.m_str != text)
			t.SetText(text);
	}

	void Refresh()
	{
		for (uint i = 0; i < m_rows.length(); i++)
		{
			auto row = m_rows[i];
			string id = RowId(row);
			auto opt = HWP::Options::Get(id);
			bool show = opt !is null;
			if (row.m_visible != show)
			{
				row.m_visible = show;
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
			if (m_hint.m_str != hint)
				m_hint.SetText(hint);
		}
	}

	void StopCapture()
	{
		m_capture = "";
		m_captureArmed = false;
	}

	void PollCapture()
	{
		auto opt = cast<HWP::Options::KeyOption>(HWP::Options::Get(m_capture));
		if (opt is null)
		{
			StopCapture();
			return;
		}
		int sc = HWP::Options::AnyKeyDown();
		if (!m_captureArmed)
		{
			// the key that pressed the button (Enter) must come up first
			m_captureArmed = sc < 0;
			return;
		}
		if (sc < 0)
			return;
		if (sc != HWP::Options::SC_ESCAPE)
		{
			opt.SetScancode(sc);
			HWP::Log("options", m_capture + " key set to " + sc + " (" + HWP::Options::KeyName(sc) + ")");
		}
		StopCapture();
	}

	bool Update(int ms, GameInput& gameInput, MenuInput& menuInput) override
	{
		if (m_capture != "")
			PollCapture();
		Refresh();
		return AWindowObject::Update(ms, gameInput, menuInput);
	}

	// no StopCapture in OnShow: MenuTabSystem calls it on every hover change, so
	// moving the mouse off the button would cancel. Closing the menu cancels.
	void Cleanup() override
	{
		StopCapture();
		AWindowObject::Cleanup();
	}

	void OnFunc(Widget@ sender, const string &in name) override
	{
		auto parse = name.split(" ");
		if (parse.length() < 2 || parse[0] != "hwp-opt")
			return;
		string id = parse[1];
		auto opt = HWP::Options::Get(id);
		if (opt is null)
			return;
		if (cast<HWP::Options::KeyOption>(opt) !is null)
		{
			if (m_capture == id)
				StopCapture();
			else
			{
				m_capture = id;
				m_captureArmed = false;
			}
		}
		else
		{
			StopCapture();
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
			uint id = HashString("hwp-options");
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
