#!/usr/bin/env python3
"""Add Extreme Sound Muffler to the client without changing server mods."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-61"
PIN = {"projectID": 363363, "fileID": 7452801, "required": True}
MARKER = {
    "mod": "Extreme Sound Muffler 3.50 / Forge 1.20.1",
    "project_id": PIN["projectID"],
    "file_id": PIN["fileID"],
    "client_only": True,
    "server_mod_list_changed": False,
    "world_data_touched": False,
}


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def main():
    manifest_path = ROOT / "client/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"] = [item for item in manifest["files"] if item["projectID"] != PIN["projectID"]]
    manifest["files"].append(PIN)
    manifest["files"].sort(key=lambda item: item["projectID"])
    manifest["version"] = VERSION
    manifest["name"] = f"Amber & Arcana {VERSION}"
    save(manifest_path, manifest)

    for relative in ("server/_crafty/build-summary.json", "server/pack-information/validation.json", "client/overrides/pack-information/validation.json"):
        path = ROOT / relative
        obj = json.loads(path.read_text())
        obj["pack_version"] = VERSION
        if relative.endswith("build-summary.json"):
            obj["version"] = VERSION
            obj["manifest_entries"] = len(manifest["files"])
            obj["mod_metadata_entries"] = len(manifest["files"])
        obj["client_sound_muffler_0_1_9_61"] = MARKER
        save(path, obj)

    modlist_path = ROOT / "client/modlist.html"
    modlist = modlist_path.read_text().replace("0.1.9-60", VERSION).replace("296 pinned", "297 pinned")
    row = '<li><a href="https://www.curseforge.com/minecraft/mc-mods/extreme-sound-muffler/files/7452801">Extreme Sound Muffler</a> — ExtremeSoundMuffler-3.50-forge-1.20.1.jar (client only)</li>\n'
    if "ExtremeSoundMuffler-3.50-forge-1.20.1.jar" not in modlist:
        modlist = modlist.replace("<ul>\n", "<ul>\n" + row, 1)
    modlist_path.write_text(modlist)

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text()
    readme = readme.replace("Download Client 0.1.9-60", f"Download Client {VERSION}")
    readme = readme.replace("dist/Amber-and-Arcana-0.1.9-60-Client.zip", f"dist/Amber-and-Arcana-{VERSION}-Client.zip")
    readme = readme.replace("| Pack | 0.1.9-60 |", f"| Pack | {VERSION} |")
    readme = readme.replace("Import `dist/Amber-and-Arcana-0.1.9-60-Client.zip`", f"Import `dist/Amber-and-Arcana-{VERSION}-Client.zip`")
    readme = readme.replace("296 + 1 local patched JAR", "297 + 1 local patched JAR")
    note = "\n### 0.1.9-61 Client sound muffler\n\nAdds Extreme Sound Muffler 3.50 for Forge 1.20.1 to the client only. Use its in-game recent-sounds list near a running Vampirism Blood Grinder to mute the grinder sound. Each player chooses their own sound settings.\n"
    if "### 0.1.9-61 Client sound muffler" not in readme:
        readme += note
    readme_path.write_text(readme)

    changelog_path = ROOT / "CHANGELOG.md"
    changelog = changelog_path.read_text()
    heading = "## 0.1.9-61 — Client sound muffler\n\n- Add Extreme Sound Muffler 3.50 (CurseForge 363363:7452801) to the client manifest only.\n- Keep the server mod list and world data unchanged.\n- Configure Vampirism Blood Grinder sound from the client sound muffler menu after launch.\n\n"
    if "## 0.1.9-61" not in changelog:
        changelog_path.write_text(heading + changelog)

    validator_path = ROOT / "scripts/validate.sh"
    validator = validator_path.read_text().replace('"0.1.9-60" and .minecraft', '"0.1.9-61" and .minecraft').replace('"0.1.9-60" and .recipe', '"0.1.9-61" and .recipe')
    validator = validator.replace('= "294" || { echo "Expected 294 client manifest entries"', '= "297" || { echo "Expected 297 client manifest entries"')
    validator = validator.replace('= "296" || { echo "Expected 296 client manifest entries"', '= "297" || { echo "Expected 297 client manifest entries"')
    validator = validator.replace('echo "Amber & Arcana 0.1.9-60 static validation passed"', '')
    check = '''\n# 0.1.9-61 client-only sound muffler pin\n+test "$(jq '[.files[] | select(.projectID == 363363 and .fileID == 7452801 and .required == true)] | length' "$manifest")" = "1" || { echo "Missing Extreme Sound Muffler client pin" >&2; exit 1; }\n+test "$(jq '.files | length' "$manifest")" = "297" || { echo "Expected 297 client manifest entries" >&2; exit 1; }\n+! rg -i 'extremesoundmuffler|extreme-sound-muffler|7452801' "$repo_dir/server/_crafty/server-mods.tsv" || { echo "Client-only sound muffler in server list" >&2; exit 1; }\n+jq -e '.client_sound_muffler_0_1_9_61.client_only == true and .client_sound_muffler_0_1_9_61.file_id == 7452801 and .client_sound_muffler_0_1_9_61.server_mod_list_changed == false' "$validation" >/dev/null\n+'''.replace('\n+', '\n')
    if "# 0.1.9-61 client-only sound muffler pin" not in validator:
        validator += check
    validator += '\necho "Amber & Arcana 0.1.9-61 static validation passed"\n' if 'echo "Amber & Arcana 0.1.9-61 static validation passed"' not in validator else ''
    validator_path.write_text(validator)

    print(f"Prepared Amber & Arcana {VERSION}: client-only Extreme Sound Muffler")


if __name__ == "__main__":
    main()
