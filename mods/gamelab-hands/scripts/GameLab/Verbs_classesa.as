// gamelab-hands: skill verbs for the class checks (plan_classesa). castat casts one of the
// local player's skills at a point, as the targeting helper does once a target is picked;
// track samples matching units every gameplay frame (a projectile's flight, a summon's
// lifetime) and reports one summary event; actorbuffs lists the buffs on actors around the
// player; skilltip is the skill's tooltip body as the skill tree writes it.
namespace GameLab
{
	// castat <skillId> <dx> <dy> [nocd]: Skill.Activate of the local player's skill, what
	// PlayerTargetingHelper.Update calls on the activating press (Player/PlayerTargetingHelper.as:
	// 291 TargetAOE, 400 Direction): a TargetAOE skill gets the point player + (dx, dy) clamped
	// to its range and cut by its raycast like CalcMouseTargetPos, any other the direction
	// (dx, dy). Then TriggerModifierEffects, as the helper does. "nocd" resets the cooldown first.
	void VerbCastAt(const string &in id, array<string>@ args)
	{
		if (args.length() < 3)
		{
			Fail(id, "usage: castat <skillId> <dx> <dy> [nocd]");
			return;
		}
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		Skills::Skill@ skill = null;
		array<string> ids;
		for (uint i = 0; i < plr.m_skills.length(); i++)
		{
			if (plr.m_skills[i] is null)
				continue;
			ids.insertLast(plr.m_skills[i].m_id);
			if (plr.m_skills[i].m_id == args[0])
				@skill = plr.m_skills[i];
		}
		if (skill is null)
		{
			Emit(Reply(id, false).Str("error", "no skill " + args[0]).Raw("skills", StrArray(ids)));
			return;
		}
		if (args.length() > 3 && args[3] == "nocd")
			skill.ResetCooldown();

		vec2 plrPos = xy(plr.m_unit.GetPosition());
		vec2 rel(parseFloat(args[1]), parseFloat(args[2]));
		float len = length(rel);
		if (len <= 0)
		{
			Fail(id, "dx dy must not both be 0");
			return;
		}
		vec2 dir = rel / len;

		Skills::TargetingParams params;
		auto mode = skill.GetTargetingMode(params);
		vec2 target = dir;
		if (mode == Skills::TargetingMode::TargetAOE)
		{
			len = min(params.rangeMax, max(params.rangeMin, len));
			if (params.needsRaycast)
			{
				auto ray = g_scene.Raycast(plrPos, plrPos + dir * len, ~0, params.raycastAnyExceptActors ? RaycastType::Any : RaycastType::Aim);
				for (uint i = 0; i < ray.length(); i++)
				{
					UnitPtr unit = ray[i].FetchUnit(g_scene);
					if (cast<PlayerBase>(unit.GetScriptBehavior()) is null)
					{
						len *= ray[i].fraction;
						break;
					}
				}
			}
			target = plrPos + dir * len;
		}

		bool activated = skill.Activate(target, 1.0f);
		if (activated)
			plr.m_targetHelper.TriggerModifierEffects(skill);
		Emit(Reply(id, activated).Str("skill", args[0]).Int("mode", int(mode)).Bool("activated", activated)
			.Num("x", plrPos.x).Num("y", plrPos.y).Num("tx", target.x).Num("ty", target.y));
	}

	const uint TRACK_CAP = 24;

	// one track sample set per unit: first and last sight, distance from the player
	class TrackTask : QueuedTasks::UpdatingTask
	{
		string m_tag;
		string m_filter;
		int m_radius;
		int m_msLeft;
		int m_t = 0;
		uint m_frames = 0;
		int m_most = 0;
		int m_truncated = 0;
		bool m_havePlr = false;
		vec2 m_plr0;
		vec2 m_plr1;

		array<int> m_ids;
		array<string> m_names;
		array<int> m_t0;
		array<int> m_t1;
		array<int> m_n;
		array<vec2> m_p0;
		array<vec2> m_p1;
		array<vec2> m_from0;
		array<float> m_dMax;
		array<int> m_tMax;
		array<float> m_dMinAfter;
		array<float> m_dLast;

		bool UpdateFrame(int ms) override
		{
			m_t += ms;
			m_msLeft -= ms;
			m_frames++;
			auto plr = GetLocalPlayer();
			if (plr !is null)
			{
				vec2 c = xy(plr.m_unit.GetPosition());
				if (!m_havePlr)
				{
					m_plr0 = c;
					m_havePlr = true;
				}
				m_plr1 = c;
				auto units = g_scene.FetchAllUnits(~0, c, m_radius);
				int seen = 0;
				for (uint i = 0; i < units.length(); i++)
				{
					if (!units[i].IsValid() || units[i].IsDestroyed() || units[i] == plr.m_unit)
						continue;
					vec2 p = xy(units[i].GetPosition());
					float d = dist(c, p);
					if (d > m_radius)
						continue;
					// the filter matches as near's does: behavior type name or .unit path
					ref@ b = units[i].GetScriptBehavior();
					if (m_filter != "" && (b is null || Reflect::GetTypeName(b).findFirst(m_filter) < 0)
						&& units[i].GetDebugName().findFirst(m_filter) < 0)
						continue;
					seen++;
					int uid = units[i].GetId();
					int k = m_ids.find(uid);
					if (k < 0)
					{
						if (m_ids.length() >= TRACK_CAP)
						{
							m_truncated++;
							continue;
						}
						m_ids.insertLast(uid);
						m_names.insertLast(units[i].GetDebugName());
						m_t0.insertLast(m_t);
						m_t1.insertLast(m_t);
						m_n.insertLast(0);
						m_p0.insertLast(p);
						m_p1.insertLast(p);
						m_from0.insertLast(c);
						m_dMax.insertLast(d);
						m_tMax.insertLast(m_t);
						m_dMinAfter.insertLast(d);
						m_dLast.insertLast(d);
						k = int(m_ids.length()) - 1;
					}
					m_t1[k] = m_t;
					m_n[k] = m_n[k] + 1;
					m_p1[k] = p;
					m_dLast[k] = d;
					if (d > m_dMax[k])
					{
						m_dMax[k] = d;
						m_tMax[k] = m_t;
						m_dMinAfter[k] = d;
					}
					else if (d < m_dMinAfter[k])
						m_dMinAfter[k] = d;
				}
				if (seen > m_most)
					m_most = seen;
			}
			if (m_msLeft > 0)
				return false;

			array<string> items;
			for (uint i = 0; i < m_ids.length(); i++)
			{
				Json e;
				e.Int("unit", m_ids[i]).Str("name", m_names[i]).Int("t0", m_t0[i]).Int("t1", m_t1[i]).Int("n", m_n[i])
					.Num("x0", m_p0[i].x).Num("y0", m_p0[i].y).Num("x1", m_p1[i].x).Num("y1", m_p1[i].y)
					.Num("px0", m_from0[i].x).Num("py0", m_from0[i].y)
					.Num("dmax", m_dMax[i]).Int("tmax", m_tMax[i]).Num("dminafter", m_dMinAfter[i]).Num("dlast", m_dLast[i]);
				items.insertLast(e.Close());
			}
			Json j;
			Emit(j.Str("ev", "track").Str("tag", m_tag).Int("ms", m_t).Int("frames", m_frames).Int("most", m_most)
				.Int("truncated", m_truncated).Num("px0", m_plr0.x).Num("py0", m_plr0.y).Num("px1", m_plr1.x).Num("py1", m_plr1.y)
				.Raw("tracks", RawArray(items)));
			return true;
		}
	}

	// track <tag> <ms> <radius> <filter>: read-only. For ms of gameplay frames, every unit within
	// radius of the player whose behavior type or .unit path contains filter (as near): first
	// and last sight (time, position), samples, its greatest distance from the player and the
	// least after it, the last. One {"ev":"track","tag":...} event when the time is up (a
	// QueuedTasks updating task, so only while a gameplay module ticks). Capped at TRACK_CAP units.
	void VerbTrack(const string &in id, array<string>@ args)
	{
		if (args.length() < 4)
		{
			Fail(id, "usage: track <tag> <ms> <radius> <filter>");
			return;
		}
		if (QueuedTasks::g_instance is null)
		{
			Fail(id, "no QueuedTasks module");
			return;
		}
		TrackTask task;
		task.m_tag = args[0];
		task.m_msLeft = int(parseInt(args[1]));
		task.m_radius = int(parseInt(args[2]));
		task.m_filter = args[3];
		QueuedTasks::Queue(task);
		Emit(Reply(id, true).Str("tag", task.m_tag).Int("ms", task.m_msLeft));
	}

	const uint ACTORBUFFS_CAP = 32;

	// actorbuffs <radius> [filter]: read-only. Live actors within radius of the player (not the
	// player), nearest first as near, with each buff's name, tags (g_actorBuffTags names) and
	// time left (ActorBuff.m_duration), from Actor.GetBuffList(). Capped at ACTORBUFFS_CAP.
	void VerbActorBuffs(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		int radius = args.length() > 0 ? int(parseInt(args[0])) : 200;
		string filter = args.length() > 1 ? args[1] : "";
		vec2 center = xy(plr.m_unit.GetPosition());
		auto units = g_scene.FetchAllUnits(~0, center, radius);
		array<Actor@> keep;
		array<float> dists;
		for (uint i = 0; i < units.length(); i++)
		{
			if (!units[i].IsValid() || units[i].IsDestroyed() || units[i] == plr.m_unit)
				continue;
			float d = dist(center, xy(units[i].GetPosition()));
			if (d > radius)
				continue;
			ref@ b = units[i].GetScriptBehavior();
			auto actor = cast<Actor>(b);
			if (actor is null || actor.IsDead())
				continue;
			if (filter != "" && Reflect::GetTypeName(b).findFirst(filter) < 0 && units[i].GetDebugName().findFirst(filter) < 0)
				continue;
			uint at = 0;
			while (at < dists.length() && dists[at] <= d)
				at++;
			keep.insertAt(at, actor);
			dists.insertAt(at, d);
		}
		array<string> items;
		for (uint i = 0; i < keep.length() && i < ACTORBUFFS_CAP; i++)
		{
			auto actor = keep[i];
			array<string> buffs;
			auto list = actor.GetBuffList();
			if (list !is null)
			{
				for (uint j = 0; j < list.m_buffs.length(); j++)
				{
					auto buff = list.m_buffs[j];
					if (buff is null || buff.m_def is null)
						continue;
					array<string> tags;
					for (uint t = 0; t < g_actorBuffTags.m_tags.length(); t++)
					{
						if ((buff.m_def.m_tags & ApplyTag(0, t + 1)) != 0)
							tags.insertLast(g_actorBuffTags.m_tags[t]);
					}
					Json bj;
					bj.Str("name", buff.m_def.m_name).Raw("tags", StrArray(tags)).Int("left", buff.m_duration)
						.Bool("debuff", buff.m_def.m_debuff);
					buffs.insertLast(bj.Close());
				}
			}
			vec3 pos = actor.m_unit.GetPosition();
			Json e;
			e.Int("unit", actor.m_unit.GetId()).Str("name", actor.m_unit.GetDebugName()).Num("hp", actor.GetHealth())
				.Num("x", pos.x).Num("y", pos.y).Num("dist", dists[i]).Raw("buffs", RawArray(buffs));
			items.insertLast(e.Close());
		}
		int truncated = keep.length() > ACTORBUFFS_CAP ? int(keep.length() - ACTORBUFFS_CAP) : 0;
		Emit(Reply(id, true).Int("count", keep.length()).Int("truncated", truncated).Raw("actors", RawArray(items)));
	}

	// skilltip <skillId> [level]: read-only. The skill's tooltip text as the skill tree and
	// CreateSkillTooltip write it (AppendTagsList + AppendSkillDesc, GUI/PlayerMenu/
	// Modifications.as:1003/1028, GUI/Tooltip.as:821-824): the description with its %params%
	// filled for the level (the character's own when omitted) and the per-level param lines.
	void VerbSkillTip(const string &in id, array<string>@ args)
	{
		auto rec = GetLocalPlayerRecord();
		if (rec is null || rec.playerClass is null)
		{
			Fail(id, "no local character");
			return;
		}
		if (args.length() < 1)
		{
			Fail(id, "usage: skilltip <skillId> [level]");
			return;
		}
		auto def = rec.playerClass.GetSkillDef(HashString(args[0]));
		if (def is null)
		{
			Fail(id, "no skill " + args[0] + " in " + rec.playerClass.m_id);
			return;
		}
		int lvl = args.length() > 1 ? int(parseInt(args[1])) : -1;
		StringBuilder desc;
		AppendTagsList(desc, def.m_tags);
		AppendSkillDesc(rec, desc, def, lvl);
		Emit(Reply(id, true).Str("skill", args[0]).Str("name", Resources::GetString(def.m_name))
			.Int("level", rec.GetSkillLevel(def)).Str("text", desc.String()));
	}

	void Register_classesa()
	{
		RegisterVerb("castat", "<skillId> <dx> <dy> [nocd]", Verb(VerbCastAt));
		RegisterVerb("track", "<tag> <ms> <radius> <filter>", Verb(VerbTrack));
		RegisterVerb("actorbuffs", "[radius] [filter]", Verb(VerbActorBuffs));
		RegisterVerb("skilltip", "<skillId> [level]", Verb(VerbSkillTip));
	}
}
