#!/usr/bin/env python3
"""Repair circular FTB Quests dependencies and prepare Amber & Arcana 0.1.9-44."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-44"
CLIENT_CHAPTERS = ROOT / "client/overrides/config/ftbquests/quests/chapters"
SERVER_CHAPTERS = ROOT / "server/config/ftbquests/quests/chapters"
MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
VALIDATE_SH = ROOT / "scripts/validate.sh"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"

# FTB Quests' SNBT writer legitimately emits both `id: "..."` and
# `id: "...",`. Accept the optional trailing comma while keeping the exact
# quest-level indentation so task/reward IDs are never mistaken for quest IDs.
ID_RE = re.compile(r'^\t\t\tid:\s*"([0-9A-Fa-f]{16})"\s*,?\s*$', re.M)
TITLE_RE = re.compile(r'^\t\t\ttitle:\s*"([^"]*)"\s*,?\s*$', re.M)
DEPS_RE = re.compile(r'^\t\t\tdependencies:\s*\[(.*?)\]\s*,?\s*$', re.M)
HEX_RE = re.compile(r'"([0-9A-Fa-f]{16})"')


@dataclass(frozen=True)
class Quest:
    qid: str
    title: str
    chapter: str
    path: Path
    deps: tuple[str, ...]


def split_quest_blocks(text: str) -> list[str]:
    """Extract top-level quest objects by SNBT nesting, not indentation."""
    marker = re.search(r'\bquests\s*:\s*\[', text)
    if not marker:
        return []
    i = marker.end()
    square = 1
    curly = 0
    start: int | None = None
    quote = False
    escape = False
    blocks: list[str] = []
    while i < len(text) and square > 0:
        ch = text[i]
        if quote:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                quote = False
            i += 1
            continue
        if ch == '"':
            quote = True
        elif ch == '[':
            square += 1
        elif ch == ']':
            square -= 1
        elif ch == '{':
            if square == 1 and curly == 0:
                start = i
            curly += 1
        elif ch == '}':
            curly -= 1
            if curly < 0:
                raise RuntimeError("unbalanced quest braces")
            if curly == 0 and start is not None:
                blocks.append(text[start:i + 1])
                start = None
        i += 1
    if square != 0 or curly != 0 or start is not None:
        raise RuntimeError("unterminated quests list/object")
    return blocks


def load_graph() -> dict[str, Quest]:
    quests: dict[str, Quest] = {}
    for path in sorted(CLIENT_CHAPTERS.glob("*.snbt")):
        for block in split_quest_blocks(path.read_text()):
            mid = ID_RE.search(block)
            if not mid:
                continue
            qid = mid.group(1).upper()
            if qid in quests:
                raise RuntimeError(f"Duplicate quest id {qid}")
            mtitle = TITLE_RE.search(block)
            mdeps = DEPS_RE.search(block)
            deps = tuple(x.upper() for x in HEX_RE.findall(mdeps.group(1))) if mdeps else ()
            quests[qid] = Quest(qid, mtitle.group(1) if mtitle else qid, path.name, path, deps)
    return quests


def find_cycle(graph: dict[str, Quest]) -> list[str] | None:
    state: dict[str, int] = {}
    stack: list[str] = []
    pos: dict[str, int] = {}

    def visit(qid: str) -> list[str] | None:
        state[qid] = 1
        pos[qid] = len(stack)
        stack.append(qid)
        for dep in graph[qid].deps:
            if dep not in graph:
                continue
            if state.get(dep, 0) == 0:
                cycle = visit(dep)
                if cycle:
                    return cycle
            elif state.get(dep) == 1:
                return stack[pos[dep]:] + [dep]
        stack.pop()
        pos.pop(qid, None)
        state[qid] = 2
        return None

    for qid in graph:
        if state.get(qid, 0) == 0:
            cycle = visit(qid)
            if cycle:
                return cycle
    return None


def remove_dependency(quest: Quest, dep: str) -> None:
    text = quest.path.read_text()
    for block in split_quest_blocks(text):
        mid = ID_RE.search(block)
        if not mid or mid.group(1).upper() != quest.qid:
            continue
        mdeps = DEPS_RE.search(block)
        if not mdeps:
            raise RuntimeError(f"Quest {quest.qid} has no dependency line")
        deps = [x.upper() for x in HEX_RE.findall(mdeps.group(1))]
        if dep not in deps:
            raise RuntimeError(f"Dependency {dep} not present on quest {quest.qid}")
        deps.remove(dep)
        original = mdeps.group(0)
        trailing_comma = original.rstrip().endswith(",")
        replacement = '\t\t\tdependencies: [' + ' '.join(f'"{d}"' for d in deps) + ']'
        if trailing_comma:
            replacement += ','
        new_block = block[:mdeps.start()] + replacement + block[mdeps.end():]
        quest.path.write_text(text.replace(block, new_block, 1))
        return
    raise RuntimeError(f"Could not locate quest block {quest.qid}")


def edge_priority(graph: dict[str, Quest], src: str, dep: str) -> tuple[int, str, str]:
    a, b = graph[src], graph[dep]
    # A starter quest depending on an advanced quest is almost certainly the backwards edge.
    if a.chapter == "getting_started.snbt" and b.chapter != a.chapter:
        tier = 0
    # Prefer dropping cross-chapter back-links before altering a chapter's internal progression.
    elif a.chapter != b.chapter:
        tier = 1
    else:
        tier = 2
    return (tier, a.chapter + ":" + a.title, b.chapter + ":" + b.title)


def repair_cycles() -> list[dict[str, str]]:
    removed: list[dict[str, str]] = []
    for _ in range(1000):
        graph = load_graph()
        cycle = find_cycle(graph)
        if not cycle:
            return removed
        edges = list(zip(cycle, cycle[1:]))
        src, dep = min(edges, key=lambda edge: edge_priority(graph, edge[0], edge[1]))
        a, b = graph[src], graph[dep]
        print(f"Removing cyclic dependency: {a.chapter}:{a.title} ({src}) -> {b.chapter}:{b.title} ({dep})")
        remove_dependency(a, dep)
        removed.append({
            "quest_id": src,
            "quest_title": a.title,
            "quest_chapter": a.chapter,
            "removed_dependency_id": dep,
            "removed_dependency_title": b.title,
            "removed_dependency_chapter": b.chapter,
        })
    raise RuntimeError("Too many quest-cycle repairs; refusing to continue")


def sync_server() -> None:
    SERVER_CHAPTERS.mkdir(parents=True, exist_ok=True)
    client_names = {p.name for p in CLIENT_CHAPTERS.glob("*.snbt")}
    for stale in SERVER_CHAPTERS.glob("*.snbt"):
        if stale.name not in client_names:
            stale.unlink()
    for source in CLIENT_CHAPTERS.glob("*.snbt"):
        (SERVER_CHAPTERS / source.name).write_bytes(source.read_bytes())


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_release_metadata(removed: list[dict[str, str]]) -> None:
    manifest = json.loads(MANIFEST.read_text())
    manifest["version"] = VERSION
    manifest["name"] = "Amber & Arcana " + VERSION
    save_json(MANIFEST, manifest)

    marker = {
        "ftb_quests_version": "2001.4.14",
        "repair_strategy": "remove only dependency edges that participate in directed cycles; prefer cross-chapter/backwards edges",
        "removed_dependency_edges": removed,
        "removed_edge_count": len(removed),
        "quest_ids_preserved": True,
        "world_data_modified": False,
        "client_server_quest_files_identical": True,
        "acyclic_validator": "scripts/validate-quest-graph.py",
    }
    for path in (SUMMARY, VALIDATION):
        data = json.loads(path.read_text())
        data["pack_version"] = VERSION
        data["quest_cycle_hotfix_0_1_9_44"] = marker
        save_json(path, data)

    text = VALIDATE_SH.read_text()
    text = text.replace('.version == "0.1.9-43"', '.version == "0.1.9-44"')
    text = text.replace('.pack_version == "0.1.9-43"', '.pack_version == "0.1.9-44"')
    text = text.replace('Amber & Arcana 0.1.9-43 static validation passed', 'Amber & Arcana 0.1.9-44 static validation passed')
    check = 'python3 "$repo_dir/scripts/validate-quest-graph.py"'
    if check not in text:
        text += "\n# 0.1.9-44: FTB Quests must never contain directed dependency cycles.\n" + check + "\n"
    VALIDATE_SH.write_text(text)

    text = README.read_text()
    text = text.replace("Download Client 0.1.9-43", "Download Client 0.1.9-44")
    text = text.replace("Download Crafty Server 0.1.9-43", "Download Crafty Server 0.1.9-44")
    text = text.replace("Amber-and-Arcana-0.1.9-43-", "Amber-and-Arcana-0.1.9-44-")
    text = text.replace("| Pack | 0.1.9-43 |", "| Pack | 0.1.9-44 |")
    text = text.replace("scripts/update-crafty-0.1.9-43.py", "scripts/update-crafty-0.1.9-44.py")
    if "### 0.1.9-44 quest-cycle repair" not in text:
        text += "\n\n### 0.1.9-44 quest-cycle repair\nRepairs circular FTB Quests dependency paths that could recurse through `TeamData.isExcludedByOtherQuestline()` until the dedicated server crashed. Quest IDs and world/player data are preserved. The build now validates the complete dependency graph as acyclic before packaging.\n"
    README.write_text(text)

    text = CHANGELOG.read_text()
    if "## 0.1.9-44" not in text:
        CHANGELOG.write_text(
            "## 0.1.9-44\n\n"
            "- Repair circular FTB Quests dependency paths that caused recursive `isExcludedByOtherQuestline` crashes.\n"
            "- Preserve all quest IDs and player/team quest progress; only cycle-closing dependency edges are removed.\n"
            "- Add a build-time directed-cycle validator so cyclic quest graphs cannot be packaged again.\n\n"
            + text
        )


def main() -> None:
    removed = repair_cycles()
    sync_server()
    if find_cycle(load_graph()):
        raise RuntimeError("Quest dependency cycle remains after repair")
    update_release_metadata(removed)
    print(f"Prepared {VERSION}; removed {len(removed)} cycle-closing dependency edge(s).")


if __name__ == "__main__":
    main()
