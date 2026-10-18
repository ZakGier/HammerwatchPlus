// The town portal's interact (doodads/hwp/forsaken_portal.unit): the vanilla mission
// board content for the hwp_campaign set. Vanilla GetItems sorts the fetched missions
// with a callback, and the engine's array sort throws "Index out of bounds" on an empty
// array, so a character the set's conditionals leave nothing for (the story intro not
// done yet) hit a script exception and no window opened (probe-portal, 2026-10-18).
// Here the portal says why instead, and the list is only sorted when it has two.
class HWPCampaignShopContent : MissionShopContent
{
	HWPCampaignShopContent(UnitPtr u, SValue& params)
	{
		super(u, params);
	}

	array<MissionDef@>@ Missions(PlayerRecord@ player)
	{
		return MissionDef::FetchMissionsFromSet(player, m_missionSetHash, m_numMissionsToShow, m_showTestMissions);
	}

	void Interact(PlayerRecord@ player, int interactLevel) override
	{
		if (Missions(player).length() == 0)
		{
			if (player !is null && player.actor !is null)
				AddFloatingText(FloatingTextType::Pickup, Resources::GetString(".hwp.campaign.portal_locked"),
					player.actor.m_unit.GetPosition() + vec3(0, -24, 0));
			HWP::Log("campaign", "portal: no mission for this character (story intro not done)");
			return;
		}
		MissionShopContent::Interact(player, interactLevel);
	}

	array<IShopItem@> GetItems() override
	{
		auto missions = Missions(m_player);
		if (missions.length() > 1)
		{
			missions.sort(function(a, b){
				return a.GetLevelSpan().x < b.GetLevelSpan().x;
			});
		}
		if (m_rewardSeed == 0)
			m_rewardSeed = randi();
		array<IShopItem@> ret;
		for (uint i = 0; i < missions.length(); i++)
			ret.insertLast(MissionShopContentItem(missions[i], m_player, m_rewardSeed + i));
		return ret;
	}
}
