#!/usr/bin/env python3
"""Idempotent Amber & Arcana 0.1.9-17 content cleanup.

Changes:
- remove The Twilight Forest from client and dedicated-server package metadata
- clean the Twilight Forest jar from existing Crafty server installs
- prevent Artifacts' Eternal Steak from generating in CHEST loot via LootJS

Glitchy Mantle is intentionally untouched: it was added to Relics for Minecraft
1.21.1 and is not part of this Forge 1.20.1 pack.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-17"
TWILIGHT_PROJECT = 227639
TWILIGHT_FILE = 5468648
TWILIGHT_JAR = "twilightforest-1.20.1-4.3.2508-universal.jar"
ETERNAL_STEAK = "artifacts:eternal_steak"


def dump_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def project_id(entry: dict):
    return entry.get("projectID", entry.get("projectId"))


def patch_manifest() -> int:
    path = ROOT / "client/manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = VERSION
    data["name"] = f"Amber & Arcana {VERSION}"
    data["files"] = [e for e in data.get("files", []) if project_id(e) != TWILIGHT_PROJECT]
    dump_json(path, data)
    return len(data["files"])


def patch_server_mods() -> int:
    path = ROOT / "server/_crafty/server-mods.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    for line in lines:
        if not line or line.startswith("#"):
            out.append(line)
            continue
        cols = line.split("\t")
        filename = cols[1].lower() if len(cols) > 1 else ""
        slug = cols[3].lower() if len(cols) > 3 else ""
        if filename == TWILIGHT_JAR.lower() or slug == "the-twilight-forest":
            continue
        out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return sum(1 for line in out if line and not line.startswith("#"))


def patch_inventory(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    out = [e for e in data if project_id(e) != TWILIGHT_PROJECT and str(e.get("slug", "")).lower() != "the-twilight-forest"]
    dump_json(path, out)
    return len(out)


def patch_remove_list() -> None:
    path = ROOT / "server/_crafty/remove-mods.txt"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    if TWILIGHT_JAR not in lines:
        lines.append(TWILIGHT_JAR)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def patch_summary(manifest_count: int, server_count: int) -> None:
    path = ROOT / "server/_crafty/build-summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pack_version"] = VERSION
    data["manifest_entries"] = manifest_count
    data["server_mod_downloads"] = server_count
    data["content_cleanup_0_1_9_17"] = {
        "twilight_forest_removed": True,
        "twilight_forest_project_id": TWILIGHT_PROJECT,
        "twilight_forest_file_id": TWILIGHT_FILE,
        "existing_server_jar_cleanup": True,
        "eternal_steak_removed_from_chest_loot": True,
        "eternal_steak_item_id": ETERNAL_STEAK,
        "glitchy_mantle_action": "none; item is not present in this Minecraft 1.20.1 pack",
    }
    dump_json(path, data)


def patch_validation(path: Path, mod_count: int) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pack_version"] = VERSION
    if "mod_files" in data:
        data["mod_files"] = mod_count
    data["content_cleanup_0_1_9_17"] = {
        "twilight_forest_removed": True,
        "twilight_forest_project_id": TWILIGHT_PROJECT,
        "eternal_steak_chest_loot_blocked": True,
        "lootjs_filter": ETERNAL_STEAK,
        "glitchy_mantle_present": False,
    }
    dump_json(path, data)


def write_loot_filter() -> None:
    script = f'''// Amber & Arcana {VERSION}\n// Keep Artifacts installed, but prevent Eternal Steak from generating in chest loot.\nLootJS.modifiers(event => {{\n    event.addLootTypeModifier(LootType.CHEST)\n        .removeLoot('{ETERNAL_STEAK}')\n}})\n'''
    for rel in [
        "client/overrides/kubejs/server_scripts/amber_arcana_loot_blacklist.js",
        "server/kubejs/server_scripts/amber_arcana_loot_blacklist.js",
    ]:
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(script, encoding="utf-8")


def patch_modlist() -> None:
    path = ROOT / "client/modlist.html"
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    lines = [line for line in lines if "Twilight Forest" not in line and "the-twilight-forest" not in line]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def patch_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("0.1.9-16", VERSION)
    marker = "## 0.1.9-17 content cleanup"
    if marker not in text:
        section = f'''\n{marker}\n\n- The Twilight Forest has been removed from the client and dedicated server package.\n- Existing Crafty installs automatically delete `{TWILIGHT_JAR}` during bootstrap.\n- `Eternal Steak` (`{ETERNAL_STEAK}`) is removed from chest-generated loot with LootJS while Artifacts remains installed.\n- Glitchy Mantle is not included in this Minecraft 1.20.1 pack, so no unrelated Relics/GlitchCore content was removed.\n\n'''
        text += section
    path.write_text(text, encoding="utf-8")


def patch_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-17" not in text:
        entry = f'''## 0.1.9-17 — Content cleanup\n\n- Remove The Twilight Forest (CurseForge {TWILIGHT_PROJECT}:{TWILIGHT_FILE}) from client and server packaging.\n- Add `{TWILIGHT_JAR}` to Crafty stale-mod cleanup for existing server installs.\n- Block `{ETERNAL_STEAK}` from CHEST loot only using the pack's existing LootJS integration.\n- Leave Artifacts installed and leave non-chest Eternal Steak acquisition untouched.\n- No Glitchy Mantle removal was necessary; that relic is not present in this Forge 1.20.1 pack.\n- Preserve the Mekanism-compatible JEI 15.2.0.27 client pin from 0.1.9-16.\n\n'''
        text = text.replace("# Changelog\n\n", "# Changelog\n\n" + entry, 1)
    path.write_text(text, encoding="utf-8")


def write_notes() -> None:
    note = f'''Amber & Arcana {VERSION} — content cleanup\n\nRemoved mod:\n- The Twilight Forest (project {TWILIGHT_PROJECT}, file {TWILIGHT_FILE})\n- Existing Crafty installs remove stale {TWILIGHT_JAR} automatically on next bootstrap.\n\nLoot adjustment:\n- {ETERNAL_STEAK} is filtered from CHEST loot through LootJS.\n- Artifacts itself remains installed.\n- This does not intentionally remove Eternal Steak from non-chest sources.\n\nGlitchy Mantle:\n- No action. The pack uses Relics 1.20.1 and does not contain Glitchy Mantle, which belongs to the later Relics 1.21.1 line.\n'''
    for rel in [
        "client/CONTENT-CLEANUP-0.1.9-17.txt",
        "client/overrides/pack-information/CONTENT-CLEANUP-0.1.9-17.txt",
        "server/CONTENT-CLEANUP-0.1.9-17.txt",
        "server/pack-information/CONTENT-CLEANUP-0.1.9-17.txt",
    ]:
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(note, encoding="utf-8")


def write_validator() -> None:
    path = ROOT / "scripts/validate.sh"
    path.write_text(f'''#!/usr/bin/env bash\nset -euo pipefail\n\nrepo_dir="$(cd "$(dirname "${{BASH_SOURCE[0]}}")/.." && pwd)"\nmanifest="$repo_dir/client/manifest.json"\nsummary="$repo_dir/server/_crafty/build-summary.json"\nvalidation="$repo_dir/server/pack-information/validation.json"\n\nfor required in "$manifest" "$summary" "$validation" "$repo_dir/server/_crafty/server-mods.tsv" "$repo_dir/server/AmberArcana-Crafty-Launcher.jar"; do\n  test -f "$required" || {{ echo "Missing required file: $required" >&2; exit 1; }}\ndone\n\nversion="$(jq -r '.version' "$manifest")"\njq -e '.version == "{VERSION}" and .minecraft.version == "1.20.1" and .minecraft.modLoaders[0].id == "forge-47.4.10"' "$manifest" >/dev/null\njq -e '.pack_version == "{VERSION}" and .recipe_viewer_0_1_9_15.rei_removed == true and .recipe_viewer_0_1_9_15.polymorph_removed == true and .recipe_tag_compat_0_1_9_14.disabled_recipe_ids == 36 and .recipe_tag_compat_0_1_9_14.repaired_tag_files == 4 and .content_cleanup_0_1_9_17.twilight_forest_removed == true and .content_cleanup_0_1_9_17.eternal_steak_chest_loot_blocked == true' "$validation" >/dev/null\n\nmanifest_count="$(jq '.files | length' "$manifest")"\nrecorded_count="$(jq '.manifest_entries' "$summary")"\ntest "$manifest_count" = "$recorded_count" || {{ echo "Manifest count differs from build summary" >&2; exit 1; }}\n\ntest "$(jq '[.files[] | select(.projectID == 238222 and .fileID == 4712868)] | length' "$manifest")" = "1" || {{ echo "Expected Mekanism-compatible JEI client pin" >&2; exit 1; }}\nfor removed_project in 310111 521393 388800 628539 544031 430127 255717 {TWILIGHT_PROJECT}; do\n  test "$(jq --argjson id "$removed_project" '[.files[] | select(.projectID == $id)] | length' "$manifest")" = "0" || {{ echo "Removed project still present: $removed_project" >&2; exit 1; }}\ndone\n\nif rg -i 'polymorph|roughlyenoughitems|roughly_enough_items|reiplugincompatibilities|twilightforest|the-twilight-forest' "$repo_dir/server/_crafty/server-mods.tsv" >/dev/null; then\n  echo "Removed viewer or Twilight Forest found in server mod list" >&2\n  exit 1\nfi\ngrep -Fxq '{TWILIGHT_JAR}' "$repo_dir/server/_crafty/remove-mods.txt" || {{ echo "Twilight Forest stale-jar cleanup missing" >&2; exit 1; }}\n\nclient_loot="$repo_dir/client/overrides/kubejs/server_scripts/amber_arcana_loot_blacklist.js"\nserver_loot="$repo_dir/server/kubejs/server_scripts/amber_arcana_loot_blacklist.js"\ntest -f "$client_loot" && test -f "$server_loot" || {{ echo "Loot blacklist missing" >&2; exit 1; }}\ncmp -s "$client_loot" "$server_loot" || {{ echo "Client/server loot blacklist differs" >&2; exit 1; }}\ngrep -Fq 'LootType.CHEST' "$server_loot" || {{ echo "Eternal Steak filter is not chest-scoped" >&2; exit 1; }}\ngrep -Fq "removeLoot('{ETERNAL_STEAK}')" "$server_loot" || {{ echo "Eternal Steak loot removal missing" >&2; exit 1; }}\n\nclient_quests="$repo_dir/client/overrides/config/ftbquests/quests"\nserver_quests="$repo_dir/server/config/ftbquests/quests"\ndiff -qr "$client_quests" "$server_quests" >/dev/null || {{ echo "Client/server quest files differ" >&2; exit 1; }}\n\nclient_compat="$repo_dir/client/overrides/kubejs/data"\nserver_compat="$repo_dir/server/kubejs/data"\ndiff -qr "$client_compat" "$server_compat" >/dev/null || {{ echo "Client/server compatibility data differs" >&2; exit 1; }}\ntest "$(find "$client_compat" -path '*/recipes/*.json' -type f | wc -l)" = "36" || {{ echo "Expected 36 disabled recipe overrides" >&2; exit 1; }}\ntest "$(find "$client_compat" -path '*/tags/*.json' -type f | wc -l)" = "4" || {{ echo "Expected 4 repaired tag files" >&2; exit 1; }}\nfind "$client_compat" -name '*.json' -type f -print0 | xargs -0 -n1 jq -e . >/dev/null\n\nunzip -tq "$repo_dir/dist/Amber-and-Arcana-${{version}}-Client.zip"\nunzip -tq "$repo_dir/dist/Amber-and-Arcana-${{version}}-Server.zip"\n( cd "$repo_dir/dist" && sha256sum -c SHA256SUMS.txt )\npython3 "$repo_dir/scripts/validate-viewer.py"\n\necho "Amber & Arcana {VERSION} static validation passed"\n''', encoding="utf-8")


def main() -> None:
    manifest_count = patch_manifest()
    server_count = patch_server_mods()
    client_mod_count = patch_inventory(ROOT / "client/overrides/pack-information/mod-files.json")
    server_mod_count = patch_inventory(ROOT / "server/pack-information/mod-files.json")
    patch_remove_list()
    patch_summary(manifest_count, server_count)
    patch_validation(ROOT / "client/overrides/pack-information/validation.json", client_mod_count)
    patch_validation(ROOT / "server/pack-information/validation.json", server_mod_count)
    write_loot_filter()
    patch_modlist()
    patch_readme()
    patch_changelog()
    write_notes()
    write_validator()
    print(f"Prepared Amber & Arcana {VERSION}: Twilight Forest removed; Eternal Steak blocked from chest loot")


if __name__ == "__main__":
    main()
