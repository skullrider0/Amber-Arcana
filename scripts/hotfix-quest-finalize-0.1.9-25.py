#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-25"
CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
MANIFEST = ROOT / "client/manifest.json"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"

AUTO_ITEM_CHAPTERS = {
    "ae2",
    "ars_nouveau",
    "create_engineering",
    "irons_spells",
    "mekanism",
    "powah",
    "refined_storage",
    "tinkers",
}

ITEM_ID_RE = r"[a-z0-9_.-]+:[a-z0-9_./-]+"
MALFORMED_STACK_RE = re.compile(
    rf'item:\s*\{{\s*count:\s*1(?:[bBsSlL])?\s*,\s*id:\s*"({ITEM_ID_RE})"\s*\}}'
)
HEX_ID_RE = re.compile(r'\bid:\s*"([0-9A-F]{16})"')


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


def top_level_objects(text: str, arr_start: int, arr_end: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    depth = 0
    in_string = False
    escaped = False
    start: int | None = None
    i = arr_start + 1
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
                    out.append((start, i + 1))
                    start = None
        i += 1
    return out


def quest_positions(text: str) -> list[tuple[int, int]]:
    m = re.search(r"(?m)^\s*quests:\s*\[", text)
    if not m:
        raise RuntimeError("Chapter has no quests array")
    arr = text.find("[", m.start())
    arr_end = find_balanced(text, arr, "[", "]")
    return top_level_objects(text, arr, arr_end)


def task_blocks(quest: str) -> list[str]:
    m = re.search(r"(?m)^\s*tasks:\s*\[", quest)
    if not m:
        return []
    arr = quest.find("[", m.start())
    arr_end = find_balanced(quest, arr, "[", "]")
    return [quest[s:e] for s, e in top_level_objects(quest, arr, arr_end)]


def task_type(task: str) -> str | None:
    m = re.search(r'(?m)^\s*type:\s*"([^"]+)"\s*,?\s*$', task)
    return m.group(1) if m else None


def task_item(task: str) -> str | None:
    m = re.search(rf'(?m)^\s*item:\s*"({ITEM_ID_RE})"\s*,?\s*$', task)
    return m.group(1) if m else None


def quest_has_optional_checkmark(quest: str) -> bool:
    for task in task_blocks(quest):
        if task_type(task) == "checkmark" and re.search(r"(?m)^\s*optional_task:\s*true\s*,?\s*$", task):
            return True
    return False


def make_checkmarks_optional(quest: str) -> tuple[str, int]:
    if quest_has_optional_checkmark(quest):
        return quest, 0
    for block in task_blocks(quest):
        if task_type(block) != "checkmark":
            continue
        m = re.search(r'(?m)^(\s*)type:\s*"checkmark"\s*,?\s*$', block)
        if not m:
            continue
        replacement = f'{m.group(1)}optional_task: true\n{m.group(1)}type: "checkmark"'
        new_block = block[:m.start()] + replacement + block[m.end():]
        return quest.replace(block, new_block, 1), 1
    return quest, 0


def polish_auto_quest_text(quest: str) -> str:
    quest = quest.replace(
        "Obtain the listed requirement item(s), complete the objective, then use the manual checkmark to confirm it works as intended.",
        "Obtain the listed requirement item(s). This item milestone completes automatically; the retained checkmark is optional for manual verification.",
    )
    quest = quest.replace("; then confirm the milestone.", "; completion is detected automatically.")
    return quest


def transform_chapter(path: Path) -> tuple[int, int]:
    original = path.read_text()
    original_ids = Counter(HEX_ID_RE.findall(original))
    fixed_text, malformed_fixed = MALFORMED_STACK_RE.subn(lambda m: f'item: "{m.group(1)}"', original)

    replacements: list[tuple[int, int, str]] = []
    optional_added = 0
    for start, end in quest_positions(fixed_text):
        quest = fixed_text[start:end]
        if path.stem in AUTO_ITEM_CHAPTERS:
            items = [task_item(t) for t in task_blocks(quest) if task_type(t) == "item"]
            items = [i for i in items if i]
            if items and all(not item.startswith("minecraft:") for item in items):
                quest, added = make_checkmarks_optional(quest)
                optional_added += added
                if added or quest_has_optional_checkmark(quest):
                    quest = polish_auto_quest_text(quest)
        replacements.append((start, end, quest))

    out = fixed_text
    for start, end, quest in reversed(replacements):
        out = out[:start] + quest + out[end:]

    if Counter(HEX_ID_RE.findall(out)) != original_ids:
        raise RuntimeError(f"ID set changed while finalizing {path.name}")
    path.write_text(out)
    return malformed_fixed, optional_added


def sync_server_tree() -> None:
    if SERVER_QUESTS.exists():
        shutil.rmtree(SERVER_QUESTS)
    shutil.copytree(CLIENT_QUESTS, SERVER_QUESTS)


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def all_chapter_text(root: Path) -> str:
    return "\n".join(path.read_text() for path in sorted((root / "chapters").glob("*.snbt")))


def collect_stats() -> dict[str, int | bool]:
    client_chapters = sorted((CLIENT_QUESTS / "chapters").glob("*.snbt"))
    server_chapters = sorted((SERVER_QUESTS / "chapters").glob("*.snbt"))
    if len(client_chapters) != 25 or len(server_chapters) != 25:
        raise RuntimeError("Expected 25 quest chapters on client and server")

    malformed = quests = optional_checks = required_checks = item_tasks = rewards_missing = 0
    for client in client_chapters:
        server = SERVER_QUESTS / "chapters" / client.name
        if not server.exists() or client.read_bytes() != server.read_bytes():
            raise RuntimeError(f"Client/server quest mismatch: {client.name}")
        text = client.read_text()
        malformed += len(MALFORMED_STACK_RE.findall(text))
        for start, end in quest_positions(text):
            quests += 1
            quest = text[start:end]
            if not re.search(r"(?m)^\s*rewards:\s*\[", quest):
                rewards_missing += 1
            for task in task_blocks(quest):
                kind = task_type(task)
                if kind == "item":
                    item_tasks += 1
                    if not task_item(task):
                        raise RuntimeError(f"Non-canonical item task remains in {client.name}")
                elif kind == "checkmark":
                    if re.search(r"(?m)^\s*optional_task:\s*true\s*,?\s*$", task):
                        optional_checks += 1
                    else:
                        required_checks += 1

    if quests != 106:
        raise RuntimeError(f"Expected 106 quests, found {quests}")
    if malformed:
        raise RuntimeError(f"Malformed lowercase-count ItemStacks remain: {malformed}")
    if rewards_missing:
        raise RuntimeError(f"Quests missing rewards: {rewards_missing}")
    if item_tasks < quests:
        raise RuntimeError(f"Expected at least one item task per quest; found {item_tasks} for {quests} quests")
    if optional_checks <= 0 or required_checks <= 0:
        raise RuntimeError("Expected a mix of automatic item milestones and required manual confirmations")

    all_text = all_chapter_text(CLIENT_QUESTS).lower()
    for stale in ("twilight forest", "twilightforest:", "the aether", "ad_astra:"):
        if stale in all_text:
            raise RuntimeError(f"Removed-content quest reference remains: {stale}")

    return {
        "quests": quests,
        "item_tasks": item_tasks,
        "optional_confirmation_tasks": optional_checks,
        "required_confirmation_tasks": required_checks,
        "malformed_item_stacks_remaining": malformed,
        "client_server_quest_files_identical": True,
        "ids_preserved": True,
    }


def update_readme() -> None:
    text = README.read_text()
    text = text.replace("Amber-and-Arcana-0.1.9-24-", "Amber-and-Arcana-0.1.9-25-")
    text = text.replace("Download Client 0.1.9-24", "Download Client 0.1.9-25")
    text = text.replace("Download Crafty Server 0.1.9-24", "Download Crafty Server 0.1.9-25")
    text = text.replace("| Pack | 0.1.9-24 |", "| Pack | 0.1.9-25 |")
    text = text.replace("Release 0.1.9-24 keeps JEI", "Release 0.1.9-25 keeps JEI")

    duplicate_bullet = (
        "- `config/ftbquests/quests/` (the synchronized 0.1.9-24 quest book)\n"
        "- `config/ftbquests/quests/` (the synchronized 0.1.9-24 quest book)\n"
    )
    if duplicate_bullet in text:
        text = text.replace(duplicate_bullet, "- `config/ftbquests/quests/` (the synchronized 0.1.9-25 quest book)\n")
    text = text.replace(
        "- `config/ftbquests/quests/` (the synchronized 0.1.9-24 quest book)",
        "- `config/ftbquests/quests/` (the synchronized 0.1.9-25 quest book)",
    )

    duplicate_sentence = (
        "In 0.1.9-24 the overlay also updates the FTB Quests configuration so existing Crafty servers receive the repaired quest book. "
        "In 0.1.9-24 the overlay also updates the FTB Quests configuration so existing Crafty servers receive the repaired quest book. "
    )
    text = text.replace(
        duplicate_sentence,
        "In 0.1.9-25 the overlay also updates the FTB Quests configuration so existing Crafty servers receive the repaired quest book. ",
    )

    quest_note = (
        "\nRelease 0.1.9-25 finalizes the FTB Quests 1.20.1 runtime format. Simple item filters are now stored as canonical item-id strings instead of malformed compound stacks with a lowercase inner `count`. Concrete mod-item milestones in the core technology and magic chapters complete automatically; their historical checkmark task IDs remain present as optional verification tasks. Build, claim, habitat, routing, and other behavior-based objectives keep required manual confirmations.\n"
    )
    marker = "## Quest runtime status — 2026-09-15\n"
    if marker in text and quest_note.strip() not in text:
        text = text.replace(marker, marker + quest_note, 1)

    overlay_section = (
        "\n### Quest-only Crafty update\n\n"
        "For an existing Crafty server that already has the correct mods, use `dist/Amber-and-Arcana-0.1.9-25-Crafty-Quest-Overlay.zip`. Stop the server, back up the world, extract the ZIP into the server root with overwrite enabled, and start the server again. If you copy the quest files while the server is already running, run `/ftbquests reload` from the server console or with sufficient in-game permission. The quest-only overlay contains only `config/ftbquests/quests/`; it does not contain a world, mods, or Crafty launcher files.\n"
    )
    validate_marker = "\n## Validate and rebuild\n"
    if validate_marker in text and "### Quest-only Crafty update" not in text:
        text = text.replace(validate_marker, overlay_section + validate_marker, 1)
    README.write_text(text)


def update_changelog() -> None:
    text = CHANGELOG.read_text()
    if "## 0.1.9-25" in text:
        return
    entry = """## 0.1.9-25 — Finalize quest runtime format and automatic milestones

- Repair all malformed FTB Quests simple item stacks by serializing item filters in the canonical 1.20.1 format.
- Preserve every existing 16-character quest/task/reward ID while making concrete mod-item milestones complete automatically.
- Keep historical checkmark task IDs as optional verification tasks for automatic milestones; keep manual confirmation required for build/claim/behavior objectives.
- Add static validation for canonical item-task serialization, mixed automatic/manual progression, ID preservation, and client/server quest parity.
- Add a quest-only Crafty overlay so existing servers can update `config/ftbquests/quests/` without touching worlds or mods.

"""
    if text.startswith("# Changelog\n\n"):
        text = "# Changelog\n\n" + entry + text[len("# Changelog\n\n"):]
    else:
        text = entry + text
    CHANGELOG.write_text(text)


def update_metadata(fixed_total: int, stats: dict[str, int | bool]) -> None:
    update_json(MANIFEST, lambda d: (d.__setitem__("name", f"Amber & Arcana {VERSION}"), d.__setitem__("version", VERSION)))

    def summary_mutate(d: dict) -> None:
        d["pack_version"] = VERSION
        d["quest_finalize_0_1_9_25"] = {
            "enabled": True,
            "malformed_item_stacks_fixed": fixed_total,
            "malformed_item_stacks_remaining": stats["malformed_item_stacks_remaining"],
            "canonical_simple_item_filters": True,
            "auto_item_milestones": stats["optional_confirmation_tasks"],
            "optional_confirmation_tasks": stats["optional_confirmation_tasks"],
            "required_confirmation_tasks": stats["required_confirmation_tasks"],
            "ids_preserved": stats["ids_preserved"],
            "client_server_quest_files_identical": stats["client_server_quest_files_identical"],
            "quest_only_crafty_overlay": f"Amber-and-Arcana-{VERSION}-Crafty-Quest-Overlay.zip",
        }

    def validation_mutate(d: dict) -> None:
        d["pack_version"] = VERSION
        d["quest_finalize_0_1_9_25"] = {
            "quests_checked": stats["quests"],
            "item_tasks_checked": stats["item_tasks"],
            "malformed_item_stacks_fixed": fixed_total,
            "malformed_item_stacks_remaining": stats["malformed_item_stacks_remaining"],
            "optional_confirmation_tasks": stats["optional_confirmation_tasks"],
            "required_confirmation_tasks": stats["required_confirmation_tasks"],
            "ids_preserved": stats["ids_preserved"],
            "client_server_quest_files_identical": stats["client_server_quest_files_identical"],
        }

    update_json(SUMMARY, summary_mutate)
    update_json(VALIDATION, validation_mutate)


def main() -> None:
    check_only = "--check-only" in sys.argv[1:]
    if check_only:
        stats = collect_stats()
        manifest = json.loads(MANIFEST.read_text())
        if manifest.get("version") != VERSION:
            raise RuntimeError(f"Manifest version is not {VERSION}")
        validation = json.loads(VALIDATION.read_text()).get("quest_finalize_0_1_9_25", {})
        if validation.get("malformed_item_stacks_remaining") != 0:
            raise RuntimeError("Validation metadata does not confirm zero malformed quest stacks")
        if validation.get("optional_confirmation_tasks") != stats["optional_confirmation_tasks"]:
            raise RuntimeError("Automatic quest count differs from validation metadata")
        if validation.get("required_confirmation_tasks") != stats["required_confirmation_tasks"]:
            raise RuntimeError("Manual quest count differs from validation metadata")
        print(f"Amber & Arcana {VERSION} quest finalization validation passed")
        return

    previous = {}
    if SUMMARY.exists():
        previous = json.loads(SUMMARY.read_text()).get("quest_finalize_0_1_9_25", {})

    malformed_fixed = 0
    optional_added = 0
    for path in sorted((CLIENT_QUESTS / "chapters").glob("*.snbt")):
        fixed, added = transform_chapter(path)
        malformed_fixed += fixed
        optional_added += added

    if not previous and malformed_fixed < 106:
        raise RuntimeError(f"Expected at least one malformed quest item stack per quest on first apply, repaired only {malformed_fixed}")

    sync_server_tree()
    stats = collect_stats()
    fixed_total = int(previous.get("malformed_item_stacks_fixed", malformed_fixed))
    if fixed_total <= 0:
        raise RuntimeError("No malformed item-stack repair was recorded")

    update_metadata(fixed_total, stats)
    update_readme()
    update_changelog()

    print(
        f"Applied Amber & Arcana {VERSION}: fixed {malformed_fixed} stacks this run, "
        f"added {optional_added} optional confirmations, "
        f"{stats['optional_confirmation_tasks']} automatic milestones / "
        f"{stats['required_confirmation_tasks']} manual confirmations"
    )


if __name__ == "__main__":
    main()
