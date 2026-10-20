// gamelab-hands: fixture verbs for a full character build (the fixture recipes' "setup").
// Each calls the function the game itself calls for the same change; the recipe reads every
// field back through `inspect player <key>` (MECHANICS.md section 8, the run-state schema).
namespace GameLab
{
	PlayerRecord@ FixtureRecord(const string &in id)
	{
		auto rec = GetLocalPlayerRecord();
		if (rec is null || rec.playerClass is null)
		{
			Fail(id, "no local character");
			return null;
		}
		return rec;
	}

	// xp <amount>: PlayerRecord.GiveExperience (kills, mission rewards), gain modifiers skipped
	void VerbXp(const string &in id, array<string>@ args)
	{
		auto rec = FixtureRecord(id);
		if (rec is null)
			return;
		if (args.length() < 1)
		{
			Fail(id, "usage: xp <amount>");
			return;
		}
		int ret = rec.GiveExperience(int(parseInt(args[0])), true);
		rec.RefreshStats();
		Emit(Reply(id, true).Int("returned", ret).Int("level", rec.level).Int("xp", rec.experience));
	}

	// material <gold|wood|stone|iron|crystals|dust|ore|all> <n>: PlayerRecord.GiveMaterial with skipGainMod, like cht_give_material: the amount lands as given (a pickup applies the gain modifiers: GetMaterialModifier). "all" gives n of each.
	void VerbMaterial(const string &in id, array<string>@ args)
	{
		auto rec = FixtureRecord(id);
		if (rec is null)
			return;
		array<string> names = { "gold", "wood", "stone", "iron", "crystals", "dust", "ore" };
		int type = args.length() > 0 ? names.find(args[0]) : -1;
		if ((type < 0 && (args.length() == 0 || args[0] != "all")) || args.length() < 2)
		{
			Fail(id, "usage: material <" + join(names, "|") + "|all> <n>");
			return;
		}
		if (type < 0)
		{
			for (uint i = 0; i < names.length(); i++)
				rec.GiveMaterial(MaterialType(i), int(parseInt(args[1])), true);
			Emit(Reply(id, true).Str("material", "all").Int("gold", rec.GetMaterial(MaterialType(0))));
			return;
		}
		int got = rec.GiveMaterial(MaterialType(type), int(parseInt(args[1])), true);
		Emit(Reply(id, true).Str("material", args[0]).Int("given", got).Int("now", rec.GetMaterial(MaterialType(type))));
	}

	// e_cheats on, a bool or an int cvar (the engine allows it in modded games; lab saves only)
	void SetCheats(bool on)
	{
		if (GetVarType("e_cheats") == cvar_type::Bool)
			SetVar("e_cheats", on);
		else
			SetVar("e_cheats", on ? 1 : 0);
	}

	bool CheatsOn()
	{
		return GetVarType("e_cheats") == cvar_type::Bool ? GetVarBool("e_cheats") : GetVarInt("e_cheats") != 0;
	}

	// cheats [on|off]: the e_cheats cvar, as typing "e_cheats 1" does. Character creation turns it
	// off again, so a setup sets it after the character is in town.
	void VerbCheats(const string &in id, array<string>@ args)
	{
		SetCheats(args.length() == 0 || args[0] != "off");
		Emit(Reply(id, true).Bool("cheats", CheatsOn()));
	}

	// levelup <n>: n levels' worth of experience through PlayerRecord.GiveExperience, gain
	// modifiers skipped, as core's "hwp levelup" (mods/core/scripts/HWP/Core/Cheats.as:89-102)
	void VerbLevelup(const string &in id, array<string>@ args)
	{
		auto rec = FixtureRecord(id);
		if (rec is null)
			return;
		int levels = args.length() > 0 ? max(1, int(parseInt(args[0]))) : 1;
		for (int i = 0; i < levels; i++)
			rec.GiveExperience(rec.LevelExperience(rec.level) - rec.LevelExperience(rec.level - 1), true);
		rec.RefreshStats();
		Emit(Reply(id, true).Int("level", rec.level));
	}

	// ngp <n>: the character's New Game+ level (PlayerRecord.ngp), as clearing the final floor
	// raises it: the level cap becomes Tweak::LevelCap + n * LevelCapNGPAdd (GetLevelCap) and
	// every attribute gains n * Tweak::AttributesPerNGP (Modifiers.as stats). levelup stops at
	// the cap, so a level 25 build needs ngp 1 first.
	void VerbNgp(const string &in id, array<string>@ args)
	{
		auto rec = FixtureRecord(id);
		if (rec is null)
			return;
		if (args.length() < 1)
		{
			Fail(id, "usage: ngp <n>");
			return;
		}
		rec.ngp = max(0, int(parseInt(args[0])));
		rec.RefreshStats();
		auto plr = cast<PlayerBase>(rec.actor);
		if (plr !is null)
			plr.RefreshModifiers();
		int now = rec.ngp;
		Emit(Reply(id, true).Int("ngp", now).Int("cap", rec.GetLevelCap()));
	}

	// points <skill|stat> <n>: bonus skill or attribute points (PlayerRecord.bonusSkillPts /
	// bonusStatPts, then SyncStatPoints), as core's "hwp skillpoints" and "hwp statpoints"
	// (mods/core/scripts/HWP/Core/Cheats.as:119-146)
	void VerbPoints(const string &in id, array<string>@ args)
	{
		auto rec = FixtureRecord(id);
		if (rec is null)
			return;
		if (args.length() < 2 || (args[0] != "skill" && args[0] != "stat"))
		{
			Fail(id, "usage: points <skill|stat> <n>");
			return;
		}
		int n = int(parseInt(args[1]));
		if (args[0] == "skill")
			rec.bonusSkillPts += n;
		else
			rec.bonusStatPts += n;
		rec.SyncStatPoints();
		auto actor = cast<PlayerBase>(rec.actor);
		if (actor !is null)
			actor.RefreshModifiers();
		Emit(Reply(id, true).Int("skillFree", rec.GetFreeSkillPoints()).Int("statFree", rec.GetPlaceableStatPoints()));
	}

	const uint SETUP_FAILED_CAP = 8;

	// setup <file>: one typed line for a whole hand-play setup. Runs each line of the file (an
	// sval array of verb lines, e.g. gamelab/setup_demo_firearms.sval) in this frame, as multi
	// does, the k-th replying under "<id>.<k>". The reply counts the lines and names the failed
	// ones (at most SETUP_FAILED_CAP, "truncated" past that); ok is false when any failed.
	void VerbSetup(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: setup <file>");
			return;
		}
		SValue@ sv = Resources::GetSValue(args[0]);
		if (sv is null || sv.GetType() != SValueType::Array)
		{
			Fail(id, "no sval array '" + args[0] + "'");
			return;
		}
		auto lines = sv.GetArray();
		array<string> failed;
		uint nFailed = 0;
		for (uint k = 0; k < lines.length(); k++)
		{
			array<string> words;
			auto parts = strTrim(lines[k].GetString()).split(" ");
			for (uint i = 0; i < parts.length(); i++)
			{
				if (parts[i].length() > 0)
					words.insertLast(parts[i]);
			}
			if (words.length() == 0)
				continue;
			string verb = words[0];
			words.removeAt(0);
			uint before = g_fails;
			if (verb == "setup" || verb == "multi")
				Fail(id + "." + k, verb + " does not nest in setup");
			else
				RunVerb(id + "." + k, verb, words);
			if (g_fails != before)
			{
				nFailed++;
				if (failed.length() < SETUP_FAILED_CAP)
					failed.insertLast("" + k + ": " + verb);
			}
		}
		Emit(Reply(id, nFailed == 0).Int("n", lines.length()).Int("failed", nFailed)
			.Str("failedLines", join(failed, ", ")).Bool("truncated", nFailed > failed.length()));
	}

	// charflag <name>: PlayerRecord.SetCharFlag (mission rewards set these)
	void VerbCharFlag(const string &in id, array<string>@ args)
	{
		auto rec = FixtureRecord(id);
		if (rec is null)
			return;
		if (args.length() < 1)
		{
			Fail(id, "usage: charflag <name>");
			return;
		}
		rec.SetCharFlag(HashString(args[0]), true);
		Emit(Reply(id, true).Str("flag", args[0]).Int("hash", HashString(args[0])));
	}

	// subclass <classId>: PlayerRecord.ChangeClass, what the subclass picker's switch does
	// (Town/SubclassPickShopContent.as:131-140). Only a subclass of the current class (or the
	// parent itself) is taken; the picker's level gate is skipped.
	void VerbSubclass(const string &in id, array<string>@ args)
	{
		auto rec = FixtureRecord(id);
		if (rec is null)
			return;
		if (args.length() < 1)
		{
			Fail(id, "usage: subclass <classId>");
			return;
		}
		auto cls = PlayerClass::Get(args[0]);
		if (cls is null)
		{
			Fail(id, "no class " + args[0]);
			return;
		}
		uint root = rec.playerClass.parent != 0 ? rec.playerClass.parent : rec.playerClass.m_idHash;
		if (cls.m_idHash != root && cls.parent != root)
		{
			Fail(id, args[0] + " is not a subclass of " + rec.playerClass.m_id);
			return;
		}
		rec.ChangeClass(cls);
		Emit(Reply(id, true).Str("class", rec.playerClass.m_id));
	}

	// the Skills::TargetingMode of a level-1 skill built from the def the way the picker's
	// MakeSkillTemp builds one (Town/SubclassPickShopContent.as:107-129); -1 when none builds
	int DefMode(PlayerSkillDef@ def)
	{
		if (def.m_levelParams.length() == 0 || def.m_levelParams[0] is null)
			return -1;
		auto@ skillParams = def.m_levelParams[0];
		array<SValue@>@ p = { @skillParams };
		UnitPtr u;
		string c = GetParamString(u, p, "class"); // the 3-argument array form MakeSkillTemp uses
		auto skill = cast<Skills::Skill>(InstantiateClass(c, u, skillParams));
		if (skill is null)
			return -1;
		skill.Initialize(null, u, p, def.m_idHash);
		return int(skill.GetTargetingMode());
	}

	// classskills <classId>: the class's skill defs as PlayerClass loaded them, in class order:
	// id, the shown name (Resources::GetString of m_name), m_type (PlayerSkillType; a passive
	// def is a Spell too, PlayerClass.as:91-92), inherited (its parent class has the same
	// def), mode (DefMode) and passive (mode 0, TargetingMode::Passive: no button, the
	// GetSkillInput / HUDPlayer test). What the Subclass Picker's skill row is checked
	// against (core SubclassPick.as).
	void VerbClassSkills(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: classskills <classId>");
			return;
		}
		auto cls = PlayerClass::Get(args[0]);
		if (cls is null)
		{
			Fail(id, "no class " + args[0]);
			return;
		}
		PlayerClass@ parent = null;
		if (cls.parent != 0)
			@parent = PlayerClass::Get(cls.parent);
		array<string> items;
		for (uint i = 0; i < cls.m_skillDefs.length(); i++)
		{
			auto def = cls.m_skillDefs[i];
			if (def is null)
				continue;
			bool inherited = false;
			for (uint k = 0; parent !is null && k < parent.m_skillDefs.length(); k++)
			{
				if (parent.m_skillDefs[k].m_idHash == def.m_idHash)
					inherited = true;
			}
			int mode = DefMode(def);
			Json j;
			j.Str("id", def.m_id).Str("name", Resources::GetString(def.m_name)).Int("type", int(def.m_type))
				.Bool("inherited", inherited).Int("mode", mode)
				.Bool("passive", mode == int(Skills::TargetingMode::Passive));
			items.insertLast(j.Close());
		}
		Emit(Reply(id, true).Str("class", cls.m_id).Str("name", Resources::GetString(cls.m_name))
			.Str("parent", parent is null ? "" : parent.m_id).Raw("skills", RawArray(items)));
	}

	// skill <skillId> [times] [combo]: PlayerRecord.SkillUp, what the skill tree's level-up
	// calls (it checks max level and free points; `hwp skillpoints` gives points). "combo"
	// picks a combo skill (SkillUp(id, true), e.g. combo_kills). The reply has the level
	// GetSkillLevel reports after.
	void VerbSkill(const string &in id, array<string>@ args)
	{
		auto rec = FixtureRecord(id);
		if (rec is null)
			return;
		if (args.length() < 1)
		{
			Fail(id, "usage: skill <skillId> [times] [combo]");
			return;
		}
		int times = args.length() > 1 ? int(parseInt(args[1])) : 1;
		bool combo = args.length() > 2 && args[2] == "combo";
		int done = 0;
		for (int i = 0; i < times; i++)
			if (rec.SkillUp(args[0], combo))
				done++;
		auto def = rec.playerClass.GetSkillDef(HashString(args[0]));
		if (def is null)
			@def = PlayerSkillDef::Get(args[0]);
		if (def is null)
		{
			Fail(id, "no skill " + args[0] + " in " + rec.playerClass.m_id);
			return;
		}
		Emit(Reply(id, done == times).Str("skill", args[0]).Int("raised", done).Int("level", rec.GetSkillLevel(def)));
	}

	// kill <radius> <filter> [hp]: Actor.Kill(null, 0) on every live actor within radius whose
	// .unit path or behavior type contains filter (as `near`), or with "tag:<tag>" that has
	// the actor tag (tag:elite, tag:boss), never the local player.
	// A real death: the unit's own death handling runs (summons leave the owner's list).
	// With hp (0-1) the actors are set to that health fraction instead of killed. With "me"
	// the local player is the killer (kill hooks and drops run; friendly actors are skipped).
	void VerbKill(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		if (args.length() < 2)
		{
			Fail(id, "usage: kill <radius> <filter>");
			return;
		}
		int radius = int(parseInt(args[0]));
		// "me": the local player is the killer, so the kill hooks run (Kill -> OnDeath ->
		// KilledActor -> PlayerKilledActor: CompositeActorBehavior.as:576-580, 870-871)
		bool byMe = args.length() > 2 && args[2] == "me";
		float hp = args.length() > 2 && !byMe ? float(parseFloat(args[2])) : -1.0f;
		array<string> names;
		vec2 center = xy(plr.m_unit.GetPosition());
		auto units = g_scene.FetchAllUnits(~0, center, radius);
		int n = 0;
		for (uint i = 0; i < units.length(); i++)
		{
			if (!units[i].IsValid() || units[i].IsDestroyed() || units[i] == plr.m_unit)
				continue;
			if (dist(center, xy(units[i].GetPosition())) > radius)
				continue;
			auto actor = cast<Actor>(units[i].GetScriptBehavior());
			if (actor is null || actor.IsDead())
				continue;
			if (args[1].findFirst("tag:") == 0)
			{
				// an actor tag (elite, boss, ...): the bitmask the game's own checks test
				if ((actor.Tags & ApplyTag(0, g_actorTags.GetTag(args[1].substr(4)))) == 0)
					continue;
			}
			else if (units[i].GetDebugName().findFirst(args[1]) < 0 && Reflect::GetTypeName(actor).findFirst(args[1]) < 0)
				continue;
			if (byMe && actor.Team == g_team_player)
				continue;
			if (hp < 0)
			{
				actor.Kill(byMe ? cast<Actor>(plr) : null, 0);
				if (names.length() < 40)
					names.insertLast(units[i].GetDebugName());
			}
			else
			{
				// not a game code path: the health fraction is written directly (the HP a
				// save or a floor change carries is this same m_hp: CompositeActorBehavior.as:375-413)
				auto comp = cast<CompositeActorBehavior>(actor);
				if (comp is null)
					continue;
				comp.m_hp = hp;
			}
			n++;
		}
		Emit(Reply(id, n > 0).Int(hp < 0 ? "killed" : "hurt", n).Raw("names", StrArray(names)));
	}

	// abort [failed]: leave the run the way the pause menu's abandon does: it sets GlobalCache
	// "main_restart", which HWR2GameMode.UpdateFrame turns into
	// MissionManager::AbortMission(Aborted) and a change to the town (GameModes/HWR2GameMode.as:187-192).
	// "failed" ends it the way the death screen's accept does: AbortMission(Failed) (GUI/DeadMenu.as:89).
	void VerbAbort(const string &in id, array<string>@ args)
	{
		if (cast<MissionGameModeBase>(g_gameMode) is null)
		{
			Fail(id, "not in a run");
			return;
		}
		bool failed = args.length() > 0 && args[0] == "failed";
		if (failed)
			MissionManager::AbortMission(MissionManager::MissionState::Failed);
		else
			GlobalCache::Set("main_restart", "1");
		Emit(Reply(id, true).Str("state", failed ? "failed" : "aborted"));
	}

	// combo: Player.GiveCombo, the game's own "enter combo now" (vanilla effects call it):
	// combo count +1, PlayerSyncCombo to all, the Combo modifier triggers.
	void VerbCombo(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null)
		{
			Fail(id, "no spawned local player");
			return;
		}
		plr.GiveCombo();
		Emit(Reply(id, plr.m_comboActive).Bool("combo", plr.m_comboActive));
	}

	// equip <baseItemId> <qualityMask> [ilvl]: Equipment::Generator.GenerateItem (the
	// spawnequipment cheat's path, Console/Cheats.as), then equipped.Equip like a new
	// character's starting gear (PlayerRecord.as:451-465). The quality is the generator's:
	// its RollQuality tests `mask & Common != 0`, which binds as `mask & (Common != 0)`, so
	// a mask without the Common bit rolls nothing and the base item's quality is used
	// (EquipmentGenerator.as:15; measured fixture-ranger 20261017-151727: rare asked, 2 given).
	// The reply carries the quality actually given. Equip refusing (MayEquip: level or
	// attribute requirements) returns the item itself, and fails the verb.
	void VerbEquip(const string &in id, array<string>@ args)
	{
		auto rec = FixtureRecord(id);
		if (rec is null)
			return;
		if (args.length() < 2)
		{
			Fail(id, "usage: equip <baseItemId> <quality> [ilvl]");
			return;
		}
		auto baseItem = Equipment::BaseItem::Get(args[0]);
		if (baseItem is null)
		{
			Fail(id, "no base item '" + args[0] + "'");
			return;
		}
		Equipment::Generator gen;
		gen.m_ilvl = args.length() > 2 ? int(parseInt(args[2])) : rec.level;
		gen.m_qualities = Item::ParseQuality(args[1]);
		auto item = gen.GenerateItem(baseItem);
		if (item is null)
		{
			Fail(id, "GenerateItem returned null for " + args[0] + " " + args[1]);
			return;
		}
		auto unequipped = rec.equipped.Equip(item);
		if (unequipped is item)
		{
			Fail(id, "equipped.Equip refused " + args[0] + " (MayEquip: requirements; character level " + rec.level + ", ilvl " + gen.m_ilvl + ")");
			return;
		}
		if (unequipped !is null)
			rec.equipInventory.Add(unequipped);
		rec.RefreshStats();
		auto plr = cast<PlayerBase>(rec.actor);
		if (plr !is null)
			plr.RefreshModifiers();
		Emit(Reply(id, true).Str("item", args[0]).Int("quality", int(item.quality)).Int("ilvl", gen.m_ilvl)
			.Bool("replaced", unequipped !is null));
	}

	// assign <str|dex|int|foc|vit> <n|all>: the attribute assigner's Buy("assign")
	// (Town/AttributeAssignerShopContent.as:10-31), once per point, while points are placeable
	void VerbAssign(const string &in id, array<string>@ args)
	{
		auto rec = FixtureRecord(id);
		if (rec is null)
			return;
		array<string> names = { "str", "dex", "int", "foc", "vit" };
		int stat = args.length() > 0 ? names.find(args[0]) : -1;
		if (stat < 0 || args.length() < 2)
		{
			Fail(id, "usage: assign <" + join(names, "|") + "> <n|all>");
			return;
		}
		int want = args[1] == "all" ? 100000 : int(parseInt(args[1]));
		int placed = 0;
		while (placed < want && rec.GetPlaceableStatPoints() > 0)
		{
			if (stat == 0) rec.pickedStr++;
			else if (stat == 1) rec.pickedDex++;
			else if (stat == 2) rec.pickedInt++;
			else if (stat == 3) rec.pickedFoc++;
			else rec.pickedVit++;
			placed++;
		}
		rec.SyncStatPoints();
		rec.RefreshModifiers();
		rec.RefreshStats();
		if (args[1] != "all" && placed < want)
		{
			Fail(id, "only " + placed + " of " + want + " points were placeable");
			return;
		}
		Emit(Reply(id, true).Str("stat", args[0]).Int("placed", placed).Int("left", rec.GetPlaceableStatPoints())
			.Int("dex", rec.currStats.Dex));
	}

	// upgrade <shopId> <upgradeId> <step>: what an upgrade shop's Buy("buy") does
	// (Town/UpgradeShop.as:139-150: SetShopUpgradeLevel, RefreshModifiers) minus the cost;
	// e.g. upgrade apothecary potion-charges 0 = the first potion charge
	void VerbUpgrade(const string &in id, array<string>@ args)
	{
		auto rec = FixtureRecord(id);
		if (rec is null)
			return;
		if (args.length() < 3)
		{
			Fail(id, "usage: upgrade <shopId> <upgradeId> <step>");
			return;
		}
		auto shop = UpgradeShop::Get(args[0]);
		if (shop is null)
		{
			Fail(id, "no upgrade shop '" + args[0] + "'");
			return;
		}
		int step = int(parseInt(args[2]));
		bool found = false;
		for (uint i = 0; i < shop.m_upgrades.length() && !found; i++)
			found = shop.m_upgrades[i].m_idHash == HashString(args[1]) && step < int(shop.m_upgrades[i].m_steps.length());
		if (!found)
		{
			Fail(id, "shop '" + args[0] + "' has no upgrade '" + args[1] + "' step " + step);
			return;
		}
		rec.SetShopUpgradeLevel(shop.m_idHash, HashString(args[1]), step);
		rec.RefreshModifiers();
		rec.RefreshStats();
		Emit(Reply(id, true).Str("shop", args[0]).Str("upgrade", args[1]).Int("step", step)
			.Int("level", rec.GetShopUpgradeLevel(shop.m_idHash, HashString(args[1])))
			.Int("potionCharges", rec.currStats.PotionCharges));
	}

	// teleport <x> <y>: set the local player's unit position (the respawn path's call,
	// Player.as SetPosition(x, y, z, true)). Measurement scenarios only: a gate scenario that
	// teleports is not evidence of play.
	void VerbTeleport(const string &in id, array<string>@ args)
	{
		auto plr = GetLocalPlayer();
		if (plr is null || args.length() < 2)
		{
			Fail(id, plr is null ? "no spawned local player" : "usage: teleport <x> <y>");
			return;
		}
		vec3 p = plr.m_unit.GetPosition();
		plr.m_unit.SetPosition(parseFloat(args[0]), parseFloat(args[1]), p.z, true);
		vec3 q = plr.m_unit.GetPosition();
		Emit(Reply(id, true).Num("fromX", p.x).Num("fromY", p.y).Num("x", q.x).Num("y", q.y));
	}

	// timescale <x>: measurement only, NOT a test accelerator. Sets the engine cvar g_timescale
	// (0.1-16), turning e_cheats on first. Game-ms timers scale with it but player movement per
	// frame does not (floor-soak 20261017-175501 at 4x: intents timed out after a quarter of
	// the walk), so gameplay results under it are not results at 1x.
	void VerbTimescale(const string &in id, array<string>@ args)
	{
		if (args.length() < 1)
		{
			Fail(id, "usage: timescale <x>");
			return;
		}
		float x = max(0.1f, min(16.0f, parseFloat(args[0])));
		// g_timescale only changes with e_cheats on (SetVar alone read back 1.0: timescale
		// 20261017-175222); the engine allows e_cheats in modded games. Lab saves only.
		SetCheats(true);
		SetVar("g_timescale", x);
		Emit(Reply(id, true).Num("set", x).Num("timescale", GetVarFloat("g_timescale"))
			.Int("cheatsType", int(GetVarType("e_cheats"))).Bool("cheats", CheatsOn()));
	}

	// cull: the cht_kill_all cheat's body (Console/Cheats.as:970-980): Kill every targetable
	// actor not on the player's team; `skipped` names (at most 16) the untargetable ones left.
	// "cull mine" names the local player as the killer (CompositeActorBehavior.Kill ->
	// OnDeath -> Player.KilledActor), so XP and the PlayerKilledActor hook run as for a
	// player's kill. Measurement scenarios only, like teleport.
	void VerbCull(const string &in id, array<string>@ args)
	{
		Actor@ killer = null;
		if (args.length() > 0 && args[0] == "mine")
		{
			auto plr = GetLocalPlayer();
			if (plr is null)
			{
				Emit(Reply(id, false).Str("error", "no local player"));
				return;
			}
			@killer = plr;
		}
		auto enemies = g_scene.FetchAllActorsWithOtherTeam(g_team_player);
		int killed = 0;
		array<string> skipped;
		for (uint i = 0; i < enemies.length(); i++)
		{
			Actor@ a = cast<Actor>(enemies[i].GetScriptBehavior());
			if (a !is null && a.IsTargetable())
			{
				a.Kill(killer, 0);
				killed++;
			}
			else if (skipped.length() < 16)
			{
				vec3 pos = enemies[i].GetPosition();
				skipped.insertLast(enemies[i].GetDebugName() + "@" + int(pos.x) + "," + int(pos.y));
			}
		}
		Emit(Reply(id, true).Int("found", enemies.length()).Int("killed", killed).Raw("skipped", StrArray(skipped)));
	}
}
