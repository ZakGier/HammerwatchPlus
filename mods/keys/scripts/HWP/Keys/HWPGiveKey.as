// The key pickups' effect: vanilla GiveKey, but the count goes through
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
		HWP::Keys::AddKeys(player, m_key, amount);
		Stats::Add(HashString("key-found-" + m_key), amount, player);
		LootLog::PresentPickup(player, Resources::GetString(".item.key." + m_key), amount);
		HWP::Keys::RefreshHUD();
	}
}
