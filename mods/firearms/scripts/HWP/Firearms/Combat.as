// Firearms Specialist script behaviour that data alone cannot express:
// - Projectile::HWPFirearmsShot (on every gun round): Critical Aim's focus stacks and
//   Headshot's first-hit flag.
// - Modifiers::HWPFirearmsHeadshot / HWPFirearmsExposure: Snipe orb and Critical Aim orb crits.
// - HWPFirearmsThrowMag: Explosive Reload's thrown magazine, one round of damage per round left.
// - HWPFirearmsReload: the Reload skill, a cast as long as its recharge that a dodge cancels.
//   It shows the automatic reload's icon sweep while it casts (the reload_cast stack).
// - HWPFirearmsGun: the guns' attacks; the empty-clip "cant" line only on a fresh click.
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
		// g_headshotEnd: the round was destroyed before it hit anything; g_headshot is
		// cleared on the next frame, not at once, because a round that stops at its first
		// target is destroyed before that hit's damage is dealt (NewProjectile.OnHit).
		bool g_headshot = false;
		bool g_headshotEnd = false;

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
			// for the HUD (ChargeHUD.as): the skill held, and how far the next charge has
			// banked (0..1), or -1 while none banks (cooling, full, or no Hoarder)
			uint m_skillId;
			float m_progress = -1;

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
				m_progress = -1;
				if (def is null || skill is null)
					return;
				m_skillId = skill.m_skillId;
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

				Show(plr, skill, have, mx);
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
					have++;
				}
				if (have < mx)
					m_progress = m_readyMs / float(period);
				Show(plr, skill, have, mx);
			}

			// the icon (ID_shown): every use ready, the stored charges and the skill itself
			// when it is off cooldown; none without the passive (mx 0)
			void Show(PlayerBase@ plr, Skills::Skill@ skill, int have, int mx)
			{
				auto shown = ActorBuffStackDef::Get(m_stack + "_shown");
				if (shown is null)
					return;
				int total = mx <= 0 ? 0 : have + (CooldownLeft(skill) > 0 ? 0 : 1);
				int now = plr.GetStacks(shown);
				if (total != now)
					plr.AddStacks(plr, shown, total - now);
			}
		}

		array<HoardedSkill@> g_hoarded = {
			HoardedSkill("players/hwp/firearms/stacks_firearms.sval:grenade_charges", "hwp_fs_frag"),
			HoardedSkill("players/hwp/firearms/stacks_firearms.sval:gl_charges", "hwp_attack_rifle_gl", "hwp_attack_rifle_gl_epic"),
			HoardedSkill("players/hwp/firearms/stacks_firearms.sval:rocket_charges", "hwp_fs_rpg") };

		// The reload bar: every reload (the automatic one, the reloading stack, and a manual
		// Reload cast up to its castpoint) shows a white bar filling just above the HUD's health
		// bar. With Over-Reload a 200 ms gold window sits at a random point in its second half.
		// One try a reload: press Reload, or left click in the bar's second half (clicks still
		// held from the shooting don't count), while the bar is in the gold. A hit finishes the
		// reload at once; a miss turns the bar's white red until the reload ends, and an
		// automatic reload goes on.
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
			bool m_active;        // the automatic reload runs
			bool m_manual;        // a manual Reload cast runs
			int m_total = 1;
			int m_windowStart = -1; // -1: no gold window (Over-Reload not learned)
			int m_elapsed;
			bool m_wasCasting;
			bool m_wasDown;
			bool m_wasFire;
			int m_topUp;
			// this automatic reload's one try has been judged: no Reload cast
			// (HWPFirearmsReload.CanActivate) until the reloading stack is gone
			bool m_autoTried;
			bool m_manualTried;
			bool m_missed;        // the try missed: the bar's white is red
			bool m_perfect;       // the try landed
			int m_hits;           // tries here, for `hwp firearms reload`
			int m_misses;
			int m_bars;           // reload bars shown

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
				auto@ buffs = plr.m_buffs.m_buffs; // a handle: plain auto copies the array
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

			bool InWindow() { return (m_active || m_manual) && m_windowStart >= 0 && m_elapsed >= m_windowStart && m_elapsed < m_windowStart + OVER_WINDOW; }

			// a new bar; the gold window only with the orb
			void Start(int total, bool gold)
			{
				m_total = max(1, total);
				m_missed = false;
				m_perfect = false;
				m_bars++;
				int half = m_total / 2;
				m_windowStart = gold ? half + randi(max(1, m_total - half - OVER_WINDOW)) : -1;
			}

			// A perfect reload finishes at once. A Reload cast jumps to just short of its
			// castpoint, so it lands next frame: its cast list (Explosive Reload's throw first)
			// then reads the clip as it was. Without a cast (a left click during the automatic
			// reload) the reloading stack is ended, and its lose-effects refill the clip. The
			// top-up two frames on fills the raised max.
			void Perfect(PlayerBase@ plr, Skills::PlayerSkillDirectional@ dir, int level)
			{
				auto def = LoadActorBuff(BUFFS + "perfect_reload_" + level);
				if (def !is null)
					plr.ApplyBuff(ActorBuff(plr, def, 1.0f, false));
				if (dir is null)
				{
					auto reloading = ActorBuffStackDef::Get(RELOADING);
					if (reloading !is null)
						plr.AddStacks(plr, reloading, -1);
				}
				else if (dir.m_castingT >= 0 && dir.m_castingT < dir.m_castpoint - 1)
					dir.m_castingT = dir.m_castpoint - 1;
				m_topUp = 2;
				m_perfect = true;
				m_hits++;
				g_reloadSounds.Perfect(plr);
			}

			void Missed()
			{
				m_missed = true;
				m_misses++;
			}

			// the window is still to come: the lever waits, since a perfect reload replaces it
			bool WindowPending() { return (m_active || m_manual) && m_windowStart >= 0 && !m_missed && !m_perfect && m_elapsed < m_windowStart + OVER_WINDOW; }

			bool ReloadDown(PlayerBase@ plr, Skills::Skill@ reload)
			{
				auto p = cast<Player>(plr);
				return p !is null && p.m_targetHelper !is null && reload !is null && p.m_targetHelper.GetSkillInput(reload).Down;
			}

			// the main attack's button (left click)
			bool FireDown(PlayerBase@ plr)
			{
				auto p = cast<Player>(plr);
				if (p is null || p.m_targetHelper is null)
					return false;
				for (uint i = 0; i < plr.m_skills.length(); i++)
				{
					auto s = plr.m_skills[i];
					if (s !is null && s.m_type == PlayerSkillType::MainHand)
						return p.m_targetHelper.GetSkillInput(s).Down;
				}
				return false;
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
				bool autoRuns = st !is null && st.m_stacks > 0;
				if (!autoRuns)
					m_autoTried = false;
				if (autoRuns && !m_manual)
				{
					int total = Modifiers::lerp(st.m_defMod.m_timerTime, st.GetIntensity());
					if (!m_active || total != m_total)
					{
						m_active = true;
						Start(total, level > 0);
						if (level > 0)
							HWP::Log("firearms", "over-reload: window " + m_windowStart + "-" + (m_windowStart + OVER_WINDOW)
								+ " of " + m_total + " ms, " + (m_total - st.m_timerTickC) + " ms in");
					}
					m_elapsed = m_total - st.m_timerTickC;
				}
				else
					m_active = false;

				// edges of the held buttons, not Pressed: gamelab-hands writes the input from its
				// own UpdateFrame, which may run after this one
				bool down = ReloadDown(plr, reload);
				bool fire = FireDown(plr);
				bool click = fire && !m_wasFire;
				if (casting && !m_wasCasting)
				{
					if (m_active || wasActive)
					{
						// a Reload cast during the automatic reload is Over-Reload's try (CanActivate
						// allows no other). The stack may already be gone this frame if the cast
						// point is 0: judge by the window as it stood last frame
						bool hit = m_windowStart >= 0 && m_elapsed >= m_windowStart && m_elapsed < m_windowStart + OVER_WINDOW;
						ClearPerfect(plr);
						if (hit)
						{
							Perfect(plr, dir, level);
							HWP::Log("firearms", "over-reload: perfect at " + m_elapsed + "/" + m_total + " ms");
						}
						else
						{
							Missed();
							HWP::Log("firearms", "over-reload: missed at " + m_elapsed + " ms (window " + m_windowStart + ")");
							// the cast, the whole Reload time, would outlast the automatic reload
							if (dir !is null)
								dir.Deactivate();
						}
						m_autoTried = true;
					}
					else if (dir !is null && dir.m_castpoint > 0)
					{
						// a manual reload that isn't perfect loses the bonus: it is judged now
						// and given back on a hit
						if (level > 0)
							ClearPerfect(plr);
						m_manual = true;
						m_manualTried = false;
						m_elapsed = 0;
						Start(dir.m_castpoint, level > 0);
						if (level > 0)
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
						bool tryNow = (down && !m_wasDown) || (click && m_elapsed >= m_total / 2);
						if (tryNow && m_windowStart >= 0 && !m_manualTried)
						{
							m_manualTried = true;
							ClearPerfect(plr);
							if (InWindow())
							{
								Perfect(plr, dir, level);
								HWP::Log("firearms", "over-reload: manual perfect at " + m_elapsed + "/" + m_total + " ms");
							}
							else
							{
								Missed();
								HWP::Log("firearms", "over-reload: manual missed at " + m_elapsed + " ms (window " + m_windowStart + ")");
							}
						}
					}
				}
				else if (m_active && click && m_windowStart >= 0 && !m_autoTried && m_elapsed >= m_total / 2)
				{
					// a left click in the automatic reload's second half
					m_autoTried = true;
					ClearPerfect(plr);
					if (InWindow())
					{
						Perfect(plr, null, level);
						HWP::Log("firearms", "over-reload: perfect (click) at " + m_elapsed + "/" + m_total + " ms");
					}
					else
					{
						Missed();
						HWP::Log("firearms", "over-reload: missed (click) at " + m_elapsed + " ms (window " + m_windowStart + ")");
					}
				}
				m_wasCasting = casting;
				m_wasDown = down;
				m_wasFire = fire;
			}

			// the HUD health bar's top left and width, in GUI space; false without a HUD
			bool HealthBar(vec2 &out pos, float &out width)
			{
				pos = vec2();
				width = 0;
				auto hud = GetHUD();
				if (hud is null)
					return false;
				for (uint i = 0; i < hud.m_components.length(); i++)
				{
					auto comp = cast<HUDPlayer>(hud.m_components[i]);
					if (comp is null || comp.m_wBarHealth is null || !comp.m_wBarHealth.m_visible)
						continue;
					pos = comp.m_wBarHealth.m_origin;
					width = comp.m_wBarHealth.m_width;
					return width > 0;
				}
				return false;
			}

			void Render(PlayerBase@ plr, int idt, SpriteBatch& sb)
			{
				if (!m_active && !m_manual)
					return;
				vec2 at;
				float w;
				const float h = 4;
				if (HealthBar(at, w))
					at.y -= h + 3;
				else
				{
					// no HUD: over the player
					w = 30;
					at = ToScreenspace(plr.m_unit.GetInterpolatedPosition(idt) + vec3(0, -30, 0)) / g_gameMode.m_wndScale - vec2(w / 2, 0);
				}
				at = vec2(int(at.x), int(at.y));
				sb.FillRectangle(vec4(at.x - 1, at.y - 1, w + 2, h + 2), vec4(0, 0, 0, 0.7f));
				float done = clamp(m_elapsed / float(m_total), 0.0f, 1.0f);
				vec4 fill = m_missed ? vec4(0.9f, 0.15f, 0.15f, 1) : vec4(0.9f, 0.9f, 0.95f, 1);
				sb.FillRectangle(vec4(at.x, at.y, int(w * done), h), fill);
				if (m_windowStart >= 0)
				{
					vec4 gold = m_perfect || InWindow() ? vec4(1, 1, 0.6f, 1) : vec4(0.95f, 0.75f, 0.2f, 1);
					if (m_missed)
						gold.w = 0.45f;
					float gx = w * m_windowStart / float(m_total);
					float gw = max(2.0f, w * OVER_WINDOW / float(m_total));
					sb.FillRectangle(vec4(at.x + int(gx), at.y - 1, int(gw), h + 2), gold);
				}
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

		// EpiPen's hiss: the grenade fuse, full for 1 s, faded to nothing over the next, then
		// stopped (the fuse runs 3.9 s). It follows the player (UpdateCombat).
		const string EPIPEN_SND = "event:/sfx/player/classes/rogue/grenade/grenade_fuse";
		const int EPIPEN_FADE_FROM = 1000;
		const int EPIPEN_FADE_TO = 2000;
		SoundInstance@ g_epipenSnd;
		int g_epipenMs = 0;

		void StartEpipenSound(PlayerBase@ plr)
		{
			if (g_epipenSnd !is null)
				g_epipenSnd.Stop();
			auto snd = Resources::GetSoundEvent(EPIPEN_SND);
			@g_epipenSnd = snd !is null ? snd.PlayTracked(plr.m_unit.GetPosition()) : null;
			g_epipenMs = 0;
			if (g_epipenSnd is null)
				return;
			g_epipenSnd.SetPaused(false);  // as main.as PlaySound3D(snd, unit) does
			g_epipenSnd.SetVolume(1.0f);
		}

		void UpdateEpipenSound(PlayerBase@ plr, int ms)
		{
			if (g_epipenSnd is null)
				return;
			g_epipenMs += ms;
			if (g_epipenMs >= EPIPEN_FADE_TO)
			{
				g_epipenSnd.Stop();
				@g_epipenSnd = null;
				HWP::Log("firearms", "adrenaline: epipen hiss faded out at " + g_epipenMs + " ms");
				return;
			}
			g_epipenSnd.SetPosition(plr.m_unit.GetPosition());
			if (g_epipenMs > EPIPEN_FADE_FROM)
				g_epipenSnd.SetVolume(1.0f - float(g_epipenMs - EPIPEN_FADE_FROM) / float(EPIPEN_FADE_TO - EPIPEN_FADE_FROM));
		}

		// The raised gun: after a rifle or pistol shot the shot's upper-body animation is
		// played again on the skill layer (1) from its start and frozen there (speed FROZEN,
		// AnimationLoopType::Hold; PlayerBase.SetUnitScene's call otherwise). The wand shot's
		// first frame has the arm out and its last is the rest pose, so the arm stays up
		// between shots instead of dropping to idle. It lets go after HOLD_MS without a gun
		// shot, or at once when the clip reloads or another skill (a dodge, Reload, a spell)
		// starts: the animation then runs on from the frozen frame at full speed, unheld, so
		// the arm comes down the shot's own way and the layer is free.
		const int HOLD_MS = 1000;
		const float FROZEN = 0.0001f;
		const array<uint> GUNS = {
			HashString("hwp_attack_rifle"), HashString("hwp_attack_rifle_epic"),
			HashString("hwp_attack_rifle_gl"), HashString("hwp_attack_rifle_gl_epic"),
			HashString("hwp_attack_glock"), HashString("hwp_attack_glock_off") };

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
					HWP::Log("firearms", "gun arm: lowered (" + why + ")");
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
					if (skill !is null && GUNS.find(skill.m_skillId) >= 0)
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
						HWP::Log("firearms", "gun arm: held");
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
			UpdateEpipenSound(plr, ms);
			if (g_headshotEnd)
			{
				g_headshot = false;
				g_headshotEnd = false;
			}
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

		vec2 m_start;

		HWPFirearmsShot(UnitPtr unit, SValue& params) {}

		void Initialize(NewProjectile@ behavior, SValue& params, Actor@ owner, ProjectileTarget@ target, uint weapon) override
		{
			@m_owner = owner;
			m_start = xy(behavior.m_unit.GetPosition());
			m_hit = false;
			m_local = !behavior.m_husk;
			m_headshot = m_local && GetParamBool(behavior.m_unit, params, "headshot", false, false);
			if (m_headshot)
			{
				HWP::Firearms::g_headshot = true;
				HWP::Firearms::g_headshotEnd = false;
			}
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

		void OnMiss(vec2 pos) override
		{
			if (m_local)
				HWP::Firearms::g_lastRange = dist(m_start, pos);
			Missed();
		}
		void OnCollide(UnitPtr unit, vec2 pos) override { Missed(); }

		// No m_hit here: Destroy() runs OnDestroyed before OnMiss on a range-out
		// (NewProjectile.Update: m_unit.Destroy(), then the OnMiss loop), and before the
		// hit's damage and OnHit when the round stops at its target (NewProjectile.OnHit), so
		// the headshot flag is only marked to clear on the next frame.
		void OnDestroyed() override
		{
			if (m_headshot && !m_hit)
				HWP::Firearms::g_headshotEnd = true;
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
// - epipen (EpiPen's dash trigger): with no stacks, gain epipen stacks, with a yellow glow
//   (epipen_glow) and the grenade fuse's hiss, faded out from 1 s to 2 s (StartEpipenSound).
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
			auto glow = LoadActorBuff(HWP::Firearms::BUFFS + "epipen_glow");
			if (glow !is null)
				plr.ApplyBuff(ActorBuff(plr, glow, 1.0f, false));
			HWP::Firearms::StartEpipenSound(plr);
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
// is the rounds that were left (reload_mag.inc: dmg per round). A Glock in either hand
// throws the smaller pistol magazine ("pistol-projectile"), the rifle its own ("projectile");
// the pick reads the owner's gun markers, so every peer draws the same one. Dual Glocks throw the two
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
	UnitProducer@ m_pistolProjectile;
	bool m_pistol;

	HWPFirearmsThrowMag(UnitPtr unit, SValue& params)
	{
		super(unit, params);
		m_dmg = GetParamInt(unit, params, "dmg", false, 0);  // mag-dmg is an int bind
		m_second = GetParamBool(unit, params, "second", false, false);
		@m_pistolProjectile = Resources::GetUnitProducer(GetParamString(unit, params, "pistol-projectile", false, ""));
	}

	void PickMag(Actor@ owner)
	{
		m_pistol = m_pistolProjectile !is null
			&& (HWP::Firearms::HasBuff(owner, "glock_main") || HWP::Firearms::HasBuff(owner, "glock_off"));
	}

	UnitPtr ProduceProjectile(vec2 shootPos, int id = 0) override
	{
		if (m_pistol)
			return m_pistolProjectile.Produce(g_scene, xyz(shootPos), id);
		return ShootProjectile::ProduceProjectile(shootPos, id);
	}

	bool NetDoAction(SValue@ param, Actor@ owner, vec2 pos, vec2 dir) override
	{
		PickMag(owner);
		return ShootProjectile::NetDoAction(param, owner, pos, dir);
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
		PickMag(owner);

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
			// as ActiveSkill's queued DoActivate does, so the others see the dash, not a slide
			SValue@ none = null;
			(Network::Message("PlayerActiveSkillDoActivate") << int(dash.m_skillId) << away << none).SendToAll();
			break;
		}
		HWP::Log("firearms", "rocket jump: " + int(dist) + " of " + m_radius + " from the blast, away "
			+ int(away.x * 100) + "," + int(away.y * 100));
		return true;
	}
}

// Reload (fs_reload.sval): the cast is the reload, and it refills at its castpoint, which is
// the level's whole recharge time (2 s down to 1.2 s). While it runs the skill's cooldown
// shows the time left, and once it ends (landed or not) Reload is ready again.
// - It won't start with a full clip, or during the automatic reload unless Over-Reload is
//   learned (the press is then that reload's timing try, Combat.as OverReloadState).
// - A dodge cancels it (PlayerTargetingHelper.CancelOther) with the clip as it was; with
//   Dodge Reload Skip it finishes at once instead: the cast list runs, then the cast ends.
class HWPFirearmsReload : Skills::PlayerSkillDirectional
{
	HWPFirearmsReload(UnitPtr unit, SValue& params) { super(unit, params); }

	bool CanActivate(bool warn = true) override
	{
		if (!Skills::PlayerSkillDirectional::CanActivate(warn))
			return false;
		auto plr = cast<PlayerBase>(m_owner);
		auto clip = ActorBuffStackDef::Get(HWP::Firearms::CLIP);
		if (plr is null || clip is null)
			return true;
		int mx = HWP::Firearms::ClipMax(plr, clip);
		if (mx > 0 && plr.GetStacks(clip) >= mx)
		{
			if (warn)
				plr.m_record.PlayVoice("cant");
			return false;
		}
		auto reloading = ActorBuffStackDef::Get(HWP::Firearms::RELOADING);
		// during the automatic reload only as Over-Reload's one timing try
		if (reloading !is null && plr.GetStacks(reloading) > 0 && (HWP::Firearms::g_overReload.Level(plr) == 0
			|| (HWP::Firearms::g_overReload.m_autoTried && plr is cast<PlayerBase>(GetLocalPlayer()))))
			return false;
		return true;
	}

	bool DashCancel()
	{
		auto plr = cast<PlayerBase>(m_owner);
		if (plr is null)
			return false;
		for (uint i = 0; i < plr.m_skills.length(); i++)
		{
			auto s = plr.m_skills[i];
			if (s !is null && s !is this && s.m_type == PlayerSkillType::Dash && HWP::Firearms::Casting(s))
				return true;
		}
		return false;
	}

	void Deactivate() override
	{
		bool cut = m_castingT >= 0 && m_castingT < m_castpoint;
		if (cut && DashCancel())
		{
			if (HWP::Firearms::HasBuff(m_owner, "dodge_skip"))
			{
				HWP::Log("firearms", "reload: dodge at " + m_castingT + "/" + m_castpoint + " ms finishes it");
				m_timeline.Update(m_timeline.GetLength() + 1);
				cut = false;
			}
			else
				HWP::Log("firearms", "reload: dodge at " + m_castingT + "/" + m_castpoint + " ms cancels it");
		}
		// a perfect reload's top-up only follows a cast that got its clip in; the others stop
		// the cast too (PlayerSkillDirectional.Deactivate sends nothing)
		if (cut && cast<PlayerBase>(m_owner) is cast<PlayerBase>(GetLocalPlayer()))
		{
			HWP::Firearms::g_overReload.m_topUp = 0;
			(Network::Message("PlayerActiveSkillDeactivate") << int(m_skillId)).SendToAll();
		}
		Skills::PlayerSkillDirectional::Deactivate();
		m_cooldownC = 0;
		CastIcon(0, 0);
	}

	// another player's Reload cut short (a missed Over-Reload try, a dodge)
	void NetDeactivate() override
	{
		if (m_castingT >= 0 && m_castingT < m_castpoint)
			Skills::PlayerSkillDirectional::Deactivate();
	}

	void Update(int dt, bool walking, vec2 aimDir) override
	{
		Skills::PlayerSkillDirectional::Update(dt, walking, aimDir);
		if (m_castingT >= 0 && m_castingT < m_castpoint)
		{
			float speed = max(0.01f, m_modSkillSpeedMul * m_castSpeedMul * GetModSkillSpeedWalk(walking));
			m_cooldownC = int((m_castpoint - m_castingT) / speed);
			CastIcon(m_cooldownC, int(m_castpoint / speed));
		}
		else
			CastIcon(0, 0);
	}

	// The automatic reload's buff icon (the reloading stack's radial sweep) for the cast:
	// the reload_cast stack, held while the cast runs, its timer set to the time left out of
	// the whole cast each frame. left 0 takes it off.
	ActorBuffStackDefBase m_iconTime;
	void CastIcon(int left, int total)
	{
		auto plr = cast<PlayerBase>(m_owner);
		auto def = ActorBuffStackDef::Get(HWP::Firearms::RELOAD_CAST);
		if (plr is null || def is null || plr !is cast<PlayerBase>(GetLocalPlayer()))
			return;
		auto st = HWP::Firearms::FindStack(plr, def);
		if (left <= 0)
		{
			if (st !is null && st.m_stacks > 0)
				plr.AddStacks(plr, def, -st.m_stacks);
			return;
		}
		if (st is null || st.m_stacks <= 0)
		{
			plr.AddStacks(plr, def, 1);
			@st = HWP::Firearms::FindStack(plr, def);
			if (st is null)
				return;
			HWP::Log("firearms", "reload: cast icon on, " + left + "/" + total + " ms");
		}
		m_iconTime.Reset(def);
		m_iconTime.m_timerTime = ivec2(total, total);
		@st.m_defMod = m_iconTime;
		st.m_timerTickC = left;
	}
}

// The rifle's and the pistols' attacks. A gun on an empty clip (reloading) says "cant" only
// for a fresh click: holding the trigger into or through a reload stays quiet. The warning is
// armed while the trigger is up, and the first warned check (a shot or the warning) spends it.
class HWPFirearmsGun : Skills::PlayerSkillDirectional
{
	bool m_warnArmed = true;

	// A held trigger restarts the skill once it reaches its length (PlayerTargetingHelper.as:629,
	// DirectionRepeating). The base Update deactivates in the frame the cycle ends and drops
	// the part of the frame past the end (PlayerSkillDirectional.as:91-100). The helper only
	// restarts it on a later pass, and the timeline's 0 entries (the first shot) fire on the
	// Update after that. So the first shot of each cycle came a frame or more late, and a
	// dual pistols' left-right gaps alternated short and long (264/330 ms,
	// look-firearms-batch 20261019-183547).
	// Instead, the gun restarts itself in that same frame, as the helper would: Activate, then
	// CancelOther and TriggerModifierEffects. It carries the overshoot into the new cycle and
	// fires its 0 entries at once.
	int CARRY_MAX = 100; // AngelScript allows no const class properties
	int m_carry = -1;

	// A gun alone in the hands can run a shorter cycle: "hwp-solo-length" replaces anim-length
	// while the owner lacks the "hwp-solo-unless" marker buff (the lone Glock: one round every
	// 300 ms, not two a 600 ms cycle, which read as a two-round burst). The timeline entries
	// past the short cycle then never fire. "hwp-solo-blocking" likewise replaces the end of
	// the blocking window, which for the pair covers the second round.
	int m_fullLen;
	int m_soloLen;
	string m_soloUnless;
	int m_fullBlocking;
	int m_soloBlocking;

	HWPFirearmsGun(UnitPtr unit, SValue& params)
	{
		super(unit, params);
		m_fullLen = m_animLen;
		m_soloLen = GetParamInt(unit, params, "hwp-solo-length", false, -1);
		m_soloUnless = GetParamString(unit, params, "hwp-solo-unless", false, "");
		m_fullBlocking = m_blocking.y;
		m_soloBlocking = GetParamInt(unit, params, "hwp-solo-blocking", false, -1);
	}

	void NetActivate(vec2 target, float intensity) override
	{
		if (m_soloLen > 0)
		{
			bool paired = HWP::Firearms::HasBuff(m_owner, m_soloUnless);
			m_animLen = paired ? m_fullLen : m_soloLen;
			if (m_soloBlocking >= 0)
				m_blocking.y = paired ? m_fullBlocking : m_soloBlocking;
		}
		Skills::PlayerSkillDirectional::NetActivate(target, intensity);
		if (m_carry >= 0)
			m_castingT = m_carry;
	}

	bool CanActivate(bool warn = true) override
	{
		bool ok = Skills::PlayerSkillDirectional::CanActivate(warn && m_warnArmed);
		if (warn && m_warnArmed && !ok)
			HWP::Log("firearms", m_id + ": refused, warned (a fresh click)");
		if (warn)
			m_warnArmed = false;
		return ok;
	}

	void Update(int dt, bool walking, vec2 aimDir) override
	{
		int carry = -1;
		if (m_castingT >= 0 && m_repeating)
		{
			float skillSpeed = m_modSkillSpeedMul * m_castSpeedMul * GetModSkillSpeedWalk(walking);
			int next = m_castingT + int(skillSpeed * dt);
			if (next >= m_skillLen)
				carry = min(next - m_skillLen, CARRY_MAX);
		}
		Skills::PlayerSkillDirectional::Update(dt, walking, aimDir);
		auto plr = cast<Player>(m_owner);
		if (plr is null || plr.m_targetHelper is null)
			return;
		bool down = plr.m_targetHelper.GetSkillInput(this).Down;
		if (!down)
			m_warnArmed = true;
		else if (carry >= 0 && m_castingT < 0)
		{
			m_carry = carry;
			bool ok = Activate(aimDir, 1.0f);
			m_carry = -1;
			if (ok)
			{
				plr.m_targetHelper.CancelOther(this, aimDir);
				plr.m_targetHelper.TriggerModifierEffects(this);
				m_timeline.Update(max(m_castingT, 1));
			}
		}
	}
}

// Sniper Shot: while it winds up (before the castpoint), a red laser dot sits where the shot
// will land: the first wall or body on the aim line (RaycastClosest, RaycastType::Shot, as
// ShootProjectile clamps a muzzle), or the round's reach. Local player only; nothing is synced.
// The module takes the dot away once the skill stops moving it (UpdateLaserDot): a skill no
// longer updated mid-windup (death, a respec) never gets to HideDot.
namespace HWP
{
	namespace Firearms
	{
		UnitPtr g_laserDot;
		int g_laserDotAge = 0;

		void UpdateLaserDot()
		{
			if (!g_laserDot.IsValid() || ++g_laserDotAge <= 2)
				return;
			g_laserDot.Destroy();
			g_laserDot = UnitPtr();
		}
	}
}

class HWPFirearmsSnipe : Skills::PlayerSkillDirectional
{
	// a Sniper Shot round's flight before it runs out (bullet_snipe.unit), measured with
	// hwp firearms muzzle (look-firearms-tips)
	float SNIPE_REACH = 300;

	UnitPtr m_dot;

	HWPFirearmsSnipe(UnitPtr unit, SValue& params) { super(unit, params); }

	void Update(int dt, bool walking, vec2 aimDir) override
	{
		Skills::PlayerSkillDirectional::Update(dt, walking, aimDir);
		auto plr = cast<Player>(m_owner);
		if (plr is null || m_castingT < 0 || m_castingT >= m_castpoint)
		{
			HideDot();
			return;
		}
		vec2 dir = normalize(m_timeline.m_dirTarget);
		vec2 from = xy(plr.m_unit.GetPosition());
		vec2 to = from + dir * SNIPE_REACH;
		auto hit = g_scene.RaycastClosest(from, to, ~0, RaycastType::Shot);
		if (hit.fraction < 1.0f)
			to = hit.point;
		if (!m_dot.IsValid())
		{
			auto fx = Resources::GetEffect("players/hwp/firearms/effects/laser_dot.effect");
			if (fx is null)
				return;
			m_dot = g_effectUnit.Produce(g_scene, xyz(to));
			auto eb = cast<EffectBehavior>(m_dot.GetScriptBehavior());
			if (eb is null)
			{
				m_dot.Destroy();
				m_dot = UnitPtr();
				return;
			}
			eb.Initialize(fx, dictionary());
			HWP::Log("firearms", "snipe: laser dot on, " + formatFloat(dist(from, to), "", 0, 1) + " out"
				+ (hit.fraction < 1.0f ? " (hit)" : " (reach)"));
		}
		m_dot.SetPosition(to.x, to.y, 0, true);
		HWP::Firearms::g_laserDot = m_dot;
		HWP::Firearms::g_laserDotAge = 0;
	}

	void Deactivate() override
	{
		Skills::PlayerSkillDirectional::Deactivate();
		HideDot();
	}

	void HideDot()
	{
		if (!m_dot.IsValid())
			return;
		m_dot.Destroy();
		m_dot = UnitPtr();
	}
}
