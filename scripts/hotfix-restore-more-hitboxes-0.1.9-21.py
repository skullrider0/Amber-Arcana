#!/usr/bin/env python3
"""Amber & Arcana 0.1.9-21: restore More Hitboxes on client + server.

Fossils and Archeology Revival 9.3.4.0 hard-requires More Hitboxes >= 1.9.2.
Restore the exact Forge 1.20.1 / More Hitboxes 1.9.2 package metadata that was
present in 0.1.9-19, and remove the 0.1.9-20 Crafty stale-jar deletion rule.

Important performance note: upstream More Hitboxes 1.9.2 has no per-mod or
per-entity whitelist/config option. Its Forge Level mixin hooks entity-query
methods globally. Therefore no fake `fossils_only` config is written here.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-21"
PROJECT_ID = 1115989
FILE_ID = 6942239
SLUG = "more-hitboxes"
JAR = "morehitboxes-forge-1.20.1-1.9.2.jar"
SHA512 = "4540869971009de3cc2c895a61fa1b84a715245202788df7124b6f5a31b82ca9854a2f1a8f14e8033d24669557cf31469d7ce61a0a4c68e90f3cfb83acc007f9"
SOURCE = "https://www.curseforge.com/minecraft/mc-mods/more-hitboxes/files/6942239"
PRE_REMOVAL_REF = "d954ce6d8e084cc8e73d6c0effe6552628e3ac3d"


def dump_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def is_more_hitboxes(entry: dict) -> bool:
    return (
        entry.get("projectID", entry.get("projectId")) == PROJECT_ID
        or entry.get("fileID", entry.get("fileId")) == FILE_ID
        or str(entry.get("slug", "")).lower() == SLUG
        or str(entry.get("filename", "")).lower().startswith("morehitboxes-")
    )


def historical_inventory_entry() -> dict:
    """Reuse the exact metadata captured before 0.1.9-20 when git history exists."""
    rel = "client/overrides/pack-information/mod-files.json"
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{PRE_REMOVAL_REF}:{rel}"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        for entry in json.loads(raw):
            if is_more_hitboxes(entry):
                return entry
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        pass

    # Runtime-critical fields; bundled metadata is informational only.
    return {
        "slug": SLUG,
        "name": "More Hitboxes",
        "projectID": PROJECT_ID,
        "fileID": FILE_ID,
        "filename": JAR,
        "source": SOURCE,
        "sha512": SHA512,
        "mods": [{"id": "morehitboxes", "version": "1.9.2"}],
        "bundled_mods": [],
    }


def patch_manifest() -> int:
    path = ROOT / "client/manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    files = [entry for entry in data.get("files", []) if not is_more_hitboxes(entry)]
    files.append({"projectID": PROJECT_ID, "fileID": FILE_ID, "required": True})
    data["files"] = files
    data["version"] = VERSION
    data["name"] = f"Amber & Arcana {VERSION}"
    dump_json(path, data)
    return len(files)


def patch_inventory(path: Path, entry: dict) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    data = [item for item in data if not is_more_hitboxes(item)]

    # Restore close to its previous alphabetical position without reordering the file.
    insert_at = next(
        (idx for idx, item in enumerate(data) if str(item.get("slug", "")).lower() == "mowzies-mobs"),
        len(data),
    )
    data.insert(insert_at, entry)
    dump_json(path, data)
    return len(data)


def patch_server_tsv() -> int:
    path = ROOT / "server/_crafty/server-mods.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = [line for line in lines if line.startswith("#")]
    rows = [line for line in lines if line and not line.startswith("#")]

    filtered: list[str] = []
    for line in rows:
        cols = line.split("\t", 4)
        fid = cols[0] if len(cols) > 0 else ""
        filename = cols[1] if len(cols) > 1 else ""
        slug = cols[3] if len(cols) > 3 else ""
        if fid == str(FILE_ID) or slug == SLUG or filename.startswith("morehitboxes-"):
            continue
        filtered.append(line)

    row = f"{FILE_ID}\t{JAR}\t{SHA512}\t{SLUG}\tMore Hitboxes"
    insert_at = next(
        (idx for idx, line in enumerate(filtered) if "\tmowzies-mobs\t" in line),
        len(filtered),
    )
    filtered.insert(insert_at, row)
    path.write_text("\n".join(header + filtered) + "\n", encoding="utf-8")
    return len(filtered)


def patch_remove_list() -> None:
    path = ROOT / "server/_crafty/remove-mods.txt"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    lines = [
        line for line in lines
        if line.strip() != JAR and not line.strip().lower().startswith("morehitboxes-")
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def restoration_metadata() -> dict:
    return {
        "restored": True,
        "project_id": PROJECT_ID,
        "file_id": FILE_ID,
        "version": "1.9.2",
        "filename": JAR,
        "client_and_server": True,
        "required_by": "Fossils and Archeology Revival 9.3.4.0",
        "fossils_only_config_available": False,
        "upstream_behavior": "More Hitboxes 1.9.2 has no per-mod/entity whitelist; Forge Level entity-query mixins remain global",
        "runtime_retest_required": True,
    }


def patch_summary(manifest_count: int, client_inventory_count: int, server_count: int) -> None:
    path = ROOT / "server/_crafty/build-summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pack_version"] = VERSION
    data["manifest_entries"] = manifest_count
    if "mod_metadata_entries" in data:
        data["mod_metadata_entries"] = client_inventory_count
    data["server_mod_downloads"] = server_count
    data["server_mod_count"] = server_count
    if isinstance(data.get("performance_fix_0_1_9_20"), dict):
        data["performance_fix_0_1_9_20"]["superseded_by"] = VERSION
    data["more_hitboxes_restore_0_1_9_21"] = restoration_metadata()
    dump_json(path, data)


def patch_validation(path: Path, mod_count: int) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pack_version"] = VERSION
    if "mod_files" in data:
        data["mod_files"] = mod_count
    if isinstance(data.get("performance_fix_0_1_9_20"), dict):
        data["performance_fix_0_1_9_20"]["superseded_by"] = VERSION
    data["more_hitboxes_restore_0_1_9_21"] = restoration_metadata()
    dump_json(path, data)


def patch_validate_sh() -> None:
    path = ROOT / "scripts/validate.sh"
    text = path.read_text(encoding="utf-8")
    text = text.replace('0.1.9-20', VERSION)
    text = text.replace(
        '.performance_fix_0_1_9_20.more_hitboxes_removed == true',
        '.more_hitboxes_restore_0_1_9_21.restored == true',
    )
    text = text.replace(
        'for removed_project in 310111 521393 388800 628539 544031 430127 255717 227639 1115989; do',
        'for removed_project in 310111 521393 388800 628539 544031 430127 255717 227639; do',
    )

    old = f'''if rg -i 'morehitboxes|more-hitboxes' "$repo_dir/server/_crafty/server-mods.tsv" >/dev/null; then
  echo "More Hitboxes still present in server mod list" >&2
  exit 1
fi
grep -Fxq '{JAR}' "$repo_dir/server/_crafty/remove-mods.txt" || {{ echo "More Hitboxes stale-jar cleanup missing" >&2; exit 1; }}
'''
    new = f'''test "$(jq '[.files[] | select(.projectID == {PROJECT_ID} and .fileID == {FILE_ID})] | length' "$manifest")" = "1" || {{ echo "Expected More Hitboxes 1.9.2 client pin" >&2; exit 1; }}
test "$(awk -F '\\t' '$4 == "{SLUG}" && $1 == "{FILE_ID}" && $2 == "{JAR}" {{n++}} END {{print n+0}}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || {{ echo "Expected More Hitboxes 1.9.2 on server" >&2; exit 1; }}
if grep -Fxq '{JAR}' "$repo_dir/server/_crafty/remove-mods.txt"; then
  echo "More Hitboxes is still scheduled for Crafty deletion" >&2
  exit 1
fi
'''
    if old in text:
        text = text.replace(old, new)
    elif "Expected More Hitboxes 1.9.2 client pin" not in text:
        marker = "grep -Fxq 'twilightforest-1.20.1-4.3.2508-universal.jar'"
        idx = text.find(marker)
        if idx == -1:
            raise SystemExit("Could not locate More Hitboxes validation insertion point")
        text = text[:idx] + new + "\n" + text[idx:]

    path.write_text(text, encoding="utf-8")


def patch_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("Amber & Arcana 0.1.9-20", f"Amber & Arcana {VERSION}")
    note = f'''\nMore Hitboxes note ({VERSION}): **More Hitboxes 1.9.2** is restored on both client and dedicated server because Fossils and Archeology Revival 9.3.4.0 requires it. Upstream More Hitboxes 1.9.2 does not provide a per-mod or per-entity whitelist/config, so there is no valid `fossils_only` setting to enable; its Forge entity-query mixins remain global and should be re-profiled with Spark.\n'''
    if f"More Hitboxes note ({VERSION})" not in text:
        text += note
    path.write_text(text, encoding="utf-8")


def patch_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if f"## {VERSION}" not in text:
        entry = f'''## {VERSION} — Restore More Hitboxes dependency\n\n- Restore More Hitboxes 1.9.2 (CurseForge {PROJECT_ID}:{FILE_ID}) on client and dedicated server.\n- Remove `{JAR}` from Crafty's stale-mod deletion list.\n- Restore the exact pre-0.1.9-20 download metadata and checksum.\n- Confirm upstream More Hitboxes 1.9.2 has no per-mod/entity whitelist or `fossils_only` config option; no nonfunctional config is added.\n- Fossils and Archeology Revival 9.3.4.0 remains the dependency requiring More Hitboxes.\n- Runtime Spark re-profile is still required because the upstream Forge Level entity-query mixins are global.\n\n'''
        text = text.replace("# Changelog\n\n", "# Changelog\n\n" + entry, 1)
    path.write_text(text, encoding="utf-8")


def write_notes() -> None:
    for rel in [
        "client/MORE-HITBOXES-REMOVAL-0.1.9-20.txt",
        "client/overrides/pack-information/MORE-HITBOXES-REMOVAL-0.1.9-20.txt",
        "server/MORE-HITBOXES-REMOVAL-0.1.9-20.txt",
        "server/pack-information/MORE-HITBOXES-REMOVAL-0.1.9-20.txt",
    ]:
        path = ROOT / rel
        if path.exists():
            path.unlink()

    note = f'''Amber & Arcana {VERSION} — More Hitboxes restored\n\nRestored mod: More Hitboxes 1.9.2\nCurseForge project: {PROJECT_ID}\nCurseForge file: {FILE_ID}\nJar: {JAR}\nSides: client + dedicated server\nRequired by: Fossils and Archeology Revival 9.3.4.0\n\nConfiguration check:\nMore Hitboxes 1.9.2 does not expose a per-mod or per-entity whitelist and has no valid `fossils_only` option. The Forge Level entity-query mixins are global, so limiting their performance cost to only Fossils mobs cannot be done through configuration.\n\nRecommended verification after deployment:\nRun a fresh 60-second Spark slow-tick profile and compare the More Hitboxes Level mixin/entity-query cost to the 0.1.9-20 baseline.\n'''
    for rel in [
        f"client/MORE-HITBOXES-RESTORE-{VERSION}.txt",
        f"client/overrides/pack-information/MORE-HITBOXES-RESTORE-{VERSION}.txt",
        f"server/MORE-HITBOXES-RESTORE-{VERSION}.txt",
        f"server/pack-information/MORE-HITBOXES-RESTORE-{VERSION}.txt",
    ]:
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(note, encoding="utf-8")


def main() -> None:
    entry = historical_inventory_entry()
    manifest_count = patch_manifest()
    client_inventory_count = patch_inventory(ROOT / "client/overrides/pack-information/mod-files.json", entry)
    server_inventory_count = patch_inventory(ROOT / "server/pack-information/mod-files.json", entry)
    server_count = patch_server_tsv()
    patch_remove_list()
    patch_summary(manifest_count, client_inventory_count, server_count)
    patch_validation(ROOT / "client/overrides/pack-information/validation.json", client_inventory_count)
    patch_validation(ROOT / "server/pack-information/validation.json", server_inventory_count)
    patch_validate_sh()
    patch_readme()
    patch_changelog()
    write_notes()
    print(f"Prepared Amber & Arcana {VERSION}: More Hitboxes restored to client/server; no fake fossils-only config added")


if __name__ == "__main__":
    main()
