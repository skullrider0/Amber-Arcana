#!/usr/bin/env python3
"""Remove the conflicting Nitro block Energizing recipe for 0.1.9-59."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-59"
NITRO_RECIPE = Path("amber_arcana/recipes/powah/energizing/nitro_crystal_block_bulk.json")


def dump(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    for root in (ROOT / "client/overrides/kubejs/data", ROOT / "server/kubejs/data"):
        (root / NITRO_RECIPE).unlink(missing_ok=True)

    marker = {
        "enabled": True,
        "conflicting_nitro_block_recipe_removed": True,
        "powah_default_nitro_output_preserved": 16,
        "remaining_bulk_block_recipes": 3,
        "world_data_touched": False,
    }
    for relative in (
        "server/_crafty/build-summary.json",
        "client/overrides/pack-information/validation.json",
        "server/pack-information/validation.json",
    ):
        path = ROOT / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        if relative.endswith("build-summary.json"):
            data["version"] = VERSION
            data["pack_version"] = VERSION
        else:
            data["pack_version"] = VERSION
        data["powah_nitro_recipe_fix_0_1_9_59"] = marker
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
    text = readme.read_text(encoding="utf-8")
    text = text.replace("0.1.9-58", VERSION)
    note = """### 0.1.9-59 Powah Nitro recipe correction
Removes the custom Nitro Crystal Block Energizing recipe because it duplicated Powah's standard inputs while returning only nine crystals' worth instead of the standard sixteen. Powah's original 16 Nitro Crystal output remains intact. The non-conflicting Blazing, Niotic, and Spirited block recipes remain.
"""
    if "### 0.1.9-59 Powah Nitro recipe correction" not in text:
        text = text.rstrip() + "\n\n" + note
    readme.write_text(text, encoding="utf-8")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    if "## 0.1.9-59" not in text:
        text = """## 0.1.9-59 — Powah Nitro recipe correction

- Remove the conflicting Nitro Crystal Block Energizing recipe from 0.1.9-58.
- Preserve Powah's standard recipe yielding 16 Nitro Crystals from its original inputs.
- Retain the non-conflicting Blazing, Niotic, and Spirited bulk block recipes.
- Client and server receive identical recipe data; no world or player data is changed.

""" + text
    changelog.write_text(text, encoding="utf-8")

    validator = ROOT / "scripts/validate.sh"
    text = validator.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-58"', '.version == "0.1.9-59"', 1)
    text = text.replace('.pack_version == "0.1.9-58"', '.pack_version == "0.1.9-59"', 1)
    text = text.replace('= "70" || { echo "Expected 70 recipe compatibility files"', '= "69" || { echo "Expected 69 recipe compatibility files"', 1)
    text = text.replace("Amber & Arcana 0.1.9-58 static validation passed", "Amber & Arcana 0.1.9-59 static validation passed", 1)
    text = text.replace("jq -e '.energy == 20000000 and .result.item == \"powah:nitro_crystal_block\"' \"$powah_recipes/nitro_crystal_block_bulk.json\" >/dev/null\n", "")
    text = text.replace(')" = "4" || { echo "Crafty update overlay missing Powah block recipes"', ')" = "3" || { echo "Crafty update overlay missing Powah block recipes"')
    if "# 0.1.9-59 Powah Nitro recipe correction checks" not in text:
        text += r'''

# 0.1.9-59 Powah Nitro recipe correction checks
test ! -e "$client_data/amber_arcana/recipes/powah/energizing/nitro_crystal_block_bulk.json" || { echo "Conflicting client Nitro block recipe remains" >&2; exit 1; }
test ! -e "$server_data/amber_arcana/recipes/powah/energizing/nitro_crystal_block_bulk.json" || { echo "Conflicting server Nitro block recipe remains" >&2; exit 1; }
jq -e '.powah_nitro_recipe_fix_0_1_9_59.conflicting_nitro_block_recipe_removed == true and .powah_nitro_recipe_fix_0_1_9_59.powah_default_nitro_output_preserved == 16 and .powah_nitro_recipe_fix_0_1_9_59.world_data_touched == false' "$validation" >/dev/null
'''
    validator.write_text(text, encoding="utf-8")

    old_updater = ROOT / "scripts/update-crafty-0.1.9-58.py"
    new_updater = ROOT / f"scripts/update-crafty-{VERSION}.py"
    text = old_updater.read_text(encoding="utf-8")
    text = text.replace("0.1.9-58", VERSION)
    new_updater.write_text(text, encoding="utf-8")

    print(f"Prepared Amber & Arcana {VERSION}: removed conflicting Nitro block recipe")


if __name__ == "__main__":
    main()
