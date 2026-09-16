#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-28"
CREATE_VERSION = "1.20.1-6.0.8"
CREATE_COMMIT = "1a1a9a2819b4f89f78caec41b55ed8cb222fa24b"
CREATE_ARCHIVE = f"https://codeload.github.com/Creators-of-Create/Create/zip/{CREATE_COMMIT}"

CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"
CHAPTER = CLIENT_QUESTS / "chapters/create_engineering.snbt"
TABLE = CLIENT_QUESTS / "reward_tables/wheel_create_engineering.snbt"
MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
MODS_TSV = ROOT / "server/_crafty/server-mods.tsv"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"

CHAPTER_ID = "0C5565DC7663F603"
GETTING_STARTED_GATE = "5DF5A47BBDCD9172"

ANCHORS = {
    "first_rotation": {
        "qid": "1ED63F4805934997",
        "item_tasks": {"create:water_wheel": "F72E447E49B9B1A4", "create:mechanical_press": "DB32483F0ECA7267"},
        "check": "17597223D8AA140A",
        "rewards": [("item", "4CF5E9DE1697B136", "create:andesite_alloy", 8), ("xp", "46F12E8E436F654A", None, 100)],
    },
    "processing_line": {
        "qid": "49A0DF8BF8B13288",
        "item_tasks": {"create:belt_connector": "60EBB3EBF4534609"},
        "check": "0DFA213F45F74EFE",
        "rewards": [("item", "09EE1EC0A7BD54FA", "minecraft:iron_ingot", 12), ("xp", "3D5BF33CC799EF27", None, 150)],
    },
    "precision": {
        "qid": "2B415B8CDDC3ACFF",
        "item_tasks": {"create:precision_mechanism": "C0ACA01B4C80BBE4"},
        "check": "5330479A28BDAE3F",
        "rewards": [("item", "7F94B72F2CF7FCC2", "create:brass_ingot", 6), ("xp", "02B62428010B71D8", None, 200)],
    },
    "steam": {
        "qid": "6A19120000000401",
        "item_tasks": {"create:steam_engine": "0B2726B1E2836F93"},
        "check": "6A19120000000402",
        "rewards": [("item", "682E10436449AE71", "minecraft:copper_block", 4), ("xp", "66FEA6BC6A22BF7D", None, 250)],
    },
    "rails": {
        "qid": "42BD2E092F753492",
        "item_tasks": {"create:track_station": "A32B4E720E7FE605"},
        "check": "266DB38DB0AF235D",
        "rewards": [("item", "65EA8FA9B022DFAF", "minecraft:powered_rail", 16), ("xp", "4BFDAFBF94A53AD6", None, 300)],
    },
    "factory": {
        "qid": "6A19120000000601",
        "item_tasks": {"create:brass_casing": "BE6613FDD637ECF3"},
        "check": "6A19120000000602",
        "rewards": [("item", "0F84366908588733", "minecraft:diamond", 2), ("xp", "38C4AF77A33A2944", None, 400), ("loot", "3955EED61E5751FB", None, 0)],
    },
}

# key, title, items, deps, x, y, xp, description, historical anchor
MILESTONES = [
    ("andesite_alloy", "Andesite Alloy", ["create:andesite_alloy"], ["$getting_started"], 0, 0, 40, "Make Andesite Alloy, the foundation material for early Create machines.", None),
    ("tools", "Engineer's Tools", ["create:goggles", "create:wrench"], ["andesite_alloy"], -5, 2, 40, "Craft Engineer's Goggles and a Wrench so you can inspect stress and reconfigure machines.", None),
    ("andesite_casing", "Andesite Casing", ["create:andesite_casing"], ["andesite_alloy"], 0, 2, 40, "Make Andesite Casing. Many first-tier kinetic machines build on this casing.", None),
    ("shafts_gears", "Shafts & Gears", ["create:shaft", "create:cogwheel", "create:large_cogwheel"], ["andesite_alloy"], 5, 2, 50, "Build shafts and both cogwheel sizes so rotation can be routed and geared.", None),
    ("rotation_control", "Control the Rotation", ["create:gearbox", "create:clutch", "create:gearshift", "create:stressometer", "create:speedometer"], ["shafts_gears", "tools"], 5, 4, 75, "Add direction control, disconnects, and gauges before expanding the workshop.", None),
    ("first_rotation", "First Rotation", ["create:water_wheel", "create:mechanical_press"], ["andesite_casing", "shafts_gears"], 0, 4, 100, "Build renewable rotational power and prove it by running a Mechanical Press.", "first_rotation"),
    ("millstone", "Milling", ["create:millstone"], ["first_rotation"], -4, 6, 60, "Add a Millstone for early crushing and material preparation.", None),
    ("mixer_basin", "Mixing & Basins", ["create:mechanical_mixer", "create:basin"], ["first_rotation"], 0, 6, 75, "Build a Mechanical Mixer over a Basin. This setup later becomes essential for heated alloy recipes.", None),
    ("encased_fan", "Bulk Processing", ["create:encased_fan"], ["first_rotation"], 4, 6, 60, "Build an Encased Fan and learn washing, smoking, blasting, and bulk processing.", None),
    ("processing_line", "A Processing Line", ["create:belt_connector", "create:depot", "create:andesite_funnel"], ["first_rotation", "encased_fan"], 4, 8, 150, "Build a belt, depot, and funnel line so items can move through multiple machines automatically.", "processing_line"),
    ("saw_drill", "Cutting & Drilling", ["create:mechanical_saw", "create:mechanical_drill"], ["first_rotation", "andesite_casing"], -6, 8, 75, "Add Mechanical Saws and Drills for automated cutting, mining, and contraption work.", None),
    ("fluid_pipes", "Pipes & Pumps", ["create:fluid_pipe", "create:mechanical_pump"], ["andesite_casing", "first_rotation"], 9, 8, 75, "Build fluid pipes and a Mechanical Pump. Fluids become a second automation network alongside belts.", None),
    ("fluid_tank", "Fluid Storage", ["create:fluid_tank", "create:copper_casing"], ["fluid_pipes"], 9, 10, 75, "Build Fluid Tanks and Copper Casing for reliable fluid buffering and later steam systems.", None),
    ("drain_spout", "Drain & Spout", ["create:item_drain", "create:spout"], ["fluid_tank", "processing_line"], 9, 12, 90, "Use an Item Drain and Spout to move fluids between items, tanks, and production lines.", None),
    ("hose_pulley", "Hose Pulley", ["create:hose_pulley"], ["fluid_tank"], 13, 12, 75, "Build a Hose Pulley for large-scale fluid intake and bottomless-source setups.", None),
    ("contraption_base", "Moving Contraptions", ["create:mechanical_piston", "create:mechanical_bearing", "create:super_glue"], ["saw_drill", "shafts_gears"], -10, 10, 100, "Build pistons, bearings, and Super Glue so structures can become controlled contraptions.", None),
    ("contraption_lift", "Pulleys & Gantries", ["create:rope_pulley", "create:gantry_shaft", "create:gantry_carriage"], ["contraption_base"], -10, 12, 100, "Add Rope Pulleys and Gantries for elevators, traversing platforms, and precise linear motion.", None),
    ("storage_interfaces", "Contraption I/O", ["create:portable_storage_interface", "create:redstone_contact", "create:contraption_controls"], ["contraption_lift", "processing_line"], -10, 14, 125, "Give moving contraptions safe item transfer, docking detection, and onboard controls.", None),
    ("rose_quartz", "Electron Tubes", ["create:polished_rose_quartz", "create:electron_tube"], ["first_rotation"], 4, 10, 75, "Produce Polished Rose Quartz and Electron Tubes to open the redstone and brass-era control tier.", None),
    ("blaze_burner", "Blaze Burner", ["create:blaze_burner"], ["mixer_basin"], -1, 10, 100, "Capture a Blaze in an empty burner and place it beneath the Basin for heated mixing.", None),
    ("brass_ingot", "Enter the Brass Age", ["create:brass_ingot"], ["mixer_basin", "blaze_burner"], -1, 12, 125, "Heat a Basin and mix Copper with Zinc to make Brass, unlocking advanced automation.", None),
    ("brass_casing", "Brass Casing", ["create:brass_casing"], ["brass_ingot"], -1, 14, 100, "Make Brass Casing for advanced logistics and automation machines.", None),
    ("brass_logistics", "Brass Logistics", ["create:brass_funnel", "create:brass_tunnel", "create:smart_chute"], ["brass_casing", "rose_quartz", "processing_line"], 4, 16, 125, "Build Brass Funnels, Brass Tunnels, and Smart Chutes for filtered routing and controlled extraction.", None),
    ("deployer", "Deployer", ["create:deployer"], ["brass_casing", "rose_quartz", "processing_line"], -1, 16, 125, "Build a Deployer. It applies items during sequenced assembly.", None),
    ("precision", "Precision Mechanisms", ["create:precision_mechanism"], ["deployer", "processing_line", "first_rotation"], -1, 18, 200, "Complete a sequenced assembly loop and produce a Precision Mechanism.", "precision"),
    ("mechanical_arm", "Mechanical Arm", ["create:mechanical_arm"], ["precision", "brass_logistics"], 4, 18, 125, "Build a Mechanical Arm for programmable routing between depots, belts, and inventories.", None),
    ("mechanical_crafter", "Mechanical Crafter", ["create:mechanical_crafter"], ["precision", "rose_quartz"], 8, 18, 150, "Build Mechanical Crafters for recipes larger than the vanilla 3x3 crafting grid.", None),
    ("crushing_wheels", "Crushing Wheels", ["create:crushing_wheel"], ["mechanical_crafter"], 8, 20, 150, "Use Mechanical Crafters to make Crushing Wheels and unlock heavy crushing recipes.", None),
    ("sturdy_sheet", "Sturdy Sheets", ["create:sturdy_sheet"], ["crushing_wheels", "first_rotation"], 8, 22, 125, "Refine obsidian into Sturdy Sheets, a gateway material for railway infrastructure.", None),
    ("redstone_network", "Factory Signals", ["create:redstone_link", "create:content_observer", "create:threshold_switch"], ["rose_quartz", "brass_casing"], 13, 18, 125, "Add wireless redstone links and inventory sensors so the factory can react to its own state.", None),
    ("packager", "Packaging Logistics", ["create:packager", "create:package_frogport"], ["redstone_network", "brass_logistics"], 13, 20, 150, "Package inventory requests and route addressed packages through a Frogport.", None),
    ("repackager", "Repackaging", ["create:repackager"], ["packager"], 13, 22, 125, "Add a Re-Packager so multi-package orders can be recombined before delivery.", None),
    ("stock_network", "Stock Network", ["create:stock_link", "create:stock_ticker", "create:factory_gauge"], ["repackager", "mechanical_arm"], 13, 24, 200, "Build a Stock Link, Stock Ticker, and Factory Gauge to turn storage into a requestable logistics network.", None),
    ("schematics", "Schematics", ["create:schematic_and_quill", "create:schematicannon"], ["precision"], -11, 20, 125, "Capture a build with the Schematic and Quill, then let a Schematicannon reproduce it from supplied materials.", None),
    ("steam", "Steam Under Control", ["create:steam_engine"], ["fluid_tank", "blaze_burner", "brass_casing"], -5, 20, 250, "Build a stable Steam Engine with continuous water, controllable heat, and an emergency disconnect.", "steam"),
    ("railway_casing", "Railway Casing", ["create:railway_casing"], ["sturdy_sheet", "brass_casing"], 18, 24, 125, "Make Railway Casing, the advanced casing tier used by train infrastructure.", None),
    ("track", "Train Track", ["create:track"], ["railway_casing"], 18, 26, 125, "Craft Create Train Track and lay a usable route with room for stations and signaling.", None),
    ("rails", "Rails & Stations", ["create:track_station"], ["track", "precision"], 18, 28, 300, "Build a Track Station and assemble a train on the route.", "rails"),
    ("rail_signaling", "Signals & Observers", ["create:track_signal", "create:track_observer"], ["rails"], 18, 30, 175, "Add Track Signals and Track Observers so multiple trains can share a network safely.", None),
    ("schedule", "Scheduled Trains", ["create:schedule"], ["rail_signaling"], 18, 32, 175, "Create a Train Schedule and complete an automatic trip between stations.", None),
    ("factory", "A Reliable Factory", ["create:brass_casing"], ["stock_network", "storage_interfaces", "steam", "schedule", "crushing_wheels", "drain_spout", "schematics"], 3, 34, 400, "Bring power, processing, fluids, contraptions, logistics, and rail automation into one maintainable factory.", "factory"),
]


def hid(seed: str) -> str:
    value = int.from_bytes(hashlib.sha256(seed.encode()).digest()[:8], "big") & ((1 << 63) - 1)
    return f"{value or 1:016X}"


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def load_source() -> Path:
    print(f"Downloading Create {CREATE_VERSION} source snapshot {CREATE_COMMIT[:12]}...", flush=True)
    with urllib.request.urlopen(CREATE_ARCHIVE, timeout=120) as response:
        data = response.read()
    z = zipfile.ZipFile(io.BytesIO(data))
    roots = {Path(n).parts[0] for n in z.namelist() if n}
    if len(roots) != 1:
        raise RuntimeError("Unexpected Create source archive layout")
    root_name = next(iter(roots))
    dest = ROOT / ".tmp-create-source"
    if dest.exists():
        shutil.rmtree(dest)
    z.extractall(dest)
    src = dest / root_name
    props = (src / "gradle.properties").read_text(errors="replace")
    if "mod_version = 6.0.8" not in props or "minecraft_version = 1.20.1" not in props:
        raise RuntimeError("Pinned Create source does not match installed mc1.20.1-6.0.8")
    return src


def validate_items(src: Path) -> list[str]:
    chunks = []
    for base in (src / "src/generated/resources", src / "src/main/resources", src / "src/main/java"):
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".json", ".java", ".lang", ".mcmeta"}:
                chunks.append(p.read_text(errors="ignore"))
    corpus = "\n".join(chunks)
    items = sorted({item for _, _, its, *_ in MILESTONES for item in its if item.startswith("create:")})
    missing = []
    for item in items:
        path = item.split(":", 1)[1]
        probes = (item, f"block.create.{path}", f"item.create.{path}", f'"{path}"', f"'{path}'")
        if not any(probe in corpus for probe in probes):
            missing.append(item)
    if missing:
        raise RuntimeError("Create milestone IDs not found in pinned 6.0.8 source: " + ", ".join(missing))
    return items


def render_item_task(task_id: str, item: str, count: int = 1) -> list[str]:
    lines = ["\t\t\t{", f'\t\t\t\tid: "{task_id}"', f'\t\t\t\titem: "{item}"']
    if count != 1:
        lines.append(f"\t\t\t\tcount: {count}L")
    lines += ["\t\t\t\tconsume_items: false", '\t\t\t\ttype: "item"', "\t\t\t}"]
    return lines


def render_check(task_id: str) -> list[str]:
    return ["\t\t\t{", f'\t\t\t\tid: "{task_id}"', "\t\t\t\toptional_task: true", '\t\t\t\ttype: "checkmark"', "\t\t\t}"]


def render_xp(reward_id: str, xp: int) -> list[str]:
    return ["\t\t\t{", f'\t\t\t\tid: "{reward_id}"', '\t\t\t\ttype: "xp"', f"\t\t\t\txp: {xp}", "\t\t\t}"]


def render_item_reward(reward_id: str, item: str, count: int) -> list[str]:
    return ["\t\t\t{", f"\t\t\t\tcount: {count}", f'\t\t\t\tid: "{reward_id}"', f'\t\t\t\titem: "{item}"', '\t\t\t\ttype: "item"', "\t\t\t}"]


def render_loot_reward(reward_id: str) -> list[str]:
    return ["\t\t\t{", f'\t\t\t\tid: "{reward_id}"', "\t\t\t\ttable_id: 787970406010393259L", '\t\t\t\ttitle: "Spin the Wheel of Fortune"', '\t\t\t\ttype: "loot"', "\t\t\t}"]


def qid_for(key: str, anchor: str | None) -> str:
    return ANCHORS[anchor]["qid"] if anchor else hid(f"create-0.1.9-28:{key}")


def render_rewards(key: str, xp: int, anchor: str | None) -> list[list[str]]:
    if not anchor:
        return [render_xp(hid(f"create-0.1.9-28:{key}:xp"), xp)]
    result = []
    for typ, rid, item, amount in ANCHORS[anchor]["rewards"]:
        if typ == "xp":
            result.append(render_xp(rid, amount))
        elif typ == "item":
            result.append(render_item_reward(rid, item, amount))
        else:
            result.append(render_loot_reward(rid))
    return result


def render_chapter() -> tuple[str, dict]:
    qids = {key: qid_for(key, anchor) for key, _, _, _, _, _, _, _, anchor in MILESTONES}
    lines = ["{", "\tdefault_hide_dependency_lines: false", '\tdefault_quest_shape: "hexagon"', '\tfilename: "create_engineering"', '\tgroup: ""', '\ticon: "create:mechanical_press"', f'\tid: "{CHAPTER_ID}"', "\torder_index: 10", "\tquest_links: []", "\tquests: ["]
    item_task_count = 0
    edge_count = 0
    for key, title, items, deps, x, y, xp, desc, anchor in MILESTONES:
        resolved = [GETTING_STARTED_GATE if dep == "$getting_started" else qids[dep] for dep in deps]
        edge_count += len(resolved)
        lines.append("\t\t{")
        if resolved:
            lines.append("\t\t\tdependencies: [")
            lines.extend(f'\t\t\t\t"{dep}"' for dep in resolved)
            lines.append("\t\t\t]")
        lines += ["\t\t\tdescription: [", f'\t\t\t\t"{esc(desc)}"', '\t\t\t\t"Progression is inventory-detected; dependencies show the setup that should be completed first."', "\t\t\t]", f'\t\t\ticon: "{items[0]}"', f'\t\t\tid: "{qids[key]}"', "\t\t\trewards: ["]
        for reward in render_rewards(key, xp, anchor):
            lines.extend(reward)
        lines += ["\t\t\t]", '\t\t\tshape: "hexagon"', "\t\t\tsize: 1.0d", f'\t\t\tsubtitle: "Create progression — {len(items)} required milestone item{"s" if len(items) != 1 else ""}"', "\t\t\ttasks: ["]
        anchor_data = ANCHORS.get(anchor or "")
        for item in items:
            task_id = anchor_data["item_tasks"].get(item) if anchor_data else None
            count = 8 if key == "factory" and item == "create:brass_casing" else 1
            lines.extend(render_item_task(task_id or hid(f"create-0.1.9-28:{key}:item:{item}"), item, count))
            item_task_count += 1
        if anchor_data:
            lines.extend(render_check(anchor_data["check"]))
        lines += ["\t\t\t]", f'\t\t\ttitle: "{esc(title)}"', f"\t\t\tx: {float(x):.1f}d", f"\t\t\ty: {float(y):.1f}d", "\t\t}"]
    lines += ["\t]", '\ttitle: "Create Engineering"', "}", ""]
    stats = {"quests": len(MILESTONES), "new_quests": len(MILESTONES) - len(ANCHORS), "preserved_anchor_quests": len(ANCHORS), "milestone_item_tasks": item_task_count, "required_dependency_edges": edge_count}
    return "\n".join(lines), stats


def render_wheel() -> str:
    entries = [(16, "create:andesite_alloy", 20.0), (8, "create:brass_ingot", 17.0), (4, "create:electron_tube", 14.0), (2, "create:precision_mechanism", 10.0), (1, "create:mechanical_arm", 8.0), (1, "create:mechanical_crafter", 8.0), (1, "create:crushing_wheel", 7.0), (1, "create:steam_engine", 6.0), (1, "create:track_station", 5.0), (1, "create:stock_ticker", 5.0)]
    lines = ["{", '\ticon: "create:precision_mechanism"', '\tid: "0AEF6EE8CFC512AB"', "\tloot_size: 1", "\torder_index: 109", "\trewards: ["]
    for count, item, weight in entries:
        cp = f"count: {count}, " if count != 1 else ""
        lines.append(f'\t\t{{ {cp}item: "{item}", weight: {weight:.1f}f }}')
    lines += ["\t]", '\ttitle: "Wheel of Fortune — Create Engineering"', "\tuse_title: true", "}", ""]
    return "\n".join(lines)


def sync_server() -> None:
    if SERVER_QUESTS.exists():
        shutil.rmtree(SERVER_QUESTS)
    shutil.copytree(CLIENT_QUESTS, SERVER_QUESTS)


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_docs(stats: dict) -> None:
    text = README.read_text()
    text = text.replace("Amber-and-Arcana-0.1.9-27-", "Amber-and-Arcana-0.1.9-28-")
    text = text.replace("Download Client 0.1.9-27", "Download Client 0.1.9-28")
    text = text.replace("Download Crafty Server 0.1.9-27", "Download Crafty Server 0.1.9-28")
    text = text.replace("| Pack | 0.1.9-27 |", "| Pack | 0.1.9-28 |")
    marker = "## Quest runtime status — 2026-09-15\n"
    note = (f"\nRelease 0.1.9-28 rebuilds Create Engineering into a {stats['quests']}-quest progression tree pinned to Create {CREATE_VERSION}. "
            f"It preserves the six historical Create quest IDs while adding {stats['new_quests']} machine/setup milestones and {stats['required_dependency_edges']} explicit dependency edges. "
            "The tree walks from Andesite Alloy and first rotation through processing, fluids, contraptions, brass, precision mechanisms, crushing, package/stock logistics, steam, schematics, and scheduled railways. Concrete machines and components complete automatically from inventory; the final factory retains its Create Wheel of Fortune reward.\n")
    if marker in text and "Release 0.1.9-28 rebuilds Create Engineering" not in text:
        text = text.replace(marker, marker + note, 1)
    README.write_text(text)

    changelog = CHANGELOG.read_text()
    if "## 0.1.9-28" not in changelog:
        entry = ("## 0.1.9-28 — Create progression tree\n\n"
                 f"- Expand Create Engineering from 6 quests to {stats['quests']} machine and setup milestones.\n"
                 f"- Pin validation to Create {CREATE_VERSION} / upstream commit `{CREATE_COMMIT}`.\n"
                 "- Guide progression through kinetics, processing, fluids, contraptions, brass, precision assembly, logistics, steam power, schematics, and trains.\n"
                 "- Preserve the six historical Create quest IDs and their task/reward IDs so existing progression is not discarded.\n"
                 "- Keep concrete machine milestones inventory-detected and retain the Create Wheel of Fortune finale.\n"
                 "- Keep client and dedicated-server quest trees byte-identical.\n\n")
        changelog = "# Changelog\n\n" + entry + changelog[len("# Changelog\n\n"):] if changelog.startswith("# Changelog\n\n") else entry + changelog
        CHANGELOG.write_text(changelog)


def main() -> None:
    installed = MODS_TSV.read_text(errors="replace")
    if "create-1.20.1-6.0.8.jar" not in installed:
        raise RuntimeError("Expected installed Create 1.20.1-6.0.8 pin")
    src = load_source()
    try:
        validated_items = validate_items(src)
        chapter_text, stats = render_chapter()
        CHAPTER.write_text(chapter_text)
        TABLE.write_text(render_wheel())
        sync_server()

        update_json(MANIFEST, lambda d: d.update(version=VERSION, name=f"Amber & Arcana {VERSION}"))

        def summary_mutate(d):
            d["pack_version"] = VERSION
            d["create_progression_0_1_9_28"] = {"enabled": True, "create_version": CREATE_VERSION, "upstream_commit": CREATE_COMMIT, **stats, "validated_create_item_ids": len(validated_items), "historical_create_quest_ids_preserved": True, "client_server_quest_files_identical": True}
        update_json(SUMMARY, summary_mutate)

        def validation_mutate(d):
            previous_manual = int(d.get("manual_quests", 193))
            d["pack_version"] = VERSION
            d["manual_quests"] = previous_manual - len(ANCHORS) + stats["quests"]
            d["create_progression_0_1_9_28"] = {"create_version": CREATE_VERSION, "upstream_commit": CREATE_COMMIT, **stats, "validated_create_item_ids": len(validated_items), "total_chapters": 26, "total_reward_tables": 31, "total_finale_loot_rewards": 26, "historical_create_quest_ids_preserved": True, "client_server_quest_files_identical": True}
        update_json(VALIDATION, validation_mutate)
        update_docs(stats)

        if any(p.read_bytes() != (SERVER_QUESTS / p.relative_to(CLIENT_QUESTS)).read_bytes() for p in CLIENT_QUESTS.rglob("*") if p.is_file()):
            raise RuntimeError("Client/server Create quest sync failed")

        print(f"Applied Amber & Arcana {VERSION}: Create Engineering now has {stats['quests']} quests, {stats['milestone_item_tasks']} milestone item tasks, and {stats['required_dependency_edges']} dependency edges", flush=True)
    finally:
        tmp = ROOT / ".tmp-create-source"
        if tmp.exists():
            shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
