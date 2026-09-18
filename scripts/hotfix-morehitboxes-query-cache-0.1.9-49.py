#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-49"
JAR = "morehitboxes-forge-1.20.1-1.9.2.2.jar"
OLD_JARS = (
    "morehitboxes-forge-1.20.1-1.9.2.jar",
    "morehitboxes-forge-1.20.1-1.9.2.1.jar",
)


def dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_sha512() -> str:
    sums = ROOT / "vendor/morehitboxes/1.9.2.2/SHA512SUMS.txt"
    line = sums.read_text(encoding="utf-8").strip().splitlines()[0]
    sha = line.split()[0]
    if len(sha) != 128:
        raise SystemExit(f"Invalid More Hitboxes SHA-512: {sha!r}")
    return sha


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
                "More Hitboxes (Amber query-cache patch)",
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
    # The active patch must never be scheduled for deletion.
    lines = [line for line in lines if line != JAR]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def marker(sha512: str) -> dict:
    return {
        "enabled": True,
        "upstream_morehitboxes_version": "1.9.2",
        "amber_patch_version": "1.9.2.2",
        "jar": JAR,
        "sha512": sha512,
        "optimization": "Cache the MoreHitboxes-only Forge PartEntity subset once per level tick before typed entity queries",
        "unrelated_part_entities_excluded_from_hot_loop": True,
        "fossils_dependency_preserved": True,
        "client_mixin_and_refmap_preserved_from_official_1_9_2": True,
        "client_update_required": True,
        "server_update_required": True,
        "world_data_touched": False,
        "runtime_spark_retest_required": True,
    }


def patch_metadata(manifest_count: int, server_count: int, sha512: str) -> None:
    summary_path = ROOT / "server/_crafty/build-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["version"] = VERSION
    summary["pack_version"] = VERSION
    summary["manifest_entries"] = manifest_count
    summary["server_mod_downloads"] = server_count
    summary["more_hitboxes_query_cache_0_1_9_49"] = marker(sha512)
    dump(summary_path, summary)

    for rel in (
        "client/overrides/pack-information/validation.json",
        "server/pack-information/validation.json",
    ):
        path = ROOT / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        data["pack_version"] = VERSION
        data["more_hitboxes_query_cache_0_1_9_49"] = marker(sha512)
        dump(path, data)


def patch_modlist() -> None:
    path = ROOT / "client/modlist.html"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"<title>Amber &amp; Arcana [^<]+ mod list</title>",
        f"<title>Amber &amp; Arcana {VERSION} mod list</title>",
        text,
    )
    text = re.sub(
        r"<h1>Amber &amp; Arcana [^<]+</h1>",
        f"<h1>Amber &amp; Arcana {VERSION}</h1>",
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

    note = """### 0.1.9-49 More Hitboxes query-cache performance patch
Upgrades Amber's local More Hitboxes patch to 1.9.2.2. The Forge typed-entity-query hook now snapshots only More Hitboxes-owned multipart pieces once per level tick instead of rescanning every Forge PartEntity on every query. This keeps Fossils multipart hitboxes while preventing unrelated multipart mobs such as Ice & Fire dragons from multiplying normal mob-AI query cost. Client mixins/refmap remain based on the official More Hitboxes 1.9.2 JAR. World/player data and quest progression are unchanged.
"""
    if "### 0.1.9-49 More Hitboxes query-cache performance patch" not in text:
        text = text.rstrip() + "\n\n" + note
    path.write_text(text, encoding="utf-8")


def patch_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-49" not in text:
        entry = """## 0.1.9-49 — More Hitboxes query-cache performance patch

- Upgrade the local More Hitboxes patch from 1.9.2.1 to 1.9.2.2.
- Cache only More Hitboxes-owned Forge multipart pieces once per level tick for typed entity queries.
- Stop unrelated Forge PartEntity collections, including Ice & Fire multipart entities, from being rescanned by every More Hitboxes typed query.
- Preserve Fossils and Archeology Revival's required More Hitboxes dependency and multipart hit behavior.
- Preserve the official More Hitboxes 1.9.2 client MinecraftMixin and refmap.
- Preserve the existing unchanged-position multipart update optimization.
- Add stale-JAR cleanup for 1.9.2.1 on existing Crafty servers.
- No quest, world, or player data changes.

"""
        if text.startswith("# Changelog\n\n"):
            text = text.replace("# Changelog\n\n", "# Changelog\n\n" + entry, 1)
        else:
            text = entry + text
    path.write_text(text, encoding="utf-8")


def main() -> None:
    sha512 = read_sha512()
    manifest_count = patch_manifest()
    server_count = patch_server_mods(sha512)
    patch_remove_list()
    patch_metadata(manifest_count, server_count, sha512)
    patch_modlist()
    patch_readme()
    patch_changelog()
    print(
        f"Prepared Amber & Arcana {VERSION}: More Hitboxes 1.9.2.2 query-cache patch; "
        f"{manifest_count} client manifest entries, {server_count} server rows"
    )


if __name__ == "__main__":
    main()
