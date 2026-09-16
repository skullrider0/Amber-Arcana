#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-41"
MANIFEST = ROOT / "client/manifest.json"
SERVER_MODS = ROOT / "server/_crafty/server-mods.tsv"
REMOVE_MODS = ROOT / "server/_crafty/remove-mods.txt"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
VALIDATE = ROOT / "scripts/validate.sh"
VALIDATE_VIEWER = ROOT / "scripts/validate-viewer.py"
CHANGELOG = ROOT / "CHANGELOG.md"
README = ROOT / "README.md"

# Minecraft 1.20.1 Forge pins.
MODS = [
    {
        "project": 388800,
        "file": 6450982,
        "filename": "polymorph-forge-0.49.10+1.20.1.jar",
        "slug": "polymorph",
        "name": "Polymorph",
        "purpose": "Recipe-conflict selector for vanilla crafting, smelting, and smithing.",
    },
    {
        "project": 941096,
        "file": 5282394,
        "filename": "polyeng-forge-0.1.1-1.20.1.jar",
        "slug": "polymorphic-energistics",
        "name": "Polymorphic Energistics",
        "purpose": "Polymorph selector support for Applied Energistics 2 terminals.",
    },
    {
        "project": 943086,
        "file": 5227282,
        "filename": "refinedpolymorph-0.1.1-1.20.1.jar",
        "slug": "refined-polymorphism",
        "name": "Refined Polymorphism",
        "purpose": "Polymorph selector support for Refined Storage grids.",
    },
    {
        "project": 278141,
        "file": 6842571,
        "filename": "SpartanWeaponry-1.20.1-forge-3.2.1-all.jar",
        "slug": "spartan-weaponry",
        "name": "Spartan Weaponry",
        "purpose": "Expanded melee/ranged weapon arsenal; pack already includes Better Combat and JEI.",
    },
]


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_manifest() -> int:
    data = json.loads(MANIFEST.read_text())
    data["name"] = f"Amber & Arcana {VERSION}"
    data["version"] = VERSION

    projects = {m["project"] for m in MODS}
    files = [f for f in data.get("files", []) if int(f.get("projectID", -1)) not in projects]
    for mod in MODS:
        files.append({"projectID": mod["project"], "fileID": mod["file"], "required": True})
    files.sort(key=lambda f: (int(f.get("projectID", 0)), int(f.get("fileID", 0))))
    data["files"] = files
    write_json(MANIFEST, data)
    return len(files)


def update_server_mods() -> int:
    raw = SERVER_MODS.read_text().splitlines()
    rows: list[list[str]] = []
    for line in raw:
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 6:
            raise RuntimeError(f"Expected 0.1.9-40 six-column server manifest row, got: {line}")
        rows.append(parts[:6])

    projects = {str(m["project"]) for m in MODS}
    slugs = {m["slug"] for m in MODS}
    filenames = {m["filename"] for m in MODS}
    rows = [r for r in rows if r[5] not in projects and r[3] not in slugs and r[1] not in filenames]

    for mod in MODS:
        rows.append([
            str(mod["file"]),
            mod["filename"],
            "",  # launcher validates non-empty completed downloads when upstream digest is unavailable here
            mod["slug"],
            mod["name"],
            str(mod["project"]),
        ])

    rows.sort(key=lambda r: (r[3].lower(), r[1].lower()))
    SERVER_MODS.write_text(
        "# fileID\tfilename\tsha512\tslug\tname\tprojectID\n"
        + "\n".join("\t".join(r) for r in rows)
        + "\n"
    )
    return len(rows)


def keep_stale_polymorph_cleanup() -> None:
    text = REMOVE_MODS.read_text()
    # Keep the old 0.49.11 cleanup because the restored, deliberately pinned
    # 1.20.1 build is 0.49.10. Never schedule the current jar for deletion.
    current = "polymorph-forge-0.49.10+1.20.1.jar"
    text = "\n".join(line for line in text.splitlines() if line.strip() != current) + "\n"
    if "polymorph-forge-0.49.11+1.20.1.jar" not in text:
        text += "polymorph-forge-0.49.11+1.20.1.jar\n"
    REMOVE_MODS.write_text(text)


def update_metadata(manifest_count: int, server_count: int) -> None:
    block = {
        "mods_added": [m["name"] for m in MODS],
        "pins": {m["name"]: f"CurseForge {m['project']}:{m['file']} / {m['filename']}" for m in MODS},
        "polymorph_selector": True,
        "ae2_selector_integration": True,
        "refined_storage_selector_integration": True,
        "spartan_weaponry": True,
        "spartan_weaponry_version": "3.2.1",
        "better_combat_already_present": True,
        "jei_already_present": True,
        "client_update_required": True,
        "server_update_required": True,
        "world_data_touched": False,
        "world_data_in_update_overlay": False,
        "manifest_entries": manifest_count,
        "server_mod_downloads": server_count,
    }

    for path in (SUMMARY, VALIDATION):
        data = json.loads(path.read_text())
        data["pack_version"] = VERSION
        data["recipe_conflicts_spartan_0_1_9_41"] = block
        if path == SUMMARY:
            data["manifest_entries"] = manifest_count
            data["mod_metadata_entries"] = manifest_count
            data["server_mod_downloads"] = server_count
            data["server_mod_count"] = server_count
        write_json(path, data)


def update_validate_viewer() -> None:
    text = VALIDATE_VIEWER.read_text()
    text = text.replace(
        'assert not {310111, 521393, 388800} & {f["projectID"] for f in files}, "Old viewer/Polymorph present"',
        'assert not {310111, 521393} & {f["projectID"] for f in files}, "Old viewer present"\n'
        'assert [(f["projectID"], f["fileID"]) for f in files if f["projectID"] == 388800] == [(388800, 6450982)], "Polymorph client pin differs"'
    )
    VALIDATE_VIEWER.write_text(text)


def update_validator() -> None:
    text = VALIDATE.read_text()
    text = text.replace('.version == "0.1.9-40"', '.version == "0.1.9-41"')
    text = text.replace('.pack_version == "0.1.9-40"', '.pack_version == "0.1.9-41"')
    text = text.replace(
        'for removed_project in 310111 521393 388800 628539 544031 430127 255717 227639; do',
        'for removed_project in 310111 521393 628539 544031 430127 255717 227639; do'
    )
    text = text.replace(
        "if rg -i 'polymorph|roughlyenoughitems|roughly_enough_items|reiplugincompatibilities|twilightforest|the-twilight-forest' \"$repo_dir/server/_crafty/server-mods.tsv\" >/dev/null; then\n  echo \"Removed viewer or Twilight Forest found in server mod list\" >&2",
        "if rg -i 'roughlyenoughitems|roughly_enough_items|reiplugincompatibilities|twilightforest|the-twilight-forest' \"$repo_dir/server/_crafty/server-mods.tsv\" >/dev/null; then\n  echo \"Removed viewer or Twilight Forest found in server mod list\" >&2"
    )
    text = text.replace('echo "Amber & Arcana 0.1.9-39 static validation passed"', 'echo "Amber & Arcana 0.1.9-41 static validation passed"')

    marker = "# 0.1.9-41 recipe conflict + Spartan Weaponry checks"
    if marker not in text:
        checks = "\n".join(
            f'test "$(jq \'[.files[] | select(.projectID == {m["project"]} and .fileID == {m["file"]})] | length\' "$manifest")" = "1" || {{ echo "Missing 0.1.9-41 client pin: {m["name"]}" >&2; exit 1; }}\n'
            f'test "$(awk -F \'\\t\' \'$1 == "{m["file"]}" && $2 == "{m["filename"]}" && $4 == "{m["slug"]}" && $6 == "{m["project"]}" {{n++}} END {{print n+0}}\' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || {{ echo "Missing 0.1.9-41 server pin: {m["name"]}" >&2; exit 1; }}'
            for m in MODS
        )
        text += f'''\n\n{marker}\n{checks}\nif grep -Fxq 'polymorph-forge-0.49.10+1.20.1.jar' "$repo_dir/server/_crafty/remove-mods.txt"; then echo "Current Polymorph jar is scheduled for deletion" >&2; exit 1; fi\njq -e '.recipe_conflicts_spartan_0_1_9_41.polymorph_selector == true and .recipe_conflicts_spartan_0_1_9_41.ae2_selector_integration == true and .recipe_conflicts_spartan_0_1_9_41.refined_storage_selector_integration == true and .recipe_conflicts_spartan_0_1_9_41.spartan_weaponry == true and .recipe_conflicts_spartan_0_1_9_41.client_update_required == true and .recipe_conflicts_spartan_0_1_9_41.world_data_touched == false' "$validation" >/dev/null\n'''
    VALIDATE.write_text(text)


def update_docs() -> None:
    if CHANGELOG.exists():
        old = CHANGELOG.read_text()
        if f"## {VERSION}" not in old:
            CHANGELOG.write_text(
                f"## {VERSION}\n\n"
                "- Restored Polymorph 0.49.10 for selectable conflicting crafting/smelting/smithing outputs.\n"
                "- Added Polymorphic Energistics 0.1.1 for AE2 terminal recipe selection.\n"
                "- Added Refined Polymorphism 0.1.1 for Refined Storage grid recipe selection.\n"
                "- Added Spartan Weaponry 3.2.1 for the expanded weapon arsenal.\n"
                "- Client and server must both update; the world-safe Crafty overlay contains no world save data.\n\n"
                + old
            )
    if README.exists():
        text = README.read_text()
        if "0.1.9-41 recipe conflicts and Spartan Weaponry" not in text:
            text += (
                "\n\n### 0.1.9-41 recipe conflicts and Spartan Weaponry\n"
                "Adds Polymorph plus AE2/Refined Storage integrations so conflicting recipes can be selected in crafting/storage terminals, "
                "and adds Spartan Weaponry 3.2.1. This is a client-and-server content update; the Crafty update overlay remains world-safe.\n"
            )
            README.write_text(text)


def main() -> None:
    manifest_count = update_manifest()
    server_count = update_server_mods()
    keep_stale_polymorph_cleanup()
    update_metadata(manifest_count, server_count)
    update_validate_viewer()
    update_validator()
    update_docs()
    print(f"Applied {VERSION}: 4 mods added, manifest={manifest_count}, server={server_count}, world data untouched")


if __name__ == "__main__":
    main()
