<!--
	The Rocket Launcher's missiles, one file per type (rocket.unit, rocket_fatboy.unit,
	rocket_magic.unit, rocket_quad.unit; demo_rpg.sval picks one with proj-unit). It explodes
	on the first hit and where its range runs out alike. The damage is rocket-dmg; an orb's
	share of it is either the skill's damage-mul (Quad, Magic Missile's ice) or a mod dict's
	intensity-mul ahead of the extra damage (Fat Boy's poison), so the shrapnel penetration
	before it is not scaled.
-->
%include "players/hwp/firearms/projectiles/shrapnel.inc"
%defblock Boom
			<dict>
				<string name="class">Explode</string>
%if QUAD
				<string name="radius-bind">quad-radius</string>
%else
				<string name="radius-bind">area-radius</string>
%endif
				<int name="min-radius">12</int>
				<float name="dist-scaling">1000</float>
				<array name="effects">
%if MAGIC
					<dict>
						<string name="class">Damage</string>
						<string name="ice-bind">rocket-dmg</string>
					</dict>
%else
					<dict>
						<string name="class">Damage</string>
						<string name="fire-bind">rocket-dmg</string>
					</dict>
%endif
					%block Shrapnel false
%if FATBOY
					<dict>
						<string name="class">ApplyBuff</string>
						<string name="buff-bind">fatboy-blind</string>
					</dict>
					<dict>
						<string name="intensity-mul-bind">fatboy-poison</string>
					</dict>
					<dict>
						<string name="class">Damage</string>
						<string name="poison-bind">rocket-dmg</string>
					</dict>
%endif
				</array>
			</dict>
			<!-- Rocket Jump (demo_rpg.sval orb): the blast dashes its owner away (Combat.as) -->
			<dict>
				<string name="class">HWPFirearmsRocketJump</string>
				<string name="jump-bind">rocket-jump</string>
%if QUAD
				<string name="radius-bind">quad-radius</string>
%else
				<string name="radius-bind">area-radius</string>
%endif
			</dict>
%if FATBOY
			<dict>
				<string name="class">SpawnEffect</string>
				<string name="effect">effects/generic/explosions/bomb_explosion_2.effect?radius=96</string>
			</dict>
			<dict>
				<string name="class">SpawnEffect</string>
				<string name="effect">effects/generic/explosions/explosion_poison_1.effect</string>
			</dict>
			<dict>
				<string name="class">PlaySound</string>
				<string name="sound">event:/sfx/player/attacks/twohanded/fire_blast</string>
			</dict>
%endif
%if MAGIC
			<dict>
				<string name="class">SpawnEffect</string>
				<string name="effect">effects/generic/explosions/ice_explosion_2.effect</string>
			</dict>
			<!-- the fire comes a moment after the ice -->
			<dict>
				<string name="class">SpawnUnit</string>
				<string name="unit">players/hwp/firearms/projectiles/rocket_magic_burn.unit</string>
			</dict>
			<dict>
				<string name="class">PlaySound</string>
				<string name="sound">event:/sfx/player/classes/wizard/fire_ball/fire_ball_explode</string>
			</dict>
%endif
%if ROCKET
			<dict>
				<string name="class">SpawnEffect</string>
				<string name="effect">effects/generic/explosions/fire_explosion_3.effect</string>
			</dict>
			<dict>
				<string name="class">PlaySound</string>
				<string name="sound">event:/sfx/player/classes/wizard/fire_ball/fire_ball_explode</string>
			</dict>
%endif
%if QUAD
			<dict>
				<string name="class">SpawnEffect</string>
				<string name="effect">effects/generic/explosions/fire_explosion_1.effect</string>
			</dict>
			<dict>
				<string name="class">PlaySound</string>
				<string name="sound">event:/sfx/player/classes/wizard/fire_ball/fire_ball_explode</string>
			</dict>
%endif
%endblock
<unit netsync="none">
	<behavior class="NewProjectile">
		<string name="anim">default</string>
%if FATBOY
		<float name="speed">6</float>
		<int name="ttl">1400</int>
%endif
%if MAGIC
		<float name="speed">12</float>
		<int name="ttl">690</int>
%endif
%if ROCKET
		<float name="speed">11</float>
		<int name="ttl">750</int>
%endif
%if QUAD
		<float name="speed">13</float>
		<int name="ttl">640</int>
%endif
		<int name="penetration">0</int>
		<bool name="bounce-on-collide">false</bool>

		<array name="hit-effects">
			%block Boom
		</array>

		<array name="miss-effects">
			%block Boom
		</array>

		<dict name="effect-params">
			<float name="height">8</float>
		</dict>
	</behavior>

	<scenes start="default">
		<scene name="default">
			<collision static="false">
%if FATBOY
				<circle radius="9" projectile="true" />
%else
				<circle radius="6" projectile="true" />
%endif
			</collision>
%if MAGIC
			<effect src="players/hwp/firearms/projectiles/missile_magic.effect" />
%endif
%if FATBOY
			<effect src="players/hwp/firearms/projectiles/missile_fatboy.effect" />
%endif
%if QUAD
			<effect src="players/hwp/firearms/projectiles/missile_quad.effect" />
%endif
%if ROCKET
			<effect src="players/hwp/firearms/projectiles/missile_rocket.effect" />
%endif
		</scene>
	</scenes>
</unit>
