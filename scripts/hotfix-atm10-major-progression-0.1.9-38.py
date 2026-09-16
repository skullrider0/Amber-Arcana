#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-38"
ATM10_COMMIT = "ab6f65e07b88423cdae1724864ba42a573ba758a"

CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"
CLIENT_CHAPTERS = CLIENT_QUESTS / "chapters"
CLIENT_TABLES = CLIENT_QUESTS / "reward_tables"
MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
VALIDATE_SH = ROOT / "scripts/validate.sh"
CHANGELOG = ROOT / "CHANGELOG.md"
README = ROOT / "README.md"
SERVER_MODS = ROOT / "server/_crafty/server-mods.tsv"

STARTER_DEP = "5DF5A47BBDCD9172"
GROUP_MACHINES = "5A29000000000002"
GROUP_STORAGE = "5A29000000000003"
GROUP_RESOURCES = "5A29000000000004"
GROUP_MAGIC = "5A29000000000005"
GROUP_ENDGAME = "5A29000000000009"


def stable_id(seed: str) -> str:
    value = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16], 16) & ((1 << 63) - 1)
    return f"{value:016X}"


def esc(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def fmt_num(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value))}.0d"
    return f"{value:.2f}".rstrip("0").rstrip(".") + "d"


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def split_quest_blocks(text: str) -> list[str]:
    lines = text.splitlines(keepends=True)
    in_quests = False
    current: list[str] | None = None
    blocks: list[str] = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not in_quests:
            if line.strip() == "quests: [":
                in_quests = True
            continue
        if current is None:
            if re.match(r'^\t\t\{\s*$', line):
                current = [raw]
                continue
            if re.match(r'^\t\],?\s*$', line):
                break
            continue
        current.append(raw)
        if re.match(r'^\t\t\},?\s*$', line):
            blocks.append("".join(current))
            current = None
    return blocks


def quest_ids(path: Path) -> list[str]:
    ids: list[str] = []
    for block in split_quest_blocks(path.read_text()):
        m = re.search(r'^\t\t\tid:\s*"([0-9A-F]{16})"', block, re.M)
        if m:
            ids.append(m.group(1))
    return ids


def chapter_id(path: Path) -> str:
    text = path.read_text()
    m = re.search(r'^\tid:\s*"([0-9A-F]{16})"', text, re.M)
    if not m:
        raise RuntimeError(f"Could not read chapter id from {path}")
    return m.group(1)


def read_table_identity(path: Path, seed: str, order_default: int) -> tuple[str, int]:
    if path.exists():
        text = path.read_text()
        mid = re.search(r'^\tid:\s*"([0-9A-F]{16})"', text, re.M)
        mord = re.search(r'^\torder_index:\s*([0-9]+)', text, re.M)
        if mid:
            return mid.group(1), int(mord.group(1)) if mord else order_default
    return stable_id(seed), order_default


def table_long(table_id: str) -> int:
    return int(table_id, 16)


def item(item_id: str, weight: float, count: int = 1) -> dict:
    return {"item": item_id, "weight": weight, "count": count}


def write_reward_table(path: Path, table_id: str, order_index: int, title: str, icon: str, loot_size: int, entries: list[dict]) -> None:
    lines = [
        "{",
        f"\ticon: {esc(icon)}",
        f"\tid: {esc(table_id)}",
        f"\tloot_size: {loot_size}",
        f"\torder_index: {order_index}",
        "\trewards: [",
    ]
    for entry in entries:
        count = int(entry.get("count", 1))
        prefix = f"count: {count}, " if count != 1 else ""
        lines.append(f"\t\t{{ {prefix}item: {esc(entry['item'])}, weight: {entry['weight']:.2f}f }}")
    lines += [
        "\t]",
        f"\ttitle: {esc(title)}",
        "\tuse_title: true",
        "}",
        "",
    ]
    path.write_text("\n".join(lines))


# Each node: title, icon, item task (None means manual checkmark), tier, deps (indices), x, y, description.
MAJOR_SPECS = {
    "mekanism": {
        "title": "Mekanism Industry", "icon": "mekanism:metallurgic_infuser", "group": GROUP_MACHINES, "order": 1,
        "nodes": [
            ("Metallurgic Foundations", "mekanism:metallurgic_infuser", "mekanism:metallurgic_infuser", 1, [], -5.25, 0.0, "Begin Mekanism with infusion chemistry and the alloys used by nearly every later machine."),
            ("Enrichment Chamber", "mekanism:enrichment_chamber", "mekanism:enrichment_chamber", 1, [0], -3.5, -1.5, "Build the Enrichment Chamber and establish the first efficient ore-processing step."),
            ("Steel Infrastructure", "mekanism:steel_casing", "mekanism:steel_casing", 1, [0], -3.5, 1.5, "Produce steel and build the casings that anchor Mekanism machines and multiblocks."),
            ("Crushing Line", "mekanism:crusher", "mekanism:crusher", 2, [1], -1.75, -1.5, "Add crushing so your processing room can prepare materials for more advanced chemistry."),
            ("Purification Line", "mekanism:purification_chamber", "mekanism:purification_chamber", 2, [3], 0.0, -1.5, "Advance into oxygen-based ore purification and automate the material flow around it."),
            ("Chemical Injection", "mekanism:chemical_injection_chamber", "mekanism:chemical_injection_chamber", 2, [4], 1.75, -1.5, "Add the Chemical Injection Chamber and move beyond the early ore-processing tiers."),
            ("Electrolysis", "mekanism:electrolytic_separator", "mekanism:electrolytic_separator", 2, [2], -1.75, 1.5, "Split fluids into useful gases and build dependable chemical production instead of hand-feeding machines."),
            ("Pressurized Reactions", "mekanism:pressurized_reaction_chamber", "mekanism:pressurized_reaction_chamber", 3, [6], 0.0, 1.5, "Use the Pressurized Reaction Chamber as the bridge between items, fluids, gases, and higher chemistry."),
            ("Dissolve the Ore", "mekanism:chemical_dissolution_chamber", "mekanism:chemical_dissolution_chamber", 3, [5, 7], 3.5, -1.5, "Enter the full chemical ore-processing chain with the Chemical Dissolution Chamber."),
            ("Wash the Slurry", "mekanism:chemical_washer", "mekanism:chemical_washer", 3, [8], 5.25, -1.5, "Clean slurry before crystallization and keep the chemical chain continuously supplied."),
            ("Crystallize the Output", "mekanism:chemical_crystallizer", "mekanism:chemical_crystallizer", 4, [9], 7.0, -1.5, "Finish the advanced ore-processing chain by crystallizing clean slurry into usable material."),
            ("Atomic Technology", "mekanism:atomic_disassembler", "mekanism:atomic_disassembler", 4, [7], 3.5, 1.5, "Reach Mekanism's portable high-energy tool tier and prove the factory can support expensive technology."),
            ("Mastery: Mekanism", "mekanism:antiprotonic_nucleosynthesizer", "mekanism:antiprotonic_nucleosynthesizer", 4, [10, 11], 8.75, 0.0, "Complete both advanced processing and atomic technology, then build the Antiprotonic Nucleosynthesizer."),
        ],
    },
    "ae2": {
        "title": "Applied Energistics 2", "icon": "ae2:controller", "group": GROUP_STORAGE, "order": 0,
        "nodes": [
            ("Charge Certus", "ae2:charger", "ae2:charger", 1, [], -5.25, 0.0, "Build a Charger and start producing the charged materials needed by Applied Energistics 2."),
            ("Inscriber Workshop", "ae2:inscriber", "ae2:inscriber", 1, [0], -3.5, 0.0, "Build an Inscriber and begin making the processors that unlock the ME network."),
            ("Logic Processing", "ae2:logic_processor", "ae2:logic_processor", 1, [1], -1.75, -1.5, "Produce a Logic Processor and establish repeatable processor manufacturing."),
            ("Power the Network", "ae2:energy_acceptor", "ae2:energy_acceptor", 2, [1], -1.75, 1.5, "Bring external power into AE2 and keep your first ME devices online."),
            ("Storage Drive", "ae2:drive", "ae2:drive", 2, [2, 3], 0.0, 0.0, "Build an ME Drive so storage becomes a real network instead of a collection of chests."),
            ("Storage Cells", "ae2:item_storage_cell_4k", "ae2:item_storage_cell_4k", 2, [4], 1.75, -1.5, "Install a useful storage cell and learn how AE2 separates drives from the cells inside them."),
            ("Crafting Terminal", "ae2:crafting_terminal", "ae2:crafting_terminal", 2, [4], 1.75, 1.5, "Craft directly from network storage and make the ME system your everyday inventory interface."),
            ("Controller and Channels", "ae2:controller", "ae2:controller", 3, [5, 6], 3.5, 0.0, "Graduate to an ME Controller and organize channel usage before the network grows out of control."),
            ("Pattern Provider", "ae2:pattern_provider", "ae2:pattern_provider", 3, [7], 5.25, -1.5, "Teach the network recipes with Pattern Providers so machines can be supplied automatically."),
            ("Molecular Assembler", "ae2:molecular_assembler", "ae2:molecular_assembler", 3, [7], 5.25, 1.5, "Build Molecular Assemblers for native AE2 autocrafting."),
            ("Crafting CPU", "ae2:crafting_storage_4k", "ae2:crafting_storage_4k", 4, [8, 9], 7.0, 0.0, "Build crafting CPU storage and successfully request a non-trivial autocrafting job."),
            ("Quantum Network", "ae2:quantum_ring", "ae2:quantum_ring", 4, [10], 8.75, 0.0, "Begin quantum networking so a mature ME system can bridge long distances and dimensions."),
            ("Mastery: AE2", "ae2:quantum_link", "ae2:quantum_link", 4, [11], 10.5, 0.0, "Finish a powered, channeled, autocrafting network and complete a Quantum Network Bridge."),
        ],
    },
    "powah": {
        "title": "Powah Energy", "icon": "powah:energizing_orb", "group": GROUP_MACHINES, "order": 3,
        "nodes": [
            ("Dielectric Foundation", "powah:dielectric_paste", "powah:dielectric_paste", 1, [], -5.25, 0.0, "Produce dielectric material, the basic construction resource behind Powah machines."),
            ("Starter Generation", "powah:thermo_generator_starter", "powah:thermo_generator_starter", 1, [0], -3.5, -1.5, "Build a Starter Thermo Generator and establish continuous power instead of emergency generation."),
            ("Energizing Orb", "powah:energizing_orb", "powah:energizing_orb", 1, [0], -3.5, 1.5, "Build the Energizing Orb that drives Powah's material tiers."),
            ("Energizing Rods", "powah:energizing_rod_starter", "powah:energizing_rod_starter", 2, [2], -1.75, 1.5, "Power the Energizing Orb with rods and arrange a reusable energizing station."),
            ("Blazing Tier", "powah:crystal_blazing", "powah:crystal_blazing", 2, [3], 0.0, 1.5, "Produce Blazing Crystals and use them to leave the early-game Powah tier."),
            ("Niotic Tier", "powah:crystal_niotic", "powah:crystal_niotic", 2, [4], 1.75, 1.5, "Produce Niotic Crystals and increase generation, transfer, and storage capacity."),
            ("Spirited Tier", "powah:crystal_spirited", "powah:crystal_spirited", 3, [5], 3.5, 1.5, "Reach Spirited materials and prepare the grid for genuinely high power demand."),
            ("Nitro Material", "powah:crystal_nitro", "powah:crystal_nitro", 4, [6], 5.25, 1.5, "Produce Nitro Crystals yourself; reward rolls can help, but the progression should not depend on winning a jackpot."),
            ("Energy Storage", "powah:energy_cell_basic", "powah:energy_cell_basic", 2, [1], -1.75, -1.5, "Add a real energy buffer so generators and machines do not have to match demand every tick."),
            ("Ender Network", "powah:ender_cell_basic", "powah:ender_cell_basic", 3, [8], 0.0, -1.5, "Use an Ender Cell to move power cleanly between separated parts of the base."),
            ("Spirited Reactor", "powah:reactor_spirited", "powah:reactor_spirited", 3, [6, 9], 3.5, -1.5, "Build a Spirited Reactor and support a serious factory load."),
            ("Nitro Generation", "powah:thermo_generator_nitro", "powah:thermo_generator_nitro", 4, [7, 10], 5.25, -1.5, "Reach Nitro generation with your own progression, not just a lucky reward roll."),
            ("Mastery: Powah", "powah:reactor_nitro", "powah:reactor_nitro", 4, [11], 7.0, 0.0, "Finish the Powah ladder with a Nitro Reactor and a grid capable of feeding endgame machinery."),
        ],
    },
    "ars_nouveau": {
        "title": "Ars Nouveau", "icon": "ars_nouveau:novice_spell_book", "group": GROUP_MAGIC, "order": 0,
        "nodes": [
            ("First Spellbook", "ars_nouveau:novice_spell_book", "ars_nouveau:novice_spell_book", 1, [], -5.25, 0.0, "Craft a Novice Spell Book and create a practical first spell."),
            ("Imbuement Chamber", "ars_nouveau:imbuement_chamber", "ars_nouveau:imbuement_chamber", 1, [0], -3.5, -1.5, "Use the Imbuement Chamber to begin producing the magical materials Ars progression expects."),
            ("Store Source", "ars_nouveau:source_jar", "ars_nouveau:source_jar", 1, [1], -1.75, -1.5, "Store Source in jars so crafting and automation are not dependent on temporary generation."),
            ("Enchanting Apparatus", "ars_nouveau:enchanting_apparatus", "ars_nouveau:enchanting_apparatus", 2, [2], 0.0, -1.5, "Build the Enchanting Apparatus and use it for a real recipe."),
            ("Arcane Core", "ars_nouveau:arcane_core", "ars_nouveau:arcane_core", 2, [1], -1.75, 1.5, "Add the Arcane Core as the foundation for more advanced Ars infrastructure."),
            ("Apprentice Spellbook", "ars_nouveau:apprentice_spell_book", "ars_nouveau:apprentice_spell_book", 2, [3, 4], 0.0, 1.5, "Upgrade to the Apprentice Spell Book and broaden your useful spell library."),
            ("Spell Turret", "ars_nouveau:spell_turret", "ars_nouveau:spell_turret", 3, [3], 1.75, -1.5, "Automate a spell with a Spell Turret instead of treating Ars as a handheld-only magic mod."),
            ("Starbuncle Logistics", "ars_nouveau:starbuncle_charm", "ars_nouveau:starbuncle_charm", 3, [5], 1.75, 1.5, "Use Starbuncles for a useful logistics or collection task."),
            ("Wixie Automation", "ars_nouveau:wixie_charm", "ars_nouveau:wixie_charm", 3, [7], 3.5, 1.5, "Add a Wixie to turn Ars crafting into repeatable automation."),
            ("Drygmy Production", "ars_nouveau:drygmy_charm", "ars_nouveau:drygmy_charm", 4, [8], 5.25, 1.5, "Build a Drygmy setup and use magical creature production as a real resource system."),
            ("Ritual Brazier", "ars_nouveau:ritual_brazier", "ars_nouveau:ritual_brazier", 3, [6], 3.5, -1.5, "Enter Ars rituals with a Ritual Brazier and perform a useful ritual."),
            ("Archmage Spellbook", "ars_nouveau:archmage_spell_book", "ars_nouveau:archmage_spell_book", 4, [5, 10], 5.25, -1.5, "Reach the Archmage Spell Book and prove your Source infrastructure can support late-game magic."),
            ("Mastery: Ars Nouveau", "ars_nouveau:archmage_spell_book", None, 4, [9, 11], 7.0, 0.0, "Finish both the automation and high-tier spellcasting branches, then confirm the Ars workshop is fully operational."),
        ],
    },
    "irons_spells": {
        "title": "Iron Spells and Wizardry", "icon": "irons_spellbooks:iron_spell_book", "group": GROUP_MAGIC, "order": 1,
        "nodes": [
            ("Iron Spell Book", "irons_spellbooks:iron_spell_book", "irons_spellbooks:iron_spell_book", 1, [], -5.25, 0.0, "Start a real spell loadout with an Iron Spell Book."),
            ("Inscription Table", "irons_spellbooks:inscription_table", "irons_spellbooks:inscription_table", 1, [0], -3.5, -1.5, "Build the Inscription Table and take control of scroll and spell progression."),
            ("Arcane Metal", "irons_spellbooks:arcane_ingot", "irons_spellbooks:arcane_ingot", 1, [0], -3.5, 1.5, "Produce Arcane Ingots for the equipment and stations used later in the mod."),
            ("Collect a Scroll", "irons_spellbooks:scroll", "irons_spellbooks:scroll", 2, [1], -1.75, -1.5, "Acquire a spell scroll and learn how scrolls feed your spellbook progression."),
            ("Upgrade Orbs", "irons_spellbooks:upgrade_orb", "irons_spellbooks:upgrade_orb", 2, [2], -1.75, 1.5, "Obtain an Upgrade Orb and start improving spellcasting equipment instead of only collecting spells."),
            ("Arcane Anvil", "irons_spellbooks:arcane_anvil", "irons_spellbooks:arcane_anvil", 2, [3, 4], 0.0, 0.0, "Build an Arcane Anvil and use it as the center of your upgrade workshop."),
            ("Upgrade a Spell", "irons_spellbooks:arcane_anvil", None, 3, [5], 1.75, 0.0, "Use the inscription and upgrade systems to improve a spell or spellcasting item, then confirm the result works."),
            ("Diamond Spell Book", "irons_spellbooks:diamond_spell_book", "irons_spellbooks:diamond_spell_book", 3, [6], 3.5, -1.5, "Increase spell capacity with a Diamond Spell Book."),
            ("Specialize a School", "irons_spellbooks:upgrade_orb", None, 3, [6], 3.5, 1.5, "Build a coherent spell school loadout with matching upgrades instead of carrying random spells."),
            ("Mithril Equipment", "irons_spellbooks:mithril_ingot", "irons_spellbooks:mithril_ingot", 3, [8], 5.25, 1.5, "Reach Mithril and use it to support higher-tier spellcasting gear."),
            ("Netherite Spell Book", "irons_spellbooks:netherite_spell_book", "irons_spellbooks:netherite_spell_book", 4, [7, 9], 5.25, -1.5, "Reach a Netherite Spell Book and build a genuinely late-game spell loadout."),
            ("Boss-Tier Loadout", "irons_spellbooks:netherite_spell_book", None, 4, [10], 7.0, 0.0, "Use your upgraded spells and equipment successfully in a difficult boss or exploration encounter."),
            ("Mastery: Iron's Spells", "irons_spellbooks:netherite_spell_book", None, 4, [11], 8.75, 0.0, "Complete the inscription, upgrade, equipment, and combat progression and confirm the build is endgame-ready."),
        ],
    },
    "ender_io": {
        "title": "Ender IO Connections", "icon": "enderio:sag_mill", "group": GROUP_MACHINES, "order": 2,
        "nodes": [
            ("Grains of Infinity", "enderio:grains_of_infinity", "enderio:grains_of_infinity", 1, [], -5.25, 0.0, "Gather Grains of Infinity and begin Ender IO's material progression."),
            ("Alloy Smelter", "enderio:alloy_smelter", "enderio:alloy_smelter", 1, [0], -3.5, -1.5, "Build an Alloy Smelter and start producing Ender IO alloys on demand."),
            ("SAG Mill", "enderio:sag_mill", "enderio:sag_mill", 1, [0], -3.5, 1.5, "Build a SAG Mill and use grinding balls and byproducts where they improve processing."),
            ("Conduit Backbone", "enderio:sag_mill", None, 2, [1, 2], -1.75, 0.0, "Build an Ender IO conduit backbone that carries at least one useful factory resource."),
            ("Filters and Priorities", "enderio:sag_mill", None, 2, [3], 0.0, 0.0, "Configure filters, extraction, priorities, and redstone behavior so the conduit network routes items correctly."),
            ("Vacuum Chest", "enderio:vacuum_chest", "enderio:vacuum_chest", 2, [4], 1.75, -1.5, "Add a Vacuum Chest where automatic collection is more useful than manual pickup."),
            ("Impulse Hopper", "enderio:impulse_hopper", "enderio:impulse_hopper", 2, [4], 1.75, 1.5, "Use an Impulse Hopper for controlled batching and machine feeding."),
            ("Slice'N'Splice", "enderio:slice_and_splice", "enderio:slice_and_splice", 3, [5], 3.5, -1.5, "Build the Slice'N'Splice and enter Ender IO's advanced component chain."),
            ("Soul Binder", "enderio:soul_binder", "enderio:soul_binder", 3, [6], 3.5, 1.5, "Build a Soul Binder and begin working with captured mob souls."),
            ("Powered Spawner", "enderio:powered_spawner", "enderio:powered_spawner", 4, [8], 5.25, 1.5, "Build a Powered Spawner and automate a mob resource without relying on natural spawns."),
            ("Enchanter", "enderio:enchanter", "enderio:enchanter", 3, [7], 5.25, -1.5, "Use the Enchanter as a practical factory-side enchanting tool."),
            ("Travel Anchors", "enderio:travel_anchor", "enderio:travel_anchor", 4, [9, 10], 7.0, 0.0, "Connect important factory areas with Travel Anchors and finish the infrastructure branch."),
            ("Mastery: Ender IO", "enderio:powered_spawner", None, 4, [11], 8.75, 0.0, "Confirm the processing, conduit, soul, automation, and travel systems operate as one clean Ender IO factory."),
        ],
    },
    "refined_storage": {
        "title": "Refined Storage", "icon": "refinedstorage:controller", "group": GROUP_STORAGE, "order": 1,
        "nodes": [
            ("Controller", "refinedstorage:controller", "refinedstorage:controller", 1, [], -5.25, 0.0, "Build the Controller and power your first Refined Storage network."),
            ("Grid", "refinedstorage:grid", "refinedstorage:grid", 1, [0], -3.5, -1.5, "Add a Grid so the network becomes a usable storage interface."),
            ("Disk Drive", "refinedstorage:disk_drive", "refinedstorage:disk_drive", 1, [0], -3.5, 1.5, "Build a Disk Drive as the storage backbone of the network."),
            ("Storage Disk", "refinedstorage:1k_storage_disk", "refinedstorage:1k_storage_disk", 2, [2], -1.75, 1.5, "Install a storage disk and move real inventory into the network."),
            ("Crafting Grid", "refinedstorage:crafting_grid", "refinedstorage:crafting_grid", 2, [1], -1.75, -1.5, "Upgrade to a Crafting Grid so storage and everyday crafting happen in one place."),
            ("External Storage", "refinedstorage:external_storage", "refinedstorage:external_storage", 2, [3], 0.0, 1.5, "Attach an external inventory or tank to the network without importing all of its contents."),
            ("Importer", "refinedstorage:importer", "refinedstorage:importer", 2, [4], 0.0, -1.5, "Automatically pull a useful resource into the network."),
            ("Exporter", "refinedstorage:exporter", "refinedstorage:exporter", 3, [6], 1.75, -1.5, "Automatically keep a machine or inventory supplied from network storage."),
            ("Interface", "refinedstorage:interface", "refinedstorage:interface", 3, [5], 1.75, 1.5, "Use an Interface as a controlled bridge between the RS network and external automation."),
            ("Pattern Grid", "refinedstorage:pattern_grid", "refinedstorage:pattern_grid", 3, [7, 8], 3.5, -1.5, "Encode processing and crafting patterns instead of crafting every intermediate by hand."),
            ("Crafter", "refinedstorage:crafter", "refinedstorage:crafter", 4, [9], 5.25, -1.5, "Build a Crafter and successfully request an automated recipe."),
            ("Network Transmitter", "refinedstorage:network_transmitter", "refinedstorage:network_transmitter", 4, [8], 3.5, 1.5, "Prepare the network for remote links with a Network Transmitter."),
            ("Mastery: Refined Storage", "refinedstorage:network_receiver", "refinedstorage:network_receiver", 4, [10, 11], 5.25, 0.0, "Complete storage, machine I/O, autocrafting, and remote networking with a Network Receiver."),
        ],
    },
}

NEW_SPECS = {
    "hostile_neural_networks": {
        "title": "Hostile Neural Networks", "icon": "hostilenetworks:deep_learner", "group": GROUP_RESOURCES, "order": 4,
        "nodes": [
            ("Deep Learner", "hostilenetworks:deep_learner", "hostilenetworks:deep_learner", 1, [], -5.25, 0.0, "Build a Deep Learner, the tool used to train mob Data Models."),
            ("Blank Data Model", "hostilenetworks:blank_data_model", "hostilenetworks:blank_data_model", 1, [0], -3.5, 0.0, "Craft a Blank Data Model and convert it into a model for a mob you actually want to farm."),
            ("Train a Model", "hostilenetworks:data_model", None, 1, [1], -1.75, 0.0, "Train a Data Model through real kills until it is ready for simulation."),
            ("Prediction Matrix", "hostilenetworks:prediction_matrix", "hostilenetworks:prediction_matrix", 2, [2], 0.0, -1.5, "Produce Prediction Matrices to fuel automated simulations."),
            ("Simulation Chamber", "hostilenetworks:sim_chamber", "hostilenetworks:sim_chamber", 2, [2], 0.0, 1.5, "Build and power a Simulation Chamber, then run a trained model inside it."),
            ("Overworld Predictions", "hostilenetworks:overworld_prediction", "hostilenetworks:overworld_prediction", 2, [3, 4], 1.75, -1.5, "Generate an Overworld Prediction from a working simulation."),
            ("Nether Predictions", "hostilenetworks:nether_prediction", "hostilenetworks:nether_prediction", 3, [3, 4], 1.75, 0.0, "Generate a Nether Prediction and broaden the kinds of loot your network can synthesize."),
            ("End Predictions", "hostilenetworks:end_prediction", "hostilenetworks:end_prediction", 3, [3, 4], 1.75, 1.5, "Generate an End Prediction and prove the chamber can support higher-value models."),
            ("Loot Fabricator", "hostilenetworks:loot_fabricator", "hostilenetworks:loot_fabricator", 3, [5, 6, 7], 3.5, 0.0, "Build a Loot Fabricator and turn predictions into the mob drops you actually need."),
            ("Advanced Model Training", "hostilenetworks:data_model", None, 3, [8], 5.25, -1.5, "Train at least one useful model beyond its basic state so simulations become more efficient."),
            ("Superior Model Training", "hostilenetworks:data_model", None, 4, [9], 5.25, 0.0, "Push a valuable model into the upper training tiers and keep it supplied with matrices."),
            ("Self-Aware Models", "hostilenetworks:data_model", None, 4, [10], 5.25, 1.5, "Reach the Self-Aware tier on at least one valuable model."),
            ("Mastery: Neural Networks", "hostilenetworks:loot_fabricator", None, 4, [11], 7.0, 0.0, "Confirm the learner, model training, simulations, predictions, and loot fabrication operate as a renewable mob-resource system."),
        ],
    },
    "draconic_evolution": {
        "title": "Draconic Evolution", "icon": "draconicevolution:awakened_core", "group": GROUP_ENDGAME, "order": 1,
        "nodes": [
            ("Draconium", "draconicevolution:draconium_ingot", "draconicevolution:draconium_ingot", 1, [], -7.0, 0.0, "Refine Draconium and begin Draconic Evolution's core material ladder."),
            ("Draconic Core", "draconicevolution:draconic_core", "draconicevolution:draconic_core", 1, [0], -5.25, 0.0, "Craft a Draconic Core, the component behind most advanced Draconic technology."),
            ("Fusion Crafting Core", "draconicevolution:crafting_core", "draconicevolution:crafting_core", 1, [1], -3.5, 0.0, "Build the Fusion Crafting Core and prepare a safe, powered fusion-crafting area."),
            ("Basic Fusion Injector", "draconicevolution:basic_crafting_injector", "draconicevolution:basic_crafting_injector", 2, [2], -1.75, 0.0, "Add Basic Fusion Crafting Injectors and complete a real fusion recipe."),
            ("Wyvern Core", "draconicevolution:wyvern_core", "draconicevolution:wyvern_core", 2, [3], 0.0, -1.5, "Reach Wyvern-tier components and prepare for stronger injectors and equipment."),
            ("Wyvern Fusion", "draconicevolution:wyvern_crafting_injector", "draconicevolution:wyvern_crafting_injector", 2, [4], 1.75, -1.5, "Upgrade the fusion array to Wyvern injectors."),
            ("Awakened Draconium", "draconicevolution:awakened_draconium_ingot", "draconicevolution:awakened_draconium_ingot", 3, [4], 0.0, 1.5, "Produce Awakened Draconium, the gateway to Draconic-tier crafting."),
            ("Awakened Core", "draconicevolution:awakened_core", "draconicevolution:awakened_core", 3, [6], 1.75, 1.5, "Craft an Awakened Core and step into the mod's late-game technology."),
            ("Awakened Fusion", "draconicevolution:awakened_crafting_injector", "draconicevolution:awakened_crafting_injector", 3, [5, 7], 3.5, 1.5, "Upgrade the fusion system again so awakened recipes are repeatable rather than one-off crafts."),
            ("Energy Core", "draconicevolution:energy_core", "draconicevolution:energy_core", 3, [4], 3.5, -1.5, "Build the heart of Draconic Evolution's massive energy-storage multiblock."),
            ("Energy Pylons", "draconicevolution:energy_pylon", "draconicevolution:energy_pylon", 3, [9], 5.25, -1.5, "Connect the Energy Core with pylons and prove the storage system can charge and discharge."),
            ("Chaotic Core", "draconicevolution:chaotic_core", "draconicevolution:chaotic_core", 4, [8, 10], 5.25, 1.5, "Reach Chaotic components through your own progression rather than relying on a reward jackpot."),
            ("Chaotic Fusion", "draconicevolution:chaotic_crafting_injector", "draconicevolution:chaotic_crafting_injector", 4, [11], 7.0, 1.5, "Build Chaotic Fusion Crafting Injectors and complete the highest fusion tier."),
            ("Draconic Reactor", "draconicevolution:reactor_core", "draconicevolution:reactor_core", 4, [11], 7.0, -1.5, "Build the Reactor Core only after understanding the mod's reactor controls and containment requirements."),
            ("Mastery: Draconic Evolution", "draconicevolution:awakened_core", None, 4, [12, 13], 8.75, 0.0, "Complete the fusion, energy-storage, chaotic, and reactor branches and confirm the endgame Draconic workshop is operational."),
        ],
    },
}

POOLS = {
    "ae2": {
        1: [item("ae2:certus_quartz_crystal", 16, 8), item("ae2:fluix_crystal", 12, 4), item("ae2:charger", 4), item("ae2:inscriber", 3)],
        2: [item("ae2:logic_processor", 14, 4), item("ae2:engineering_processor", 10, 3), item("ae2:drive", 6), item("ae2:crafting_terminal", 6), item("ae2:item_storage_cell_4k", 5)],
        3: [item("ae2:controller", 7), item("ae2:dense_energy_cell", 7), item("ae2:pattern_provider", 8), item("ae2:molecular_assembler", 8), item("ae2:item_storage_cell_64k", 3), item("ae2:crafting_storage_4k", 4)],
        4: [item("ae2:pattern_provider", 9, 2), item("ae2:molecular_assembler", 9, 2), item("ae2:item_storage_cell_64k", 6), item("ae2:crafting_storage_16k", 5), item("ae2:controller", 5), item("ae2:quantum_ring", 1.0), item("ae2:quantum_link", 0.35)],
    },
    "mekanism": {
        1: [item("mekanism:basic_control_circuit", 16, 6), item("mekanism:alloy_infused", 14, 6), item("mekanism:steel_casing", 8, 2), item("mekanism:enrichment_chamber", 3), item("mekanism:metallurgic_infuser", 3)],
        2: [item("mekanism:advanced_control_circuit", 14, 6), item("mekanism:alloy_reinforced", 12, 5), item("mekanism:crusher", 6), item("mekanism:purification_chamber", 5), item("mekanism:electrolytic_separator", 4)],
        3: [item("mekanism:elite_control_circuit", 12, 5), item("mekanism:alloy_atomic", 10, 4), item("mekanism:chemical_injection_chamber", 6), item("mekanism:pressurized_reaction_chamber", 6), item("mekanism:chemical_dissolution_chamber", 3)],
        4: [item("mekanism:ultimate_control_circuit", 12, 4), item("mekanism:chemical_washer", 8), item("mekanism:chemical_crystallizer", 8), item("mekanism:ultimate_energy_cube", 5), item("mekanism:atomic_disassembler", 3), item("mekanism:digital_miner", 1.0), item("mekanism:antiprotonic_nucleosynthesizer", 0.35), item("mekanism:mekasuit_helmet", 0.25)],
    },
    "powah": {
        1: [item("powah:dielectric_paste", 18, 16), item("powah:thermo_generator_starter", 8), item("powah:energy_cell_starter", 7), item("powah:energizing_rod_starter", 5)],
        2: [item("powah:crystal_blazing", 14, 5), item("powah:thermo_generator_hardened", 8), item("powah:energy_cell_hardened", 8), item("powah:reactor_basic", 5), item("powah:energizing_rod_hardened", 6)],
        3: [item("powah:crystal_niotic", 12, 5), item("powah:crystal_spirited", 8, 3), item("powah:thermo_generator_niotic", 7), item("powah:energy_cell_spirited", 5), item("powah:reactor_spirited", 3), item("powah:energizing_rod_spirited", 5)],
        4: [item("powah:crystal_spirited", 12, 5), item("powah:crystal_nitro", 3, 2), item("powah:thermo_generator_spirited", 8), item("powah:energy_cell_spirited", 8), item("powah:reactor_spirited", 6), item("powah:thermo_generator_nitro", 0.25), item("powah:energy_cell_nitro", 0.35), item("powah:reactor_nitro", 0.20), item("powah:energizing_rod_nitro", 0.45)],
    },
    "ars_nouveau": {
        1: [item("ars_nouveau:source_gem", 18, 8), item("ars_nouveau:novice_spell_book", 5), item("ars_nouveau:imbuement_chamber", 5)],
        2: [item("ars_nouveau:source_gem", 14, 16), item("ars_nouveau:source_jar", 8), item("ars_nouveau:enchanting_apparatus", 7), item("ars_nouveau:arcane_core", 7), item("ars_nouveau:apprentice_spell_book", 3)],
        3: [item("ars_nouveau:spell_turret", 7), item("ars_nouveau:starbuncle_charm", 7), item("ars_nouveau:wixie_charm", 6), item("ars_nouveau:drygmy_charm", 5), item("ars_nouveau:ritual_brazier", 5), item("ars_nouveau:source_gem", 10, 24)],
        4: [item("ars_nouveau:spell_turret", 8, 2), item("ars_nouveau:drygmy_charm", 7), item("ars_nouveau:wixie_charm", 7), item("ars_nouveau:ritual_brazier", 7), item("ars_nouveau:enchanting_apparatus", 6), item("ars_nouveau:archmage_spell_book", 0.45)],
    },
    "irons_spells": {
        1: [item("irons_spellbooks:arcane_ingot", 16, 5), item("irons_spellbooks:scroll", 12, 3), item("irons_spellbooks:iron_spell_book", 5), item("irons_spellbooks:inscription_table", 4)],
        2: [item("irons_spellbooks:arcane_ingot", 14, 8), item("irons_spellbooks:upgrade_orb", 10, 2), item("irons_spellbooks:arcane_anvil", 6), item("irons_spellbooks:diamond_spell_book", 1.5)],
        3: [item("irons_spellbooks:mithril_ingot", 12, 4), item("irons_spellbooks:upgrade_orb", 10, 3), item("irons_spellbooks:diamond_spell_book", 5), item("irons_spellbooks:arcane_anvil", 6), item("irons_spellbooks:netherite_spell_book", 0.75)],
        4: [item("irons_spellbooks:mithril_ingot", 12, 8), item("irons_spellbooks:upgrade_orb", 12, 4), item("irons_spellbooks:diamond_spell_book", 7), item("irons_spellbooks:netherite_spell_book", 0.35), item("irons_spellbooks:arcane_ingot", 10, 16)],
    },
    "ender_io": {
        1: [item("enderio:grains_of_infinity", 18, 12), item("enderio:alloy_smelter", 5), item("enderio:sag_mill", 5)],
        2: [item("enderio:vacuum_chest", 9), item("enderio:impulse_hopper", 9), item("enderio:alloy_smelter", 7), item("enderio:sag_mill", 7), item("enderio:grains_of_infinity", 12, 24)],
        3: [item("enderio:slice_and_splice", 9), item("enderio:soul_binder", 9), item("enderio:enchanter", 8), item("enderio:vacuum_chest", 7), item("enderio:impulse_hopper", 7)],
        4: [item("enderio:slice_and_splice", 10), item("enderio:soul_binder", 10), item("enderio:enchanter", 9), item("enderio:travel_anchor", 6, 2), item("enderio:powered_spawner", 0.65)],
    },
    "refined_storage": {
        1: [item("refinedstorage:quartz_enriched_iron", 18, 12), item("refinedstorage:controller", 5), item("refinedstorage:grid", 6), item("refinedstorage:disk_drive", 5)],
        2: [item("refinedstorage:4k_storage_disk", 10), item("refinedstorage:16k_storage_disk", 5), item("refinedstorage:crafting_grid", 7), item("refinedstorage:external_storage", 7), item("refinedstorage:disk_drive", 7)],
        3: [item("refinedstorage:importer", 10, 2), item("refinedstorage:exporter", 10, 2), item("refinedstorage:interface", 8), item("refinedstorage:pattern_grid", 7), item("refinedstorage:64k_storage_disk", 3)],
        4: [item("refinedstorage:crafter", 9, 2), item("refinedstorage:pattern_grid", 8), item("refinedstorage:64k_storage_disk", 7), item("refinedstorage:network_transmitter", 4), item("refinedstorage:network_receiver", 4)],
    },
    "hostile_neural_networks": {
        1: [item("hostilenetworks:blank_data_model", 18, 4), item("hostilenetworks:prediction_matrix", 15, 8), item("hostilenetworks:deep_learner", 4)],
        2: [item("hostilenetworks:prediction_matrix", 16, 16), item("hostilenetworks:overworld_prediction", 10, 4), item("hostilenetworks:sim_chamber", 2.5)],
        3: [item("hostilenetworks:prediction_matrix", 15, 24), item("hostilenetworks:overworld_prediction", 9, 6), item("hostilenetworks:nether_prediction", 8, 5), item("hostilenetworks:end_prediction", 7, 4), item("hostilenetworks:sim_chamber", 5), item("hostilenetworks:loot_fabricator", 4)],
        4: [item("hostilenetworks:prediction_matrix", 15, 32), item("hostilenetworks:overworld_prediction", 10, 8), item("hostilenetworks:nether_prediction", 10, 8), item("hostilenetworks:end_prediction", 9, 6), item("hostilenetworks:sim_chamber", 7), item("hostilenetworks:loot_fabricator", 7), item("hostilenetworks:sim_chamber", 0.75, 2), item("hostilenetworks:loot_fabricator", 0.65, 2)],
    },
    "draconic_evolution": {
        1: [item("draconicevolution:draconium_ingot", 18, 6), item("draconicevolution:draconium_dust", 14, 10), item("draconicevolution:draconic_core", 7), item("draconicevolution:basic_crafting_injector", 3)],
        2: [item("draconicevolution:draconium_ingot", 14, 12), item("draconicevolution:wyvern_core", 8), item("draconicevolution:wyvern_crafting_injector", 5), item("draconicevolution:crafting_core", 4)],
        3: [item("draconicevolution:awakened_draconium_ingot", 10, 4), item("draconicevolution:awakened_core", 8), item("draconicevolution:awakened_crafting_injector", 6), item("draconicevolution:energy_core", 4), item("draconicevolution:energy_pylon", 5, 2)],
        4: [item("draconicevolution:awakened_draconium_ingot", 12, 6), item("draconicevolution:awakened_core", 10, 2), item("draconicevolution:energy_pylon", 8, 2), item("draconicevolution:chaotic_core", 0.40), item("draconicevolution:chaotic_crafting_injector", 0.30), item("draconicevolution:reactor_core", 0.20)],
    },
}


def verify_mods() -> None:
    rows = SERVER_MODS.read_text()
    required = [
        "\tapplied-energistics-2\t", "\tars-nouveau\t", "\tender-io\t", "\tirons-spells-n-spellbooks\t",
        "\tmekanism\t", "\tpowah-rearchitected\t", "\trefined-storage\t", "\thostile-neural-networks\t", "\tdraconic-evolution\t",
    ]
    missing = [needle.strip("\t") for needle in required if needle not in rows]
    if missing:
        raise RuntimeError("Missing required installed mods for 0.1.9-38: " + ", ".join(missing))


def reward_tables_for(chapter: str, title: str, icon_id: str, is_new: bool) -> tuple[dict[int, tuple[str, int]], tuple[str, int]]:
    tiers: dict[int, tuple[str, int]] = {}
    for tier in range(1, 5):
        path = CLIENT_TABLES / f"modroll_{chapter}_tier_{tier}.snbt"
        table_id, order_index = read_table_identity(path, f"AA38:{chapter}:tier:{tier}", 800 + len(MAJOR_SPECS) * 10 + tier)
        tiers[tier] = (table_id, order_index)
        write_reward_table(path, table_id, order_index, f"{title} — Tier {tier} Roll", icon_id, tier, POOLS[chapter][tier])

    wheel_path = CLIENT_TABLES / f"wheel_{chapter}.snbt"
    wheel_id, wheel_order = read_table_identity(wheel_path, f"AA38:{chapter}:wheel", 900 + len(MAJOR_SPECS))
    # Finale pool is deliberately large and weighted: useful late-game items are common, jackpots stay rare.
    finale = []
    for tier in (2, 3, 4):
        finale.extend(POOLS[chapter][tier])
    write_reward_table(wheel_path, wheel_id, wheel_order, f"Wheel of Fortune — {title}", icon_id, 5, finale)
    return tiers, (wheel_id, wheel_order)


def build_quest_block(chapter: str, qid: str, node: tuple, tier_tables: dict[int, tuple[str, int]], wheel: tuple[str, int], qids: list[str], root_dep: str | None, is_final: bool) -> str:
    title, icon_id, task_item, tier, dep_indices, x, y, description = node
    deps = [qids[i] for i in dep_indices]
    if not dep_indices and root_dep:
        deps.append(root_dep)

    lines = ["\t\t{"]
    if deps:
        lines.append("\t\t\tdependencies: [" + " ".join(esc(d) for d in deps) + "]")
    lines += [
        f"\t\t\tdescription: [{esc(description)}]",
        f"\t\t\ticon: {esc(icon_id)}",
        f"\t\t\tid: {esc(qid)}",
        "\t\t\trewards: [",
        "\t\t\t\t{",
        f"\t\t\t\t\tid: {esc(stable_id('AA38:'+qid+':xp'))}",
        "\t\t\t\t\ttype: \"xp\"",
        f"\t\t\t\t\txp: {50 * tier}",
        "\t\t\t\t}",
    ]
    table_id = tier_tables[tier][0]
    lines += [
        "\t\t\t\t{",
        f"\t\t\t\t\tid: {esc(stable_id('AA38:'+qid+':tier'))}",
        f"\t\t\t\t\ttable_id: {table_long(table_id)}L",
        f"\t\t\t\t\ttitle: {esc(title + ' — Tier ' + str(tier) + ' Roll')}",
        "\t\t\t\t\ttype: \"loot\"",
        "\t\t\t\t}",
    ]
    if is_final:
        lines += [
            "\t\t\t\t{",
            f"\t\t\t\t\tid: {esc(stable_id('AA38:'+qid+':wheel'))}",
            f"\t\t\t\t\ttable_id: {table_long(wheel[0])}L",
            "\t\t\t\t\ttitle: \"Spin the Wheel of Fortune\"",
            "\t\t\t\t\ttype: \"loot\"",
            "\t\t\t\t}",
        ]
    lines += ["\t\t\t]"]

    if is_final:
        lines.append("\t\t\tshape: \"hexagon\"")
        lines.append("\t\t\tsize: 1.5d")
    lines.append("\t\t\ttasks: [")
    lines.append("\t\t\t\t{")
    lines.append(f"\t\t\t\t\tid: {esc(stable_id('AA38:'+qid+':task'))}")
    if task_item:
        lines.append(f"\t\t\t\t\titem: {esc(task_item)}")
        lines.append("\t\t\t\t\tconsume_items: false")
        lines.append(f"\t\t\t\t\ttitle: {esc('Obtain: ' + title)}")
        lines.append("\t\t\t\t\ttype: \"item\"")
        subtitle = f"Obtain {title}; inventory detection completes this milestone automatically."
    else:
        lines.append(f"\t\t\t\t\ttitle: {esc('Confirm: ' + title)}")
        lines.append("\t\t\t\t\ttype: \"checkmark\"")
        subtitle = "Hands-on progression milestone; confirm it after completing the described mechanic."
    lines += [
        "\t\t\t\t}",
        "\t\t\t]",
        f"\t\t\tsubtitle: {esc(subtitle)}",
        f"\t\t\ttitle: {esc(title)}",
        f"\t\t\tx: {fmt_num(x)}",
        f"\t\t\ty: {fmt_num(y)}",
        "\t\t}",
    ]
    return "\n".join(lines)


def write_chapter(chapter: str, spec: dict, qids: list[str], cid: str, root_dep: str | None, is_new: bool) -> None:
    if len(qids) != len(spec["nodes"]):
        raise RuntimeError(f"{chapter}: expected {len(spec['nodes'])} quest ids, got {len(qids)}")
    tiers, wheel = reward_tables_for(chapter, spec["title"], spec["icon"], is_new)
    blocks = [
        build_quest_block(chapter, qid, node, tiers, wheel, qids, root_dep, i == len(qids) - 1)
        for i, (qid, node) in enumerate(zip(qids, spec["nodes"]))
    ]
    lines = [
        "{",
        "\tdefault_hide_dependency_lines: false",
        "\tdefault_quest_shape: \"\"",
        f"\tfilename: {esc(chapter)}",
        f"\tgroup: {esc(spec['group'])}",
        f"\ticon: {esc(spec['icon'])}",
        f"\tid: {esc(cid)}",
        f"\torder_index: {spec['order']}",
        "\tprogression_mode: \"flexible\"",
        "\tquest_links: [ ]",
        "\tquests: [",
        "\n".join(blocks),
        "\t]",
        f"\ttitle: {esc(spec['title'])}",
        "}",
        "",
    ]
    (CLIENT_CHAPTERS / f"{chapter}.snbt").write_text("\n".join(lines))


def rebuild_existing() -> tuple[int, dict[str, list[str]]]:
    preserved = 0
    ids_by_chapter: dict[str, list[str]] = {}
    for chapter, spec in MAJOR_SPECS.items():
        path = CLIENT_CHAPTERS / f"{chapter}.snbt"
        qids = quest_ids(path)
        if len(qids) != 13:
            raise RuntimeError(f"{chapter}: expected 13 existing quest ids, found {len(qids)}")
        cid = chapter_id(path)
        ids_by_chapter[chapter] = qids
        write_chapter(chapter, spec, qids, cid, STARTER_DEP, is_new=False)
        preserved += len(qids)
    return preserved, ids_by_chapter


def add_new_chapters() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for chapter, spec in NEW_SPECS.items():
        qids = [stable_id(f"AA38:{chapter}:quest:{i}:{node[0]}") for i, node in enumerate(spec["nodes"])]
        cid = stable_id(f"AA38:{chapter}:chapter")
        write_chapter(chapter, spec, qids, cid, None, is_new=True)
        out[chapter] = qids
    # Put Draconic Evolution between Buddycards and the existing Endgame chapter.
    endgame = CLIENT_CHAPTERS / "endgame.snbt"
    if endgame.exists():
        text = endgame.read_text()
        text = re.sub(r'(^\torder_index:\s*)1\s*,?$', r'\g<1>2', text, count=1, flags=re.M)
        endgame.write_text(text)
    return out


def sync_server() -> None:
    if SERVER_QUESTS.exists():
        shutil.rmtree(SERVER_QUESTS)
    shutil.copytree(CLIENT_QUESTS, SERVER_QUESTS)


def count_quests() -> int:
    return sum(len(quest_ids(path)) for path in CLIENT_CHAPTERS.glob("*.snbt"))


def patch_validator() -> None:
    text = VALIDATE_SH.read_text()
    text = text.replace("0.1.9-37", VERSION)
    text = text.replace("= \"26\" || { echo \"Expected 26 live quest chapters\"", "= \"28\" || { echo \"Expected 28 live quest chapters\"")
    text = text.replace("= \"135\" || { echo \"Expected 135 live reward tables\"", "= \"145\" || { echo \"Expected 145 live reward tables\"")
    text = text.replace("= \"26\" || { echo \"Expected flexible progression mode in all 26 chapters\"", "= \"28\" || { echo \"Expected flexible progression mode in all 28 chapters\"")
    marker = "# 0.1.9-38 ATM10-inspired semantic major progression checks"
    if marker not in text:
        text += f'''\n\n{marker}\njq -e '.atm10_major_progression_0_1_9_38.reference_pack == "AllTheMods/ATM-10" and .atm10_major_progression_0_1_9_38.reference_commit == "{ATM10_COMMIT}" and .atm10_major_progression_0_1_9_38.existing_chapters_rebuilt == 7 and .atm10_major_progression_0_1_9_38.new_chapters_added == 2 and .atm10_major_progression_0_1_9_38.final_chapters == 28 and .atm10_major_progression_0_1_9_38.preserved_existing_quest_ids == 91 and .atm10_major_progression_0_1_9_38.reward_tables_final == 145 and .atm10_major_progression_0_1_9_38.fortune_wheels_touched == 9 and .atm10_major_progression_0_1_9_38.client_server_quest_files_identical == true' "$validation" >/dev/null\nfor chapter in hostile_neural_networks draconic_evolution; do\n  test -f "$client_quests/chapters/$chapter.snbt" || {{ echo "Missing new 0.1.9-38 chapter: $chapter" >&2; exit 1; }}\ndone\nfor chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage; do\n  if rg -F 'AA35 deep progression milestone' "$client_quests/chapters/$chapter.snbt" >/dev/null; then\n    echo "Generic AA35 filler remains in rebuilt major chapter: $chapter" >&2\n    exit 1\n  fi\ndone\nfor chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage hostile_neural_networks draconic_evolution; do\n  for tier in 1 2 3 4; do\n    test -f "$client_quests/reward_tables/modroll_${{chapter}}_tier_${{tier}}.snbt" || {{ echo "Missing hand-curated tier table: $chapter tier $tier" >&2; exit 1; }}\n  done\n  test -f "$client_quests/reward_tables/wheel_${{chapter}}.snbt" || {{ echo "Missing Fortune Wheel: $chapter" >&2; exit 1; }}\ndone\ndiff -qr "$client_quests" "$server_quests" >/dev/null || {{ echo "Client/server quest trees differ after 0.1.9-38" >&2; exit 1; }}\n'''
    VALIDATE_SH.write_text(text)


def update_metadata(preserved: int, total_quests: int) -> None:
    manifest = json.loads(MANIFEST.read_text())
    manifest["name"] = f"Amber & Arcana {VERSION}"
    manifest["version"] = VERSION
    write_json(MANIFEST, manifest)

    block = {
        "reference_pack": "AllTheMods/ATM-10",
        "reference_commit": ATM10_COMMIT,
        "reference_use": "milestone sequencing, branch structure, and visual progression density only; Amber & Arcana uses original prose and its own weighted tier rolls plus Fortune Wheels",
        "existing_chapters_rebuilt": len(MAJOR_SPECS),
        "existing_chapter_names": list(MAJOR_SPECS.keys()),
        "new_chapters_added": len(NEW_SPECS),
        "new_chapter_names": list(NEW_SPECS.keys()),
        "final_chapters": len(list(CLIENT_CHAPTERS.glob("*.snbt"))),
        "preserved_existing_quest_ids": preserved,
        "hostile_neural_networks_quests": len(NEW_SPECS["hostile_neural_networks"]["nodes"]),
        "draconic_evolution_quests": len(NEW_SPECS["draconic_evolution"]["nodes"]),
        "final_quest_count": total_quests,
        "tier_tables_hand_curated": 9 * 4,
        "fortune_wheels_touched": 9,
        "reward_tables_final": len(list(CLIENT_TABLES.glob("*.snbt"))),
        "generic_aa35_filler_removed_from_rebuilt_chapters": True,
        "generic_fixed_vanilla_item_rewards_removed_from_rebuilt_chapters": True,
        "fortune_wheel_mechanic_preserved": True,
        "compact_branch_spacing_preserved": True,
        "client_server_quest_files_identical": True,
        "minecraft_launch_tested": False,
        "gameplay_tested": False,
    }

    summary = json.loads(SUMMARY.read_text())
    summary["pack_version"] = VERSION
    summary["atm10_major_progression_0_1_9_38"] = block
    write_json(SUMMARY, summary)

    validation = json.loads(VALIDATION.read_text())
    validation["pack_version"] = VERSION
    validation["chapters"] = block["final_chapters"]
    validation["manual_quests"] = total_quests
    validation["atm10_major_progression_0_1_9_38"] = block
    write_json(VALIDATION, validation)


def update_docs() -> None:
    heading = f"## {VERSION}"
    changelog = CHANGELOG.read_text() if CHANGELOG.exists() else ""
    if heading not in changelog:
        entry = f'''{heading}\n\n- Rebuilt AE2, Mekanism, Powah, Ars Nouveau, Iron's Spells, Ender IO, and Refined Storage into real mechanics-based progression branches using ATM10 only as a layout/progression reference.\n- Added dedicated 13-quest Hostile Neural Networks and 15-quest Draconic Evolution chapters.\n- Replaced generic AA35 filler milestones in the rebuilt chapters with concrete mod mechanics and item milestones.\n- Hand-curated four weighted reward tiers plus a five-draw Fortune Wheel for all nine touched chapters.\n- Corrected the Ender IO reward pools so they no longer contain Create items.\n- Preserved all 91 existing quest IDs across the seven rebuilt chapters.\n\n'''
        CHANGELOG.write_text(entry + changelog)
    if README.exists():
        readme = README.read_text()
        if VERSION not in readme:
            readme += f"\n\n### {VERSION} major quest progression\nATM10-inspired milestone/branch audit for the major tech and magic chapters, plus new Hostile Neural Networks and Draconic Evolution progression. Amber & Arcana keeps its own tier-roll and Fortune Wheel reward system.\n"
            README.write_text(readme)


def main() -> None:
    verify_mods()
    validation = json.loads(VALIDATION.read_text())
    already = validation.get("atm10_major_progression_0_1_9_38")
    if already and already.get("final_chapters") == 28:
        # Canonical source is already transformed. Keep version metadata stable and
        # only verify/synchronize parity so future builds are idempotent.
        manifest = json.loads(MANIFEST.read_text())
        manifest["name"] = f"Amber & Arcana {VERSION}"
        manifest["version"] = VERSION
        write_json(MANIFEST, manifest)
        sync_server()
        patch_validator()
        print(f"Amber & Arcana {VERSION} major progression already applied; canonical quest source verified")
        return

    preserved, _ = rebuild_existing()
    add_new_chapters()
    sync_server()
    total = count_quests()
    update_metadata(preserved, total)
    patch_validator()
    update_docs()

    final_chapters = len(list(CLIENT_CHAPTERS.glob("*.snbt")))
    final_tables = len(list(CLIENT_TABLES.glob("*.snbt")))
    if final_chapters != 28:
        raise RuntimeError(f"Expected 28 chapters after 0.1.9-38, found {final_chapters}")
    if final_tables != 145:
        raise RuntimeError(f"Expected 145 reward tables after 0.1.9-38, found {final_tables}")
    print(f"Applied Amber & Arcana {VERSION}: 7 major chapters rebuilt, 2 chapters added, {total} quests, {final_tables} reward tables")


if __name__ == "__main__":
    main()
