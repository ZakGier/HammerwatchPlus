// gamelab-hands: verbs for the UI plan checks (gamelab/bots/plan_ui.py). mouse pins the game
// mode's cursor (BaseGameMode.m_mice[0], what GetGameModeMousePosition and so HUD components
// read; posted OS mouse messages never reach the game) on a point or a buff bar icon; buffbar
// lists the buff bar; givebuff / givestacks put a buff or stacks on the local player the way
// a shrine / an AddStacks effect does; tintwatch records the multiply colour of every
// projectile seen for a while; shootproj fires one projectile unit; unitsof lists the units of
// a type (also ones FetchAllUnits misses: no solid collision, e.g. a minimap-only marker).
namespace GameLab
{
	const uint UI_CAP = 32;

	bool g_uiPinned = false;
	vec2 g_uiPin;          // UI units (window pixels / m_wndScale)
	string g_uiPinBuff;    // non-empty: follow this buff bar icon (icons shift as buffs come and go)

	// lang key -> text, as bufftips' Text: empty and the placeholder "title" mean no text
	string UiText(const string &in s)
	{
		if (s.isEmpty() || s == "title")
			return "";
		return s.substr(0, 1) == "." ? Resources::GetString(s) : s;
	}

	// the name key, name, description and kind of what a buff bar icon shows (as bufftips' Describe)
	string UiDescribe(IBuffWidgetInfo@ info, string &out key, string &out desc, string &out kind)
	{
		key = "";
		desc = "";
		kind = "";
		auto buff = cast<ActorBuff>(info);
		if (buff !is null && buff.m_def !is null)
		{
			kind = "buff";
			key = buff.m_def.m_name;
			desc = UiText(buff.m_def.m_description);
			return UiText(buff.m_def.m_name);
		}
		auto stacked = cast<ActorBuffStacked>(info);
		if (stacked !is null && stacked.m_def !is null)
		{
			kind = "stacks";
			key = stacked.m_def.m_name;
			string name = UiText(stacked.m_def.m_name);
			if (!name.isEmpty())
			{
				desc = UiText(stacked.m_def.m_desc);
				return name;
			}
			if (stacked.m_def.m_buffDef !is null)
			{
				key = stacked.m_def.m_buffDef.m_name;
				desc = UiText(stacked.m_def.m_buffDef.m_description);
				return UiText(stacked.m_def.m_buffDef.m_name);
			}
			return "";
		}
		auto skill = cast<Skills::Skill>(info);
		if (skill !is null)
		{
			kind = "skill";
			key = skill.m_name;
			return UiText(skill.m_name);
		}
		return "";
	}

	HUDBuffs@ UiBuffs()
	{
		auto hud = GetHUD();
		if (hud is null)
			return null;
		for (uint i = 0; i < hud.m_components.length(); i++)
		{
			auto buffs = cast<HUDBuffs>(hud.m_components[i]);
			if (buffs !is null)
				return buffs;
		}
		return null;
	}

	// the buff bar icons a cursor can be on (bufftips' Hovered walks the same ones)
	bool UiIconShown(BuffWidget@ w)
	{
		return w !is null && w.m_visible && w.m_buff !is null && w.m_buff.GetBuffIcon() !is null;
	}

	// the centre of a buff bar icon in UI units: the bar draws its widgets at (origin + offset) * m_scale
	// (HUDComponent.Draw; bufftips' hit test uses the same box)
	vec2 UiIconCentre(HUDBuffs@ buffs, BuffWidget@ w)
	{
		return (w.m_origin + vec2(w.m_width, w.m_height) * 0.5f + buffs.m_offset) * buffs.m_scale;
	}

	// the first shown icon matching m: its index among the bar's children, or a part of the name
	// key, the shown name or the kind
	BuffWidget@ UiFindIcon(HUDBuffs@ buffs, const string &in m)
	{
		if (buffs is null || buffs.m_wBuffList is null)
			return null;
		auto children = buffs.m_wBuffList.m_children;
		const string numerals = "0123456789";
		bool digits = m.length() > 0;
		for (uint c = 0; c < m.length(); c++)
			digits = digits && numerals.findFirst(m.substr(c, 1)) >= 0;
		for (uint i = 0; i < children.length(); i++)
		{
			auto w = cast<BuffWidget>(children[i]);
			if (!UiIconShown(w))
				continue;
			if (digits)
			{
				if (int(i) == parseInt(m))
					return w;
				continue;
			}
			string key, desc, kind;
			string name = UiDescribe(w.m_buff, key, desc, kind);
			if (key.findFirst(m) >= 0 || name.findFirst(m) >= 0 || kind == m)
				return w;
		}
		return null;
	}

	// every frame, paused or not (Modules::GameLabUiModule below), after BaseGameMode.UpdateMouse
	// wrote the OS cursor into m_mice: the next frame's UpdateWidgets (the HUD and its components)
	// runs before UpdateMouse and reads this
	void UiPinFrame()
	{
		if (!g_uiPinned)
			return;
		auto gm = cast<BaseGameMode>(g_gameMode);
		if (gm is null || gm.m_mice.length() == 0)
			return;
		if (!g_uiPinBuff.isEmpty())
		{
			auto buffs = UiBuffs();
			auto w = UiFindIcon(buffs, g_uiPinBuff);
			if (w !is null)
				g_uiPin = UiIconCentre(buffs, w);
		}
		vec2 p = g_uiPin * g_gameMode.m_wndScale;
		gm.m_mice[0].m_pos = p;
		gm.m_mice[0].m_posPrev = p;
	}

	Json@ UiMouseReply(const string &in id)
	{
		auto gm = cast<BaseGameMode>(g_gameMode);
		vec2 m = (gm is null || gm.m_mice.length() == 0) ? vec2(-1, -1) : gm.m_mice[0].m_pos / g_gameMode.m_wndScale;
		bool menu = gm !is null && gm.m_windowManager !is null && gm.m_windowManager.GetCurrentWindow() !is null;
		return Reply(id, true).Bool("pinned", g_uiPinned).Str("follow", g_uiPinBuff)
			.Num("x", g_uiPin.x).Num("y", g_uiPin.y).Num("mx", m.x).Num("my", m.y)
			.Num("wndW", g_gameMode.m_wndWidth).Num("wndH", g_gameMode.m_wndHeight).Num("scale", g_gameMode.m_wndScale)
			.Bool("menu", menu);
	}

	// mouse [x y | buff <match> | off]: pin the game mode cursor at UI point x y, or on the
	// centre of the first shown buff bar icon matching <match> (child index, or a part of the
	// name key / shown name, or the kind buff|stacks|skill), followed every frame; off lets the
	// OS cursor back. Replies with the pin, the cursor now (mx my, UI units; it lands next
	// frame), the window size in UI units, m_wndScale and whether a menu window is open.
	void VerbMouse(const string &in id, array<string>@ args)
	{
		if (args.length() >= 1 && args[0] == "off")
		{
			g_uiPinned = false;
			g_uiPinBuff = "";
		}
		else if (args.length() >= 2 && args[0] == "buff")
		{
			auto buffs = UiBuffs();
			auto w = UiFindIcon(buffs, args[1]);
			if (w is null)
			{
				Fail(id, "no shown buff bar icon matching '" + args[1] + "'");
				return;
			}
			g_uiPin = UiIconCentre(buffs, w);
			g_uiPinBuff = args[1];
			g_uiPinned = true;
		}
		else if (args.length() >= 2)
		{
			g_uiPin = vec2(parseFloat(args[0]), parseFloat(args[1]));
			g_uiPinBuff = "";
			g_uiPinned = true;
		}
		Emit(UiMouseReply(id));
	}

	// buffbar: the HUD buff bar (HUDBuffs.m_wBuffList, child 0 is the shadow curse counter): per
	// icon its child index, kind, name key, shown name and description (resolved as bufftips
	// does), debuff, ms left / max, stack count, shown, centre and size in UI units; the bar's
	// scale and visibility, the HUD component types (HWPBuffTipsHUD when bufftips is on) and the
	// cursor as mouse reports it.
	void VerbBuffBar(const string &in id, array<string>@ args)
	{
		auto buffs = UiBuffs();
		if (buffs is null || buffs.m_wBuffList is null)
		{
			Fail(id, "no HUD buff bar");
			return;
		}
		array<string> items;
		auto children = buffs.m_wBuffList.m_children;
		for (uint i = 1; i < children.length() && items.length() < UI_CAP; i++)
		{
			auto w = cast<BuffWidget>(children[i]);
			if (w is null || w.m_buff is null)
				continue;
			string key, desc, kind;
			string name = UiDescribe(w.m_buff, key, desc, kind);
			vec2 c = UiIconCentre(buffs, w);
			Json e;
			e.Int("i", i).Str("kind", kind).Str("key", key).Str("name", name).Str("desc", desc)
				.Bool("debuff", w.m_buff.IsDebuff()).Int("left", w.m_buff.GetBuffIconDuration())
				.Int("max", w.m_buff.GetBuffIconMaxDuration()).Int("count", w.m_buff.GetBuffIconCount())
				.Bool("shown", UiIconShown(w)).Num("x", c.x).Num("y", c.y)
				.Num("w", w.m_width * buffs.m_scale).Num("h", w.m_height * buffs.m_scale);
			items.insertLast(e.Close());
		}
		array<string> comps;
		auto hud = GetHUD();
		for (uint i = 0; hud !is null && i < hud.m_components.length(); i++)
			comps.insertLast(Reflect::GetTypeName(hud.m_components[i]));
		Emit(UiMouseReply(id).Bool("visible", buffs.IsVisible()).Num("barScale", buffs.m_scale)
			.Raw("icons", RawArray(items)).Raw("components", StrArray(comps)));
	}

	// givebuff <buffPath> [ms] [icon]: ApplyBuff(ActorBuff(player, def, 1, false, 0, ms)) on the
	// local player, as a shrine does (WorldScript/Shrine.as:157); ms -1 or left out keeps the
	// def's duration. "icon" applies a private copy of the def (own path hash) with the damage
	// shrine buff's HUD icon: vanilla debuffs have no "hud" sprite, so they never reach the
	// buff bar; the copy lets a test hover one. Replies with what ApplyBuff returned.
	void VerbGiveBuff(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: givebuff <buffPath> [ms] [icon]");
			return;
		}
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		ActorBuffDef@ def = LoadActorBuff(args[0]);
		if (def is null)
		{
			Fail(id, "no buff '" + args[0] + "'");
			return;
		}
		int ms = args.length() > 1 ? int(parseInt(args[1])) : -1;
		bool icon = args.length() > 2 && args[2] == "icon";
		if (icon)
		{
			SValue@ sv = Resources::GetSValue(HashString(args[0]));
			auto donor = LoadActorBuff("tweak/buffs/shrine_buffs.sval:damage");
			if (sv is null || donor is null || donor.m_hud is null)
			{
				Fail(id, "no sval or donor icon for '" + args[0] + "'");
				return;
			}
			@def = ActorBuffDef(HashString("gamelab-ui:" + args[0]), sv);
			@def.m_hud = donor.m_hud;
		}
		bool applied = plr.ApplyBuff(ActorBuff(plr, def, 1.0f, false, 0, ms));
		Emit(Reply(id, true).Bool("applied", applied).Str("key", def.m_name).Str("name", UiText(def.m_name))
			.Bool("debuff", def.m_debuff).Bool("hud", def.m_hud !is null).Int("dur", def.m_duration).Int("ms", ms));
	}

	// givestacks <stackId> <n>: Actor.AddStacks(player, ActorBuffStackDef::Get(id), n) on the local
	// player, as an AddStacks effect with target-self does (Behaviors/Effects/AddStacks.as:80);
	// id as in svals, e.g. players/paladin/stacks_paladin.sval:inner_flame. Replies with GetStacks.
	void VerbGiveStacks(const string &in id, array<string>@ args)
	{
		if (args.length() < 2)
		{
			Fail(id, "usage: givestacks <stackId> <n>");
			return;
		}
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		auto def = ActorBuffStackDef::Get(args[0]);
		if (def is null)
		{
			Fail(id, "no stack buff '" + args[0] + "'");
			return;
		}
		bool added = plr.AddStacks(plr, def, int(parseInt(args[1])));
		Emit(Reply(id, true).Bool("added", added).Int("stacks", plr.GetStacks(def)));
	}

	// the projectile classes: vanilla's and the colors module's swaps (mods/colors module.json)
	array<string> UI_PROJ_CLASSES = { "NewProjectile", "RayProjectile", "BeamProjectile",
		"HWPNewProjectile", "HWPRayProjectile", "HWPBeamProjectile" };

	string UiColorJson(vec4 c)
	{
		Json j;
		return j.Num("r", c.x).Num("g", c.y).Num("b", c.z).Num("a", c.w).Close();
	}

	string UiProjJson(UnitPtr u, IProjectile@ p, int t)
	{
		Actor@ owner = p.GetOwner();
		bool friendly = owner !is null && GetPlayerOwner(owner) !is null;
		ref@ b = u.GetScriptBehavior();
		Json e;
		e.Int("unit", u.GetId()).Str("name", u.GetDebugName()).Str("behavior", b is null ? "" : Reflect::GetTypeName(b))
			.Str("owner", owner is null ? "" : owner.m_unit.GetDebugName()).Bool("friendly", friendly)
			.Int("t", t).Raw("color", UiColorJson(u.GetMultiplyColor()));
		return e.Close();
	}

	// first sight of every projectile unit in the level (by behavior class, so sensor-only
	// projectiles count too): unit, .unit path, behavior type, owner, friendly as colors decides
	// it (owner is a player or player-owned: GetPlayerOwner), the multiply colour then
	class TintWatchTask : QueuedTasks::UpdatingTask
	{
		string m_tag;
		int m_msLeft;
		int m_t = 0;
		int m_truncated = 0;
		array<int> m_ids;
		array<string> m_items;

		bool UpdateFrame(int ms) override
		{
			m_t += ms;
			m_msLeft -= ms;
			for (uint k = 0; k < UI_PROJ_CLASSES.length(); k++)
			{
				auto units = g_scene.FetchAllUnitsWithBehavior(UI_PROJ_CLASSES[k]);
				for (uint i = 0; i < units.length(); i++)
				{
					if (!units[i].IsValid() || units[i].IsDestroyed())
						continue;
					int uid = units[i].GetId();
					if (m_ids.find(uid) >= 0)
						continue;
					auto p = cast<IProjectile>(units[i].GetScriptBehavior());
					if (p is null)
						continue;
					if (m_ids.length() >= UI_CAP)
					{
						m_truncated++;
						continue;
					}
					m_ids.insertLast(uid);
					m_items.insertLast(UiProjJson(units[i], p, m_t));
				}
			}
			if (m_msLeft > 0)
				return false;
			Json j;
			Emit(j.Str("ev", "tintwatch").Str("tag", m_tag).Int("ms", m_t).Int("truncated", m_truncated)
				.Raw("projectiles", RawArray(m_items)));
			return true;
		}
	}

	// tintwatch <tag> <ms>: read-only. For ms of gameplay frames, the first sight of every
	// projectile (see TintWatchTask), then one {"ev":"tintwatch","tag":...} event. A QueuedTasks
	// updating task, so only while a gameplay module ticks unpaused. Capped at UI_CAP projectiles.
	void VerbTintWatch(const string &in id, array<string>@ args)
	{
		if (args.length() < 2)
		{
			Fail(id, "usage: tintwatch <tag> <ms>");
			return;
		}
		if (QueuedTasks::g_instance is null)
		{
			Fail(id, "no QueuedTasks module");
			return;
		}
		TintWatchTask task;
		task.m_tag = args[0];
		task.m_msLeft = int(parseInt(args[1]));
		QueuedTasks::Queue(task);
		Emit(Reply(id, true).Str("tag", task.m_tag).Int("ms", task.m_msLeft));
	}

	// shootproj <unitFile> <me|none> [dx dy]: what ShootProjectile does with one projectile
	// (Behaviors/Actions/ShootProjectile.as:131-142): Produce the unit 20 units from the player
	// along (dx, dy) (default 1 0), IProjectile.Initialize(owner, ProjectileTargetDir(dir), 1,
	// false, 0), owner the local player or none (a trap's shot). Replies with the behavior type
	// and the unit's multiply colour right after.
	void VerbShootProj(const string &in id, array<string>@ args)
	{
		if (args.length() < 2)
		{
			Fail(id, "usage: shootproj <unitFile> <me|none> [dx dy]");
			return;
		}
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		auto prod = Resources::GetUnitProducer(args[0]);
		if (prod is null)
		{
			Fail(id, "no unit '" + args[0] + "'");
			return;
		}
		vec2 dir = vec2(1, 0);
		if (args.length() >= 4)
			dir = vec2(parseFloat(args[2]), parseFloat(args[3]));
		if (length(dir) < 0.001f)
			dir = vec2(1, 0);
		dir = normalize(dir);
		Actor@ owner = null;
		if (args[1] == "me")
			@owner = plr;
		UnitPtr u = prod.Produce(g_scene, xyz(xy(plr.m_unit.GetPosition()) + dir * 20.0f));
		if (!u.IsValid())
		{
			Fail(id, "'" + args[0] + "' produced nothing");
			return;
		}
		auto p = cast<IProjectile>(u.GetScriptBehavior());
		if (p is null)
		{
			u.Destroy();
			Fail(id, "'" + args[0] + "' is not a projectile");
			return;
		}
		p.Initialize(owner, ProjectileTargetDir(dir), 1.0f, false, 0);
		Emit(Reply(id, true).Raw("projectile", UiProjJson(u, p, 0)));
	}

	// unitsof <unitFile...>: Scene.FetchAllUnitsOfType for each .unit file: id, position, hidden,
	// per file and capped at UI_CAP each. Finds units without solid collision too (a minimap-only
	// marker), which near's FetchAllUnits misses.
	void VerbUnitsOf(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: unitsof <unitFile...>");
			return;
		}
		Json@ r = Reply(id, true);
		for (uint a = 0; a < args.length(); a++)
		{
			auto prod = Resources::GetUnitProducer(args[a]);
			array<string> items;
			int n = 0;
			if (prod !is null)
			{
				auto units = g_scene.FetchAllUnitsOfType(prod);
				for (uint i = 0; i < units.length(); i++)
				{
					if (!units[i].IsValid() || units[i].IsDestroyed())
						continue;
					n++;
					if (items.length() >= UI_CAP)
						continue;
					vec3 pos = units[i].GetPosition();
					Json e;
					e.Int("unit", units[i].GetId()).Num("x", pos.x).Num("y", pos.y).Bool("hidden", units[i].IsHidden());
					items.insertLast(e.Close());
				}
			}
			Json f;
			f.Bool("found", prod !is null).Int("count", n).Raw("units", RawArray(items));
			r.Raw(args[a], f.Close());
		}
		Emit(r);
	}

	// what walking onto a pickup does: its own Collide handler, with the local player as the unit
	void VerbPickup(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: pickup <unitId>");
			return;
		}
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		UnitPtr u = g_scene.GetUnit(int(parseInt(args[0])));
		if (!u.IsValid() || u.IsDestroyed())
		{
			Fail(id, "no unit " + args[0]);
			return;
		}
		auto p = cast<Pickup>(u.GetScriptBehavior());
		if (p is null)
		{
			Fail(id, "unit " + args[0] + " is not a Pickup");
			return;
		}
		bool was = p.m_visible;
		p.Collide(plr.m_unit, xy(u.GetPosition()), vec2());
		Json@ r = Reply(id, true);
		r.Int("unit", u.GetId()).Bool("wasVisible", was).Bool("visible", p.m_visible)
			.Bool("destroyed", !u.IsValid() || u.IsDestroyed());
		Emit(r);
	}

	void Register_ui()
	{
		RegisterVerb("mouse", "[x y | buff <match> | off]", Verb(VerbMouse));
		RegisterVerb("buffbar", "", Verb(VerbBuffBar));
		RegisterVerb("givebuff", "<buffPath> [ms] [icon]", Verb(VerbGiveBuff));
		RegisterVerb("givestacks", "<stackId> <n>", Verb(VerbGiveStacks));
		RegisterVerb("tintwatch", "<tag> <ms>", Verb(VerbTintWatch));
		RegisterVerb("shootproj", "<unitFile> <me|none> [dx dy]", Verb(VerbShootProj));
		RegisterVerb("unitsof", "<unitFile...>", Verb(VerbUnitsOf));
		RegisterVerb("pickup", "<unitId>", Verb(VerbPickup));
	}
}

namespace Modules
{
	// made automatically per game mode (Modules::MakeModules); keeps the mouse pin every frame,
	// paused frames included (AGameplayGameMode.UpdatePausedFrame ticks modules with paused true)
	class GameLabUiModule : Module
	{
		GameLabUiModule()
		{
			super("gamelab-ui");
		}

		void UpdateFrame(int ms, GameInput& gameInput, MenuInput& menuInput, bool paused) override
		{
			GameLab::UiPinFrame();
		}
	}
}
