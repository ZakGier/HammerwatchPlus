<!--
	Elemental Bullets' rounds (Elemental.as HWPFirearmsGunShot fires one when a shot rolls an
	element): a gun's round (rifle_round, glock_round...) with its weapon damage all as the
	element and no armor penetration, the orbs' riders (HWPFirearmsBulletRider) and the
	element's tinted look (round_<LOOK>_<ELEMENT>.effect). One file per gun and element,
	each a single %block Round with that gun's numbers.
-->
%defblock Round TTL SPEED PEN MUL OFFHAND LOOK ELEMENT
<unit netsync="none">
	<behavior class="NewProjectile">
		<string name="anim">default</string>
		<int name="ttl">%%TTL%%</int>
		<float name="speed">%%SPEED%%</float>
		<int name="penetration">%%PEN%%</int>
		<bool name="bounce-on-collide">false</bool>

		<array name="modifiers">
			<dict>
				<string name="class">Projectile::Speed</string>
				<float name="hit-intensity-mul">0.5</float>
			</dict>
			<!-- Critical Aim's focus (Combat.as Projectile::HWPFirearmsShot) -->
			<dict>
				<string name="class">Projectile::HWPFirearmsShot</string>
			</dict>
		</array>

		<array name="hit-effects">
			<dict>
				<string name="class">HWPFirearmsElementalDamage</string>
				<string name="element">%%ELEMENT%%</string>
				<bool name="off-hand">%%OFFHAND%%</bool>
				<float name="mul">%%MUL%%</float>
				<bool name="shield-blockable">true</bool>
			</dict>
			<dict>
				<string name="class">HWPFirearmsBulletRider</string>
				<string name="element">%%ELEMENT%%</string>
			</dict>
			<dict>
				<string name="class">SpawnEffect</string>
				<string name="effect">effects/generic/impacts/pierce_impact_1.effect</string>
				<bool name="clone-owner-params">true</bool>
			</dict>
			<dict>
				<string name="class">PlaySound</string>
				<string name="sound">event:/sfx/items/item_metal_small_2</string>
			</dict>
		</array>

		<array name="miss-effects">
			<dict>
				<string name="class">SpawnEffect</string>
				<string name="effect">effects/generic/impacts/spark_impact_1.effect</string>
			</dict>
		</array>

		<dict name="effect-params">
			<float name="height">11</float>
		</dict>
	</behavior>

	<scenes start="default">
		<scene name="default">
			<collision static="false">
				<circle radius="5" projectile="true" />
			</collision>
			<effect src="players/hwp/firearms/projectiles/round_%%LOOK%%_%%ELEMENT%%.effect" />
		</scene>
	</scenes>
</unit>
%endblock
