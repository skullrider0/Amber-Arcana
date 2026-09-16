#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-34"
CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"
CHAPTERS = CLIENT_QUESTS / "chapters"
TABLES = CLIENT_QUESTS / "reward_tables"
MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
VALIDATE_SH = ROOT / "scripts/validate.sh"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"

# Productive Bees and Create Engineering already have deep custom progression.
# 0.1.9-34 focuses on the compact chapters where only a handful of sequential
# quests otherwise make the reward curve feel flat.
SHORT_CHAIN_MAX_QUESTS = 10
EXCLUDED = {"productive_bees", "create_engineering"}
LOOT_SIZE = {1: 1, 2: 2, 3: 3, 4: 4}
FINALE_LOOT_SIZE = 5
TARGET_ENTRIES = {1: 12, 2: 16, 3: 20, 4: 24}

helper_path = ROOT / "scripts/hotfix-mod-tier-loot-0.1.9-32.py"
spec = importlib.util.spec_from_file_location("aa_loot32", helper_path)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load 0.1.9-32 reward helpers")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def chapter_title(text: str, stem: str) -> str:
    return h.chapter_title(text, stem).replace(" & ", " and ")


def table_identity(path: Path) -> tuple[str, int]:
    text = path.read_text()
    mid = re.search(r'(?m)^\s*id:\s*"([0-9A-F]{16})"', text)
    mord = re.search(r'(?m)^\s*order_index:\s*(-?\d+)', text)
    if not mid or not mord:
        raise RuntimeError(f"Could not preserve reward-table identity for {path.name}")
    return mid.group(1), int(mord.group(1))


def parse_entries(path: Path) -> list[tuple[int, str, float]]:
    text = path.read_text()
    out: list[tuple[int, str, float]] = []
    for m in re.finditer(
        r'\{\s*(?:count:\s*(\d+)\s*,\s*)?item:\s*"([a-z0-9_.-]+:[a-z0-9_./-]+)"\s*,\s*weight:\s*([0-9.]+)f\s*\}',
        text,
    ):
        count = int(m.group(1) or 1)
        item = m.group(2)
        weight = float(m.group(3))
        if h.is_modded(item):
            out.append((count, item, weight))
    return out


def component_like(item: str) -> bool:
    p = item.split(":", 1)[1]
    tokens = (
        "ingot", "nugget", "dust", "shard", "crystal", "gem", "alloy", "plate",
        "gear", "rod", "wire", "cable", "coil", "circuit", "processor", "component",
        "essence", "rune", "fiber", "thread", "sheet", "mechanism", "fragment", "chip",
        "comb", "wax", "material", "part", "core", "pellet", "clump", "dirty_",
    )
    return any(t in p for t in tokens)


def bulky_count(item: str, tier: int, variant: int) -> int:
    if not component_like(item):
        return 1
    base = {1: 2, 2: 4, 3: 6, 4: 8}[tier]
    return min(16, base * (variant + 1))


def dedupe_items(entries: list[tuple[int, str, float]]) -> list[str]:
    seen = set()
    out = []
    for _count, item, _weight in entries:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def expand_pool(stem: str, tier: int, source_by_tier: dict[int, list[tuple[int, str, float]]]) -> list[tuple[int, str, float]]:
    current = dedupe_items(source_by_tier[tier])
    prev = dedupe_items(source_by_tier[max(1, tier - 1)])
    nxt = dedupe_items(source_by_tier[min(4, tier + 1)])
    deepest = dedupe_items(source_by_tier[4])

    # Keep the chapter namespace/theme pure. The source tables were already
    # validated in 0.1.9-32, so we only remix known-good modded item IDs here.
    ordered: list[tuple[str, str]] = []
    seen = set()
    for band, items in (("prev", prev), ("current", current), ("preview", nxt if tier >= 2 else []), ("deep", deepest if tier >= 3 else [])):
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            ordered.append((band, item))

    if not ordered:
        raise RuntimeError(f"No modded reward items available for short chapter {stem} tier {tier}")

    target = TARGET_ENTRIES[tier]
    out: list[tuple[int, str, float]] = []

    # First pass: one outcome per known item, with progression-sensitive weights.
    for band, item in ordered:
        if band == "prev":
            weight = 14.0 if tier >= 3 else 16.0
        elif band == "current":
            weight = 9.0 if tier <= 2 else 7.0
        elif band == "preview":
            weight = 2.0 if tier == 2 else 1.25
        else:
            weight = 0.55
        # Preserve already-known sub-1 jackpot behavior from T4 when possible.
        original = [w for _c, i, w in source_by_tier.get(4, []) if i == item]
        if tier == 4 and original and min(original) < 1.0:
            weight = min(original)
        out.append((1, item, weight))

    # Second pass: bulk/component variants make the weighted pool feel richer
    # without inventing registry IDs. Machines/equipment stay single-count.
    variant = 0
    idx = 0
    while len(out) < target:
        band, item = ordered[idx % len(ordered)]
        count = bulky_count(item, tier, variant % 2)
        if count == 1:
            # Single machines can still appear as a separate lower-weight outcome;
            # this makes strong machines rarer than common components.
            weight = 4.5 if band in {"prev", "current"} else 0.75
        else:
            weight = max(2.0, 11.0 - variant * 1.5)
        candidate = (count, item, weight)
        if candidate not in out:
            out.append(candidate)
        idx += 1
        if idx % len(ordered) == 0:
            variant += 1
        if idx > target * 10:
            break

    return out[:target]


def render_table(table_id: str, order: int, title: str, tier: int, entries: list[tuple[int, str, float]]) -> str:
    lines = [
        "{",
        f'\ticon: "{entries[0][1]}"',
        f'\tid: "{table_id}"',
        f"\tloot_size: {LOOT_SIZE[tier]}",
        f"\torder_index: {order}",
        "\trewards: [",
    ]
    for count, item, weight in entries:
        cp = f"count: {count}, " if count != 1 else ""
        lines.append(f'\t\t{{ {cp}item: "{item}", weight: {weight:.2f}f }}')
    lines += [
        "\t]",
        f'\ttitle: "{title} — Tier {tier} Roll"',
        "\tuse_title: true",
        "}",
        "",
    ]
    return "\n".join(lines)


def render_wheel(table_id: str, order: int, title: str, pools: dict[int, list[tuple[int, str, float]]]) -> tuple[str, int]:
    # Finale favors T3/T4 outcomes with five draws. Deep single-machine outcomes
    # retain small weights, while component bundles remain the common consolation.
    candidates = pools[3] + pools[4]
    unique: list[tuple[int, str, float]] = []
    seen = set()
    for count, item, weight in candidates:
        key = (count, item)
        if key in seen:
            continue
        seen.add(key)
        if weight < 1.0:
            final_weight = min(weight, 0.45)
        elif component_like(item):
            final_weight = min(9.0, max(3.0, weight))
        else:
            final_weight = min(6.0, max(1.0, weight * 0.75))
        unique.append((count, item, final_weight))
        if len(unique) >= 24:
            break
    if len(unique) < 12:
        raise RuntimeError(f"Finale pool for {title} is unexpectedly thin")

    lines = [
        "{",
        f'\ticon: "{unique[0][1]}"',
        f'\tid: "{table_id}"',
        f"\tloot_size: {FINALE_LOOT_SIZE}",
        f"\torder_index: {order}",
        "\trewards: [",
    ]
    for count, item, weight in unique:
        cp = f"count: {count}, " if count != 1 else ""
        lines.append(f'\t\t{{ {cp}item: "{item}", weight: {weight:.2f}f }}')
    lines += [
        "\t]",
        f'\ttitle: "Wheel of Fortune — {title}"',
        "\tuse_title: true",
        "}",
        "",
    ]
    return "\n".join(lines), len(unique)


def reward_tier(depth: int, max_depth: int, index: int, total: int) -> int:
    if total <= 1:
        return 4
    if depth == max_depth and index == total - 1:
        return 4
    ratio = max(depth / max(1, max_depth), index / max(1, total - 1))
    if ratio < 0.25:
        return 1
    if ratio < 0.55:
        return 2
    if ratio < 0.82:
        return 3
    return 4


def inject_all_short_quest_rolls(stem: str, title: str, text: str, table_ids: dict[int, str]) -> tuple[str, int]:
    positions = h.quest_positions(text)
    depths = h.compute_depths(text)
    max_depth = max(depths.values()) if depths else 0
    covered = 0

    for index, (qs, qe) in reversed(list(enumerate(positions))):
        block = text[qs:qe]
        qid = h.quest_id(block)
        tier = reward_tier(depths.get(qid, 0), max_depth, index, len(positions))
        decimal_table = int(table_ids[tier], 16)

        # Remove any existing mod-tier roll for this chapter so each quest ends up
        # with exactly one depth-appropriate roll. Finale Wheel rewards are separate.
        rewards = h.reward_objects(block)
        removals = []
        for rs, re_ in rewards:
            obj = block[rs:re_]
            if re.search(r'title:\s*"[^"\n]+ Tier [1-4] Roll"', obj) and 'type: "loot"' in obj:
                removals.append((rs, re_))
        for rs, re_ in reversed(removals):
            block = block[:rs] + block[re_:]

        arr = h.named_array(block, "rewards")
        if not arr:
            raise RuntimeError(f"Quest {qid} in {stem} has no rewards array")
        rid = h.deterministic_long(f"amber-arcana-short34:{stem}:{qid}")
        reward = (
            "\n\t\t\t\t{\n"
            f'\t\t\t\t\tid: "{rid:016X}"\n'
            f"\t\t\t\t\ttable_id: {decimal_table}L\n"
            f'\t\t\t\t\ttitle: "{title} Tier {tier} Roll"\n'
            '\t\t\t\t\ttype: "loot"\n'
            "\t\t\t\t}"
        )
        # Avoid the trailing quote introduced for readable construction above.
        reward = reward[:-1]
        insert_at = arr[1]
        existing = block[arr[0] + 1:arr[1]].strip()
        prefix = "" if not existing else "\n"
        block = block[:insert_at] + prefix + reward + "\n\t\t\t" + block[insert_at:]
        text = text[:qs] + block + text[qe:]
        covered += 1

    return text, covered


def main() -> None:
    short = []
    total_short_quests = 0
    all_covered = 0
    expanded_entries = 0
    finale_entries = 0

    for path in sorted(CHAPTERS.glob("*.snbt")):
        stem = path.stem
        if stem in EXCLUDED:
            continue
        text = path.read_text()
        qcount = len(h.quest_positions(text))
        if not (1 <= qcount <= SHORT_CHAIN_MAX_QUESTS):
            continue
        title = chapter_title(text, stem)

        source_by_tier: dict[int, list[tuple[int, str, float]]] = {}
        ids: dict[int, str] = {}
        expanded: dict[int, list[tuple[int, str, float]]] = {}
        for tier in range(1, 5):
            table = TABLES / f"modroll_{stem}_tier_{tier}.snbt"
            if not table.exists():
                raise RuntimeError(f"Short chapter {stem} is missing {table.name}")
            source_by_tier[tier] = parse_entries(table)
            ids[tier], order = table_identity(table)
            expanded[tier] = expand_pool(stem, tier, source_by_tier)
            table.write_text(render_table(ids[tier], order, title, tier, expanded[tier]))
            expanded_entries += len(expanded[tier])

        wheel = TABLES / f"wheel_{stem}.snbt"
        if not wheel.exists():
            raise RuntimeError(f"Short chapter {stem} is missing finale wheel")
        wid, worder = table_identity(wheel)
        wheel_text, wcount = render_wheel(wid, worder, title, expanded)
        wheel.write_text(wheel_text)
        finale_entries += wcount

        new_text, covered = inject_all_short_quest_rolls(stem, title, text, ids)
        path.write_text(new_text)
        short.append({"chapter": stem, "title": title, "quests": qcount})
        total_short_quests += qcount
        all_covered += covered

    if not short:
        raise RuntimeError("No short progression chapters were found")
    if all_covered != total_short_quests:
        raise RuntimeError("Not every short-chain quest received a tier roll")

    # Sync all quest changes server-side.
    if SERVER_QUESTS.exists():
        shutil.rmtree(SERVER_QUESTS)
    shutil.copytree(CLIENT_QUESTS, SERVER_QUESTS)

    def manifest_mut(d):
        d["version"] = VERSION
        d["name"] = re.sub(r"0\.1\.9-\d+", VERSION, d.get("name", "Amber & Arcana"))
    update_json(MANIFEST, manifest_mut)

    metrics = {
        "short_chain_max_quests": SHORT_CHAIN_MAX_QUESTS,
        "short_chapters_rebalanced": len(short),
        "short_quests_rebalanced": total_short_quests,
        "short_quest_roll_coverage_percent": 100.0,
        "tier_weighted_entries_generated": expanded_entries,
        "finale_weighted_entries_generated": finale_entries,
        "tier_loot_sizes": {str(k): v for k, v in LOOT_SIZE.items()},
        "finale_loot_size": FINALE_LOOT_SIZE,
        "generic_vanilla_items_added": 0,
        "historical_quest_ids_preserved": True,
        "historical_reward_table_ids_preserved": True,
        "client_server_quest_files_identical": True,
        "chapters": short,
    }

    update_json(VALIDATION, lambda d: (d.__setitem__("pack_version", VERSION), d.__setitem__("short_chain_rewards_0_1_9_34", metrics)))
    update_json(SUMMARY, lambda d: (d.__setitem__("pack_version", VERSION), d.__setitem__("short_chain_rewards_0_1_9_34", metrics)))

    vt = VALIDATE_SH.read_text()
    vt = vt.replace('.version == "0.1.9-33"', '.version == "0.1.9-34"')
    vt = vt.replace('.pack_version == "0.1.9-33"', '.pack_version == "0.1.9-34"')
    vt = vt.replace('Amber & Arcana 0.1.9-33 static validation passed', 'Amber & Arcana 0.1.9-34 static validation passed')
    marker = "# 0.1.9-34 short-chain reward progression checks"
    if marker not in vt:
        vt += f'''\n\n{marker}\njq -e '.short_chain_rewards_0_1_9_34.short_chapters_rebalanced >= 10 and .short_chain_rewards_0_1_9_34.short_quests_rebalanced >= 30 and .short_chain_rewards_0_1_9_34.short_quest_roll_coverage_percent == 100 and .short_chain_rewards_0_1_9_34.generic_vanilla_items_added == 0 and .short_chain_rewards_0_1_9_34.client_server_quest_files_identical == true' "$validation" >/dev/null\nfor table in "$client_quests"/reward_tables/modroll_*_tier_4.snbt; do\n  stem="$(basename "$table")"\n  if [ "$stem" = "modroll_productive_bees_tier_4.snbt" ] || [ "$stem" = "modroll_create_engineering_tier_4.snbt" ]; then continue; fi\n  grep -Eq 'loot_size: [34]' "$table" || {{ echo "Expanded T4 table has too few draws: $stem" >&2; exit 1; }}\ndone\n'''
    VALIDATE_SH.write_text(vt)

    rt = README.read_text()
    if "0.1.9-34 short-chain reward progression" not in rt:
        rt += f'''\n\n## 0.1.9-34 short-chain reward progression\n\nCompact quest chapters now use a compressed but much richer reward curve. Every quest in chapters with at most {SHORT_CHAIN_MAX_QUESTS} quests receives a mod-specific tier roll, tiers 3/4 use 3/4 draws, and chapter finales use five draws. Reward tables are expanded with weighted quantity variants and rare deep-progression outcomes using only modded item IDs already validated by the preceding reward pass. Productive Bees and Create Engineering retain their dedicated deeper reward systems.\n'''
        README.write_text(rt)

    ct = CHANGELOG.read_text()
    heading = "## 0.1.9-34 — Richer rewards for short progression chapters"
    if heading not in ct:
        body = f'''# Changelog\n\n{heading}\n\n- Rebalance every compact chapter with at most {SHORT_CHAIN_MAX_QUESTS} quests.\n- Give 100% of quests in those short chains a depth-appropriate mod-specific loot roll.\n- Expand tier pools to 12/16/20/24 weighted outcomes with 1/2/3/4 draws.\n- Expand short-chapter finales to five draws with deeper items kept in a low-weight jackpot band.\n- Add no generic vanilla filler and preserve existing quest IDs and reward-table IDs.\n\n'''
        CHANGELOG.write_text(body + ct.removeprefix("# Changelog\n\n"))

    print(f"Prepared Amber & Arcana {VERSION}: {len(short)} short chapters / {total_short_quests} quests rebalanced")


if __name__ == "__main__":
    main()
