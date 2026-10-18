// gamelab-hands: verbs for the runs test plan (architect loadout, HoH1 bosses).
// pressfunc clicks a button by what it does rather than its id (the loadout's
// rows are all clones with id "rect"), wsexec runs a level's world script the
// way its trigger would, actors adds what a boss is doing (casting skills,
// scene, targetable, moving) to what near reports, rayhit finds where a
// RayProjectile flying from a point would stop (wall or hard tiles), trail
// follows units every frame in-engine (a boss's projectiles live for less
// than a console round trip lets a bot see).
namespace GameLab
{
	// the first visible, enabled interactable under w whose func is name; invisible subtrees are skipped
	AInteractableWidget@ RunsFindFunc(Widget@ w, const string &in name)
	{
		if (w is null || !w.m_visible)
			return null;
		auto iw = cast<AInteractableWidget>(w);
		if (iw !is null && iw.m_enabled && iw.m_func == name)
			return iw;
		for (uint i = 0; i < w.m_children.length(); i++)
		{
			auto found = RunsFindFunc(w.m_children[i], name);
			if (found !is null)
				return found;
		}
		return null;
	}

	// pressfunc <func...>: click the first visible, enabled interactable widget of the top window whose func is that
	void VerbPressFunc(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: pressfunc <func...>");
			return;
		}
		auto gm = cast<BaseGameMode>(g_gameMode);
		AWindowObject@ wnd;
		if (gm !is null && gm.m_windowManager !is null)
			@wnd = gm.m_windowManager.GetCurrentWindow();
		if (wnd is null || wnd.m_widget is null)
		{
			Fail(id, "no open window");
			return;
		}
		string name = args[0];
		for (uint i = 1; i < args.length(); i++)
			name += " " + args[i];
		auto iw = RunsFindFunc(wnd.m_widget, name);
		if (iw is null)
		{
			Fail(id, "no visible enabled widget with func '" + name + "' in " + Reflect::GetTypeName(wnd));
			return;
		}
		Emit(Reply(id, true).Str("window", Reflect::GetTypeName(wnd)).Str("widget", Reflect::GetTypeName(iw)).Str("wid", iw.m_id));
		iw.ClickDown(false, vec2());
		iw.ClickUp(false, vec2());
	}

	// wsexec <type> <comment>: Execute() the first world script of that type with that comment (host only)
	void VerbWsExec(const string &in id, array<string>@ args)
	{
		if (args.length() < 2)
		{
			Fail(id, "usage: wsexec <type> <comment>");
			return;
		}
		if (!Network::IsServer())
		{
			Fail(id, "wsexec is host only");
			return;
		}
		auto found = g_scene.FetchAllWorldScriptsWithComment(args[0], args[1]);
		if (found.length() == 0)
		{
			Fail(id, "no " + args[0] + " '" + args[1] + "'");
			return;
		}
		auto ws = found[0];
		bool enabled = ws.IsEnabled();
		bool now = ws.CanExecuteNow();
		ws.Execute();
		Emit(Reply(id, true).Int("found", found.length()).Bool("enabled", enabled).Bool("now", now));
	}

	// actors [radius] [filter]: CompositeActorBehavior units within radius (default 400) of the player:
	// position, hp, scene, the skills casting right now, targetable, moving (non-static body), frozen
	void VerbActors(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		int radius = args.length() > 0 ? int(parseInt(args[0])) : 400;
		string filter = args.length() > 1 ? args[1] : "";
		vec2 center = xy(plr.m_unit.GetPosition());
		auto units = g_scene.FetchAllUnits(~0, center, radius);
		array<string> items;
		for (uint i = 0; i < units.length() && items.length() < 32; i++)
		{
			UnitPtr u = units[i];
			if (!u.IsValid() || u.IsDestroyed())
				continue;
			auto a = cast<CompositeActorBehavior>(u.GetScriptBehavior());
			if (a is null)
				continue;
			vec3 pos = u.GetPosition();
			if (dist(center, xy(pos)) > radius)
				continue;
			if (filter != "" && Reflect::GetTypeName(a).findFirst(filter) < 0 && u.GetDebugName().findFirst(filter) < 0)
				continue;
			array<string> casting;
			if (a.m_skills !is null)
			{
				for (uint s = 0; s < a.m_skills.length(); s++)
				{
					if (a.m_skills[s].IsCasting())
						casting.insertLast(Reflect::GetTypeName(a.m_skills[s]));
				}
			}
			auto body = u.GetPhysicsBody();
			Json e;
			e.Int("unit", u.GetId()).Str("name", u.GetDebugName()).Str("behavior", Reflect::GetTypeName(a));
			e.Num("x", pos.x).Num("y", pos.y).Num("hp", a.GetHealth()).Bool("dead", a.IsDead());
			e.Str("scene", u.GetCurrentUnitScene().GetName()).Raw("casting", StrArray(casting));
			e.Bool("targetable", a.IsTargetable()).Bool("moving", body !is null && !body.IsStatic()).Bool("frozen", a.m_frozen);
			items.insertLast(e.Close());
		}
		Emit(Reply(id, true).Int("count", items.length()).Raw("actors", RawArray(items)));
	}

	// rayhit <x0> <y0> <x1> <y1> [hardness]: where a RayProjectile from (x0,y0) toward (x1,y1) stops:
	// "wall", the first Shot raycast hit that is no damage taker (RayProjectile.HitUnit destroys a
	// bounceless one there), and "tile", the first point (4 px steps) on tiles harder than
	// hardness (default 4, HoH1LurkerProjectile's destroy-at-hardness)
	void VerbRayHit(const string &in id, array<string>@ args)
	{
		if (args.length() < 4)
		{
			Fail(id, "usage: rayhit <x0> <y0> <x1> <y1> [hardness]");
			return;
		}
		vec2 from = vec2(parseFloat(args[0]), parseFloat(args[1]));
		vec2 to = vec2(parseFloat(args[2]), parseFloat(args[3]));
		int hardness = args.length() > 4 ? int(parseInt(args[4])) : 4;
		Json@ r = Reply(id, true);
		bool wall = false;
		array<RaycastResult>@ results = g_scene.Raycast(from, to, ~0, RaycastType::Shot);
		for (uint i = 0; i < results.length() && !wall; i++)
		{
			RaycastResult res = results[i];
			UnitPtr u = res.FetchUnit(g_scene);
			if (u.IsValid() && cast<IDamageTaker>(u.GetScriptBehavior()) !is null)
				continue;
			wall = true;
			r.Num("wx", res.point.x).Num("wy", res.point.y).Num("wd", dist(from, res.point));
			r.Str("wname", u.IsValid() ? u.GetDebugName() : "").Bool("wsensor", res.fixture.IsSensor());
		}
		r.Bool("wall", wall);
		float len = dist(from, to);
		bool tile = false;
		if (len > 0)
		{
			vec2 dir = normalize(to - from);
			for (float d = 0; d <= len && !tile; d += 4.0f)
			{
				vec2 p = from + dir * d;
				auto tilesets = g_scene.FetchTilesets(p);
				for (uint i = 0; i < tilesets.length() && !tile; i++)
				{
					SValue@ data = tilesets[i].GetData();
					SValue@ h = data is null ? null : data.GetDictionaryEntry("hardness");
					if (h is null || h.GetType() != SValueType::Integer || h.GetInteger() <= hardness)
						continue;
					tile = true;
					r.Num("tx", p.x).Num("ty", p.y).Num("td", d).Int("th", h.GetInteger());
				}
			}
		}
		r.Bool("tile", tile);
		Emit(r);
	}

	const uint TRAIL_CAP = 32;
	const uint TRAIL_POINTS = 200;

	string RunsPoint(vec2 p, int t)
	{
		return "[" + int(p.x) + "," + int(p.y) + "," + t + "]";
	}

	// every unit a trail sees: first and last sight (exact to the frame) and a point every step ms
	class RunsTrailTask : QueuedTasks::UpdatingTask
	{
		string m_tag;
		string m_filter;
		int m_radius;
		int m_msLeft;
		int m_step;
		int m_t = 0;
		int m_next = 0;
		int m_truncated = 0;
		array<string> m_plr;

		array<int> m_ids;
		array<string> m_names;
		array<int> m_t0;
		array<int> m_t1;
		array<vec2> m_p0;
		array<vec2> m_p1;
		array<string> m_pts;
		array<int> m_n;

		bool UpdateFrame(int ms) override
		{
			m_t += ms;
			m_msLeft -= ms;
			bool sample = m_t >= m_next;
			if (sample)
				m_next = m_t + m_step;
			auto plr = GetLocalPlayer();
			if (plr !is null)
			{
				vec2 c = xy(plr.m_unit.GetPosition());
				if (sample && m_plr.length() < TRAIL_POINTS)
					m_plr.insertLast(RunsPoint(c, m_t));
				auto units = g_scene.FetchAllUnits(~0, c, m_radius);
				for (uint i = 0; i < units.length(); i++)
				{
					UnitPtr u = units[i];
					if (!u.IsValid() || u.IsDestroyed() || u == plr.m_unit)
						continue;
					vec2 p = xy(u.GetPosition());
					if (dist(c, p) > m_radius)
						continue;
					ref@ b = u.GetScriptBehavior();
					if (m_filter != "" && (b is null || Reflect::GetTypeName(b).findFirst(m_filter) < 0)
						&& u.GetDebugName().findFirst(m_filter) < 0)
						continue;
					int k = m_ids.find(u.GetId());
					bool first = k < 0;
					if (first)
					{
						if (m_ids.length() >= TRAIL_CAP)
						{
							m_truncated++;
							continue;
						}
						m_ids.insertLast(u.GetId());
						m_names.insertLast(u.GetDebugName());
						m_t0.insertLast(m_t);
						m_t1.insertLast(m_t);
						m_p0.insertLast(p);
						m_p1.insertLast(p);
						m_pts.insertLast("");
						m_n.insertLast(0);
						k = int(m_ids.length()) - 1;
					}
					m_t1[k] = m_t;
					m_p1[k] = p;
					if ((first || sample) && uint(m_n[k]) < TRAIL_POINTS)
					{
						m_pts[k] += (m_n[k] > 0 ? "," : "") + RunsPoint(p, m_t);
						m_n[k] = m_n[k] + 1;
					}
				}
			}
			if (m_msLeft > 0)
				return false;

			array<string> items;
			for (uint i = 0; i < m_ids.length(); i++)
			{
				Json e;
				e.Int("unit", m_ids[i]).Str("name", m_names[i]).Int("t0", m_t0[i]).Int("t1", m_t1[i])
					.Num("x0", m_p0[i].x).Num("y0", m_p0[i].y).Num("x1", m_p1[i].x).Num("y1", m_p1[i].y)
					.Raw("pts", "[" + m_pts[i] + "]");
				items.insertLast(e.Close());
			}
			Json j;
			Emit(j.Str("ev", "trail").Str("tag", m_tag).Int("ms", m_t).Int("truncated", m_truncated)
				.Raw("plr", RawArray(m_plr)).Raw("units", RawArray(items)));
			return true;
		}
	}

	// trail <tag> <ms> <radius> <filter> [stepMs]: read-only. For ms of gameplay frames, every unit
	// within radius of the player whose behavior type or .unit path contains filter (as near):
	// first and last sight (time, position) and a point [x,y,ms] every stepMs (default 100), the
	// player's own points too. One {"ev":"trail","tag":...} event when the time is up (a
	// QueuedTasks updating task, so only while a gameplay module ticks). Capped at TRAIL_CAP units,
	// TRAIL_POINTS points each.
	void VerbTrail(const string &in id, array<string>@ args)
	{
		if (args.length() < 4)
		{
			Fail(id, "usage: trail <tag> <ms> <radius> <filter> [stepMs]");
			return;
		}
		if (QueuedTasks::g_instance is null)
		{
			Fail(id, "no QueuedTasks module");
			return;
		}
		RunsTrailTask task;
		task.m_tag = args[0];
		task.m_msLeft = int(parseInt(args[1]));
		task.m_radius = int(parseInt(args[2]));
		task.m_filter = args[3];
		task.m_step = args.length() > 4 ? max(16, int(parseInt(args[4]))) : 100;
		QueuedTasks::Queue(task);
		Emit(Reply(id, true).Str("tag", task.m_tag).Int("ms", task.m_msLeft).Int("step", task.m_step));
	}

	void Register_runs()
	{
		RegisterVerb("pressfunc", "<func...>", Verb(VerbPressFunc));
		RegisterVerb("wsexec", "<type> <comment>", Verb(VerbWsExec));
		RegisterVerb("actors", "[radius] [filter]", Verb(VerbActors));
		RegisterVerb("rayhit", "<x0> <y0> <x1> <y1> [hardness]", Verb(VerbRayHit));
		RegisterVerb("trail", "<tag> <ms> <radius> <filter> [stepMs]", Verb(VerbTrail));
	}
}
