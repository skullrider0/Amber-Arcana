#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-47"
PROJECT = 1218668
FILE = 6862342
SLUG = "tcondiadema"
NAME = "Tinker's Domain"
JAR = "Tinkers Domain-1.9fix.jar"

def dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def pid(entry: dict):
    return entry.get("projectID", entry.get("projectId"))

def patch_manifest() -> int:
    path = ROOT / "client/manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["files"] = [e for e in data["files"] if pid(e) != PROJECT]
    data["files"].append({"projectID": PROJECT, "fileID": FILE, "required": True})
    data["files"].sort(key=lambda e: (int(pid(e) or 0), int(e.get("fileID", 0) or 0)))
    data["version"] = VERSION
    data["name"] = "Amber & Arcana " + VERSION
    dump(path, data)
    return len(data["files"])

def patch_server_mods() -> int:
    path = ROOT / "server/_crafty/server-mods.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = next((line for line in lines if line.startswith("#")), "# fileID\tfilename\tsha512\tslug\tname\tprojectID")
    rows = []
    for line in lines:
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) != 6:
            continue
        if cols[5] == str(PROJECT) or cols[3] == SLUG:
            continue
        rows.append(cols)
    rows.append([str(FILE), JAR, "", SLUG, NAME, str(PROJECT)])
    rows.sort(key=lambda row: row[4].lower())
    path.write_text(header + "\n" + "\n".join("\t".join(row) for row in rows) + "\n", encoding="utf-8")
    return len(rows)

def patch_inventory(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    data = [e for e in data if pid(e) != PROJECT and str(e.get("slug", "")).lower() != SLUG]
    data.append({
        "slug": SLUG,
        "name": NAME,
        "projectID": PROJECT,
        "fileID": FILE,
        "filename": JAR,
        "source": f"https://www.curseforge.com/minecraft/mc-mods/{SLUG}/files/{FILE}",
        "sha512": "",
        "mods": [{"id": "tcondiadema", "version": "1.9"}],
        "bundled_mods": [],
    })
    data.sort(key=lambda e: str(e.get("name", e.get("slug", ""))).lower())
    dump(path, data)
    return len(data)

def marker() -> dict:
    return {
        "missing_dependency_fixed": True,
        "dependency_mod_id": "tcondiadema",
        "required_by": "vampirismtinker",
        "minimum_version": "1.5",
        "project_id": PROJECT,
        "file_id": FILE,
        "filename": JAR,
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
    summary["vampirism_tinker_dependency_fix_0_1_9_47"] = marker()
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
        data["vampirism_tinker_dependency_fix_0_1_9_47"] = marker()
        dump(path, data)

def patch_modlist() -> None:
    path = ROOT / "client/modlist.html"
    text = path.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if f"/{SLUG}/files/" not in line and JAR not in line]
    row = f'<li><a href="https://www.curseforge.com/minecraft/mc-mods/{SLUG}/files/{FILE}">Tinker&#x27;s Domain</a> — {JAR}</li>'
    insert_at = next((i for i, line in enumerate(lines) if "tinkers-construct/files/" in line), max(0, len(lines) - 2))
    lines.insert(insert_at + 1, row)
    text = "\n".join(lines) + "\n"
    text = re.sub(r"<title>Amber &amp; Arcana [^<]+ mod list</title>", f"<title>Amber &amp; Arcana {VERSION} mod list</title>", text)
    text = re.sub(r"<h1>Amber &amp; Arcana [^<]+</h1>", f"<h1>Amber &amp; Arcana {VERSION}</h1>", text)
    text = re.sub(r"<p>\d+ pinned CurseForge mod/library files plus the local More Hitboxes performance patch\.</p>", "<p>298 pinned CurseForge mod/library files plus the local More Hitboxes performance patch.</p>", text)
    path.write_text(text, encoding="utf-8")

def patch_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    direct = f"[Download Client {VERSION}](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Client.zip) · [Download Crafty Server {VERSION}](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Server.zip) · [Update existing Crafty server](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Crafty-Update-Overlay.zip)"
    text = re.sub(r"\[Download Client[^\n]+", direct, text, count=1)
    text = re.sub(r"\| Pack \| [^|]+\|", f"| Pack | {VERSION} |", text, count=1)
    text = re.sub(r"\| Client manifest entries \| [^|]+\|", "| Client manifest entries | 298 + 1 local patched JAR |", text, count=1)
    text = re.sub(r"\| Server managed mod entries \| [^|]+\|", "| Server managed mod entries | 278 |", text, count=1)
    text = text.replace("Amber-and-Arcana-0.1.9-46-Client.zip", f"Amber-and-Arcana-{VERSION}-Client.zip")
    text = text.replace("Amber-and-Arcana-0.1.9-46-Server.zip", f"Amber-and-Arcana-{VERSION}-Server.zip")
    text = text.replace("Amber-and-Arcana-0.1.9-46-Crafty-Update-Overlay.zip", f"Amber-and-Arcana-{VERSION}-Crafty-Update-Overlay.zip")
    if "### 0.1.9-47 Vampirism Tinker dependency fix" not in text:
        text += "\n\n### 0.1.9-47 Vampirism Tinker dependency fix\nAdds Tinker's Domain (tcondiadema) 1.9fix, required by Vampirism Tinker 1.6. No quests or world/player data are changed.\n"
    path.write_text(text, encoding="utf-8")

def patch_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-47" not in text:
        entry = f"""## 0.1.9-47 — Vampirism Tinker dependency fix

- Add Tinker's Domain / tcondiadema (CurseForge {PROJECT}:{FILE}, {JAR}).
- Fix dedicated-server startup: Vampirism Tinker 1.6 requires tcondiadema 1.5 or newer.
- Add the dependency to both client and Crafty managed server lists.
- Preserve the seven Vampirism addons, Iron Chests removal, More Hitboxes/performance fixes, and existing quests.
- No world/player data is included in the update overlay.

"""
        text = text.replace("# Changelog\n\n", "# Changelog\n\n" + entry, 1)
    path.write_text(text, encoding="utf-8")

def patch_validator() -> None:
    path = ROOT / "scripts/validate.sh"
    text = path.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-46"', '.version == "0.1.9-47"', 1)
    text = text.replace('.pack_version == "0.1.9-46"', '.pack_version == "0.1.9-47"', 1)
    text = text.replace('echo "Amber & Arcana 0.1.9-46 static validation passed"', 'echo "Amber & Arcana 0.1.9-47 static validation passed"', 1)
    text = text.replace('= "297" || { echo "Expected 297 client manifest entries"', '= "298" || { echo "Expected 298 client manifest entries"')
    text = text.replace('= "277" || { echo "Expected 277 server mod rows"', '= "278" || { echo "Expected 278 server mod rows"')
    if "# 0.1.9-47 Vampirism Tinker dependency checks" not in text:
        text += f"""
# 0.1.9-47 Vampirism Tinker dependency checks
test "$(jq '[.files[] | select(.projectID == {PROJECT} and .fileID == {FILE})] | length' "$manifest")" = "1" || {{ echo "Missing 0.1.9-47 Tinker Domain client pin" >&2; exit 1; }}
test "$(awk -F '\t' '$1 == "{FILE}" && $2 == "{JAR}" && $4 == "{SLUG}" && $6 == "{PROJECT}" {{n++}} END {{print n+0}}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || {{ echo "Missing 0.1.9-47 Tinker Domain server pin" >&2; exit 1; }}
jq -e '.vampirism_tinker_dependency_fix_0_1_9_47.missing_dependency_fixed == true and .vampirism_tinker_dependency_fix_0_1_9_47.dependency_mod_id == "tcondiadema" and .vampirism_tinker_dependency_fix_0_1_9_47.minimum_version == "1.5" and .vampirism_tinker_dependency_fix_0_1_9_47.quest_progression_changed == false and .vampirism_tinker_dependency_fix_0_1_9_47.world_data_touched == false' "$validation" >/dev/null
"""
    path.write_text(text, encoding="utf-8")

def main() -> None:
    manifest_count = patch_manifest()
    server_count = patch_server_mods()
    client_count = patch_inventory(ROOT / "client/overrides/pack-information/mod-files.json")
    server_inventory_count = patch_inventory(ROOT / "server/pack-information/mod-files.json")
    patch_metadata(manifest_count, server_count, client_count, server_inventory_count)
    patch_modlist()
    patch_readme()
    patch_changelog()
    patch_validator()
    print(f"Prepared Amber & Arcana {VERSION}: added {NAME}; {manifest_count} client entries, {server_count} server entries")

if __name__ == "__main__":
    main()
