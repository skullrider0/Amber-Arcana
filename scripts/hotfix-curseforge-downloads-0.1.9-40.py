#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-40"
MANIFEST = ROOT / "client/manifest.json"
SERVER_MODS = ROOT / "server/_crafty/server-mods.tsv"
SUMMARY = ROOT / "server/_crafty/build-summary.json"
VALIDATION = ROOT / "server/pack-information/validation.json"
VALIDATE = ROOT / "scripts/validate.sh"
CHANGELOG = ROOT / "CHANGELOG.md"
README = ROOT / "README.md"


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def enrich_server_mods(manifest: dict) -> tuple[int, int]:
    by_file = {str(int(e["fileID"])): str(int(e["projectID"])) for e in manifest.get("files", [])}
    raw = SERVER_MODS.read_text().splitlines()
    rows = []
    missing: list[str] = []
    for line in raw:
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            raise RuntimeError(f"Malformed server mod row: {line}")
        base = parts[:5]
        file_id = base[0].strip()
        if file_id == "0":
            project_id = "0"
        else:
            project_id = by_file.get(file_id, "")
            if not project_id:
                missing.append(f"{file_id}:{base[3]}:{base[1]}")
        rows.append(base + [project_id])
    if missing:
        raise RuntimeError("Server files missing CurseForge project IDs from client manifest: " + ", ".join(missing))
    SERVER_MODS.write_text("# fileID\tfilename\tsha512\tslug\tname\tprojectID\n" + "\n".join("\t".join(r) for r in rows) + "\n")
    nonlocal_rows = sum(1 for r in rows if r[0] != "0")
    return len(rows), nonlocal_rows


def update_release_metadata(server_rows: int, mapped_rows: int) -> None:
    manifest = json.loads(MANIFEST.read_text())
    manifest["name"] = f"Amber & Arcana {VERSION}"
    manifest["version"] = VERSION
    write_json(MANIFEST, manifest)

    block = {
        "reason": "CurseForge began requiring API-key authentication for direct CDN downloads on 2026-07-16; the old Crafty bootstrap therefore received 401 responses for missing server mods.",
        "server_mod_rows": server_rows,
        "server_mod_rows_with_project_ids": mapped_rows,
        "server_manifest_has_project_ids": True,
        "curseforge_web_download_fallback": True,
        "cursemaven_fallback": True,
        "authenticated_cdn_supported": True,
        "api_key_env": "CURSEFORGE_API_KEY",
        "api_key_file": "_crafty/curseforge-api-key.txt",
        "launcher_in_update_overlay": True,
        "world_data_touched": False,
        "world_data_in_update_overlay": False,
    }

    summary = json.loads(SUMMARY.read_text())
    summary["pack_version"] = VERSION
    summary["curseforge_download_fix_0_1_9_40"] = block
    write_json(SUMMARY, summary)

    validation = json.loads(VALIDATION.read_text())
    validation["pack_version"] = VERSION
    validation["curseforge_download_fix_0_1_9_40"] = block
    write_json(VALIDATION, validation)


def update_validator() -> None:
    text = VALIDATE.read_text()
    text = text.replace('.version == "0.1.9-39"', '.version == "0.1.9-40"')
    text = text.replace('.pack_version == "0.1.9-39"', '.pack_version == "0.1.9-40"')
    marker = "# 0.1.9-40 CurseForge downloader compatibility checks"
    if marker not in text:
        text += r'''

# 0.1.9-40 CurseForge downloader compatibility checks
jq -e '.curseforge_download_fix_0_1_9_40.server_manifest_has_project_ids == true and .curseforge_download_fix_0_1_9_40.curseforge_web_download_fallback == true and .curseforge_download_fix_0_1_9_40.cursemaven_fallback == true and .curseforge_download_fix_0_1_9_40.authenticated_cdn_supported == true and .curseforge_download_fix_0_1_9_40.launcher_in_update_overlay == true and .curseforge_download_fix_0_1_9_40.world_data_touched == false and .curseforge_download_fix_0_1_9_40.world_data_in_update_overlay == false' "$validation" >/dev/null
awk -F '\t' 'BEGIN{bad=0} /^#/ || NF==0 {next} NF!=6 {bad++} $1!="0" && ($6=="" || $6=="0") {bad++} END{exit bad?1:0}' "$repo_dir/server/_crafty/server-mods.tsv" || { echo "0.1.9-40 server mod rows are missing project IDs" >&2; exit 1; }
grep -Fq 'CURSEFORGE_API_KEY' "$repo_dir/server/_crafty/source/AmberArcanaCraftyLauncher.java" || { echo "Launcher API-key support missing" >&2; exit 1; }
grep -Fq 'www.curseforge.com/api/v1/mods/' "$repo_dir/server/_crafty/source/AmberArcanaCraftyLauncher.java" || { echo "Launcher CurseForge web fallback missing" >&2; exit 1; }
grep -Fq 'cursemaven.com' "$repo_dir/server/_crafty/source/AmberArcanaCraftyLauncher.java" || { echo "Launcher CurseMaven fallback missing" >&2; exit 1; }
update_overlay="$repo_dir/dist/Amber-and-Arcana-${version}-Crafty-Update-Overlay.zip"
test "$(unzip -Z1 "$update_overlay" | grep -Fxc 'AmberArcana-Crafty-Launcher.jar')" = "1" || { echo "Updated Crafty launcher missing from update overlay" >&2; exit 1; }
if unzip -Z1 "$update_overlay" | grep -Ei '(^|/)(world|world_nether|world_the_end)(/|$)' >/dev/null; then echo "World data leaked into update overlay" >&2; exit 1; fi
'''
    VALIDATE.write_text(text)


def update_docs() -> None:
    if CHANGELOG.exists():
        old = CHANGELOG.read_text()
        if f"## {VERSION}" not in old:
            CHANGELOG.write_text(
                f"## {VERSION}\n\n"
                "- Fixed Crafty server mod downloads after CurseForge enforced API-key authentication on direct CDN requests.\n"
                "- Added project IDs to the dedicated-server mod manifest and no-key CurseForge website/CurseMaven fallbacks.\n"
                "- Added optional authenticated CDN support through CURSEFORGE_API_KEY or _crafty/curseforge-api-key.txt.\n"
                "- The world-safe Crafty update overlay now includes the updated bootstrap launcher itself.\n\n" + old
            )
    if README.exists():
        text = README.read_text()
        if "0.1.9-40 CurseForge downloader" not in text:
            text += (
                "\n\n### 0.1.9-40 CurseForge downloader\n"
                "Crafty can again populate a missing server mods directory after CurseForge's July 2026 CDN authentication change. "
                "The launcher first uses an authenticated CDN when CURSEFORGE_API_KEY is configured, otherwise it uses validated CurseForge web and CurseMaven fallbacks. "
                "The update overlay contains no world save data.\n"
            )
            README.write_text(text)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    rows, mapped = enrich_server_mods(manifest)
    update_release_metadata(rows, mapped)
    update_validator()
    update_docs()
    print(f"Applied {VERSION}: {mapped}/{rows} downloadable server mod rows now carry CurseForge project IDs")


if __name__ == "__main__":
    main()
