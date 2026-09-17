#!/usr/bin/env python3
"""Validate Amber & Arcana's FTB Quests dependency graph and recursion depth."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "client/overrides/config/ftbquests/quests/chapters"
SERVER = ROOT / "server/config/ftbquests/quests/chapters"

# FTB Quests' SNBT writer legitimately emits both `id: "..."` and
# `id: "...",`. Keep the indentation constraint so nested task/reward IDs are
# not mistaken for quest IDs, but accept the optional trailing comma.
ID_RE = re.compile(r'^\t\t\tid:\s*"([0-9A-Fa-f]{16})"\s*,?\s*$', re.M)
TITLE_RE = re.compile(r'^\t\t\ttitle:\s*"([^"]*)"\s*,?\s*$', re.M)
DEPS_RE = re.compile(r'^\t\t\tdependencies:\s*\[(.*?)\]', re.M | re.S)
HEX_RE = re.compile(r'"([0-9A-Fa-f]{16})"')


@dataclass(frozen=True)
class Quest:
    qid: str
    title: str
    chapter: str
    deps: tuple[str, ...]


def split_quest_blocks(text: str) -> list[str]:
    """Extract top-level objects from the SNBT quests list using nesting, not indentation."""
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


def load_graph(chapters: Path) -> dict[str, Quest]:
    quests: dict[str, Quest] = {}
    for path in sorted(chapters.glob("*.snbt")):
        blocks = split_quest_blocks(path.read_text())
        for block in blocks:
            mid = ID_RE.search(block)
            if not mid:
                raise RuntimeError(f"could not read top-level quest ID in {path.name}")
            qid = mid.group(1).upper()
            if qid in quests:
                raise RuntimeError(f"duplicate quest id {qid}: {path.name} and {quests[qid].chapter}")
            mtitle = TITLE_RE.search(block)
            mdeps = DEPS_RE.search(block)
            deps = tuple(x.upper() for x in HEX_RE.findall(mdeps.group(1))) if mdeps else ()
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


def longest_path(graph: dict[str, Quest]) -> list[str]:
    memo: dict[str, list[str]] = {}

    def path_from(qid: str) -> list[str]:
        if qid in memo:
            return memo[qid]
        candidates = [path_from(dep) for dep in graph[qid].deps if dep in graph]
        best = max(candidates, key=len) if candidates else []
        memo[qid] = [qid] + best
        return memo[qid]

    return max((path_from(qid) for qid in graph), key=len, default=[])


def validate_one(label: str, chapters: Path) -> dict[str, Quest]:
    graph = load_graph(chapters)
    cycle = find_cycle(graph)
    if cycle:
        print(f"{label} quest dependency cycle detected:", file=sys.stderr)
        for a, b in zip(cycle, cycle[1:]):
            qa, qb = graph[a], graph[b]
            print(f"  {qa.chapter}:{qa.title} ({a}) -> {qb.chapter}:{qb.title} ({b})", file=sys.stderr)
        raise SystemExit(1)

    path = longest_path(graph)
    edges = sum(sum(dep in graph for dep in q.deps) for q in graph.values())
    cross = sum(sum(dep in graph and graph[dep].chapter != q.chapter for dep in q.deps) for q in graph.values())
    unresolved = sorted({dep for q in graph.values() for dep in q.deps if dep not in graph})
    print(f"{label}: {len(graph)} quests, {edges} quest edges, {cross} cross-chapter edges, acyclic")
    print(f"{label}: maximum recursive quest dependency depth = {len(path)}")
    if path:
        print(f"{label}: longest path = " + " -> ".join(
            f"{graph[qid].chapter}:{graph[qid].title}({qid})" for qid in path
        ))
    if unresolved:
        print(f"{label}: {len(unresolved)} dependency ID(s) resolve outside the quest set: " + ", ".join(unresolved))
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
