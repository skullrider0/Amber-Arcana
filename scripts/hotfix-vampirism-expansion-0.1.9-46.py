#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-46"
IRON_PROJECT = 228756
IRON_FILE = 4614852
IRON_JAR = "ironchest-1.20.1-14.4.4.jar"

ADDONS = [
    ("vampirism-irons-spells-compatibility", "Vampirism Iron's Spells Compatibility", 1350048, 8525675, "vampire_spells_addon-forge-1.20.1-0.0.9.jar", "0.0.9"),
    ("vampires-delight", "Vampire's Delight", 939092, 8200186, "VampiresDelight-1.20.1-0.1.13c.jar", "0.1.13c"),
    ("vampiric-ageing-a-vampirism-addon", "Vampiric Ageing", 906331, 6125994, "vampiricageing-1.20.1-1.3.26.jar", "1.3.26"),
    ("werewolves-become-a-beast", "Werewolves - Become a Beast!", 417851, 6722563, "Werewolves-1.20.1-2.0.2.7.jar", "2.0.2.7"),
    ("vampirism-tinker", "Vampirism Tinker", 1314650, 6814093, "vampirismtinker-1.6.jar", "1.6"),
    ("create-vampirism", "Create Vampirism", 1238539, 6775688, "create_vampirism-1.20.1_0.5.0.jar", "0.5.0"),
    ("vampirism-umbrella-curios-support", "Vampirism Umbrella Curios Support", 1565325, 8219863, "RIP_vampirismcurioscompat-1.0.0.jar", "1.0.0"),
]
ADDON_PROJECTS = {a[2] for a in ADDONS}
ADDON_SLUGS = {a[0] for a in ADDONS}

def dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def pid(entry: dict):
    return entry.get("projectID", entry.get("projectId"))

def patch_manifest() -> int:
    path = ROOT / "client/manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    files = [e for e in data.get("files", []) if pid(e) != IRON_PROJECT and pid(e) not in ADDON_PROJECTS]
    for slug, name, project, file_id, filename, version in ADDONS:
        files.append({"projectID": project, "fileID": file_id, "required": True})
    files.sort(key=lambda e: (int(pid(e) or 0), int(e.get("fileID", 0) or 0)))
    data["files"] = files
    data["version"] = VERSION
    data["name"] = "Amber & Arcana " + VERSION
    dump(path, data)
    return len(files)

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
        if cols[0] == str(IRON_FILE) or cols[1].lower() == IRON_JAR.lower() or cols[3] == "iron-chests" or cols[5] == str(IRON_PROJECT):
            continue
        if cols[3] in ADDON_SLUGS or (cols[5].isdigit() and int(cols[5]) in ADDON_PROJECTS):
            continue
        kept.append(cols)
    for slug, name, project, file_id, filename, version in ADDONS:
        kept.append([str(file_id), filename, "", slug, name, str(project)])
    kept.sort(key=lambda row: row[4].lower())
    path.write_text(header + "\n" + "\n".join("\t".join(row) for row in kept) + "\n", encoding="utf-8")
    return len(kept)

def patch_inventory(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    data = [e for e in data if pid(e) != IRON_PROJECT and pid(e) not in ADDON_PROJECTS and str(e.get("slug", "")).lower() != "iron-chests" and str(e.get("slug", "")).lower() not in ADDON_SLUGS]
    for slug, name, project, file_id, filename, version in ADDONS:
        data.append({
            "slug": slug,
            "name": name,
            "projectID": project,
            "fileID": file_id,
            "filename": filename,
            "source": "https://www.curseforge.com/minecraft/mc-mods/" + slug + "/files/" + str(file_id),
            "sha512": "",
            "mods": [],
            "bundled_mods": [],
        })
    data.sort(key=lambda e: str(e.get("name", e.get("slug", ""))).lower())
    dump(path, data)
    return len(data)

def patch_remove_list() -> None:
    path = ROOT / "server/_crafty/remove-mods.txt"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    lines = [line for line in lines if line.strip()]
    if IRON_JAR not in lines:
        lines.append(IRON_JAR)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def marker() -> dict:
    return {
        "addons_added": 7,
        "addon_pins": [{"project_id": a[2], "file_id": a[3], "filename": a[4]} for a in ADDONS],
        "iron_chests_removed": True,
        "iron_chests_project_id": IRON_PROJECT,
        "iron_chests_file_id": IRON_FILE,
        "iron_chests_stale_jar_cleanup": True,
        "quest_progression_changed": False,
        "create_vampirism_blood_feeding_enabled": False,
        "client_update_required": True,
        "server_update_required": True,
        "world_data_touched": False,
    }

def patch_metadata(manifest_count: int, server_count: int, client_mod_count: int, server_mod_count: int) -> None:
    summary_path = ROOT / "server/_crafty/build-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["pack_version"] = VERSION
    summary["manifest_entries"] = manifest_count
    summary["server_mod_downloads"] = server_count
    summary["vampirism_expansion_0_1_9_46"] = marker()
    dump(summary_path, summary)
    for rel, count in [
        ("client/overrides/pack-information/validation.json", client_mod_count),
        ("server/pack-information/validation.json", server_mod_count),
    ]:
        path = ROOT / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        data["pack_version"] = VERSION
        if "mod_files" in data:
            data["mod_files"] = count
        data["vampirism_expansion_0_1_9_46"] = marker()
        dump(path, data)

def patch_modlist() -> None:
    path = ROOT / "client/modlist.html"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    lines = [line for line in lines if "iron-chests/files/4614852" not in line and "ironchest-1.20.1-14.4.4.jar" not in line and not any("/" + a[0] + "/files/" + str(a[3]) in line for a in ADDONS)]
    additions = []
    for slug, name, project, file_id, filename, version in ADDONS:
        label = name.replace("&", "&amp;").replace("'", "&#x27;")
        additions.append('<li><a href="https://www.curseforge.com/minecraft/mc-mods/' + slug + '/files/' + str(file_id) + '">' + label + '</a> — ' + filename + '</li>')
    insert_at = next((i for i, line in enumerate(lines) if "vampirism-become-a-vampire" in line), max(0, len(lines) - 2))
    lines[insert_at:insert_at] = additions
    text = "\n".join(lines) + "\n"
    text = re.sub(r"<title>Amber &amp; Arcana [^<]+ mod list</title>", "<title>Amber &amp; Arcana " + VERSION + " mod list</title>", text)
    text = re.sub(r"<h1>Amber &amp; Arcana [^<]+</h1>", "<h1>Amber &amp; Arcana " + VERSION + "</h1>", text)
    text = re.sub(r"<p>\d+ pinned mod/library files plus one shader entry\.</p>", "<p>297 pinned CurseForge mod/library files plus the local More Hitboxes performance patch.</p>", text)
    path.write_text(text, encoding="utf-8")

def patch_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    direct = "[Download Client " + VERSION + "](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-" + VERSION + "-Client.zip) · [Download Crafty Server " + VERSION + "](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-" + VERSION + "-Server.zip) · [Update existing Crafty server](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-" + VERSION + "-Crafty-Update-Overlay.zip)"
    text = re.sub(r"\[Download Client[^\n]+", direct, text, count=1)
    text = re.sub(r"\| Pack \| [^|]+\|", "| Pack | " + VERSION + " |", text, count=1)
    text = re.sub(r"\| Client manifest entries \| [^|]+\|", "| Client manifest entries | 297 + 1 local patched JAR |", text, count=1)
    text = re.sub(r"\| Server managed mod entries \| [^|]+\|", "| Server managed mod entries | 277 |", text, count=1)
    text = re.sub(r"Import dist/Amber-and-Arcana-[^\s]+-Client\.zip", "Import dist/Amber-and-Arcana-" + VERSION + "-Client.zip", text, count=1)
    text = re.sub(r"Create a fresh server from dist/Amber-and-Arcana-[^\s]+-Server\.zip", "Create a fresh server from dist/Amber-and-Arcana-" + VERSION + "-Server.zip", text, count=1)
    if "### 0.1.9-46 Vampirism expansion" not in text:
        text += "\n\n### 0.1.9-46 Vampirism expansion\nAdds seven Forge 1.20.1 Vampirism addons without changing FTB Quest progression: Vampirism Iron's Spells Compatibility, Vampire's Delight, Vampiric Ageing, Werewolves, Vampirism Tinker, Create Vampirism, and Vampirism Umbrella Curios Support. Iron Chests is removed from client/server packaging and existing Crafty installs delete " + IRON_JAR + " on the next launcher start. Create Vampirism's WIP Blood Feeding feature is not enabled.\n"
    path.write_text(text, encoding="utf-8")

def patch_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-46" not in text:
        entry = "## 0.1.9-46 — Vampirism addon expansion and Iron Chests removal\n\n"
        for slug, name, project, file_id, filename, version in ADDONS:
            entry += "- Add " + name + " " + version + " (" + str(project) + ":" + str(file_id) + ").\n"
        entry += "- Remove Iron Chests (" + str(IRON_PROJECT) + ":" + str(IRON_FILE) + ") and clean up " + IRON_JAR + " on existing Crafty installs.\n"
        entry += "- Do not add or change Vampirism/Werewolf FTB Quest progression.\n"
        entry += "- Leave Create Vampirism Blood Feeding disabled/default-off.\n"
        entry += "- Preserve the local More Hitboxes performance patch and existing spawn/performance fixes.\n\n"
        text = text.replace("# Changelog\n\n", "# Changelog\n\n" + entry, 1)
    path.write_text(text, encoding="utf-8")

def write_notes() -> None:
    lines = ["Amber & Arcana " + VERSION + " — Vampirism expansion", "", "Added (client + server):"]
    for slug, name, project, file_id, filename, version in ADDONS:
        lines.append("- " + name + " — project " + str(project) + ", file " + str(file_id) + " — " + filename)
    lines += ["", "Removed:", "- Iron Chests — project " + str(IRON_PROJECT) + ", file " + str(IRON_FILE), "- Existing Crafty installs remove stale " + IRON_JAR + " on next launcher start.", "", "Quest policy:", "- No FTB Quest progression was added or changed.", "", "Create Vampirism:", "- WIP Blood Feeding is intentionally not enabled.", "", "Existing More Hitboxes/performance fixes remain in place.", ""]
    note = "\n".join(lines)
    for rel in ["client/VAMPIRISM-EXPANSION-0.1.9-46.txt", "client/overrides/pack-information/VAMPIRISM-EXPANSION-0.1.9-46.txt", "server/VAMPIRISM-EXPANSION-0.1.9-46.txt", "server/pack-information/VAMPIRISM-EXPANSION-0.1.9-46.txt"]:
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(note, encoding="utf-8")

def patch_validator() -> None:
    path = ROOT / "scripts/validate.sh"
    text = path.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-45"', '.version == "' + VERSION + '"')
    text = text.replace('.pack_version == "0.1.9-45"', '.pack_version == "' + VERSION + '"')
    text = text.replace('echo "Amber & Arcana 0.1.9-45 static validation passed"', 'echo "Amber & Arcana ' + VERSION + ' static validation passed"')
    if "# 0.1.9-46 Vampirism addon expansion checks" not in text:
        text += "\n\n# 0.1.9-46 Vampirism addon expansion checks\n"
        text += "test \"$(jq '[.files[] | select(.projectID == 228756 or .fileID == 4614852)] | length' \"$manifest\")\" = \"0\" || { echo \"Iron Chests remains in client manifest\" >&2; exit 1; }\n"
        text += "grep -Fxq '" + IRON_JAR + "' \"$repo_dir/server/_crafty/remove-mods.txt\" || { echo \"Iron Chests stale-jar cleanup missing\" >&2; exit 1; }\n"
        for slug, name, project, file_id, filename, version in ADDONS:
            text += "test \"$(jq '[.files[] | select(.projectID == " + str(project) + " and .fileID == " + str(file_id) + ")] | length' \"$manifest\")\" = \"1\" || { echo \"Missing 0.1.9-46 client pin: " + name.replace('"', '') + "\" >&2; exit 1; }\n"
            text += "test \"$(awk -F '\\t' '$1 == \"" + str(file_id) + "\" && $2 == \"" + filename + "\" && $4 == \"" + slug + "\" && $6 == \"" + str(project) + "\" {n++} END {print n+0}' \"$repo_dir/server/_crafty/server-mods.tsv\")\" = \"1\" || { echo \"Missing 0.1.9-46 server pin: " + name.replace('"', '') + "\" >&2; exit 1; }\n"
        text += "if rg -F $'\tiron-chests\t' \"$repo_dir/server/_crafty/server-mods.tsv\" >/dev/null; then echo \"Iron Chests remains in server mod list\" >&2; exit 1; fi\n"
        text += "jq -e '.vampirism_expansion_0_1_9_46.addons_added == 7 and .vampirism_expansion_0_1_9_46.iron_chests_removed == true and .vampirism_expansion_0_1_9_46.quest_progression_changed == false and .vampirism_expansion_0_1_9_46.create_vampirism_blood_feeding_enabled == false and .vampirism_expansion_0_1_9_46.world_data_touched == false' \"$validation\" >/dev/null\n"
        text += "test \"$(jq '.files | length' \"$manifest\")\" = \"297\" || { echo \"Expected 297 client manifest entries\" >&2; exit 1; }\n"
        text += "test \"$(awk -F '\\t' '!/^#/ && NF {n++} END {print n+0}' \"$repo_dir/server/_crafty/server-mods.tsv\")\" = \"277\" || { echo \"Expected 277 server mod rows\" >&2; exit 1; }\n"
    path.write_text(text, encoding="utf-8")

def main() -> None:
    manifest_count = patch_manifest()
    server_count = patch_server_mods()
    client_mod_count = patch_inventory(ROOT / "client/overrides/pack-information/mod-files.json")
    server_mod_count = patch_inventory(ROOT / "server/pack-information/mod-files.json")
    patch_remove_list()
    patch_metadata(manifest_count, server_count, client_mod_count, server_mod_count)
    patch_modlist()
    patch_readme()
    patch_changelog()
    write_notes()
    patch_validator()
    print("Prepared Amber & Arcana " + VERSION + ": seven Vampirism addons added, Iron Chests removed, quests untouched")

if __name__ == "__main__":
    main()
