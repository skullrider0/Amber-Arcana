#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-36"
MANIFEST = ROOT / "client/manifest.json"
SERVER_MODS = ROOT / "server/_crafty/server-mods.tsv"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
VALIDATE_SH = ROOT / "scripts/validate.sh"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"

# CurseForge project/file pins selected specifically for Minecraft 1.20.1 Forge.
# SHA-1 is accepted by the existing AmberArcanaCraftyLauncher when prefixed with
# "sha1:". Infernos Otter Taming is a very new release whose public metadata does
# not expose a digest through the sources used for this release, so that one row
# intentionally leaves the digest blank; the launcher still verifies a non-empty
# completed download before starting Forge.
MODS = [
    {
        "project": 351748,
        "file": 4864220,
        "filename": "mininggadgets-1.15.6.jar",
        "hash": "sha1:79cfc6e0afc3ed3fc86bbda274ef3fccdc8260dd",
        "slug": "mining-gadgets",
        "name": "Mining Gadgets",
        "kind": "requested",
    },
    {
        "project": 284497,
        "file": 6880323,
        "filename": "IronJetpacks-1.20.1-7.0.9.jar",
        "hash": "sha1:b1fdcfdd48ac4519ea95cb3b8dbaacc5cf819b20",
        "slug": "iron-jetpacks",
        "name": "Iron Jetpacks",
        "kind": "requested",
    },
    {
        "project": 1060096,
        "file": 5870964,
        "filename": "mekanism_lasers-1.0.10.jar",
        "hash": "sha1:ef2c02ea81563a8275a533e0ba35609bfd68c7a5",
        "slug": "mekanism-lasers",
        "name": "Mekanism Lasers",
        "kind": "requested",
    },
    {
        "project": 223565,
        "file": 6793843,
        "filename": "Draconic-Evolution-1.20.1-3.1.2.621-universal.jar",
        "hash": "sha1:8abd0ee849f9654ec91d3ecbd115e2c296f08c73",
        "slug": "draconic-evolution",
        "name": "Draconic Evolution",
        "kind": "requested",
    },
    {
        "project": 231382,
        "file": 5422013,
        "filename": "BrandonsCore-1.20.1-3.2.1.302-universal.jar",
        "hash": "sha1:1378ba5f84267c18f945c52d787ac86e40d6c241",
        "slug": "brandons-core",
        "name": "Brandon's Core",
        "kind": "dependency",
    },
    {
        "project": 242818,
        "file": 8491810,
        "filename": "CodeChickenLib-1.20.1-4.4.0.528-universal.jar",
        "hash": "sha1:66c614b047414e3cfcd69ff7f001b7033c5813c6",
        "slug": "codechicken-lib-1-8",
        "name": "CodeChicken Lib",
        "kind": "dependency",
    },
    {
        "project": 552574,
        "file": 5895036,
        "filename": "HostileNeuralNetworks-1.20.1-5.3.3.jar",
        "hash": "sha1:ec0c77124e7e29c6d642410e3b7b3652a866aff5",
        "slug": "hostile-neural-networks",
        "name": "Hostile Neural Networks",
        "kind": "requested",
    },
    {
        "project": 283644,
        "file": 6274231,
        "filename": "Placebo-1.20.1-8.6.3.jar",
        "hash": "sha1:e85f53de2e582a79ce25ff1df1e7b5b5fc08440f",
        "slug": "placebo",
        "name": "Placebo",
        "kind": "dependency",
    },
    {
        "project": 1632230,
        "file": 8670714,
        "filename": "ottertaming-1.20.1-Forge-1.0.2.jar",
        "hash": "",
        "slug": "infernos-otter-taming",
        "name": "Infernos Otter Taming",
        "kind": "requested",
    },
]

REQUIRED_EXISTING_SLUGS = {
    "cucumber": "Iron Jetpacks dependency",
    "mekanism": "Mekanism Lasers dependency",
    "critters-and-companions": "Infernos Otter Taming dependency",
    "geckolib": "Critters and Companions dependency",
}


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_manifest() -> int:
    data = json.loads(MANIFEST.read_text())
    data["name"] = f"Amber & Arcana {VERSION}"
    data["version"] = VERSION

    wanted_projects = {m["project"] for m in MODS}
    files = [entry for entry in data.get("files", []) if entry.get("projectID") not in wanted_projects]
    for mod in MODS:
        files.append({"projectID": mod["project"], "fileID": mod["file"], "required": True})
    files.sort(key=lambda e: (int(e.get("projectID", 0)), int(e.get("fileID", 0))))
    data["files"] = files
    write_json(MANIFEST, data)
    return len(files)


def update_server_mods() -> int:
    raw = SERVER_MODS.read_text().splitlines()
    header = next((line for line in raw if line.startswith("#")), "# fileID\tfilename\tsha512\tslug\tname")
    rows = []
    for line in raw:
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t", 4)
        if len(parts) != 5:
            raise RuntimeError(f"Malformed server mod row: {line}")
        rows.append(parts)

    present_slugs = {r[3] for r in rows}
    missing = [f"{slug} ({why})" for slug, why in REQUIRED_EXISTING_SLUGS.items() if slug not in present_slugs]
    if missing:
        raise RuntimeError("Missing required existing dependencies: " + ", ".join(missing))

    wanted_projects = {str(m["file"]) for m in MODS}
    wanted_slugs = {m["slug"] for m in MODS}
    wanted_filenames = {m["filename"] for m in MODS}
    rows = [r for r in rows if r[0] not in wanted_projects and r[3] not in wanted_slugs and r[1] not in wanted_filenames]

    for mod in MODS:
        rows.append([
            str(mod["file"]),
            mod["filename"],
            mod["hash"],
            mod["slug"],
            mod["name"],
        ])

    rows.sort(key=lambda r: (r[3].lower(), r[1].lower()))
    SERVER_MODS.write_text(header + "\n" + "\n".join("\t".join(r) for r in rows) + "\n")
    return len(rows)


def update_metadata(manifest_count: int, server_count: int) -> None:
    requested = [m["name"] for m in MODS if m["kind"] == "requested"]
    deps = [m["name"] for m in MODS if m["kind"] == "dependency"]
    block = {
        "requested_mods_added": requested,
        "dependencies_added": deps,
        "already_present_dependencies_reused": ["Cucumber Library", "Mekanism", "Critters and Companions", "GeckoLib"],
        "mekanism_request_interpretation": "Mekanism Lasers 1.0.10 for the requested Mekanism mining/laser expansion; Mining Gadgets supplies the dedicated mining laser tool.",
        "curseforge_entries_added": len(MODS),
        "client_manifest_entries": manifest_count,
        "server_mod_downloads": server_count,
        "requires_client_update": True,
        "world_data_touched": False,
        "crafty_update_overlay_world_safe": True,
        "server_downloads_on_next_start": True,
    }

    summary = json.loads(SUMMARY.read_text())
    summary["pack_version"] = VERSION
    summary["manifest_entries"] = manifest_count
    summary["mod_metadata_entries"] = manifest_count
    summary["server_mod_downloads"] = server_count
    summary["server_mod_count"] = server_count
    summary["tech_expansion_0_1_9_36"] = block
    write_json(SUMMARY, summary)

    validation = json.loads(VALIDATION.read_text())
    validation["pack_version"] = VERSION
    validation["tech_expansion_0_1_9_36"] = block
    write_json(VALIDATION, validation)


def update_validator() -> None:
    text = VALIDATE_SH.read_text()
    text = text.replace("0.1.9-35", VERSION)

    marker = "# 0.1.9-36 requested technology/content expansion checks"
    if marker not in text:
        project_checks = " ".join(f'{m["project"]}:{m["file"]}' for m in MODS)
        row_checks = "\n".join(
            f"test \"$(awk -F '\\\\t' '$1 == \"{m['file']}\" && $2 == \"{m['filename']}\" {{n++}} END {{print n+0}}' \"$repo_dir/server/_crafty/server-mods.tsv\")\" = \"1\" || {{ echo \"Missing 0.1.9-36 server mod pin: {m['name']}\" >&2; exit 1; }}"
            for m in MODS
        )
        text += f'''\n\n{marker}\nfor pin in {project_checks}; do\n  project="${{pin%%:*}}"\n  file="${{pin##*:}}"\n  test "$(jq --argjson p "$project" --argjson f "$file" '[.files[] | select(.projectID == $p and .fileID == $f)] | length' "$manifest")" = "1" || {{ echo "Missing 0.1.9-36 client manifest pin $pin" >&2; exit 1; }}\ndone\n{row_checks}\njq -e '.tech_expansion_0_1_9_36.curseforge_entries_added == 9 and .tech_expansion_0_1_9_36.requires_client_update == true and .tech_expansion_0_1_9_36.world_data_touched == false and .tech_expansion_0_1_9_36.crafty_update_overlay_world_safe == true and .tech_expansion_0_1_9_36.server_downloads_on_next_start == true' "$validation" >/dev/null\n'''
    VALIDATE_SH.write_text(text)


def update_docs() -> None:
    changelog = CHANGELOG.read_text() if CHANGELOG.exists() else ""
    heading = f"## {VERSION}"
    if heading not in changelog:
        entry = f'''{heading}\n\n- Added Mining Gadgets 1.15.6.\n- Added Iron Jetpacks 7.0.9, reusing the pack's existing Cucumber Library.\n- Added Mekanism Lasers 1.0.10, using the existing Mekanism installation.\n- Added Draconic Evolution 3.1.2.621 with Brandon's Core and CodeChicken Lib.\n- Added Hostile Neural Networks 5.3.3 with Placebo.\n- Added Infernos Otter Taming 1.0.2, reusing Critters and Companions and GeckoLib.\n- Crafty update remains world-safe: the update overlay changes pack/mod metadata and quests only; world saves are not included.\n\n'''
        CHANGELOG.write_text(entry + changelog)

    if README.exists():
        readme = README.read_text()
        if "0.1.9-36" not in readme:
            readme += "\n\n### 0.1.9-36 tech expansion\nAdds Mining Gadgets, Iron Jetpacks, Mekanism Lasers, Draconic Evolution, Hostile Neural Networks, Infernos Otter Taming, and required missing libraries. The Crafty update overlay never contains world data.\n"
            README.write_text(readme)


def main() -> None:
    manifest_count = update_manifest()
    server_count = update_server_mods()
    update_metadata(manifest_count, server_count)
    update_validator()
    update_docs()

    print(
        f"Applied Amber & Arcana {VERSION}: {len([m for m in MODS if m['kind'] == 'requested'])} requested mods + "
        f"{len([m for m in MODS if m['kind'] == 'dependency'])} dependencies; "
        f"client manifest={manifest_count}, server downloads={server_count}; world data untouched"
    )


if __name__ == "__main__":
    main()
