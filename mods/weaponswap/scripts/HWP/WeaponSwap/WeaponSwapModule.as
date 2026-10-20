// Weapon swap: two weapon sets per character. The active set is what you
// hold; the other set (main-hand + off-hand) is stored as serialized items in
// the player record (HWP bag keys weaponswap.main/off), so it survives saves
// and never duplicates. A swap unequips the held pair into the store and
// equips the stored pair through the vanilla EquippedItems (which sends
// PlayerEquipmentEquip/Unequip to the lobby).
//
// Set 2 starts empty, so the first swap leaves your hands empty: equip the
// second set from your bag, then X flips between them. The inventory screen
// shows the other set in two slots above your character (core hwp-gear-slot
// widgets; click one, or press X, to swap), and while you are empty-handed
// with weapons in the other set an on-screen tip says to press X.
//
// A swap is a 2 s channel: you stand still (players/hwp/weaponswap/buffs_weaponswap.sval)
// with a bar over your head, and the sets change when it ends. A dodge or the swap key
// again cancels it. The channel also runs behind the character menu (which pauses a solo
// game), so a swap clicked there lands in the menu.
namespace HWP
{
	namespace WeaponSwap
	{
		const string KEY_MAIN = "weaponswap.main";
		const string KEY_OFF = "weaponswap.off";
		const string KEY_SET = "weaponswap.set";
		const int DEFAULT_SCANCODE = 27; // SDL scancode for X
		const int COOLDOWN_MS = 1000;
		const int CHANNEL_MS = 2000;
		const string SWAP_BUFF = "players/hwp/weaponswap/buffs_weaponswap.sval:swapping";

		int g_scancode = DEFAULT_SCANCODE;
		string g_keyName = "X";
		bool g_wasDown = false;
		int g_cooldown = 0;
		int g_version = 0;   // bumped whenever the stored set changes; the HUD tip reloads on change
		int g_channel = 0;   // ms left of the swap's channel; 0: none
		int g_swaps = 0;     // channels finished / cancelled here, for `hwp swapkey`
		int g_cancels = 0;

		void Changed()
		{
			g_version++;
			HWP::Gear::Changed();
		}

		void RefreshSettings()
		{
			int was = g_scancode;
			g_scancode = HWP::Settings::GetInt("weaponswap.key", DEFAULT_SCANCODE);
			g_keyName = HWP::Settings::GetString("weaponswap.keyname", HWP::Options::KeyName(g_scancode));
			// a new key that is held right now (just pressed to bind it) must not swap
			if (g_scancode != was)
				g_wasDown = true;
		}

		// the row in the player menu's Plus tab: click, then press the new key
		class SwapKeyOption : HWP::Options::KeyOption
		{
			string Title() override { return Resources::GetString(".hwp.weaponswap.option"); }
			int Scancode() override { return g_scancode; }
			string Value() override { return g_keyName; }
			void SetScancode(int scancode) override
			{
				if (scancode == DEFAULT_SCANCODE)
					HWP::Settings::Reset("weaponswap.key");
				else
					HWP::Settings::SetInt("weaponswap.key", scancode);
				HWP::Settings::Reset("weaponswap.keyname");
				RefreshSettings();
				Changed();
			}
		}

		void OnSettingChanged(const string &in key)
		{
			if (key.findFirst("weaponswap.") == 0)
			{
				RefreshSettings();
				Changed();
			}
		}

		HWP::DataBag@ Bag() { return HWP::SaveData::Local(); }

		// 1 or 2: the set in your hands
		int ActiveSet() { return Bag().GetInt(KEY_SET, 1) == 2 ? 2 : 1; }
		int OtherSet() { return 3 - ActiveSet(); }

		Equipment::Equipment@ LoadAlt(const string &in key)
		{
			auto sv = Bag().Get(key);
			if (sv is null)
				return null;
			return cast<Equipment::Equipment>(Item::LoadItem(sv));
		}

		void StoreAlt(const string &in key, Equipment::Equipment@ item)
		{
			if (item is null)
				Bag().Remove(key);
			else
			{
				SValueBuilder b;
				Item::SaveItem(b, item);
				Bag().Take(key, b.Build());
			}
			Changed();
		}

		bool HasAlt() { return Bag().Has(KEY_MAIN) || Bag().Has(KEY_OFF); }

		bool EmptyHanded(PlayerRecord@ rec)
		{
			return rec !is null && rec.equipped !is null
				&& rec.equipped.m_items[int(EquippedItemsSlots::MainHand)] is null
				&& rec.equipped.m_items[int(EquippedItemsSlots::OffHand)] is null;
		}

		string SwapText()
		{
			return Resources::GetString(".hwp.weaponswap.nav", { { "key", g_keyName }, { "set", "" + OtherSet() } });
		}

		bool TypingInChat()
		{
			auto main = cast<MainMenuGameMode>(g_gameMode);
			return main !is null && main.m_wChat !is null && main.m_wChat.m_wInput !is null && main.m_wChat.m_wInput.m_typing;
		}

		// true while the only open window is the character menu
		bool InPlayerMenu()
		{
			auto gm = cast<BaseGameMode>(g_gameMode);
			if (gm is null || gm.m_windowManager is null || gm.m_windowManager.m_objects.length() != 1)
				return false;
			return cast<PlayerMenu>(gm.m_windowManager.m_objects[0]) !is null;
		}

		// The raw scancode poll cannot tell the hotkey from typing an 'x' into a
		// rename box or the console, so nothing swaps while any text input has
		// the keyboard or any window other than the character menu is open.
		bool InputBusy()
		{
			auto cb = GetControlBindings();
			if (cb !is null && cb.IsExpectingTextInput())
				return true;
			if (TypingInChat())
				return true;
			auto gm = cast<BaseGameMode>(g_gameMode);
			if (gm !is null && gm.m_windowManager !is null && !gm.m_windowManager.IsEmpty() && !InPlayerMenu())
				return true;
			return false;
		}

		void Feedback(PlayerRecord@ rec, const string &in text)
		{
			auto pb = cast<PlayerBase>(rec.actor);
			if (pb !is null && pb.m_unit.IsValid())
				AddFloatingText(FloatingTextType::Pickup, text, pb.m_unit.GetPosition());
		}

		// true when the item is now in the slot (Equip returns a refused item)
		bool Wear(PlayerRecord@ rec, Equipment::Equipment@ item, EquippedItemsSlots slot)
		{
			return rec.equipped.Equip(item, slot) !is item;
		}

		// the bag, or (full) the floor at your feet, yours alone to pick up
		void ToBag(PlayerRecord@ rec, Equipment::Equipment@ item)
		{
			if (rec.equipInventory.CanAdd() || rec.actor is null)
			{
				rec.equipInventory.Add(item);
				HWP::Commands::Reply(Resources::GetString(".hwp.weaponswap.to_bag", { { "item", item.GetName() } }));
				return;
			}
			Item::DropItem(item, rec.actor.m_unit.GetPosition(), 1, true, rec);
			HWP::Commands::Reply(Resources::GetString(".hwp.weaponswap.to_floor", { { "item", item.GetName() } }));
		}

		void Swap()
		{
			auto rec = GetLocalPlayerRecord();
			if (rec is null || rec.equipped is null || rec.IsDead())
				return;

			int mainSlot = int(EquippedItemsSlots::MainHand);
			int offSlot = int(EquippedItemsSlots::OffHand);
			Equipment::Equipment@ curMain = rec.equipped.m_items[mainSlot];
			Equipment::Equipment@ curOff = rec.equipped.m_items[offSlot];
			Equipment::Equipment@ altMain = LoadAlt(KEY_MAIN);
			Equipment::Equipment@ altOff = LoadAlt(KEY_OFF);

			// requirement checks happen while the current pair is still worn,
			// as a manual equip would see it
			bool canMain = altMain is null || rec.equipped.MayEquip(altMain, false);
			bool canOff = altOff is null || rec.equipped.MayEquip(altOff, false);

			if (curMain is null && curOff is null && altMain is null && altOff is null)
			{
				Feedback(rec, Resources::GetString(".hwp.weaponswap.nothing"));
				return;
			}

			if (curMain !is null)
				rec.equipped.Unequip(EquippedItemsSlots::MainHand);
			if (curOff !is null)
				rec.equipped.Unequip(EquippedItemsSlots::OffHand);

			// Equip re-checks the requirements without the pair just taken off
			// (whose stats may have been what made the alt weapon wieldable) and
			// hands a refused item back, so every item is accounted for here:
			// worn, stored as the other set, or in the bag
			Equipment::Equipment@ keepMain = curMain;
			Equipment::Equipment@ keepOff = curOff;

			if (altMain !is null && !(canMain && Wear(rec, altMain, EquippedItemsSlots::MainHand)))
			{
				@keepMain = altMain;
				HWP::Commands::Reply(Resources::GetString(".hwp.weaponswap.cannot", { { "item", altMain.GetName() } }));
				if (curMain !is null && !Wear(rec, curMain, EquippedItemsSlots::MainHand))
					ToBag(rec, curMain);
			}

			bool twoHanded = rec.equipped.m_items[mainSlot] !is null && rec.equipped.m_items[mainSlot].GetSlot() == Equipment::Slot::TwoHanded;
			if (altOff !is null && (twoHanded || !(canOff && Wear(rec, altOff, EquippedItemsSlots::OffHand))))
			{
				@keepOff = altOff;
				if (!twoHanded)
					HWP::Commands::Reply(Resources::GetString(".hwp.weaponswap.cannot", { { "item", altOff.GetName() } }));
				if (curOff !is null && (twoHanded || !Wear(rec, curOff, EquippedItemsSlots::OffHand)))
					ToBag(rec, curOff);
			}

			StoreAlt(KEY_MAIN, keepMain);
			StoreAlt(KEY_OFF, keepOff);
			Bag().SetInt(KEY_SET, OtherSet());
			Changed();
			g_cooldown = COOLDOWN_MS;

			Feedback(rec, Resources::GetString(".hwp.weaponswap.swapped", { { "set", "" + ActiveSet() } }));
			HWP::Log("weaponswap", "set " + ActiveSet() + " in hand; other set " + (keepMain is null ? "-" : keepMain.GetName())
				+ " / " + (keepOff is null ? "-" : keepOff.GetName()));

			auto gm = cast<BaseGameMode>(g_gameMode);
			if (gm !is null)
				gm.m_windowManager.CloseTooltip();
		}

		PlayerBase@ LocalPlayer()
		{
			auto rec = GetLocalPlayerRecord();
			return rec is null ? null : cast<PlayerBase>(rec.actor);
		}

		void RemoveSwapBuff(PlayerBase@ plr)
		{
			if (plr is null)
				return;
			uint hash = HashString(SWAP_BUFF);
			bool removed = false;
			auto buffs = plr.m_buffs.m_buffs;
			for (uint i = 0; i < buffs.length(); i++)
			{
				if (buffs[i].m_def.m_pathHash == hash)
				{
					buffs[i].Clear();
					buffs.removeAt(i--);
					removed = true;
				}
			}
			if (removed)
				plr.RefreshModifiers();
		}

		bool Dodging(PlayerBase@ plr)
		{
			for (uint i = 0; i < plr.m_skills.length(); i++)
			{
				auto sk = plr.m_skills[i];
				if (sk is null || sk.m_type != PlayerSkillType::Dash)
					continue;
				auto a = cast<Skills::ActiveSkill>(sk);
				if (a !is null && a.m_castingC > 0)
					return true;
				auto p = cast<Skills::PlayerSkill>(sk);
				if (p !is null && p.m_castingT >= 0)
					return true;
			}
			return false;
		}

		// start the channel; the sets change when it ends (UpdateChannel)
		void StartChannel()
		{
			auto rec = GetLocalPlayerRecord();
			auto plr = LocalPlayer();
			if (rec is null || rec.equipped is null || rec.IsDead() || plr is null)
				return;
			if (EmptyHanded(rec) && !HasAlt())
			{
				Feedback(rec, Resources::GetString(".hwp.weaponswap.nothing"));
				return;
			}
			g_channel = CHANNEL_MS;
			auto def = LoadActorBuff(SWAP_BUFF);
			if (def !is null)
				plr.ApplyBuff(ActorBuff(plr, def, 1.0f, false));
			Feedback(rec, Resources::GetString(".hwp.weaponswap.channel", { { "set", "" + OtherSet() } }));
			HWP::Log("weaponswap", "swap channel started (" + CHANNEL_MS + " ms)");
		}

		void CancelChannel(const string &in why)
		{
			if (g_channel <= 0)
				return;
			g_channel = 0;
			g_cancels++;
			RemoveSwapBuff(LocalPlayer());
			auto rec = GetLocalPlayerRecord();
			if (rec !is null && rec.actor !is null)
				Feedback(rec, Resources::GetString(".hwp.weaponswap.cancelled"));
			HWP::Log("weaponswap", "swap cancelled (" + why + ")");
		}

		// dodge: the Dash key (held or pressed) or a dash under way. Rooted by the swap buff,
		// the dash itself may not get going, so the key alone cancels
		void UpdateChannel(int ms, bool paused, bool dashKey)
		{
			// a solo game pauses behind the character menu: the channel runs there too, so a
			// swap clicked in the menu lands in it (no time passes for the world either way)
			if (g_channel <= 0 || (paused && !InPlayerMenu()))
				return;
			auto rec = GetLocalPlayerRecord();
			auto plr = LocalPlayer();
			if (rec is null || plr is null || rec.IsDead())
			{
				CancelChannel("dead");
				return;
			}
			if ((dashKey && !paused) || Dodging(plr))
			{
				CancelChannel("dodge");
				return;
			}
			g_channel -= ms;
			if (g_channel > 0)
				return;
			g_channel = 0;
			RemoveSwapBuff(plr);
			g_swaps++;
			Swap();
		}

		// the channel's bar over the local player
		void RenderChannel(int idt, SpriteBatch& sb)
		{
			auto plr = LocalPlayer();
			if (g_channel <= 0 || plr is null || !plr.m_unit.IsValid())
				return;
			const float w = 30;
			const float h = 3;
			vec2 at = ToScreenspace(plr.m_unit.GetInterpolatedPosition(idt) + vec3(0, -34, 0)) / g_gameMode.m_wndScale - vec2(w / 2, 0);
			at = vec2(int(at.x), int(at.y));
			float done = clamp(1.0f - g_channel / float(CHANNEL_MS), 0.0f, 1.0f);
			sb.FillRectangle(vec4(at.x - 1, at.y - 1, w + 2, h + 2), vec4(0, 0, 0, 0.7f));
			sb.FillRectangle(vec4(at.x, at.y, int(w * done), h), vec4(0.55f, 0.8f, 1.0f, 1.0f));
		}

		// the key or a click: start a swap, or cancel the one under way
		void Toggle()
		{
			if (g_channel > 0)
				CancelChannel("key");
			else if (g_cooldown <= 0)
				StartChannel();
		}

		// move the other set back into the bag
		void Drop()
		{
			auto rec = GetLocalPlayerRecord();
			if (rec is null || rec.equipInventory is null)
				return;
			auto altMain = LoadAlt(KEY_MAIN);
			auto altOff = LoadAlt(KEY_OFF);
			int needed = (altMain is null ? 0 : 1) + (altOff is null ? 0 : 1);
			if (needed == 0)
				return;
			if (rec.equipInventory.m_maxItems >= 0 && int(rec.equipInventory.m_items.length()) + needed > rec.equipInventory.m_maxItems)
			{
				HWP::Commands::Reply(Resources::GetString(".hwp.weaponswap.inventory_full"));
				return;
			}
			if (altMain !is null)
				rec.equipInventory.Add(altMain);
			if (altOff !is null)
				rec.equipInventory.Add(altOff);
			StoreAlt(KEY_MAIN, null);
			StoreAlt(KEY_OFF, null);
			HWP::Commands::Reply(Resources::GetString(".hwp.weaponswap.dropped"));
		}

		void Poll(int ms, bool paused)
		{
			if (g_cooldown > 0)
				g_cooldown -= ms;
			bool down = Platform::IsKeyDown(ControllerType::Keyboard, 0, g_scancode);
			bool pressed = down && !g_wasDown;
			g_wasDown = down;
			if (!pressed || g_cooldown > 0 || InputBusy())
				return;
			// on the Plus tab the key may be getting rebound (or just tried out)
			if (HWP::Options::TabOpen())
				return;
			// a solo game pauses behind the character menu; swapping there is wanted
			if (paused && !InPlayerMenu())
				return;
			Toggle();
		}

		// 'hwp swap': as the key (start or cancel the channel); 'now' (cheat): at once
		void CmdSwap(array<string>@ args)
		{
			if (args.length() > 0 && args[0] == "now")
			{
				if (HWP::Cheats::On())
					Swap();
				return;
			}
			Toggle();
			HWP::Commands::Reply(g_channel > 0 ? "swap channel: " + g_channel + " ms" : "swap channel: none");
		}
		void CmdSwapDrop(array<string>@ args) { Drop(); }

		void CmdSwapKey(array<string>@ args)
		{
			if (args.length() < 1 || parseInt(args[0]) <= 0)
			{
				auto altMain = LoadAlt(KEY_MAIN);
				auto altOff = LoadAlt(KEY_OFF);
				HWP::Commands::Reply(Resources::GetString(".hwp.weaponswap.status", {
					{ "set", "" + ActiveSet() }, { "main", altMain is null ? "-" : altMain.GetName() },
					{ "off", altOff is null ? "-" : altOff.GetName() }, { "code", "" + g_scancode }, { "name", g_keyName } }));
				HWP::Commands::Reply("swap channel: " + (g_channel > 0 ? g_channel + " ms left" : "none") + ", swaps " + g_swaps + ", cancelled " + g_cancels);
				return;
			}
			int code = parseInt(args[0]);
			HWP::Settings::SetInt("weaponswap.key", code);
			if (args.length() >= 2)
				HWP::Settings::SetString("weaponswap.keyname", args[1]);
			else
				HWP::Settings::Reset("weaponswap.keyname");
			RefreshSettings();
			Changed();
			HWP::Commands::Reply(Resources::GetString(".hwp.weaponswap.key_set", { { "code", "" + code }, { "name", g_keyName } }));
		}
	}
}

// The other weapon set in the character menu: core hwp-gear-slot widgets
// hwp-alt-main / hwp-alt-off (gui/playermenu/character.gui). Drawn dimmed;
// hovering shows the item (or, empty, what the slot is), clicking swaps sets.
class HWPAltWeaponSlot : HWP::Gear::Slot
{
	bool m_main;

	HWPAltWeaponSlot(bool main)
	{
		m_main = main;
	}

	Equipment::Equipment@ Item() override
	{
		if (m_main)
			return HWP::WeaponSwap::LoadAlt(HWP::WeaponSwap::KEY_MAIN);
		auto off = HWP::WeaponSwap::LoadAlt(HWP::WeaponSwap::KEY_OFF);
		if (off !is null)
			return off;
		// a two-handed weapon fills both slots, like the vanilla off-hand slot shows it
		auto main = HWP::WeaponSwap::LoadAlt(HWP::WeaponSwap::KEY_MAIN);
		if (main !is null && main.GetSlot() == Equipment::Slot::TwoHanded)
			return main;
		return null;
	}

	bool Mirrored() override
	{
		return !m_main && !HWP::WeaponSwap::Bag().Has(HWP::WeaponSwap::KEY_OFF);
	}

	string Title() override
	{
		return Resources::GetString(".hwp.weaponswap.slot_title", { { "set", "" + HWP::WeaponSwap::OtherSet() } });
	}

	string Text() override
	{
		return Resources::GetString(m_main ? ".hwp.weaponswap.slot_main" : ".hwp.weaponswap.slot_off", { { "key", HWP::WeaponSwap::g_keyName } });
	}

	array<string>@ Nav() override
	{
		return { HWP::WeaponSwap::SwapText() };
	}

	void Click() override
	{
		HWP::WeaponSwap::Toggle();
	}
}

// The empty-hands tip: shown while you hold no weapon and the other set has one.
class HWPWeaponSwapHUD : HUDComponent
{
	TextWidget@ m_text;
	int m_seen = -1;
	bool m_hasAlt = false;

	HWPWeaponSwapHUD(GUIBuilder@ b)
	{
		super(b, "gui/hwp_weaponswap.gui");
		@m_text = cast<TextWidget>(m_widget.GetWidgetById("text"));
		m_visible = false;
	}

	void Update(int dt, PlayerRecord@ record) override
	{
		if (m_seen != HWP::WeaponSwap::g_version)
		{
			m_seen = HWP::WeaponSwap::g_version;
			m_hasAlt = HWP::WeaponSwap::HasAlt();
			m_text.SetText(Resources::GetString(".hwp.weaponswap.tip", { { "key", HWP::WeaponSwap::g_keyName } }));
		}
		bool show = m_hasAlt && record !is null && !record.IsDead() && HWP::WeaponSwap::EmptyHanded(record);
		if (show != m_visible)
		{
			m_visible = show;
			Invalidate();
		}
		HUDComponent::Update(dt, record);
	}
}

// the two lines under the other set in the character screen (core
// hwp-gear-label widgets): a caption and the swap key
class HWPAltWeaponLabel : HWP::Gear::Label
{
	bool m_hint;

	HWPAltWeaponLabel(bool hint)
	{
		m_hint = hint;
	}

	string Text() override
	{
		if (m_hint)
			return Resources::GetString(".hwp.weaponswap.label_hint", { { "key", HWP::WeaponSwap::g_keyName } });
		return Resources::GetString(".hwp.weaponswap.label");
	}
}

namespace HWPWeaponSwap
{
	[Hook]
	void HUDConstructor(HUD@ hud, GUIBuilder@ b)
	{
		hud.m_components.insertLast(HWPWeaponSwapHUD(b));
	}
}

namespace Modules
{
	class HWPWeaponSwapModule : Module, HWP::ModuleStart
	{
		HWPWeaponSwapModule()
		{
			super("hwp-weaponswap");
			HWP::Gear::Register("hwp-alt-main", HWPAltWeaponSlot(true));
			HWP::Gear::Register("hwp-alt-off", HWPAltWeaponSlot(false));
			HWP::Gear::RegisterLabel("hwp-alt-caption", HWPAltWeaponLabel(false));
			HWP::Gear::RegisterLabel("hwp-alt-hint", HWPAltWeaponLabel(true));
			HWP::Commands::Register("swap", "[now]  swap weapon sets (hotkey X): a 2 s channel, again to cancel; now (cheat) at once", HWP::Commands::Handler(HWP::WeaponSwap::CmdSwap));
			HWP::Commands::Register("swapkey", "[scancode [name]]  show or set the swap hotkey", HWP::Commands::Handler(HWP::WeaponSwap::CmdSwapKey));
			HWP::Commands::Register("swapdrop", " move the other weapon set back into your inventory", HWP::Commands::Handler(HWP::WeaponSwap::CmdSwapDrop));
			HWP::Commands::OnSettingChanged(HWP::Commands::SettingListener(HWP::WeaponSwap::OnSettingChanged));
			HWP::Options::Register("swapkey", HWP::WeaponSwap::SwapKeyOption());
		}

		void Start(StartMode sMode)
		{
			HWP::WeaponSwap::RefreshSettings();
			HWP::WeaponSwap::g_cooldown = 0;
			HWP::WeaponSwap::g_channel = 0;
			HWP::WeaponSwap::g_wasDown = false;
			HWP::WeaponSwap::Changed();
		}

		void UpdateFrame(int ms, GameInput& gameInput, MenuInput& menuInput, bool paused) override
		{
			HWP::WeaponSwap::Poll(ms, paused);
			HWP::WeaponSwap::UpdateChannel(ms, paused, gameInput.Dash.Down || gameInput.Dash.Pressed);
		}

		void RenderFrame(int idt, SpriteBatch& sb) override
		{
			HWP::WeaponSwap::RenderChannel(idt, sb);
		}
	}
}
