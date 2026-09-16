#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-29"

CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"
CLIENT_CHAPTERS = CLIENT_QUESTS / "chapters"
GROUPS_FILE = CLIENT_QUESTS / "chapter_groups.snbt"
MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"

# Stable IDs below the signed-long high bit. Keep these forever once published.
GROUPS = [
    ("5A29000000000001", "Start Here"),
    ("5A29000000000002", "Machines & Production"),
    ("5A29000000000003", "Storage & Networks"),
    ("5A29000000000004", "Resources & Farming"),
    ("5A29000000000005", "Magic & Rituals"),
    ("5A29000000000006", "Exploration & Creatures"),
    ("5A29000000000007", "Building & Settlements"),
    ("5A29000000000008", "Tools, Combat & Equipment"),
    ("5A29000000000009", "Collections & Endgame"),
]

# Chapters are grouped by gameplay mechanic rather than mod-name/alphabetical order.
# Order indexes are local to each chapter group.
ASSIGNMENTS = {
    "getting_started": ("5A29000000000001", 0),

    "create_engineering": ("5A29000000000002", 0),
    "mekanism": ("5A29000000000002", 1),
    "ender_io": ("5A29000000000002", 2),
    "powah": ("5A29000000000002", 3),
    "create_workshops": ("5A29000000000002", 4),
    "create_city": ("5A29000000000002", 5),

    "ae2": ("5A29000000000003", 0),
    "refined_storage": ("5A29000000000003", 1),

    "productive_bees": ("5A29000000000004", 0),
    # Reserve order_index 1 for Mystical Agriculture if it is added later.
    "food_factory": ("5A29000000000004", 2),
    "butchery": ("5A29000000000004", 3),

    "ars_nouveau": ("5A29000000000005", 0),
    "irons_spells": ("5A29000000000005", 1),
    "ritual_magic": ("5A29000000000005", 2),

    "alex_caves": ("5A29000000000006", 0),
    "dimensions": ("5A29000000000006", 1),
    "dinosaur_laboratory": ("5A29000000000006", 2),
    "alex_wildlife": ("5A29000000000006", 3),
    "aquarium": ("5A29000000000006", 4),

    "settlement": ("5A29000000000007", 0),

    "tinkers": ("5A29000000000008", 0),
    "firearms": ("5A29000000000008", 1),
    "alex_utilities": ("5A29000000000008", 2),

    "buddycards": ("5A29000000000009", 0),
    "endgame": ("5A29000000000009", 1),
}


def write_groups() -> None:
    lines = ["{", "\tchapter_groups: ["]
    for group_id, title in GROUPS:
        lines.append(f'\t\t{{ id: "{group_id}", title: "{title}" }}')
    lines += ["\t]", "}", ""]
    GROUPS_FILE.write_text("\n".join(lines))


def set_group(text: str, group_id: str, filename: str) -> str:
    pattern = r'^\s*group:\s*"[^"]*"\s*$'
    if re.search(pattern, text, flags=re.MULTILINE):
        return re.sub(pattern, f'\tgroup: "{group_id}"', text, count=1, flags=re.MULTILINE)

    # Some historical chapters never had a group field. Insert it immediately
    # after filename so the result remains normal FTB Quests chapter SNBT.
    pattern = r'^(\s*filename:\s*"[^"]+"\s*)$'
    updated, count = re.subn(
        pattern,
        lambda m: m.group(1) + f'\n\tgroup: "{group_id}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise RuntimeError(f"Could not add group field to {filename}")
    return updated


def set_order(text: str, order: int, filename: str) -> str:
    pattern = r'^\s*order_index:\s*-?\d+\s*$'
    if re.search(pattern, text, flags=re.MULTILINE):
        return re.sub(pattern, f"\torder_index: {order}", text, count=1, flags=re.MULTILINE)

    # Be tolerant of old chapters without order_index as well.
    pattern = r'^(\s*quest_links:\s*\[.*)$'
    updated, count = re.subn(
        pattern,
        lambda m: f"\torder_index: {order}\n" + m.group(1),
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise RuntimeError(f"Could not add order_index to {filename}")
    return updated


def organize_chapters() -> dict[str, int]:
    files = sorted(CLIENT_CHAPTERS.glob("*.snbt"))
    stems = {p.stem for p in files}
    expected = set(ASSIGNMENTS)
    missing = expected - stems
    unassigned = stems - expected
    if missing or unassigned:
        raise RuntimeError(
            f"Quest grouping must explicitly cover every chapter. Missing={sorted(missing)}; unassigned={sorted(unassigned)}"
        )

    counts = {title: 0 for _, title in GROUPS}
    title_by_id = dict(GROUPS)

    for path in files:
        group_id, order = ASSIGNMENTS[path.stem]
        text = path.read_text()
        text = set_group(text, group_id, path.name)
        text = set_order(text, order, path.name)
        path.write_text(text)
        counts[title_by_id[group_id]] += 1

    return counts


def sync_server() -> None:
    if SERVER_QUESTS.exists():
        shutil.rmtree(SERVER_QUESTS)
    shutil.copytree(CLIENT_QUESTS, SERVER_QUESTS)


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_docs(counts: dict[str, int]) -> None:
    text = README.read_text()
    text = text.replace("Amber-and-Arcana-0.1.9-28-", "Amber-and-Arcana-0.1.9-29-")
    text = text.replace("Download Client 0.1.9-28", "Download Client 0.1.9-29")
    text = text.replace("Download Crafty Server 0.1.9-28", "Download Crafty Server 0.1.9-29")
    text = text.replace("| Pack | 0.1.9-28 |", "| Pack | 0.1.9-29 |")
    marker = "## Quest runtime status — 2026-09-15\n"
    note = (
        "\nRelease 0.1.9-29 reorganizes every quest chapter by gameplay mechanic instead of leaving the quest book mostly flat. "
        "The new chapter groups are Start Here, Machines & Production, Storage & Networks, Resources & Farming, "
        "Magic & Rituals, Exploration & Creatures, Building & Settlements, Tools/Combat & Equipment, and Collections & Endgame. "
        "Create, Mekanism, Ender IO, Powah and the other production chapters now live together; Productive Bees is placed in Resources & Farming, "
        "with an intentional ordering slot reserved for a future Mystical Agriculture chapter if that mod is added. "
        "Only chapter grouping/order metadata changes; quest/task/reward IDs and progression remain intact.\n"
    )
    if marker in text and "Release 0.1.9-29 reorganizes every quest chapter" not in text:
        text = text.replace(marker, marker + note, 1)
    README.write_text(text)

    changelog = CHANGELOG.read_text()
    if "## 0.1.9-29" not in changelog:
        group_lines = "\n".join(f"  - {name}: {count} chapter(s)" for name, count in counts.items())
        entry = (
            "## 0.1.9-29 — Mechanics-based quest organization\n\n"
            "- Reorganize all 26 FTB Quests chapters into stable mechanic-based chapter groups.\n"
            "- Put Create Engineering/Workshops/City, Mekanism, Ender IO and Powah under Machines & Production.\n"
            "- Put Applied Energistics 2 and Refined Storage under Storage & Networks.\n"
            "- Put Productive Bees and resource/food-production content under Resources & Farming, reserving order index 1 for a future Mystical Agriculture chapter.\n"
            "- Separate magic, exploration/creatures, settlements, tools/combat, and collection/endgame content into their own groups.\n"
            "- Preserve every existing chapter, quest, task and reward ID; this is navigation/order only.\n"
            f"{group_lines}\n\n"
        )
        if changelog.startswith("# Changelog\n\n"):
            changelog = "# Changelog\n\n" + entry + changelog[len("# Changelog\n\n"):]
        else:
            changelog = entry + changelog
        CHANGELOG.write_text(changelog)


def main() -> None:
    write_groups()
    counts = organize_chapters()
    sync_server()

    def mutate_manifest(data):
        data["version"] = VERSION
        data["name"] = f"Amber & Arcana {VERSION}"
    update_json(MANIFEST, mutate_manifest)

    group_stats = [
        {"id": group_id, "title": title, "chapters": counts[title]}
        for group_id, title in GROUPS
    ]

    def mutate_summary(data):
        data["pack_version"] = VERSION
        data["quest_organization_0_1_9_29"] = {
            "chapter_groups": len(GROUPS),
            "chapters_grouped": len(ASSIGNMENTS),
            "groups": group_stats,
            "future_mystical_agriculture_slot": "Resources & Farming / order_index 1",
            "quest_ids_changed": False,
            "client_server_quest_files_identical": True,
        }
    update_json(SUMMARY, mutate_summary)

    def mutate_validation(data):
        data["pack_version"] = VERSION
        data["quest_organization_0_1_9_29"] = {
            "chapter_groups": len(GROUPS),
            "chapters_grouped": len(ASSIGNMENTS),
            "groups": group_stats,
            "all_chapters_explicitly_assigned": True,
            "historical_ids_preserved": True,
            "client_server_quest_files_identical": True,
        }
    update_json(VALIDATION, mutate_validation)

    update_docs(counts)

    client_files = {p.relative_to(CLIENT_QUESTS) for p in CLIENT_QUESTS.rglob("*") if p.is_file()}
    server_files = {p.relative_to(SERVER_QUESTS) for p in SERVER_QUESTS.rglob("*") if p.is_file()}
    if client_files != server_files:
        raise RuntimeError("Client/server quest file sets differ after grouping")
    for rel in client_files:
        if (CLIENT_QUESTS / rel).read_bytes() != (SERVER_QUESTS / rel).read_bytes():
            raise RuntimeError(f"Client/server quest mismatch after grouping: {rel}")

    print(
        f"Applied Amber & Arcana {VERSION}: organized {len(ASSIGNMENTS)} chapters into {len(GROUPS)} mechanic groups",
        flush=True,
    )


if __name__ == "__main__":
    main()
