#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "client/overrides/config/ftbquests/quests/chapters"
TARGET = ROOT / "scripts/hotfix-deep-short-progression-0.1.9-35.py"


def repair_missing_loot_braces(text: str) -> tuple[str, int]:
    """Repair a 0.1.9-34 formatting defect in generated loot rewards.

    Affected quest files can contain a reward ending like:
        type: "loot"
      ]
    with the reward object's closing `}` missing. This made the quest array
    structurally unbalanced and prevented later deterministic quest parsing.
    Only this exact situation is repaired: a `]` whose previous nonblank line is
    a loot type field. Valid reward objects are untouched.
    """
    lines = text.splitlines()
    out: list[str] = []
    repairs = 0
    for line in lines:
        if line.strip() == "]":
            prev = next((candidate for candidate in reversed(out) if candidate.strip()), "")
            if prev.strip() == 'type: "loot"':
                prop_indent = prev[: len(prev) - len(prev.lstrip())]
                if prop_indent.endswith("\t"):
                    close_indent = prop_indent[:-1]
                elif len(prop_indent) >= 4:
                    close_indent = prop_indent[:-4]
                else:
                    close_indent = ""
                out.append(close_indent + "}")
                repairs += 1
        out.append(line)
    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(out) + trailing, repairs


repairs = 0
for path in sorted(CHAPTERS.glob("*.snbt")):
    text = path.read_text()
    fixed, count = repair_missing_loot_braces(text)
    if count:
        path.write_text(fixed)
        repairs += count

print(f"0.1.9-35 preflight repaired {repairs} legacy missing loot-reward braces")

spec = importlib.util.spec_from_file_location("aa_deep35", TARGET)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load 0.1.9-35 deep progression hotfix")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.main()
