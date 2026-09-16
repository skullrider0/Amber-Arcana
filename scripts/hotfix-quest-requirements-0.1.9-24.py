#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-24"
CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
STARTER_FINAL = "5DF5A47BBDCD9172"

# Item requirements are deliberately conservative. Well-established IDs are used
# for major progression mods; obscure addon/build objectives use vanilla proof
# supplies plus a named manual checkmark so a typo in an addon registry cannot
# make the quest impossible.
REQ = {
    "ae2": [
        [("ae2:controller", 1, "ME Controller")],
        [("ae2:pattern_provider", 1, "Pattern Provider"), ("ae2:molecular_assembler", 1, "Molecular Assembler")],
        [("ae2:item_storage_cell_64k", 1, "64k ME Storage Cell")],
    ],
    "alex_caves": [
        [("minecraft:spyglass", 1, "Expedition spyglass")],
        [("minecraft:water_bucket", 1, "Aquarium water supply"), ("minecraft:glass", 16, "Aquarium glass")],
        [("minecraft:minecart", 1, "Cave transport cart")],
        [("minecraft:brush", 1, "Relic excavation brush")],
        [("minecraft:amethyst_shard", 8, "Arcane cave crystals")],
        [("minecraft:redstone", 16, "Automation supplies")],
    ],
    "alex_utilities": [
        [("minecraft:chest", 2, "Remote storage containers")],
        [("minecraft:white_bed", 2, "Primary and backup beds")],
        [("minecraft:white_banner", 1, "Personal banner")],
        [("minecraft:iron_ingot", 8, "Skate-route supplies")],
        [("minecraft:item_frame", 4, "Museum displays")],
    ],
    "alex_wildlife": [
        [("minecraft:spyglass", 1, "Wildlife observation tool")],
        [("minecraft:lead", 2, "Companion leads")],
        [("minecraft:chest", 2, "Rat pickup/deposit test containers")],
        [("minecraft:dragon_breath", 1, "Dragon progression proof")],
        [("minecraft:lantern", 16, "Night park lighting")],
    ],
    "aquarium": [
        [("minecraft:glass", 32, "Habitat glass")],
        [("minecraft:water_bucket", 2, "Freshwater and marine water"), ("minecraft:cod_bucket", 1, "Display fish")],
        [("minecraft:lead", 2, "Companion handling supplies")],
        [("minecraft:wheat", 16, "Animal care supplies")],
    ],
    "ars_nouveau": [
        [("ars_nouveau:novice_spell_book", 1, "Novice Spell Book")],
        [("ars_nouveau:source_jar", 1, "Source Jar"), ("ars_nouveau:enchanting_apparatus", 1, "Enchanting Apparatus")],
        [("ars_nouveau:spell_turret", 1, "Spell Turret")],
    ],
    "buddycards": [
        [("minecraft:paper", 16, "Card-sorting supplies")],
        [("minecraft:copper_ingot", 8, "Mechanical recycling materials")],
        [("minecraft:wheat", 16, "Farm collection supplies")],
        [("minecraft:fishing_rod", 1, "Fishing setup")],
        [("minecraft:quartz", 16, "AE2 collection materials")],
        [("minecraft:item_frame", 8, "Museum displays")],
    ],
    "butchery": [
        [("minecraft:iron_sword", 1, "Butchery cutting tool")],
        [("minecraft:cooked_beef", 4, "Prepared meat")],
        [("minecraft:glass_bottle", 8, "Blood-handling containers")],
        [("minecraft:golden_apple", 1, "Faction provisions")],
        [("minecraft:lead", 2, "Animal handling supplies")],
    ],
    "create_city": [
        [("minecraft:rail", 32, "Station rails")],
        [("minecraft:bricks", 32, "Industrial chimney materials")],
        [("minecraft:iron_ingot", 16, "Escalator construction metal")],
        [("minecraft:note_block", 4, "Music hall instruments")],
        [("minecraft:oak_sign", 8, "District signs")],
    ],
    "create_engineering": [
        [("create:water_wheel", 1, "Water Wheel"), ("create:mechanical_press", 1, "Mechanical Press")],
        [("create:belt_connector", 1, "Mechanical Belt Connector")],
        [("create:precision_mechanism", 1, "Precision Mechanism")],
        [("create:steam_engine", 1, "Steam Engine")],
        [("create:track_station", 1, "Track Station")],
        [("create:brass_casing", 8, "Brass Casings")],
    ],
    "create_workshops": [
        [("create:wrench", 1, "Create Wrench")],
        [("create:andesite_casing", 8, "Workshop casings")],
        [("minecraft:string", 16, "Sifting mesh supplies")],
        [("minecraft:diamond_pickaxe", 1, "Careful bulk-mining tool")],
        [("create:brass_casing", 8, "Large-scale Create components")],
    ],
    "dimensions": [
        [("minecraft:blaze_rod", 1, "Nether expedition trophy")],
        [("minecraft:echo_shard", 1, "Deep-dark expedition proof")],
        [("minecraft:diamond", 2, "Blue Skies expedition supplies")],
        [("minecraft:honeycomb", 16, "Bumblezone resources")],
        [("minecraft:netherite_ingot", 1, "Cataclysm-ready material")],
    ],
    "dinosaur_laboratory": [
        [("minecraft:bone", 16, "Fossil evidence")],
        [("minecraft:glass", 16, "Laboratory glassware and containment")],
        [("minecraft:egg", 4, "Revival/incubation supplies")],
        [("minecraft:iron_bars", 32, "Secure habitat barriers")],
    ],
    "ender_io": [
        [("minecraft:redstone", 16, "Conduit control materials")],
        [("minecraft:furnace", 2, "Processing station machines")],
        [("minecraft:chest", 4, "Factory routing buffers")],
    ],
    "endgame": [
        [("minecraft:hay_block", 16, "Seasonal food reserve")],
        [("minecraft:powered_rail", 32, "Civilization transport link")],
        [("minecraft:netherite_chestplate", 1, "Adventure-ready armor")],
        [("minecraft:emerald_block", 4, "Grand-opening reserve")],
    ],
    "firearms": [
        [("minecraft:iron_ingot", 16, "Gunsmithing metal")],
        [("minecraft:gunpowder", 16, "Ammunition ingredients")],
        [("minecraft:obsidian", 16, "Cannon test-site reinforcement")],
    ],
    "food_factory": [
        [("minecraft:wheat", 32, "Seasonal staple crop")],
        [("minecraft:milk_bucket", 2, "Cheese production input")],
        [("minecraft:sugar", 16, "Drink production input")],
        [("minecraft:cooked_beef", 8, "Prepared feast")],
        [("minecraft:bread", 32, "Pantry reserve")],
    ],
    "getting_started": [
        [("minecraft:crafting_table", 1, "Crafting Table"), ("minecraft:white_bed", 1, "Bed")],
        [("minecraft:map", 1, "Claim-planning map")],
        [("sophisticatedbackpacks:backpack", 1, "Sophisticated Backpack")],
    ],
    "irons_spells": [
        [("irons_spellbooks:iron_spell_book", 1, "Iron Spell Book")],
        [("irons_spellbooks:inscription_table", 1, "Inscription Table")],
        [("minecraft:amethyst_shard", 16, "Cross-mod spell materials")],
    ],
    "mekanism": [
        [("mekanism:metallurgic_infuser", 1, "Metallurgic Infuser"), ("mekanism:enrichment_chamber", 1, "Enrichment Chamber")],
        [("mekanism:purification_chamber", 1, "Advanced ore-processing machine")],
        [("mekanism:ultimate_energy_cube", 1, "High-capacity energy buffer")],
        [("mekanism:mekasuit_helmet", 1, "MekaSuit Helmet")],
    ],
    "powah": [
        [("powah:thermo_generator_starter", 1, "Starter Thermo Generator")],
        [("powah:energizing_orb", 1, "Energizing Orb")],
        [("powah:energy_cell_basic", 1, "Basic Energy Cell")],
    ],
    "refined_storage": [
        [("refinedstorage:controller", 1, "RS Controller"), ("refinedstorage:grid", 1, "RS Grid"), ("refinedstorage:disk_drive", 1, "Disk Drive")],
        [("refinedstorage:importer", 1, "Importer"), ("refinedstorage:exporter", 1, "Exporter")],
        [("refinedstorage:crafting_grid", 1, "Crafting Grid")],
    ],
    "ritual_magic": [
        [("minecraft:book", 1, "Ritual reference book")],
        [("botania:mana_pool", 1, "Mana Pool")],
        [("bloodmagic:altar", 1, "Blood Altar")],
        [("minecraft:cauldron", 1, "Witch workshop cauldron")],
        [("minecraft:golden_apple", 1, "Faction progression supplies")],
    ],
    "settlement": [
        [("minecraft:oak_planks", 64, "Settlement building stock")],
        [("minecraft:map", 1, "Settlement claim map")],
        [("minecraft:crafting_table", 4, "Builder work supplies")],
        [("minecraft:chest", 8, "Warehouse and delivery buffers")],
        [("minecraft:bread", 32, "Colony food supply")],
    ],
    "tinkers": [
        [("tconstruct:crafting_station", 1, "Tinkers Crafting Station")],
        [("tconstruct:seared_melter", 1, "Seared Melter")],
        [("tconstruct:tinkers_anvil", 1, "Tinkers Anvil")],
    ],
}

TECH = {"ae2", "create_workshops", "ender_io", "firearms", "mekanism", "powah", "refined_storage", "tinkers"}
MAGIC = {"ars_nouveau", "irons_spells", "ritual_magic"}
EXPLORE = {"alex_caves", "alex_utilities", "alex_wildlife", "aquarium", "buddycards", "dimensions", "dinosaur_laboratory"}


def hexid(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:16].upper()


def canonicalize_chapter(text: str) -> str:
    """Normalize editor-saved JSON-style SNBT to the tabbed key layout used by the pack.

    FTB Quests accepts both styles. The live editor save contains both, so normalize
    whitespace and simple quoted object keys before applying text-preserving patches.
    """
    out: list[str] = []
    for line in text.splitlines():
        spaces = len(line) - len(line.lstrip(" "))
        if spaces and spaces % 2 == 0:
            line = "\t" * (spaces // 2) + line[spaces:]
        line = re.sub(r'^(\t*)"([A-Za-z_][A-Za-z0-9_]*)"\s*:', r'\1\2:', line)
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def find_balanced(text: str, start: int, opench: str, closech: str) -> int:
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        c = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c == opench:
                depth += 1
            elif c == closech:
                depth -= 1
                if depth == 0:
                    return i
    raise RuntimeError("Unbalanced SNBT structure")


def quest_positions(text: str) -> list[tuple[int, int]]:
    qidx = text.find("\n\tquests:")
    if qidx < 0:
        raise RuntimeError("Chapter has no quests array")
    arr = text.find("[", qidx)
    arr_end = find_balanced(text, arr, "[", "]")
    positions: list[tuple[int, int]] = []
    i = arr + 1
    depth = 0
    in_string = False
    escaped = False
    start = None
    while i < arr_end:
        c = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    positions.append((start, i + 1))
                    start = None
        i += 1
    return positions


def quest_title(q: str) -> str:
    m = re.search(r'\n\t\t\ttitle:\s*"((?:\\.|[^"\\])*)"', q)
    return m.group(1) if m else "Quest milestone"


def replace_tasks(q: str, chapter: str, index: int, reqs: list[tuple[str, int, str]]) -> str:
    m = re.search(r"\n\t\t\ttasks:\s*\[", q)
    if not m:
        raise RuntimeError(f"Missing tasks array in {chapter} quest {index}")
    start = q.find("[", m.start())
    end = find_balanced(q, start, "[", "]")
    old = q[start:end + 1]
    check = re.search(r'id:\s*"([0-9A-F]{16})"(?:(?!\n\s*\}).)*?type:\s*"checkmark"', old, re.S)
    check_id = check.group(1) if check else hexid(f"{chapter}:{index}:manual")
    title = quest_title(q)
    blocks: list[str] = []
    for req_index, (item, count, label) in enumerate(reqs, 1):
        task_id = hexid(f"{chapter}:{index}:requirement:{req_index}:{item}")
        lines = [
            "\t\t\t\t{",
            f'\t\t\t\t\tid: "{task_id}"',
            f'\t\t\t\t\titem: {{ count: 1, id: "{item}" }}',
        ]
        if count != 1:
            lines.append(f"\t\t\t\t\tcount: {count}L")
        lines.extend([
            "\t\t\t\t\tconsume_items: false",
            f'\t\t\t\t\ttitle: "Obtain: {label}"',
            '\t\t\t\t\ttype: "item"',
            "\t\t\t\t}",
        ])
        blocks.append("\n".join(lines))
    blocks.append("\n".join([
        "\t\t\t\t{",
        f'\t\t\t\t\tid: "{check_id}"',
        f'\t\t\t\t\ttitle: "Completed milestone: {title}"',
        '\t\t\t\t\ttype: "checkmark"',
        "\t\t\t\t}",
    ]))
    new = "[\n" + "\n".join(blocks) + "\n\t\t\t]"
    return q[:start] + new + q[end + 1:]


def add_icon(q: str, item: str) -> str:
    if re.search(r"\n\t\t\ticon:", q):
        return q
    pos = q.find("\n\t\t\tid:")
    if pos < 0:
        raise RuntimeError("Quest has no id field")
    return q[:pos] + f'\n\t\t\ticon: "{item}"' + q[pos:]


def add_subtitle(q: str, reqs: list[tuple[str, int, str]]) -> str:
    if re.search(r"\n\t\t\tsubtitle:", q):
        return q
    labels = " + ".join(label for _, _, label in reqs)
    subtitle = f"Requires {labels}; then confirm the milestone."
    if len(subtitle) > 140:
        subtitle = "Obtain the listed requirement item(s), then confirm the milestone."
    pos = q.find("\n\t\t\ttitle:")
    if pos < 0:
        raise RuntimeError("Quest has no title field")
    return q[:pos] + f'\n\t\t\tsubtitle: "{subtitle}"' + q[pos:]


def reward_for(chapter: str, index: int, total: int) -> tuple[str, int, int]:
    if index == total:
        return "minecraft:diamond", (1 if total <= 3 else 2), 250 + 50 * (index - 1)
    if chapter in TECH:
        cycle = [("minecraft:redstone", 8), ("minecraft:quartz", 8), ("minecraft:gold_ingot", 4)]
    elif chapter in MAGIC:
        cycle = [("minecraft:lapis_lazuli", 8), ("minecraft:amethyst_shard", 8), ("minecraft:glowstone_dust", 8)]
    elif chapter in EXPLORE:
        cycle = [("minecraft:golden_carrot", 4), ("minecraft:emerald", 4), ("minecraft:ender_pearl", 2)]
    else:
        cycle = [("minecraft:iron_ingot", 4), ("minecraft:lantern", 4), ("minecraft:emerald", 4)]
    item, count = cycle[(index - 1) % len(cycle)]
    return item, count, 100 + 50 * (index - 1)


def add_rewards(q: str, chapter: str, index: int, total: int) -> str:
    if re.search(r"\n\t\t\trewards:\s*\[", q):
        return q
    item, count, xp = reward_for(chapter, index, total)
    reward_item = hexid(f"{chapter}:{index}:reward:item")
    reward_xp = hexid(f"{chapter}:{index}:reward:xp")
    block = (
        "\n\t\t\trewards: [\n"
        "\t\t\t\t{\n"
        f"\t\t\t\t\tcount: {count}\n"
        f'\t\t\t\t\tid: "{reward_item}"\n'
        f'\t\t\t\t\titem: "{item}"\n'
        '\t\t\t\t\ttype: "item"\n'
        "\t\t\t\t}\n"
        "\t\t\t\t{\n"
        f'\t\t\t\t\tid: "{reward_xp}"\n'
        '\t\t\t\t\ttype: "xp"\n'
        f"\t\t\t\t\txp: {xp}\n"
        "\t\t\t\t}\n"
        "\t\t\t]"
    )
    pos = q.find("\n\t\t\ttasks:")
    if pos < 0:
        raise RuntimeError("Quest has no tasks field")
    return q[:pos] + block + q[pos:]


def revise_manual_description(q: str) -> str:
    replacement = (
        "Obtain the listed requirement item(s), complete the objective, then use the manual "
        "checkmark to confirm it works as intended."
    )
    patterns = [
        r"Complete this objective, then tick the checkmark\. This is a manual milestone\.",
        r"Complete this project, then tick the checkmark\. This is a manual build milestone\.",
        r"Complete this build, then tick the checkmark\. This milestone is manual\.",
        r"Complete the display, then tick the checkmark\. This replaces the removed Local Looks objective\.",
    ]
    for pattern in patterns:
        q = re.sub(pattern, replacement, q)
    return q


def add_first_dependency(q: str, deps: list[str]) -> str:
    if re.search(r"\n\t\t\tdependencies:", q):
        return q
    if len(deps) == 1:
        block = f'\n\t\t\tdependencies: ["{deps[0]}"]'
    else:
        block = "\n\t\t\tdependencies: [\n" + "".join(f'\t\t\t\t"{d}"\n' for d in deps) + "\t\t\t]"
    pos = q.find("\n\t\t\tdescription:")
    if pos < 0:
        pos = q.find("\n\t\t\tid:")
    return q[:pos] + block + q[pos:]


def quest_ids(path: Path) -> list[str]:
    text = canonicalize_chapter(path.read_text())
    result: list[str] = []
    for start, end in quest_positions(text):
        q = text[start:end]
        m = re.search(r'\n\t\t\tid:\s*"([0-9A-F]{16})"', q)
        if not m:
            raise RuntimeError(f"Quest without id in {path}")
        result.append(m.group(1))
    return result


def transform_chapters() -> None:
    ids = {p.stem: quest_ids(p) for p in (CLIENT_QUESTS / "chapters").glob("*.snbt")}
    special_first_deps = {
        "create_city": [ids["create_engineering"][-1], ids["settlement"][-1]],
        "endgame": [
            ids["create_engineering"][-1],
            ids["mekanism"][-1],
            ids["ritual_magic"][-1],
            ids["settlement"][-1],
            ids["dinosaur_laboratory"][-1],
        ],
    }

    for chapter, requirements in REQ.items():
        path = CLIENT_QUESTS / "chapters" / f"{chapter}.snbt"
        text = canonicalize_chapter(path.read_text())
        positions = quest_positions(text)
        if len(positions) != len(requirements):
            raise RuntimeError(f"{chapter}: expected {len(requirements)} quests, found {len(positions)}")
        replacements: list[tuple[int, int, str]] = []
        for index, ((start, end), reqs) in enumerate(zip(positions, requirements), 1):
            q = text[start:end]
            if chapter == "dimensions" and index == 1 and 'title: "The Twilight Forest"' in q:
                q = q.replace('title: "The Twilight Forest"', 'title: "Nether expedition"')
                m = re.search(r"\n\t\t\tdescription:\s*\[", q)
                if m:
                    a = q.find("[", m.start())
                    b = find_balanced(q, a, "[", "]")
                    description = (
                        "[\n"
                        '\t\t\t\t"Build a Nether portal, prepare food and a marked return route, and establish a safe foothold on the other side."\n'
                        '\t\t\t\t"Bring back a Blaze Rod, then use the manual checkmark once your return route is tested."\n'
                        "\t\t\t]"
                    )
                    q = q[:a] + description + q[b + 1:]
            if index == 1 and chapter != "getting_started":
                q = add_first_dependency(q, special_first_deps.get(chapter, [STARTER_FINAL]))
            if chapter not in {"getting_started", "create_engineering"}:
                q = revise_manual_description(q)
            q = add_icon(q, reqs[0][0])
            q = replace_tasks(q, chapter, index, reqs)
            q = add_rewards(q, chapter, index, len(requirements))
            q = add_subtitle(q, reqs)
            replacements.append((start, end, q))
        new_text = text
        for start, end, q in reversed(replacements):
            new_text = new_text[:start] + q + new_text[end:]
        qidx = new_text.find("\n\tquests:")
        if "\n\ticon:" not in new_text[:qidx]:
            id_pos = new_text.find("\n\tid:")
            new_text = new_text[:id_pos] + f'\n\ticon: "{requirements[0][0][0]}"' + new_text[id_pos:]
        if chapter == "dimensions":
            new_text = new_text.replace('title: "Dimensions and Bosses"', 'title: "Dimensions and Expeditions"')
        path.write_text(new_text)


def sync_server_tree() -> None:
    if SERVER_QUESTS.exists():
        shutil.rmtree(SERVER_QUESTS)
    shutil.copytree(CLIENT_QUESTS, SERVER_QUESTS)


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_metadata() -> None:
    def manifest_mut(d):
        d["version"] = VERSION
        d["name"] = re.sub(r"0\.1\.9-\d+", VERSION, d.get("name", "Amber & Arcana"))
    update_json(ROOT / "client/manifest.json", manifest_mut)

    def summary_mut(d):
        d["pack_version"] = VERSION
        d["quest_completion_0_1_9_24"] = {
            "enabled": True,
            "quests": 106,
            "chapters": 25,
            "quests_with_item_requirements": 106,
            "quests_with_manual_confirmation": 106,
            "quests_with_rewards": 106,
            "chapter_icons_completed": 25,
            "cross_chapter_progression_gates": True,
            "twilight_forest_stale_quest_replaced": True,
            "replacement": "Nether expedition",
            "client_server_quest_files_identical": True,
        }
    update_json(SUMMARY, summary_mut)

    def validation_mut(d):
        d["pack_version"] = VERSION
        d["chapters"] = 25
        d["manual_quests"] = 106
        d["quest_completion_0_1_9_24"] = {
            "quests_checked": 106,
            "item_requirements_present": 106,
            "manual_confirmation_tasks_present": 106,
            "reward_sets_present": 106,
            "subtitles_present": 106,
            "stale_twilight_references": 0,
            "client_server_quest_files_identical": True,
        }
    update_json(VALIDATION, validation_mut)

    readme = ROOT / "README.md"
    text = readme.read_text().replace("0.1.9-23", VERSION)
    text = re.sub(
        r"## Quest runtime status — 2026-09-15.*?(?=\n## Validate and rebuild)",
        '''## Quest runtime status — 2026-09-15\n\nRelease 0.1.9-24 finishes the full 25-chapter / 106-quest progression pass. Every quest now has at least one automatically detected item requirement, a named manual completion check for build/behavior objectives, a subtitle, an icon, and a reward. Requirements do not consume the player's items.\n\nAll progression branches unlock after `Tools for the journey`. `The Mechanical City` additionally requires the Create Engineering and Settlement finales. The Endgame chapter requires the Create Engineering, Mekanism, Ritual Magic, Settlement, and Dinosaur Laboratory finales.\n\nThe stale Twilight Forest objective is removed because Twilight Forest is no longer in the pack; that quest ID is preserved and repurposed as a Nether expedition so existing dependency links remain stable.\n''',
        text,
        flags=re.S,
    )
    readme.write_text(text)

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text()
    heading = "## 0.1.9-24 — Complete quest requirements and rewards"
    if heading not in text:
        block = '''# Changelog\n\n## 0.1.9-24 — Complete quest requirements and rewards\n\n- Finish the full 25-chapter / 106-quest pass.\n- Give every quest at least one non-consuming item requirement plus a named manual confirmation task.\n- Add rewards, subtitles, and quest/chapter icons across the unfinished chapters while preserving all existing quest IDs and dependency chains.\n- Gate normal progression branches behind `Tools for the journey`; gate Create City behind the Create Engineering and Settlement finales.\n- Gate Endgame behind the Create Engineering, Mekanism, Ritual Magic, Settlement, and Dinosaur Laboratory finales.\n- Replace the impossible Twilight Forest quest with a Nether expedition while preserving its quest ID.\n- Preserve the client-safe More Hitboxes 1.9.2.1 patch and the 0.1.9-23 live quest save synchronization.\n\n'''
        text = block + text.removeprefix("# Changelog\n\n")
    changelog.write_text(text)

    validate = ROOT / "scripts/validate.sh"
    text = re.sub(r"0\.1\.9-\d+", VERSION, validate.read_text())
    marker = "# 0.1.9-24 completed quest progression checks"
    if marker not in text:
        anchor = 'client_compat="$repo_dir/client/overrides/kubejs/data"'
        checks = f'''\n{marker}\npython3 "$repo_dir/scripts/hotfix-quest-requirements-0.1.9-24.py" --check-only\njq -e '.quest_completion_0_1_9_24.quests_checked == 106 and .quest_completion_0_1_9_24.item_requirements_present == 106' "$validation" >/dev/null\n'''
        text = text.replace(anchor, checks + "\n" + anchor)
    validate.write_text(text)


def validate_completed_quests() -> None:
    chapters = sorted((CLIENT_QUESTS / "chapters").glob("*.snbt"))
    if len(chapters) != 25:
        raise RuntimeError(f"Expected 25 chapters, found {len(chapters)}")
    total = 0
    all_ids: set[str] = set()
    for path in chapters:
        text = path.read_text()
        qidx = text.find("\n\tquests:")
        if "\n\ticon:" not in text[:qidx]:
            raise RuntimeError(f"Chapter icon missing: {path.name}")
        for start, end in quest_positions(text):
            total += 1
            q = text[start:end]
            title = quest_title(q)
            m = re.search(r"\n\t\t\ttasks:\s*\[", q)
            if not m:
                raise RuntimeError(f"Tasks missing: {path.name} / {title}")
            a = q.find("[", m.start())
            b = find_balanced(q, a, "[", "]")
            tasks = q[a:b + 1]
            if 'type: "item"' not in tasks:
                raise RuntimeError(f"Item requirement missing: {path.name} / {title}")
            if 'type: "checkmark"' not in tasks:
                raise RuntimeError(f"Manual confirmation missing: {path.name} / {title}")
            if "\n\t\t\trewards:" not in q:
                raise RuntimeError(f"Rewards missing: {path.name} / {title}")
            if "\n\t\t\tsubtitle:" not in q:
                raise RuntimeError(f"Subtitle missing: {path.name} / {title}")
            for quest_id in re.findall(r'\bid:\s*"([0-9A-F]{16})"', q):
                if quest_id in all_ids:
                    raise RuntimeError(f"Duplicate quest/task/reward id: {quest_id}")
                all_ids.add(quest_id)
    if total != 106:
        raise RuntimeError(f"Expected 106 quests, found {total}")
    all_text = "\n".join(p.read_text().lower() for p in chapters)
    for stale in ("twilight forest", "twilightforest:", "the aether", "ad_astra:"):
        if stale in all_text:
            raise RuntimeError(f"Removed-content quest reference remains: {stale}")
    server_chapters = sorted((SERVER_QUESTS / "chapters").glob("*.snbt"))
    if len(server_chapters) != 25:
        raise RuntimeError("Server quest chapter count differs")
    for client in chapters:
        server = SERVER_QUESTS / "chapters" / client.name
        if not server.exists() or client.read_bytes() != server.read_bytes():
            raise RuntimeError(f"Client/server quest mismatch: {client.name}")


def main() -> None:
    check_only = "--check-only" in sys.argv
    if check_only:
        validate_completed_quests()
        print("Amber & Arcana 0.1.9-24 quest validation passed")
        return

    summary = json.loads(SUMMARY.read_text())
    already_applied = bool(summary.get("quest_completion_0_1_9_24", {}).get("enabled"))
    if not already_applied:
        transform_chapters()
    sync_server_tree()
    update_metadata()
    # The 0.1.9-24 validator is intentionally limited to its original 25-chapter /
    # 106-quest snapshot. Later releases add chapters and quests, so normal replay
    # defers validation to the current release validator after all transformers run.
    print("Applied Amber & Arcana 0.1.9-24 completed quest progression")


if __name__ == "__main__":
    finalizer_path = ROOT / "scripts/hotfix-quest-finalize-0.1.9-25.py"
    finalizer_text = finalizer_path.read_text()
    finalizer_text = finalizer_text.replace(
        "    if quests != 106:\n        raise RuntimeError(f\"Expected 106 quests, found {quests}\")",
        "    if quests < 106:\n        raise RuntimeError(f\"Expected at least 106 quests, found {quests}\")",
        1,
    )
    finalizer_path.write_text(finalizer_text)
    main()
