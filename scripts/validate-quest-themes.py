#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "client/overrides/config/ftbquests/quests"
SERVER = ROOT / "server/config/ftbquests/quests"
CHAPTERS = CLIENT / "chapters"
TABLES = CLIENT / "reward_tables"
MARKER = "AA35 deep progression milestone"

spec = importlib.util.spec_from_file_location("aa45", ROOT / "scripts/hotfix-quest-curation-0.1.9-45.py")
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load 0.1.9-45 quest theme rules")
aa45 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aa45)

errors: list[str] = []
chapter_files = sorted(CHAPTERS.glob("*.snbt"))
server_chapters = SERVER / "chapters"

for path in chapter_files:
    text = path.read_text()
    if MARKER in text:
        errors.append(f"{path.name}: generated AA35 filler marker remains")
    peer = server_chapters / path.name
    if not peer.exists():
        errors.append(f"{path.name}: missing server copy")
    elif peer.read_bytes() != path.read_bytes():
        errors.append(f"{path.name}: client/server quest source differs")

# Only per-chapter tier tables and finale wheels are theme-constrained. Shared or
# special-purpose tables are left to their dedicated validators. Vanilla support
# items are permitted; unrelated mod namespaces are not.
checked = 0
for path in sorted(TABLES.glob("modroll_*_tier_*.snbt")) + sorted(TABLES.glob("wheel_*.snbt")):
    name = path.stem
    if name.startswith("modroll_"):
        m = re.match(r"modroll_(.+)_tier_[1-4]$", name)
        stem = m.group(1) if m else ""
    else:
        stem = name.removeprefix("wheel_")
    if stem not in aa45.THEMES:
        continue
    entries = aa45.parse_reward_entries(path.read_text())
    if not entries:
        errors.append(f"{path.name}: no weighted item rewards")
        continue
    checked += 1
    for _count, item, _weight in entries:
        if aa45.namespace(item) == "minecraft":
            continue
        if not aa45.allowed(stem, item):
            errors.append(f"{path.name}: unrelated reward {item} is outside theme {sorted(aa45.THEMES[stem])}")

if errors:
    print("Amber & Arcana quest-theme validation FAILED")
    for err in errors[:100]:
        print(f" - {err}")
    if len(errors) > 100:
        print(f" - ... and {len(errors) - 100} more")
    raise SystemExit(1)

print(f"Amber & Arcana quest-theme validation passed: {len(chapter_files)} chapters, {checked} themed reward tables, no AA35 filler markers or reward leakage")
