// Firearms Specialist script behaviour that data alone cannot express:
// - Projectile::HWPFirearmsShot (on every gun round): Critical Aim's focus stacks and
//   Headshot's first-hit flag.
// - Modifiers::HWPFirearmsHeadshot / HWPFirearmsExposure: Snipe orb and Critical Aim orb crits.
// - HWPFirearmsThrowMag: Explosive Reload's thrown magazine, one round of damage per round left.
// - Hoarder (Ordinance Hoarder charges) and OverReload (Over-Reload's timing window), ticked
//   by the module for the local player only.
namespace HWP
{
	namespace Firearms
	{
		const string FOCUS = "players/hwp/firearms/stacks_firearms.sval:focus";
		const string BUFFS = "players/hwp/firearms/buffs_firearms.sval:";

		// Set while a Snipe round is in flight and has hit nothing yet; HWPFirearmsHeadshot
		// crits Snipe damage while it is set. Only the local player's rounds set it.
		bool g_headshot = false;

		ActorBuffStacked@ FindStack(PlayerBase@ plr, ActorBuffStackDef@ def)
		{
			if (plr is null || def is null)
				return null;
			auto stacks = plr.m_buffs.m_stacks;
			for (uint i = 0; i < stacks.length(); i++)
			{
				if (stacks[i].m_def is def)
					return stacks[i];
			}
			return null;
		}

		bool HasBuff(Actor@ actor, const string &in name)
		{
			return actor !is null && actor.HasBuff(HashString(BUFFS + name));
		}

		Skills::Skill@ FindSkill(PlayerBase@ plr, uint id)
		{
			for (uint i = 0; i < plr.m_skills.length(); i++)
			{
				if (plr.m_skills[i] !is null && plr.m_skills[i].m_skillId == id)
					return plr.m_skills[i];
			}
			return null;
		}

		// Cooldown state of the two skill families (ActiveSkill starts its cooldown when the
		// cast starts, PlayerSkill when it ends).
		int CooldownLeft(Skills::Skill@ s)
		{
			auto a = cast<Skills::ActiveSkill>(s);
			if (a !is null)
				return a.m_cooldownC;
			auto p = cast<Skills::PlayerSkill>(s);
			return p !is null ? p.m_cooldownC : 0;
		}

		int CooldownFull(Skills::Skill@ s)
		{
			auto a = cast<Skills::ActiveSkill>(s);
			if (a !is null)
				return int(a.m_cooldown * a.m_modCooldownMul);
			auto p = cast<Skills::PlayerSkill>(s);
			return p !is null ? int(p.m_cooldown * p.m_modCooldownMul) : 0;
		}

		bool Casting(Skills::Skill@ s)
		{
			auto a = cast<Skills::ActiveSkill>(s);
			if (a !is null)
				return a.m_castingC > 0;
			auto p = cast<Skills::PlayerSkill>(s);
			return p !is null && p.m_castingT >= 0;
		}

		// Ordinance Hoarder: while the Frag Grenade, the Grenade Launcher or the Rocket Launcher
		// sits ready it banks a charge per cooldown's worth of time, up to the charges stack's
		// max (0 without the passive). When the skill goes on cooldown and a charge is banked,
		// the charge is spent and the cooldown cleared once the cast is over. ids are the
		// skill's alternatives, the first one held counting (alt: the other rifle's launcher).
		class HoardedSkill
		{
			array<uint> m_ids;
			string m_stack;
			int m_readyMs;
			bool m_wasCooling;
			bool m_spend;

			HoardedSkill(const string &in stack, const string &in id, const string &in alt = "")
			{
				m_ids.insertLast(HashString(id));
				if (alt != "")
					m_ids.insertLast(HashString(alt));
				m_stack = stack;
			}

			void Update(PlayerBase@ plr, int ms)
			{
				auto def = ActorBuffStackDef::Get(m_stack);
				Skills::Skill@ skill = null;
				for (uint i = 0; i < m_ids.length() && skill is null; i++)
					@skill = FindSkill(plr, m_ids[i]);
				if (def is null || skill is null)
					return;
				int mx = ClipMax(plr, def);
				int have = plr.GetStacks(def);
				bool cooling = CooldownLeft(skill) > 0;

				if (cooling && !m_wasCooling)
					m_spend = true;
				m_wasCooling = cooling;

				if (m_spend && !Casting(skill))
				{
					m_spend = false;
					if (have > 0)
					{
						skill.ResetCooldown();
						plr.AddStacks(plr, def, -1);
						m_wasCooling = false;
						have--;
						HWP::Log("firearms", "hoarder: spent a charge of " + m_stack + ", " + have + " left");
					}
				}

				if (cooling || have >= mx || mx <= 0)
				{
					m_readyMs = 0;
					return;
				}
				m_readyMs += ms;
				int period = max(1, CooldownFull(skill));
				if (m_readyMs >= period)
				{
					m_readyMs -= period;
					plr.AddStacks(plr, def, 1);
				}
			}
		}

		array<HoardedSkill@> g_hoarded = {
			HoardedSkill("players/hwp/firearms/stacks_firearms.sval:grenade_charges", "hwp_fs_frag"),
			HoardedSkill("players/hwp/firearms/stacks_firearms.sval:gl_charges", "hwp_attack_rifle_gl", "hwp_attack_rifle_gl_epic"),
			HoardedSkill("players/hwp/firearms/stacks_firearms.sval:rocket_charges", "hwp_fs_rpg") };

		// Over-Reload: while a reload runs, a 200 ms window opens at a random point in its
		// second half (drawn as a gold arc on a ring over the player). Two kinds of reload:
		// - the automatic one (the reloading stack): casting Reload inside the window;
		// - a manual Reload cast, up to its castpoint: pressing Reload again inside the window,
		//   which also finishes the cast at once.
		// A perfect reload applies perfect_reload_<level>, which raises the clip max until the
		// clip next runs dry or a reload isn't perfect. It replaces any bonus already held, so
		// the clip never holds more than a perfect reload of an empty clip gives.
		const int OVER_WINDOW = 200;
		const uint RELOAD_ID = HashString("hwp_fs_reload");
		const array<uint> PERFECT = {
			HashString(BUFFS + "perfect_reload_1"), HashString(BUFFS + "perfect_reload_2"),
			HashString(BUFFS + "perfect_reload_3") };
		const array<uint> OVER_MARKERS = {
			HashString(BUFFS + "over_reload_1"), HashString(BUFFS + "over_reload_2"),
			HashString(BUFFS + "over_reload_3") };

		class OverReloadState
		{
			bool m_active;
			int m_total;
			int m_windowStart;
			int m_elapsed;
			bool m_wasCasting;
			bool m_manual;
			bool m_wasDown;
			int m_topUp;

			int Level(PlayerBase@ plr)
			{
				for (int i = 3; i >= 1; i--)
				{
					if (plr.HasBuff(OVER_MARKERS[i - 1]))
						return i;
				}
				return 0;
			}

			void ClearPerfect(PlayerBase@ plr)
			{
				bool removed = false;
				auto buffs = plr.m_buffs.m_buffs;
				for (uint i = 0; i < buffs.length(); i++)
				{
					if (PERFECT.find(buffs[i].m_def.m_pathHash) >= 0)
					{
						buffs[i].Clear();
						buffs.removeAt(i--);
						removed = true;
					}
				}
				if (removed)
					plr.RefreshModifiers();
			}

			bool InWindow() { return (m_active || m_manual) && m_elapsed >= m_windowStart && m_elapsed < m_windowStart + OVER_WINDOW; }

			void PickWindow(int total)
			{
				m_total = max(1, total);
				int half = m_total / 2;
				m_windowStart = half + randi(max(1, m_total - half - OVER_WINDOW));
			}

			// A perfect reload finishes at once: the cast jumps to just short of its castpoint, so
			// it lands next frame. Its cast list (Explosive Reload's throw first) then reads the
			// clip as it was, and the top-up two frames on fills the raised max.
			void Perfect(PlayerBase@ plr, Skills::PlayerSkillDirectional@ dir, int level)
			{
				auto def = LoadActorBuff(BUFFS + "perfect_reload_" + level);
				if (def !is null)
					plr.ApplyBuff(ActorBuff(plr, def, 1.0f, false));
				if (dir !is null && dir.m_castingT >= 0 && dir.m_castingT < dir.m_castpoint - 1)
					dir.m_castingT = dir.m_castpoint - 1;
				m_topUp = 2;
				g_reloadSounds.Perfect(plr);
			}

			// the window is still to come: the lever waits, since a perfect reload replaces it
			bool WindowPending() { return (m_active || m_manual) && m_elapsed < m_windowStart + OVER_WINDOW; }

			bool ReloadDown(PlayerBase@ plr, Skills::Skill@ reload)
			{
				auto p = cast<Player>(plr);
				return p !is null && p.m_targetHelper !is null && reload !is null && p.m_targetHelper.GetSkillInput(reload).Down;
			}

			void Update(PlayerBase@ plr, int ms)
			{
				// the clip's lose-effects remove the bonus when it runs dry (stacks_firearms.sval)
				if (m_topUp > 0 && --m_topUp == 0)
				{
					auto clip = ActorBuffStackDef::Get(CLIP);
					if (clip !is null)
						plr.AddStacks(plr, clip, 999);
				}

				int level = Level(plr);
				auto st = FindStack(plr, ActorBuffStackDef::Get(RELOADING));
				auto reload = FindSkill(plr, RELOAD_ID);
				auto dir = cast<Skills::PlayerSkillDirectional>(reload);
				bool casting = reload !is null && Casting(reload);
				bool wasActive = m_active;
				// the reloading stack outlives the Reload cast's start (it drops at the castpoint):
				// once a cast is under way, its press has been judged
				if (st !is null && st.m_stacks > 0 && level > 0 && !(casting && m_wasCasting))
				{
					int total = Modifiers::lerp(st.m_defMod.m_timerTime, st.GetIntensity());
					if (!m_active || total != m_total)
					{
						m_active = true;
						PickWindow(total);
						HWP::Log("firearms", "over-reload: window " + m_windowStart + "-" + (m_windowStart + OVER_WINDOW)
							+ " of " + m_total + " ms, " + (m_total - st.m_timerTickC) + " ms in");
					}
					m_elapsed = m_total - st.m_timerTickC;
				}
				else
					m_active = false;

				// edges of the held button, not Pressed: gamelab-hands writes the input from its
				// own UpdateFrame, which may run after this one
				bool down = ReloadDown(plr, reload);
				if (casting && !m_wasCasting && level > 0)
				{
					// the stack may already be gone this frame if the cast point is 0: judge by
					// the window as it stood last frame
					bool fromAuto = m_active || wasActive;
					bool hit = m_active ? InWindow() : (wasActive && m_elapsed >= m_windowStart && m_elapsed < m_windowStart + OVER_WINDOW);
					ClearPerfect(plr);
					if (hit)
					{
						Perfect(plr, dir, level);
						HWP::Log("firearms", "over-reload: perfect at " + m_elapsed + "/" + m_total + " ms");
					}
					else if (wasActive)
						HWP::Log("firearms", "over-reload: missed at " + m_elapsed + " ms (window " + m_windowStart + ")");
					m_active = false;

					if (!fromAuto && dir !is null && dir.m_castpoint > 0)
					{
						m_manual = true;
						m_elapsed = 0;
						PickWindow(dir.m_castpoint);
						HWP::Log("firearms", "over-reload: manual window " + m_windowStart + "-" + (m_windowStart + OVER_WINDOW)
							+ " of " + m_total + " ms, " + dir.m_castingT + " ms in");
					}
				}
				else if (m_manual)
				{
					if (!casting || dir is null || dir.m_castingT >= dir.m_castpoint)
						m_manual = false;
					else
					{
						m_elapsed = dir.m_castingT;
						if (down && !m_wasDown)
						{
							if (InWindow())
							{
								Perfect(plr, dir, level);
								HWP::Log("firearms", "over-reload: manual perfect at " + m_elapsed + "/" + m_total + " ms");
							}
							else
								HWP::Log("firearms", "over-reload: manual missed at " + m_elapsed + " ms (window " + m_windowStart + ")");
							m_manual = false;
						}
					}
				}
				m_wasCasting = casting;
				m_wasDown = down;
			}

			void Render(PlayerBase@ plr, int idt, SpriteBatch& sb)
			{
				if (!m_active && !m_manual)
					return;
				vec2 pos = ToScreenspace(plr.m_unit.GetInterpolatedPosition(idt) + vec3(0, -26, 0)) / g_gameMode.m_wndScale;
				const float full = 2 * PI;
				const float top = -PI / 2;
				sb.DrawCircle(pos, 9, vec4(0, 0, 0, 0.6f), 24, 3);
				sb.DrawCircleArc(pos, 9, top, full * m_elapsed / float(m_total), 0, vec4(0.85f, 0.85f, 0.9f, 0.9f), 24, 2);
				vec4 gold = InWindow() ? vec4(1, 1, 0.6f, 1) : vec4(0.95f, 0.75f, 0.2f, 1);
				sb.DrawCircleArc(pos, 9, top + full * m_windowStart / float(m_total), full * OVER_WINDOW / float(m_total), 0, gold, 24, 3);
			}
		}

		OverReloadState g_overReload;

		// Reload sounds, played at the player: the unlock as the mag comes out, the lever on
		// 250 ms before the reload finishes, or the lever off at once on a perfect reload (and
		// then no lever on). A reload is the reloading stack or a Reload cast short of its castpoint.
		const int LEVER_LEAD = 250;
		const array<string> RELOAD_SNDS = {
			"event:/sfx/doodads/doors/unlock", "event:/sfx/doodads/buttons/lever_on",
			"event:/sfx/doodads/buttons/lever_off" };
		const uint SND_UNLOCK = 0;
		const uint SND_LEVER_ON = 1;
		const uint SND_LEVER_OFF = 2;

		class ReloadSounds
		{
			array<SoundEvent@> m_snd = { null, null, null };
			bool m_on;
			bool m_lever;
			int m_left;
			int m_clipAtStart;
			int m_checkFill;

			void Play(PlayerBase@ plr, uint i)
			{
				if (m_snd[i] is null)
					@m_snd[i] = Resources::GetSoundEvent(RELOAD_SNDS[i]);
				if (m_snd[i] !is null)
					PlaySound3D(m_snd[i], plr.m_unit.GetPosition());
				HWP::Log("firearms", "reload sound: " + RELOAD_SNDS[i] + (m_snd[i] is null ? " (missing)" : ""));
			}

			int Clip(PlayerBase@ plr)
			{
				auto st = FindStack(plr, ActorBuffStackDef::Get(CLIP));
				return st is null ? 0 : st.m_stacks;
			}

			void Perfect(PlayerBase@ plr)
			{
				Play(plr, SND_LEVER_OFF);
				m_lever = true;
			}

			void Update(PlayerBase@ plr)
			{
				auto st = FindStack(plr, ActorBuffStackDef::Get(RELOADING));
				auto reload = FindSkill(plr, RELOAD_ID);
				auto dir = cast<Skills::PlayerSkillDirectional>(reload);
				bool castOn = dir !is null && Casting(reload) && dir.m_castingT < dir.m_castpoint;
				bool autoOn = st !is null && st.m_stacks > 0;
				bool on = castOn || autoOn;
				int left = castOn ? dir.m_castpoint - dir.m_castingT : (autoOn ? st.m_timerTickC : 0);

				if (on && !m_on)
				{
					Play(plr, SND_UNLOCK);
					m_lever = false;
					m_clipAtStart = Clip(plr);
					m_checkFill = 0;
				}
				else if (on && left > m_left + 50)
					m_lever = false;   // the reload started over (a dodge)

				if (on && !m_lever && left <= LEVER_LEAD && !g_overReload.WindowPending())
				{
					Play(plr, SND_LEVER_ON);
					m_lever = true;
				}

				// ended early with the lever still to come (Dodge Reload Skip): the lever once the
				// clip has filled, which may land a frame or two after the stack drops
				if (!on && m_on && !m_lever)
					m_checkFill = 3;
				if (m_checkFill > 0)
				{
					if (on)
						m_checkFill = 0;
					else if (Clip(plr) > m_clipAtStart)
					{
						Play(plr, SND_LEVER_ON);
						m_lever = true;
						m_checkFill = 0;
					}
					else
						m_checkFill--;
				}
				m_on = on;
				m_left = left;
			}
		}

		ReloadSounds g_reloadSounds;

		// Adrenaline: the heal the last hurt bought, landed next frame (HWPFirearmsAdrenaline)
		const string ADRENALINE = "players/hwp/firearms/stacks_firearms.sval:adrenaline";
		int g_adrenalineHeal = 0;

		// The Glocks' raised arm: after a pistol shot the shot's upper-body animation is
		// played again on the skill layer (1) from its start and frozen there (speed FROZEN,
		// AnimationLoopType::Hold; PlayerBase.SetUnitScene's call otherwise). The wand shot's
		// first frame has the arm out and its last is the rest pose, so the arm stays up
		// between shots instead of dropping to idle. It lets go after HOLD_MS without a pistol
		// shot, or at once when the clip reloads or another skill (a dodge, Reload, a spell)
		// starts: the animation then runs on from the frozen frame at full speed, unheld, so
		// the arm comes down the shot's own way and the layer is free.
		const int HOLD_MS = 2000;
		const float FROZEN = 0.0001f;
		const array<uint> PISTOLS = { HashString("hwp_attack_glock"), HashString("hwp_attack_glock_off") };

		class AimHold
		{
			int m_leftMs;
			bool m_holding;
			bool m_wasShooting;
			PlayerAnimationSetEntry@ m_anim;

			void Play(PlayerBase@ plr, bool resetTime, AnimationLoopType loop, float speed)
			{
				if (m_anim is null)
					return;
				if (m_anim.m_skel3dset !is null)
					plr.m_effectParams.PlayAnimation3D(m_anim.m_anim3d, m_anim.m_skel3dset, plr.m_unit, 1, m_anim.m_priority, resetTime, loop, speed);
				else
					plr.m_effectParams.PlayAnimation3D(m_anim.m_anim3d, plr.m_skeleton, plr.m_unit, 1, m_anim.m_priority, resetTime, loop, speed);
			}

			void Release(PlayerBase@ plr, const string &in why)
			{
				if (m_holding)
				{
					Play(plr, false, AnimationLoopType::None, 1.0f);
					HWP::Log("firearms", "pistol arm: lowered (" + why + ")");
				}
				m_holding = false;
				m_leftMs = 0;
			}

			void Update(PlayerBase@ plr, int ms)
			{
				Skills::PlayerSkill@ shooting = null;
				string other = "";
				for (uint i = 0; i < plr.m_skills.length(); i++)
				{
					auto skill = cast<Skills::PlayerSkill>(plr.m_skills[i]);
					auto active = cast<Skills::ActiveSkill>(plr.m_skills[i]);
					bool on = (skill !is null && skill.IsActive()) || (active !is null && active.IsActive());
					if (!on)
						continue;
					if (skill !is null && PISTOLS.find(skill.m_skillId) >= 0)
						@shooting = skill;
					else if (other == "")
						other = "skill " + plr.m_skills[i].m_skillId;
				}
				auto reload = ActorBuffStackDef::Get(RELOADING);
				if (reload !is null && plr.GetStacks(reload) > 0)
					other = "reloading";

				if (shooting !is null)
				{
					if (plr.m_animSet !is null)
						@m_anim = plr.m_animSet.GetAnimation(shooting.m_animation);
					m_leftMs = HOLD_MS;
					m_holding = false;
					m_wasShooting = true;
					return;
				}
				if (other != "")
				{
					Release(plr, other);
					m_wasShooting = false;
					return;
				}
				if (m_wasShooting && m_leftMs > 0)
				{
					// the shot just ended: back to its first frame, frozen
					Play(plr, true, AnimationLoopType::Hold, FROZEN);
					if (!m_holding)
						HWP::Log("firearms", "pistol arm: held");
					m_holding = true;
					m_wasShooting = false;
				}
				if (!m_holding)
					return;
				m_leftMs -= ms;
				if (m_leftMs <= 0)
					Release(plr, HOLD_MS + " ms without a shot");
			}
		}
		AimHold g_aimHold;

		void UpdateCombat(int ms)
		{
			auto plr = cast<PlayerBase>(GetLocalPlayer());
			if (plr is null || !IsFirearms(GetLocalPlayerRecord()))
				return;
			if (g_adrenalineHeal > 0)
			{
				int healed = plr.Heal(g_adrenalineHeal, false);
				HWP::Log("firearms", "adrenaline: healed " + healed + " of " + g_adrenalineHeal);
				g_adrenalineHeal = 0;
			}
			for (uint i = 0; i < g_hoarded.length(); i++)
				g_hoarded[i].Update(plr, ms);
			g_overReload.Update(plr, ms);
			g_reloadSounds.Update(plr);
			g_aimHold.Update(plr, ms);
		}

		void RenderCombat(int idt, SpriteBatch& sb)
		{
			auto plr = cast<PlayerBase>(GetLocalPlayer());
			if (plr !is null)
				g_overReload.Render(plr, idt, sb);
		}

		// Critical Aim's focus: +1 per gun round that hits an actor, all lost when a round
		// misses: it runs out of range or hits a wall or other non-actor (HWPFirearmsShot).
		// The stack's max is 0 (so nothing happens) without the passive.
		void Focus(Actor@ owner, bool hit)
		{
			auto plr = cast<PlayerBase>(owner);
			auto def = ActorBuffStackDef::Get(FOCUS);
			if (plr is null || def is null || plr !is cast<PlayerBase>(GetLocalPlayer()))
				return;
			if (hit)
			{
				if (ClipMax(plr, def) > 0)
					plr.AddStacks(plr, def, 1);
			}
			else
			{
				int have = plr.GetStacks(def);
				if (have > 0)
					plr.AddStacks(plr, def, -have);
			}
		}
	}
}

namespace Projectile
{
	// On every gun round (bullet_snipe, glock_round*, rifle_round*). headshot=true marks
	// Snipe's round for HWPFirearmsHeadshot.
	class HWPFirearmsShot : ProjectileModifier
	{
		Actor@ m_owner;
		bool m_headshot;
		bool m_local;
		bool m_hit;

		HWPFirearmsShot(UnitPtr unit, SValue& params) {}

		void Initialize(NewProjectile@ behavior, SValue& params, Actor@ owner, ProjectileTarget@ target, uint weapon) override
		{
			@m_owner = owner;
			m_hit = false;
			m_local = !behavior.m_husk;
			m_headshot = m_local && GetParamBool(behavior.m_unit, params, "headshot", false, false);
			if (m_headshot)
				HWP::Firearms::g_headshot = true;
		}

		void OnHit(UnitPtr unit, vec2 pos) override
		{
			if (m_hit || cast<Actor>(unit.GetScriptBehavior()) is null)
				return;
			m_hit = true;
			if (m_headshot)
				HWP::Firearms::g_headshot = false;
			if (m_local)
				HWP::Firearms::Focus(m_owner, true);
		}

		// A miss is the range running out (OnMiss) or a wall (OnCollide: a hit on a unit that
		// isn't an actor). A round destroyed any other way, such as blocked by a shield
		// (NewProjectile.HitUnit destroys it without OnHit) or unloaded, neither gains nor loses.
		void Missed()
		{
			if (m_local && !m_hit)
				HWP::Firearms::Focus(m_owner, false);
			m_hit = true;
		}

		void OnMiss(vec2 pos) override { Missed(); }
		void OnCollide(UnitPtr unit, vec2 pos) override { Missed(); }

		// No m_hit here: Destroy() runs OnDestroyed before OnMiss on a range-out
		// (NewProjectile.Update: m_unit.Destroy(), then the OnMiss loop).
		void OnDestroyed() override
		{
			if (m_headshot)
				HWP::Firearms::g_headshot = false;
		}
	}
}

namespace Modifiers
{
	// Headshot (Snipe orb): the first target a Snipe round hits takes a critical hit.
	class HWPFirearmsHeadshot : Modifier
	{
		uint m_skillId;

		HWPFirearmsHeadshot(UnitPtr unit, SValue& params)
		{
			m_skillId = HashString(GetParamString(unit, params, "skill-id", true, ""));
		}

		ModDynamism HasCrit() override { return ModDynamism::Dynamic; }
		int Crit(PlayerBase@ player, Actor@ attacked, Skills::Skill@ skill, float intensity) override
		{
			return (skill !is null && skill.m_skillId == m_skillId && HWP::Firearms::g_headshot) ? 1 : 0;
		}
	}

	// Elemental Exposure (Critical Aim orb): one crit roll at chance per element (fire, ice,
	// lightning, poison) afflicting the target.
	class HWPFirearmsExposure : Modifier
	{
		vec2 m_chance;

		HWPFirearmsExposure(UnitPtr unit, SValue& params)
		{
			m_chance = GetParamVec2(unit, params, "chance", true, 0);
		}

		ModDynamism HasCrit() override { return ModDynamism::Dynamic; }
		int Crit(PlayerBase@ player, Actor@ attacked, Skills::Skill@ skill, float intensity) override
		{
			if (attacked is null)
				return 0;
			auto buffs = attacked.GetBuffList();
			if (buffs is null)
				return 0;
			float chance = lerp(m_chance, intensity);
			array<int> pools = { buffs.m_fireDmgPool, buffs.m_iceDmgPool, buffs.m_lightningDmgPool, buffs.m_poisonDmgPool };
			for (uint i = 0; i < pools.length(); i++)
			{
				if (pools[i] > 0 && roll_chance(player, chance))
					return 1;
			}
			return 0;
		}
	}

	// A crit roll at chance per stack of buff held: Critical Focus (adrenaline) and Extended
	// Crit Chance (the clip's rounds left).
	class HWPFirearmsStackCrit : Modifier
	{
		vec2 m_chance;
		string m_buff;

		HWPFirearmsStackCrit(UnitPtr unit, SValue& params)
		{
			m_chance = GetParamVec2(unit, params, "chance", true, 0);
			m_buff = GetParamString(unit, params, "buff", true);
		}

		ModDynamism HasCrit() override { return ModDynamism::Dynamic; }
		int Crit(PlayerBase@ player, Actor@ attacked, Skills::Skill@ skill, float intensity) override
		{
			auto def = ActorBuffStackDef::Get(m_buff);
			if (player is null || def is null)
				return 0;
			int stacks = player.GetStacks(def);
			return (stacks > 0 && roll_chance(player, lerp(m_chance, intensity) * stacks)) ? 1 : 0;
		}
	}
}

// Adrenaline's effects on the player (assault_adrenaline.sval), local only:
// - heal (the hurt trigger): spend every stack for heal of max health each. The trigger runs
//   before the damage, so the heal waits a frame (g_adrenalineHeal, UpdateCombat).
// - epipen (EpiPen's dash trigger): with no stacks, gain epipen stacks.
class HWPFirearmsAdrenaline : IEffect
{
	float m_heal;
	int m_epipen;

	HWPFirearmsAdrenaline(UnitPtr unit, SValue& params)
	{
		m_heal = GetParamFloat(unit, params, "heal", false, 0);
		m_epipen = GetParamInt(unit, params, "epipen", false, 0);
	}

	CanEvade IsEvadable(Actor@ attacker) { return CanEvade::Neither; }
	void SetWeaponInformation(uint weapon) {}

	bool CanApply(Actor@ owner, UnitPtr target, vec2 pos, vec2 dir, float intensity) override
	{
		return cast<PlayerBase>(target.GetScriptBehavior()) !is null;
	}

	bool Apply(Actor@ owner, UnitPtr target, vec2 pos, vec2 dir, float intensity, bool husk)
	{
		auto plr = cast<PlayerBase>(target.GetScriptBehavior());
		auto def = ActorBuffStackDef::Get(HWP::Firearms::ADRENALINE);
		if (husk || plr is null || def is null || plr !is cast<PlayerBase>(GetLocalPlayer()))
			return false;
		int stacks = plr.GetStacks(def);
		if (m_epipen > 0)
		{
			if (stacks > 0)
				return false;
			plr.AddStacks(plr, def, m_epipen);
			HWP::Log("firearms", "adrenaline: epipen, " + plr.GetStacks(def) + " stacks");
			return true;
		}
		if (stacks <= 0 || m_heal <= 0)
			return false;
		int amount = max(1, int(stacks * m_heal * plr.GetMaxHp() + 0.5f));
		HWP::Firearms::g_adrenalineHeal += amount;
		plr.AddStacks(plr, def, -stacks);
		HWP::Log("firearms", "adrenaline: hurt, " + stacks + " stacks spent for " + amount + " health");
		return true;
	}
}

// Explosive Reload: throws the magazine before the refill, as a projectile whose intensity
// is the rounds that were left (reload_mag.unit: dmg per round). Dual Glocks throw the two
// magazines one after the other: the cast throws the main hand's half of the rounds and
// keeps the off hand's for the "second" throw, a later timeline entry (fs_reload.sval).
// Does nothing without the orb (dmg 0) or with an empty clip.
namespace HWP
{
	namespace Firearms
	{
		// owner unit id -> rounds in the off-hand magazine still to be thrown
		dictionary g_secondMag;
		const float MAG_ANGLE = 8 * PI / 180.0;
	}
}

class HWPFirearmsThrowMag : ShootProjectile
{
	int m_dmg;
	bool m_second;

	HWPFirearmsThrowMag(UnitPtr unit, SValue& params)
	{
		super(unit, params);
		m_dmg = GetParamInt(unit, params, "dmg", false, 0);  // mag-dmg is an int bind
		m_second = GetParamBool(unit, params, "second", false, false);
	}

	bool Skip(SValueBuilder@ builder)
	{
		builder.PushArray();
		builder.PopArray();
		return false;
	}

	bool DoAction(SValueBuilder@ builder, Actor@ owner, Actor@ target, vec2 pos, vec2 dir, float intensity) override
	{
		auto plr = cast<PlayerBase>(owner);
		auto clip = ActorBuffStackDef::Get(HWP::Firearms::CLIP);
		if (plr is null || clip is null || m_dmg <= 0)
			return Skip(builder);
		string key = "" + owner.m_unit.GetId();
		m_projectiles = 1;
		m_spread = 0;

		if (m_second)
		{
			int left = 0;
			if (!HWP::Firearms::g_secondMag.get(key, left) || left <= 0)
				return Skip(builder);
			HWP::Firearms::g_secondMag.delete(key);
			HWP::Log("firearms", "explosive reload: second magazine, " + left + " rounds (scene " + g_scene.GetTime() + " ms)");
			return ShootProjectile::DoAction(builder, owner, target, pos, addrot(dir, HWP::Firearms::MAG_ANGLE), intensity * left);
		}

		HWP::Firearms::g_secondMag.delete(key);
		int rounds = plr.GetStacks(clip);
		if (rounds <= 0)
			return Skip(builder);
		bool dual = HWP::Firearms::HasBuff(owner, "glock_main") && HWP::Firearms::HasBuff(owner, "glock_off");
		HWP::Log("firearms", "explosive reload: " + rounds + " rounds at " + m_dmg + (dual ? ", two magazines" : "") + " (scene " + g_scene.GetTime() + " ms)");
		if (!dual)
			return ShootProjectile::DoAction(builder, owner, target, pos, dir, intensity * rounds);
		int second = rounds / 2;
		if (second > 0)
			HWP::Firearms::g_secondMag.set(key, second);
		return ShootProjectile::DoAction(builder, owner, target, pos, addrot(dir, -HWP::Firearms::MAG_ANGLE), intensity * (rounds - second));
	}
}

// Rocket Jump (demo_rpg.sval orb, jump 1): a rocket blast whose radius reaches its owner
// dashes them away from its centre with their own dash (the first Skills::Charge, started
// directly, so it costs no dash charge) and gives rocket_jump, 100% evade for the flight
// (as Rogue's flurry_of_blades). The rocket never hurts its owner (Explode hit-self).
class HWPFirearmsRocketJump : IEffect
{
	int m_jump;
	int m_radius;

	HWPFirearmsRocketJump(UnitPtr unit, SValue& params)
	{
		m_jump = GetParamInt(unit, params, "jump", false, 0);
		m_radius = GetParamInt(unit, params, "radius", false, 0);
	}

	CanEvade IsEvadable(Actor@ attacker) { return CanEvade::Neither; }
	void SetWeaponInformation(uint weapon) {}
	bool CanApply(Actor@ owner, UnitPtr target, vec2 pos, vec2 dir, float intensity) override { return true; }

	bool Apply(Actor@ owner, UnitPtr target, vec2 pos, vec2 dir, float intensity, bool husk)
	{
		auto plr = cast<Player>(owner);
		if (husk || m_jump <= 0 || plr is null || plr.IsDead())
			return false;
		vec2 at = xy(plr.m_unit.GetPosition());
		float dist = length(at - pos);
		if (dist > m_radius)
			return false;
		vec2 away = dist > 1 ? (at - pos) / dist : plr.GetDirection() * -1.0f;

		auto buff = LoadActorBuff(HWP::Firearms::BUFFS + "rocket_jump");
		if (buff !is null)
			plr.ApplyBuff(ActorBuff(plr, buff, 1.0f, false));
		for (uint i = 0; i < plr.m_skills.length(); i++)
		{
			auto dash = cast<Skills::Charge>(plr.m_skills[i]);
			if (dash is null)
				continue;
			dash.NetDoActivate(null, away);
			dash.m_holding = false;
			break;
		}
		HWP::Log("firearms", "rocket jump: " + int(dist) + " of " + m_radius + " from the blast, away "
			+ int(away.x * 100) + "," + int(away.y * 100));
		return true;
	}
}
