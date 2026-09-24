#!/usr/bin/env python3
"""Add bulk Powah crystal-block Energizing recipes for 0.1.9-58."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-58"

RECIPES = {
    "blazing_crystal_block_bulk.json": {
        "type": "powah:energizing",
        "ingredients": [{"item": "botania:blaze_block"}],
        "energy": 810000,
        "result": {"item": "powah:blazing_crystal_block"},
    },
    "niotic_crystal_block_bulk.json": {
        "type": "powah:energizing",
        "ingredients": [{"item": "minecraft:diamond_block"}],
        "energy": 2700000,
        "result": {"item": "powah:niotic_crystal_block"},
    },
    "spirited_crystal_block_bulk.json": {
        "type": "powah:energizing",
        "ingredients": [{"item": "minecraft:emerald_block"}],
        "energy": 9000000,
        "result": {"item": "powah:spirited_crystal_block"},
    },
    "nitro_crystal_block_bulk.json": {
        "type": "powah:energizing",
        "ingredients": [
            {"item": "minecraft:nether_star"},
            {"item": "minecraft:redstone_block"},
            {"item": "minecraft:redstone_block"},
            {"item": "powah:blazing_crystal_block"},
        ],
        "energy": 20000000,
        "result": {"item": "powah:nitro_crystal_block"},
    },
}


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    for root in (ROOT / "client/overrides/kubejs/data", ROOT / "server/kubejs/data"):
        recipe_root = root / "amber_arcana/recipes/powah/energizing"
        for name, recipe in RECIPES.items():
            dump(recipe_root / name, recipe)

    marker = {
        "enabled": True,
        "energizing_recipes_added": len(RECIPES),
        "blazing_bulk_input": "botania:blaze_block",
        "client_server_recipe_data_identical": True,
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
        data["powah_block_recipes_0_1_9_58"] = marker
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
    text = text.replace("Amber-and-Arcana-0.1.9-57", f"Amber-and-Arcana-{VERSION}")
    text = text.replace("Download Client 0.1.9-57", f"Download Client {VERSION}")
    text = text.replace("Download Crafty Server 0.1.9-57", f"Download Crafty Server {VERSION}")
    text = text.replace("scripts/update-crafty-0.1.9-49.py", f"scripts/update-crafty-{VERSION}.py")
    text = re.sub(r"\| Pack \| 0\.1\.9-\d+ \|", f"| Pack | {VERSION} |", text)
    note = """### 0.1.9-58 Powah bulk crystal-block recipes
Adds direct Energizing Orb recipes for Blazing, Niotic, Spirited, and Nitro crystal blocks. The Blazing recipe uses Botania's Blaze Mesh (`botania:blaze_block`). Client and server recipe data are identical; no world or player data is changed.
"""
    text = re.sub(r"\n### 0\.1\.9-58[^\n]*\n.*?(?=\n### |\Z)", "", text, flags=re.S)
    readme.write_text(text.rstrip() + "\n\n" + note, encoding="utf-8")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    text = text.replace("## Unreleased — Powah bulk crystal-block recipes", "## 0.1.9-58 — Powah bulk crystal-block recipes", 1)
    changelog.write_text(text, encoding="utf-8")

    updater = ROOT / f"scripts/update-crafty-{VERSION}.py"
    if not updater.exists():
        updater.write_text(
            "#!/usr/bin/env python3\n"
            f'"""Crafty updater for Amber & Arcana {VERSION}."""\n'
            "from pathlib import Path\n\n"
            '_source = Path(__file__).with_name("update-crafty-0.1.9-57.py").read_text(encoding="utf-8")\n'
            f'_source = _source.replace("VERSION = \'0.1.9-57\'", "VERSION = \'{VERSION}\'", 1)\n'
            f'_source = _source.replace("matching 0.1.9-57 Client ZIP", "matching {VERSION} Client ZIP", 1)\n'
            'exec(compile(_source, str(Path(__file__)), "exec"), globals())\n',
            encoding="utf-8",
        )

    validator = ROOT / "scripts/validate.sh"
    text = validator.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-57"', '.version == "0.1.9-58"', 1)
    text = text.replace('.pack_version == "0.1.9-57"', '.pack_version == "0.1.9-58"', 1)
    text = text.replace("Amber & Arcana 0.1.9-57 static validation passed", "Amber & Arcana 0.1.9-58 static validation passed", 1)
    if "# 0.1.9-58 Powah bulk crystal-block recipe checks" not in text:
        text += r'''

# 0.1.9-58 Powah bulk crystal-block recipe checks
powah_recipes="$server_data/amber_arcana/recipes/powah/energizing"
jq -e '.ingredients == [{"item":"botania:blaze_block"}] and .energy == 810000 and .result.item == "powah:blazing_crystal_block"' "$powah_recipes/blazing_crystal_block_bulk.json" >/dev/null
jq -e '.ingredients == [{"item":"minecraft:diamond_block"}] and .energy == 2700000 and .result.item == "powah:niotic_crystal_block"' "$powah_recipes/niotic_crystal_block_bulk.json" >/dev/null
jq -e '.ingredients == [{"item":"minecraft:emerald_block"}] and .energy == 9000000 and .result.item == "powah:spirited_crystal_block"' "$powah_recipes/spirited_crystal_block_bulk.json" >/dev/null
jq -e '.energy == 20000000 and .result.item == "powah:nitro_crystal_block"' "$powah_recipes/nitro_crystal_block_bulk.json" >/dev/null
jq -e '.powah_block_recipes_0_1_9_58.enabled == true and .powah_block_recipes_0_1_9_58.energizing_recipes_added == 4 and .powah_block_recipes_0_1_9_58.blazing_bulk_input == "botania:blaze_block" and .powah_block_recipes_0_1_9_58.world_data_touched == false' "$validation" >/dev/null
test "$(unzip -Z1 "$overlay" | grep -Ec '^kubejs/data/amber_arcana/recipes/powah/energizing/.+\.json$')" = "4" || { echo "Crafty update overlay missing Powah block recipes" >&2; exit 1; }
'''
    validator.write_text(text, encoding="utf-8")

    print(f"Prepared Amber & Arcana {VERSION}: Powah bulk crystal-block recipes")


if __name__ == "__main__":
    main()
