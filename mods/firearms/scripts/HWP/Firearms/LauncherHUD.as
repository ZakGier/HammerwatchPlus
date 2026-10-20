namespace HWP
{
	namespace Firearms
	{
		// The HUD's off-hand slot for a two-hander draws the main-hand item's icon, mirrored
		// (HUDPlayer.RefreshSkills: SetSkill(offHandSkill, mainHandWeapon, true)). A rifle's
		// off-hand attack is its underbarrel grenade launcher, so that slot shows the launcher
		// close-up of the rifle's tier instead (items/hwp/firearms_items.png row 1, rifle_gl_0N),
		// unmirrored. Only the skill bar: the inventory keeps the rifle's own icon.
		class LauncherIcon : Item::Item
		{
			ScriptSprite@ m_icon;
			int m_tier;

			LauncherIcon(int tier)
			{
				m_tier = tier;
				@m_icon = ScriptSprite(Resources::GetTexture2D("items/hwp/firearms_items.png"), vec4(24 * tier, 24, 24, 24));
			}

			ScriptSprite@ GetIcon() override { return m_icon; }
		}

		array<LauncherIcon@> g_launcherIcons;

		// the close-up for a rifle (hwp_rifle_01..03), or null for anything else
		LauncherIcon@ LauncherIconFor(Item::Item@ weapon)
		{
			auto equip = cast<Equipment::Item>(weapon);
			if (equip is null || equip.baseItem is null)
				return null;
			string id = equip.baseItem.m_id;
			if (id.length() != 12 || id.substr(0, 10) != "hwp_rifle_")
				return null;
			int tier = parseInt(id.substr(10)) - 1;
			if (tier < 0 || tier > 2)
				return null;
			if (g_launcherIcons.length() == 0)
			{
				for (int i = 0; i < 3; i++)
					g_launcherIcons.insertLast(LauncherIcon(i));
			}
			return g_launcherIcons[tier];
		}
	}
}

namespace Modules
{
	// RefreshSkills rebuilds the slot's widget on every equipment or skill change, so each frame
	// a fresh off-hand widget under a rifle gets the close-up (a widget already showing it is
	// left alone).
	class HWPFirearmsLauncherHUDModule : Module
	{
		int m_shownTier = -1;

		HWPFirearmsLauncherHUDModule()
		{
			super("hwp-firearms-launcher-hud");
		}

		void UpdateFrame(int ms, GameInput& gameInput, MenuInput& menuInput, bool paused) override
		{
			auto hud = g_gameMode.GetHUD();
			if (hud is null)
				return;
			// the HUD shows the spectated player's skills while spectating (HUD.RefreshSkills)
			PlayerRecord@ record = GetLocalPlayerRecord();
			auto gm = cast<AGameplayGameMode>(g_gameMode);
			if (gm !is null && gm.m_spectating && gm.m_spectatingPlayer >= 0 && gm.m_spectatingPlayer < int(g_players.length()))
				@record = g_players[gm.m_spectatingPlayer];
			if (record is null || record.equipped is null)
				return;
			auto icon = HWP::Firearms::LauncherIconFor(record.equipped.m_items[EquippedItemsSlots::MainHand]);
			if (icon is null)
				return;
			for (uint i = 0; i < hud.m_components.length(); i++)
			{
				auto comp = cast<HUDPlayer>(hud.m_components[i]);
				if (comp is null || comp.m_wOffHandSkillSlot is null)
					continue;
				array<Widget@>@ kids = comp.m_wOffHandSkillSlot.m_children;
				for (uint j = 0; j < kids.length(); j++)
				{
					auto w = cast<SkillWidget>(kids[j]);
					if (w is null || w.m_item is icon)
						continue;
					@w.m_item = icon;
					w.m_mirroredIcon = false;
					if (m_shownTier != icon.m_tier)
						print("[HWP:firearms] launcher close-up on the off-hand slot: tier " + (icon.m_tier + 1));
					m_shownTier = icon.m_tier;
				}
			}
		}
	}
}
