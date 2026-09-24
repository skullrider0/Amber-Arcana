#!/usr/bin/env python3
"""Add the Energized Steel block batch recipe for 0.1.9-60."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-60"
RECIPE = {
    "type": "powah:energizing",
    "ingredients": [
        {"item": "minecraft:iron_block"},
        {"item": "minecraft:gold_block"},
    ],
    "energy": 90000,
    "result": {"item": "powah:energized_steel_block", "count": 2},
}


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    relative = Path("amber_arcana/recipes/powah/energizing/energized_steel_block_bulk.json")
    for root in (ROOT / "client/overrides/kubejs/data", ROOT / "server/kubejs/data"):
        dump(root / relative, RECIPE)

    marker = {
        "enabled": True,
        "iron_blocks": 1,
        "gold_blocks": 1,
        "energized_steel_blocks": 2,
        "energy": 90000,
        "equivalent_single_crafts": 9,
        "world_data_touched": False,
    }
    for relative_path in (
        "server/_crafty/build-summary.json",
        "client/overrides/pack-information/validation.json",
        "server/pack-information/validation.json",
    ):
        path = ROOT / relative_path
        data = json.loads(path.read_text(encoding="utf-8"))
        if relative_path.endswith("build-summary.json"):
            data["version"] = VERSION
            data["pack_version"] = VERSION
        else:
            data["pack_version"] = VERSION
        data["powah_energized_steel_block_0_1_9_60"] = marker
        dump(path, data)

    manifest = ROOT / "client/manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["version"] = VERSION
    data["name"] = "Amber & Arcana " + VERSION
    dump(manifest, data)

    modlist = ROOT / "client/modlist.html"
    text = re.sub(r"Amber &amp; Arcana 0\.1\.9-\d+", f"Amber &amp; Arcana {VERSION}", modlist.read_text(encoding="utf-8"))
    modlist.write_text(text, encoding="utf-8")

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8").replace("0.1.9-59", VERSION)
    note = """### 0.1.9-60 Powah Energized Steel block recipe
Adds a bulk Energizing Orb recipe converting one Iron Block and one Gold Block into two Energized Steel Blocks for 90,000 FE, exactly matching nine normal Energized Steel crafts.
"""
    if "### 0.1.9-60 Powah Energized Steel block recipe" not in text:
        text = text.rstrip() + "\n\n" + note
    readme.write_text(text, encoding="utf-8")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    if "## 0.1.9-60" not in text:
        text = """## 0.1.9-60 — Powah Energized Steel block recipe

- Add `1 Iron Block + 1 Gold Block -> 2 Energized Steel Blocks` in the Energizing Orb.
- Use 90,000 FE, exactly nine times Powah's standard 10,000 FE recipe.
- Keep Powah's original Nitro recipe yielding 16 Nitro Crystals.
- Client and server receive identical recipe data; no world or player data is changed.

""" + text
    changelog.write_text(text, encoding="utf-8")

    validator = ROOT / "scripts/validate.sh"
    text = validator.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-59"', '.version == "0.1.9-60"', 1)
    text = text.replace('.pack_version == "0.1.9-59"', '.pack_version == "0.1.9-60"', 1)
    text = text.replace('= "69" || { echo "Expected 69 recipe compatibility files"', '= "70" || { echo "Expected 70 recipe compatibility files"', 1)
    text = text.replace("Amber & Arcana 0.1.9-59 static validation passed", "Amber & Arcana 0.1.9-60 static validation passed", 1)
    text = text.replace(')" = "3" || { echo "Crafty update overlay missing Powah block recipes"', ')" = "4" || { echo "Crafty update overlay missing Powah block recipes"')
    if "# 0.1.9-60 Powah Energized Steel block recipe checks" not in text:
        text += r'''

# 0.1.9-60 Powah Energized Steel block recipe checks
jq -e '.ingredients == [{"item":"minecraft:iron_block"},{"item":"minecraft:gold_block"}] and .energy == 90000 and .result == {"item":"powah:energized_steel_block","count":2}' "$powah_recipes/energized_steel_block_bulk.json" >/dev/null
jq -e '.powah_energized_steel_block_0_1_9_60.enabled == true and .powah_energized_steel_block_0_1_9_60.energized_steel_blocks == 2 and .powah_energized_steel_block_0_1_9_60.energy == 90000 and .powah_energized_steel_block_0_1_9_60.world_data_touched == false' "$validation" >/dev/null
'''
    validator.write_text(text, encoding="utf-8")

    old_updater = ROOT / "scripts/update-crafty-0.1.9-59.py"
    new_updater = ROOT / f"scripts/update-crafty-{VERSION}.py"
    text = old_updater.read_text(encoding="utf-8").replace("0.1.9-59", VERSION)
    new_updater.write_text(text, encoding="utf-8")

    print(f"Prepared Amber & Arcana {VERSION}: Energized Steel block batch recipe")


if __name__ == "__main__":
    main()
