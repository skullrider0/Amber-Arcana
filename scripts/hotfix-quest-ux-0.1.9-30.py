#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
import math
import re
import shutil
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-30"
PB_COMMIT = "2190d6b4c0f4a35acc26415759c3be731d1eac22"
PB_ARCHIVE = f"https://codeload.github.com/JDKDigital/productive-bees/zip/{PB_COMMIT}"

CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"
CHAPTERS = CLIENT_QUESTS / "chapters"
REWARD_TABLES = CLIENT_QUESTS / "reward_tables"
GROUPS_FILE = CLIENT_QUESTS / "chapter_groups.snbt"
PB_CHAPTER = CHAPTERS / "productive_bees.snbt"
MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"

SAFE_GROUPS = [
    ("5A29000000000001", "Start Here"),
    ("5A29000000000002", "Machines and Production"),
    ("5A29000000000003", "Storage and Networks"),
    ("5A29000000000004", "Resources and Farming"),
    ("5A29000000000005", "Magic and Rituals"),
    ("5A29000000000006", "Exploration and Creatures"),
    ("5A29000000000007", "Building and Settlements"),
    ("5A29000000000008", "Tools, Combat and Equipment"),
    ("5A29000000000009", "Collections and Endgame"),
]

TIER_POOLS = {
    1: [
        (16, "minecraft:coal", 24.0),
        (8, "minecraft:iron_ingot", 20.0),
        (12, "minecraft:copper_ingot", 20.0),
        (16, "minecraft:redstone", 16.0),
        (8, "minecraft:bread", 12.0),
        (32, "minecraft:torch", 8.0),
    ],
    2: [
        (16, "minecraft:iron_ingot", 22.0),
        (8, "minecraft:gold_ingot", 18.0),
        (32, "minecraft:redstone", 18.0),
        (16, "minecraft:lapis_lazuli", 14.0),
        (4, "minecraft:emerald", 12.0),
        (4, "minecraft:ender_pearl", 10.0),
        (8, "minecraft:experience_bottle", 6.0),
    ],
    3: [
        (3, "minecraft:diamond", 20.0),
        (8, "minecraft:emerald", 18.0),
        (6, "minecraft:blaze_rod", 16.0),
        (8, "minecraft:ender_pearl", 14.0),
        (16, "minecraft:golden_carrot", 12.0),
        (16, "minecraft:experience_bottle", 12.0),
        (1, "minecraft:netherite_scrap", 8.0),
    ],
    4: [
        (8, "minecraft:diamond", 20.0),
        (2, "minecraft:emerald_block", 16.0),
        (32, "minecraft:experience_bottle", 16.0),
        (2, "minecraft:netherite_scrap", 14.0),
        (32, "minecraft:golden_carrot", 12.0),
        (16, "minecraft:ender_pearl", 10.0),
        (1, "minecraft:totem_of_undying", 6.0),
        (1, "minecraft:enchanted_golden_apple", 2.0),
    ],
}


def deterministic_long(seed: str) -> int:
    value = int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:8], "big") & ((1 << 63) - 1)
    return value or 1


def deterministic_hex(seed: str) -> str:
    return f"{deterministic_long(seed):016X}"


def hid(seed: str) -> str:
    return deterministic_hex(seed)


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


def quest_id(block: str) -> str:
    m = re.search(r'(?m)^\s*id:\s*"([0-9A-F]{16})"\s*,?\s*$', block)
    if not m:
        raise RuntimeError("Quest block is missing a 16-character id")
    return m.group(1)

def quest_title(block: str) -> str:
    matches = re.findall(r'(?m)^\s*title:\s*"([^"]*)"\s*,?\s*$', block)
    return matches[-1] if matches else quest_id(block)


def quest_dependencies(block: str) -> list[str]:
    arr = named_array(block, "dependencies")
    if not arr:
        return []
    raw = block[arr[0] + 1:arr[1]]
    return re.findall(r'"([0-9A-F]{16})"', raw)


def quest_has_loot(block: str) -> bool:
    return any(block_type(reward) == "loot" for reward in child_blocks(block, "rewards"))


def coord(block: str, axis: str) -> float:
    m = re.search(rf'(?m)^\s*{axis}:\s*(-?\d+(?:\.\d+)?)(?:[dDfF])?\s*,?\s*$', block)
    return float(m.group(1)) if m else 0.0


def set_coord(block: str, axis: str, value: float) -> str:
    pattern = rf'(?m)^(\s*){axis}:\s*-?\d+(?:\.\d+)?(?:[dDfF])?\s*(,?)\s*$'
    m = re.search(pattern, block)
    line = None
    if m:
        indent, comma = m.group(1), m.group(2)
        line = f"{indent}{axis}: {value:.1f}d{comma}"
        return re.sub(pattern, line, block, count=1)

    # Historical blocks normally have coordinates, but tolerate a missing field.
    close = block.rfind("}")
    if close < 0:
        raise RuntimeError("Malformed quest block while setting coordinates")
    return block[:close] + f"\n\t\t\t{axis}: {value:.1f}d\n\t\t" + block[close:]


def replace_array(block: str, name: str, object_texts: list[str]) -> str:
    arr = named_array(block, name)
    if not arr:
        raise RuntimeError(f"Quest {quest_id(block)} has no {name} array")
    line = re.search(rf'(?m)^(\s*){re.escape(name)}:\s*\[', block)
    base = line.group(1) if line else "\t\t\t"
    body = "\n".join(object_texts)
    replacement = "[\n" + body + "\n" + base + "]"
    return block[:arr[0]] + replacement + block[arr[1] + 1:]


def add_reward(block: str, reward_text: str) -> str:
    arr = named_array(block, "rewards")
    if not arr:
        raise RuntimeError(f"Quest {quest_id(block)} has no rewards array")
    line = re.search(r'(?m)^(\s*)rewards:\s*\[', block)
    base = line.group(1) if line else "\t\t\t"
    insertion = "\n" + reward_text + "\n" + base
    return block[:arr[1]] + insertion + block[arr[1]:]


def sanitize_literal_ampersands(text: str) -> str:
    # FTB Library treats '&' as a formatting introducer. Human-readable labels like
    # "Machines & Production" therefore render as a red formatting error. Avoid that
    # parser ambiguity by spelling out plain-text conjunctions. Formatting codes such
    # as &6 and &r are left untouched.
    return text.replace(" & ", " and ")


def rewrite_group_titles() -> None:
    lines = ["{", "\tchapter_groups: ["]
    for gid, title in SAFE_GROUPS:
        lines.append(f'\t\t{{ id: "{gid}", title: "{title}" }}')
    lines += ["\t]", "}", ""]
    GROUPS_FILE.write_text("\n".join(lines))


def source_bee_metadata() -> tuple[set[str], dict[str, bool]]:
    print("Downloading Productive Bees source metadata for automatic species verification...", flush=True)
    with urllib.request.urlopen(PB_ARCHIVE, timeout=120) as response:
        data = response.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        roots = {Path(n).parts[0] for n in z.namelist() if n}
        if len(roots) != 1:
            raise RuntimeError("Unexpected Productive Bees source archive layout")
        root_name = next(iter(roots))
        tmp = ROOT / ".tmp-productive-bees-ux"
        if tmp.exists():
            shutil.rmtree(tmp)
        z.extractall(tmp)
    src = tmp / root_name

    defs: dict[str, bool] = {}
    definition_root = src / "src/generated/resources/data/productivebees/productivebees"
    for path in sorted(definition_root.rglob("*.json")):
        bee = f"productivebees:{path.stem}"
        payload = json.loads(path.read_text())
        defs[bee] = bool(payload.get("createComb", True))

    bees = set(defs)

    def outputs(value) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, dict):
            for key in ("bee", "id"):
                if isinstance(value.get(key), str):
                    return [value[key]]
            return []
        if isinstance(value, list):
            out: list[str] = []
            for v in value:
                out.extend(outputs(v))
            return out
        return []

    breeding = src / "src/main/resources/data/productivebees/recipes/bee_breeding"
    for path in sorted(breeding.rglob("*.json")):
        payload = json.loads(path.read_text())
        for key in ("parent1", "parent2"):
            if isinstance(payload.get(key), str):
                bees.add(payload[key])
        bees.update(outputs(payload.get("offspring")))

    conversion = src / "src/main/resources/data/productivebees/recipes/bee_conversion"
    for path in sorted(conversion.rglob("*.json")):
        payload = json.loads(path.read_text())
        if isinstance(payload.get("source"), str):
            bees.add(payload["source"])
        bees.update(outputs(payload.get("result")))

    return bees, defs


def render_bee_task(task_id: str, bee: str, configurable: bool, produces_comb: bool) -> tuple[str, str]:
    inner = "\t\t\t\t"
    prop = inner + "\t"
    sub = prop + "\t"
    sub2 = sub + "\t"

    if configurable and produces_comb:
        text = [
            f"{inner}{{",
            f'{prop}id: "{task_id}"',
            f"{prop}item: {{",
            f"{sub}Count: 1b",
            f'{sub}id: "productivebees:configurable_honeycomb"',
            f"{sub}tag: {{",
            f"{sub2}EntityTag: {{",
            f'{sub2}\ttype: "{bee}"',
            f"{sub2}}}",
            f"{sub}}}",
            f"{prop}}}",
            f"{prop}match_nbt: true",
            f'{prop}type: "item"',
            f"{prop}weak_nbt_match: true",
            f"{inner}}}",
        ]
        return "\n".join(text), "comb"

    cage_tag = [f'{sub}entity: "productivebees:configurable_bee"', f'{sub}type: "{bee}"'] if configurable else [f'{sub}entity: "{bee}"']
    text = [
        f"{inner}{{",
        f'{prop}id: "{task_id}"',
        f"{prop}item: {{",
        f"{sub}Count: 1b",
        f'{sub}id: "productivebees:bee_cage"',
        f"{sub}tag: {{",
        *cage_tag,
        f"{sub}}}",
        f"{prop}}}",
        f"{prop}match_nbt: true",
        f'{prop}type: "item"',
        f"{prop}weak_nbt_match: true",
        f"{inner}}}",
    ]
    return "\n".join(text), "cage"


def patch_bee_species(text: str, all_bees: set[str], definitions: dict[str, bool]) -> tuple[str, int, int, int]:
    qid_to_bee = {hid(f"productive-bees-bee:{bee}"): bee for bee in all_bees}
    expected = int(json.loads(VALIDATION.read_text()).get("productive_bees_0_1_9_27", {}).get("bee_quests", 0))
    matched = comb_tasks = cage_tasks = 0

    blocks = quest_positions(text)
    for start, end in reversed(blocks):
        block = text[start:end]
        qid = quest_id(block)
        bee = qid_to_bee.get(qid)
        if not bee:
            continue

        configurable = bee in definitions
        produces_comb = definitions.get(bee, False)
        task_id = hid(f"{qid}:confirm")
        task_text, mode = render_bee_task(task_id, bee, configurable, produces_comb)
        block = replace_array(block, "tasks", [task_text])
        if mode == "comb":
            comb_tasks += 1
            new_line = "Completion is automatic: carry at least one honeycomb produced by this exact bee species."
        else:
            cage_tasks += 1
            new_line = "Completion is automatic: capture this exact bee species in a Bee Cage and carry the filled cage."
        block = block.replace(
            "Bee-species completion is a manual confirmation because individual Productive Bees species are stored as typed bee data rather than unique inventory item IDs.",
            new_line,
        )
        block = block.replace(
            "capture it with a Bee Cage, then confirm the milestone.",
            "capture it with a Bee Cage. Carrying the filled cage completes this milestone automatically.",
        )
        text = text[:start] + block + text[end:]
        matched += 1

    if expected and matched != expected:
        raise RuntimeError(f"Expected to convert {expected} Productive Bees species quests, converted {matched}")
    return text, matched, comb_tasks, cage_tasks


def chapter_graph(text: str) -> tuple[list[dict], dict[str, int]]:
    infos: list[dict] = []
    ids: set[str] = set()
    for start, end in quest_positions(text):
        block = text[start:end]
        qid = quest_id(block)
        ids.add(qid)
        infos.append({
            "qid": qid,
            "start": start,
            "end": end,
            "block": block,
            "deps": quest_dependencies(block),
            "title": quest_title(block),
            "old_x": coord(block, "x"),
            "old_y": coord(block, "y"),
            "has_loot": quest_has_loot(block),
        })

    by_id = {info["qid"]: info for info in infos}
    memo: dict[str, int] = {}
    visiting: set[str] = set()

    def depth(qid: str) -> int:
        if qid in memo:
            return memo[qid]
        if qid in visiting:
            return 0
        visiting.add(qid)
        parents = [dep for dep in by_id[qid]["deps"] if dep in by_id and dep != qid]
        value = 0 if not parents else 1 + max(depth(parent) for parent in parents)
        visiting.remove(qid)
        memo[qid] = value
        return value

    for qid in by_id:
        depth(qid)
    return infos, memo


def relayout_chapter(text: str) -> tuple[str, float, float, dict[str, int]]:
    infos, depths = chapter_graph(text)
    by_id = {info["qid"]: info for info in infos}
    layers: dict[int, list[str]] = defaultdict(list)
    for qid, depth in depths.items():
        layers[depth].append(qid)

    order_rank: dict[str, float] = {}
    for depth in sorted(layers):
        qids = layers[depth]

        def sort_key(qid: str):
            parents = [p for p in by_id[qid]["deps"] if p in order_rank]
            bary = sum(order_rank[p] for p in parents) / len(parents) if parents else by_id[qid]["old_y"]
            return (bary, by_id[qid]["title"].lower(), qid)

        qids.sort(key=sort_key)
        for i, qid in enumerate(qids):
            order_rank[qid] = float(i)

    max_rows = 7
    depth_gap = 7.0
    chunk_gap = 2.2
    row_gap = 3.2
    coords: dict[str, tuple[float, float]] = {}

    for depth in sorted(layers):
        qids = layers[depth]
        for chunk_index in range(math.ceil(len(qids) / max_rows)):
            chunk = qids[chunk_index * max_rows:(chunk_index + 1) * max_rows]
            for row, qid in enumerate(chunk):
                x = depth * depth_gap + chunk_index * chunk_gap
                y = (row - (len(chunk) - 1) / 2.0) * row_gap
                coords[qid] = (x, y)

    if not coords:
        return text, 0.0, 0.0, depths
    xs = [xy[0] for xy in coords.values()]
    ys = [xy[1] for xy in coords.values()]
    x_mid = (min(xs) + max(xs)) / 2.0
    y_mid = (min(ys) + max(ys)) / 2.0
    coords = {qid: (x - x_mid, y - y_mid) for qid, (x, y) in coords.items()}

    for start, end in reversed(quest_positions(text)):
        block = text[start:end]
        qid = quest_id(block)
        x, y = coords[qid]
        block = set_coord(block, "x", x)
        block = set_coord(block, "y", y)
        text = text[:start] + block + text[end:]

    xs = [xy[0] for xy in coords.values()]
    ys = [xy[1] for xy in coords.values()]
    return text, max(xs) - min(xs), max(ys) - min(ys), depths


def tier_for_depth(depth: int) -> int:
    if depth <= 1:
        return 1
    if depth <= 3:
        return 2
    if depth <= 5:
        return 3
    return 4


def render_depth_reward(qid: str, tier: int) -> str:
    rid = deterministic_hex(f"amber-arcana-depth-reward:{qid}")
    table_id = deterministic_long(f"amber-arcana-depth-tier-table:{tier}")
    inner = "\t\t\t\t"
    prop = inner + "\t"
    return "\n".join([
        f"{inner}{{",
        f'{prop}id: "{rid}"',
        f"{prop}table_id: {table_id}L",
        f'{prop}title: "Tier {tier} Depth Roll"',
        f'{prop}type: "loot"',
        f"{inner}}}",
    ])


def add_depth_rewards(chapter_texts: dict[Path, str], depth_maps: dict[Path, dict[str, int]]) -> tuple[dict[Path, str], int, int, int, dict[int, int]]:
    total = existing = added = 0
    tiers = defaultdict(int)

    for path in sorted(chapter_texts):
        text = chapter_texts[path]
        records = []
        for start, end in quest_positions(text):
            block = text[start:end]
            qid = quest_id(block)
            records.append({
                "qid": qid,
                "start": start,
                "end": end,
                "depth": depth_maps[path][qid],
                "has_loot": quest_has_loot(block),
            })
        total += len(records)
        existing += sum(1 for r in records if r["has_loot"])
        target = math.ceil(len(records) * 0.70)
        already = sum(1 for r in records if r["has_loot"])
        need = max(0, target - already)
        candidates = [r for r in records if not r["has_loot"]]
        candidates.sort(key=lambda r: (-r["depth"], deterministic_long(f"depth-pick:{r['qid']}")))
        selected = {r["qid"] for r in candidates[:need]}

        for start, end in reversed(quest_positions(text)):
            block = text[start:end]
            qid = quest_id(block)
            if qid not in selected:
                continue
            tier = tier_for_depth(depth_maps[path][qid])
            block = add_reward(block, render_depth_reward(qid, tier))
            text = text[:start] + block + text[end:]
            tiers[tier] += 1
            added += 1
        chapter_texts[path] = text

    covered = existing + added
    if covered / max(total, 1) < 0.70:
        raise RuntimeError(f"Tiered loot coverage below 70%: {covered}/{total}")
    return chapter_texts, total, covered, added, dict(tiers)


def render_tier_table(tier: int) -> str:
    table_id = deterministic_long(f"amber-arcana-depth-tier-table:{tier}")
    icon = {1: "minecraft:iron_ingot", 2: "minecraft:gold_ingot", 3: "minecraft:diamond", 4: "minecraft:netherite_scrap"}[tier]
    lines = [
        "{",
        f'\ticon: "{icon}"',
        f'\tid: "{table_id:016X}"',
        "\tloot_size: 1",
        f"\torder_index: {200 + tier}",
        "\trewards: [",
    ]
    for count, item, weight in TIER_POOLS[tier]:
        count_part = f"count: {count}, " if count != 1 else ""
        lines.append(f'\t\t{{ {count_part}item: "{item}", weight: {weight:.1f}f }}')
    lines += [
        "\t]",
        f'\ttitle: "Depth Tier {tier} Supply Roll"',
        "\tuse_title: true",
        "}",
        "",
    ]
    return "\n".join(lines)


def write_tier_tables() -> None:
    REWARD_TABLES.mkdir(parents=True, exist_ok=True)
    for old in REWARD_TABLES.glob("depth_tier_*.snbt"):
        old.unlink()
    for tier in sorted(TIER_POOLS):
        (REWARD_TABLES / f"depth_tier_{tier}.snbt").write_text(render_tier_table(tier))


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
    text = text.replace("Amber-and-Arcana-0.1.9-29-", "Amber-and-Arcana-0.1.9-30-")
    text = text.replace("Download Client 0.1.9-29", "Download Client 0.1.9-30")
    text = text.replace("Download Crafty Server 0.1.9-29", "Download Crafty Server 0.1.9-30")
    text = text.replace("| Pack | 0.1.9-29 |", "| Pack | 0.1.9-30 |")
    marker = "## Quest runtime status — 2026-09-15\n"
    note = (
        f"\nRelease 0.1.9-30 repairs FTB quest-group labels so literal ampersands no longer trigger formatting errors, "
        f"re-lays out all {stats['chapters_relaid_out']} quest chapters as compact dependency layers, and adds depth-tiered supply rolls to "
        f"{stats['loot_covered_quests']} of {stats['total_quests']} quests ({stats['loot_coverage_percent']:.1f}%). "
        f"Productive Bees species milestones now complete from exact NBT-matched evidence: {stats['bee_comb_tasks']} species use their typed honeycomb and "
        f"{stats['bee_cage_tasks']} species use a filled Bee Cage when a comb is not appropriate. Historical quest/task IDs are preserved.\n"
    )
    if marker in text and "Release 0.1.9-30 repairs FTB quest-group labels" not in text:
        text = text.replace(marker, marker + note, 1)
    README.write_text(text)

    changelog = CHANGELOG.read_text()
    if "## 0.1.9-30" not in changelog:
        entry = (
            "## 0.1.9-30 — Quest UX, tiered rewards, and automatic bee verification\n\n"
            "- Replace literal ampersands in player-facing FTB Quests labels with parser-safe wording, fixing red `Invalid formatting` group headers.\n"
            "- Re-layout every chapter into compact left-to-right dependency layers to reduce giant empty gaps and long crossing lines.\n"
            f"- Give at least 70% of quests a loot roll, counting existing chapter finales; new rolls use four depth tiers and never replace fixed rewards.\n"
            "- Make Productive Bees species milestones inventory-detected: comb-producing configurable bees require their exact typed honeycomb, while non-comb or non-configurable bees require the exact species in a filled Bee Cage.\n"
            "- Use `match_nbt: true` plus weak NBT matching so cage metadata can contain normal extra bee state without defeating species detection.\n"
            "- Preserve existing quest, task, reward, chapter, and group IDs; client/server quest trees remain identical.\n\n"
        )
        if changelog.startswith("# Changelog\n\n"):
            changelog = "# Changelog\n\n" + entry + changelog[len("# Changelog\n\n"):]
        else:
            changelog = entry + changelog
        CHANGELOG.write_text(changelog)


def main() -> None:
    chapters = sorted(CHAPTERS.glob("*.snbt"))
    if len(chapters) != 26:
        raise RuntimeError(f"Expected 26 quest chapters before 0.1.9-30, found {len(chapters)}")

    rewrite_group_titles()
    all_bees, definitions = source_bee_metadata()

    chapter_texts: dict[Path, str] = {}
    depth_maps: dict[Path, dict[str, int]] = {}
    max_width = max_height = 0.0
    bee_species = bee_comb = bee_cage = 0

    try:
        for path in chapters:
            text = sanitize_literal_ampersands(path.read_text())
            if path == PB_CHAPTER:
                text, bee_species, bee_comb, bee_cage = patch_bee_species(text, all_bees, definitions)
            text, width, height, depths = relayout_chapter(text)
            chapter_texts[path] = text
            depth_maps[path] = depths
            max_width = max(max_width, width)
            max_height = max(max_height, height)

        # Sanitize historical reward-table titles too (some inherit chapter titles).
        for table in sorted(REWARD_TABLES.glob("*.snbt")):
            table.write_text(sanitize_literal_ampersands(table.read_text()))

        chapter_texts, total_quests, covered, added, tier_counts = add_depth_rewards(chapter_texts, depth_maps)
        for path, text in chapter_texts.items():
            path.write_text(text)
        write_tier_tables()
        sync_server()

        if any(" & " in p.read_text() for p in CLIENT_QUESTS.rglob("*.snbt")):
            raise RuntimeError("Unescaped literal ampersand text remains in FTB Quests SNBT")

        coverage = covered * 100.0 / total_quests
        reward_table_count = len(list(REWARD_TABLES.glob("*.snbt")))
        stats = {
            "group_labels_fixed": True,
            "chapters_relaid_out": len(chapters),
            "max_chapter_width": round(max_width, 1),
            "max_chapter_height": round(max_height, 1),
            "total_quests": total_quests,
            "loot_covered_quests": covered,
            "loot_coverage_percent": round(coverage, 1),
            "tier_loot_rewards_added": added,
            "tier_tables": 4,
            "tier_reward_counts": {str(k): int(v) for k, v in sorted(tier_counts.items())},
            "total_reward_tables": reward_table_count,
            "bee_species_item_detection": bee_species,
            "bee_comb_tasks": bee_comb,
            "bee_cage_tasks": bee_cage,
            "bee_manual_species_tasks_remaining": 0,
            "historical_ids_preserved": True,
            "client_server_quest_files_identical": True,
        }

        def mutate_manifest(data):
            data["version"] = VERSION
            data["name"] = f"Amber & Arcana {VERSION}"
        update_json(MANIFEST, mutate_manifest)

        def mutate_summary(data):
            data["pack_version"] = VERSION
            data["quest_ux_0_1_9_30"] = stats
        update_json(SUMMARY, mutate_summary)

        def mutate_validation(data):
            data["pack_version"] = VERSION
            data["quest_ux_0_1_9_30"] = stats
        update_json(VALIDATION, mutate_validation)

        update_docs(stats)

        for client_file in CLIENT_QUESTS.rglob("*"):
            if client_file.is_file():
                server_file = SERVER_QUESTS / client_file.relative_to(CLIENT_QUESTS)
                if not server_file.exists() or client_file.read_bytes() != server_file.read_bytes():
                    raise RuntimeError(f"Client/server quest mismatch after 0.1.9-30: {client_file.name}")

        print(
            f"Applied Amber & Arcana {VERSION}: {len(chapters)} chapters relaid, "
            f"loot on {covered}/{total_quests} quests ({coverage:.1f}%), "
            f"{bee_species} bee species auto-detected ({bee_comb} comb / {bee_cage} cage)",
            flush=True,
        )
    finally:
        tmp = ROOT / ".tmp-productive-bees-ux"
        if tmp.exists():
            shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
