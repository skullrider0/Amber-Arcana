#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-48"

REMOVE = [
    {
        "project": 1314650,
        "file": 6814093,
        "slug": "vampirism-tinker",
        "jar": "vampirismtinker-1.6.jar",
        "name": "Vampirism Tinker",
    },
    {
        "project": 1218668,
        "file": 6862342,
        "slug": "tcondiadema",
        "jar": "Tinkers Domain-1.9fix.jar",
        "name": "Tinker's Domain",
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
    for jar in sorted(REMOVE_JARS):
        if jar not in lines:
            lines.append(jar)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def marker() -> dict:
    return {
        "reason": "Vampirism Tinker 1.6 loads ClientDiademaRegister on DEDICATED_SERVER and crashes Forge during mod construction",
        "vampirism_tinker_removed": True,
        "tinkers_domain_removed": True,
        "active_vampirism_addons_from_0_1_9_46": 6,
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
    summary["vampirism_tinker_dedicated_server_fix_0_1_9_48"] = marker()
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
        data["vampirism_tinker_dedicated_server_fix_0_1_9_48"] = marker()
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
    text = re.sub(r"<p>\d+ pinned CurseForge mod/library files plus the local More Hitboxes performance patch\.</p>", "<p>296 pinned CurseForge mod/library files plus the local More Hitboxes performance patch.</p>", text)
    path.write_text(text, encoding="utf-8")

def patch_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    direct = f"[Download Client {VERSION}](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Client.zip) · [Download Crafty Server {VERSION}](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Server.zip) · [Update existing Crafty server](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Crafty-Update-Overlay.zip)"
    text = re.sub(r"\[Download Client[^\n]+", direct, text, count=1)
    text = re.sub(r"\| Pack \| [^|]+\|", f"| Pack | {VERSION} |", text, count=1)
    text = re.sub(r"\| Client manifest entries \| [^|]+\|", "| Client manifest entries | 296 + 1 local patched JAR |", text, count=1)
    text = re.sub(r"\| Server managed mod entries \| [^|]+\|", "| Server managed mod entries | 276 |", text, count=1)
    text = text.replace("Amber-and-Arcana-0.1.9-47-Client.zip", f"Amber-and-Arcana-{VERSION}-Client.zip")
    text = text.replace("Amber-and-Arcana-0.1.9-47-Server.zip", f"Amber-and-Arcana-{VERSION}-Server.zip")
    text = text.replace("Amber-and-Arcana-0.1.9-47-Crafty-Update-Overlay.zip", f"Amber-and-Arcana-{VERSION}-Crafty-Update-Overlay.zip")
    if "### 0.1.9-48 dedicated-server compatibility fix" not in text:
        text += "\n\n### 0.1.9-48 dedicated-server compatibility fix\nRemoves Vampirism Tinker 1.6 because it crashes Forge dedicated servers by loading the client-only ClientDiademaRegister class during mod construction. Tinker's Domain is removed with it because it was added only as Vampirism Tinker's dependency. The other six Vampirism addons remain. Quests and world/player data are unchanged.\n"
    path.write_text(text, encoding="utf-8")

def patch_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-48" not in text:
        entry = """## 0.1.9-48 — Vampirism Tinker dedicated-server compatibility fix

- Remove Vampirism Tinker 1.6 from client and server.
- Remove Tinker's Domain / tcondiadema, which was only required by Vampirism Tinker.
- Add stale-JAR cleanup for vampirismtinker-1.6.jar and Tinkers Domain-1.9fix.jar on existing Crafty installs.
- Keep the other six Vampirism addons from 0.1.9-46.
- Preserve Iron Chests removal, More Hitboxes/performance fixes, spawn balancing, and all existing quest progression.
- No world/player data is included in the update overlay.

"""
        text = text.replace("# Changelog\n\n", "# Changelog\n\n" + entry, 1)
    path.write_text(text, encoding="utf-8")

def patch_validator() -> None:
    path = ROOT / "scripts/validate.sh"
    lines = path.read_text(encoding="utf-8").splitlines()
    filtered = []
    for line in lines:
        if "Missing 0.1.9-46 client pin: Vampirism Tinker" in line:
            continue
        if "Missing 0.1.9-46 server pin: Vampirism Tinker" in line:
            continue
        if "Missing 0.1.9-47 Tinker Domain client pin" in line:
            continue
        if "Missing 0.1.9-47 Tinker Domain server pin" in line:
            continue
        if "vampirism_tinker_dependency_fix_0_1_9_47" in line and line.lstrip().startswith("jq -e"):
            continue
        filtered.append(line)
    text = "\n".join(filtered) + "\n"
    text = text.replace('.version == "0.1.9-47"', '.version == "0.1.9-48"', 1)
    text = text.replace('.pack_version == "0.1.9-47"', '.pack_version == "0.1.9-48"', 1)
    text = text.replace('echo "Amber & Arcana 0.1.9-47 static validation passed"', 'echo "Amber & Arcana 0.1.9-48 static validation passed"', 1)
    text = text.replace('= "298" || { echo "Expected 298 client manifest entries"', '= "296" || { echo "Expected 296 client manifest entries"')
    text = text.replace('= "278" || { echo "Expected 278 server mod rows"', '= "276" || { echo "Expected 276 server mod rows"')
    if "# 0.1.9-48 Vampirism Tinker dedicated-server fix" not in text:
        text += f"""
# 0.1.9-48 Vampirism Tinker dedicated-server fix
test "$(jq '[.files[] | select(.projectID == 1314650 or .fileID == 6814093 or .projectID == 1218668 or .fileID == 6862342)] | length' "$manifest")" = "0" || {{ echo "Dedicated-server-incompatible Vampirism Tinker or its orphan dependency remains in client manifest" >&2; exit 1; }}
if rg -F $'\tvampirism-tinker\t|\ttcondiadema\t' "$repo_dir/server/_crafty/server-mods.tsv" >/dev/null; then echo "Vampirism Tinker or Tinker Domain remains in server mod list" >&2; exit 1; fi
grep -Fxq 'vampirismtinker-1.6.jar' "$repo_dir/server/_crafty/remove-mods.txt" || {{ echo "Vampirism Tinker stale-jar cleanup missing" >&2; exit 1; }}
grep -Fxq 'Tinkers Domain-1.9fix.jar' "$repo_dir/server/_crafty/remove-mods.txt" || {{ echo "Tinker Domain stale-jar cleanup missing" >&2; exit 1; }}
jq -e '.vampirism_tinker_dedicated_server_fix_0_1_9_48.vampirism_tinker_removed == true and .vampirism_tinker_dedicated_server_fix_0_1_9_48.tinkers_domain_removed == true and .vampirism_tinker_dedicated_server_fix_0_1_9_48.active_vampirism_addons_from_0_1_9_46 == 6 and .vampirism_tinker_dedicated_server_fix_0_1_9_48.quest_progression_changed == false and .vampirism_tinker_dedicated_server_fix_0_1_9_48.world_data_touched == false' "$validation" >/dev/null
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
    print(f"Prepared Amber & Arcana {VERSION}: removed dedicated-server-incompatible Vampirism Tinker and orphan Tinker's Domain; {manifest_count} client entries, {server_count} server entries")

if __name__ == "__main__":
    main()
