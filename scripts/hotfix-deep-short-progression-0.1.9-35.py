#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import math
import re
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-35"
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

EXCLUDED = {"create_engineering", "productive_bees"}
MARKER = "AA35 deep progression milestone"
CURRENCY_ITEMS = {"minecraft:diamond", "minecraft:emerald", "minecraft:emerald_block"}

helper_path = ROOT / "scripts/hotfix-mod-tier-loot-0.1.9-32.py"
spec = importlib.util.spec_from_file_location("aa35_helpers", helper_path)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load quest helpers")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)

# These are behavior-oriented milestones. They deliberately use required
# checkmarks because FTB Quests cannot reliably detect that a player actually
# operated/automated a machine, completed a ritual, explored a biome, etc.
# Item acquisition remains automatic on the historical anchor quests.
ACTIONS: dict[str, list[tuple[str, str]]] = {
    "getting_started": [
        ("Prepare", "Organize the materials and tools from this milestone so the next system can be built without scavenging mid-project."),
        ("Build", "Put the milestone into a real starter-base setup instead of leaving the required item in a chest."),
        ("Connect", "Connect this milestone to storage, power, farming, or another useful base system and verify it works in normal play."),
    ],
    "mekanism": [
        ("Commission", "Place, power, configure, and run the Mekanism machines from this milestone on a real recipe."),
        ("Automate", "Route inputs, outputs, power, and side configuration so this Mekanism step can run without hand-feeding every operation."),
        ("Scale", "Add upgrades, buffering, or factory capacity and prove the process remains stable under sustained load."),
    ],
    "ender_io": [
        ("Wire", "Build a clean Ender IO conduit backbone for the machines unlocked by this milestone."),
        ("Route", "Use conduit filters, priorities, and extraction settings to move the correct resources without loops."),
        ("Automate", "Turn this part of Ender IO into a repeatable unattended production step."),
    ],
    "powah": [
        ("Stabilize", "Install the Powah generation or storage from this milestone and keep a useful machine powered continuously."),
        ("Energize", "Use the Energizing system and tier materials to support the next stage instead of crafting only the quest item."),
        ("Scale", "Increase generation, transfer, and storage headroom so the network can survive a larger factory load."),
    ],
    "create_workshops": [
        ("Build", "Turn this Create milestone into a working workshop station with sensible input and output handling."),
        ("Automate", "Make the process repeat reliably with belts, funnels, chutes, or another appropriate Create transport method."),
        ("Integrate", "Connect the workshop to another Create production line so materials flow between systems."),
    ],
    "create_city": [
        ("Plan", "Give this Create build a deliberate place in the city with room for maintenance and future expansion."),
        ("Connect", "Link this milestone into the city's item, fluid, rotational-power, or railway infrastructure."),
        ("Scale", "Expand the system until it serves more than one machine, building, station, or production area."),
    ],
    "ae2": [
        ("Network", "Bring the ME components from this milestone online as part of a powered network and verify terminals can see the intended storage."),
        ("Channel", "Route the network cleanly with channels, dense cable, P2P, or subnetworks as appropriate for the installed AE2 setup."),
        ("Autocraft", "Teach AE2 a useful recipe and successfully request it through the network rather than crafting it by hand."),
    ],
    "refined_storage": [
        ("Network", "Bring this Refined Storage milestone online as a powered network with accessible storage."),
        ("Route", "Connect at least one real machine or inventory using import, export, external storage, or interfaces without creating loops."),
        ("Autocraft", "Teach the network a useful recipe and successfully request or process it automatically."),
    ],
    "food_factory": [
        ("Process", "Use the food-production blocks from this milestone to complete a real processing chain."),
        ("Automate", "Automate ingredient input and finished-food output so the line can keep producing while you do something else."),
        ("Scale", "Expand the line to support several recipes or a sustained supply for the whole base."),
    ],
    "butchery": [
        ("Process", "Use the Butchery equipment from this milestone on its intended processing step and collect the resulting products."),
        ("Preserve", "Turn the outputs into useful food, blood, organs, or downstream ingredients instead of discarding byproducts."),
        ("Automate", "Create a repeatable processing flow for the parts of the Butchery chain that can be automated safely."),
    ],
    "ars_nouveau": [
        ("Cast", "Build and test a practical Ars Nouveau spell that uses the progression unlocked by this milestone."),
        ("Source", "Generate and move Source reliably enough to keep this stage of Ars crafting or automation supplied."),
        ("Automate", "Use Ars automation such as turrets, relays, apparatus work, or another installed integration on a repeatable task."),
    ],
    "irons_spells": [
        ("Learn", "Equip the spellcasting gear from this milestone and successfully use an appropriate spell in normal play."),
        ("Upgrade", "Improve your spellbook, scrolls, ink, armor, or spell selection so this tier is more than a one-off craft."),
        ("Prove", "Use the upgraded spell loadout in a meaningful combat or exploration encounter and confirm it is ready for the next tier."),
    ],
    "ritual_magic": [
        ("Prepare", "Build the ritual workspace and stock the ingredients or power source needed for this milestone."),
        ("Perform", "Complete a real ritual, rite, or magical process from this stage and verify the expected result occurs."),
        ("Sustain", "Make the ritual system repeatable by organizing ingredients, storage, safety, and any renewable inputs."),
    ],
    "alex_caves": [
        ("Explore", "Travel through the cave content tied to this milestone and identify the hazards, resources, and landmarks around it."),
        ("Recover", "Bring home a useful resource, specimen, or crafted result from the exploration rather than only visiting the area."),
        ("Survive", "Prepare equipment and complete another expedition using what you learned from the previous trip."),
    ],
    "dimensions": [
        ("Enter", "Reach the dimension or portal stage represented by this milestone and establish a safe arrival point."),
        ("Establish", "Create a small operating foothold with supplies, storage, and a reliable route home."),
        ("Recover", "Return with a meaningful dimension-specific resource or objective completed before moving deeper."),
    ],
    "dinosaur_laboratory": [
        ("Extract", "Run the fossil or DNA workflow far enough to produce usable material for the laboratory."),
        ("Incubate", "Use the laboratory chain to create or prepare a living specimen rather than stopping at raw DNA."),
        ("Contain", "Build a secure habitat with feeding, observation, and escape prevention suitable for the specimen."),
    ],
    "alex_wildlife": [
        ("Observe", "Find and observe the creature or wildlife system represented by this milestone in an appropriate habitat."),
        ("Care", "Provide the food, enclosure, breeding conditions, or interaction needed to keep the creature safely."),
        ("Document", "Complete another wildlife objective and organize the resulting drops, specimens, or discoveries."),
    ],
    "aquarium": [
        ("Collect", "Acquire aquatic life or materials for this milestone without emptying the local habitat."),
        ("House", "Build a functional aquarium environment with enough space and the conditions needed by the inhabitants."),
        ("Breed", "Maintain or breed the collection and turn the aquarium into a stable long-term system."),
    ],
    "settlement": [
        ("Build", "Turn this settlement milestone into an actual completed structure or service area rather than a pile of materials."),
        ("Staff", "Assign or support the workers, villagers, colonists, or residents needed to make the new area useful."),
        ("Expand", "Connect the new service to roads, storage, defenses, food, or another settlement system and prepare the next expansion."),
    ],
    "tinkers": [
        ("Forge", "Use the Tinkers setup from this milestone to make a real tool or weapon part and assemble useful equipment."),
        ("Modify", "Apply modifiers or material choices that solve a real mining, combat, or building need."),
        ("Upgrade", "Improve the foundry/smeltery workflow and create a stronger second-generation tool rather than stopping at the first craft."),
    ],
    "firearms": [
        ("Manufacture", "Produce the weapon, ammunition, or supporting components for this milestone through the intended crafting chain."),
        ("Test", "Use the firearm on a safe combat test and confirm ammunition, handling, and reliability before relying on it."),
        ("Upgrade", "Improve the weapon setup with the installed attachments, ammunition options, or higher-tier manufacturing path."),
    ],
    "alex_utilities": [
        ("Build", "Craft and place the utility from this milestone where it solves a real base or exploration problem."),
        ("Use", "Run the utility through its intended job and verify you understand its controls and limitations."),
        ("Integrate", "Connect the utility to another storage, transport, automation, or creature-management system."),
    ],
    "buddycards": [
        ("Collect", "Open, trade, or find enough cards from this stage to make visible progress on the collection rather than obtaining only one sample."),
        ("Organize", "Sort the collection and identify the missing cards, rarities, or sets needed for the next milestone."),
        ("Complete", "Finish a meaningful set or collection goal before advancing to the final Buddycards milestones."),
    ],
    "endgame": [
        ("Prepare", "Assemble the infrastructure, equipment, and renewable supplies needed to attempt this endgame milestone repeatedly."),
        ("Conquer", "Complete the milestone in normal play and bring the resulting resources back into your main progression."),
        ("Perfect", "Automate, optimize, or repeat the endgame objective until it becomes a stable part of the finished base."),
    ],
}


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def root_title(block: str) -> str:
    m = re.search(r'(?m)^\s*title:\s*"([^"]+)"', block)
    return m.group(1) if m else "Milestone"


def root_icon(block: str, fallback: str) -> str:
    m = re.search(r'(?m)^\s*icon:\s*"([^"]+)"', block)
    return m.group(1) if m else fallback


def chapter_icon(text: str) -> str:
    head = text[: text.find("quests:") if "quests:" in text else len(text)]
    m = re.search(r'(?m)^\s*icon:\s*"([^"]+)"', head)
    return m.group(1) if m else "minecraft:book"


def chapter_title(text: str, stem: str) -> str:
    return h.chapter_title(text, stem).replace(" & ", " and ")


def stage_count(original_count: int) -> int:
    if original_count <= 3:
        return 3
    if original_count <= 5:
        return 2
    return 1


def gen_id(seed: str) -> str:
    return f"{h.deterministic_long(seed):016X}"


def set_dependencies(block: str, deps: list[str]) -> str:
    deps = list(dict.fromkeys(deps))
    rendered = "[" + ", ".join(json.dumps(d) for d in deps) + "]"
    arr = h.named_array(block, "dependencies")
    if arr:
        line_start = block.rfind("\n", 0, arr[0]) + 1
        indent = re.match(r"\s*", block[line_start:]).group(0)
        return block[:line_start] + f"{indent}dependencies: {rendered}" + block[arr[1] + 1:]
    mid = re.search(r'(?m)^(\s*)id:\s*"[0-9A-F]{16}"[^\n]*\n', block)
    if not mid:
        raise RuntimeError("Could not insert quest dependencies")
    indent = mid.group(1)
    return block[:mid.end()] + f"{indent}dependencies: {rendered}\n" + block[mid.end():]


def set_rewards(block: str, objects: list[str]) -> str:
    arr = h.named_array(block, "rewards")
    if not arr:
        raise RuntimeError(f"Quest {h.quest_id(block)} has no rewards array")
    line_start = block.rfind("\n", 0, arr[0]) + 1
    indent = re.match(r"\s*", block[line_start:]).group(0)
    body_indent = indent + "\t"
    body = "\n".join(body_indent + obj for obj in objects)
    replacement = f"{indent}rewards: ["
    if body:
        replacement += "\n" + body + "\n" + indent
    replacement += "]"
    return block[:line_start] + replacement + block[arr[1] + 1:]


def reward_info(block: str) -> tuple[list[str], str | None, str | None, int]:
    kept: list[str] = []
    wheel: str | None = None
    tier_reward_id: str | None = None
    removed_currency = 0
    for s, e in h.reward_objects(block):
        obj = block[s:e]
        title = re.search(r'title:\s*"([^"]+)"', obj)
        rid = re.search(r'id:\s*"([0-9A-F]{16})"', obj)
        item = re.search(r'item:\s*"([^"]+)"', obj)
        is_loot = 'type: "loot"' in obj
        if is_loot and title and title.group(1) == "Spin the Wheel of Fortune":
            wheel = obj
            continue
        if is_loot and title and re.search(r" Tier [1-4] Roll$", title.group(1)):
            if rid:
                tier_reward_id = rid.group(1)
            continue
        if item and item.group(1) in CURRENCY_ITEMS and 'type: "item"' in obj:
            removed_currency += 1
            continue
        kept.append(obj)
    return kept, wheel, tier_reward_id, removed_currency


def loot_reward_obj(reward_id: str, table_id: int, title: str) -> str:
    return (
        "{\n"
        f'\t\t\t\t\tid: "{reward_id}"\n'
        f"\t\t\t\t\ttable_id: {table_id}L\n"
        f"\t\t\t\t\ttitle: {json.dumps(title, ensure_ascii=False)}\n"
        '\t\t\t\t\ttype: "loot"\n'
        "\t\t\t\t}"
    )


def render_manual_quest(stem: str, anchor_id: str, anchor_title: str, icon: str, stage: int, dep: str, action: tuple[str, str]) -> str:
    prefix, description = action
    qid = gen_id(f"aa35:{stem}:{anchor_id}:stage:{stage}")
    task_id = gen_id(f"aa35:{stem}:{anchor_id}:stage:{stage}:task")
    title = f"{prefix}: {anchor_title}"
    return (
        "{\n"
        f'\t\t\tdependencies: ["{dep}"]\n'
        "\t\t\tdescription: [\n"
        f"\t\t\t\t{json.dumps(description, ensure_ascii=False)}\n"
        f"\t\t\t\t{json.dumps('Complete this hands-on milestone before advancing. ' + MARKER, ensure_ascii=False)}\n"
        "\t\t\t]\n"
        f"\t\t\ticon: {json.dumps(icon)}\n"
        f'\t\t\tid: "{qid}"\n'
        "\t\t\trewards: []\n"
        f"\t\t\tsubtitle: {json.dumps('Hands-on progression milestone; confirm it after actually completing the described mechanic.')}\n"
        "\t\t\ttasks: [\n"
        "\t\t\t\t{\n"
        f'\t\t\t\t\tid: "{task_id}"\n'
        f"\t\t\t\t\ttitle: {json.dumps('Confirm: ' + title, ensure_ascii=False)}\n"
        '\t\t\t\t\ttype: "checkmark"\n'
        "\t\t\t\t}\n"
        "\t\t\t]\n"
        f"\t\t\ttitle: {json.dumps(title, ensure_ascii=False)}\n"
        "\t\t\tx: 0.0d\n"
        "\t\t\ty: 0.0d\n"
        "\t\t}"
    )


def render_mastery(stem: str, title: str, icon: str, deps: list[str]) -> str:
    qid = gen_id(f"aa35:{stem}:mastery")
    task_id = gen_id(f"aa35:{stem}:mastery:task")
    dep_text = ", ".join(json.dumps(d) for d in deps)
    return (
        "{\n"
        f"\t\t\tdependencies: [{dep_text}]\n"
        "\t\t\tdescription: [\n"
        f"\t\t\t\t{json.dumps('Finish every progression branch in this chapter, then verify the systems work together as a complete build.', ensure_ascii=False)}\n"
        f"\t\t\t\t{json.dumps('This is the true chapter finale and carries the Wheel of Fortune reward. ' + MARKER, ensure_ascii=False)}\n"
        "\t\t\t]\n"
        f"\t\t\ticon: {json.dumps(icon)}\n"
        f'\t\t\tid: "{qid}"\n'
        "\t\t\trewards: []\n"
        f"\t\t\tsubtitle: {json.dumps('Complete every branch before claiming the chapter finale.')}\n"
        "\t\t\ttasks: [\n"
        "\t\t\t\t{\n"
        f'\t\t\t\t\tid: "{task_id}"\n'
        f"\t\t\t\t\ttitle: {json.dumps('Confirm chapter mastery: ' + title, ensure_ascii=False)}\n"
        '\t\t\t\t\ttype: "checkmark"\n'
        "\t\t\t\t}\n"
        "\t\t\t]\n"
        f"\t\t\ttitle: {json.dumps(title + ' Mastery', ensure_ascii=False)}\n"
        "\t\t\tx: 0.0d\n"
        "\t\t\ty: 0.0d\n"
        "\t\t}"
    )


def set_xy(block: str, x: float, y: float) -> str:
    block = re.sub(r'(?m)^(\s*)x:\s*-?[0-9.]+d?,?', lambda m: f"{m.group(1)}x: {x:.1f}d", block, count=1)
    block = re.sub(r'(?m)^(\s*)y:\s*-?[0-9.]+d?,?', lambda m: f"{m.group(1)}y: {y:.1f}d", block, count=1)
    return block


def replace_quests(text: str, blocks: list[str]) -> str:
    arr = h.named_array(text, "quests")
    if not arr:
        raise RuntimeError("Chapter has no quests array")
    m = re.search(r'(?m)^(\s*)quests:\s*\[', text)
    base = m.group(1) if m else "\t"
    object_indent = base + "\t"
    body = "\n".join(object_indent + b for b in blocks)
    return text[:arr[0]] + "[\n" + body + "\n" + base + "]" + text[arr[1] + 1:]


def local_depths(blocks: dict[str, str]) -> dict[str, int]:
    deps = {qid: [d for d in h.quest_deps(block) if d in blocks] for qid, block in blocks.items()}
    memo: dict[str, int] = {}
    visiting: set[str] = set()

    def visit(qid: str) -> int:
        if qid in memo:
            return memo[qid]
        if qid in visiting:
            raise RuntimeError(f"Quest dependency cycle involving {qid}")
        visiting.add(qid)
        value = 0 if not deps[qid] else 1 + max(visit(d) for d in deps[qid])
        visiting.remove(qid)
        memo[qid] = value
        return value

    for qid in blocks:
        visit(qid)
    return memo


def tier_for(depth: int, max_depth: int) -> int:
    if max_depth <= 0:
        return 4
    ratio = depth / max_depth
    if ratio < 0.25:
        return 1
    if ratio < 0.50:
        return 2
    if ratio < 0.75:
        return 3
    return 4


def table_ids(stem: str) -> dict[int, int]:
    out: dict[int, int] = {}
    for tier in range(1, 5):
        path = TABLES / f"modroll_{stem}_tier_{tier}.snbt"
        if not path.exists():
            raise RuntimeError(f"Missing tier table for {stem}: {path.name}")
        m = re.search(r'(?m)^\s*id:\s*"([0-9A-F]{16})"', path.read_text())
        if not m:
            raise RuntimeError(f"Missing table id in {path.name}")
        out[tier] = int(m.group(1), 16)
    return out


def layout(blocks: dict[str, str], order: dict[str, int]) -> tuple[dict[str, str], float, float]:
    depths = local_depths(blocks)
    groups: dict[int, list[str]] = defaultdict(list)
    for qid, depth in depths.items():
        groups[depth].append(qid)
    for ids in groups.values():
        ids.sort(key=lambda q: order.get(q, 10**9))

    max_same_depth = max((len(v) for v in groups.values()), default=1)
    row_height = max(8.0, max_same_depth * 3.2 + 4.0)
    columns = 9
    x_spacing = 4.0
    y_spacing = 3.2
    positions: dict[str, tuple[float, float]] = {}
    for depth in sorted(groups):
        row = depth // columns
        col = depth % columns
        if row % 2:
            col = columns - 1 - col
        x = (col - (columns - 1) / 2.0) * x_spacing
        ids = groups[depth]
        for lane, qid in enumerate(ids):
            y = row * row_height + (lane - (len(ids) - 1) / 2.0) * y_spacing
            positions[qid] = (x, y)

    updated = {qid: set_xy(block, *positions[qid]) for qid, block in blocks.items()}
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    width = (max(xs) - min(xs)) if xs else 0.0
    height = (max(ys) - min(ys)) if ys else 0.0
    return updated, width, height


def process_chapter(path: Path) -> dict:
    stem = path.stem
    text = path.read_text()
    title = chapter_title(text, stem)
    cicon = chapter_icon(text)
    positions = h.quest_positions(text)
    all_blocks = [text[s:e] for s, e in positions]
    original_blocks = [b for b in all_blocks if MARKER not in b]
    if not original_blocks:
        raise RuntimeError(f"No historical quests found in {stem}")

    original_ids = [h.quest_id(b) for b in original_blocks]
    if len(original_ids) != len(set(original_ids)):
        raise RuntimeError(f"Duplicate historical quest id in {stem}")
    original_set = set(original_ids)
    stages_per_anchor = stage_count(len(original_ids))

    # Compute deterministic stage ids so a replay can restore dependencies that
    # currently point at generated 0.1.9-35 gates before rebuilding the tree.
    generated_by_anchor: dict[str, list[str]] = {}
    reverse_terminal: dict[str, str] = {}
    for qid in original_ids:
        ids = [gen_id(f"aa35:{stem}:{qid}:stage:{i}") for i in range(stages_per_anchor)]
        generated_by_anchor[qid] = ids
        reverse_terminal[ids[-1]] = qid

    restored: dict[str, str] = {}
    old_tier_reward_ids: dict[str, str] = {}
    wheel_obj: str | None = None
    removed_currency = 0
    wheel_count = 0

    for block in original_blocks:
        qid = h.quest_id(block)
        deps = []
        for dep in h.quest_deps(block):
            deps.append(reverse_terminal.get(dep, dep))
        block = set_dependencies(block, deps)
        kept, wheel, tier_rid, currency_count = reward_info(block)
        block = set_rewards(block, kept)
        if wheel:
            wheel_obj = wheel
            wheel_count += 1
        if tier_rid:
            old_tier_reward_ids[qid] = tier_rid
        removed_currency += currency_count
        restored[qid] = block

    # Build the historical local dependency graph before inserting gates.
    original_parents = {qid: [d for d in h.quest_deps(restored[qid]) if d in original_set] for qid in original_ids}
    children: dict[str, list[str]] = defaultdict(list)
    for child, parents in original_parents.items():
        for parent in parents:
            children[parent].append(child)

    # Replace each local historical dependency with the terminal hands-on stage
    # after that parent. This makes the new progression real rather than cosmetic.
    for qid in original_ids:
        deps = []
        for dep in h.quest_deps(restored[qid]):
            if dep in original_set:
                deps.append(generated_by_anchor[dep][-1])
            else:
                deps.append(dep)
        restored[qid] = set_dependencies(restored[qid], deps)

    blocks: dict[str, str] = dict(restored)
    order: dict[str, int] = {}
    serial = 0
    for qid in original_ids:
        order[qid] = serial
        serial += 1
        anchor_title = root_title(restored[qid])
        icon = root_icon(restored[qid], cicon)
        dep = qid
        actions = ACTIONS.get(stem, ACTIONS["getting_started"])
        for stage in range(stages_per_anchor):
            action = actions[stage % len(actions)]
            block = render_manual_quest(stem, qid, anchor_title, icon, stage, dep, action)
            sid = h.quest_id(block)
            blocks[sid] = block
            order[sid] = serial
            serial += 1
            dep = sid

    leaves = [qid for qid in original_ids if not children.get(qid)]
    mastery_deps = [generated_by_anchor[qid][-1] for qid in leaves]
    if not mastery_deps:
        mastery_deps = [generated_by_anchor[original_ids[-1]][-1]]
    mastery = render_mastery(stem, title, cicon, mastery_deps)
    mastery_id = h.quest_id(mastery)
    blocks[mastery_id] = mastery
    order[mastery_id] = serial

    # Recalculate depth after the real gates are in place, then give every quest
    # exactly one depth-appropriate tier roll. Historical quest reward ids are
    # reused when possible so already-claimed rolls are not needlessly reset.
    depths = local_depths(blocks)
    max_depth = max(depths.values()) if depths else 0
    tids = table_ids(stem)
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for qid in list(blocks):
        block = blocks[qid]
        kept, stray_wheel, existing_tier_id, currency_count = reward_info(block)
        removed_currency += currency_count
        if stray_wheel:
            wheel_obj = wheel_obj or stray_wheel
        tier = 4 if qid == mastery_id else tier_for(depths[qid], max_depth)
        rid = old_tier_reward_ids.get(qid) or existing_tier_id or gen_id(f"aa35:{stem}:{qid}:tier-reward")
        kept.append(loot_reward_obj(rid, tids[tier], f"{title} Tier {tier} Roll"))
        if qid == mastery_id and wheel_obj:
            kept.append(wheel_obj)
        blocks[qid] = set_rewards(block, kept)
        tier_counts[tier] += 1

    if wheel_count > 1:
        raise RuntimeError(f"Expected one historical wheel reward in {stem}, found {wheel_count}")
    if wheel_obj is None:
        raise RuntimeError(f"No Wheel of Fortune reward found to move in {stem}")

    blocks, width, height = layout(blocks, order)

    # Order the chapter by dependency depth, then by stable historical/generated
    # sequence. This makes the file deterministic and the visual tree predictable.
    depths = local_depths(blocks)
    sorted_ids = sorted(blocks, key=lambda q: (depths[q], order.get(q, 10**9), q))
    new_text = replace_quests(text, [blocks[qid] for qid in sorted_ids])
    path.write_text(new_text)

    # Final chapter-level checks before server sync.
    final_positions = h.quest_positions(new_text)
    final_blocks = [new_text[s:e] for s, e in final_positions]
    final_ids = [h.quest_id(b) for b in final_blocks]
    if len(final_ids) != len(set(final_ids)):
        raise RuntimeError(f"Duplicate quest ids after expansion in {stem}")
    if not original_set.issubset(set(final_ids)):
        raise RuntimeError(f"Historical quest id lost in {stem}")
    loot_coverage = sum(1 for b in final_blocks if re.search(r'title:\s*"[^"]+ Tier [1-4] Roll"', b))
    if loot_coverage != len(final_blocks):
        raise RuntimeError(f"Tier roll coverage failed in {stem}: {loot_coverage}/{len(final_blocks)}")
    if sum(1 for b in final_blocks if "Spin the Wheel of Fortune" in b) != 1:
        raise RuntimeError(f"Wheel reward is not unique in {stem}")

    return {
        "chapter": stem,
        "title": title,
        "historical_quests": len(original_ids),
        "generated_mechanics_quests": len(final_blocks) - len(original_ids) - 1,
        "total_quests": len(final_blocks),
        "stages_per_historical_quest": stages_per_anchor,
        "max_depth": max(local_depths({h.quest_id(b): b for b in final_blocks}).values()),
        "tier_counts": {str(k): v for k, v in tier_counts.items()},
        "layout_width": round(width, 1),
        "layout_height": round(height, 1),
        "generic_currency_rewards_removed": removed_currency,
        "historical_ids_preserved": True,
        "wheel_moved_to_mastery": True,
    }


def main() -> None:
    targets = [p for p in sorted(CHAPTERS.glob("*.snbt")) if p.stem not in EXCLUDED]
    if len(targets) != 24:
        raise RuntimeError(f"Expected 24 compact chapters to deepen, found {len(targets)}")

    chapter_stats = [process_chapter(path) for path in targets]
    original_total = sum(s["historical_quests"] for s in chapter_stats)
    generated_total = sum(s["generated_mechanics_quests"] for s in chapter_stats)
    expanded_total = sum(s["total_quests"] for s in chapter_stats)
    currency_removed = sum(s["generic_currency_rewards_removed"] for s in chapter_stats)
    minimum_quests = min(s["total_quests"] for s in chapter_stats)
    minimum_depth = min(s["max_depth"] for s in chapter_stats)
    max_width = max(s["layout_width"] for s in chapter_stats)
    max_height = max(s["layout_height"] for s in chapter_stats)

    if original_total < 100:
        raise RuntimeError(f"Expected at least 100 historical compact quests, found {original_total}")
    if minimum_quests < 10:
        raise RuntimeError(f"A deepened chapter is still too short: minimum {minimum_quests}")
    if minimum_depth < 4:
        raise RuntimeError(f"A deepened chapter still has insufficient dependency depth: {minimum_depth}")

    # Synchronize the complete quest tree after all chapter edits.
    if SERVER_QUESTS.exists():
        shutil.rmtree(SERVER_QUESTS)
    shutil.copytree(CLIENT_QUESTS, SERVER_QUESTS)

    update_json(MANIFEST, lambda d: (d.__setitem__("version", VERSION), d.__setitem__("name", f"Amber & Arcana {VERSION}")))

    metrics = {
        "chapters_expanded": len(chapter_stats),
        "historical_short_quests_preserved": original_total,
        "generated_mechanics_quests": generated_total,
        "expanded_short_quest_total": expanded_total,
        "minimum_quests_per_expanded_chapter": minimum_quests,
        "minimum_dependency_depth": minimum_depth,
        "tier_roll_coverage_percent": 100.0,
        "finale_wheels_moved_to_true_mastery": len(chapter_stats),
        "generic_diamond_emerald_rewards_removed": currency_removed,
        "max_layout_width": max_width,
        "max_layout_height": max_height,
        "historical_quest_ids_preserved": True,
        "historical_tier_reward_ids_reused": True,
        "client_server_quest_files_identical": True,
        "excluded_custom_deep_chapters": sorted(EXCLUDED),
        "chapters": chapter_stats,
    }
    update_json(VALIDATION, lambda d: (d.__setitem__("pack_version", VERSION), d.__setitem__("deep_short_progression_0_1_9_35", metrics)))
    update_json(SUMMARY, lambda d: (d.__setitem__("pack_version", VERSION), d.__setitem__("deep_short_progression_0_1_9_35", metrics)))

    vt = VALIDATE_SH.read_text()
    vt = vt.replace('.version == "0.1.9-34"', '.version == "0.1.9-35"')
    vt = vt.replace('.pack_version == "0.1.9-34"', '.pack_version == "0.1.9-35"')
    vt = vt.replace('Amber & Arcana 0.1.9-34 static validation passed', 'Amber & Arcana 0.1.9-35 static validation passed')
    marker = "# 0.1.9-35 deep compact-chapter progression checks"
    if marker not in vt:
        vt += f'''\n\n{marker}\njq -e '.deep_short_progression_0_1_9_35.chapters_expanded == 24 and .deep_short_progression_0_1_9_35.historical_short_quests_preserved >= 100 and .deep_short_progression_0_1_9_35.generated_mechanics_quests >= 100 and .deep_short_progression_0_1_9_35.minimum_quests_per_expanded_chapter >= 10 and .deep_short_progression_0_1_9_35.minimum_dependency_depth >= 4 and .deep_short_progression_0_1_9_35.tier_roll_coverage_percent == 100 and .deep_short_progression_0_1_9_35.finale_wheels_moved_to_true_mastery == 24 and .deep_short_progression_0_1_9_35.historical_quest_ids_preserved == true and .deep_short_progression_0_1_9_35.client_server_quest_files_identical == true' "$validation" >/dev/null\ntest "$(rg -l '{MARKER}' "$client_quests/chapters" | wc -l)" = "24" || {{ echo "Deep progression marker missing from one or more expanded chapters" >&2; exit 1; }}\ncmp -r "$client_quests" "$server_quests" >/dev/null || {{ echo "Client/server quest trees differ after 0.1.9-35" >&2; exit 1; }}\n'''
    VALIDATE_SH.write_text(vt)

    rt = README.read_text()
    if "0.1.9-35 deep progression pass" not in rt:
        rt += f'''\n\n## 0.1.9-35 deep progression pass\n\nThe 24 formerly compact quest chapters now use real multi-step progression trees instead of three-to-ten broad milestones. Historical item-acquisition quests are preserved, but every local dependency is gated through required hands-on mechanics milestones such as commissioning machines, routing storage, automating production, performing rituals, exploring safely, or scaling a system. The pass adds {generated_total} hands-on quests, raises the compact chapters to {expanded_total} total quests, keeps tiered mod-specific loot on 100% of those quests, moves each Wheel of Fortune reward to a true chapter-mastery finale, removes remaining fixed diamond/emerald rewards from the expanded chapters, and preserves the existing historical quest IDs. Create Engineering and Productive Bees retain their dedicated custom trees.\n'''
        README.write_text(rt)

    ct = CHANGELOG.read_text()
    heading = "## 0.1.9-35 — Deep progression for compact chapters"
    if heading not in ct:
        body = f'''# Changelog\n\n{heading}\n\n- Expand all 24 formerly compact chapters into multi-step mechanics progression trees while preserving their historical quest IDs.\n- Add {generated_total} required hands-on progression quests for commissioning, operation, automation, exploration, rituals, scaling, and other chapter-specific mechanics.\n- Gate historical local dependencies through the new mechanics milestones so the added depth is real progression rather than optional decoration.\n- Give every original and new quest one depth-appropriate mod-specific Tier 1-4 loot roll.\n- Move every compact chapter's Wheel of Fortune reward to a new true mastery finale that depends on all branch leaves.\n- Remove fixed diamond/emerald currency rewards from the expanded chapters; XP and useful starter materials remain.\n- Re-layout the expanded trees in a compact serpentine dependency layout and synchronize the complete quest tree client/server.\n\n'''
        CHANGELOG.write_text(body + ct.removeprefix("# Changelog\n\n"))

    # Quest parity is the last invariant before the build archives are created.
    for client_file in CLIENT_QUESTS.rglob("*"):
        if client_file.is_file():
            server_file = SERVER_QUESTS / client_file.relative_to(CLIENT_QUESTS)
            if not server_file.exists() or client_file.read_bytes() != server_file.read_bytes():
                raise RuntimeError(f"Client/server quest mismatch: {client_file.relative_to(CLIENT_QUESTS)}")

    print(
        f"Applied Amber & Arcana {VERSION}: deepened {len(chapter_stats)} chapters from "
        f"{original_total} historical quests to {expanded_total} total quests, with "
        f"{generated_total} new mechanics milestones and 100% tier-roll coverage"
    )


if __name__ == "__main__":
    main()
