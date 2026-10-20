<!--
	Explosive Reload's thrown magazine (fs_reload.sval, HWPFirearmsThrowMag), one file per
	gun: reload_mag_rifle.unit, and reload_mag_pistol.unit (%define PISTOL), the smaller mag
	thrown by a Glock in either hand. Only the look differs (mags.png,
	tools/make_mag_art.py); the blast is the same. It is thrown
	with the rounds left as its intensity, so the blast deals mag-dmg per round
	(Damage.as: damage times intensity). Thrown along the aim it lands 100 out, the point
	GroundBouncing hit-target flies to for a direction (IProjectile.as GetTargetPos). It
	carries no shrapnel: elemental penetration scales with intensity too and would multiply
	by the round count.
-->
<unit netsync="none">
	<behavior class="NewProjectile">
		<string name="anim">default</string>
		<float name="speed">6</float>
		<int name="ttl">2000</int>
		<int name="penetration">999</int>
		<bool name="penetrate-all">true</bool>
		<int name="bounces">0</int>

		<array name="modifiers">
			<dict>
				<string name="class">Projectile::GroundBouncing</string>
				<int name="period">500</int>
				<int name="height">12</int>
				<int name="bounces">0</int>
				<bool name="hit-target">true</bool>
			</dict>
		</array>

		<array name="destroyed-effects">
			<dict>
				<string name="class">Explode</string>
				<int name="radius">48</int>
				<int name="min-radius">12</int>
				<float name="dist-scaling">1000</float>
				<array name="effects">
					<dict>
						<string name="class">Damage</string>
						<string name="physical-bind">mag-dmg</string>
					</dict>
				</array>
			</dict>
			<dict>
				<string name="class">SpawnEffect</string>
				<string name="effect">effects/generic/explosions/bomb_explosion_1.effect?radius=48</string>
			</dict>
			<dict>
				<string name="class">PlaySound</string>
				<string name="sound">event:/sfx/player/classes/rogue/grenade/grenade_explode</string>
			</dict>
		</array>

		<dict name="effect-params">
			<float name="height">8</float>
		</dict>
	</behavior>

	<scenes start="default">
		<scene name="default">
			<collision static="false">
				<circle radius="4" projectile="true" />
			</collision>
%if PISTOL
			<scene src="special/shadow.unit:5" />
			<effect src="./mag_pistol.effect" />
%else
			<scene src="special/shadow.unit:7" />
			<effect src="./mag_rifle.effect" />
%endif
		</scene>
	</scenes>
</unit>
