#!/usr/bin/env python3
"""Amber & Arcana 0.1.9-19: manage JEI on the Crafty dedicated server.

The client already uses JEI 15.20.0.106 (CurseForge file 6075247).
This hotfix adds the same JEI build to the server-managed mod list so recipe
transfer/autofill integrations that require server-side JEI can operate.
It also makes the build emit a tiny Crafty-root overlay ZIP containing only
_crafty/server-mods.tsv for existing 0.1.9-18 servers.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-19"
JEI_PROJECT = 238222
JEI_FILE = 6075247
JEI_VERSION = "15.20.0.106"
JEI_JAR = f"jei-1.20.1-forge-{JEI_VERSION}.jar"
JEI_ROW = f"{JEI_FILE}\t{JEI_JAR}\t\tjei\tJust Enough Items (JEI)"


def dump_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_manifest() -> int:
    path = ROOT / "client/manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = VERSION
    data["name"] = f"Amber & Arcana {VERSION}"
    matches = [e for e in data.get("files", []) if e.get("projectID") == JEI_PROJECT]
    if len(matches) != 1 or matches[0].get("fileID") != JEI_FILE:
        raise SystemExit("Client JEI pin is not 238222:6075247")
    dump_json(path, data)
    return len(data.get("files", []))


def patch_server_tsv() -> int:
    path = ROOT / "server/_crafty/server-mods.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    for line in lines:
        if not line or line.startswith("#"):
            out.append(line)
            continue
        cols = line.split("\t", 4)
        filename = cols[1] if len(cols) > 1 else ""
        slug = cols[3] if len(cols) > 3 else ""
        if slug == "jei" or filename.startswith("jei-"):
            continue
        out.append(line)
    out.append(JEI_ROW)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return sum(1 for line in out if line and not line.startswith("#"))


def patch_server_inventory() -> int:
    path = ROOT / "server/pack-information/mod-files.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    filtered = []
    for entry in data:
        pid = entry.get("projectID", entry.get("projectId"))
        slug = str(entry.get("slug", "")).lower()
        filename = str(entry.get("filename", "")).lower()
        if pid == JEI_PROJECT or slug == "jei" or filename.startswith("jei-"):
            continue
        filtered.append(entry)
    filtered.append({
        "slug": "jei",
        "name": "Just Enough Items (JEI)",
        "projectID": JEI_PROJECT,
        "fileID": JEI_FILE,
        "filename": JEI_JAR,
        "source": f"https://www.curseforge.com/minecraft/mc-mods/jei/files/{JEI_FILE}",
        "mods": [{"id": "jei", "version": JEI_VERSION}],
        "bundled_mods": [],
    })
    dump_json(path, filtered)
    return len(filtered)


def patch_summary(manifest_count: int, server_count: int) -> None:
    path = ROOT / "server/_crafty/build-summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pack_version"] = VERSION
    data["manifest_entries"] = manifest_count
    data["server_mod_downloads"] = server_count
    data["server_mod_count"] = server_count
    data["server_jei_0_1_9_19"] = {
        "enabled": True,
        "project_id": JEI_PROJECT,
        "file_id": JEI_FILE,
        "version": JEI_VERSION,
        "filename": JEI_JAR,
        "reason": "Server-side JEI requested for recipe transfer/autofill integrations",
        "crafty_overlay": f"Amber-and-Arcana-{VERSION}-Crafty-JEI-Overlay.zip",
    }
    dump_json(path, data)


def patch_validation(path: Path, server_inventory_count: int | None = None) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pack_version"] = VERSION
    if server_inventory_count is not None and "mod_files" in data:
        data["mod_files"] = server_inventory_count
    data["server_jei_0_1_9_19"] = {
        "enabled": True,
        "project_id": JEI_PROJECT,
        "file_id": JEI_FILE,
        "version": JEI_VERSION,
        "client_server_same_version": True,
        "runtime_tested": False,
    }
    dump_json(path, data)


def patch_validate_viewer() -> None:
    path = ROOT / "scripts/validate-viewer.py"
    text = path.read_text(encoding="utf-8")
    old = 'assert not [row for row in rows if len(row) >= 4 and (row[3] == "jei" or row[1].startswith("jei-"))], "JEI should be client-only for this hotfix"'
    new = f'''server_jei = [row for row in rows if len(row) >= 4 and (row[3] == "jei" or row[1].startswith("jei-"))]\nassert len(server_jei) == 1, "Expected exactly one server JEI entry"\nassert server_jei[0][0] == "{JEI_FILE}" and server_jei[0][1] == "{JEI_JAR}", "Server JEI pin differs from client"'''
    if old in text:
        text = text.replace(old, new)
    elif "Expected exactly one server JEI entry" not in text:
        raise SystemExit("Could not patch validate-viewer server JEI assertion")
    text = text.replace("server viewer cleanup", "matching server JEI pin")
    path.write_text(text, encoding="utf-8")


def patch_validate_sh() -> None:
    path = ROOT / "scripts/validate.sh"
    text = path.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-18"', f'.version == "{VERSION}"')
    text = text.replace('.pack_version == "0.1.9-18"', f'.pack_version == "{VERSION}"')
    text = text.replace('Amber & Arcana 0.1.9-18 static validation passed', f'Amber & Arcana {VERSION} static validation passed')
    marker = "grep -Fxq 'twilightforest-1.20.1-4.3.2508-universal.jar'"
    check = f'''test "$(awk -F '\\t' '$4 == "jei" && $1 == "{JEI_FILE}" && $2 == "{JEI_JAR}" {{n++}} END {{print n+0}}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || {{ echo "Expected matching JEI {JEI_VERSION} on server" >&2; exit 1; }}\n\n'''
    if "Expected matching JEI 15.20.0.106 on server" not in text:
        idx = text.find(marker)
        if idx == -1:
            raise SystemExit("Could not locate server validation insertion point")
        text = text[:idx] + check + text[idx:]
    overlay_check = '''overlay="$repo_dir/dist/Amber-and-Arcana-${version}-Crafty-JEI-Overlay.zip"\ntest -f "$overlay" || { echo "Crafty JEI overlay missing" >&2; exit 1; }\nunzip -tq "$overlay"\ntest "$(unzip -Z1 "$overlay" | grep -Fxc '_crafty/server-mods.tsv')" = "1" || { echo "Crafty JEI overlay has unexpected layout" >&2; exit 1; }\n'''
    archive_marker = 'unzip -tq "$repo_dir/dist/Amber-and-Arcana-${version}-Client.zip"'
    if "Crafty JEI overlay missing" not in text:
        text = text.replace(archive_marker, overlay_check + "\n" + archive_marker)
    path.write_text(text, encoding="utf-8")


def patch_build() -> None:
    path = ROOT / "scripts/build.sh"
    text = path.read_text(encoding="utf-8")
    overlay = '''# Small overlay for an existing Crafty server: extract at the server root.\nrm -f "$dist_dir/Amber-and-Arcana-${version}-Crafty-JEI-Overlay.zip"\n(\n  cd "$repo_dir/server"\n  zip -q "$dist_dir/Amber-and-Arcana-${version}-Crafty-JEI-Overlay.zip" _crafty/server-mods.tsv\n)\n\n'''
    if "Crafty-JEI-Overlay.zip" not in text:
        marker = 'echo "Built Amber & Arcana ${version}"'
        if marker not in text:
            raise SystemExit("Could not locate final build message in build.sh")
        text = text.replace(marker, overlay + marker)
    path.write_text(text, encoding="utf-8")


def patch_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("0.1.9-18", VERSION)
    old = "JEI remains omitted from the dedicated server."
    new = f"The matching JEI {JEI_VERSION} build is now also managed on the dedicated server for recipe transfer/autofill support."
    text = text.replace(old, new)
    section = f'''\n## Crafty JEI overlay\n\nFor an existing server, download `dist/Amber-and-Arcana-{VERSION}-Crafty-JEI-Overlay.zip`, stop the server, and extract it into the Crafty server root (the folder containing `AmberArcana-Crafty-Launcher.jar`) with overwrite enabled. The overlay contains only `_crafty/server-mods.tsv`; on the next start the launcher downloads `{JEI_JAR}` into `mods/`. It does not contain or overwrite the world.\n'''
    if "## Crafty JEI overlay" not in text:
        text += section
    path.write_text(text, encoding="utf-8")


def patch_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-19" not in text:
        entry = f'''## 0.1.9-19 — Server JEI / Crafty overlay\n\n- Add JEI {JEI_VERSION} (CurseForge {JEI_PROJECT}:{JEI_FILE}) to the Crafty dedicated-server managed mod list.\n- Keep client and server on the exact same JEI build.\n- Add a tiny Crafty-root overlay ZIP containing only `_crafty/server-mods.tsv` for existing servers.\n- Preserve Twilight Forest removal and the Eternal Steak chest-loot filter.\n\n'''
        text = text.replace("# Changelog\n\n", "# Changelog\n\n" + entry, 1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    manifest_count = patch_manifest()
    server_count = patch_server_tsv()
    inv_count = patch_server_inventory()
    patch_summary(manifest_count, server_count)
    patch_validation(ROOT / "client/overrides/pack-information/validation.json")
    patch_validation(ROOT / "server/pack-information/validation.json", inv_count)
    patch_validate_viewer()
    patch_validate_sh()
    patch_build()
    patch_readme()
    patch_changelog()
    print(f"Prepared Amber & Arcana {VERSION}: server JEI {JEI_VERSION}; Crafty overlay enabled")


if __name__ == "__main__":
    main()
