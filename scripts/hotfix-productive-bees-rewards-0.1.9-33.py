#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-33"
CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"
TABLES = CLIENT_QUESTS / "reward_tables"
MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
VALIDATE_SH = ROOT / "scripts/validate.sh"

# Verified against Productive Bees 1.20.1-12.6.0 source snapshot
# 2190d6b4c0f4a35acc26415759c3be731d1eac22. These are real registered
# Productive Bees item/block-item IDs for the exact pack version.
VERIFIED_ITEMS = {
    "productivebees:honey_treat",
    "productivebees:bee_cage",
    "productivebees:sturdy_bee_cage",
    "productivebees:nest_locator",
    "productivebees:upgrade_base",
    "productivebees:upgrade_productivity",
    "productivebees:upgrade_productivity_2",
    "productivebees:upgrade_productivity_3",
    "productivebees:upgrade_productivity_4",
    "productivebees:upgrade_time",
    "productivebees:upgrade_breeding",
    "productivebees:upgrade_not_babee",
    "productivebees:upgrade_comb_block",
    "productivebees:upgrade_anti_teleport",
    "productivebees:upgrade_range",
    "productivebees:upgrade_filter",
    "productivebees:upgrade_bee_sampler",
    "productivebees:upgrade_simulator",
    "productivebees:feeder",
    "productivebees:centrifuge",
    "productivebees:powered_centrifuge",
    "productivebees:heated_centrifuge",
    "productivebees:honey_generator",
    "productivebees:catcher",
    "productivebees:incubator",
    "productivebees:gene_indexer",
    "productivebees:bottler",
    "productivebees:advanced_oak_beehive",
    "productivebees:expansion_box_oak",
    "productivebees:gene_bottle",
    "productivebees:wax",
    "productivebees:draconic_dust",
    "productivebees:draconic_chunk",
    "productivebees:sugarbag_honeycomb",
    "productivebees:bee_nest_diamond_helmet",
    "productivebees:inactive_dragon_egg",
}

# (count, item, weight). Later tiers deliberately have broader pools and more
# draws. Useful upgrades are common enough to feel rewarding, while the truly
# progression-skipping rewards stay in a small jackpot band.
TIER_POOLS = {
    1: [
        (8, "productivebees:honey_treat", 20.0),
        (8, "productivebees:bee_cage", 18.0),
        (2, "productivebees:sturdy_bee_cage", 8.0),
        (1, "productivebees:nest_locator", 8.0),
        (2, "productivebees:upgrade_base", 14.0),
        (1, "productivebees:feeder", 10.0),
        (1, "productivebees:centrifuge", 9.0),
        (1, "productivebees:advanced_oak_beehive", 7.0),
        (1, "productivebees:expansion_box_oak", 7.0),
        (4, "productivebees:gene_bottle", 6.0),
        (16, "productivebees:wax", 10.0),
        (1, "productivebees:bottler", 5.0),
    ],
    2: [
        (4, "productivebees:sturdy_bee_cage", 12.0),
        (4, "productivebees:upgrade_base", 12.0),
        (2, "productivebees:upgrade_time", 11.0),
        (1, "productivebees:upgrade_breeding", 9.0),
        (1, "productivebees:upgrade_range", 9.0),
        (1, "productivebees:upgrade_filter", 9.0),
        (1, "productivebees:upgrade_not_babee", 7.0),
        (1, "productivebees:upgrade_productivity", 8.0),
        (1, "productivebees:powered_centrifuge", 7.0),
        (1, "productivebees:incubator", 7.0),
        (1, "productivebees:catcher", 6.0),
        (1, "productivebees:gene_indexer", 6.0),
        (1, "productivebees:honey_generator", 6.0),
        (1, "productivebees:bottler", 8.0),
        (1, "productivebees:upgrade_comb_block", 4.0),
        (1, "productivebees:upgrade_bee_sampler", 3.5),
        (1, "productivebees:upgrade_simulator", 2.5),
    ],
    3: [
        (2, "productivebees:upgrade_productivity", 12.0),
        (1, "productivebees:upgrade_productivity_2", 8.0),
        (2, "productivebees:upgrade_time", 9.0),
        (1, "productivebees:upgrade_breeding", 8.0),
        (1, "productivebees:upgrade_range", 8.0),
        (1, "productivebees:upgrade_filter", 8.0),
        (1, "productivebees:upgrade_simulator", 7.0),
        (1, "productivebees:upgrade_bee_sampler", 7.0),
        (1, "productivebees:upgrade_anti_teleport", 6.0),
        (1, "productivebees:upgrade_comb_block", 6.0),
        (1, "productivebees:powered_centrifuge", 8.0),
        (1, "productivebees:heated_centrifuge", 5.0),
        (1, "productivebees:gene_indexer", 7.0),
        (1, "productivebees:honey_generator", 7.0),
        (1, "productivebees:incubator", 7.0),
        (8, "productivebees:gene_bottle", 6.0),
        (2, "productivebees:draconic_dust", 3.0),
        (1, "productivebees:upgrade_productivity_3", 2.0),
        # Tiny preview jackpot: possible before T4, but intentionally extremely rare.
        (1, "productivebees:upgrade_productivity_4", 0.10),
    ],
    4: [
        (2, "productivebees:upgrade_productivity", 10.0),
        (1, "productivebees:upgrade_productivity_2", 9.0),
        (1, "productivebees:upgrade_productivity_3", 4.0),
        # Omega Productivity jackpot. Four T4 draws make it exciting without making it common.
        (1, "productivebees:upgrade_productivity_4", 0.30),
        (1, "productivebees:upgrade_simulator", 7.0),
        (1, "productivebees:upgrade_bee_sampler", 7.0),
        (1, "productivebees:upgrade_anti_teleport", 6.0),
        (1, "productivebees:upgrade_comb_block", 6.0),
        (2, "productivebees:upgrade_breeding", 6.0),
        (2, "productivebees:upgrade_range", 6.0),
        (2, "productivebees:upgrade_filter", 6.0),
        (1, "productivebees:powered_centrifuge", 8.0),
        (1, "productivebees:heated_centrifuge", 7.0),
        (1, "productivebees:gene_indexer", 8.0),
        (1, "productivebees:honey_generator", 7.0),
        (1, "productivebees:incubator", 7.0),
        (1, "productivebees:catcher", 6.0),
        (1, "productivebees:bottler", 6.0),
        (4, "productivebees:draconic_dust", 5.0),
        (2, "productivebees:draconic_chunk", 2.5),
        (4, "productivebees:sugarbag_honeycomb", 3.0),
        (1, "productivebees:bee_nest_diamond_helmet", 0.75),
        (1, "productivebees:inactive_dragon_egg", 0.50),
        (8, "productivebees:sturdy_bee_cage", 7.0),
        (16, "productivebees:gene_bottle", 6.0),
    ],
}

LOOT_SIZE = {1: 1, 2: 2, 3: 3, 4: 4}

FINALE_POOL = [
    (2, "productivebees:upgrade_productivity", 10.0),
    (1, "productivebees:upgrade_productivity_2", 8.0),
    (1, "productivebees:upgrade_productivity_3", 3.0),
    (1, "productivebees:upgrade_productivity_4", 0.20),
    (1, "productivebees:upgrade_simulator", 7.0),
    (1, "productivebees:upgrade_bee_sampler", 7.0),
    (1, "productivebees:upgrade_anti_teleport", 5.0),
    (1, "productivebees:upgrade_comb_block", 5.0),
    (1, "productivebees:heated_centrifuge", 7.0),
    (1, "productivebees:powered_centrifuge", 8.0),
    (1, "productivebees:gene_indexer", 8.0),
    (1, "productivebees:honey_generator", 7.0),
    (1, "productivebees:incubator", 7.0),
    (2, "productivebees:draconic_chunk", 3.0),
    (8, "productivebees:draconic_dust", 5.0),
    (8, "productivebees:sugarbag_honeycomb", 4.0),
    (1, "productivebees:bee_nest_diamond_helmet", 0.50),
    (1, "productivebees:inactive_dragon_egg", 0.35),
    (8, "productivebees:sturdy_bee_cage", 6.0),
    (16, "productivebees:gene_bottle", 6.0),
]


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def read_table_identity(path: Path) -> tuple[str, int]:
    text = path.read_text()
    mid = re.search(r'(?m)^\s*id:\s*"([0-9A-F]{16})"', text)
    mord = re.search(r'(?m)^\s*order_index:\s*(-?\d+)', text)
    if not mid or not mord:
        raise RuntimeError(f"Could not preserve reward-table identity: {path.name}")
    return mid.group(1), int(mord.group(1))


def render_table(table_id: str, order: int, title: str, icon: str, loot_size: int, entries) -> str:
    lines = [
        "{",
        f'\ticon: "{icon}"',
        f'\tid: "{table_id}"',
        f"\tloot_size: {loot_size}",
        f"\torder_index: {order}",
        "\trewards: [",
    ]
    for count, item, weight in entries:
        if item not in VERIFIED_ITEMS:
            raise RuntimeError(f"Unverified Productive Bees reward ID: {item}")
        count_part = f"count: {count}, " if count != 1 else ""
        lines.append(f'\t\t{{ {count_part}item: "{item}", weight: {weight:.2f}f }}')
    lines += [
        "\t]",
        f'\ttitle: "{title}"',
        "\tuse_title: true",
        "}",
        "",
    ]
    return "\n".join(lines)


def write_tables() -> dict:
    tier_counts = {}
    unique_items = set()
    for tier, entries in TIER_POOLS.items():
        path = TABLES / f"modroll_productive_bees_tier_{tier}.snbt"
        if not path.exists():
            raise RuntimeError(f"Missing generated Productive Bees tier table: {path.name}")
        table_id, order = read_table_identity(path)
        path.write_text(render_table(
            table_id,
            order,
            f"Productive Bees — Tier {tier} Roll",
            entries[0][1],
            LOOT_SIZE[tier],
            entries,
        ))
        tier_counts[str(tier)] = len(entries)
        unique_items.update(item for _count, item, _weight in entries)

    wheel = TABLES / "wheel_productive_bees.snbt"
    if not wheel.exists():
        raise RuntimeError("Missing Productive Bees finale wheel table")
    table_id, order = read_table_identity(wheel)
    wheel.write_text(render_table(
        table_id,
        order,
        "Wheel of Fortune — Productive Bees",
        "productivebees:upgrade_productivity_3",
        5,
        FINALE_POOL,
    ))
    unique_items.update(item for _count, item, _weight in FINALE_POOL)

    return {
        "tier_tables_rebalanced": 4,
        "tier_entry_counts": tier_counts,
        "tier_loot_sizes": {str(k): v for k, v in LOOT_SIZE.items()},
        "finale_weighted_entries": len(FINALE_POOL),
        "finale_loot_size": 5,
        "unique_productive_bees_rewards": len(unique_items),
        "omega_upgrade_item": "productivebees:upgrade_productivity_4",
        "omega_tier3_preview_weight": 0.10,
        "omega_tier4_weight": 0.30,
        "omega_finale_weight": 0.20,
        "productive_bees_version": "1.20.1-12.6.0",
        "upstream_commit": "2190d6b4c0f4a35acc26415759c3be731d1eac22",
        "generic_vanilla_items_in_new_bee_tables": 0,
        "historical_table_ids_preserved": True,
        "client_server_quest_files_identical": True,
    }


def sync_server() -> None:
    if SERVER_QUESTS.exists():
        shutil.rmtree(SERVER_QUESTS)
    shutil.copytree(CLIENT_QUESTS, SERVER_QUESTS)


def update_validator() -> None:
    text = VALIDATE_SH.read_text()
    text = text.replace('.version == "0.1.9-32"', '.version == "0.1.9-33"')
    text = text.replace('.pack_version == "0.1.9-32"', '.pack_version == "0.1.9-33"')
    text = text.replace('Amber & Arcana 0.1.9-32 static validation passed', 'Amber & Arcana 0.1.9-33 static validation passed')

    marker = "# 0.1.9-33 Productive Bees reward progression checks"
    if marker not in text:
        text += r'''

# 0.1.9-33 Productive Bees reward progression checks
jq -e '.productive_bees_rewards_0_1_9_33.tier_tables_rebalanced == 4 and .productive_bees_rewards_0_1_9_33.tier_entry_counts["1"] >= 10 and .productive_bees_rewards_0_1_9_33.tier_entry_counts["2"] >= 15 and .productive_bees_rewards_0_1_9_33.tier_entry_counts["3"] >= 18 and .productive_bees_rewards_0_1_9_33.tier_entry_counts["4"] >= 20 and .productive_bees_rewards_0_1_9_33.tier_loot_sizes["4"] == 4 and .productive_bees_rewards_0_1_9_33.finale_loot_size == 5 and .productive_bees_rewards_0_1_9_33.unique_productive_bees_rewards >= 30 and .productive_bees_rewards_0_1_9_33.generic_vanilla_items_in_new_bee_tables == 0 and .productive_bees_rewards_0_1_9_33.historical_table_ids_preserved == true and .productive_bees_rewards_0_1_9_33.client_server_quest_files_identical == true' "$validation" >/dev/null
pb_t4="$client_quests/reward_tables/modroll_productive_bees_tier_4.snbt"
pb_wheel="$client_quests/reward_tables/wheel_productive_bees.snbt"
grep -Fq 'loot_size: 4' "$pb_t4" || { echo "Productive Bees Tier 4 should return four draws" >&2; exit 1; }
grep -Fq 'item: "productivebees:upgrade_productivity_4", weight: 0.30f' "$pb_t4" || { echo "Productive Bees Omega Tier 4 jackpot missing" >&2; exit 1; }
grep -Fq 'loot_size: 5' "$pb_wheel" || { echo "Productive Bees finale should return five draws" >&2; exit 1; }
grep -Fq 'item: "productivebees:upgrade_productivity_4", weight: 0.20f' "$pb_wheel" || { echo "Productive Bees finale Omega jackpot missing" >&2; exit 1; }
if rg -n 'minecraft:(diamond|emerald|emerald_block)' "$client_quests/reward_tables/modroll_productive_bees_tier_"*.snbt "$pb_wheel" >/dev/null; then
  echo "Generic diamond/emerald reward leaked into Productive Bees progression tables" >&2
  exit 1
fi
'''
    VALIDATE_SH.write_text(text)


def update_docs(stats: dict) -> None:
    text = README.read_text()
    text = text.replace("Amber-and-Arcana-0.1.9-32-", "Amber-and-Arcana-0.1.9-33-")
    text = text.replace("Download Client 0.1.9-32", "Download Client 0.1.9-33")
    text = text.replace("Download Crafty Server 0.1.9-32", "Download Crafty Server 0.1.9-33")
    text = text.replace("| Pack | 0.1.9-32 |", "| Pack | 0.1.9-33 |")
    marker = "## Quest runtime status — 2026-09-15\n"
    note = (
        "\nRelease 0.1.9-33 makes Productive Bees rewards scale much more strongly with chapter depth. "
        f"Its four tier rolls now contain {sum(stats['tier_entry_counts'].values())} weighted entries across progressively stronger pools, "
        "Tier 3 gives three draws, Tier 4 gives four, and the Master Apiarist Wheel gives five. "
        "Later pools emphasize Productive Bees upgrades and machines instead of generic diamonds/emeralds. "
        "Omega Productivity (`productivebees:upgrade_productivity_4`) is a genuine jackpot at weight 0.30 in Tier 4 and 0.20 in the finale wheel.\n"
    )
    if marker in text and "Release 0.1.9-33 makes Productive Bees rewards" not in text:
        text = text.replace(marker, marker + note, 1)
    README.write_text(text)

    changelog = CHANGELOG.read_text()
    if "## 0.1.9-33" not in changelog:
        entry = (
            "## 0.1.9-33 — Productive Bees reward progression\n\n"
            "- Rebuild all four Productive Bees tier tables around a much larger pool of mod-specific upgrades, machines, bee tools, and advanced materials.\n"
            "- Scale reward volume with progression: Tier 1 gives 1 draw, Tier 2 gives 2, Tier 3 gives 3, Tier 4 gives 4, and Master Apiarist gives 5.\n"
            "- Add the Productive Bees productivity upgrade ladder to later tiers, including an intentionally rare Omega Productivity jackpot.\n"
            "- Keep Omega rare despite multi-draw tables: weight 0.10 as a Tier 3 preview, 0.30 in Tier 4, and 0.20 in the finale wheel.\n"
            "- Remove generic diamond/emerald-style filler from the new bee reward pools and preserve existing reward-table IDs.\n\n"
        )
        if changelog.startswith("# Changelog\n\n"):
            changelog = "# Changelog\n\n" + entry + changelog[len("# Changelog\n\n"):]
        else:
            changelog = entry + changelog
        CHANGELOG.write_text(changelog)


def main() -> None:
    stats = write_tables()

    def manifest_mutate(d):
        d["version"] = VERSION
        d["name"] = f"Amber & Arcana {VERSION}"
    update_json(MANIFEST, manifest_mutate)

    def summary_mutate(d):
        d["pack_version"] = VERSION
        d["productive_bees_rewards_0_1_9_33"] = stats
    update_json(SUMMARY, summary_mutate)

    def validation_mutate(d):
        d["pack_version"] = VERSION
        d["productive_bees_rewards_0_1_9_33"] = stats
    update_json(VALIDATION, validation_mutate)

    sync_server()
    update_validator()
    update_docs(stats)

    # Strong parity and content checks before the build archives are created.
    for tier in range(1, 5):
        c = TABLES / f"modroll_productive_bees_tier_{tier}.snbt"
        s = SERVER_QUESTS / "reward_tables" / c.name
        if c.read_bytes() != s.read_bytes():
            raise RuntimeError(f"Client/server Productive Bees Tier {tier} table differs")
    if (TABLES / "wheel_productive_bees.snbt").read_bytes() != (SERVER_QUESTS / "reward_tables/wheel_productive_bees.snbt").read_bytes():
        raise RuntimeError("Client/server Productive Bees finale wheel differs")

    print(
        f"Applied Amber & Arcana {VERSION}: Productive Bees reward pools now have "
        f"{sum(stats['tier_entry_counts'].values())} tier entries, 4 Tier-4 draws, "
        f"5 finale draws, and rare Omega Productivity jackpots",
        flush=True,
    )


if __name__ == "__main__":
    main()
