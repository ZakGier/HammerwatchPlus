// Extra materials in the character menu's materials tab (gui/playermenu/
// character.gui): sections under the run and town rows for things a module
// keeps per character ("Supplies": bet tokens, fishing bait; "Plants & Herbs":
// farm seeds and the harvest). Each cell is a hwp-material widget in its
// section's wrapping grid, filled by the provider a module registers under the
// cell's id; a cell without a provider (its module is off) is hidden and the
// grid closes the gap, and a section without any hides. Each section sits under
// the one before it. Hovering a cell shows the provider's Title() / Text();
// clicking it calls Click().
//
// Providers register in their module ctor (script globals reset every level).
// Counts are read every frame while the tab is open, so no change calls.
namespace HWP
{
	namespace Materials
	{
		class Material
		{
			// 13x13, like the vanilla material icons
			ScriptSprite@ Icon() { return null; }
			int Count() { return 0; }
			// the hover tooltip
			string Title() { return ""; }
			string Text() { return ""; }
			void Click() {}
		}

		dictionary g_materials;

		void Register(const string &in id, Material@ material)
		{
			g_materials.set(id, @material);
		}

		Material@ Get(const string &in id)
		{
			Material@ material;
			if (g_materials.get(id, @material))
				return material;
			return null;
		}
	}
}

// one cell: the material background sprite, the provider's icon, and a
// "count" text child. Interactable (mouse only) for its tooltip; it has to be
// visible when the menu collects its interactables, so the gui leaves it
// visible and Refresh hides it once it knows there is no provider.
class HWPMaterialWidget : AInteractableWidget
{
	Sprite@ m_background;
	HWP::Materials::Material@ m_material;
	ScriptSprite@ m_icon;
	TextWidget@ m_count;
	int m_shown = -1;

	HWPMaterialWidget()
	{
		super();
	}

	Widget@ Clone() override
	{
		HWPMaterialWidget@ w = HWPMaterialWidget();
		CloneInto(w);
		return w;
	}

	void Load(WidgetLoadingContext &ctx) override
	{
		AInteractableWidget::Load(ctx);
		string src = ctx.GetString("src", false);
		if (src != "")
			@m_background = ctx.GetGUIDef().GetSprite(src);
	}

	// called by the section, also while this cell is hidden
	bool Refresh()
	{
		@m_material = HWP::Materials::Get(m_id);
		bool show = m_material !is null;
		if (m_visible != show)
			m_visible = show;
		if (m_material is null)
			return false;
		if (m_icon is null)
			@m_icon = m_material.Icon();
		if (m_count is null)
			@m_count = cast<TextWidget>(GetWidgetById("count"));
		int n = m_material.Count();
		if (m_count !is null && n != m_shown)
		{
			m_shown = n;
			m_count.SetText("" + n);
		}
		return true;
	}

	void ClickUp(bool usingMouse, vec2 mousePos) override
	{
		AInteractableWidget::ClickUp(usingMouse, mousePos);
		if (m_material is null)
			return;
		auto gm = cast<BaseGameMode>(g_gameMode);
		if (gm !is null)
			gm.m_windowManager.CloseTooltip();
		m_material.Click();
	}

	// the vanilla small material box (gui/gui.png 297 134 29 26, playermenu/character.gui);
	// a smaller cell gets its top left and the last 3 px of its right and bottom edges
	void DrawCompactBackground(SpriteBatch& sb, vec2 pos)
	{
		auto tex = Resources::GetTexture2D("gui/gui.png");
		if (tex is null)
			return;
		const int bx = 297, by = 134, bw = 29, bh = 26, e = 3;
		int w = m_width, h = m_height;
		sb.DrawSprite(tex, vec4(pos.x, pos.y, w - e, h - e), vec4(bx, by, w - e, h - e));
		sb.DrawSprite(tex, vec4(pos.x + w - e, pos.y, e, h - e), vec4(bx + bw - e, by, e, h - e));
		sb.DrawSprite(tex, vec4(pos.x, pos.y + h - e, w - e, e), vec4(bx, by + bh - e, w - e, e));
		sb.DrawSprite(tex, vec4(pos.x + w - e, pos.y + h - e, e, e), vec4(bx + bw - e, by + bh - e, e, e));
	}

	void DoDraw(SpriteBatch& sb, vec2 pos) override
	{
		if (m_width < 29 || m_height < 26)
			DrawCompactBackground(sb, pos);
		else if (m_background !is null)
			sb.DrawSprite(pos, m_background, g_menuTime, vec4(1.0f));
		if (m_icon !is null)
			m_icon.Draw(sb, pos + vec2(int((m_width - m_icon.GetWidth()) / 2), m_icon.GetHeight() > 13 ? 1 : 3), int(g_menuTime), vec4(1.0f));
	}

	void ShowTooltip() override
	{
		auto gm = cast<BaseGameMode>(g_gameMode);
		if (gm is null)
			return;
		if (m_material is null || m_material.Title() == "")
		{
			gm.m_windowManager.CloseTooltip();
			return;
		}
		// at the mouse, not the window's tooltip anchor (none here: top-center)
		vec2 mouse = gm.GetMousePos() / gm.m_wndScale;
		gm.m_windowManager.SetTooltip(CreateTooltip(Resources::GetSValue("gui/variable/itemtooltip_common.sval"), m_material.Title(), m_material.Text()), mouse + vec2(10, 10), true);
	}

	void Hover() override
	{
		ShowTooltip();
		AInteractableWidget::Hover();
	}

	void Leave() override
	{
		auto gm = cast<BaseGameMode>(g_gameMode);
		if (gm !is null)
			gm.m_windowManager.CloseTooltip();
		AInteractableWidget::Leave();
	}
}

// a section: its header and a "cells" group (flow hboxwrapped) with the
// hwp-material cells. It hides the header when no cell has a provider, sizes
// the grid to its rows, moves under the section before it, and the last one sets
// the materials tab's height (the sections don't fit the tab's four bag rows of
// room, so they scroll in).
class HWPMaterialsWidget : GroupWidget
{
	int m_tabHeight = -1;
	Widget@ m_cells;
	int m_gridTop = -1;
	bool m_any = false;
	int m_bottom = -1; // in the tab, padding included; -1 while hidden

	HWPMaterialsWidget()
	{
		super();
	}

	Widget@ Clone() override
	{
		HWPMaterialsWidget@ w = HWPMaterialsWidget();
		CloneInto(w);
		return w;
	}

	// the sections of this tab, in gui order
	array<HWPMaterialsWidget@>@ Sections()
	{
		array<HWPMaterialsWidget@> all;
		if (m_parent is null)
			return all;
		for (uint i = 0; i < m_parent.m_children.length(); i++)
		{
			auto sec = cast<HWPMaterialsWidget>(m_parent.m_children[i]);
			if (sec !is null)
				all.insertLast(sec);
		}
		return all;
	}

	void Update(int dt) override
	{
		auto all = Sections();
		int at = all.findByRef(this);
		// the tab's own height, from before the first section changed it
		if (m_parent !is null && at == 0 && m_tabHeight < 0)
			m_tabHeight = m_parent.m_height;
		if (at > 0)
		{
			auto prev = all[at - 1];
			int y = prev.m_any ? int(prev.m_offset.y) + prev.m_height + 2 : int(prev.m_offset.y);
			if (int(m_offset.y) != y)
				m_offset.y = y;
		}
		if (m_cells is null)
		{
			@m_cells = GetWidgetById("cells");
			if (m_cells !is null)
				m_gridTop = int(m_cells.m_offset.y);
		}

		int shown = 0;
		int cellW = 0;
		int cellH = 0;
		if (m_cells !is null)
		{
			for (uint i = 0; i < m_cells.m_children.length(); i++)
			{
				auto cell = cast<HWPMaterialWidget>(m_cells.m_children[i]);
				if (cell !is null && cell.Refresh())
				{
					shown++;
					cellW = cell.m_width;
					cellH = cell.m_height;
				}
			}
		}
		bool any = shown > 0;
		m_any = any;
		for (uint i = 0; i < m_children.length(); i++)
		{
			if (m_children[i] !is m_cells && m_children[i].m_visible != any)
				m_children[i].m_visible = any;
		}

		int h = m_height;
		if (any && m_cells !is null)
		{
			int step = max(1, cellW + m_cells.m_spacing);
			int perRow = max(1, (m_cells.m_width - cellW) / step + 1);
			int rows = (shown + perRow - 1) / perRow;
			int gridH = rows * cellH + (rows - 1) * m_cells.m_spacingLine;
			if (m_cells.m_height != gridH)
				m_cells.m_height = gridH;
			h = m_gridTop + gridH;
			if (m_height != h)
				m_height = h;
		}
		m_bottom = any ? int(m_offset.y + (m_parent is null ? 0 : m_parent.m_padding.y)) + h : -1;
		if (m_parent !is null && at == int(all.length()) - 1)
		{
			int tab = all[0].m_tabHeight;
			for (uint i = 0; i < all.length(); i++)
				if (all[i].m_bottom > tab)
					tab = all[i].m_bottom;
			if (m_parent.m_height != tab)
				m_parent.m_height = tab;
			// Character.as turns the scrollbar off on the materials tab
			auto sb = cast<ScrollbarWidget>(m_parent.m_parent);
			if (sb !is null)
				sb.m_enabled = tab > sb.m_height;
		}
		GroupWidget::Update(dt);
	}
}

ref@ LoadHWPMaterialWidget(WidgetLoadingContext &ctx)
{
	HWPMaterialWidget@ w = HWPMaterialWidget();
	w.Load(ctx);
	return w;
}

ref@ LoadHWPMaterialsWidget(WidgetLoadingContext &ctx)
{
	HWPMaterialsWidget@ w = HWPMaterialsWidget();
	w.Load(ctx);
	return w;
}

namespace HWPMaterials
{
	[Hook]
	void LoadWidgetProducers(GUIBuilder@ builder)
	{
		builder.AddWidgetProducer("hwp-material", LoadHWPMaterialWidget);
		builder.AddWidgetProducer("hwp-materials", LoadHWPMaterialsWidget);
	}
}
