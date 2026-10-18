// gamelab-hands: world script verbs. prefab fabricates a prefab next to the
// player (as PrefabPicker does), ws lists world scripts by type and comment
// (enabled, trigger times, a Variable's value), usews presses a UseTrigger the
// way the use key does (IUsable.Use, which executes it on the host), goto puts
// the player next to a world script (a generated room's puzzle, say).
namespace GameLab
{
	// prefab <file> <dx> <dy>: Prefab.Fabricate at the player + (dx, dy)
	void VerbPrefab(const string &in id, array<string>@ args)
	{
		if (args.length() < 3)
		{
			Fail(id, "usage: prefab <file> <dx> <dy>");
			return;
		}
		auto plr = GetLocalPlayer();
		if (plr is null || !Network::IsServer())
		{
			Fail(id, plr is null ? "no spawned local player" : "prefab is host only");
			return;
		}
		auto pfb = Resources::GetPrefab(args[0]);
		if (pfb is null)
		{
			Fail(id, "no prefab '" + args[0] + "'");
			return;
		}
		vec3 pos = plr.m_unit.GetPosition() + vec3(parseFloat(args[1]), parseFloat(args[2]), 0);
		pfb.Fabricate(g_scene, pos);
		Emit(Reply(id, true).Num("x", pos.x).Num("y", pos.y));
	}

	// ws <type> [commentPrefix]: every world script of that type whose comment
	// starts with the prefix: comment, enabled, trigger times, position, value (Variables)
	void VerbWs(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: ws <type> [commentPrefix]");
			return;
		}
		string prefix = args.length() > 1 ? args[1] : "";
		auto all = g_scene.FetchAllWorldScripts(args[0]);
		array<string> items;
		for (uint i = 0; i < all.length(); i++)
		{
			auto ws = all[i];
			string c = ws.GetComment();
			if (prefix != "" && c.findFirst(prefix) != 0)
				continue;
			Json e;
			vec3 pos = ws.GetUnit().GetPosition();
			e.Str("c", c).Bool("e", ws.IsEnabled()).Int("t", ws.GetTriggerTimes()).Num("x", pos.x).Num("y", pos.y);
			auto var = cast<WorldScript::Variable>(ws.GetUnit().GetScriptBehavior());
			if (var !is null)
				e.Int("v", var.GetValue());
			items.insertLast(e.Close());
		}
		Emit(Reply(id, true).Int("count", items.length()).Raw("scripts", RawArray(items)));
	}

	// usews <comment> [ifType ifComment]: IUsable.Use of the UseTrigger with that
	// comment; with a condition only while that other world script is enabled
	// (a static scenario can then press exactly the cells a random puzzle wants)
	void VerbUseWs(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null || args.length() < 1 || args.length() == 2)
		{
			Fail(id, plr is null ? "no spawned local player" : "usage: usews <comment> [ifType ifComment]");
			return;
		}
		if (args.length() >= 3)
		{
			auto cond = g_scene.FetchAllWorldScriptsWithComment(args[1], args[2]);
			if (cond.length() == 0)
			{
				Fail(id, "no " + args[1] + " '" + args[2] + "'");
				return;
			}
			if (!cond[0].IsEnabled())
			{
				Emit(Reply(id, true).Bool("used", false).Bool("condition", false));
				return;
			}
		}
		auto found = g_scene.FetchAllWorldScriptsWithComment("UseTrigger", args[0]);
		if (found.length() == 0)
		{
			Fail(id, "no UseTrigger '" + args[0] + "'");
			return;
		}
		auto usable = cast<IUsable>(found[0].GetUnit().GetScriptBehavior());
		if (usable is null)
		{
			Fail(id, "'" + args[0] + "' is not usable");
			return;
		}
		bool could = usable.CanUse(plr);
		if (could)
			usable.Use(plr);
		Emit(Reply(id, true).Bool("used", could).Bool("condition", true).Int("found", found.length()));
	}

	// goto <type> <comment> [dx dy]: the player to that world script's position + (dx, dy)
	void VerbGoto(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null || args.length() < 2)
		{
			Fail(id, plr is null ? "no spawned local player" : "usage: goto <type> <comment> [dx dy]");
			return;
		}
		auto found = g_scene.FetchAllWorldScriptsWithComment(args[0], args[1]);
		if (found.length() == 0)
		{
			Fail(id, "no " + args[0] + " '" + args[1] + "'");
			return;
		}
		vec3 to = found[0].GetUnit().GetPosition();
		if (args.length() >= 4)
			to += vec3(parseFloat(args[2]), parseFloat(args[3]), 0);
		vec3 p = plr.m_unit.GetPosition();
		plr.m_unit.SetPosition(to.x, to.y, p.z, true);
		vec3 q = plr.m_unit.GetPosition();
		Emit(Reply(id, true).Int("found", found.length()).Num("x", q.x).Num("y", q.y));
	}
}
