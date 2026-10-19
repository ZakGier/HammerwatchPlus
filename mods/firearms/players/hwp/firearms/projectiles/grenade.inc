<!--
	The thrown grenade, one file per type (grenade_frag, grenade_frag_stun, grenade_incendiary,
	grenade_gas). The arc
	(GroundBouncing, bounces 0) destroys it where it lands: it explodes then, not at ttl.
	Damage and penetration come from the Frag Grenade's binds (fs_frag.sval); the
	elemental penetration from Elemental Shrapnel's custom stat (hwp-shrapnel, 0 without it).
	Each DamagePenetration follows its Damage so it merges into it (Damage.as TryMerge).
-->
%include "players/hwp/firearms/projectiles/shrapnel.inc"
<unit netsync="none">
	<behavior class="NewProjectile">
		<string name="anim">default</string>
		<float name="speed">7</float>
		<int name="ttl">2000</int>
		<int name="penetration">999</int>
		<bool name="penetrate-all">true</bool>
		<int name="bounces">0</int>

		<array name="modifiers">
			<dict>
				<string name="class">Projectile::GroundBouncing</string>
				<int name="period">650</int>
				<int name="height">16</int>
				<int name="bounces">0</int>
				<bool name="hit-target">true</bool>
			</dict>
		</array>

		<array name="destroyed-effects">
%if !GAS
			<dict>
				<string name="class">Explode</string>
				<string name="radius-bind">area-radius</string>
				<int name="min-radius">12</int>
				<float name="dist-scaling">1000</float>
				<array name="effects">
%if FRAG
					<dict>
						<string name="class">Damage</string>
						<string name="physical-bind">grenade-dmg</string>
					</dict>
					<dict>
						<string name="class">DamagePenetration</string>
						<string name="armor-bind">grenade-pen</string>
					</dict>
%endif
%if STUN
					<dict>
						<string name="class">Damage</string>
						<string name="lightning-bind">grenade-dmg</string>
					</dict>
					<dict>
						<string name="class">DamagePenetration</string>
						<string name="lightning-bind">grenade-pen</string>
					</dict>
%endif
%if FIRE
					<dict>
						<string name="class">Damage</string>
						<string name="fire-bind">grenade-dmg</string>
					</dict>
					<dict>
						<string name="class">DamagePenetration</string>
						<string name="fire-bind">grenade-pen</string>
					</dict>
%endif
					%block Shrapnel false
					<!-- the Shrapnel orb's armor break (fs_frag.sval) -->
					<dict>
						<string name="class">ApplyBuff</string>
						<string name="buff-bind">shrapnel-buff</string>
					</dict>
%if STUN
					<dict>
						<bool name="only-actors">true</bool>
					</dict>
					<dict>
						<string name="class">ApplyBuff</string>
						<string name="buff-bind">stun-buff</string>
					</dict>
					<dict>
						<string name="class">ApplyBuff</string>
						<string name="buff-bind">stun-slow</string>
					</dict>
%endif
				</array>
			</dict>
%endif
%if FRAG
			<dict>
				<string name="class">SpawnEffect</string>
				<string name="effect">effects/generic/explosions/bomb_explosion_2.effect?radius=128</string>
			</dict>
			<dict>
				<string name="class">PlaySound</string>
				<string name="sound">event:/sfx/player/classes/rogue/grenade/grenade_explode</string>
			</dict>
%endif
%if STUN
			<dict>
				<string name="class">SpawnEffect</string>
				<string name="effect">effects/generic/explosions/bomb_explosion_2.effect?radius=128&lightning=1</string>
			</dict>
			<!-- the electric flash over the whole radius: Sorcerer's static field, held briefly -->
			<dict>
				<string name="class">SpawnUnit</string>
				<string name="unit">players/hwp/firearms/projectiles/grenade_stun_flash.unit</string>
			</dict>
			<dict>
				<string name="class">SpawnEffect</string>
				<string name="effect">effects/generic/explosions/lightning_explosion_discharge_big.effect</string>
			</dict>
			<dict>
				<string name="class">PlaySound</string>
				<string name="sound">event:/sfx/player/classes/rogue/grenade/grenade_shock</string>
			</dict>
%endif
%if FIRE
			<dict>
				<string name="class">SpawnEffect</string>
				<string name="effect">effects/generic/explosions/fire_explosion_3.effect</string>
			</dict>
			<dict>
				<string name="class">PlaySound</string>
				<string name="sound">event:/sfx/player/classes/rogue/grenade/grenade_incendiary</string>
			</dict>
			<dict>
				<string name="class">SpawnUnit</string>
				<string name="unit">players/hwp/firearms/projectiles/grenade_incendiary_area.unit</string>
			</dict>
%endif
%if GAS
			<dict>
				<string name="class">PlaySound</string>
				<string name="sound">event:/sfx/player/classes/rogue/grenade/grenade_bounce</string>
			</dict>
			<dict>
				<string name="class">SpawnUnit</string>
				<string name="unit">players/hwp/firearms/projectiles/grenade_gas_cloud.unit</string>
			</dict>
%endif
		</array>

		<dict name="effect-params">
			<float name="height">8</float>
		</dict>
	</behavior>

	<scenes start="default">
		<scene name="default">
			<collision static="false">
				<circle radius="5" projectile="true" />
			</collision>
			<effect src="effects/generic/other/bomb.effect" />
		</scene>
	</scenes>
</unit>
