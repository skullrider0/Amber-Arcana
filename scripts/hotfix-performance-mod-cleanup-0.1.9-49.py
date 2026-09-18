#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-49"

REMOVE = [
    {
        "project": 250498,
        "file": 7815705,
        "slug": "mowzies-mobs",
        "jar": "mowziesmobs-1.8.2.jar",
        "name": "Mowzie's Mobs",
    },
    {
        "project": 457252,
        "file": 4779746,
        "slug": "untamedwilds",
        "jar": "untamedwilds-1.20.1-4.0.4.jar",
        "name": "Untamed Wilds",
    },
]
REMOVE_PROJECTS = {x["project"] for x in REMOVE}
REMOVE_FILES = {x["file"] for x in REMOVE}
REMOVE_SLUGS = {x["slug"] for x in REMOVE}
REMOVE_JARS = {x["jar"] for x in REMOVE}

def dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def pid(entry: dict):
    return entry.get("projectID", entry.get("projectId"))

def patch_manifest() -> int:
    path = ROOT / "client/manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["files"] = [
        e for e in data["files"]
        if pid(e) not in REMOVE_PROJECTS and e.get("fileID") not in REMOVE_FILES
    ]
    data["version"] = VERSION
    data["name"] = "Amber & Arcana " + VERSION
    dump(path, data)
    return len(data["files"])

def patch_server_mods() -> int:
    path = ROOT / "server/_crafty/server-mods.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = next((line for line in lines if line.startswith("#")), "# fileID\tfilename\tsha512\tslug\tname\tprojectID")
    kept = []
    for line in lines:
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) != 6:
            continue
        file_id, filename, _hash, slug, _name, project = cols
        if filename in REMOVE_JARS or slug in REMOVE_SLUGS or (project.isdigit() and int(project) in REMOVE_PROJECTS) or (file_id.isdigit() and int(file_id) in REMOVE_FILES):
            continue
        kept.append(cols)
    path.write_text(header + "\n" + "\n".join("\t".join(row) for row in kept) + "\n", encoding="utf-8")
    return len(kept)

def patch_inventory(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    data = [
        e for e in data
        if pid(e) not in REMOVE_PROJECTS
        and e.get("fileID") not in REMOVE_FILES
        and str(e.get("slug", "")).lower() not in REMOVE_SLUGS
        and str(e.get("filename", "")) not in REMOVE_JARS
    ]
    dump(path, data)
    return len(data)

def patch_remove_list() -> None:
    path = ROOT / "server/_crafty/remove-mods.txt"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    if "# Removed in Amber & Arcana 0.1.9-49 for server performance." not in lines:
        lines.append("# Removed in Amber & Arcana 0.1.9-49 for server performance.")
    for jar in sorted(REMOVE_JARS):
        if jar not in lines:
            lines.append(jar)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def marker() -> dict:
    return {
        "reason": "server performance cleanup after Spark profiling",
        "mowzies_mobs_removed": True,
        "untamed_wilds_removed": True,
        "removed_projects": sorted(REMOVE_PROJECTS),
        "removed_files": sorted(REMOVE_FILES),
        "client_update_required": True,
        "server_update_required": True,
        "quest_progression_changed": False,
        "world_data_touched": False,
    }

def patch_metadata(manifest_count: int, server_count: int, client_count: int, server_inventory_count: int) -> None:
    summary_path = ROOT / "server/_crafty/build-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["version"] = VERSION
    summary["pack_version"] = VERSION
    summary["manifest_entries"] = manifest_count
    summary["server_mod_downloads"] = server_count
    summary["performance_mod_cleanup_0_1_9_49"] = marker()
    dump(summary_path, summary)

    for rel, count in [
        ("client/overrides/pack-information/validation.json", client_count),
        ("server/pack-information/validation.json", server_inventory_count),
    ]:
        path = ROOT / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        data["pack_version"] = VERSION
        if "mod_files" in data:
            data["mod_files"] = count
        data["performance_mod_cleanup_0_1_9_49"] = marker()
        dump(path, data)

def patch_modlist() -> None:
    path = ROOT / "client/modlist.html"
    text = path.read_text(encoding="utf-8")
    lines = []
    for line in text.splitlines():
        if any("/" + item["slug"] + "/files/" in line or item["jar"] in line for item in REMOVE):
            continue
        lines.append(line)
    text = "\n".join(lines) + "\n"
    text = re.sub(r"<title>Amber &amp; Arcana [^<]+ mod list</title>", f"<title>Amber &amp; Arcana {VERSION} mod list</title>", text)
    text = re.sub(r"<h1>Amber &amp; Arcana [^<]+</h1>", f"<h1>Amber &amp; Arcana {VERSION}</h1>", text)
    text = re.sub(r"<p>\d+ pinned CurseForge mod/library files plus the local More Hitboxes performance patch\.</p>", "<p>294 pinned CurseForge mod/library files plus the local More Hitboxes performance patch.</p>", text)
    path.write_text(text, encoding="utf-8")

def patch_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    direct = f"[Download Client {VERSION}](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Client.zip) · [Download Crafty Server {VERSION}](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Server.zip) · [Update existing Crafty server](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Crafty-Update-Overlay.zip)"
    text = re.sub(r"\[Download Client[^\n]+", direct, text, count=1)
    text = re.sub(r"\| Pack \| [^|]+\|", f"| Pack | {VERSION} |", text, count=1)
    text = re.sub(r"\| Client manifest entries \| [^|]+\|", "| Client manifest entries | 294 + 1 local patched JAR |", text, count=1)
    text = re.sub(r"\| Server managed mod entries \| [^|]+\|", "| Server managed mod entries | 274 |", text, count=1)
    text = re.sub(r"dist/Amber-and-Arcana-0\.1\.9-\d+-Client\.zip", f"dist/Amber-and-Arcana-{VERSION}-Client.zip", text, count=1)
    text = re.sub(r"dist/Amber-and-Arcana-0\.1\.9-\d+-Server\.zip", f"dist/Amber-and-Arcana-{VERSION}-Server.zip", text, count=1)
    text = re.sub(r"dist/Amber-and-Arcana-0\.1\.9-\d+-Crafty-Update-Overlay\.zip", f"dist/Amber-and-Arcana-{VERSION}-Crafty-Update-Overlay.zip", text, count=1)
    if "### 0.1.9-49 performance mod cleanup" not in text:
        text += "\n\n### 0.1.9-49 performance mod cleanup\nRemoves Mowzie's Mobs and Untamed Wilds from client and server after the latest Spark performance pass. Existing Crafty installs delete mowziesmobs-1.8.2.jar and untamedwilds-1.20.1-4.0.4.jar on the next launcher start. Quest progression and world/player data are unchanged.\n"
    path.write_text(text, encoding="utf-8")

def patch_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-49" not in text:
        entry = """## 0.1.9-49 — Performance mod cleanup

- Remove Mowzie's Mobs from client and server.
- Remove Untamed Wilds from client and server.
- Add stale-JAR cleanup for mowziesmobs-1.8.2.jar and untamedwilds-1.20.1-4.0.4.jar on existing Crafty installs.
- Preserve the More Hitboxes Fossils compatibility patch and all existing quest progression.
- No world/player data is included in the update overlay.

"""
        text = text.replace("# Changelog\n\n", "# Changelog\n\n" + entry, 1)
    path.write_text(text, encoding="utf-8")

def patch_validator() -> None:
    path = ROOT / "scripts/validate.sh"
    text = path.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-48"', '.version == "0.1.9-49"', 1)
    text = text.replace('.pack_version == "0.1.9-48"', '.pack_version == "0.1.9-49"', 1)
    text = text.replace('echo "Amber & Arcana 0.1.9-48 static validation passed"', 'echo "Amber & Arcana 0.1.9-49 static validation passed"', 1)
    text = text.replace('= "296" || { echo "Expected 296 client manifest entries"', '= "294" || { echo "Expected 294 client manifest entries"')
    text = text.replace('= "276" || { echo "Expected 276 server mod rows"', '= "274" || { echo "Expected 274 server mod rows"')
    if "# 0.1.9-49 performance mod cleanup" not in text:
        text += """
# 0.1.9-49 performance mod cleanup
test "$(jq '[.files[] | select(.projectID == 250498 or .fileID == 7815705 or .projectID == 457252 or .fileID == 4779746)] | length' "$manifest")" = "0" || { echo "Removed performance-heavy mods remain in client manifest" >&2; exit 1; }
if awk -F '\t' '$1=="7815705" || $1=="4779746" || $6=="250498" || $6=="457252" {bad=1} END{exit bad?0:1}' "$repo_dir/server/_crafty/server-mods.tsv"; then echo "Mowzie's Mobs or Untamed Wilds remains in server mod list" >&2; exit 1; fi
grep -Fxq 'mowziesmobs-1.8.2.jar' "$repo_dir/server/_crafty/remove-mods.txt" || { echo "Mowzie's Mobs stale-jar cleanup missing" >&2; exit 1; }
grep -Fxq 'untamedwilds-1.20.1-4.0.4.jar' "$repo_dir/server/_crafty/remove-mods.txt" || { echo "Untamed Wilds stale-jar cleanup missing" >&2; exit 1; }
jq -e '.performance_mod_cleanup_0_1_9_49.mowzies_mobs_removed == true and .performance_mod_cleanup_0_1_9_49.untamed_wilds_removed == true and .performance_mod_cleanup_0_1_9_49.quest_progression_changed == false and .performance_mod_cleanup_0_1_9_49.world_data_touched == false' "$validation" >/dev/null
"""
    path.write_text(text, encoding="utf-8")

def main() -> None:
    manifest_count = patch_manifest()
    server_count = patch_server_mods()
    client_count = patch_inventory(ROOT / "client/overrides/pack-information/mod-files.json")
    server_inventory_count = patch_inventory(ROOT / "server/pack-information/mod-files.json")
    patch_remove_list()
    patch_metadata(manifest_count, server_count, client_count, server_inventory_count)
    patch_modlist()
    patch_readme()
    patch_changelog()
    patch_validator()
    print(f"Prepared Amber & Arcana {VERSION}: removed Mowzie's Mobs and Untamed Wilds; {manifest_count} client entries, {server_count} server entries")

if __name__ == "__main__":
    main()
