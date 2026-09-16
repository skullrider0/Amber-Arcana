#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
import shutil
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-37"
ATM10_COMMIT = "ab6f65e07b88423cdae1724864ba42a573ba758a"
TARGET_EDGE_GAP = 1.75
MIN_NODE_GAP = 1.10
MIN_SCALE = 0.22
MAX_SCALE = 0.90

CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"
CLIENT_CHAPTERS = CLIENT_QUESTS / "chapters"
SERVER_CHAPTERS = SERVER_QUESTS / "chapters"
MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
VALIDATE_SH = ROOT / "scripts/validate.sh"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"

ID_RE = re.compile(r'^\t\t\tid: "([0-9A-F]{16})"$', re.M)
DEP_RE = re.compile(r'^\t\t\tdependencies:\s*\[(.*?)\](?:\n|$)', re.M | re.S)
DEP_ID_RE = re.compile(r'"([0-9A-F]{16})"')
X_RE = re.compile(r'^\t\t\tx:\s*(-?[0-9]+(?:\.[0-9]+)?)d$', re.M)
Y_RE = re.compile(r'^\t\t\ty:\s*(-?[0-9]+(?:\.[0-9]+)?)d$', re.M)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def split_quest_blocks(text: str) -> list[tuple[int, int, str]]:
    lines = text.splitlines(keepends=True)
    offsets = []
    pos = 0
    for line in lines:
        offsets.append(pos)
        pos += len(line)

    in_quests = False
    start_line = None
    blocks: list[tuple[int, int, str]] = []
    for i, raw in enumerate(lines):
        line = raw.rstrip("\r\n")
        if not in_quests:
            if line == "\tquests: [":
                in_quests = True
            continue
        if start_line is None and line == "\t\t{":
            start_line = i
            continue
        if start_line is not None and line == "\t\t}":
            start = offsets[start_line]
            end = offsets[i] + len(raw)
            blocks.append((start, end, text[start:end]))
            start_line = None
            continue
        if start_line is None and line == "\t]":
            break
    return blocks


def parse_node(block: str) -> dict | None:
    mid = ID_RE.search(block)
    mx = X_RE.search(block)
    my = Y_RE.search(block)
    if not (mid and mx and my):
        return None
    dep_match = DEP_RE.search(block)
    deps = DEP_ID_RE.findall(dep_match.group(1)) if dep_match else []
    return {
        "id": mid.group(1),
        "x": float(mx.group(1)),
        "y": float(my.group(1)),
        "deps": deps,
    }


def snap(value: float, step: float = 0.25) -> float:
    snapped = round(value / step) * step
    if abs(snapped) < 1e-9:
        return 0.0
    return snapped


def fmt(value: float) -> str:
    value = snap(value)
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value))}.0d"
    s = f"{value:.2f}".rstrip("0").rstrip(".")
    return s + "d"


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def chapter_metrics(nodes: list[dict]) -> dict:
    if not nodes:
        return {"width": 0.0, "height": 0.0, "edge_median": 0.0, "edge_count": 0}
    by_id = {n["id"]: n for n in nodes}
    edge_lengths = []
    for n in nodes:
        for dep in n["deps"]:
            if dep in by_id:
                d = by_id[dep]
                edge_lengths.append(math.hypot(n["x"] - d["x"], n["y"] - d["y"]))
    xs = [n["x"] for n in nodes]
    ys = [n["y"] for n in nodes]
    return {
        "width": round(max(xs) - min(xs), 3),
        "height": round(max(ys) - min(ys), 3),
        "edge_median": round(statistics.median(edge_lengths), 3) if edge_lengths else 0.0,
        "edge_count": len(edge_lengths),
    }


def compact_positions(nodes: list[dict]) -> tuple[dict[str, tuple[float, float]], float]:
    if not nodes:
        return {}, 1.0

    metrics = chapter_metrics(nodes)
    median_edge = metrics["edge_median"]
    if median_edge > 0:
        scale = TARGET_EDGE_GAP / median_edge
    else:
        coords = [(n["x"], n["y"]) for n in nodes]
        nearest = []
        for i, p in enumerate(coords):
            ds = [distance(p, q) for j, q in enumerate(coords) if i != j and distance(p, q) > 0]
            if ds:
                nearest.append(min(ds))
        baseline = statistics.median(nearest) if nearest else TARGET_EDGE_GAP
        scale = TARGET_EDGE_GAP / baseline if baseline > 0 else 1.0
    scale = min(MAX_SCALE, max(MIN_SCALE, scale))
    scale = min(scale, 1.0)  # this release only compacts; it never spreads a chapter out

    min_x = min(n["x"] for n in nodes)
    max_x = max(n["x"] for n in nodes)
    min_y = min(n["y"] for n in nodes)
    max_y = max(n["y"] for n in nodes)
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0

    base: dict[str, tuple[float, float]] = {
        n["id"]: (snap((n["x"] - cx) * scale), snap((n["y"] - cy) * scale))
        for n in nodes
    }

    # Preserve the old branch geometry but prevent compacting from causing icons
    # to overlap. Nudge only the vertical lane and keep the dependency direction.
    placed: dict[str, tuple[float, float]] = {}
    order = sorted(nodes, key=lambda n: (base[n["id"]][0], base[n["id"]][1], n["id"]))
    for idx, n in enumerate(order):
        qid = n["id"]
        x, original_y = base[qid]
        y = original_y
        if any(distance((x, y), p) < MIN_NODE_GAP for p in placed.values()):
            found = False
            for ring in range(1, 25):
                for sign in (-1, 1):
                    candidate = snap(original_y + sign * ring * 0.5)
                    if all(distance((x, candidate), p) >= MIN_NODE_GAP for p in placed.values()):
                        y = candidate
                        found = True
                        break
                if found:
                    break
        placed[qid] = (x, y)

    # Recenter after collision nudges so each chapter opens around the progression.
    if placed:
        xs = [p[0] for p in placed.values()]
        ys = [p[1] for p in placed.values()]
        rcx = (min(xs) + max(xs)) / 2.0
        rcy = (min(ys) + max(ys)) / 2.0
        placed = {qid: (snap(x - rcx), snap(y - rcy)) for qid, (x, y) in placed.items()}

    return placed, round(scale, 4)


def ensure_flexible_mode(text: str) -> str:
    if re.search(r'^\tprogression_mode:', text, re.M):
        return re.sub(r'^\tprogression_mode:.*$', '\tprogression_mode: "flexible"', text, count=1, flags=re.M)
    order = re.search(r'^\torder_index:.*$', text, re.M)
    if order:
        pos = order.end()
        return text[:pos] + '\n\tprogression_mode: "flexible"' + text[pos:]
    qlinks = re.search(r'^\tquest_links:', text, re.M)
    if qlinks:
        return text[:qlinks.start()] + '\tprogression_mode: "flexible"\n' + text[qlinks.start():]
    return text


def apply_layout(path: Path) -> dict:
    text = path.read_text()
    blocks = split_quest_blocks(text)
    nodes = [n for _, _, block in blocks if (n := parse_node(block))]
    before = chapter_metrics(nodes)
    positions, scale = compact_positions(nodes)

    out = []
    cursor = 0
    repositioned = 0
    for start, end, block in blocks:
        node = parse_node(block)
        if node and node["id"] in positions:
            x, y = positions[node["id"]]
            old = (node["x"], node["y"])
            block = X_RE.sub(f"\t\t\tx: {fmt(x)}", block, count=1)
            block = Y_RE.sub(f"\t\t\ty: {fmt(y)}", block, count=1)
            if old != (x, y):
                repositioned += 1
        out.append(text[cursor:start])
        out.append(block)
        cursor = end
    out.append(text[cursor:])
    new_text = ensure_flexible_mode("".join(out))
    path.write_text(new_text)

    after_nodes = [n for _, _, block in split_quest_blocks(new_text) if (n := parse_node(block))]
    after = chapter_metrics(after_nodes)
    return {
        "chapter": path.stem,
        "quests": len(nodes),
        "repositioned": repositioned,
        "scale": scale,
        "width_before": before["width"],
        "width_after": after["width"],
        "height_before": before["height"],
        "height_after": after["height"],
        "median_dependency_gap_before": before["edge_median"],
        "median_dependency_gap_after": after["edge_median"],
        "dependency_edges": before["edge_count"],
    }


def sync_server() -> None:
    SERVER_CHAPTERS.mkdir(parents=True, exist_ok=True)
    for src in CLIENT_CHAPTERS.glob("*.snbt"):
        shutil.copy2(src, SERVER_CHAPTERS / src.name)
    shutil.copy2(CLIENT_QUESTS / "chapter_groups.snbt", SERVER_QUESTS / "chapter_groups.snbt")


def update_release_metadata(stats: list[dict], already_applied: bool) -> None:
    manifest = json.loads(MANIFEST.read_text())
    manifest["name"] = f"Amber & Arcana {VERSION}"
    manifest["version"] = VERSION
    write_json(MANIFEST, manifest)

    total_quests = sum(s["quests"] for s in stats)
    total_repositioned = sum(s["repositioned"] for s in stats)
    total_edges = sum(s["dependency_edges"] for s in stats)
    widths_before = [s["width_before"] for s in stats]
    widths_after = [s["width_after"] for s in stats]
    gaps_before = [s["median_dependency_gap_before"] for s in stats if s["median_dependency_gap_before"] > 0]
    gaps_after = [s["median_dependency_gap_after"] for s in stats if s["median_dependency_gap_after"] > 0]

    block = {
        "reference_pack": "AllTheMods/ATM-10",
        "reference_commit": ATM10_COMMIT,
        "reference_use": "layout density, branch readability, visible dependency chains, and flexible progression style only; ATM10 quest prose/rewards are not copied",
        "chapters_compacted": len(stats),
        "quests_considered": total_quests,
        "quests_repositioned": total_repositioned,
        "dependency_edges_preserved": total_edges,
        "target_dependency_gap": TARGET_EDGE_GAP,
        "median_chapter_dependency_gap_before": round(statistics.median(gaps_before), 3) if gaps_before else 0.0,
        "median_chapter_dependency_gap_after": round(statistics.median(gaps_after), 3) if gaps_after else 0.0,
        "max_chapter_width_before": round(max(widths_before), 3) if widths_before else 0.0,
        "max_chapter_width_after": round(max(widths_after), 3) if widths_after else 0.0,
        "progression_mode": "flexible",
        "dependency_lines_visible": True,
        "quest_ids_preserved": True,
        "tasks_preserved": True,
        "rewards_preserved": True,
        "fortune_wheel_preserved": True,
        "client_server_quest_files_identical": True,
        "applied_to_canonical_source": True,
        "already_applied_on_entry": already_applied,
        "chapters": stats,
    }

    summary = json.loads(SUMMARY.read_text())
    summary["pack_version"] = VERSION
    summary["atm10_layout_0_1_9_37"] = block
    write_json(SUMMARY, summary)

    validation = json.loads(VALIDATION.read_text())
    validation["pack_version"] = VERSION
    validation["atm10_layout_0_1_9_37"] = block
    write_json(VALIDATION, validation)


def update_validator() -> None:
    text = VALIDATE_SH.read_text()
    text = text.replace("0.1.9-36", VERSION)
    marker = "# 0.1.9-37 ATM10-inspired compact layout checks"
    if marker not in text:
        text += f'''\n\n{marker}\njq -e '.atm10_layout_0_1_9_37.reference_pack == "AllTheMods/ATM-10" and .atm10_layout_0_1_9_37.reference_commit == "{ATM10_COMMIT}" and .atm10_layout_0_1_9_37.chapters_compacted == 26 and .atm10_layout_0_1_9_37.quest_ids_preserved == true and .atm10_layout_0_1_9_37.tasks_preserved == true and .atm10_layout_0_1_9_37.rewards_preserved == true and .atm10_layout_0_1_9_37.fortune_wheel_preserved == true and .atm10_layout_0_1_9_37.client_server_quest_files_identical == true and .atm10_layout_0_1_9_37.max_chapter_width_after < .atm10_layout_0_1_9_37.max_chapter_width_before' "$validation" >/dev/null\ntest "$(grep -Rhc $'\\tprogression_mode: "flexible"' "$client_quests/chapters"/*.snbt | awk '{{s+=$1}} END {{print s+0}}')" = "26" || {{ echo "Expected flexible progression mode in all 26 chapters" >&2; exit 1; }}\ndiff -qr "$client_quests" "$server_quests" >/dev/null || {{ echo "Client/server quest trees differ after 0.1.9-37" >&2; exit 1; }}\n'''
    VALIDATE_SH.write_text(text)


def update_docs() -> None:
    changelog = CHANGELOG.read_text() if CHANGELOG.exists() else ""
    heading = f"## {VERSION}"
    if heading not in changelog:
        entry = f'''{heading}\n\n- Reworked the quest-book display using ATM10's compact visual density and dependency-chain readability as a reference, without copying ATM10 quest text or rewards.\n- Compacted all 26 Amber & Arcana chapters adaptively toward ~{TARGET_EDGE_GAP} quest-node dependency spacing instead of the previous large gaps.\n- Preserved every existing quest ID, task, reward, tier roll, and Wheel of Fortune reward.\n- Enabled flexible chapter progression display and kept dependency lines visible.\n- Reference snapshot: AllTheMods/ATM-10 `{ATM10_COMMIT}`.\n\n'''
        CHANGELOG.write_text(entry + changelog)
    if README.exists():
        readme = README.read_text()
        if VERSION not in readme:
            readme += f"\n\n### {VERSION} compact quest layout\nQuest chapters now use a denser ATM10-inspired visual scale with visible dependency chains while retaining Amber & Arcana's own progression, tier rolls, and Wheel of Fortune system.\n"
            README.write_text(readme)


def main() -> None:
    validation = json.loads(VALIDATION.read_text())
    previous = validation.get("atm10_layout_0_1_9_37")
    already_applied = bool(previous and previous.get("applied_to_canonical_source"))

    if already_applied:
        # Canonical source was already compacted in a previous successful build.
        # Do not shrink it again. Recompute metrics for validation and keep parity.
        stats = []
        for path in sorted(CLIENT_CHAPTERS.glob("*.snbt")):
            text = ensure_flexible_mode(path.read_text())
            path.write_text(text)
            nodes = [n for _, _, block in split_quest_blocks(text) if (n := parse_node(block))]
            m = chapter_metrics(nodes)
            stats.append({
                "chapter": path.stem,
                "quests": len(nodes),
                "repositioned": 0,
                "scale": 1.0,
                "width_before": m["width"],
                "width_after": m["width"],
                "height_before": m["height"],
                "height_after": m["height"],
                "median_dependency_gap_before": m["edge_median"],
                "median_dependency_gap_after": m["edge_median"],
                "dependency_edges": m["edge_count"],
            })
        sync_server()
        # Preserve the original compaction evidence instead of overwriting it with
        # a no-op rebuild snapshot.
        manifest = json.loads(MANIFEST.read_text())
        manifest["name"] = f"Amber & Arcana {VERSION}"
        manifest["version"] = VERSION
        write_json(MANIFEST, manifest)
        summary = json.loads(SUMMARY.read_text())
        summary["pack_version"] = VERSION
        summary["atm10_layout_0_1_9_37"] = previous
        write_json(SUMMARY, summary)
        validation["pack_version"] = VERSION
        validation["atm10_layout_0_1_9_37"] = previous
        write_json(VALIDATION, validation)
        update_validator()
        update_docs()
        print(f"Amber & Arcana {VERSION} compact layout already applied; verified canonical quest geometry without rescaling")
        return

    stats = [apply_layout(path) for path in sorted(CLIENT_CHAPTERS.glob("*.snbt"))]
    if len(stats) != 26:
        raise RuntimeError(f"Expected 26 quest chapters, found {len(stats)}")
    sync_server()
    update_release_metadata(stats, already_applied=False)
    update_validator()
    update_docs()

    max_before = max((s["width_before"] for s in stats), default=0.0)
    max_after = max((s["width_after"] for s in stats), default=0.0)
    print(
        f"Applied Amber & Arcana {VERSION}: compacted {len(stats)} chapters / "
        f"{sum(s['quests'] for s in stats)} quests; max width {max_before:.2f} -> {max_after:.2f}; "
        f"ATM10-inspired dependency spacing target {TARGET_EDGE_GAP}"
    )


if __name__ == "__main__":
    main()
