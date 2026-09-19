#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-52"

MODS = [
    {
        "project": 237749,
        "file": 5096038,
        "slug": "coroutil",
        "name": "CoroUtil",
        "jar": "coroutil-forge-1.20.1-1.3.7.jar",
        "mod_id": "coroutil",
        "mod_version": "1.20.1-1.3.7",
    },
    {
        "project": 974401,
        "file": 7594372,
        "slug": "mobtimizations",
        "name": "Mobtimizations - Entity Performance Fixes",
        "jar": "mobtimizations-forge-1.20.1-1.0.1.jar",
        "mod_id": "mobtimizations",
        "mod_version": "1.20.1-1.0.1",
    },
]


def dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def pid(entry: dict):
    return entry.get("projectID", entry.get("projectId"))


def patch_manifest() -> int:
    path = ROOT / "client/manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    projects = {m["project"] for m in MODS}
    data["files"] = [e for e in data["files"] if pid(e) not in projects]
    for mod in MODS:
        data["files"].append({
            "projectID": mod["project"],
            "fileID": mod["file"],
            "required": True,
        })
    data["files"].sort(key=lambda e: (int(pid(e) or 0), int(e.get("fileID", 0) or 0)))
    data["version"] = VERSION
    data["name"] = "Amber & Arcana " + VERSION
    dump(path, data)
    return len(data["files"])


def patch_server_mods() -> int:
    path = ROOT / "server/_crafty/server-mods.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = next((line for line in lines if line.startswith("#")), "# fileID\tfilename\tsha512\tslug\tname\tprojectID")
    projects = {str(m["project"]) for m in MODS}
    slugs = {m["slug"] for m in MODS}
    jars = {m["jar"] for m in MODS}

    rows = []
    for line in lines:
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) != 6:
            raise SystemExit(f"Malformed server mod row: {line}")
        if cols[5] in projects or cols[3] in slugs or cols[1] in jars:
            continue
        rows.append(cols)

    for mod in MODS:
        rows.append([
            str(mod["file"]),
            mod["jar"],
            "",
            mod["slug"],
            mod["name"],
            str(mod["project"]),
        ])

    rows.sort(key=lambda row: (row[4].lower(), row[1].lower()))
    path.write_text(header + "\n" + "\n".join("\t".join(row) for row in rows) + "\n", encoding="utf-8")
    return len(rows)


def patch_inventory(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    projects = {m["project"] for m in MODS}
    slugs = {m["slug"] for m in MODS}
    data = [
        e for e in data
        if pid(e) not in projects and str(e.get("slug", "")).lower() not in slugs
    ]
    for mod in MODS:
        data.append({
            "slug": mod["slug"],
            "name": mod["name"],
            "projectID": mod["project"],
            "fileID": mod["file"],
            "filename": mod["jar"],
            "source": f'https://www.curseforge.com/minecraft/mc-mods/{mod["slug"]}/files/{mod["file"]}',
            "sha512": "",
            "mods": [{"id": mod["mod_id"], "version": mod["mod_version"]}],
            "bundled_mods": [],
        })
    data.sort(key=lambda e: str(e.get("name", e.get("slug", ""))).lower())
    dump(path, data)
    return len(data)


def marker() -> dict:
    return {
        "enabled": True,
        "reason": "Reduce entity AI/pathfinding and targeting overhead identified by Spark profiling",
        "mobtimizations": {
            "project_id": 974401,
            "file_id": 7594372,
            "filename": "mobtimizations-forge-1.20.1-1.0.1.jar",
            "version": "1.0.1",
        },
        "coroutil": {
            "project_id": 237749,
            "file_id": 5096038,
            "filename": "coroutil-forge-1.20.1-1.3.7.jar",
            "version": "1.3.7",
            "required_by": "mobtimizations",
        },
        "client_update_required": True,
        "server_update_required": True,
        "quest_progression_changed": False,
        "world_data_touched": False,
        "runtime_spark_retest_required": True,
    }


def patch_metadata(manifest_count: int, server_count: int, client_inventory_count: int, server_inventory_count: int) -> None:
    summary_path = ROOT / "server/_crafty/build-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["version"] = VERSION
    summary["pack_version"] = VERSION
    summary["manifest_entries"] = manifest_count
    summary["server_mod_downloads"] = server_count
    summary["mobtimizations_0_1_9_52"] = marker()
    dump(summary_path, summary)

    for rel, count in [
        ("client/overrides/pack-information/validation.json", client_inventory_count),
        ("server/pack-information/validation.json", server_inventory_count),
    ]:
        path = ROOT / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        data["pack_version"] = VERSION
        if "mod_files" in data:
            data["mod_files"] = count
        data["mobtimizations_0_1_9_52"] = marker()
        dump(path, data)


def patch_modlist() -> None:
    path = ROOT / "client/modlist.html"
    text = path.read_text(encoding="utf-8")
    lines = [
        line for line in text.splitlines()
        if not any(f'/{m["slug"]}/files/' in line or m["jar"] in line for m in MODS)
    ]

    insert_at = next((i for i, line in enumerate(lines) if "modernfix/files/" in line), max(0, len(lines) - 2))
    lines.insert(insert_at + 1, '<li><a href="https://www.curseforge.com/minecraft/mc-mods/mobtimizations/files/7594372">Mobtimizations - Entity Performance Fixes</a> — mobtimizations-forge-1.20.1-1.0.1.jar</li>')
    lines.insert(insert_at + 1, '<li><a href="https://www.curseforge.com/minecraft/mc-mods/coroutil/files/5096038">CoroUtil</a> — coroutil-forge-1.20.1-1.3.7.jar</li>')

    text = "\n".join(lines) + "\n"
    text = re.sub(r"<title>Amber &amp; Arcana [^<]+ mod list</title>", f"<title>Amber &amp; Arcana {VERSION} mod list</title>", text)
    text = re.sub(r"<h1>Amber &amp; Arcana [^<]+</h1>", f"<h1>Amber &amp; Arcana {VERSION}</h1>", text)
    text = re.sub(
        r"<p>\d+ pinned CurseForge mod/library files plus the local More Hitboxes performance patch\.</p>",
        "<p>296 pinned CurseForge mod/library files plus the local More Hitboxes performance patch.</p>",
        text,
    )
    path.write_text(text, encoding="utf-8")


def patch_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    direct = (
        f"[Download Client {VERSION}](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Client.zip) · "
        f"[Download Crafty Server {VERSION}](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Server.zip) · "
        f"[Update existing Crafty server](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Crafty-Update-Overlay.zip)"
    )
    text = re.sub(r"\[Download Client[^\n]+", direct, text, count=1)
    text = re.sub(r"\| Pack \| [^|]+\|", f"| Pack | {VERSION} |", text, count=1)
    text = re.sub(r"\| Client manifest entries \| [^|]+\|", "| Client manifest entries | 296 + 1 local patched JAR |", text, count=1)
    text = re.sub(r"\| Server managed mod entries \| [^|]+\|", "| Server managed mod entries | 276 |", text, count=1)

    note = """### 0.1.9-52 Mob AI optimization
Adds Mobtimizations 1.0.1 and its CoroUtil 1.3.7 dependency to both client and dedicated server. This targets repeated entity AI/pathfinding/target-search work identified in Spark profiles while preserving the More Hitboxes 1.9.2.3 spatial-query patch. No world/player or quest data is changed; a post-deployment Spark comparison is recommended.
"""
    if "### 0.1.9-52 Mob AI optimization" not in text:
        text = text.rstrip() + "\n\n" + note
    path.write_text(text, encoding="utf-8")


def patch_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-52" not in text:
        entry = """## 0.1.9-52 — Mob AI optimization

- Add Mobtimizations 1.0.1 for Forge 1.20.1 (CurseForge 974401:7594372) to client and server.
- Add required CoroUtil 1.3.7 (CurseForge 237749:5096038) to client and server.
- Target repeated entity AI, pathfinding, avoidance, and target-search overhead seen in Spark profiles.
- Preserve the Amber More Hitboxes 1.9.2.3 spatial-query patch.
- No quest, world, or player-data changes; run a fresh Spark profile after deployment.

"""
        text = entry + text
    path.write_text(text, encoding="utf-8")


def patch_validator() -> None:
    path = ROOT / "scripts/validate.sh"
    text = path.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-51"', '.version == "0.1.9-52"', 1)
    text = text.replace('.pack_version == "0.1.9-51"', '.pack_version == "0.1.9-52"', 1)
    text = text.replace('Amber & Arcana 0.1.9-51 static validation passed', 'Amber & Arcana 0.1.9-52 static validation passed', 1)
    text = text.replace('"294" || { echo "Expected 294 client manifest entries"', '"296" || { echo "Expected 296 client manifest entries"', 1)
    text = text.replace('"274" || { echo "Expected 274 server mod rows"', '"276" || { echo "Expected 276 server mod rows"', 1)

    block = """
# 0.1.9-52 Mobtimizations + CoroUtil checks
test "$(jq '[.files[] | select(.projectID == 974401 and .fileID == 7594372)] | length' "$manifest")" = "1" || { echo "Missing Mobtimizations client pin" >&2; exit 1; }
test "$(jq '[.files[] | select(.projectID == 237749 and .fileID == 5096038)] | length' "$manifest")" = "1" || { echo "Missing CoroUtil client pin" >&2; exit 1; }
test "$(awk -F '\t' '$1 == "7594372" && $2 == "mobtimizations-forge-1.20.1-1.0.1.jar" && $4 == "mobtimizations" && $6 == "974401" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing Mobtimizations server pin" >&2; exit 1; }
test "$(awk -F '\t' '$1 == "5096038" && $2 == "coroutil-forge-1.20.1-1.3.7.jar" && $4 == "coroutil" && $6 == "237749" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing CoroUtil server pin" >&2; exit 1; }
jq -e '.mobtimizations_0_1_9_52.enabled == true and .mobtimizations_0_1_9_52.world_data_touched == false and .mobtimizations_0_1_9_52.runtime_spark_retest_required == true' "$validation" >/dev/null
"""
    if "# 0.1.9-52 Mobtimizations + CoroUtil checks" not in text:
        text = text.rstrip() + "\n\n" + block.lstrip()
    path.write_text(text, encoding="utf-8")


def main() -> None:
    manifest_count = patch_manifest()
    server_count = patch_server_mods()
    client_inventory_count = patch_inventory(ROOT / "client/overrides/pack-information/mod-files.json")
    server_inventory_count = patch_inventory(ROOT / "server/pack-information/mod-files.json")
    patch_metadata(manifest_count, server_count, client_inventory_count, server_inventory_count)
    patch_modlist()
    patch_readme()
    patch_changelog()
    patch_validator()
    print(
        f"Prepared Amber & Arcana {VERSION}: Mobtimizations + CoroUtil; "
        f"{manifest_count} client manifest entries, {server_count} managed server entries"
    )


if __name__ == "__main__":
    main()
