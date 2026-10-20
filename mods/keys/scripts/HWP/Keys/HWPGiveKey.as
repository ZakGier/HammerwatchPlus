// The key pickups' effect: vanilla GiveKey, but in a run the key goes to the
// party pool (HWP::Keys::GiveFoundKey; a client's add goes to the host), in town through
// HWP::Keys::AddKeys (vanilla PlayerRecord.AddKeys corrupts it, KeysModule.as).
class HWPGiveKey : GiveKey
{
	HWPGiveKey(UnitPtr unit, SValue& params)
	{
		super(unit, params);
	}

	void Apply(PlayerRecord@ player) override
	{
		int amount = m_amount;
		int tier = HWP::Keys::TierIndex(m_key);
		if (tier == 0)
		{
			HWP::Keys::AddKeys(player, m_key, amount);
			return;
		}
		HWP::Keys::GiveFoundKey(player, tier, amount);
		Stats::Add(HashString("key-found-" + m_key), amount, player);
		LootLog::PresentPickup(player, Resources::GetString(".item.key." + m_key), amount);
		HWP::Keys::RefreshHUD();
	}
}
