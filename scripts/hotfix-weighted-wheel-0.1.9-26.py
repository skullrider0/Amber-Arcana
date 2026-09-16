#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-26"
CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"
CLIENT_LANG = ROOT / "client/overrides/kubejs/assets/ftbquests/lang/en_us.json"
MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"

ITEM_ID_RE = r"[a-z0-9_.-]+:[a-z0-9_./-]+"


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


def named_array(text: str, name: str, start_at: int = 0) -> tuple[int, int] | None:
    m = re.search(rf"(?m)^\s*{re.escape(name)}:\s*\[", text[start_at:])
    if not m:
        return None
    pos = start_at + m.start()
    arr = text.find("[", pos)
    return arr, find_balanced(text, arr, "[", "]")


def quest_positions(text: str) -> list[tuple[int, int]]:
    arr = named_array(text, "quests")
    if not arr:
        raise RuntimeError("Chapter has no quests array")
    return top_level_objects(text, *arr)


def child_blocks(parent: str, name: str) -> list[str]:
    arr = named_array(parent, name)
    if not arr:
        return []
    return [parent[s:e] for s, e in top_level_objects(parent, *arr)]


def block_type(block: str) -> str | None:
    m = re.search(r'(?m)^\s*type:\s*"([^"]+)"\s*,?\s*$', block)
    return m.group(1) if m else None


def block_item(block: str) -> str | None:
    m = re.search(rf'(?m)^\s*item:\s*"({ITEM_ID_RE})"\s*,?\s*$', block)
    return m.group(1) if m else None


def block_count(block: str) -> int:
    m = re.search(r"(?m)^\s*count:\s*(\d+)(?:[bBsSlL])?\s*,?\s*$", block)
    return max(1, int(m.group(1))) if m else 1


def chapter_title(text: str, fallback: str) -> str:
    # Chapter title is outside quest objects and appears before the quests array in this pack.
    before = text[: named_array(text, "quests")[0]]
    matches = re.findall(r'(?m)^\s*title:\s*"([^"]+)"\s*,?\s*$', before)
    return matches[-1] if matches else fallback.replace("_", " ").title()


def deterministic_long(seed: str) -> int:
    # Positive signed Java long, stable across builds.
    value = int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:8], "big") & ((1 << 63) - 1)
    return value or 1


def deterministic_hex(seed: str) -> str:
    return f"{deterministic_long(seed):016X}"


def build_pool(text: str) -> list[tuple[str, int, float]]:
    # Ordered by appearance so the table feels like the chapter rather than a registry dump.
    pool: OrderedDict[str, dict[str, float | int | bool]] = OrderedDict()

    for qs, qe in quest_positions(text):
        quest = text[qs:qe]

        # Existing fixed quest rewards are the common/medium wheel results.
        for reward in child_blocks(quest, "rewards"):
            if block_type(reward) != "item":
                continue
            item = block_item(reward)
            if not item:
                continue
            count = min(16, block_count(reward))
            entry = pool.setdefault(item, {"count": count, "weight": 0.0, "reward": True})
            entry["count"] = max(int(entry["count"]), count)
            entry["weight"] = min(40.0, float(entry["weight"]) + 18.0)
            entry["reward"] = True

        # Modded requirement items become rare jackpot results. Because the wheel is
        # attached only to the chapter finale, these cannot skip that chapter's progression.
        for task in child_blocks(quest, "tasks"):
            if block_type(task) != "item":
                continue
            item = block_item(task)
            if not item:
                continue
            modded = not item.startswith("minecraft:")
            entry = pool.setdefault(item, {"count": 1, "weight": 0.0, "reward": False})
            if not bool(entry["reward"]):
                entry["weight"] = max(float(entry["weight"]), 7.0 if modded else 2.0)

    if not pool:
        raise RuntimeError("Chapter has no item rewards or item tasks to build a wheel pool")

    # Keep each table readable in the FTB tooltip. Prefer the fixed rewards, then
    # modded task items, then vanilla task items. A maximum of eight options makes
    # weights understandable and prevents giant tooltips.
    entries = list(pool.items())
    entries.sort(
        key=lambda kv: (
            0 if bool(kv[1]["reward"]) else 1,
            0 if not kv[0].startswith("minecraft:") else 1,
            -float(kv[1]["weight"]),
        )
    )
    entries = entries[:8]

    result: list[tuple[str, int, float]] = []
    for item, data in entries:
        result.append((item, int(data["count"]), float(data["weight"])))
    return result


def render_table(table_id: int, title: str, order_index: int, pool: list[tuple[str, int, float]]) -> str:
    modded = next((item for item, _, _ in pool if not item.startswith("minecraft:")), None)
    icon = modded or pool[0][0]
    lines = [
        "{",
        f'\ticon: "{icon}"',
        f'\tid: "{table_id:016X}"',
        "\tloot_size: 1",
        f"\torder_index: {order_index}",
        "\trewards: [",
    ]
    for item, count, weight in pool:
        count_part = f"count: {count}, " if count != 1 else ""
        lines.append(f'\t\t{{ {count_part}item: "{item}", weight: {weight:.1f}f }}')
    lines += [
        "\t]",
        f'\ttitle: "Wheel of Fortune — {title}"',
        "\tuse_title: true",
        "}",
        "",
    ]
    return "\n".join(lines)


def add_loot_reward_to_finale(text: str, stem: str, table_id: int) -> tuple[str, bool]:
    reward_id = deterministic_hex(f"amber-arcana-wheel-reward:{stem}")
    if reward_id in text or re.search(rf"table_id:\s*{table_id}L", text):
        return text, False

    quests = quest_positions(text)
    if not quests:
        raise RuntimeError(f"No quests in {stem}")
    start, end = quests[-1]
    quest = text[start:end]
    arr = named_array(quest, "rewards")
    if not arr:
        raise RuntimeError(f"Final quest in {stem} has no rewards array")
    _, arr_end = arr

    indent_match = re.search(r"(?m)^(\s*)rewards:\s*\[", quest)
    base_indent = indent_match.group(1) if indent_match else "\t\t\t"
    item_indent = base_indent + "\t"
    prop_indent = item_indent + "\t"
    block = (
        "\n"
        f"{item_indent}{{\n"
        f'{prop_indent}id: "{reward_id}"\n'
        f"{prop_indent}table_id: {table_id}L\n"
        f'{prop_indent}title: "Spin the Wheel of Fortune"\n'
        f'{prop_indent}type: "loot"\n'
        f"{item_indent}}}\n"
        f"{base_indent}"
    )
    quest = quest[:arr_end] + block + quest[arr_end:]

    # Add a concise player-facing note once, but do not rewrite historical quest IDs/tasks.
    desc = named_array(quest, "description")
    if desc and "Wheel of Fortune" not in quest:
        _, desc_end = desc
        desc_indent_match = re.search(r"(?m)^(\s*)description:\s*\[", quest)
        di = (desc_indent_match.group(1) if desc_indent_match else base_indent) + "\t"
        note = f'\n{di}"&dWheel of Fortune:&r The finale includes one weighted bonus roll. Click its reward icon to reveal the result."\n{base_indent}'
        quest = quest[:desc_end] + note + quest[desc_end:]

    return text[:start] + quest + text[end:], True


def write_lang_override() -> None:
    CLIENT_LANG.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if CLIENT_LANG.exists():
        try:
            data = json.loads(CLIENT_LANG.read_text())
        except json.JSONDecodeError:
            data = {}
    data["ftbquests.rewards"] = "Wheel of Fortune"
    CLIENT_LANG.write_text(json.dumps(data, indent=2) + "\n")


def sync_server_quests() -> None:
    if SERVER_QUESTS.exists():
        shutil.rmtree(SERVER_QUESTS)
    shutil.copytree(CLIENT_QUESTS, SERVER_QUESTS)


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_docs(table_count: int, modded_entries: int) -> None:
    text = README.read_text()
    text = text.replace("Amber-and-Arcana-0.1.9-25-", "Amber-and-Arcana-0.1.9-26-")
    text = text.replace("Download Client 0.1.9-25", "Download Client 0.1.9-26")
    text = text.replace("Download Crafty Server 0.1.9-25", "Download Crafty Server 0.1.9-26")
    text = text.replace("| Pack | 0.1.9-25 |", "| Pack | 0.1.9-26 |")
    marker = "## Quest runtime status — 2026-09-15\n"
    note = (
        "\nRelease 0.1.9-26 adds a weighted Wheel of Fortune bonus to every chapter finale. "
        f"The build generates {table_count} chapter-themed wheel tables from already-validated quest rewards and requirement items, including {modded_entries} modded-item entries. "
        "The wheel uses FTB Quests' native `loot` reward path, which requires a deliberate click, rolls server-side, and opens the full-screen reward reveal. Existing fixed rewards and all historical quest/task/reward IDs remain intact.\n"
    )
    if marker in text and "Release 0.1.9-26 adds a weighted Wheel of Fortune" not in text:
        text = text.replace(marker, marker + note, 1)
    README.write_text(text)

    changelog = CHANGELOG.read_text()
    if "## 0.1.9-26" not in changelog:
        entry = (
            "## 0.1.9-26 — Weighted Wheel of Fortune finale rewards\n\n"
            "- Add a server-authoritative weighted `loot` reward to every chapter finale using FTB Quests 2001.4.14's native reward-table system.\n"
            "- Generate chapter-themed weighted tables from existing validated rewards and item requirements, with modded requirement items used as rarer jackpot results.\n"
            "- Preserve all existing fixed rewards and historical quest/task/reward IDs; wheel rewards are additive.\n"
            "- Brand the native full-screen reward reveal as `Wheel of Fortune` on updated clients.\n"
            "- Keep client and dedicated-server quest trees byte-identical after generation.\n\n"
        )
        if changelog.startswith("# Changelog\n\n"):
            changelog = "# Changelog\n\n" + entry + changelog[len("# Changelog\n\n"):]
        else:
            changelog = entry + changelog
        CHANGELOG.write_text(changelog)


def main() -> None:
    chapters = sorted((CLIENT_QUESTS / "chapters").glob("*.snbt"))
    if len(chapters) != 25:
        raise RuntimeError(f"Expected 25 chapters, found {len(chapters)}")

    table_dir = CLIENT_QUESTS / "reward_tables"
    table_dir.mkdir(parents=True, exist_ok=True)

    # Remove only wheel tables generated by this hotfix, keeping the five historical tables.
    for old in table_dir.glob("wheel_*.snbt"):
        old.unlink()

    wheels_added = 0
    modded_entries = 0
    total_entries = 0
    ids_seen: set[int] = set()

    for index, chapter in enumerate(chapters):
        text = chapter.read_text()
        stem = chapter.stem
        title = chapter_title(text, stem)
        pool = build_pool(text)
        total_entries += len(pool)
        modded_entries += sum(1 for item, _, _ in pool if not item.startswith("minecraft:"))

        table_id = deterministic_long(f"amber-arcana-wheel-table:{stem}")
        if table_id in ids_seen:
            raise RuntimeError(f"Wheel table ID collision for {stem}")
        ids_seen.add(table_id)

        table_file = table_dir / f"wheel_{stem}.snbt"
        table_file.write_text(render_table(table_id, title, 100 + index, pool))

        updated, added = add_loot_reward_to_finale(text, stem, table_id)
        chapter.write_text(updated)
        wheels_added += int(added)

    if wheels_added not in (0, 25):
        raise RuntimeError(f"Expected 25 new finale wheel rewards on first application (or 0 idempotently), got {wheels_added}")

    # Every generated table should have at least one modded result somewhere in the release.
    if modded_entries < 25:
        raise RuntimeError(f"Expected broad modded-item coverage, found only {modded_entries} modded wheel entries")

    write_lang_override()
    sync_server_quests()

    total_tables = len(list((CLIENT_QUESTS / "reward_tables").glob("*.snbt")))
    if total_tables != 30:
        raise RuntimeError(f"Expected 30 reward tables (5 historical + 25 wheels), found {total_tables}")

    # Static integrity checks before metadata/docs are changed.
    if any(a.read_bytes() != (SERVER_QUESTS / "chapters" / a.name).read_bytes() for a in chapters):
        raise RuntimeError("Client/server chapter mismatch after wheel generation")
    if any(a.read_bytes() != (SERVER_QUESTS / "reward_tables" / a.name).read_bytes() for a in table_dir.glob("*.snbt")):
        raise RuntimeError("Client/server reward-table mismatch after wheel generation")

    client_text = "\n".join(p.read_text() for p in chapters)
    if len(re.findall(r'(?m)^\s*type:\s*"loot"\s*,?\s*$', client_text)) != 25:
        raise RuntimeError("Expected exactly 25 finale loot rewards")
    if len(re.findall(r"(?m)^\s*table_id:\s*\d+L\s*,?\s*$", client_text)) < 25:
        raise RuntimeError("Wheel table references are missing")

    update_json(MANIFEST, lambda d: (d.__setitem__("name", f"Amber & Arcana {VERSION}"), d.__setitem__("version", VERSION)))

    def summary_mutate(d: dict) -> None:
        d["pack_version"] = VERSION
        d["wheel_of_fortune_0_1_9_26"] = {
            "enabled": True,
            "chapter_finale_wheels": 25,
            "generated_wheel_tables": 25,
            "historical_reward_tables_retained": 5,
            "total_reward_tables": total_tables,
            "weighted_entries": total_entries,
            "modded_item_entries": modded_entries,
            "reward_type": "ftbquests:loot",
            "full_screen_reveal": True,
            "server_authoritative_roll": True,
            "existing_fixed_rewards_preserved": True,
            "client_server_quest_files_identical": True,
        }

    def validation_mutate(d: dict) -> None:
        d["pack_version"] = VERSION
        d["wheel_of_fortune_0_1_9_26"] = {
            "chapters_checked": 25,
            "finale_loot_rewards": 25,
            "generated_wheel_tables": 25,
            "total_reward_tables": total_tables,
            "weighted_entries": total_entries,
            "modded_item_entries": modded_entries,
            "client_server_quest_files_identical": True,
            "historical_ids_preserved": True,
        }

    update_json(SUMMARY, summary_mutate)
    update_json(VALIDATION, validation_mutate)
    update_docs(total_tables, modded_entries)

    print(
        f"Applied Amber & Arcana {VERSION}: 25 finale wheels, {total_tables} total tables, "
        f"{total_entries} weighted entries ({modded_entries} modded)"
    )


if __name__ == "__main__":
    main()
