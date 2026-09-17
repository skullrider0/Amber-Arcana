#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-45"
CLIENT = ROOT / "client/overrides/config/ftbquests/quests"
SERVER = ROOT / "server/config/ftbquests/quests"
CHAPTERS = CLIENT / "chapters"
TABLES = CLIENT / "reward_tables"
MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
MARKER = "AA35 deep progression milestone"

# Reward namespaces are explicit on purpose. A chapter is never allowed to fall
# back to an unrelated technology mod merely because its own pool is small.
THEMES: dict[str, set[str]] = {
    "ae2": {"ae2", "ae2things", "appmek", "appliedmekanistics", "megacells", "ae2wtlib", "ae2buddycards"},
    "alex_caves": {"alexscaves", "alexscaves_torpedoes", "alexs_caves_spellbooks"},
    "alex_utilities": {"alexsmobs", "alexscaves", "cloudstorage"},
    "alex_wildlife": {"alexsmobs", "untamedwilds", "crittersandcompanions"},
    "aquarium": {"aquaculture", "aquaculturedelight", "aquaculturebuddycards"},
    "ars_nouveau": {"ars_nouveau", "ars_creo", "ars_elemental", "ars_n_spells", "arseng"},
    "buddycards": {"buddycards", "ae2buddycards", "aquaculturebuddycards"},
    "butchery": {"butchery", "butchercraft", "farmersdelight", "bloodmagic", "vampirism", "hexerei"},
    "create_city": {"create"},
    "create_engineering": {"create"},
    "create_workshops": {"create"},
    "dimensions": {"blue_skies", "the_bumblezone", "bumblezone"},
    "dinosaur_laboratory": {"fossil"},
    "draconic_evolution": {"draconicevolution", "brandonscore"},
    "ender_io": {"enderio"},
    "endgame": {"draconicevolution", "mekanism", "powah", "ae2", "refinedstorage", "productivebees", "tconstruct", "irons_spellbooks", "ars_nouveau"},
    "firearms": {"create", "scorchedguns", "irons_spellbooks", "irons_spellbooks_addons"},
    "food_factory": {"farmersdelight", "sliceanddice", "create", "butchery", "butchercraft"},
    "getting_started": {"minecraft", "sophisticatedbackpacks", "waystones"},
    "hostile_neural_networks": {"hostilenetworks", "hostile_neural_networks"},
    "irons_spells": {"irons_spellbooks", "irons_spells"},
    "mekanism": {"mekanism", "mekanismgenerators", "mekanismtools", "mekanismadditions"},
    "powah": {"powah"},
    "productive_bees": {"productivebees", "justdirethings", "direthings"},
    "refined_storage": {"refinedstorage", "refinedstorageaddons", "rsrequestify", "refinedpolymorph"},
    "ritual_magic": {"bloodmagic", "hexerei", "vampirism", "ars_nouveau"},
    "settlement": {"minecolonies", "structurize", "domum_ornamentum"},
    "tinkers": {"tconstruct", "mantle"},
}

# General non-mod rewards are intentionally limited to useful supplies. They are
# only used when a chapter has too few correctly themed entries after filtering.
GENERAL_FALLBACK = [
    "minecraft:iron_ingot",
    "minecraft:gold_ingot",
    "minecraft:redstone",
    "minecraft:lapis_lazuli",
    "minecraft:ender_pearl",
    "minecraft:experience_bottle",
]
STARTER_FALLBACK = [
    "minecraft:iron_ingot",
    "minecraft:bread",
    "minecraft:torch",
    "minecraft:ender_pearl",
]


def find_balanced(text: str, start: int, opench: str, closech: str) -> int:
    depth = 0
    quoted = False
    escaped = False
    for i in range(start, len(text)):
        c = text[i]
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
            continue
        if c == '"':
            quoted = True
        elif c == opench:
            depth += 1
        elif c == closech:
            depth -= 1
            if depth == 0:
                return i
    raise RuntimeError(f"Unbalanced {opench}{closech}")


def named_array(text: str, name: str) -> tuple[int, int] | None:
    m = re.search(rf"(?m)^\s*{re.escape(name)}:\s*\[", text)
    if not m:
        return None
    start = text.find("[", m.start())
    return start, find_balanced(text, start, "[", "]")


def top_objects(text: str, start: int, end: int) -> list[str]:
    out: list[str] = []
    depth = 0
    quoted = False
    escaped = False
    obj_start: int | None = None
    for i in range(start + 1, end):
        c = text[i]
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
            continue
        if c == '"':
            quoted = True
        elif c == "{":
            if depth == 0:
                obj_start = i
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and obj_start is not None:
                out.append(text[obj_start:i + 1])
                obj_start = None
    return out


def quest_blocks(text: str) -> list[str]:
    arr = named_array(text, "quests")
    return top_objects(text, *arr) if arr else []


def qid(block: str) -> str:
    m = re.search(r'(?m)^\s*id:\s*"([0-9A-Fa-f]{16})"\s*,?', block)
    if not m:
        raise RuntimeError("Quest missing id")
    return m.group(1).upper()


def deps(block: str) -> list[str]:
    arr = named_array(block, "dependencies")
    if not arr:
        return []
    return [x.upper() for x in re.findall(r'"([0-9A-Fa-f]{16})"', block[arr[0] + 1:arr[1]])]


def set_deps(block: str, values: list[str]) -> str:
    values = list(dict.fromkeys(values))
    rendered = "[" + ", ".join(json.dumps(x) for x in values) + "]"
    arr = named_array(block, "dependencies")
    if arr:
        line_start = block.rfind("\n", 0, arr[0]) + 1
        indent = re.match(r"\s*", block[line_start:]).group(0)
        line_end = block.find("\n", arr[1])
        if line_end < 0:
            line_end = arr[1] + 1
        return block[:line_start] + f"{indent}dependencies: {rendered}" + block[line_end:]
    m = re.search(r'(?m)^(\s*)id:\s*"[0-9A-Fa-f]{16}"\s*,?\s*$', block)
    if not m:
        raise RuntimeError(f"Could not insert dependencies for {qid(block)}")
    indent = m.group(1)
    return block[:m.end()] + f"\n{indent}dependencies: {rendered}" + block[m.end():]


def replace_quests(text: str, blocks: list[str]) -> str:
    arr = named_array(text, "quests")
    if not arr:
        return text
    body = "\n".join("\t\t" + b for b in blocks)
    return text[:arr[0]] + "[\n" + body + "\n\t]" + text[arr[1] + 1:]


def namespace(item: str) -> str:
    return item.split(":", 1)[0] if ":" in item else ""


def allowed(stem: str, item: str) -> bool:
    ns = namespace(item)
    if stem.startswith("create_"):
        return ns == "create" or ns.startswith("create")
    return ns in THEMES.get(stem, set())


def item_ids(text: str) -> list[str]:
    return re.findall(r'(?m)^\s*item:\s*"([a-z0-9_.-]+:[a-z0-9_./-]+)"', text)


def parse_reward_entries(text: str) -> list[tuple[int, str, float]]:
    out: list[tuple[int, str, float]] = []
    arr = named_array(text, "rewards")
    if not arr:
        return out
    for obj in top_objects(text, *arr):
        mi = re.search(r'item:\s*"([a-z0-9_.-]+:[a-z0-9_./-]+)"', obj)
        if not mi:
            continue
        mc = re.search(r'count:\s*(\d+)', obj)
        mw = re.search(r'weight:\s*([0-9.]+)f?', obj)
        out.append((int(mc.group(1)) if mc else 1, mi.group(1), float(mw.group(1)) if mw else 1.0))
    return out


def render_reward_table(original: str, entries: list[tuple[int, str, float]]) -> str:
    arr = named_array(original, "rewards")
    if not arr:
        raise RuntimeError("Reward table missing rewards array")
    lines = []
    for count, item, weight in entries:
        cp = f"count: {count}, " if count != 1 else ""
        lines.append(f'\t\t{{ {cp}item: "{item}", weight: {weight:.2f}f }}')
    return original[:arr[0]] + "[\n" + "\n".join(lines) + "\n\t]" + original[arr[1] + 1:]


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def main() -> None:
    chapter_texts = {p.stem: p.read_text() for p in sorted(CHAPTERS.glob("*.snbt"))}
    missing = sorted(set(chapter_texts) - set(THEMES))
    if missing:
        raise RuntimeError(f"0.1.9-45 needs explicit reward themes for chapters: {missing}")

    filler: dict[str, list[str]] = {}
    for text in chapter_texts.values():
        for block in quest_blocks(text):
            if MARKER in block:
                filler[qid(block)] = deps(block)

    def resolve(dep: str, visiting: set[str] | None = None) -> list[str]:
        if dep not in filler:
            return [dep]
        visiting = set() if visiting is None else visiting
        if dep in visiting:
            raise RuntimeError(f"Cycle inside AA35 filler chain at {dep}")
        visiting.add(dep)
        out: list[str] = []
        for parent in filler[dep]:
            out.extend(resolve(parent, visiting.copy()))
        return list(dict.fromkeys(out))

    removed_by_chapter: dict[str, int] = {}
    kept_total = 0
    for stem, text in chapter_texts.items():
        kept: list[str] = []
        removed = 0
        for block in quest_blocks(text):
            if qid(block) in filler:
                removed += 1
                continue
            new_deps: list[str] = []
            for parent in deps(block):
                new_deps.extend(resolve(parent))
            block = set_deps(block, new_deps)
            kept.append(block)
        new_text = replace_quests(text, kept)
        if MARKER in new_text:
            raise RuntimeError(f"AA35 marker survived in {stem}")
        (CHAPTERS / f"{stem}.snbt").write_text(new_text)
        removed_by_chapter[stem] = removed
        kept_total += len(kept)

    # Re-theme the existing per-chapter rolls and wheels. We keep table IDs,
    # loot sizes, weights, and quest reward IDs; only unrelated item choices are
    # filtered/replaced.
    tables_changed = 0
    entries_removed = 0
    for stem in sorted(chapter_texts):
        candidates = []
        for item in item_ids((CHAPTERS / f"{stem}.snbt").read_text()):
            if allowed(stem, item) and item not in candidates:
                candidates.append(item)
        fallback = STARTER_FALLBACK if stem == "getting_started" else GENERAL_FALLBACK

        files = sorted(TABLES.glob(f"modroll_{stem}_tier_*.snbt"))
        wheel = TABLES / f"wheel_{stem}.snbt"
        if wheel.exists():
            files.append(wheel)
        for path in files:
            original = path.read_text()
            old = parse_reward_entries(original)
            if not old:
                continue
            new: list[tuple[int, str, float]] = []
            seen: set[tuple[int, str]] = set()
            for count, item, weight in old:
                if allowed(stem, item):
                    key = (count, item)
                    if key not in seen:
                        seen.add(key)
                        new.append((count, item, weight))
                else:
                    entries_removed += 1
            source = candidates + [x for x in fallback if stem == "getting_started"]
            for item in source:
                if len(new) >= min(8, max(4, len(old))):
                    break
                if not allowed(stem, item):
                    continue
                key = (1, item)
                if key not in seen:
                    seen.add(key)
                    new.append((1, item, 8.0))
            if not new:
                raise RuntimeError(f"No correctly themed rewards remain in {path.name}; curate {stem} explicitly")
            rendered = render_reward_table(original, new)
            if rendered != original:
                path.write_text(rendered)
                tables_changed += 1

    # Client/server quest sources must stay byte-identical.
    if SERVER.exists():
        shutil.rmtree(SERVER)
    shutil.copytree(CLIENT, SERVER)

    update_json(MANIFEST, lambda d: (d.__setitem__("version", VERSION), d.__setitem__("name", f"Amber & Arcana {VERSION}")))
    update_json(SUMMARY, lambda d: d.__setitem__("version", VERSION))
    def mutate_validation(d: dict) -> None:
        d["pack_version"] = VERSION
        d["quest_curation_0_1_9_45"] = {
            "aa35_filler_quests_removed": sum(removed_by_chapter.values()),
            "remaining_quests": kept_total,
            "reward_tables_rethemed": tables_changed,
            "unrelated_reward_entries_removed": entries_removed,
            "explicit_chapter_reward_themes": len(THEMES),
            "create_generic_fallback_removed": True,
            "client_server_quest_files_identical": True,
            "historical_non_filler_quest_ids_preserved": True,
        }
    update_json(VALIDATION, mutate_validation)

    readme = README.read_text()
    readme = re.sub(r'0\.1\.9-44-Client\.zip', f'{VERSION}-Client.zip', readme, count=1)
    readme = re.sub(r'0\.1\.9-44-Server\.zip', f'{VERSION}-Server.zip', readme, count=1)
    readme = re.sub(r'0\.1\.9-44-Crafty-Update-Overlay\.zip', f'{VERSION}-Crafty-Update-Overlay.zip', readme, count=1)
    readme = re.sub(r'\| Pack \| 0\.1\.9-44 \|', f'| Pack | {VERSION} |', readme, count=1)
    note = (
        "\n\n### 0.1.9-45 quest curation\n"
        "Removes the generated AA35 filler chains (for example Prepare/Build/Connect copies of the same milestone), reconnects the meaningful quests directly, and replaces the old Create-first generic reward fallback with explicit per-chapter reward themes. Build validation now rejects leftover AA35 filler markers and unrelated reward namespaces. Existing non-filler quest IDs and world/player data are preserved.\n"
    )
    if "### 0.1.9-45 quest curation" not in readme:
        readme += note
    README.write_text(readme)

    changelog = CHANGELOG.read_text() if CHANGELOG.exists() else ""
    entry = (
        f"## {VERSION}\n"
        "- Removed generated AA35 filler milestone chains and rewired real quest dependencies.\n"
        "- Removed Create-first generic reward fallback; reward tables are now constrained by explicit chapter themes.\n"
        "- Preserved all non-filler quest IDs and synchronized client/server quest data.\n\n"
    )
    if not changelog.startswith(f"## {VERSION}"):
        CHANGELOG.write_text(entry + changelog)

    print(f"Prepared {VERSION}: removed {sum(removed_by_chapter.values())} filler quests; kept {kept_total}; rethemed {tables_changed} reward tables; removed {entries_removed} unrelated reward entries.")


if __name__ == "__main__":
    main()
