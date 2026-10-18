// gamelab-hands: verbs for the pet checks (gamelab/bots/plan_pets.py): click one row of a
// list whose rows have no id (the pet dye menu clones its rows with SetID("")), compare
// what the scene queries find around the player (PetWait's QueryCircle against the other
// fetches), and remove a unit (a pet gone missing). Each drives the game's own calls,
// never a screen coordinate. (A building's tier: buildup, Verbs_farming.as.)
namespace GameLab
{
	const uint PETS_CAP = 24;

	// presslist <widgetId> [index]: the visible interactable children of that widget in the
	// top window, in order (count and script types); with an index, click that one the way
	// press does (ClickDown + ClickUp, not using the mouse: the button's own OnFunc)
	void VerbPressList(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: presslist <widgetId> [index]");
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
		Widget@ parent = wnd.m_widget.GetWidgetById(args[0]);
		if (parent is null)
		{
			Fail(id, "no widget '" + args[0] + "' in " + Reflect::GetTypeName(wnd));
			return;
		}
		array<AInteractableWidget@> rows;
		array<string> types;
		if (parent.m_children !is null)
		{
			for (uint i = 0; i < parent.m_children.length(); i++)
			{
				auto iw = cast<AInteractableWidget>(parent.m_children[i]);
				if (iw is null || !iw.m_visible)
					continue;
				rows.insertLast(iw);
				types.insertLast(Reflect::GetTypeName(iw));
			}
		}
		if (args.length() < 2)
		{
			Emit(Reply(id, true).Str("window", Reflect::GetTypeName(wnd)).Int("count", rows.length()).Raw("types", StrArray(types)));
			return;
		}
		int k = int(parseInt(args[1]));
		if (k < 0 || k >= int(rows.length()))
		{
			Fail(id, "index " + k + " out of " + rows.length() + " rows");
			return;
		}
		auto pick = rows[k];
		string wtype = types[k];
		pick.ClickDown(false, vec2());
		pick.ClickUp(false, vec2());
		Emit(Reply(id, true).Str("window", Reflect::GetTypeName(wnd)).Int("count", rows.length()).Int("pressed", k)
			.Str("widget", wtype));
	}

	// the pets module's puzzle test (HWP::PetWait::IsPuzzleUnit), restated here: gamelab-hands
	// also loads without the pets module
	bool PetsPuzzlePath(const string &in path)
	{
		return path.findFirst("doodads/buttons/") == 0 || path.findFirst("puzzle") >= 0;
	}

	string PetsProducerName(UnitPtr u)
	{
		if (!u.IsValid())
			return "";
		auto prod = u.GetUnitProducer();
		if (prod is null)
			return "";
		return prod.GetResourceName();
	}

	// how many of units are of the unit file want (within radius of center; radius < 0: all)
	int PetsCountOf(array<UnitPtr>@ units, const string &in want, vec2 center, int radius)
	{
		int n = 0;
		if (units is null)
			return 0;
		for (uint i = 0; i < units.length(); i++)
		{
			if (!units[i].IsValid() || units[i].IsDestroyed())
				continue;
			if (radius >= 0 && dist(center, xy(units[i].GetPosition())) > radius)
				continue;
			if (PetsProducerName(units[i]) == want)
				n++;
		}
		return n;
	}

	// querycmp <radius> <unitFile>: read-only. How many units of that file each scene query
	// finds within radius of the player: QueryCircle with and without sensors (PetWait.NearPuzzle
	// asks with sensors), FetchAllUnits, FetchUnitsOfType, and FetchAllUnitsOfType (the whole
	// level, plus the nearest one's distance); then what QueryCircle with sensors returned
	// (distinct unit files, capped) and how many of those PetWait would call a puzzle unit.
	void VerbQueryCmp(const string &in id, array<string>@ args)
	{
		if (args.length() < 2)
		{
			Fail(id, "usage: querycmp <radius> <unitFile>");
			return;
		}
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		int radius = int(parseInt(args[0]));
		auto prod = Resources::GetUnitProducer(args[1]);
		if (prod is null)
		{
			Fail(id, "no unit '" + args[1] + "'");
			return;
		}
		string want = prod.GetResourceName();
		vec2 center = xy(plr.m_unit.GetPosition());
		auto sensors = g_scene.QueryCircle(center, radius, ~0, RaycastType::Any, true);
		auto solid = g_scene.QueryCircle(center, radius, ~0, RaycastType::Any, false);
		auto all = g_scene.FetchAllUnits(~0, center, radius);
		auto typed = g_scene.FetchUnitsOfType(prod, center, radius);
		auto level = g_scene.FetchAllUnitsOfType(prod);
		float nearest = -1;
		for (uint i = 0; i < level.length(); i++)
		{
			if (!level[i].IsValid() || level[i].IsDestroyed())
				continue;
			float d = dist(center, xy(level[i].GetPosition()));
			if (nearest < 0 || d < nearest)
				nearest = d;
		}
		array<string> seen;
		int puzzle = 0;
		for (uint i = 0; i < sensors.length(); i++)
		{
			string name = PetsProducerName(sensors[i]);
			if (PetsPuzzlePath(name))
				puzzle++;
			if (seen.find(name) < 0 && seen.length() < PETS_CAP)
				seen.insertLast(name);
		}
		Emit(Reply(id, true).Str("unit", want).Int("radius", radius)
			.Int("querySensors", PetsCountOf(sensors, want, center, -1))
			.Int("querySolid", PetsCountOf(solid, want, center, -1))
			.Int("fetchAll", PetsCountOf(all, want, center, radius))
			.Int("fetchType", PetsCountOf(typed, want, center, -1))
			.Int("levelType", PetsCountOf(level, want, center, -1)).Num("levelNearest", nearest)
			.Int("queryTotal", sensors.length()).Int("queryPuzzle", puzzle).Raw("queryUnits", StrArray(seen)));
	}

	// unitdestroy <radius> <filter>: UnitPtr.Destroy on every unit within radius of the player
	// (not the player) whose debug name contains filter: a pet gone missing, so the game's own
	// recovery (the Gold Collector vendor's Summon) can be tested. Capped.
	void VerbUnitDestroy(const string &in id, array<string>@ args)
	{
		if (args.length() < 2 || args[1].isEmpty())
		{
			Fail(id, "usage: unitdestroy <radius> <filter>");
			return;
		}
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		int radius = int(parseInt(args[0]));
		vec2 center = xy(plr.m_unit.GetPosition());
		auto units = g_scene.FetchAllUnits(~0, center, radius);
		array<string> gone;
		for (uint i = 0; i < units.length() && gone.length() < PETS_CAP; i++)
		{
			if (!units[i].IsValid() || units[i].IsDestroyed() || units[i] == plr.m_unit)
				continue;
			if (dist(center, xy(units[i].GetPosition())) > radius)
				continue;
			string name = units[i].GetDebugName();
			if (name.findFirst(args[1]) < 0)
				continue;
			gone.insertLast(name);
			units[i].Destroy();
		}
		Emit(Reply(id, true).Int("count", gone.length()).Raw("units", StrArray(gone)));
	}

	void Register_pets()
	{
		RegisterVerb("presslist", "<widgetId> [index]", Verb(VerbPressList));
		RegisterVerb("querycmp", "<radius> <unitFile>", Verb(VerbQueryCmp));
		RegisterVerb("unitdestroy", "<radius> <filter>", Verb(VerbUnitDestroy));
	}
}
