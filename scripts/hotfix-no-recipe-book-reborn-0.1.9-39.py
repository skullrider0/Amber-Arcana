#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-39"
PROJECT_ID = 551314
FILE_ID = 4725571
MOD_NAME = "No Recipe Book Reborn"
MOD_VERSION = "1.0.5"
MOD_FILENAME = "norecipebookreborn-1.0.5.jar"

MANIFEST = ROOT / "client/manifest.json"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
VALIDATE_SH = ROOT / "scripts/validate.sh"
SERVER_MODS = ROOT / "server/_crafty/server-mods.tsv"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_manifest() -> int:
    data = json.loads(MANIFEST.read_text())
    data["name"] = f"Amber & Arcana {VERSION}"
    data["version"] = VERSION

    files = [
        entry for entry in data.get("files", [])
        if int(entry.get("projectID", -1)) != PROJECT_ID
    ]
    files.append({"projectID": PROJECT_ID, "fileID": FILE_ID, "required": True})
    files.sort(key=lambda e: (int(e.get("projectID", 0)), int(e.get("fileID", 0))))
    data["files"] = files
    write_json(MANIFEST, data)
    return len(files)


def update_metadata(manifest_count: int) -> None:
    block = {
        "name": MOD_NAME,
        "version": MOD_VERSION,
        "project_id": PROJECT_ID,
        "file_id": FILE_ID,
        "filename": MOD_FILENAME,
        "minecraft": "1.20.1",
        "loader": "Forge",
        "environment": "client-only",
        "server_mod_added": False,
        "requires_server_update": False,
        "requires_client_update": True,
        "world_data_touched": False,
    }

    summary = json.loads(SUMMARY.read_text())
    summary["pack_version"] = VERSION
    summary["manifest_entries"] = manifest_count
    summary["mod_metadata_entries"] = manifest_count
    summary["no_recipe_book_reborn_0_1_9_39"] = block
    write_json(SUMMARY, summary)

    validation = json.loads(VALIDATION.read_text())
    validation["pack_version"] = VERSION
    validation["no_recipe_book_reborn_0_1_9_39"] = block
    write_json(VALIDATION, validation)


def update_validator() -> None:
    text = VALIDATE_SH.read_text()
    text = text.replace("0.1.9-38", VERSION)
    marker = "# 0.1.9-39 No Recipe Book Reborn client-only checks"
    if marker not in text:
        text += f'''\n\n{marker}\ntest "$(jq '[.files[] | select(.projectID == {PROJECT_ID} and .fileID == {FILE_ID})] | length' "$manifest")" = "1" || {{ echo "Expected {MOD_NAME} {MOD_VERSION} client pin" >&2; exit 1; }}\nif rg -F '{MOD_FILENAME}' "$repo_dir/server/_crafty/server-mods.tsv" >/dev/null || rg -F $'\\tno-recipe-book-reborn\\t' "$repo_dir/server/_crafty/server-mods.tsv" >/dev/null; then\n  echo "{MOD_NAME} is client-only and must not be installed on the dedicated server" >&2\n  exit 1\nfi\njq -e '.no_recipe_book_reborn_0_1_9_39.project_id == {PROJECT_ID} and .no_recipe_book_reborn_0_1_9_39.file_id == {FILE_ID} and .no_recipe_book_reborn_0_1_9_39.environment == "client-only" and .no_recipe_book_reborn_0_1_9_39.requires_server_update == false and .no_recipe_book_reborn_0_1_9_39.world_data_touched == false' "$validation" >/dev/null\n'''
    VALIDATE_SH.write_text(text)


def update_docs() -> None:
    changelog = CHANGELOG.read_text() if CHANGELOG.exists() else ""
    heading = f"## {VERSION}"
    if heading not in changelog:
        CHANGELOG.write_text(
            f'''{heading}\n\n- Added No Recipe Book Reborn 1.0.5 for Forge 1.20.1.\n- Client-only quality-of-life change: removes the vanilla recipe-book buttons from supported crafting/furnace-style screens.\n- Dedicated-server mod list is intentionally unchanged.\n\n''' + changelog
        )

    if README.exists():
        readme = README.read_text()
        if heading not in readme:
            readme += f'''\n\n### {VERSION} client QoL\nAdds No Recipe Book Reborn 1.0.5 to the client manifest only. It is not installed on the dedicated server and does not touch world data.\n'''
            README.write_text(readme)


def main() -> None:
    manifest_count = update_manifest()
    update_metadata(manifest_count)
    update_validator()
    update_docs()

    # Defensive assertion: this mod must remain client-only.
    server_text = SERVER_MODS.read_text()
    if MOD_FILENAME in server_text or "\tno-recipe-book-reborn\t" in server_text:
        raise RuntimeError("No Recipe Book Reborn unexpectedly present in server mod list")

    print(f"Applied Amber & Arcana {VERSION}: {MOD_NAME} {MOD_VERSION} client-only; manifest entries={manifest_count}")


if __name__ == "__main__":
    main()
