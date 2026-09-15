#!/usr/bin/env python3
"""Idempotent 0.1.9-16 hotfix for Mekanism 1.20.1 machine recipe visibility.

Mekanism 10.4.16's 1.20.x build pins JEI 15.2.0.27. Newer JEI builds can
load the item list while failing to expose Mekanism machine categories. This
script pins the CurseForge client manifest to JEI file 4712868 and removes JEI
from the dedicated-server download list because the recipe viewer is not needed
server-side.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-16"
JEI_PROJECT = 238222
JEI_FILE = 4712868
JEI_NAME = "jei-1.20.1-forge-15.2.0.27.jar"


def dump_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_manifest() -> int:
    path = ROOT / "client/manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = VERSION
    data["name"] = f"Amber & Arcana {VERSION}"
    found = 0
    for entry in data.get("files", []):
        if entry.get("projectID") == JEI_PROJECT:
            entry["fileID"] = JEI_FILE
            entry["required"] = True
            found += 1
    if found != 1:
        raise SystemExit(f"Expected one JEI manifest entry, found {found}")
    dump_json(path, data)
    return len(data.get("files", []))


def patch_server_mods() -> int:
    path = ROOT / "server/_crafty/server-mods.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        if not line or line.startswith("#"):
            out.append(line)
            continue
        cols = line.split("\t")
        if len(cols) >= 4 and (cols[3].lower() == "jei" or cols[1].lower().startswith("jei-")):
            continue
        out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return sum(1 for line in out if line and not line.startswith("#"))


def patch_summary(manifest_count: int, server_count: int) -> None:
    path = ROOT / "server/_crafty/build-summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if "pack_version" in data:
        data["pack_version"] = VERSION
    if "version" in data and isinstance(data["version"], str) and data["version"].startswith("0.1.9-"):
        data["version"] = VERSION
    data["manifest_entries"] = manifest_count
    data["server_mod_downloads"] = server_count
    dump_json(path, data)


def patch_validation(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pack_version"] = VERSION
    data["recipe_viewer_0_1_9_16"] = {
        "client": f"JEI 15.2.0.27 / CurseForge file {JEI_FILE}",
        "server_jei_removed": True,
        "reason": "Mekanism 10.4.16 machine-category compatibility",
        "atomic_alloy_test": "Metallurgic Infuser category should be visible after fresh client import"
    }
    dump_json(path, data)


def patch_inventory(path: Path, server: bool) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for entry in data:
        pid = entry.get("projectID", entry.get("projectId"))
        slug = str(entry.get("slug", "")).lower()
        filename = str(entry.get("filename", "")).lower()
        is_jei = pid == JEI_PROJECT or slug == "jei" or filename.startswith("jei-")
        if not is_jei:
            out.append(entry)
            continue
        if server:
            continue
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
        # The authoritative client download is the CurseForge manifest pin.
        # Do not retain the SHA-512 of the superseded JEI binary in the inventory.
        entry.pop("sha512", None)
        out.append(entry)
    dump_json(path, out)


def patch_validator() -> None:
    path = ROOT / "scripts/validate-viewer.py"
    path.write_text('''#!/usr/bin/env python3\n"""Validate the Mekanism-compatible JEI client pin and release archives."""\nimport json\nfrom pathlib import Path\nimport zipfile\n\nroot = Path(__file__).resolve().parents[1]\nmanifest = json.loads((root / "client/manifest.json").read_text())\nversion = manifest["version"]\nexpected = (238222, 4712868)\nfiles = manifest["files"]\nassert len({f["projectID"] for f in files}) == len(files), "Duplicate projects"\nassert [(f["projectID"], f["fileID"]) for f in files if f["projectID"] == 238222] == [expected], "Client JEI pin differs"\nassert not {310111, 521393, 388800} & {f["projectID"] for f in files}, "Old viewer/Polymorph present"\nrows = [line.split("\\t") for line in (root / "server/_crafty/server-mods.tsv").read_text().splitlines() if line and not line.startswith("#")]\nassert not [row for row in rows if len(row) >= 4 and (row[3] == "jei" or row[1].startswith("jei-"))], "JEI should be client-only for this hotfix"\nsummary = json.loads((root / "server/_crafty/build-summary.json").read_text())\nassert summary["server_mod_downloads"] == len(rows), "Server count differs"\nfor side, prefix in [("Client", "client"), ("Server", "server")]:\n    archive_path = root / f"dist/Amber-and-Arcana-{version}-{side}.zip"\n    with zipfile.ZipFile(archive_path) as archive:\n        assert archive.testzip() is None, "Archive CRC failure"\n        source = root / prefix\n        for p in source.rglob("*"):\n            if p.is_file():\n                name = p.relative_to(source).as_posix()\n                assert archive.read(name) == p.read_bytes(), f"Stale archive file: {name}"\nprint("Mekanism-compatible JEI pin, server viewer cleanup, archive CRCs, and source parity passed")\n''', encoding="utf-8")


def patch_validate_sh() -> None:
    path = ROOT / "scripts/validate.sh"
    text = path.read_text(encoding="utf-8")
    text = text.replace('0.1.9-15', VERSION)
    text = text.replace('fileID == 8879628', f'fileID == {JEI_FILE}')
    path.write_text(text, encoding="utf-8")


def patch_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("0.1.9-15", VERSION)
    old = "Release 0.1.9-16 replaces REI with **JEI 15.59.0.211 Forge (beta)** on client and server to restore native recipe integrations and avoid the observed REI armor-repair display exception. All 0.1.9-14 recipe/tag overrides and established quest IDs are preserved. This is a diagnostic build: in-game machine browsing and crafting still need retesting. See [the diagnosis and test checklist](docs/jei-display-0.1.9-16.md)."
    new = "Release 0.1.9-16 pins the **client** to JEI 15.2.0.27 (CurseForge file 4712868), the JEI line used by Mekanism 10.4.16's 1.20.x build. JEI is removed from the dedicated-server download set because recipe browsing is client-side. This hotfix specifically targets missing Mekanism machine categories such as the Metallurgic Infuser recipe used for Atomic Alloy. All 0.1.9-14 recipe/tag overrides and established quest IDs remain preserved."
    text = text.replace(old, new)
    text = text.replace("JEI 15.59.0.211", "JEI 15.2.0.27")
    path.write_text(text, encoding="utf-8")


def patch_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-16" in text:
        return
    entry = '''## 0.1.9-16 — Mekanism machine-recipe JEI compatibility\n\n- Pin client JEI to 15.2.0.27 (CurseForge file 4712868), matching Mekanism 10.4.16's 1.20.x JEI baseline.\n- Remove JEI from the dedicated-server mod download list; the viewer is not required server-side.\n- Target missing Mekanism machine categories, including Metallurgic Infuser recipes such as Atomic Alloy.\n- Preserve the 0.1.9-14 recipe/tag fixes, quests, and all non-viewer content.\n- Rebuild client/server archives and validate archive/source parity.\n\n'''
    text = text.replace("# Changelog\n\n", "# Changelog\n\n" + entry, 1)
    path.write_text(text, encoding="utf-8")


def write_notes() -> None:
    note = f'''Amber & Arcana {VERSION} — Mekanism / JEI compatibility hotfix\n\nClient recipe viewer: JEI 15.2.0.27 (CurseForge project {JEI_PROJECT}, file {JEI_FILE})\nDedicated server: JEI intentionally omitted.\n\nWhy: Mekanism 10.4.16's Minecraft 1.20.x build uses JEI 15.2.0.27 as its dependency baseline. Newer JEI builds can leave Mekanism items visible while its machine recipe categories do not register.\n\nAcceptance check after a FRESH CurseForge import:\n1. Launch and join the matching server.\n2. Search JEI for Atomic Alloy.\n3. Press R / view recipe.\n4. A Mekanism Metallurgic Infuser recipe category should appear.\n5. Check at least one Crusher, Enrichment Chamber, and Energized Smelter recipe too.\n\nAtomic Alloy is a Mekanism machine recipe made by infusing Reinforced Alloy with the Refined Obsidian infusion type in a Metallurgic Infuser.\n'''
    for rel in [
        "client/JEI-MEKANISM-COMPAT-0.1.9-16.txt",
        "client/overrides/pack-information/JEI-MEKANISM-COMPAT-0.1.9-16.txt",
        "server/JEI-MEKANISM-COMPAT-0.1.9-16.txt",
        "server/pack-information/JEI-MEKANISM-COMPAT-0.1.9-16.txt",
    ]:
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(note, encoding="utf-8")


def main() -> None:
    manifest_count = patch_manifest()
    server_count = patch_server_mods()
    patch_summary(manifest_count, server_count)
    for rel in ["client/overrides/pack-information/validation.json", "server/pack-information/validation.json"]:
        patch_validation(ROOT / rel)
    patch_inventory(ROOT / "client/overrides/pack-information/mod-files.json", server=False)
    patch_inventory(ROOT / "server/pack-information/mod-files.json", server=True)
    patch_validator()
    patch_validate_sh()
    patch_readme()
    patch_changelog()
    write_notes()
    print(f"Prepared Amber & Arcana {VERSION}: JEI client pin {JEI_FILE}, server JEI removed")


if __name__ == "__main__":
    main()
