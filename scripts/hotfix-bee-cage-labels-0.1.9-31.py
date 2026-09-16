#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-31"
CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"
PB_CHAPTER = CLIENT_QUESTS / "chapters/productive_bees.snbt"
MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
VALIDATE_SH = ROOT / "scripts/validate.sh"


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
    raise RuntimeError(f"Unbalanced {opench}{closech} structure")


def named_array(text: str, name: str) -> tuple[int, int] | None:
    m = re.search(rf"(?m)^\s*{re.escape(name)}:\s*\[", text)
    if not m:
        return None
    arr = text.find("[", m.start())
    return arr, find_balanced(text, arr, "[", "]")


def top_level_objects(text: str, arr_start: int, arr_end: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    depth = 0
    in_string = False
    escaped = False
    start = None
    for i in range(arr_start + 1, arr_end):
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
                    out.append((start, i + 1))
                    start = None
    return out


def quest_positions(text: str) -> list[tuple[int, int]]:
    arr = named_array(text, "quests")
    if not arr:
        raise RuntimeError("Productive Bees chapter has no quests array")
    return top_level_objects(text, *arr)


def quest_title(block: str) -> str:
    matches = re.findall(r'(?m)^\s*title:\s*"([^"]*)"\s*,?\s*$', block)
    if not matches:
        raise RuntimeError("Productive Bees quest is missing a title")
    return matches[-1]


def patch_task_title(task: str, label: str) -> str:
    # ItemTask inherits QuestObject title support. Supplying a raw task title makes
    # FTB Quests show the exact species instead of Bee Cage () / generic bee age data.
    pattern = r'(?m)^(\s*)title:\s*"[^"]*"\s*(,?)\s*$'
    m = re.search(pattern, task)
    safe = label.replace("\\", "\\\\").replace('"', '\\"')
    if m:
        indent, comma = m.group(1), m.group(2)
        return re.sub(pattern, f'{indent}title: "{safe}"{comma}', task, count=1)

    type_line = re.search(r'(?m)^(\s*)type:\s*"item"\s*(,?)\s*$', task)
    if not type_line:
        raise RuntimeError("Bee Cage task is missing type: item")
    indent = type_line.group(1)
    return task[:type_line.start()] + f'{indent}title: "{safe}"\n' + task[type_line.start():]


def patch_bee_cage_ui(text: str) -> tuple[str, int, int]:
    patched = 0
    verified_specific = 0

    for qstart, qend in reversed(quest_positions(text)):
        quest = text[qstart:qend]
        title = quest_title(quest)
        tasks_arr = named_array(quest, "tasks")
        if not tasks_arr:
            continue
        task_positions = top_level_objects(quest, *tasks_arr)

        for tstart, tend in reversed(task_positions):
            task = quest[tstart:tend]
            # Ignore the ordinary setup quest that only asks for an empty Bee Cage.
            if 'id: "productivebees:bee_cage"' not in task or "item: {" not in task:
                continue
            if 'match_nbt: true' not in task or 'weak_nbt_match: true' not in task:
                raise RuntimeError(f"{title}: species cage task is not NBT-matched")

            entity = re.search(r'(?m)^\s*entity:\s*"([^"]+)"', task)
            if not entity:
                raise RuntimeError(f"{title}: species cage task has no entity NBT filter")
            entity_id = entity.group(1)
            if entity_id == "productivebees:configurable_bee":
                type_match = re.search(r'(?m)^\s*type:\s*"(productivebees:[^"]+)"', task)
                if not type_match:
                    raise RuntimeError(f"{title}: configurable cage has no bee type filter")
            verified_specific += 1

            task = patch_task_title(task, f"Capture {title}")
            quest = quest[:tstart] + task + quest[tend:]
            patched += 1

        text = text[:qstart] + quest + text[qend:]

    expected = int(json.loads(VALIDATION.read_text()).get("quest_ux_0_1_9_30", {}).get("bee_cage_tasks", 0))
    if expected and patched != expected:
        raise RuntimeError(f"Expected {expected} species-specific Bee Cage tasks, patched {patched}")
    if patched == 0:
        raise RuntimeError("No species-specific Productive Bees cage tasks were found")
    return text, patched, verified_specific


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def sync_server() -> None:
    if SERVER_QUESTS.exists():
        shutil.rmtree(SERVER_QUESTS)
    shutil.copytree(CLIENT_QUESTS, SERVER_QUESTS)


def update_validator(patched: int) -> None:
    if not VALIDATE_SH.exists():
        return
    text = VALIDATE_SH.read_text()
    text = text.replace('.version == "0.1.9-29"', '.version == "0.1.9-31"')
    text = text.replace('.version == "0.1.9-30"', '.version == "0.1.9-31"')
    text = text.replace('.pack_version == "0.1.9-29"', '.pack_version == "0.1.9-31"')
    text = text.replace('.pack_version == "0.1.9-30"', '.pack_version == "0.1.9-31"')
    text = text.replace('Amber & Arcana 0.1.9-29 static validation passed', 'Amber & Arcana 0.1.9-31 static validation passed')
    text = text.replace('Amber & Arcana 0.1.9-30 static validation passed', 'Amber & Arcana 0.1.9-31 static validation passed')
    marker = "# 0.1.9-31 Productive Bees cage-label checks"
    if marker not in text:
        text += f'''\n\n{marker}\njq -e '.bee_cage_ui_0_1_9_31.cage_tasks_labeled == {patched} and .bee_cage_ui_0_1_9_31.species_filters_verified == {patched} and .bee_cage_ui_0_1_9_31.matching_behavior_changed == false and .bee_cage_ui_0_1_9_31.client_server_quest_files_identical == true' "$validation" >/dev/null\ntest "$(grep -Ec '^\\s*title: "Capture .*Bee"' "$client_quests/chapters/productive_bees.snbt")" -ge "{patched}" || {{ echo "Productive Bees cage task species labels missing" >&2; exit 1; }}\n'''
    VALIDATE_SH.write_text(text)


def update_docs(patched: int) -> None:
    text = README.read_text()
    text = text.replace("Amber-and-Arcana-0.1.9-30-", "Amber-and-Arcana-0.1.9-31-")
    text = text.replace("Download Client 0.1.9-30", "Download Client 0.1.9-31")
    text = text.replace("Download Crafty Server 0.1.9-30", "Download Crafty Server 0.1.9-31")
    text = text.replace("| Pack | 0.1.9-30 |", "| Pack | 0.1.9-31 |")
    marker = "## Quest runtime status — 2026-09-15\n"
    note = (
        f"\nRelease 0.1.9-31 gives all {patched} species-specific Productive Bees cage tasks explicit task labels such as `Capture Ashy Mining Bee`. "
        "The existing NBT filters were already species-specific; this release fixes the misleading generic `Bee Cage ()` tooltip without loosening or changing completion matching.\n"
    )
    if marker in text and "Release 0.1.9-31 gives all" not in text:
        text = text.replace(marker, marker + note, 1)
    README.write_text(text)

    changelog = CHANGELOG.read_text()
    if "## 0.1.9-31" not in changelog:
        entry = (
            "## 0.1.9-31 — Productive Bees cage task labels\n\n"
            f"- Give all {patched} species-specific Bee Cage tasks explicit species labels in FTB Quests.\n"
            "- Preserve the existing `match_nbt: true` + weak-NBT species filters; only the task presentation changes.\n"
            "- Keep quest/task/reward IDs and existing player progression intact.\n\n"
        )
        if changelog.startswith("# Changelog\n\n"):
            changelog = "# Changelog\n\n" + entry + changelog[len("# Changelog\n\n"):]
        else:
            changelog = entry + changelog
        CHANGELOG.write_text(changelog)


def main() -> None:
    text = PB_CHAPTER.read_text()
    text, patched, verified = patch_bee_cage_ui(text)
    PB_CHAPTER.write_text(text)

    def manifest_mutate(d):
        d["version"] = VERSION
        d["name"] = f"Amber & Arcana {VERSION}"
    update_json(MANIFEST, manifest_mutate)

    payload = {
        "cage_tasks_labeled": patched,
        "species_filters_verified": verified,
        "task_label_format": "Capture <exact quest bee species>",
        "matching_behavior_changed": False,
        "historical_ids_preserved": True,
        "client_server_quest_files_identical": True,
    }

    def summary_mutate(d):
        d["pack_version"] = VERSION
        d["bee_cage_ui_0_1_9_31"] = payload
    update_json(SUMMARY, summary_mutate)

    def validation_mutate(d):
        d["pack_version"] = VERSION
        d["bee_cage_ui_0_1_9_31"] = payload
    update_json(VALIDATION, validation_mutate)

    sync_server()
    update_docs(patched)
    update_validator(patched)

    if PB_CHAPTER.read_bytes() != (SERVER_QUESTS / "chapters/productive_bees.snbt").read_bytes():
        raise RuntimeError("Client/server Productive Bees chapter differs after cage-label patch")

    print(
        f"Applied Amber & Arcana {VERSION}: labeled {patched} species-specific Bee Cage tasks; "
        f"verified {verified} NBT species filters without changing matching behavior",
        flush=True,
    )


if __name__ == "__main__":
    main()
