#!/usr/bin/env python3
"""Validate that Amber & Arcana's FTB Quests dependency graph is acyclic."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "client/overrides/config/ftbquests/quests/chapters"
SERVER = ROOT / "server/config/ftbquests/quests/chapters"

ID_RE = re.compile(r'^\t\t\tid:\s*"([0-9A-F]{16})"\s*$', re.M)
TITLE_RE = re.compile(r'^\t\t\ttitle:\s*"([^"]*)"\s*$', re.M)
DEPS_RE = re.compile(r'^\t\t\tdependencies:\s*\[(.*?)\]\s*$', re.M)
HEX_RE = re.compile(r'"([0-9A-F]{16})"')


@dataclass(frozen=True)
class Quest:
    qid: str
    title: str
    chapter: str
    deps: tuple[str, ...]


def split_quest_blocks(text: str) -> list[str]:
    lines = text.splitlines(keepends=True)
    in_quests = False
    current: list[str] | None = None
    blocks: list[str] = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not in_quests:
            if line.strip() == "quests: [":
                in_quests = True
            continue
        if current is None:
            if re.match(r'^\t\t\{\s*$', line):
                current = [raw]
                continue
            if re.match(r'^\t\],?\s*$', line):
                break
            continue
        current.append(raw)
        if re.match(r'^\t\t\},?\s*$', line):
            blocks.append("".join(current))
            current = None
    return blocks


def load_graph(chapters: Path) -> dict[str, Quest]:
    quests: dict[str, Quest] = {}
    for path in sorted(chapters.glob("*.snbt")):
        for block in split_quest_blocks(path.read_text()):
            mid = ID_RE.search(block)
            if not mid:
                continue
            qid = mid.group(1)
            if qid in quests:
                raise RuntimeError(f"duplicate quest id {qid}: {path.name} and {quests[qid].chapter}")
            mtitle = TITLE_RE.search(block)
            mdeps = DEPS_RE.search(block)
            deps = tuple(HEX_RE.findall(mdeps.group(1))) if mdeps else ()
            quests[qid] = Quest(qid, mtitle.group(1) if mtitle else qid, path.name, deps)
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


def validate_one(label: str, chapters: Path) -> dict[str, Quest]:
    graph = load_graph(chapters)
    cycle = find_cycle(graph)
    if cycle:
        print(f"{label} quest dependency cycle detected:", file=sys.stderr)
        for a, b in zip(cycle, cycle[1:]):
            qa, qb = graph[a], graph[b]
            print(f"  {qa.chapter}:{qa.title} ({a}) -> {qb.chapter}:{qb.title} ({b})", file=sys.stderr)
        raise SystemExit(1)
    print(f"{label}: {len(graph)} quests, dependency graph is acyclic")
    return graph


def main() -> None:
    client = validate_one("client", CLIENT)
    server = validate_one("server", SERVER)
    if set(client) != set(server):
        raise SystemExit("client/server quest ID sets differ")
    for qid, q in client.items():
        other = server[qid]
        if q.deps != other.deps:
            raise SystemExit(f"client/server dependencies differ for quest {qid}")
    print("Amber & Arcana FTB Quests graph validation passed")


if __name__ == "__main__":
    main()
