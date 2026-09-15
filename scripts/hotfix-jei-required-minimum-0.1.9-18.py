#!/usr/bin/env python3
"""Amber & Arcana 0.1.9-18 JEI dependency compatibility hotfix.

The 0.1.9-16/17 client pin to JEI 15.2.0.27 is below hard minimums declared
by Create, Sophisticated Core, ModernFix, Chipped, and Tinkers' Construct.
Pin Forge 1.20.1 JEI to 15.20.0.106 (CurseForge file 6075247), which satisfies
the strictest declared minimum while avoiding the much newer 15.57/15.59 line.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-18"
JEI_PROJECT = 238222
JEI_FILE = 6075247
JEI_NAME = "jei-1.20.1-forge-15.20.0.106.jar"


def dump_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_manifest() -> int:
    path = ROOT / "client/manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = VERSION
    data["name"] = f"Amber & Arcana {VERSION}"
    matches = 0
    for entry in data.get("files", []):
        if entry.get("projectID") == JEI_PROJECT:
            entry["fileID"] = JEI_FILE
            entry["required"] = True
            matches += 1
    if matches != 1:
        raise SystemExit(f"Expected one JEI manifest entry, found {matches}")
    dump_json(path, data)
    return len(data.get("files", []))


def patch_inventory(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    matches = 0
    for entry in data:
        pid = entry.get("projectID", entry.get("projectId"))
        slug = str(entry.get("slug", "")).lower()
        filename = str(entry.get("filename", "")).lower()
        if pid == JEI_PROJECT or slug == "jei" or filename.startswith("jei-"):
            if "projectID" in entry:
                entry["projectID"] = JEI_PROJECT
            if "projectId" in entry:
                entry["projectId"] = JEI_PROJECT
            if "fileID" in entry:
                entry["fileID"] = JEI_FILE
            if "fileId" in entry:
                entry["fileId"] = JEI_FILE
            if "filename" in entry:
                entry["filename"] = JEI_NAME
            entry.pop("sha512", None)
            matches += 1
    if matches != 1:
        raise SystemExit(f"Expected one JEI inventory entry in {path}, found {matches}")
    dump_json(path, data)


def patch_summary(manifest_count: int) -> None:
    path = ROOT / "server/_crafty/build-summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pack_version"] = VERSION
    data["manifest_entries"] = manifest_count
    data["jei_dependency_fix_0_1_9_18"] = {
        "client": "JEI 15.20.0.106 / CurseForge file 6075247",
        "server_jei_removed": True,
        "reason": "Satisfy hard JEI minimums declared by Create, Sophisticated Core, ModernFix, Chipped, and Tinkers' Construct",
        "strictest_minimum": "15.20.0.106",
        "mekanism_machine_recipe_retest_required": True,
    }
    dump_json(path, data)


def patch_validation(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pack_version"] = VERSION
    data["jei_dependency_fix_0_1_9_18"] = {
        "project_id": JEI_PROJECT,
        "file_id": JEI_FILE,
        "version": "15.20.0.106",
        "client_only": True,
        "declared_mod_minimums_satisfied": True,
        "runtime_tested": False,
    }
    dump_json(path, data)


def patch_validate_viewer() -> None:
    path = ROOT / "scripts/validate-viewer.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace("expected = (238222, 4712868)", f"expected = ({JEI_PROJECT}, {JEI_FILE})")
    text = text.replace("Mekanism-compatible JEI pin", "JEI dependency-compatible client pin")
    path.write_text(text, encoding="utf-8")


def patch_validate_sh() -> None:
    path = ROOT / "scripts/validate.sh"
    text = path.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-17"', f'.version == "{VERSION}"')
    text = text.replace('.pack_version == "0.1.9-17"', f'.pack_version == "{VERSION}"')
    text = text.replace('select(.projectID == 238222 and .fileID == 4712868)', f'select(.projectID == {JEI_PROJECT} and .fileID == {JEI_FILE})')
    text = text.replace('Expected Mekanism-compatible JEI client pin', 'Expected JEI 15.20.0.106 client pin')
    text = text.replace('Amber & Arcana 0.1.9-17 static validation passed', f'Amber & Arcana {VERSION} static validation passed')
    if 'jei_dependency_fix_0_1_9_18' not in text:
        needle = '.content_cleanup_0_1_9_17.eternal_steak_chest_loot_blocked == true'
        text = text.replace(needle, needle + ' and .jei_dependency_fix_0_1_9_18.file_id == 6075247')
    path.write_text(text, encoding="utf-8")


def patch_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("Download Client 0.1.9-17", f"Download Client {VERSION}")
    text = text.replace("Amber-and-Arcana-0.1.9-17-Client.zip", f"Amber-and-Arcana-{VERSION}-Client.zip")
    text = text.replace("Download Crafty Server 0.1.9-17", f"Download Crafty Server {VERSION}")
    text = text.replace("Amber-and-Arcana-0.1.9-17-Server.zip", f"Amber-and-Arcana-{VERSION}-Server.zip")
    text = text.replace("| Pack | 0.1.9-17 |", f"| Pack | {VERSION} |")
    old = "Release 0.1.9-17 pins the **client** to JEI 15.2.0.27 (CurseForge file 4712868), the JEI line used by Mekanism 10.4.16's 1.20.x build. JEI is removed from the dedicated-server download set because recipe browsing is client-side. This hotfix specifically targets missing Mekanism machine categories such as the Metallurgic Infuser recipe used for Atomic Alloy. All 0.1.9-14 recipe/tag overrides and established quest IDs remain preserved."
    new = "Release 0.1.9-18 pins the **client** to JEI 15.20.0.106 (CurseForge file 6075247). This is the lowest release that satisfies the strictest JEI minimum shown by the current mod set, including Sophisticated Core and Tinkers' Construct, while staying below the later 15.57/15.59 builds previously tested. JEI remains omitted from the dedicated server. Mekanism machine recipe display still requires an in-game retest."
    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def patch_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-18" not in text:
        entry = '''## 0.1.9-18 — JEI dependency compatibility\n\n- Raise client JEI from 15.2.0.27 to 15.20.0.106 (CurseForge 238222:6075247).\n- Fix Forge startup failures from Create, Sophisticated Core, ModernFix, Chipped, and Tinkers' Construct requiring newer JEI APIs.\n- Keep JEI client-only on the dedicated-server package.\n- Preserve the 0.1.9-17 Twilight Forest removal and Eternal Steak chest-loot filter.\n- Retest Mekanism machine recipe categories in-game after launch.\n\n'''
        text = text.replace("# Changelog\n\n", "# Changelog\n\n" + entry, 1)
    path.write_text(text, encoding="utf-8")


def write_notes() -> None:
    note = f'''Amber & Arcana {VERSION} — JEI dependency compatibility hotfix\n\nClient JEI: 15.20.0.106\nCurseForge: project {JEI_PROJECT}, file {JEI_FILE}\nJar: {JEI_NAME}\nDedicated server: JEI intentionally omitted.\n\nWhy:\n- 15.2.0.27 is below hard minimums declared by several installed mods.\n- The strictest startup requirement observed is JEI 15.20.0.106 or newer.\n- This release pins exactly 15.20.0.106 instead of jumping to the later 15.57/15.59 line.\n\nAcceptance checks:\n1. Fresh CurseForge import launches past mod dependency validation.\n2. Join the matching 0.1.9-18 server.\n3. Verify Create/Tinkers/Chipped JEI pages open.\n4. Verify Mekanism Metallurgic Infuser, Crusher, Enrichment Chamber, and Energized Smelter categories still display.\n'''
    for rel in [
        "client/JEI-DEPENDENCY-FIX-0.1.9-18.txt",
        "client/overrides/pack-information/JEI-DEPENDENCY-FIX-0.1.9-18.txt",
        "server/JEI-DEPENDENCY-FIX-0.1.9-18.txt",
        "server/pack-information/JEI-DEPENDENCY-FIX-0.1.9-18.txt",
    ]:
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(note, encoding="utf-8")


def main() -> None:
    manifest_count = patch_manifest()
    patch_inventory(ROOT / "client/overrides/pack-information/mod-files.json")
    patch_summary(manifest_count)
    patch_validation(ROOT / "client/overrides/pack-information/validation.json")
    patch_validation(ROOT / "server/pack-information/validation.json")
    patch_validate_viewer()
    patch_validate_sh()
    patch_readme()
    patch_changelog()
    write_notes()
    print(f"Prepared Amber & Arcana {VERSION}: JEI pinned to 15.20.0.106 / file {JEI_FILE}")


if __name__ == "__main__":
    main()
