#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-51"
JAR = "morehitboxes-forge-1.20.1-1.9.2.3.jar"
OLD_JARS = (
    "morehitboxes-forge-1.20.1-1.9.2.jar",
    "morehitboxes-forge-1.20.1-1.9.2.1.jar",
    "morehitboxes-forge-1.20.1-1.9.2.2.jar",
)
VENDOR = ROOT / "vendor/morehitboxes/1.9.2.3" / JAR


def dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def vendor_sha512() -> str:
    sums = ROOT / "vendor/morehitboxes/1.9.2.3/SHA512SUMS.txt"
    expected = sums.read_text(encoding="utf-8").strip().splitlines()[0].split()[0]
    actual = hashlib.sha512(VENDOR.read_bytes()).hexdigest()
    if expected != actual:
        raise SystemExit(f"More Hitboxes vendor checksum mismatch: {actual}")
    return actual


def install_local_jars() -> None:
    for rel in ("client/overrides/mods", "server/mods"):
        mods = ROOT / rel
        mods.mkdir(parents=True, exist_ok=True)
        for old in OLD_JARS:
            (mods / old).unlink(missing_ok=True)
        shutil.copy2(VENDOR, mods / JAR)


def patch_manifest() -> int:
    path = ROOT / "client/manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = VERSION
    data["name"] = "Amber & Arcana " + VERSION
    dump(path, data)
    return len(data["files"])


def patch_server_mods(sha512: str) -> int:
    path = ROOT / "server/_crafty/server-mods.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = next((line for line in lines if line.startswith("#")), "# fileID\tfilename\tsha512\tslug\tname\tprojectID")
    rows = []
    found = 0
    for line in lines:
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 6:
            raise SystemExit(f"Malformed server mod row: {line}")
        if fields[3] == "more-hitboxes" or fields[1].startswith("morehitboxes-forge-1.20.1-"):
            fields = [
                "0",
                JAR,
                sha512,
                "more-hitboxes",
                "More Hitboxes (Amber spatial performance patch)",
                "0",
            ]
            found += 1
        rows.append(fields)
    if found != 1:
        raise SystemExit(f"Expected exactly one More Hitboxes row, found {found}")
    path.write_text(header + "\n" + "\n".join("\t".join(row) for row in rows) + "\n", encoding="utf-8")
    return len(rows)


def patch_remove_list() -> None:
    path = ROOT / "server/_crafty/remove-mods.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    for jar in OLD_JARS:
        if jar not in lines:
            lines.append(jar)
    lines = [line for line in lines if line != JAR]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def marker(sha512: str) -> dict:
    return {
        "enabled": True,
        "upstream_morehitboxes_version": "1.9.2",
        "amber_patch_version": "1.9.2.3",
        "jar": JAR,
        "sha512": sha512,
        "optimization": "Spatially index MoreHitboxes multipart entities once per level tick and query only overlapping chunk buckets",
        "fossils_dependency_preserved": True,
        "client_mixin_and_refmap_preserved_from_official_1_9_2": True,
        "client_boot_tested": True,
        "client_boot_test_result": "Reached Minecraft main menu on Forge 47.4.10",
        "client_update_required": True,
        "server_update_required": True,
        "world_data_touched": False,
        "runtime_spark_retest_required": True,
    }


def patch_metadata(manifest_count: int, server_count: int, sha512: str) -> None:
    key = "more_hitboxes_spatial_cache_0_1_9_51"
    for rel in (
        "server/_crafty/build-summary.json",
        "client/overrides/pack-information/validation.json",
        "server/pack-information/validation.json",
    ):
        path = ROOT / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        if rel.endswith("build-summary.json"):
            data["version"] = VERSION
            data["pack_version"] = VERSION
            data["manifest_entries"] = manifest_count
            data["server_mod_downloads"] = server_count
        else:
            data["pack_version"] = VERSION
        data[key] = marker(sha512)
        dump(path, data)


def patch_modlist() -> None:
    path = ROOT / "client/modlist.html"
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<title>Amber &amp; Arcana [^<]+ mod list</title>",
                  f"<title>Amber &amp; Arcana {VERSION} mod list</title>", text)
    text = re.sub(r"<h1>Amber &amp; Arcana [^<]+</h1>",
                  f"<h1>Amber &amp; Arcana {VERSION}</h1>", text)
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

    note = """### 0.1.9-51 More Hitboxes spatial-query performance patch
Promotes the client-boot-tested More Hitboxes 1.9.2.3 patch. Typed entity queries now use a per-tick spatial chunk-bucket index instead of walking the full level-wide MoreHitboxes multipart set for every AI query. Fossils and Archeology Revival compatibility is preserved, as are the official More Hitboxes 1.9.2 client mixin/refmap. The client test build reached the Minecraft main menu on Forge 47.4.10. World/player data and quest progression are unchanged; a post-deployment Spark comparison is still required.
"""
    if "### 0.1.9-51 More Hitboxes spatial-query performance patch" not in text:
        text = text.rstrip() + "\n\n" + note
    path.write_text(text, encoding="utf-8")


def patch_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-51" not in text:
        entry = """## 0.1.9-51 — More Hitboxes spatial-query performance patch

- Promote the boot-tested Amber More Hitboxes patch to 1.9.2.3.
- Replace the level-wide typed-query multipart scan with a once-per-tick spatial chunk-bucket index.
- Preserve Fossils and Archeology Revival's required More Hitboxes dependency and multipart hit behavior.
- Preserve the official More Hitboxes 1.9.2 client MinecraftMixin and refmap.
- Remove stale 1.9.2, 1.9.2.1 and 1.9.2.2 local patch JARs during Crafty updates.
- Client boot test passed on Minecraft 1.20.1 / Forge 47.4.10.
- No quest, world, or player-data changes; runtime Spark comparison remains required.

"""
        text = entry + text
    path.write_text(text, encoding="utf-8")


def main() -> None:
    sha512 = vendor_sha512()
    install_local_jars()
    manifest_count = patch_manifest()
    server_count = patch_server_mods(sha512)
    patch_remove_list()
    patch_metadata(manifest_count, server_count, sha512)
    patch_modlist()
    patch_readme()
    patch_changelog()
    print(f"Prepared Amber & Arcana {VERSION}: More Hitboxes 1.9.2.3 spatial-query patch")


if __name__ == "__main__":
    main()
