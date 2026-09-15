#!/usr/bin/env python3
"""Amber & Arcana 0.1.9-20: remove More Hitboxes from client and server.

Spark profiling showed More Hitboxes' Level entity-query mixin consuming a large
share of the dedicated-server thread. Remove it from both sides, add its old jar
to Crafty's stale-mod cleanup list, and preserve all 0.1.9-19 JEI changes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-20"
PROJECT_ID = 1115989
FILE_ID = 6942239
SLUG = "more-hitboxes"
JAR = "morehitboxes-forge-1.20.1-1.9.2.jar"


def dump_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def matches_entry(entry: dict) -> bool:
    pid = entry.get("projectID", entry.get("projectId"))
    fid = entry.get("fileID", entry.get("fileId"))
    slug = str(entry.get("slug", "")).lower()
    filename = str(entry.get("filename", "")).lower()
    return (
        pid == PROJECT_ID
        or fid == FILE_ID
        or slug == SLUG
        or filename == JAR.lower()
        or filename.startswith("morehitboxes-")
    )


def patch_manifest() -> int:
    path = ROOT / "client/manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    before = len(data.get("files", []))
    data["files"] = [
        e for e in data.get("files", [])
        if not (e.get("projectID") == PROJECT_ID or e.get("fileID") == FILE_ID)
    ]
    removed = before - len(data["files"])
    if removed != 1:
        raise SystemExit(f"Expected to remove one More Hitboxes manifest entry, removed {removed}")
    data["version"] = VERSION
    data["name"] = f"Amber & Arcana {VERSION}"
    dump_json(path, data)
    return len(data["files"])


def patch_inventory(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    before = len(data)
    data = [e for e in data if not matches_entry(e)]
    removed = before - len(data)
    if removed != 1:
        raise SystemExit(f"Expected to remove one More Hitboxes inventory entry from {path}, removed {removed}")
    dump_json(path, data)
    return len(data)


def patch_server_tsv() -> int:
    path = ROOT / "server/_crafty/server-mods.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    removed = 0
    for line in lines:
        if not line or line.startswith("#"):
            out.append(line)
            continue
        cols = line.split("\t", 4)
        fid = cols[0] if len(cols) > 0 else ""
        filename = cols[1] if len(cols) > 1 else ""
        slug = cols[3] if len(cols) > 3 else ""
        if fid == str(FILE_ID) or slug == SLUG or filename == JAR or filename.startswith("morehitboxes-"):
            removed += 1
            continue
        out.append(line)
    if removed != 1:
        raise SystemExit(f"Expected to remove one More Hitboxes server row, removed {removed}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return sum(1 for line in out if line and not line.startswith("#"))


def patch_remove_list() -> None:
    path = ROOT / "server/_crafty/remove-mods.txt"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    if JAR not in lines:
        lines.append(JAR)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def patch_summary(manifest_count: int, server_count: int) -> None:
    path = ROOT / "server/_crafty/build-summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pack_version"] = VERSION
    data["manifest_entries"] = manifest_count
    data["server_mod_downloads"] = server_count
    data["server_mod_count"] = server_count
    data["performance_fix_0_1_9_20"] = {
        "more_hitboxes_removed": True,
        "project_id": PROJECT_ID,
        "file_id": FILE_ID,
        "filename": JAR,
        "reason": "Spark slow-tick profile showed More Hitboxes entity-query mixin dominating server-thread time",
        "client_and_server": True,
        "crafty_stale_jar_cleanup": True,
    }
    dump_json(path, data)


def patch_validation(path: Path, mod_count: int | None = None) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pack_version"] = VERSION
    if mod_count is not None and "mod_files" in data:
        data["mod_files"] = mod_count
    data["performance_fix_0_1_9_20"] = {
        "more_hitboxes_removed": True,
        "project_id": PROJECT_ID,
        "file_id": FILE_ID,
        "filename": JAR,
        "client_and_server": True,
        "stale_jar_cleanup": True,
        "runtime_retest_required": True,
    }
    dump_json(path, data)


def patch_validate_sh() -> None:
    path = ROOT / "scripts/validate.sh"
    text = path.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-19"', f'.version == "{VERSION}"')
    text = text.replace('.pack_version == "0.1.9-19"', f'.pack_version == "{VERSION}"')
    text = text.replace('Amber & Arcana 0.1.9-19 static validation passed', f'Amber & Arcana {VERSION} static validation passed')

    # Validate the new performance-removal metadata.
    validation_needle = '.jei_dependency_fix_0_1_9_18.file_id == 6075247'
    if '.performance_fix_0_1_9_20.more_hitboxes_removed == true' not in text:
        text = text.replace(
            validation_needle,
            validation_needle + ' and .performance_fix_0_1_9_20.more_hitboxes_removed == true'
        )

    # Add More Hitboxes' CurseForge project to the removed-project assertion.
    old = 'for removed_project in 310111 521393 388800 628539 544031 430127 255717 227639; do'
    new = 'for removed_project in 310111 521393 388800 628539 544031 430127 255717 227639 1115989; do'
    text = text.replace(old, new)

    # Ensure no server row remains and Crafty knows to delete an old installed jar.
    marker = "grep -Fxq 'twilightforest-1.20.1-4.3.2508-universal.jar'"
    check = f'''if rg -i 'morehitboxes|more-hitboxes' "$repo_dir/server/_crafty/server-mods.tsv" >/dev/null; then\n  echo "More Hitboxes still present in server mod list" >&2\n  exit 1\nfi\ngrep -Fxq '{JAR}' "$repo_dir/server/_crafty/remove-mods.txt" || {{ echo "More Hitboxes stale-jar cleanup missing" >&2; exit 1; }}\n\n'''
    if "More Hitboxes stale-jar cleanup missing" not in text:
        idx = text.find(marker)
        if idx == -1:
            raise SystemExit("Could not locate stale-jar validation insertion point")
        text = text[:idx] + check + text[idx:]

    path.write_text(text, encoding="utf-8")


def patch_modlist_html() -> None:
    for path in (ROOT / "client").rglob("*.html"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        original = text
        # Remove normal HTML list entries containing the mod name/slug.
        text = re.sub(
            r"<li\b[^>]*>.*?(?:More Hitboxes|more-hitboxes).*?</li>\s*",
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        # Handle line-oriented generated mod lists too.
        text = "\n".join(
            line for line in text.splitlines()
            if "more hitboxes" not in line.lower() and "more-hitboxes" not in line.lower()
        )
        if original.endswith("\n"):
            text += "\n"
        if text != original:
            path.write_text(text, encoding="utf-8")


def patch_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("0.1.9-19", VERSION)
    note = "\nPerformance note: 0.1.9-20 removes **More Hitboxes** from both client and dedicated server after Spark profiling showed its multipart entity-query mixin consuming a disproportionate share of server-thread time. Existing Crafty servers should remove `morehitboxes-forge-1.20.1-1.9.2.jar` from `mods/` before restarting.\n"
    if "Performance note: 0.1.9-20" not in text:
        text += note
    path.write_text(text, encoding="utf-8")


def patch_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-20" not in text:
        entry = f'''## 0.1.9-20 — More Hitboxes performance removal\n\n- Remove More Hitboxes 1.9.2 from both client and dedicated server.\n- Remove CurseForge project {PROJECT_ID} / file {FILE_ID} from the client manifest and pack inventories.\n- Remove `{JAR}` from Crafty's managed server mod list.\n- Add `{JAR}` to `_crafty/remove-mods.txt` so an updated Crafty server deletes the stale jar automatically.\n- Preserve JEI {"15.20.0.106"} on both client and server, Twilight Forest removal, and the Eternal Steak chest-loot filter.\n\n'''
        text = text.replace("# Changelog\n\n", "# Changelog\n\n" + entry, 1)
    path.write_text(text, encoding="utf-8")


def write_notes() -> None:
    note = f'''Amber & Arcana {VERSION} — More Hitboxes performance removal\n\nRemoved mod: More Hitboxes 1.9.2\nCurseForge project: {PROJECT_ID}\nCurseForge file: {FILE_ID}\nOld jar: {JAR}\nSides: client + dedicated server\n\nReason:\nSpark slow-tick profiling showed More Hitboxes' injected entity-query path taking a disproportionate amount of the main server thread.\n\nExisting Crafty server:\n1. Stop the server.\n2. Delete mods/{JAR}.\n3. Update to the matching 0.1.9-20 server metadata/package when convenient.\n4. Start the server and run another 60-second slow-tick Spark profile.\n'''
    for rel in [
        "client/MORE-HITBOXES-REMOVAL-0.1.9-20.txt",
        "client/overrides/pack-information/MORE-HITBOXES-REMOVAL-0.1.9-20.txt",
        "server/MORE-HITBOXES-REMOVAL-0.1.9-20.txt",
        "server/pack-information/MORE-HITBOXES-REMOVAL-0.1.9-20.txt",
    ]:
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(note, encoding="utf-8")


def main() -> None:
    manifest_count = patch_manifest()
    client_inventory_count = patch_inventory(ROOT / "client/overrides/pack-information/mod-files.json")
    server_inventory_count = patch_inventory(ROOT / "server/pack-information/mod-files.json")
    server_count = patch_server_tsv()
    patch_remove_list()
    patch_summary(manifest_count, server_count)
    patch_validation(ROOT / "client/overrides/pack-information/validation.json", client_inventory_count)
    patch_validation(ROOT / "server/pack-information/validation.json", server_inventory_count)
    patch_validate_sh()
    patch_modlist_html()
    patch_readme()
    patch_changelog()
    write_notes()
    print(f"Prepared Amber & Arcana {VERSION}: More Hitboxes removed from client/server and stale-jar cleanup enabled")


if __name__ == "__main__":
    main()
