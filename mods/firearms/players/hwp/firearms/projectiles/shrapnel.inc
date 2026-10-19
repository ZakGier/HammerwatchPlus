<!--
	Elemental Shrapnel (demo_hoarder.sval): the elemental penetration every explosive carries.
	hwp-shrapnel is a custom stat (Modifiers::CustomStat), which a bind falls back to when the
	skill has no bind of that name (PlayerBase.FetchData); Reload keeps it at 0 without the orb.
	Put it right after a Damage with the same true-strike so it merges into that damage;
	ShrapnelBlockable is for a shield-blockable one (the rifle's grenade launcher).
-->
%defblock Shrapnel TRUESTRIKE
					<dict>
						<string name="class">DamagePenetration</string>
						<string name="fire-bind">hwp-shrapnel</string>
						<string name="ice-bind">hwp-shrapnel</string>
						<string name="lightning-bind">hwp-shrapnel</string>
						<string name="poison-bind">hwp-shrapnel</string>
						<bool name="true-strike">%%TRUESTRIKE%%</bool>
					</dict>
%endblock
%defblock ShrapnelBlockable
					<dict>
						<string name="class">DamagePenetration</string>
						<string name="fire-bind">hwp-shrapnel</string>
						<string name="ice-bind">hwp-shrapnel</string>
						<string name="lightning-bind">hwp-shrapnel</string>
						<string name="poison-bind">hwp-shrapnel</string>
						<bool name="shield-blockable">true</bool>
					</dict>
%endblock
