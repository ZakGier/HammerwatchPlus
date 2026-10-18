// The General Merchant: sells keys and bag slots (core HWP::Bag) in town,
// and on its Trinkets tab six trinkets to take into the next run (below). First
// interact class of the exit guard by the run start (our copy of
// actors/npcs/town/npc_misc_guard_exit.unit); his vanilla speech bubble is the
// second, so NPCBehavior shows it once the shop window closes. Uses the stock
// ShopWindow (gui/shops/default.gui) with one IShopItem per key tier. The gold is spent
// inside Buy (AutoSpendCost false) so an unavailable purchase cannot cost
// anything - keys live in the buyer's own PlayerRecord, nothing is networked.

class HWPKeyShopItem : IShopItem
{
	string m_key;
	int m_tier;
	ShopCost@ m_cost;

	HWPKeyShopItem(int tier, int price)
	{
		m_tier = tier;
		m_key = HWP::Keys::TIERS[tier - 1];
		@m_cost = ShopCost(MaterialType::Gold, price);
	}

	string GetID() { return m_key; }
	uint GetIDHash() { return HashString(m_key); }
	string GetTitle() { return Resources::GetString(".item.key." + m_key); }
	string GetSubTitle() { return Resources::GetString(".hwp.keys.shop." + m_key); }
	string GetDescription() { return ""; }

	ScriptSprite@ GetIcon()
	{
		return ScriptSprite(Resources::GetTexture2D("items/special/base.png"), HWP::Keys::KeyIconFrame(m_tier));
	}

	Sprite@ GetBackground() { return GetQualitySprite(HWP::Keys::TierQuality(m_tier)); }

	ShopCost@ GetCost() { return m_cost; }
	bool AutoSpendCost() { return false; }
	string OnFunc() { return "buy"; }

	// one ace key at a time: it is the expensive, run-defining one
	bool IsAvailable(PlayerRecord@ player)
	{
		if (player is null)
			return false;
		if (m_tier == 4)
			return player.GetKeys(m_key) < 1;
		return true;
	}

	void ShowTooltip(WindowManager@ manager, bool compare) { }
	Item::Item@ GetItem() { return null; }
}

// One more equipment bag slot for the buyer's character (core HWP::Bag): the
// price climbs with every slot, up to a full extra row.
class HWPBagShopItem : IShopItem
{
	ShopCost@ m_cost;

	HWPBagShopItem(PlayerRecord@ player)
	{
		// sold out at full size: no cost line (the subtitle says the bag is full)
		int price = HWP::Bag::NextPrice(player);
		if (price > 0)
			@m_cost = ShopCost(MaterialType::Gold, price);
	}

	string GetID() { return "hwp_bag_slot"; }
	uint GetIDHash() { return HashString("hwp_bag_slot"); }
	string GetTitle() { return Resources::GetString(".hwp.bag.shop_title"); }

	string GetSubTitle()
	{
		auto rec = GetLocalPlayerRecord();
		dictionary params = { { "cap", HWP::Bag::Capacity(rec) }, { "max", HWP::Bag::BASE + HWP::Bag::MAX_EXTRA } };
		return Resources::GetString(HWP::Bag::NextPrice(rec) > 0 ? ".hwp.bag.shop_sub" : ".hwp.bag.shop_sub_full", params);
	}

	string GetDescription() { return ""; }

	ScriptSprite@ GetIcon()
	{
		return ScriptSprite(Resources::GetTexture2D("gui/gui.png"), vec4(190, 40, 27, 27));
	}

	Sprite@ GetBackground() { return GetQualitySprite(Item::Quality::Uncommon); }

	ShopCost@ GetCost() { return m_cost; }
	bool AutoSpendCost() { return false; }
	string OnFunc() { return "buy"; }
	bool IsAvailable(PlayerRecord@ player) { return HWP::Bag::NextPrice(player) > 0; }
	void ShowTooltip(WindowManager@ manager, bool compare) { }
	Item::Item@ GetItem() { return null; }
}

class HWPGeneralMerchant : AShopContent
{
	string m_tab = "keys"; // or "trinkets" (HWPMerchantWindow's tab row)

	HWPGeneralMerchant() {}
	HWPGeneralMerchant(UnitPtr u, SValue& params)
	{
		super(u, params);
	}

	string GetName() override { return ".hwp.keys.merchant.name"; }

	AWindowObject@ MakeShopWindow(GUIBuilder@ guiBuilder) override
	{
		@m_window = HWPMerchantWindow(guiBuilder, this);
		return m_window;
	}

	array<IShopItem@> GetItems() override
	{
		array<IShopItem@> ret;
		if (m_tab == "trinkets")
		{
			auto stock = HWP::Keys::TrinketStock(m_player !is null ? m_player : GetLocalPlayerRecord());
			for (uint i = 0; i < stock.length(); i++)
				ret.insertLast(HWPTrinketShopItem(stock[i]));
			return ret;
		}
		for (int tier = 1; tier <= 4; tier++)
			ret.insertLast(HWPKeyShopItem(tier, HWP::Keys::KeyPrice(tier)));
		ret.insertLast(HWPBagShopItem(m_player !is null ? m_player : GetLocalPlayerRecord()));
		return ret;
	}

	string GetEmptyShopText() override
	{
		return m_tab == "trinkets" ? ".hwp.keys.merchant.sold_out" : "";
	}

	bool Buy(const string &in func, uint hash, IShopItem@ item) override
	{
		if (func != "buy" || m_player is null)
			return false;
		auto trinketItem = cast<HWPTrinketShopItem>(item);
		if (trinketItem !is null)
		{
			if (!HWP::Keys::BuyTrinket(m_player, trinketItem.m_item))
				return false;
			LootLog::PresentPickup(m_player, Resources::GetString(".hwp.keys.merchant.packed_one", { { "name", trinketItem.m_item.GetName() } }), 1);
			return true;
		}
		auto bagItem = cast<HWPBagShopItem>(item);
		if (bagItem !is null)
		{
			if (!HWP::Bag::Buy(m_player))
				return false;
			LootLog::PresentPickup(m_player, Resources::GetString(".hwp.bag.bought", { { "cap", HWP::Bag::Capacity(m_player) } }), 1);
			return true;
		}
		auto keyItem = cast<HWPKeyShopItem>(item);
		if (keyItem is null || !keyItem.IsAvailable(m_player))
			return false;
		if (!keyItem.m_cost.CanAfford(m_player))
			return false;

		keyItem.m_cost.Spend(m_player);
		m_player.AddKeys(keyItem.m_key, 1);
		Stats::Add(HashString("key-bought-" + keyItem.m_key), 1, m_player);
		LootLog::PresentPickup(m_player, Resources::GetString(".item.key." + keyItem.m_key), 1);
		HWP::Keys::RefreshHUD();
		HWP::Log("keys", m_player.GetName() + " bought a " + keyItem.m_key + " key");
		return true;
	}

	void Save(SValueBuilder& builder) override { }
	void Load(SValue@ sval) override { }
}

// ---- the Trinkets tab ------------------------------------------------------------
// Six trinkets per character (2 common, 2 uncommon, 2 rare), at the price a
// run's trinket shop asks (TrinketShopShopContent: GetPrice() x (1 + 0.2 x
// ShopLevel); the dungeon shop rooms place theirs at ShopLevel 1). A bought
// trinket is packed: ResetForNewMission empties the trinket bag when the run
// is set up, so the packed ones are handed over (GiveItem, local like every
// vanilla trinket shop) when the run's first level starts. The stock rerolls
// after every run. Everything is the buyer's own HWP save data.
namespace HWP
{
	namespace Keys
	{
		const string KEY_TSTOCK = "keys.trinket_stock";   // "id,id,..." still for sale
		const string KEY_TPACKED = "keys.trinket_packed"; // "id,id,..." bought, not handed over
		const string KEY_TSTALE = "keys.trinket_stale";   // a run started since the roll
		const float TRINKET_PRICE_RATE = 1.2f;
		const array<Item::Quality> TRINKET_STOCK = {
			Item::Quality::Common, Item::Quality::Common,
			Item::Quality::Uncommon, Item::Quality::Uncommon,
			Item::Quality::Rare, Item::Quality::Rare };

		array<string>@ IdList(HWP::DataBag@ bag, const string &in key)
		{
			array<string> ret;
			auto parts = bag.GetString(key).split(",");
			for (uint i = 0; i < parts.length(); i++)
			{
				if (parts[i] != "")
					ret.insertLast(parts[i]);
			}
			return ret;
		}

		void SetIdList(HWP::DataBag@ bag, const string &in key, array<string>@ ids)
		{
			bag.SetString(key, join(ids, ","));
		}

		Item::Trinket@ TrinketById(const string &in id)
		{
			return cast<Item::Trinket>(Item::Get(HashString(id)));
		}

		int TrinketPrice(Item::Trinket@ t)
		{
			return int(t.GetPrice() * TRINKET_PRICE_RATE);
		}

		// the stock for sale, rolled when there is none yet or a run happened since
		array<Item::Trinket@>@ TrinketStock(PlayerRecord@ rec)
		{
			array<Item::Trinket@> ret;
			if (rec is null)
				return ret;
			auto bag = HWP::SaveData::Player(rec);
			if (!bag.Has(KEY_TSTOCK) || bag.GetBool(KEY_TSTALE, false))
				RollTrinkets(rec, bag.GetBool(KEY_TSTALE, false));
			auto ids = IdList(bag, KEY_TSTOCK);
			for (uint i = 0; i < ids.length(); i++)
			{
				auto t = TrinketById(ids[i]);
				if (t !is null)
					ret.insertLast(t);
			}
			return ret;
		}

		void RollTrinkets(PlayerRecord@ rec, bool afterRun)
		{
			auto bag = HWP::SaveData::Player(rec);
			array<string> ids;
			for (uint i = 0; i < TRINKET_STOCK.length(); i++)
			{
				// GetRandomTrinket only avoids what the bag holds: reroll repeats
				Item::Trinket@ t;
				for (int tries = 0; tries < 8; tries++)
				{
					@t = Item::GetRandomTrinket(rec, TRINKET_STOCK[i]);
					if (t !is null && ids.find(t.m_id) < 0)
						break;
				}
				if (t !is null && ids.find(t.m_id) < 0)
					ids.insertLast(t.m_id);
			}
			SetIdList(bag, KEY_TSTOCK, ids);
			bag.SetBool(KEY_TSTALE, false);
			HWP::Log("keys", "trinket stock rolled" + (afterRun ? " (after a run)" : "") + ": " + join(ids, " "));
		}

		bool BuyTrinket(PlayerRecord@ rec, Item::Trinket@ t)
		{
			auto bag = HWP::SaveData::Player(rec);
			auto stock = IdList(bag, KEY_TSTOCK);
			int at = stock.find(t.m_id);
			if (at < 0)
				return false;
			ShopCost cost(MaterialType::Gold, TrinketPrice(t));
			if (!cost.CanAfford(rec))
				return false;
			cost.Spend(rec);
			stock.removeAt(at);
			SetIdList(bag, KEY_TSTOCK, stock);
			auto packed = IdList(bag, KEY_TPACKED);
			packed.insertLast(t.m_id);
			SetIdList(bag, KEY_TPACKED, packed);
			HWP::Log("keys", rec.GetName() + " packed trinket " + t.m_id + " for " + TrinketPrice(t) + " gold");
			return true;
		}

		// every gameplay level start (ModuleStart): a run level hands the
		// packed trinkets to the local character and marks the stock for a reroll
		void TrinketsLevelStart()
		{
			if (g_inTown)
				return;
			auto rec = GetLocalPlayerRecord();
			if (rec is null || rec.playerClass is null)
				return;
			auto bag = HWP::SaveData::Player(rec);
			bag.SetBool(KEY_TSTALE, true);
			auto packed = IdList(bag, KEY_TPACKED);
			if (packed.length() == 0)
				return;
			bag.Remove(KEY_TPACKED);
			int given = 0;
			for (uint i = 0; i < packed.length(); i++)
			{
				auto t = TrinketById(packed[i]);
				if (t is null)
					continue;
				rec.GiveItem(t);
				given++;
			}
			HWP::Log("keys", "handed over " + given + " packed trinket(s): " + join(packed, " "));
		}
	}
}

class HWPTrinketShopItem : IShopItem
{
	Item::Trinket@ m_item;
	ShopCost@ m_cost;

	HWPTrinketShopItem(Item::Trinket@ item)
	{
		@m_item = item;
		@m_cost = ShopCost(MaterialType::Gold, HWP::Keys::TrinketPrice(item));
	}

	string GetID() { return "hwp_trinket_" + m_item.m_id; }
	uint GetIDHash() { return HashString(GetID()); }
	string GetTitle() { return "\\c" + Item::QualityColorString(m_item.GetQuality()) + m_item.GetName(); }
	string GetSubTitle() { return m_item.m_set !is null ? m_item.m_set.m_name : ""; }
	string GetDescription() { return m_item.GetDescription(GetLocalPlayerRecord()); }
	ScriptSprite@ GetIcon() { return m_item.GetIcon(); }
	Sprite@ GetBackground() { return GetQualitySprite(m_item.GetQuality()); }
	ShopCost@ GetCost() { return m_cost; }
	bool AutoSpendCost() { return false; }
	string OnFunc() { return "buy"; }
	bool IsAvailable(PlayerRecord@ player) { return player !is null; }

	void ShowTooltip(WindowManager@ manager, bool compare)
	{
		manager.SetTooltip(Item::BuildItemTooltip(m_item, m_item.GetPrice(), 1, false), true);
	}

	Item::Item@ GetItem() { return null; }
}

// the stock ShopWindow plus the tab row (gui/hwp_merchant.gui)
class HWPMerchantWindow : ShopWindow
{
	MenuTabGroupWidget@ m_tabs;

	HWPMerchantWindow(GUIBuilder@ b, AShopContent@ content)
	{
		super(b, content, "gui/hwp_merchant.gui");
		@m_tabs = cast<MenuTabGroupWidget>(m_widget.GetWidgetById("hwp-merchant-tabs"));
		auto merchant = cast<HWPGeneralMerchant>(content);
		if (m_tabs !is null && merchant !is null)
			m_tabs.SetChecked(merchant.m_tab == "trinkets" ? 1 : 0);
	}

	void Refresh() override
	{
		ShopWindow::Refresh();
		auto merchant = cast<HWPGeneralMerchant>(m_shopContent);
		auto info = cast<TextWidget>(m_widget.GetWidgetById("extra-info"));
		if (merchant is null || info is null)
			return;
		string text = "";
		if (merchant.m_tab == "trinkets")
		{
			auto rec = merchant.m_player !is null ? merchant.m_player : GetLocalPlayerRecord();
			int packed = rec is null ? 0 : HWP::Keys::IdList(HWP::SaveData::Player(rec), HWP::Keys::KEY_TPACKED).length();
			text = Resources::GetString(".hwp.keys.merchant.packed", { { "num", packed } });
		}
		info.SetText(text);
	}

	void OnFunc(Widget@ sender, const string &in name) override
	{
		auto parse = name.split(" ");
		if (parse.length() == 2 && parse[0] == "hwp-tab")
		{
			auto merchant = cast<HWPGeneralMerchant>(m_shopContent);
			if (merchant !is null && merchant.m_tab != parse[1])
			{
				merchant.m_tab = parse[1];
				m_manager.CloseTooltip();
				Refresh();
			}
			return;
		}
		ShopWindow::OnFunc(sender, name);
	}
}
