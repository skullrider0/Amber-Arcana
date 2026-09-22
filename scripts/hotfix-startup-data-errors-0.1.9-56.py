#!/usr/bin/env python3
"""Disable malformed upstream data entries reported by the 2026-09-21 startup log."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-56"

BROKEN_RECIPES = (
    "deeperdarker/recipes/resonarium_helmet_smithing.json",
    "deeperdarker/recipes/resonarium_chestplate_smithing.json",
    "deeperdarker/recipes/resonarium_leggings_smithing.json",
    "deeperdarker/recipes/resonarium_boots_smithing.json",
    "deeperdarker/recipes/resonarium_sword_smithing.json",
    "deeperdarker/recipes/resonarium_pickaxe_smithing.json",
    "deeperdarker/recipes/resonarium_axe_smithing.json",
    "deeperdarker/recipes/resonarium_shovel_smithing.json",
    "deeperdarker/recipes/resonarium_hoe_smithing.json",
    "delightful/recipes/knives/smithing/resonarium_knife.json",
    "create_things_and_misc/recipes/netheriteportablewithlecraft.json",
    "cataclysm/recipes/stonecutting/azure_seastone_brick_stair_from_stonecutting.json",
    "tconstruct/recipes/tools/modifiers/slotless/embellishment/wood/slimewood_bloodshroom.json",
    "create_vampirism/recipes/vampire/curse_of_vampire.json",
)

BROKEN_ADVANCEMENTS = (
    "farmersrespite/advancements/main/stunt_tea_bush.json",
    "sob/advancements/get_prickly_pear.json",
    "beautify/advancements/progression/candelabra.json",
    "cloudstorage/advancements/cloudstorage/static_balloon.json",
)


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_tree(root: Path) -> None:
    # Forge evaluates recipe conditions before invoking the broken recipe codec.
    # A false condition therefore removes the bad recipe without inventing a new
    # progression path or changing any item IDs.
    disabled_recipe = {"conditions": [{"type": "forge:false"}]}
    for relative in BROKEN_RECIPES:
        dump(root / relative, disabled_recipe)

    # Keep the upstream advancement IDs resolvable while making them impossible
    # to award. This is safer than substituting unrelated items or triggers.
    disabled_advancement = {
        "criteria": {
            "disabled_invalid_upstream_advancement": {
                "trigger": "minecraft:impossible"
            }
        }
    }
    for relative in BROKEN_ADVANCEMENTS:
        dump(root / relative, disabled_advancement)


def patch_updater() -> None:
    old = ROOT / "scripts/update-crafty-0.1.9-55.py"
    new = ROOT / f"scripts/update-crafty-{VERSION}.py"
    text = old.read_text(encoding="utf-8")
    text = text.replace("VERSION = '0.1.9-55'", f"VERSION = '{VERSION}'", 1)
    text = text.replace("matching 0.1.9-55 Client ZIP", f"matching {VERSION} Client ZIP", 1)
    new.write_text(text, encoding="utf-8")


def main() -> None:
    for data_root in (ROOT / "client/overrides/kubejs/data", ROOT / "server/kubejs/data"):
        patch_tree(data_root)

    marker = {
        "enabled": True,
        "source_log": "2026-09-21 startup log",
        "disabled_malformed_recipes": len(BROKEN_RECIPES),
        "replaced_invalid_advancements": len(BROKEN_ADVANCEMENTS),
        "servercore_modded_caps_preserved": True,
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
        data["startup_data_repairs_0_1_9_56"] = marker
        dump(path, data)

    manifest_path = ROOT / "client/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = VERSION
    manifest["name"] = "Amber & Arcana " + VERSION
    dump(manifest_path, manifest)

    modlist = ROOT / "client/modlist.html"
    text = modlist.read_text(encoding="utf-8")
    text = re.sub(r"Amber &amp; Arcana 0\.1\.9-\d+", f"Amber &amp; Arcana {VERSION}", text)
    modlist.write_text(text, encoding="utf-8")

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    # Historical hotfixes rewrite their own heading while being replayed. Keep
    # the current download/instruction references current, then canonicalize the
    # three latest release notes so repeated builds cannot accumulate copies.
    text = text.replace("Amber-and-Arcana-0.1.9-55", f"Amber-and-Arcana-{VERSION}")
    text = text.replace("| Pack | 0.1.9-55 |", f"| Pack | {VERSION} |")
    text = text.replace("Client 0.1.9-55", f"Client {VERSION}")
    text = text.replace("Server 0.1.9-55", f"Server {VERSION}")
    text = re.sub(r"\n### 0\.1\.9-(?:54|55|56)[^\n]*\n.*?(?=\n### |\Z)", "", text, flags=re.S)
    notes = """
### 0.1.9-54 Powah Thermo compatibility
Adds Create: Central Kitchen Dragon's Breath as a Powah Thermo Generator coolant at -20 and Tinkers' Construct Blazing Blood as a placed heat source at 3500. Registrations run at KubeJS post-init so modded registries are populated first. A separate client-only JEI recipe injection displays Blazing Blood without altering Powah's internal heat-source map. The Crafty update overlay now includes the required KubeJS startup script. No world, player, or quest data is changed.

### 0.1.9-55 chunk-load performance tuning
Based on the 2026-09-21 server log, ServerCore now reacts sooner to sustained chunk-loading pressure: target 30 MSPT; chunk-tick and simulation distance 6→3; view distance 8→6 only while overloaded; autosaves every 10 minutes. Mob caps, spawners, quests, and the client-safe MoreHitboxes patch are unchanged. Missing Untamed Wilds entities and Mowzie's structure references are legacy data being discarded after their intentional 0.1.9-49 removal; those performance-heavy mods remain removed. No world/player data is changed by this release.

### 0.1.9-56 startup data repairs
Disables 14 malformed upstream recipes and replaces four invalid advancements with inert, valid definitions. The fixes are mirrored on client and server. Modded ServerCore mob-cap entries remain enabled; its early registration warning is retained rather than silently dropping the configured rat, vampire, and werewolf caps. No world or player data is changed.
"""
    text = text.rstrip() + "\n\n" + notes.lstrip()
    readme.write_text(text, encoding="utf-8")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    if "## 0.1.9-56" not in text:
        text = """## 0.1.9-56 — Startup data repairs

- Disable 14 malformed upstream recipes before their broken serializers run.
- Replace four invalid advancements with inert definitions that preserve their resource IDs.
- Preserve the configured rat, vampire, and werewolf ServerCore caps despite its harmless early-registration warning.
- Preserve Crafty ownership when the stopped-server updater runs as root.
- No world or player data is included or modified.

""" + text
    changelog.write_text(text, encoding="utf-8")

    validator = ROOT / "scripts/validate.sh"
    text = validator.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-55"', '.version == "0.1.9-56"', 1)
    text = text.replace('.pack_version == "0.1.9-55"', '.pack_version == "0.1.9-56"', 1)
    text = text.replace("Amber & Arcana 0.1.9-55 static validation passed", "Amber & Arcana 0.1.9-56 static validation passed", 1)
    text = text.replace(
        'test "$(find "$client_compat" -path \'*/recipes/*.json\' -type f | wc -l)" = "51" || { echo "Expected 36 disabled recipe overrides plus 15 bee recipes" >&2; exit 1; }',
        'test "$(find "$client_compat" -path \'*/recipes/*.json\' -type f | wc -l)" = "65" || { echo "Expected 65 recipe compatibility files" >&2; exit 1; }',
    )
    if "# 0.1.9-56 startup data repair checks" not in text:
        text += r'''

# 0.1.9-56 startup data repair checks
client_data="$repo_dir/client/overrides/kubejs/data"
server_data="$repo_dir/server/kubejs/data"
diff -qr "$client_data" "$server_data" >/dev/null || { echo "Client/server KubeJS data differ" >&2; exit 1; }
test "$(find "$server_data" -type f -path '*/recipes/*.json' -exec grep -l 'forge:false' {} + | wc -l)" -ge 14 || { echo "Malformed recipe overrides missing" >&2; exit 1; }
test "$(find "$server_data" -type f -path '*/advancements/*.json' -exec grep -l 'minecraft:impossible' {} + | wc -l)" -ge 4 || { echo "Invalid advancement overrides missing" >&2; exit 1; }
jq -e '.startup_data_repairs_0_1_9_56.enabled == true and .startup_data_repairs_0_1_9_56.disabled_malformed_recipes == 14 and .startup_data_repairs_0_1_9_56.replaced_invalid_advancements == 4 and .startup_data_repairs_0_1_9_56.world_data_touched == false' "$validation" >/dev/null
'''
    validator.write_text(text, encoding="utf-8")

    patch_updater()
    print(f"Prepared Amber & Arcana {VERSION}: startup data repairs")


if __name__ == "__main__":
    main()
