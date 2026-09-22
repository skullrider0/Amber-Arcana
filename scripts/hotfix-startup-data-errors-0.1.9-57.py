#!/usr/bin/env python3
"""Second startup-log cleanup pass for Amber & Arcana 0.1.9-57."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-57"

BLOCK_LOOT = (
    "culturaldelights/loot_tables/blocks/exotic_roll_medley_block.json",
    "culturaldelights/loot_tables/blocks/fruiting_avocado_leaves.json",
    "culturaldelights/loot_tables/blocks/avocado_leaves.json",
    "farmersrespite/loot_tables/blocks/kettle.json",
    "butchery/loot_tables/blocks/chicken_cut_1_drop.json",
    "butchery_alexs_mobs/loot_tables/blocks/caiman_cut_1_drop.json",
    "butchery_alexs_mobs/loot_tables/blocks/caiman_cut_2_drop.json",
    "butchery_alexs_mobs/loot_tables/blocks/caiman_cut_3_drop.json",
)

DECOCRAFT_BLOCK_LOOT = tuple(
    f"decocraft/loot_tables/blocks/{name}.json"
    for name in (
        "china_cabinet_open_black", "china_cabinet_open_birch",
        "china_cabinet_open_brown", "china_cabinet_open_jungle",
        "china_cabinet_open_spruce", "laptop_closed_black",
        "laptop_closed_pink", "laptop_closed_silver",
        "picnic_basket_closed_black", "school_desk_open_black",
        "school_desk_open_blue", "school_desk_open_cherry",
        "school_desk_open_cyan", "school_desk_open_gray",
        "school_desk_open_green", "school_desk_open_light_blue",
        "school_desk_open_light_gray", "school_desk_open_lime",
        "school_desk_open_magenta", "school_desk_open_orange",
        "school_desk_open_pink", "school_desk_open_purple",
        "school_desk_open_red", "school_desk_open_yellow",
    )
)

ENTITY_LOOT = (
    "create_vampirism/loot_tables/entities/vampire_baron.json",
    "naturalist/loot_tables/entities/tortoise.json",
)

CHEST_LOOT = (
    "irons_spellbooks/loot_tables/chests/citadel/citadel_tomes.json",
    "irons_spellbooks/loot_tables/chests/catacombs/crypt_loot.json",
)

T45 = {
    "t45_body": {
        "part": "ntgl:body", "parent": "ntgl:config/model/base/body.json",
        "chassis": ["ntgl:example_chassis"], "model": "ntgl:geo/power_armor/t45.geo.json",
        "texture": {"default": "ntgl:textures/power_armor/t45.png"},
        "hide": ["body_bottom_frame"], "mods": ["jetpack"],
        "attachments": [
            {"frame": "body_top", "armor": "body_top_armor"},
            {"frame": "body_top", "armor": "jetpack"},
            {"frame": "body_bottom", "armor": "body_bottom_armor"},
        ],
    },
    "t45_helmet": {
        "part": "ntgl:head", "chassis": ["ntgl:example_chassis"],
        "model": "ntgl:geo/power_armor/t45.geo.json",
        "texture": {"default": "ntgl:textures/power_armor/t45.png"},
        "hide": ["head_frame"],
        "attachments": [{"frame": "head", "armor": "helmet"}],
    },
    "t45_left_arm": {
        "part": "ntgl:left_arm", "chassis": ["ntgl:example_chassis"],
        "model": "ntgl:geo/power_armor/t45.geo.json",
        "texture": {"default": "ntgl:textures/power_armor/t45.png"},
        "hide": ["left_upper_arm_frame", "left_forearm_frame"],
        "attachments": [
            {"frame": "body_top", "armor": "left_shoulder_armor"},
            {"frame": "left_arm", "armor": "left_upper_arm_armor"},
            {"frame": "left_lower_arm", "armor": "left_forearm_armor"},
        ],
    },
    "t45_left_leg": {
        "part": "ntgl:left_leg", "chassis": ["ntgl:example_chassis"],
        "model": "ntgl:geo/power_armor/t45.geo.json",
        "texture": {"default": "ntgl:textures/power_armor/t45.png"},
        "hide": ["left_toes_frame"],
        "attachments": [
            {"frame": "left_upper_leg", "armor": "left_upper_leg_armor"},
            {"frame": "left_lower_leg", "armor": "left_lower_leg_armor"},
            {"frame": "left_toes", "armor": "left_toes_armor"},
        ],
    },
    "t45_right_arm": {
        "part": "ntgl:right_arm", "chassis": ["ntgl:example_chassis"],
        "model": "ntgl:geo/power_armor/t45.geo.json",
        "texture": {"default": "ntgl:textures/power_armor/t45.png"},
        "hide": ["right_upper_arm_frame", "right_forearm_frame"],
        "attachments": [
            {"frame": "body_top", "armor": "right_shoulder_armor"},
            {"frame": "right_arm", "armor": "right_upper_arm_armor"},
            {"frame": "right_lower_arm", "armor": "right_forearm_armor"},
            {"frame": "right_lower_arm_pov", "armor": "pov_right_forearm_armor"},
        ],
    },
    "t45_right_leg": {
        "part": "ntgl:right_leg", "chassis": ["ntgl:example_chassis"],
        "model": "ntgl:geo/power_armor/t45.geo.json",
        "texture": {"default": "ntgl:textures/power_armor/t45.png"},
        "hide": ["right_toes_frame"],
        "attachments": [
            {"frame": "right_upper_leg", "armor": "right_upper_leg_armor"},
            {"frame": "right_lower_leg", "armor": "right_lower_leg_armor"},
            {"frame": "right_toes", "armor": "right_toes_armor"},
        ],
    },
}


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_data(root: Path) -> None:
    for relative in BLOCK_LOOT + DECOCRAFT_BLOCK_LOOT:
        dump(root / relative, {"type": "minecraft:block", "pools": []})
    for relative in ENTITY_LOOT:
        dump(root / relative, {"type": "minecraft:entity", "pools": []})
    for relative in CHEST_LOOT:
        dump(root / relative, {"type": "minecraft:chest", "pools": []})

    dump(root / "create_alexscaves_compat/recipes/mixing/marine_snow.json",
         {"conditions": [{"type": "forge:false"}]})

    for name, definition in T45.items():
        repaired = {"id": f"ntgl:{name}", **definition}
        dump(root / f"ntgl/cc/equipment/t45/{name}.json", repaired)

    dump(root / "buddycards/patchouli_books/buddycards_rules/book.json", {
        "name": "item.buddycards.buddycards_rulebook",
        "landing_text": "Welcome to the Buddycards TCG! This book will cover everything you need to know to play and then some.",
        "version": 1, "creative_tab": "buddycards",
        "book_texture": "patchouli:textures/gui/book_blue.png",
        "model": "buddycards:buddycards_rulebook", "show_progress": False,
        "use_resource_pack": True,
    })
    dump(root / "rebornstorage/patchouli_books/rs_book/book.json", {
        "name": "item.rebornstorage.rs_book", "landing_text": "rebornstorage.landing",
        "version": "1", "creative_tab": "rebornstorage", "use_resource_pack": True,
    })


def patch_servercore(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    replacements = {
        "'VAMPIRISM_HUNTER'": "'vampirism_hunter'",
        "'VAMPIRISM_VAMPIRE'": "'vampirism_vampire'",
        "'WEREWOLVES_WEREWOLF'": "'werewolves_werewolf'",
        "'RATS'": "'RATS_RATS'",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def patch_updater() -> None:
    old = ROOT / "scripts/update-crafty-0.1.9-56.py"
    new = ROOT / f"scripts/update-crafty-{VERSION}.py"
    text = old.read_text(encoding="utf-8")
    text = text.replace("VERSION = '0.1.9-56'", f"VERSION = '{VERSION}'", 1)
    text = text.replace("matching 0.1.9-56 Client ZIP", f"matching {VERSION} Client ZIP", 1)
    new.write_text(text, encoding="utf-8")


def main() -> None:
    for root in (ROOT / "client/overrides/kubejs/data", ROOT / "server/kubejs/data"):
        patch_data(root)
    for path in (ROOT / "client/overrides/config/servercore/config.yml", ROOT / "server/config/servercore/config.yml"):
        patch_servercore(path)

    marker = {
        "enabled": True,
        "empty_broken_loot_tables": len(BLOCK_LOOT + DECOCRAFT_BLOCK_LOOT + ENTITY_LOOT + CHEST_LOOT),
        "ntgl_t45_definitions_repaired": len(T45),
        "patchouli_books_repaired": 2,
        "servercore_registered_categories_repaired": 4,
        "world_data_touched": False,
    }
    for relative in ("server/_crafty/build-summary.json", "client/overrides/pack-information/validation.json", "server/pack-information/validation.json"):
        path = ROOT / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        if relative.endswith("build-summary.json"):
            data["version"] = VERSION
            data["pack_version"] = VERSION
        else:
            data["pack_version"] = VERSION
        data["startup_data_repairs_0_1_9_57"] = marker
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
    text = text.replace("Amber-and-Arcana-0.1.9-56", f"Amber-and-Arcana-{VERSION}")
    text = text.replace("| Pack | 0.1.9-56 |", f"| Pack | {VERSION} |")
    text = text.replace("Client 0.1.9-56", f"Client {VERSION}")
    text = text.replace("Server 0.1.9-56", f"Server {VERSION}")
    text = re.sub(r"\n### 0\.1\.9-57[^\n]*\n.*?(?=\n### |\Z)", "", text, flags=re.S)
    note = """### 0.1.9-57 startup data repairs, pass two
Repairs four registered ServerCore category names, six NTGL T45 definitions, and two Patchouli book descriptors. Disables one malformed compatibility recipe and replaces currently unparseable upstream loot tables with valid empty tables, matching their previous effective behavior while removing reload error spam. No world or player data is changed.
"""
    text = text.rstrip() + "\n\n" + note
    readme.write_text(text, encoding="utf-8")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    if "## 0.1.9-57" not in text:
        text = """## 0.1.9-57 — Startup data repairs, pass two

- Correct registered ServerCore category names for Rats, Vampirism, and Werewolves.
- Repair all six malformed NTGL T45 equipment definitions.
- Repair the Buddycards and Reborn Storage Patchouli book descriptors.
- Disable one malformed Create/Alex's Caves compatibility recipe.
- Neutralize 36 unparseable upstream loot tables that already produced no loot.
- No world or player data is included or modified.

""" + text
    changelog.write_text(text, encoding="utf-8")

    validator = ROOT / "scripts/validate.sh"
    text = validator.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-56"', '.version == "0.1.9-57"', 1)
    text = text.replace('.pack_version == "0.1.9-56"', '.pack_version == "0.1.9-57"', 1)
    text = text.replace("Amber & Arcana 0.1.9-56 static validation passed", "Amber & Arcana 0.1.9-57 static validation passed", 1)
    text = text.replace('= "65" || { echo "Expected 65 recipe compatibility files"', '= "66" || { echo "Expected 66 recipe compatibility files"', 1)
    text = text.replace("category: 'VAMPIRISM_VAMPIRE'", "category: 'vampirism_vampire'")
    if "# 0.1.9-57 second startup data repair checks" not in text:
        text += r'''

# 0.1.9-57 second startup data repair checks
grep -Fq "category: 'RATS_RATS'" "$server_sc" || { echo "Registered Rats category missing" >&2; exit 1; }
grep -Fq "category: 'vampirism_hunter'" "$server_sc" || { echo "Registered hunter category missing" >&2; exit 1; }
test "$(find "$server_data/ntgl/cc/equipment/t45" -type f -name '*.json' | wc -l)" = "6" || { echo "NTGL T45 repairs incomplete" >&2; exit 1; }
find "$server_data/ntgl/cc/equipment/t45" -type f -name '*.json' -print0 | xargs -0 -n1 jq -e '.id | startswith("ntgl:t45_")' >/dev/null
jq -e '.use_resource_pack == true' "$server_data/buddycards/patchouli_books/buddycards_rules/book.json" >/dev/null
jq -e '.use_resource_pack == true' "$server_data/rebornstorage/patchouli_books/rs_book/book.json" >/dev/null
jq -e '.startup_data_repairs_0_1_9_57.enabled == true and .startup_data_repairs_0_1_9_57.empty_broken_loot_tables == 36 and .startup_data_repairs_0_1_9_57.ntgl_t45_definitions_repaired == 6 and .startup_data_repairs_0_1_9_57.world_data_touched == false' "$validation" >/dev/null
'''
    validator.write_text(text, encoding="utf-8")
    patch_updater()
    print(f"Prepared Amber & Arcana {VERSION}: second startup data repair pass")


if __name__ == "__main__":
    main()
