#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-32"
CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"
CHAPTERS = CLIENT_QUESTS / "chapters"
TABLES = CLIENT_QUESTS / "reward_tables"
MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
VALIDATE_SH = ROOT / "scripts/validate.sh"

# Powah is explicitly curated because its current quest chapter only references a
# few early blocks. These IDs are normal Powah tier families (no creative items).
POWAH_TIERS = {
    1: [
        "powah:dielectric_casing",
        "powah:energizing_orb",
        "powah:thermo_generator_starter",
        "powah:energy_cell_starter",
        "powah:energy_cell_basic",
        "powah:reactor_starter",
    ],
    2: [
        "powah:thermo_generator_basic",
        "powah:thermo_generator_hardened",
        "powah:energy_cell_hardened",
        "powah:reactor_basic",
        "powah:reactor_hardened",
        "powah:energizing_rod_hardened",
    ],
    3: [
        "powah:thermo_generator_blazing",
        "powah:thermo_generator_niotic",
        "powah:energy_cell_blazing",
        "powah:energy_cell_niotic",
        "powah:reactor_blazing",
        "powah:reactor_niotic",
        "powah:energizing_rod_niotic",
    ],
    4: [
        "powah:thermo_generator_spirited",
        "powah:energy_cell_spirited",
        "powah:reactor_spirited",
        "powah:energizing_rod_spirited",
        "powah:thermo_generator_nitro",
        "powah:energy_cell_nitro",
        "powah:reactor_nitro",
        "powah:energizing_rod_nitro",
    ],
}
POWAH_JACKPOTS = {
    "powah:thermo_generator_nitro": 0.25,
    "powah:reactor_nitro": 0.20,
    "powah:energy_cell_nitro": 0.35,
    "powah:energizing_rod_nitro": 0.50,
}

# Higher tiers give several independently weighted results, but jackpot machines
# are kept at sub-1 weights so extra draws do not make Nitro equipment common.
LOOT_SIZE = {1: 1, 2: 2, 3: 2, 4: 3}


def deterministic_long(seed: str) -> int:
    value = int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:8], "big") & ((1 << 63) - 1)
    return value or 1


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


def named_array(text: str, name: str, start_at: int = 0) -> tuple[int, int] | None:
    m = re.search(rf"(?m)^\s*{re.escape(name)}:\s*\[", text[start_at:])
    if not m:
        return None
    pos = start_at + m.start()
    arr = text.find("[", pos)
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
        return []
    return top_level_objects(text, *arr)


def quest_id(block: str) -> str:
    m = re.search(r'(?m)^\s*id:\s*"([0-9A-F]{16})"', block)
    if not m:
        raise RuntimeError("Quest missing id")
    return m.group(1)


def quest_deps(block: str) -> list[str]:
    arr = named_array(block, "dependencies")
    if not arr:
        return []
    return re.findall(r'"([0-9A-F]{16})"', block[arr[0] + 1:arr[1]])


def chapter_title(text: str, stem: str) -> str:
    head = text[: text.find("quests:") if "quests:" in text else len(text)]
    m = re.search(r'(?m)^\s*title:\s*"([^"]+)"', head)
    return m.group(1) if m else stem.replace("_", " ").title()


def compute_depths(text: str) -> dict[str, int]:
    blocks = [text[s:e] for s, e in quest_positions(text)]
    deps = {quest_id(b): quest_deps(b) for b in blocks}
    memo: dict[str, int] = {}
    visiting: set[str] = set()

    def depth(qid: str) -> int:
        if qid in memo:
            return memo[qid]
        if qid in visiting:
            return 0
        visiting.add(qid)
        parents = [p for p in deps[qid] if p in deps and p != qid]
        value = 0 if not parents else 1 + max(depth(p) for p in parents)
        visiting.remove(qid)
        memo[qid] = value
        return value

    for qid in deps:
        depth(qid)
    return memo


def direct_items(text: str) -> list[str]:
    return re.findall(r'(?m)^\s*item:\s*"([a-z0-9_.-]+:[a-z0-9_./-]+)"', text)


def namespace(item: str) -> str:
    return item.split(":", 1)[0]


def is_modded(item: str) -> bool:
    return namespace(item) not in {"minecraft", "itemfilters", "ftbquests", "kubejs"}


def replace_array_objects(text: str, name: str, objects: list[str]) -> str:
    arr = named_array(text, name)
    if not arr:
        raise RuntimeError(f"Missing {name} array")
    m = re.search(rf'(?m)^(\s*){re.escape(name)}:\s*\[', text)
    base = m.group(1) if m else "\t"
    body = "\n".join(objects)
    return text[:arr[0]] + "[\n" + body + "\n" + base + "]" + text[arr[1] + 1:]


def reward_objects(block: str) -> list[tuple[int, int]]:
    arr = named_array(block, "rewards")
    return top_level_objects(block, *arr) if arr else []


def build_catalog(chapter_texts: dict[str, str]) -> tuple[dict[str, dict[str, int]], dict[str, set[str]]]:
    # namespace -> item -> deepest observed quest depth
    by_namespace: dict[str, dict[str, int]] = defaultdict(dict)
    chapter_namespaces: dict[str, set[str]] = defaultdict(set)
    for stem, text in chapter_texts.items():
        depths = compute_depths(text)
        for s, e in quest_positions(text):
            block = text[s:e]
            qid = quest_id(block)
            for item in direct_items(block):
                if not is_modded(item):
                    continue
                ns = namespace(item)
                chapter_namespaces[stem].add(ns)
                by_namespace[ns][item] = max(by_namespace[ns].get(item, 0), depths.get(qid, 0))

        wheel = TABLES / f"wheel_{stem}.snbt"
        if wheel.exists():
            for item in direct_items(wheel.read_text()):
                if is_modded(item):
                    ns = namespace(item)
                    chapter_namespaces[stem].add(ns)
                    by_namespace[ns][item] = max(by_namespace[ns].get(item, 0), 8)
    return by_namespace, chapter_namespaces


def tiered_items_for_chapter(
    stem: str,
    local_text: str,
    catalog: dict[str, dict[str, int]],
    chapter_namespaces: dict[str, set[str]],
) -> dict[int, list[str]]:
    if stem == "powah":
        return {tier: list(items) for tier, items in POWAH_TIERS.items()}

    namespaces = set(chapter_namespaces.get(stem, set()))
    local_modded = [i for i in direct_items(local_text) if is_modded(i)]
    if not namespaces and local_modded:
        namespaces.update(namespace(i) for i in local_modded)

    candidates: dict[str, int] = {}
    for ns in namespaces:
        candidates.update(catalog.get(ns, {}))

    # If a general chapter has no mod namespace of its own, use a cross-mod starter
    # sampler instead of falling back to diamonds/emeralds.
    if not candidates:
        preferred = ("create", "mekanism", "powah", "productivebees", "ars_nouveau")
        for ns in preferred:
            for item, depth in catalog.get(ns, {}).items():
                candidates[item] = depth
                if len(candidates) >= 20:
                    break
            if len(candidates) >= 20:
                break

    if not candidates:
        raise RuntimeError(f"No modded reward candidates found for {stem}")

    max_depth = max(candidates.values()) or 1
    buckets: dict[int, list[str]] = {1: [], 2: [], 3: [], 4: []}
    for item, depth in sorted(candidates.items(), key=lambda kv: (kv[1], kv[0])):
        ratio = depth / max_depth
        tier = 1 if ratio <= 0.25 else 2 if ratio <= 0.50 else 3 if ratio <= 0.75 else 4
        buckets[tier].append(item)

    # Every tier needs choices. Borrow neighboring progression items where a small
    # mod chapter does not expose enough unique items of its own.
    all_items = [item for t in range(1, 5) for item in buckets[t]]
    for tier in range(1, 5):
        if len(buckets[tier]) < 3:
            ranked = sorted(
                all_items,
                key=lambda item: (
                    abs((candidates[item] / max_depth) - ((tier - 0.5) / 4.0)),
                    item,
                ),
            )
            for item in ranked:
                if item not in buckets[tier]:
                    buckets[tier].append(item)
                if len(buckets[tier]) >= min(6, len(all_items)):
                    break
    return buckets


def table_entries(stem: str, tier: int, buckets: dict[int, list[str]]) -> list[tuple[str, float]]:
    if stem == "powah":
        # T4 includes Spirited items as attainable high-end hits and Nitro as true
        # jackpots. Nitro weights stay tiny despite three draws.
        if tier == 1:
            items = buckets[1]
        elif tier == 2:
            items = buckets[1][-2:] + buckets[2]
        elif tier == 3:
            items = buckets[2][-3:] + buckets[3]
        else:
            items = buckets[3][-3:] + buckets[4]
        out = []
        for item in items:
            if item in POWAH_JACKPOTS:
                weight = POWAH_JACKPOTS[item]
            elif item.endswith("_spirited"):
                weight = 3.0
            elif item.endswith("_niotic"):
                weight = 7.0
            elif item.endswith("_blazing"):
                weight = 10.0
            else:
                weight = 14.0
            out.append((item, weight))
        return out

    # High-tier tables deliberately retain some prior-tier components as common
    # outcomes. The deepest items are the jackpot band rather than guaranteed loot.
    if tier == 1:
        items = buckets[1][:12]
    elif tier == 2:
        items = (buckets[1][-4:] + buckets[2])[:14]
    elif tier == 3:
        items = (buckets[2][-5:] + buckets[3])[:16]
    else:
        items = (buckets[2][-3:] + buckets[3][-6:] + buckets[4])[:18]

    out: list[tuple[str, float]] = []
    high = set(buckets[tier])
    jackpot = set(buckets[4][-max(1, math.ceil(len(buckets[4]) * 0.20)):]) if tier == 4 else set()
    for item in items:
        if item in jackpot:
            weight = 0.6
        elif item in high:
            weight = 5.0 if tier >= 3 else 9.0
        else:
            weight = 16.0
        out.append((item, weight))
    return out


def render_table(stem: str, title: str, tier: int, entries: list[tuple[str, float]], order: int) -> str:
    table_id = deterministic_long(f"amber-arcana-mod-tier:{stem}:{tier}")
    icon = entries[0][0]
    lines = [
        "{",
        f'\ticon: "{icon}"',
        f'\tid: "{table_id:016X}"',
        f"\tloot_size: {LOOT_SIZE[tier]}",
        f"\torder_index: {order}",
        "\trewards: [",
    ]
    for item, weight in entries:
        lines.append(f'\t\t{{ item: "{item}", weight: {weight:.2f}f }}')
    lines += [
        "\t]",
        f'\ttitle: "{title} — Tier {tier} Roll"',
        "\tuse_title: true",
        "}",
        "",
    ]
    return "\n".join(lines)


def retarget_depth_rolls(stem: str, title: str, text: str) -> tuple[str, int]:
    changed = 0
    for qstart, qend in reversed(quest_positions(text)):
        quest = text[qstart:qend]
        for rstart, rend in reversed(reward_objects(quest)):
            reward = quest[rstart:rend]
            m = re.search(r'title:\s*"Tier ([1-4]) Depth Roll"', reward)
            if not m:
                # Idempotent replay after the 0.1.9-32 source has already been saved.
                m = re.search(rf'title:\s*"{re.escape(title)} Tier ([1-4]) Roll"', reward)
            if not m:
                continue
            tier = int(m.group(1))
            table_id = deterministic_long(f"amber-arcana-mod-tier:{stem}:{tier}")
            reward = re.sub(r'(?m)^\s*table_id:\s*\d+L', f'\t\t\t\t\ttable_id: {table_id}L', reward, count=1)
            reward = re.sub(r'title:\s*"[^"]*Tier [1-4][^"]*Roll"', f'title: "{title} Tier {tier} Roll"', reward, count=1)
            quest = quest[:rstart] + reward + quest[rend:]
            changed += 1
        text = text[:qstart] + quest + text[qend:]
    return text, changed


def retheme_wheel(stem: str, title: str, tier_buckets: dict[int, list[str]]) -> int:
    path = TABLES / f"wheel_{stem}.snbt"
    if not path.exists():
        return 0
    text = path.read_text()
    entries = table_entries(stem, 4, tier_buckets)
    if not entries:
        return 0
    reward_lines = []
    for item, weight in entries:
        # Finale wheels are slightly more generous than ordinary T4 rolls, while
        # preserving explicit sub-1 Nitro weights from the Powah pool.
        wheel_weight = weight if stem == "powah" and item in POWAH_JACKPOTS else max(weight, 1.0)
        reward_lines.append(f'\t\t{{ item: "{item}", weight: {wheel_weight:.2f}f }}')
    text = replace_array_objects(text, "rewards", reward_lines)
    text = re.sub(r'(?m)^\s*loot_size:\s*\d+', "\tloot_size: 2", text, count=1)
    path.write_text(text)
    return len(entries)


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def sync_server() -> None:
    if SERVER_QUESTS.exists():
        shutil.rmtree(SERVER_QUESTS)
    shutil.copytree(CLIENT_QUESTS, SERVER_QUESTS)


def update_validator(stats: dict) -> None:
    if not VALIDATE_SH.exists():
        return
    text = VALIDATE_SH.read_text()
    text = text.replace('0.1.9-31', VERSION)

    # Current-source reward-table count changed from four global depth tables to
    # chapter/mod-specific four-tier sets.
    count = stats["total_reward_tables"]
    text = re.sub(
        r'test "\$\(find "\$qroot/reward_tables" -maxdepth 1 -name \'\*\.snbt\' -type f \| wc -l\)" = "\d+" \|\| \{ echo "Expected \d+ live reward tables" >&2; exit 1; \}',
        f'test "$(find "$qroot/reward_tables" -maxdepth 1 -name \'*.snbt\' -type f | wc -l)" = "{count}" || {{ echo "Expected {count} live reward tables" >&2; exit 1; }}',
        text,
    )
    text = re.sub(
        r'test "\$\(find "\$client_quests/reward_tables"[^\n]*depth_tier_[^\n]*\n',
        '',
        text,
    )
    text = re.sub(
        r'test "\$\(find "\$server_quests/reward_tables"[^\n]*depth_tier_[^\n]*\n',
        '',
        text,
    )
    text = re.sub(r'test "\$\(unzip -Z1 "\$quest_overlay"[^\n]*depth_tier_4\.snbt[^\n]*\n', '', text)

    marker = "# 0.1.9-32 mod-specific tier loot checks"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip() + "\n"
    text += f'''\n\n{marker}\njq -e '.mod_tier_loot_0_1_9_32.tier_tables == {stats["tier_tables"]} and .mod_tier_loot_0_1_9_32.depth_rewards_retargeted >= 100 and .mod_tier_loot_0_1_9_32.generic_depth_tables_remaining == 0 and .mod_tier_loot_0_1_9_32.powah_nitro_jackpots == 4 and .mod_tier_loot_0_1_9_32.client_server_quest_files_identical == true' "$validation" >/dev/null\ntest "$(find "$client_quests/reward_tables" -maxdepth 1 -name 'modroll_*_tier_*.snbt' -type f | wc -l)" = "{stats["tier_tables"]}" || {{ echo "Mod-specific tier table count mismatch" >&2; exit 1; }}\ntest "$(find "$client_quests/reward_tables" -maxdepth 1 -name 'depth_tier_*.snbt' -type f | wc -l)" = "0" || {{ echo "Legacy generic depth tables still present" >&2; exit 1; }}\nif rg -n 'minecraft:(diamond|emerald|emerald_block)' "$client_quests/reward_tables/modroll_"* >/dev/null; then echo "Generic diamond/emerald leaked into mod tier tables" >&2; exit 1; fi\ngrep -Fq 'item: "powah:thermo_generator_nitro", weight: 0.25f' "$client_quests/reward_tables/modroll_powah_tier_4.snbt" || {{ echo "Rare Nitro Thermo Generator jackpot missing" >&2; exit 1; }}\ngrep -Fq 'item: "powah:reactor_nitro", weight: 0.20f' "$client_quests/reward_tables/modroll_powah_tier_4.snbt" || {{ echo "Rare Nitro Reactor jackpot missing" >&2; exit 1; }}\ngrep -Fq 'loot_size: 3' "$client_quests/reward_tables/modroll_powah_tier_4.snbt" || {{ echo "High-tier multi-item roll missing" >&2; exit 1; }}\n'''
    VALIDATE_SH.write_text(text)


def update_docs(stats: dict) -> None:
    readme = README.read_text()
    readme = readme.replace("Amber-and-Arcana-0.1.9-31-", "Amber-and-Arcana-0.1.9-32-")
    readme = readme.replace("Download Client 0.1.9-31", "Download Client 0.1.9-32")
    readme = readme.replace("Download Crafty Server 0.1.9-31", "Download Crafty Server 0.1.9-32")
    readme = readme.replace("| Pack | 0.1.9-31 |", "| Pack | 0.1.9-32 |")
    marker = "## Quest runtime status — 2026-09-15\n"
    note = (
        f"\nRelease 0.1.9-32 replaces the four global diamond/emerald-style depth pools with {stats['tier_tables']} chapter/mod-specific tier tables. "
        f"{stats['depth_rewards_retargeted']} existing quest rolls now point at themed mod loot, and {stats['wheel_tables_rethemed']} finale wheels were rebuilt around modded items. "
        "Tier 2+ rolls can return multiple results; Tier 4 returns three results, but top machines remain low-weight jackpots. Powah's Nitro Thermo Generator, Nitro Reactor, Nitro Energy Cell, and Nitro Energizing Rod use sub-1 weights instead of becoming guaranteed endgame handouts.\n"
    )
    if marker in readme and "Release 0.1.9-32 replaces" not in readme:
        readme = readme.replace(marker, marker + note, 1)
    README.write_text(readme)

    changelog = CHANGELOG.read_text()
    if "## 0.1.9-32" not in changelog:
        entry = (
            "## 0.1.9-32 — Mod-specific tier loot rolls\n\n"
            "- Replace the four generic depth reward pools with four themed tiers per quest chapter/mod.\n"
            "- Remove diamonds, emeralds, and other generic vanilla filler from the new tier tables; rewards are selected from items belonging to the chapter's actual mods.\n"
            "- Make Tier 2 rolls award two results, Tier 3 two results, and Tier 4 three results.\n"
            "- Keep the strongest Tier 4 equipment rare instead of guaranteed; Powah Nitro generators/cells/reactors/rods are explicit sub-1-weight jackpots.\n"
            "- Re-theme chapter finale Wheel of Fortune tables around the same mod-specific progression pools.\n"
            "- Preserve quest/reward IDs and current player progression while changing only loot-table targets and contents.\n\n"
        )
        if changelog.startswith("# Changelog\n\n"):
            changelog = "# Changelog\n\n" + entry + changelog[len("# Changelog\n\n"):]
        else:
            changelog = entry + changelog
        CHANGELOG.write_text(changelog)


def main() -> None:
    chapter_paths = sorted(CHAPTERS.glob("*.snbt"))
    if len(chapter_paths) != 26:
        raise RuntimeError(f"Expected 26 chapters, found {len(chapter_paths)}")

    chapter_texts = {p.stem: p.read_text() for p in chapter_paths}
    catalog, chapter_namespaces = build_catalog(chapter_texts)

    # Remove the old universal vanilla-heavy tier pools and rebuild only the
    # generated mod-specific tables on each run.
    for path in TABLES.glob("depth_tier_*.snbt"):
        path.unlink()
    for path in TABLES.glob("modroll_*_tier_*.snbt"):
        path.unlink()

    tier_tables = 0
    retargeted = 0
    wheel_tables = 0
    wheel_entries = 0
    mod_entries = 0
    chapter_sets = 0

    for index, path in enumerate(chapter_paths):
        stem = path.stem
        text = chapter_texts[stem]
        title = chapter_title(text, stem)
        buckets = tiered_items_for_chapter(stem, text, catalog, chapter_namespaces)

        wrote_any = False
        for tier in range(1, 5):
            entries = table_entries(stem, tier, buckets)
            if len(entries) < 2:
                raise RuntimeError(f"{stem} tier {tier} has fewer than two modded choices")
            table_path = TABLES / f"modroll_{stem}_tier_{tier}.snbt"
            table_path.write_text(render_table(stem, title, tier, entries, 300 + index * 4 + tier))
            tier_tables += 1
            mod_entries += len(entries)
            wrote_any = True
        chapter_sets += int(wrote_any)

        text, changed = retarget_depth_rolls(stem, title, text)
        retargeted += changed
        path.write_text(text)
        chapter_texts[stem] = text

        wheel_count = retheme_wheel(stem, title, buckets)
        if wheel_count:
            wheel_tables += 1
            wheel_entries += wheel_count

    # There were 149 generated depth rewards in 0.1.9-30. Idempotent source
    # replays may report them again under their new titles, so the count remains.
    if retargeted < 100:
        raise RuntimeError(f"Expected broad retargeting of existing depth rolls, found {retargeted}")

    total_tables = len(list(TABLES.glob("*.snbt")))
    generic_remaining = len(list(TABLES.glob("depth_tier_*.snbt")))
    if generic_remaining:
        raise RuntimeError("Generic depth-tier tables remain after mod-specific conversion")

    powah_t4 = (TABLES / "modroll_powah_tier_4.snbt").read_text()
    for item in POWAH_JACKPOTS:
        if item not in powah_t4:
            raise RuntimeError(f"Powah Nitro jackpot missing: {item}")

    # New generated modroll tables must not drift back toward generic vanilla
    # currency. Historical fixed quest rewards are intentionally left alone.
    for table in TABLES.glob("modroll_*_tier_*.snbt"):
        t = table.read_text()
        if re.search(r'minecraft:(diamond|emerald|emerald_block)', t):
            raise RuntimeError(f"Generic vanilla currency found in {table.name}")

    def manifest_mutate(d):
        d["version"] = VERSION
        d["name"] = f"Amber & Arcana {VERSION}"
    update_json(MANIFEST, manifest_mutate)

    stats = {
        "chapter_roll_sets": chapter_sets,
        "tier_tables": tier_tables,
        "tier_loot_sizes": {str(k): v for k, v in LOOT_SIZE.items()},
        "depth_rewards_retargeted": retargeted,
        "wheel_tables_rethemed": wheel_tables,
        "wheel_modded_entries": wheel_entries,
        "modded_tier_entries": mod_entries,
        "generic_depth_tables_remaining": generic_remaining,
        "powah_nitro_jackpots": len(POWAH_JACKPOTS),
        "powah_nitro_max_weight": max(POWAH_JACKPOTS.values()),
        "total_reward_tables": total_tables,
        "historical_quest_reward_ids_preserved": True,
        "client_server_quest_files_identical": True,
    }

    def summary_mutate(d):
        d["pack_version"] = VERSION
        d["mod_tier_loot_0_1_9_32"] = stats
    update_json(SUMMARY, summary_mutate)

    def validation_mutate(d):
        d["pack_version"] = VERSION
        d["mod_tier_loot_0_1_9_32"] = stats
    update_json(VALIDATION, validation_mutate)

    sync_server()
    update_docs(stats)
    update_validator(stats)

    # Sync happens before metadata-only files are touched, so validate quest parity.
    for client_file in CLIENT_QUESTS.rglob("*"):
        if client_file.is_file():
            server_file = SERVER_QUESTS / client_file.relative_to(CLIENT_QUESTS)
            if not server_file.exists() or client_file.read_bytes() != server_file.read_bytes():
                raise RuntimeError(f"Client/server quest mismatch: {client_file.relative_to(CLIENT_QUESTS)}")

    print(
        f"Applied Amber & Arcana {VERSION}: {tier_tables} mod-specific tier tables, "
        f"{retargeted} quest rolls retargeted, {wheel_tables} wheels re-themed; "
        f"Powah Nitro jackpots max weight {stats['powah_nitro_max_weight']:.2f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
