#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-54"


def dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_release_metadata() -> None:
    manifest_path = ROOT / "client/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = VERSION
    manifest["name"] = "Amber & Arcana " + VERSION
    dump(manifest_path, manifest)

    marker = {
        "enabled": True,
        "powah_version": "5.0.11",
        "coolant_fluid": "create_central_kitchen:dragon_breath",
        "coolant_value": -20,
        "heat_source_block": "tconstruct:blazing_blood_fluid",
        "heat_value": 3500,
        "jei_display_fluid": "tconstruct:blazing_blood",
        "startup_event": "StartupEvents.postInit",
        "client_jei_direct_recipe_injection": True,
        "client_update_required": True,
        "server_update_required": True,
        "quest_progression_changed": False,
        "world_data_touched": False,
    }

    for rel in (
        "server/_crafty/build-summary.json",
        "client/overrides/pack-information/validation.json",
        "server/pack-information/validation.json",
    ):
        path = ROOT / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        if rel.endswith("build-summary.json"):
            data["version"] = VERSION
            data["pack_version"] = VERSION
        else:
            data["pack_version"] = VERSION
        data["powah_thermo_compat_0_1_9_54"] = marker
        dump(path, data)


def patch_modlist() -> None:
    path = ROOT / "client/modlist.html"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"<title>Amber &amp; Arcana 0\.1\.9-\d+ mod list</title>",
        f"<title>Amber &amp; Arcana {VERSION} mod list</title>",
        text,
        count=1,
    )
    text = re.sub(
        r"<h1>Amber &amp; Arcana 0\.1\.9-\d+</h1>",
        f"<h1>Amber &amp; Arcana {VERSION}</h1>",
        text,
        count=1,
    )
    path.write_text(text, encoding="utf-8")


def patch_readme_changelog() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    direct = (
        f"[Download Client {VERSION}](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Client.zip) · "
        f"[Download Crafty Server {VERSION}](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Server.zip) · "
        f"[Update existing Crafty server](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Crafty-Update-Overlay.zip)"
    )
    text = re.sub(r"\[Download Client[^\n]+", direct, text, count=1)
    text = re.sub(r"\| Pack \| [^|]+\|", f"| Pack | {VERSION} |", text, count=1)
    text = re.sub(
        r"Import `dist/Amber-and-Arcana-0\.1\.9-\d+-Client\.zip`",
        f"Import `dist/Amber-and-Arcana-{VERSION}-Client.zip`",
        text,
        count=1,
    )
    text = re.sub(
        r"Create a fresh server from `dist/Amber-and-Arcana-0\.1\.9-\d+-Server\.zip`",
        f"Create a fresh server from `dist/Amber-and-Arcana-{VERSION}-Server.zip`",
        text,
        count=1,
    )
    text = re.sub(
        r"extract `dist/Amber-and-Arcana-0\.1\.9-\d+-Crafty-Update-Overlay\.zip`",
        f"extract `dist/Amber-and-Arcana-{VERSION}-Crafty-Update-Overlay.zip`",
        text,
        count=1,
    )
    note = """### 0.1.9-54 Powah Thermo compatibility
Adds Create: Central Kitchen Dragon's Breath as a Powah Thermo Generator coolant at -20 and Tinkers' Construct Blazing Blood as a placed heat source at 3500. Registrations run at KubeJS post-init so modded registries are populated first. A separate client-only JEI recipe injection displays Blazing Blood without altering Powah's internal heat-source map. The Crafty update overlay now includes the required KubeJS startup script. No world, player, or quest data is changed.
"""
    if "### 0.1.9-54 Powah Thermo compatibility" not in text:
        text = text.rstrip() + "\n\n" + note
    path.write_text(text, encoding="utf-8")

    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-54" not in text:
        entry = """## 0.1.9-54 — Powah Thermo compatibility

- Register Create: Central Kitchen `create_central_kitchen:dragon_breath` as Powah Thermo coolant -20.
- Register Tinkers' Construct placed Blazing Blood block `tconstruct:blazing_blood_fluid` as Powah Thermo heat source 3500.
- Defer the registrations to `StartupEvents.postInit` so Forge's modded fluid/block registries are populated.
- Add a client-only JEI display recipe for `tconstruct:blazing_blood` at 3500 without mutating Powah's internal heat-source map.
- Include the Powah startup compatibility script in the world-safe Crafty update overlay.
- Client and server both need the matching update; no world/player or quest data is changed.

"""
        text = entry + text
    path.write_text(text, encoding="utf-8")


def patch_validator() -> None:
    path = ROOT / "scripts/validate.sh"
    text = path.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-53"', '.version == "0.1.9-54"', 1)
    text = text.replace('.pack_version == "0.1.9-53"', '.pack_version == "0.1.9-54"', 1)
    text = text.replace(
        "Amber & Arcana 0.1.9-53 static validation passed",
        "Amber & Arcana 0.1.9-54 static validation passed",
        1,
    )

    block = r"""
# 0.1.9-54 Powah Thermo compatibility checks
client_powah="$repo_dir/client/overrides/kubejs/startup_scripts/amber_arcana_powah_thermo_compat.js"
server_powah="$repo_dir/server/kubejs/startup_scripts/amber_arcana_powah_thermo_compat.js"
client_powah_jei="$repo_dir/client/overrides/kubejs/client_scripts/amber_arcana_powah_jei_compat.js"
test -f "$client_powah" && test -f "$server_powah" && test -f "$client_powah_jei" || { echo "Powah compatibility scripts missing" >&2; exit 1; }
cmp -s "$client_powah" "$server_powah" || { echo "Client/server Powah startup scripts differ" >&2; exit 1; }
grep -Fq "StartupEvents.postInit" "$client_powah" || { echo "Powah compatibility is not post-init" >&2; exit 1; }
grep -Fq "create_central_kitchen', 'dragon_breath" "$client_powah" || { echo "Central Kitchen Dragon Breath coolant ID missing" >&2; exit 1; }
grep -Fq "tconstruct', 'blazing_blood_fluid" "$client_powah" || { echo "Blazing Blood block heat-source ID missing" >&2; exit 1; }
grep -Fq "registerCoolant(dragonBreathId, -20)" "$client_powah" || { echo "Dragon Breath -20 coolant value missing" >&2; exit 1; }
grep -Fq "registerHeatSource(blazingBloodBlockId, 3500)" "$client_powah" || { echo "Blazing Blood 3500 heat value missing" >&2; exit 1; }
grep -Fq "HeatSourceCategory\$Recipe" "$client_powah_jei" || { echo "Safe Powah JEI recipe injection missing" >&2; exit 1; }
grep -Fq "tconstruct', 'blazing_blood" "$client_powah_jei" || { echo "Blazing Blood JEI fluid ID missing" >&2; exit 1; }
jq -e '.powah_thermo_compat_0_1_9_54.enabled == true and .powah_thermo_compat_0_1_9_54.coolant_value == -20 and .powah_thermo_compat_0_1_9_54.heat_value == 3500 and .powah_thermo_compat_0_1_9_54.client_jei_direct_recipe_injection == true and .powah_thermo_compat_0_1_9_54.world_data_touched == false' "$validation" >/dev/null

test "$(unzip -Z1 "$update_overlay" | grep -Fxc 'kubejs/startup_scripts/amber_arcana_powah_thermo_compat.js')" = "1" || { echo "Crafty update overlay missing Powah startup compatibility" >&2; exit 1; }
test "$(unzip -Z1 "$repo_dir/dist/Amber-and-Arcana-${version}-Client.zip" | grep -Fxc 'overrides/kubejs/startup_scripts/amber_arcana_powah_thermo_compat.js')" = "1" || { echo "Client ZIP missing Powah startup compatibility" >&2; exit 1; }
test "$(unzip -Z1 "$repo_dir/dist/Amber-and-Arcana-${version}-Client.zip" | grep -Fxc 'overrides/kubejs/client_scripts/amber_arcana_powah_jei_compat.js')" = "1" || { echo "Client ZIP missing Powah JEI compatibility" >&2; exit 1; }
test "$(unzip -Z1 "$repo_dir/dist/Amber-and-Arcana-${version}-Server.zip" | grep -Fxc 'kubejs/startup_scripts/amber_arcana_powah_thermo_compat.js')" = "1" || { echo "Server ZIP missing Powah startup compatibility" >&2; exit 1; }
"""
    if "# 0.1.9-54 Powah Thermo compatibility checks" not in text:
        text = text.rstrip() + "\n\n" + block.lstrip()
    path.write_text(text, encoding="utf-8")


def main() -> None:
    patch_release_metadata()
    patch_modlist()
    patch_readme_changelog()
    patch_validator()
    print("Prepared Amber & Arcana 0.1.9-54: Powah Thermo + JEI compatibility")


if __name__ == "__main__":
    main()
