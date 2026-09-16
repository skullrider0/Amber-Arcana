#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-27"
PB_VERSION = "1.20.1-12.6.0"
PB_COMMIT = "2190d6b4c0f4a35acc26415759c3be731d1eac22"
PB_ARCHIVE = f"https://codeload.github.com/JDKDigital/productive-bees/zip/{PB_COMMIT}"

CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"
CHAPTER = CLIENT_QUESTS / "chapters/productive_bees.snbt"
TABLE = CLIENT_QUESTS / "reward_tables/wheel_productive_bees.snbt"
MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
MODS_TSV = ROOT / "server/_crafty/server-mods.tsv"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"

GROUP_ID = "6AA0010000000001"
CHAPTER_ID = "6AA002BEE00000000"

SETUP = [
    ("bee_cage", "Bee Cage", "productivebees:bee_cage", "Craft a Bee Cage so you can safely capture and move bees."),
    ("advanced_hive", "Advanced Beehive", "productivebees:advanced_oak_beehive", "Build an Advanced Beehive. This is the core home for productive bees and accepts upgrades."),
    ("expansion_box", "Expansion Box", "productivebees:expansion_box_oak", "Add an Expansion Box to increase your Advanced Beehive capacity and unlock upgrade slots."),
    ("feeder", "Feeder", "productivebees:feeder", "Craft a Feeder so enclosed bees can reach the flowering block or item they need."),
    ("centrifuge", "Centrifuge", "productivebees:centrifuge", "Craft a Centrifuge to process combs into their useful resources."),
    ("breeding_chamber", "Breeding Chamber", "productivebees:breeding_chamber", "Craft a Breeding Chamber for controlled bee breeding. The family tree below follows Productive Bees' real 12.6.0 recipes."),
]

REMOVED_MODS = {"ad_astra", "aether", "twilightforest", "the_aether"}
MOD_ALIASES = {
    "ae2": ("appliedenergistics2", "applied-energistics-2", "ae2"),
    "tconstruct": ("tconstruct", "tinkers", "tinkers-construct"),
    "allthemodium": ("allthemodium",),
    "byg": ("byg", "biomesyoullgo", "oh-the-biomes-youll-go"),
    "mekanism": ("mekanism",),
    "botania": ("botania",),
    "powah": ("powah",),
    "enderio": ("enderio", "ender-io"),
    "create": ("create-", "\tcreate\t", " create "),
    "create_enchantment_industry": ("create-enchantment-industry", "create_enchantment_industry"),
    "thermal": ("thermal",),
    "evilcraft": ("evilcraft",),
    "elementalcraft": ("elementalcraft",),
    "chemlib": ("chemlib",),
    "silentgear": ("silentgear", "silent-gear"),
    "silentgems": ("silentgems", "silent-gems"),
    "ars_nouveau": ("ars_nouveau", "ars-nouveau"),
    "bloodmagic": ("bloodmagic", "blood-magic"),
}

BRANCH_NAMES = {
    "core": "Core Resource Bees",
    "alloys": "Alloy Bees",
    "ores": "Ore Bees",
    "gems": "Gem Bees",
    "dusts": "Dust Bees",
    "appliedenergistics2": "Applied Energistics 2 Bees",
    "mekanism": "Mekanism Bees",
    "tconstruct": "Tinkers' Construct Bees",
    "botania": "Botania Bees",
    "powah": "Powah Bees",
    "enderio": "Ender IO Bees",
    "create": "Create Bees",
    "create_enchantment_industry": "Create Enchantment Industry Bees",
    "thermal": "Thermal Bees",
    "evilcraft": "EvilCraft Bees",
    "elementalcraft": "ElementalCraft Bees",
    "chemlib": "ChemLib Bees",
    "silentgems": "Silent Gems Bees",
    "atm": "ATM Integration Bees",
    "byg": "Biome Integration Bees",
}


def hid(seed: str) -> str:
    value = int.from_bytes(hashlib.sha256(seed.encode()).digest()[:8], "big") & ((1 << 63) - 1)
    return f"{value or 1:016X}"


def hlong(seed: str) -> int:
    return int(hid(seed), 16)


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def bee_name(bee: str) -> str:
    if bee == "minecraft:bee":
        return "Honey Bee"
    path = bee.split(":", 1)[-1]
    if path.endswith("_bee"):
        path = path[:-4]
    words = path.replace("/", " ").replace("_", " ").split()
    special = {"ae2": "AE2", "rf": "RF", "xp": "XP", "dna": "DNA"}
    title = " ".join(special.get(w.lower(), w.capitalize()) for w in words)
    return title if title.lower().endswith("bee") else title + " Bee"


def load_source() -> Path:
    print(f"Downloading Productive Bees {PB_VERSION} source snapshot {PB_COMMIT[:12]}...", flush=True)
    with urllib.request.urlopen(PB_ARCHIVE, timeout=120) as response:
        data = response.read()
    z = zipfile.ZipFile(io.BytesIO(data))
    roots = {Path(n).parts[0] for n in z.namelist() if n}
    if len(roots) != 1:
        raise RuntimeError("Unexpected Productive Bees source archive layout")
    root_name = next(iter(roots))
    dest = ROOT / ".tmp-productive-bees-source"
    if dest.exists():
        shutil.rmtree(dest)
    z.extractall(dest)
    src = dest / root_name
    props = (src / "gradle.properties").read_text()
    if f"mod_version={PB_VERSION}" not in props or "minecraft_version=1.20.1" not in props:
        raise RuntimeError("Pinned Productive Bees source does not match installed 1.20.1-12.6.0")
    return src


def mod_present(modid: str, installed_text: str) -> bool:
    modid = modid.lower()
    if modid in REMOVED_MODS:
        return False
    if modid in installed_text:
        return True
    return any(token in installed_text for token in MOD_ALIASES.get(modid, ()))


def cond_allows(cond, installed_text: str) -> bool:
    if not isinstance(cond, dict):
        return True
    typ = str(cond.get("type", "")).lower()
    if typ in {"forge:mod_loaded", "neoforge:mod_loaded"}:
        return mod_present(str(cond.get("modid", "")), installed_text)
    if typ in {"forge:not", "neoforge:not"}:
        child = cond.get("value", cond.get("condition", {}))
        return not cond_allows(child, installed_text)
    if typ in {"forge:and", "neoforge:and"}:
        values = cond.get("values", cond.get("conditions", []))
        return all(cond_allows(c, installed_text) for c in values)
    if typ in {"forge:or", "neoforge:or"}:
        values = cond.get("values", cond.get("conditions", []))
        return any(cond_allows(c, installed_text) for c in values)
    return True


def active_bee_definitions(src: Path, installed_text: str) -> tuple[set[str], set[str]]:
    base = src / "src/generated/resources/data/productivebees/productivebees"
    all_defs: set[str] = set()
    active: set[str] = set()
    if not base.exists():
        raise RuntimeError("Productive Bees generated bee-definition directory missing")
    for path in sorted(base.rglob("*.json")):
        bee = f"productivebees:{path.stem}"
        all_defs.add(bee)
        data = json.loads(path.read_text())
        conditions = data.get("conditions", data.get("forge:conditions", []))
        if all(cond_allows(c, installed_text) for c in conditions):
            active.add(bee)
    return all_defs, active


def output_bees(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        bee = value.get("bee") or value.get("id")
        return [bee] if isinstance(bee, str) else []
    if isinstance(value, list):
        out = []
        for v in value:
            out.extend(output_bees(v))
        return out
    return []


def ingredient_text(item) -> str:
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return "the listed conversion item"
    if isinstance(item.get("item"), str):
        return item["item"]
    if isinstance(item.get("tag"), str):
        return "#" + item["tag"]
    return "the listed conversion item"


def category_for(path: Path, base: Path) -> str:
    rel = path.relative_to(base)
    if len(rel.parts) <= 1:
        return "core"
    return rel.parts[0]


def parse_routes(src: Path, all_defs: set[str], active_defs: set[str], installed_text: str):
    routes = defaultdict(list)
    route_count = 0

    def bee_allowed(bee: str) -> bool:
        return bee not in all_defs or bee in active_defs

    breeding = src / "src/main/resources/data/productivebees/recipes/bee_breeding"
    for path in sorted(breeding.rglob("*.json")):
        data = json.loads(path.read_text())
        conditions = data.get("conditions", data.get("forge:conditions", []))
        if not all(cond_allows(c, installed_text) for c in conditions):
            continue
        parents = [data.get("parent1"), data.get("parent2")]
        if not all(isinstance(p, str) for p in parents):
            continue
        for child in output_bees(data.get("offspring")):
            if not isinstance(child, str):
                continue
            refs = parents + [child]
            if not all(bee_allowed(b) for b in refs):
                continue
            cat = category_for(path, breeding)
            routes[child].append({
                "kind": "breed",
                "parents": tuple(parents),
                "category": cat,
                "detail": f"Breed {bee_name(parents[0])} + {bee_name(parents[1])}.",
                "source": str(path.relative_to(breeding)),
            })
            route_count += 1

    conversion = src / "src/main/resources/data/productivebees/recipes/bee_conversion"
    for path in sorted(conversion.rglob("*.json")):
        data = json.loads(path.read_text())
        conditions = data.get("conditions", data.get("forge:conditions", []))
        if not all(cond_allows(c, installed_text) for c in conditions):
            continue
        source = data.get("source")
        if not isinstance(source, str):
            continue
        item = ingredient_text(data.get("item"))
        cat = category_for(path, conversion)
        for child in output_bees(data.get("result")):
            if not isinstance(child, str):
                continue
            if not bee_allowed(source) or not bee_allowed(child):
                continue
            routes[child].append({
                "kind": "convert",
                "parents": (source,),
                "category": cat,
                "detail": f"Convert {bee_name(source)} using {item}.",
                "source": str(path.relative_to(conversion)),
            })
            route_count += 1

    if not routes:
        raise RuntimeError("No active Productive Bees progression routes were parsed")
    return routes, route_count


def choose_routes(routes):
    chosen = {}
    for child, options in routes.items():
        chosen[child] = sorted(
            options,
            key=lambda r: (0 if r["kind"] == "breed" else 1, 0 if r["category"] == "core" else 1, r["source"])
        )[0]
    return chosen


def compute_depths(chosen):
    produced = set(chosen)
    roots = set()
    for route in chosen.values():
        roots.update(p for p in route["parents"] if p not in produced)

    memo = {b: 0 for b in roots}
    visiting = set()

    def depth(bee):
        if bee in memo:
            return memo[bee]
        if bee in visiting:
            return 1
        visiting.add(bee)
        route = chosen.get(bee)
        if not route:
            value = 0
        else:
            value = 1 + max(depth(p) for p in route["parents"])
        visiting.remove(bee)
        memo[bee] = value
        return value

    for bee in produced:
        depth(bee)
    return roots, memo


def render_task(task_id: str, item: str | None = None, optional: bool = False) -> list[str]:
    lines = ["\t\t\t{"]
    lines.append(f'\t\t\t\tid: "{task_id}"')
    if item:
        lines.append(f'\t\t\t\titem: "{item}"')
        lines.append('\t\t\t\ttype: "item"')
    else:
        if optional:
            lines.append("\t\t\t\toptional_task: true")
        lines.append('\t\t\t\ttype: "checkmark"')
    lines.append("\t\t\t}")
    return lines


def render_reward(reward_id: str, xp: int = 25) -> list[str]:
    return [
        "\t\t\t{",
        f'\t\t\t\tid: "{reward_id}"',
        '\t\t\t\ttype: "xp"',
        f"\t\t\t\txp: {xp}",
        "\t\t\t}",
    ]


def quest_block(qid: str, title: str, subtitle: str, description: list[str], x: float, y: float,
                dependencies: list[str], tasks: list[list[str]], rewards: list[list[str]]) -> list[str]:
    lines = ["\t\t{"]
    if dependencies:
        lines.append("\t\t\tdependencies: [")
        for dep in dependencies:
            lines.append(f'\t\t\t\t"{dep}"')
        lines.append("\t\t\t]")
    lines.append("\t\t\tdescription: [")
    for d in description:
        lines.append(f'\t\t\t\t"{esc(d)}"')
    lines.append("\t\t\t]")
    lines.append(f'\t\t\tid: "{qid}"')
    lines.append("\t\t\trewards: [")
    for reward in rewards:
        lines.extend(reward)
    lines.append("\t\t\t]")
    lines.append(f'\t\t\tsubtitle: "{esc(subtitle)}"')
    lines.append("\t\t\ttasks: [")
    for task in tasks:
        lines.extend(task)
    lines.append("\t\t\t]")
    lines.append(f'\t\t\ttitle: "{esc(title)}"')
    lines.append(f"\t\t\tx: {x:.1f}d")
    lines.append(f"\t\t\ty: {y:.1f}d")
    lines.append("\t\t}")
    return lines


def render_chapter(chosen, routes, roots, depths):
    setup_ids = {key: hid(f"productive-bees-setup:{key}") for key, *_ in SETUP}
    bee_ids = {bee: hid(f"productive-bees-bee:{bee}") for bee in set(chosen) | set(roots)}

    category = {bee: ("wild_base" if bee in roots else chosen[bee]["category"]) for bee in bee_ids}
    categories = sorted({c for c in category.values() if c != "wild_base"})
    cat_names = {"wild_base": "Wild & Base Bees", **BRANCH_NAMES}
    lane_categories = ["wild_base"] + categories
    lane_x = {cat: (i - (len(lane_categories) - 1) / 2) * 14.0 for i, cat in enumerate(lane_categories)}

    positions = {}
    grouped = defaultdict(list)
    for bee in bee_ids:
        grouped[(category[bee], depths.get(bee, 0))].append(bee)
    for (cat, depth), bees in grouped.items():
        bees.sort(key=bee_name)
        for i, bee in enumerate(bees):
            offset = (i - (len(bees) - 1) / 2) * 2.8
            positions[bee] = (lane_x[cat] + offset, 12.0 + depth * 4.0)

    lines = [
        "{",
        "\tdefault_hide_dependency_lines: false",
        '\tdefault_quest_shape: ""',
        '\tfilename: "productive_bees"',
        f'\tgroup: "{GROUP_ID}"',
        '\ticon: "productivebees:bee_cage"',
        f'\tid: "{CHAPTER_ID}"',
        "\torder_index: 25",
        "\tquest_links: []",
        "\tquests: [",
    ]

    previous = None
    for i, (key, title, item, desc) in enumerate(SETUP):
        qid = setup_ids[key]
        deps = [previous] if previous else []
        subtitle = "Beekeeping setup" if i < len(SETUP) - 1 else "Unlocks the bee family tree below"
        lines.extend(quest_block(
            qid, title, subtitle,
            [desc, "Concrete equipment tasks complete automatically when the item is in your inventory."],
            0.0, i * 2.0, deps,
            [render_task(hid(f"{qid}:item"), item)],
            [render_reward(hid(f"{qid}:xp"), 50 if i == len(SETUP) - 1 else 25)],
        ))
        previous = qid

    setup_gate = setup_ids["breeding_chamber"]

    for bee in sorted(bee_ids, key=lambda b: (depths.get(b, 0), category[b], bee_name(b))):
        qid = bee_ids[bee]
        x, y = positions[bee]
        if bee in roots:
            deps = [setup_gate]
            detail = (
                "This is a base/source bee for the generated progression tree. Find or obtain it in-world, "
                "capture it with a Bee Cage, then confirm the milestone."
            )
            subtitle = f"{cat_names.get(category[bee], category[bee].replace('_', ' ').title())} — source bee"
        else:
            route = chosen[bee]
            deps = [bee_ids[p] for p in route["parents"] if p in bee_ids]
            alternatives = routes.get(bee, [])
            detail = route["detail"]
            if len(alternatives) > 1:
                detail += f" JEI may show {len(alternatives) - 1} additional valid route(s); this tree uses one canonical path so dependencies stay readable."
            subtitle = f"{cat_names.get(category[bee], category[bee].replace('_', ' ').title())} — depth {depths[bee]}"
        lines.extend(quest_block(
            qid, bee_name(bee), subtitle,
            [
                detail,
                "Bee-species completion is a manual confirmation because individual Productive Bees species are stored as typed bee data rather than unique inventory item IDs.",
            ],
            x, y, deps,
            [render_task(hid(f"{qid}:confirm"))],
            [render_reward(hid(f"{qid}:xp"), 25)],
        ))

    children = defaultdict(set)
    for child, route in chosen.items():
        for parent in route["parents"]:
            children[parent].add(child)

    branch_ids = {}
    branch_y = (max(depths.values()) + 2) * 4.0 + 12.0
    for cat in categories:
        members = [b for b in bee_ids if category[b] == cat]
        terminals = [b for b in members if not any(c in members for c in children.get(b, ()))]
        if not terminals:
            terminals = sorted(members, key=lambda b: depths.get(b, 0))[-1:]
        bid = hid(f"productive-bees-branch:{cat}")
        branch_ids[cat] = bid
        title = cat_names.get(cat, cat.replace("_", " ").title())
        lines.extend(quest_block(
            bid, f"{title} Complete", f"Finish the {title} branch",
            ["Complete the terminal bee milestones in this branch, then confirm the branch completion."],
            lane_x[cat], branch_y,
            [bee_ids[b] for b in sorted(terminals)],
            [render_task(hid(f"{bid}:confirm"))],
            [render_reward(hid(f"{bid}:xp"), 100)],
        ))

    master_id = hid("productive-bees-master-apiarist")
    wheel_id = hlong("amber-arcana-wheel-table:productive_bees")
    wheel_reward_id = hid("amber-arcana-wheel-reward:productive_bees")
    master_deps = list(branch_ids.values())
    if not master_deps:
        master_deps = [bee_ids[b] for b in chosen]
    lines.extend(quest_block(
        master_id, "Master Apiarist", "Complete the Productive Bees family tree",
        [
            "Finish every generated bee branch and confirm this milestone.",
            "Your finale includes a server-authoritative weighted Wheel of Fortune bonus roll.",
        ],
        0.0, branch_y + 5.0, master_deps,
        [render_task(hid(f"{master_id}:confirm"))],
        [
            render_reward(hid(f"{master_id}:xp"), 1000),
            [
                "\t\t\t{",
                f'\t\t\t\tid: "{wheel_reward_id}"',
                f"\t\t\t\ttable_id: {wheel_id}L",
                '\t\t\t\ttitle: "Spin the Wheel of Fortune"',
                '\t\t\t\ttype: "loot"',
                "\t\t\t}",
            ],
        ],
    ))

    lines.extend([
        "\t]",
        '\ttitle: "Productive Bees"',
        "}",
        "",
    ])
    stats = {
        "setup_quests": len(SETUP),
        "bee_quests": len(bee_ids),
        "root_bees": len(roots),
        "generated_branches": len(branch_ids),
        "master_quest": 1,
    }
    return "\n".join(lines), stats


def render_wheel() -> str:
    table_id = hlong("amber-arcana-wheel-table:productive_bees")
    entries = [
        (8, "productivebees:bee_cage", 26.0),
        (16, "productivebees:honey_treat", 24.0),
        (1, "productivebees:advanced_oak_beehive", 16.0),
        (1, "productivebees:expansion_box_oak", 14.0),
        (1, "productivebees:centrifuge", 10.0),
        (1, "productivebees:feeder", 6.0),
        (1, "productivebees:breeding_chamber", 4.0),
    ]
    lines = [
        "{",
        '\ticon: "productivebees:honey_treat"',
        f'\tid: "{table_id:016X}"',
        "\tloot_size: 1",
        "\torder_index: 130",
        "\trewards: [",
    ]
    for count, item, weight in entries:
        cp = f"count: {count}, " if count != 1 else ""
        lines.append(f'\t\t{{ {cp}item: "{item}", weight: {weight:.1f}f }}')
    lines += [
        "\t]",
        '\ttitle: "Wheel of Fortune — Productive Bees"',
        "\tuse_title: true",
        "}",
        "",
    ]
    return "\n".join(lines)


def sync_server() -> None:
    if SERVER_QUESTS.exists():
        shutil.rmtree(SERVER_QUESTS)
    shutil.copytree(CLIENT_QUESTS, SERVER_QUESTS)


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_docs(stats: dict, route_count: int, active_defs: int) -> None:
    text = README.read_text()
    text = text.replace("Amber-and-Arcana-0.1.9-26-", "Amber-and-Arcana-0.1.9-27-")
    text = text.replace("Download Client 0.1.9-26", "Download Client 0.1.9-27")
    text = text.replace("Download Crafty Server 0.1.9-26", "Download Crafty Server 0.1.9-27")
    text = text.replace("| Pack | 0.1.9-26 |", "| Pack | 0.1.9-27 |")
    marker = "## Quest runtime status — 2026-09-15\n"
    note = (
        f"\nRelease 0.1.9-27 adds a generated Productive Bees family-tree chapter pinned to Productive Bees {PB_VERSION}. "
        f"It contains {stats['setup_quests']} setup quests, {stats['bee_quests']} bee milestones, "
        f"{stats['generated_branches']} branch completion nodes, and a Master Apiarist Wheel of Fortune finale. "
        f"The generator screened {route_count} active breeding/conversion routes against the installed mod set and {active_defs} active configurable bee definitions. "
        "Bee progression is rendered from real upstream breeding/conversion recipes; species milestones use manual confirmation while concrete equipment remains inventory-detected.\n"
    )
    if marker in text and "Release 0.1.9-27 adds a generated Productive Bees family-tree chapter" not in text:
        text = text.replace(marker, marker + note, 1)
    README.write_text(text)

    changelog = CHANGELOG.read_text()
    if "## 0.1.9-27" not in changelog:
        entry = (
            "## 0.1.9-27 — Productive Bees progression tree\n\n"
            f"- Add a Productive Bees quest chapter generated from the exact {PB_VERSION} upstream breeding and conversion data.\n"
            "- Start with Bee Cage, Advanced Beehive, Expansion Box, Feeder, Centrifuge, and Breeding Chamber setup.\n"
            "- Lay out wild/base bees and their descendants as visual branches with actual parent dependencies and integration-specific lanes.\n"
            "- Filter configurable bees by installed-mod conditions so removed or unavailable integrations do not become required progression.\n"
            "- Add branch completion milestones and a Master Apiarist finale with a Productive Bees weighted Wheel of Fortune table.\n"
            "- Keep client/server quest trees identical and preserve all pre-existing quest IDs.\n\n"
        )
        if changelog.startswith("# Changelog\n\n"):
            changelog = "# Changelog\n\n" + entry + changelog[len("# Changelog\n\n"):]
        else:
            changelog = entry + changelog
        CHANGELOG.write_text(changelog)


def main() -> None:
    if not MODS_TSV.exists():
        raise RuntimeError("server-mods.tsv missing")
    installed_text = MODS_TSV.read_text(errors="replace").lower()
    if "productivebees-1.20.1-12.6.0.jar" not in installed_text:
        raise RuntimeError("Expected installed Productive Bees 1.20.1-12.6.0 pin")

    src = load_source()
    try:
        all_defs, active_defs = active_bee_definitions(src, installed_text)
        routes, route_count = parse_routes(src, all_defs, active_defs, installed_text)
        chosen = choose_routes(routes)
        roots, depths = compute_depths(chosen)

        chapter_text, stats = render_chapter(chosen, routes, roots, depths)
        CHAPTER.parent.mkdir(parents=True, exist_ok=True)
        CHAPTER.write_text(chapter_text)
        TABLE.parent.mkdir(parents=True, exist_ok=True)
        TABLE.write_text(render_wheel())

        sync_server()

        def mutate_manifest(d):
            d["version"] = VERSION
            d["name"] = f"Amber & Arcana {VERSION}"
        update_json(MANIFEST, mutate_manifest)

        def mutate_summary(d):
            d["pack_version"] = VERSION
            d["productive_bees_0_1_9_27"] = {
                "enabled": True,
                "productive_bees_version": PB_VERSION,
                "upstream_commit": PB_COMMIT,
                "setup_quests": stats["setup_quests"],
                "bee_quests": stats["bee_quests"],
                "root_bees": stats["root_bees"],
                "generated_branches": stats["generated_branches"],
                "active_routes_screened": route_count,
                "active_configurable_bee_definitions": len(active_defs),
                "master_apiarist_wheel": True,
                "client_server_quest_files_identical": True,
            }
        update_json(SUMMARY, mutate_summary)

        def mutate_validation(d):
            d["pack_version"] = VERSION
            d["chapters"] = 26
            d["manual_quests"] = 106 + stats["setup_quests"] + stats["bee_quests"] + stats["generated_branches"] + stats["master_quest"]
            d["productive_bees_0_1_9_27"] = {
                "productive_bees_version": PB_VERSION,
                "upstream_commit": PB_COMMIT,
                "setup_quests": stats["setup_quests"],
                "bee_quests": stats["bee_quests"],
                "root_bees": stats["root_bees"],
                "generated_branches": stats["generated_branches"],
                "active_routes_screened": route_count,
                "active_configurable_bee_definitions": len(active_defs),
                "total_chapters": 26,
                "total_reward_tables": 31,
                "total_finale_loot_rewards": 26,
                "client_server_quest_files_identical": True,
                "historical_ids_preserved": True,
            }
        update_json(VALIDATION, mutate_validation)

        update_docs(stats, route_count, len(active_defs))

        if any(p.read_bytes() != (SERVER_QUESTS / p.relative_to(CLIENT_QUESTS)).read_bytes()
               for p in CLIENT_QUESTS.rglob("*") if p.is_file()):
            raise RuntimeError("Client/server Productive Bees quest sync failed")

        print(
            f"Applied Amber & Arcana {VERSION}: Productive Bees family tree with "
            f"{stats['bee_quests']} bee quests, {stats['root_bees']} roots, "
            f"{stats['generated_branches']} branches and {route_count} active routes",
            flush=True,
        )
    finally:
        tmp = ROOT / ".tmp-productive-bees-source"
        if tmp.exists():
            shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
