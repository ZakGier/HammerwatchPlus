// hwp firearms sound: a cheat for picking the guns' firing sound by ear. A mod can't add a
// sound file (the FMOD banks aren't in the unpack), so the pick is one of the game's own
// events. Each is played as a short burst at the player, three shots apart, the way the
// pistols fire. They are 3D events: played without a position (SoundEvent.Play()) they sit
// at the world origin and fade out with distance, which was silent in the demo town.
namespace HWP
{
	namespace Firearms
	{
		const array<string> AUDITION = {
			"event:/sfx/player/attacks/offhand/hand_crossbow_shot",          // 1: the pistols' first sound
			"event:/sfx/player/attacks/twohanded/crossbow_quick_shot",       // 2: the rifle's first sound
			"event:/sfx/player/attacks/offhand/hand_crossbow_shot_hit",
			"event:/sfx/player/attacks/twohanded/quick_shot_hit",
			"event:/sfx/player/attacks/twohanded/crossbow_quick_shot_hit",
			"event:/sfx/player/attacks/offhand/throw_knife",
			"event:/sfx/actors/beasts/trolls/troll_brute/troll_brute_slingshot_cast",
			"event:/sfx/actors/beasts/trolls/troll_brute/troll_brute_slingshot_hit",
			"event:/sfx/player/attacks/twohanded/crossbow_explosive_shot",
			"event:/sfx/player/attacks/twohanded/crossbow_explosive_shot_explode",
			"event:/sfx/actors/beasts/spiders/spider_white/spider_white_spit",
			"event:/sfx/actors/beasts/spiders/spider_black/spider_black_spit",
			"event:/sfx/doodads/traps/magic_ball/magic_ball_ice_shoot",
			"event:/sfx/doodads/traps/arrows/arrow_shoot",
			"event:/sfx/doodads/traps/magic_ball/magic_ball_lightning_shoot",
			"event:/sfx/doodads/traps/floor_spikes/floor_spikes_start",
			"event:/sfx/doodads/traps/floor_spikes/floor_spikes_stop",
			"event:/sfx/actors/bosses/boss_bandit/bandit_throwing_star_bounce",
			"event:/sfx/player/attacks/offhand/throw_knife_hit",
			"event:/sfx/actors/aberrations/phantoms/rogue/phantom_rogue_throw_hit",
			"event:/sfx/actors/aberrations/phantoms/ranger/phantom_ranger_quick_shot_hit",
			"event:/sfx/player/attacks/mainhand/lightning_bolt",
			"event:/sfx/doodads/traps/magic_ball/magic_ball_fire_shoot",
			"event:/sfx/actors/aberrations/phantoms/ranger/phantom_ranger_quick_shot",
			"event:/sfx/player/attacks/twohanded/shortbow_quick_shot",
			"event:/sfx/player/attacks/twohanded/longbow_quick_shot",
			"event:/sfx/player/attacks/twohanded/maul_slam_impact",
			"event:/sfx/doodads/traps/boulder/boulder_impact" };
		const int AUDITION_GAP = 260;

		int g_auditionAt = 0; // 1-based; 0 before the first pick
		SoundEvent@ g_auditionSnd;
		int g_auditionLeft = 0;
		int g_auditionWait = 0;

		void CmdSound(array<string>@ args)
		{
			if (!HWP::Cheats::On())
				return;
			// args[0] is "sound"
			string what = args.length() > 1 ? args[1] : "list";
			int shots = args.length() > 2 ? parseInt(args[2]) : 3;
			string evt;
			string at = "";
			if (what == "list")
			{
				int missing = 0;
				for (uint i = 0; i < AUDITION.length(); i++)
				{
					bool found = Resources::GetSoundEvent(AUDITION[i]) !is null;
					if (!found)
						missing++;
					HWP::Log("firearms", "sound " + (i + 1) + ": " + AUDITION[i] + (found ? "" : " (not found)"));
				}
				HWP::Commands::Reply(AUDITION.length() + " sounds, " + missing + " not found (listed in the log); hwp firearms sound <n>|next|prev|again [shots]");
				return;
			}
			else if (what.findFirst("event:/") == 0)
				evt = what;
			else
			{
				if (what == "next")
					g_auditionAt = g_auditionAt % int(AUDITION.length()) + 1;
				else if (what == "prev")
					g_auditionAt = g_auditionAt <= 1 ? int(AUDITION.length()) : g_auditionAt - 1;
				else if (what != "again")
					g_auditionAt = parseInt(what);
				if (g_auditionAt < 1 || g_auditionAt > int(AUDITION.length()))
				{
					HWP::Commands::Reply("pick 1 to " + AUDITION.length());
					g_auditionAt = 0;
					return;
				}
				evt = AUDITION[g_auditionAt - 1];
				at = g_auditionAt + ": ";
			}
			@g_auditionSnd = Resources::GetSoundEvent(evt);
			if (g_auditionSnd is null)
			{
				HWP::Commands::Reply("no such sound: " + evt);
				return;
			}
			g_auditionLeft = clamp(shots, 1, 10);
			g_auditionWait = 0;
			HWP::Commands::Reply("sound " + at + evt);
			HWP::Log("firearms", "audition " + at + evt);
		}

		void UpdateAudition(int ms)
		{
			if (g_auditionLeft <= 0 || g_auditionSnd is null)
				return;
			g_auditionWait -= ms;
			if (g_auditionWait > 0)
				return;
			auto plr = GetLocalPlayer();
			if (plr is null)
				g_auditionSnd.Play();
			else
				PlaySound3D(g_auditionSnd, plr.m_unit.GetPosition());
			g_auditionLeft--;
			g_auditionWait = AUDITION_GAP;
		}
	}
}

// PlaySound with a volume: the guns' shots (attacks_firearms.sval). The instance is kept
// (the last 16) so the handle isn't let go while the shot still plays. Above 1 is louder
// than the event's own level: FMOD's instance volume is a linear gain.
class HWPFirearmsSound : PlaySound
{
	float m_volume;

	HWPFirearmsSound(UnitPtr unit, SValue& params)
	{
		super(unit, params);
		m_volume = GetParamFloat(unit, params, "volume", false, 1.0f);
	}

	void Do(Actor@ owner, vec2 pos) override
	{
		if (m_snd is null)
			return;
		// the same three ways as PlaySound.Do: 2D, following the owner (main.as
		// PlaySound3D(snd, unit), which lets go of sounds under 350 ms) or at the position
		SoundInstance@ inst;
		bool attach = m_attach && owner !is null;
		if (m_2d)
			@inst = m_snd.PlayTracked();
		else if (attach)
			@inst = m_snd.PlayTracked(owner.m_unit.GetPosition());
		else
			@inst = m_snd.PlayTracked(xyz(pos));
		if (inst is null)
			return;
		inst.SetVolume(m_volume);
		if (attach)
		{
			inst.SetPaused(false);
			int len = inst.GetLength();
			if (len < 0 || len > 350)
			{
				AttachedSound aSnd;
				@aSnd.sound = inst;
				aSnd.unit = owner.m_unit;
				m_attachedSounds.insertLast(aSnd);
			}
		}
		HWP::Firearms::g_shotSounds.insertLast(inst);
		if (HWP::Firearms::g_shotSounds.length() > 16)
			HWP::Firearms::g_shotSounds.removeAt(0);
	}
}

namespace HWP
{
	namespace Firearms
	{
		array<SoundInstance@> g_shotSounds;
	}
}
