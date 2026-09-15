#!/usr/bin/env python3
"""Amber & Arcana 0.1.9-22: ship the client-safe More Hitboxes performance patch."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-22"
PROJECT_ID = 1115989
FILE_ID = 6942239
SLUG = "more-hitboxes"
OLD_JAR = "morehitboxes-forge-1.20.1-1.9.2.jar"
JAR = "morehitboxes-forge-1.20.1-1.9.2.1.jar"
VENDOR_DIR = ROOT / "vendor/morehitboxes/1.9.2.1"
VENDOR_JAR = VENDOR_DIR / JAR

# These four entry fingerprints came from the client-safe beta that booted in the
# user's Forge 47.4.10 client. The overall ZIP hash can change if ZIP metadata is
# regenerated, so release validation also checks the actual runtime-critical bytes.
EXPECTED_ENTRY_SHA256 = {
    "com/github/darkpred/morehitboxes/mixin/LevelMixin.class": "b8be4ff50fa2483000260a85d765d069bc2563cf3731be83a511cf7a18f52ed9",
    "com/github/darkpred/morehitboxes/api/MultiPart.class": "4a80919ee9911744b50d8e975bd3a7088beafda145ca8353eff02fb11619e7b6",
    "com/github/darkpred/morehitboxes/mixin/MinecraftMixin.class": "6c81b6251b306f3e35216fd5f4690f61b5cd7deba66aef1acf6c6b16774b190b",
    "mixins.morehitboxes.refmap.json": "f306522d5797b7cb2d0c1baaef3aaa6ae81843d1c688b8b8302276520214921d",
}


def dump_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def file_digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_sum(path: Path) -> str:
    return path.read_text(encoding="utf-8").split()[0].lower()


def is_more_hitboxes(entry: dict) -> bool:
    return (
        entry.get("projectID", entry.get("projectId")) == PROJECT_ID
        or entry.get("fileID", entry.get("fileId")) == FILE_ID
        or str(entry.get("slug", "")).lower() == SLUG
        or str(entry.get("filename", "")).lower().startswith("morehitboxes-")
    )


def verify_patch() -> tuple[str, str]:
    sha256 = read_sum(VENDOR_DIR / "SHA256SUMS.txt")
    sha512 = read_sum(VENDOR_DIR / "SHA512SUMS.txt")
    for path in (VENDOR_JAR, ROOT / "client/overrides/mods" / JAR, ROOT / "server/mods" / JAR):
        if not path.is_file():
            raise SystemExit(f"Missing patched More Hitboxes jar: {path}")
        if file_digest(path, "sha256") != sha256 or file_digest(path, "sha512") != sha512:
            raise SystemExit(f"Checksum mismatch for patched More Hitboxes jar: {path}")
        with zipfile.ZipFile(path) as zf:
            for name, expected in EXPECTED_ENTRY_SHA256.items():
                actual = hashlib.sha256(zf.read(name)).hexdigest()
                if actual != expected:
                    raise SystemExit(f"Client-safe More Hitboxes entry fingerprint mismatch: {name}")
    return sha256, sha512


def patch_manifest() -> int:
    path = ROOT / "client/manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["files"] = [entry for entry in data.get("files", []) if not is_more_hitboxes(entry)]
    data["version"] = VERSION
    data["name"] = f"Amber & Arcana {VERSION}"
    dump_json(path, data)
    return len(data["files"])


def patch_inventory(path: Path, sha512: str) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    previous = next((entry for entry in data if is_more_hitboxes(entry)), {})
    data = [entry for entry in data if not is_more_hitboxes(entry)]
    entry = dict(previous)
    entry.update({
        "slug": SLUG,
        "name": "More Hitboxes (Amber performance patch)",
        "projectID": 0,
        "fileID": 0,
        "filename": JAR,
        "source": f"vendor/morehitboxes/1.9.2.1/{JAR}",
        "sha512": sha512,
        "mods": [{"id": "morehitboxes", "version": "1.9.2.1"}],
    })
    entry.setdefault("bundled_mods", [])
    insert_at = next((i for i, item in enumerate(data) if item.get("slug") == "mowzies-mobs"), len(data))
    data.insert(insert_at, entry)
    dump_json(path, data)
    return len(data)


def patch_server_tsv(sha512: str) -> int:
    path = ROOT / "server/_crafty/server-mods.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    headers = [line for line in lines if line.startswith("#")]
    rows: list[str] = []
    for line in lines:
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t", 4)
        if len(cols) == 5 and (cols[3] == SLUG or cols[1].startswith("morehitboxes-")):
            continue
        rows.append(line)
    row = f"0\t{JAR}\t{sha512}\t{SLUG}\tMore Hitboxes (Amber performance patch)"
    insert_at = next((i for i, line in enumerate(rows) if "\tmowzies-mobs\t" in line), len(rows))
    rows.insert(insert_at, row)
    path.write_text("\n".join(headers + rows) + "\n", encoding="utf-8")
    return len(rows)


def patch_remove_list() -> None:
    path = ROOT / "server/_crafty/remove-mods.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    old_seen = False
    for line in lines:
        value = line.strip()
        if value == JAR:
            continue
        if value == OLD_JAR:
            if old_seen:
                continue
            old_seen = True
        out.append(line)
    if not old_seen:
        out.extend(["", "# Replaced by Amber More Hitboxes 1.9.2.1 performance patch.", OLD_JAR])
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def release_metadata(sha256: str, sha512: str) -> dict:
    return {
        "enabled": True,
        "base_version": "1.9.2",
        "patched_version": "1.9.2.1",
        "filename": JAR,
        "sha256": sha256,
        "sha512": sha512,
        "client_and_server": True,
        "required_by": "Fossils and Archeology Revival 9.3.4.0",
        "patched_classes": [
            "com.github.darkpred.morehitboxes.mixin.LevelMixin",
            "com.github.darkpred.morehitboxes.api.MultiPart",
        ],
        "official_client_mixin_and_refmap_preserved": True,
        "known_good_entry_fingerprints_verified": True,
        "client_boot_tested": True,
        "spark_retest_required": True,
    }


def patch_summary(manifest_count: int, inventory_count: int, server_count: int, sha256: str, sha512: str) -> None:
    path = ROOT / "server/_crafty/build-summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pack_version"] = VERSION
    data["manifest_entries"] = manifest_count
    data["mod_metadata_entries"] = inventory_count
    data["server_mod_downloads"] = server_count
    data["server_mod_count"] = server_count
    if isinstance(data.get("more_hitboxes_restore_0_1_9_21"), dict):
        data["more_hitboxes_restore_0_1_9_21"]["superseded_by"] = VERSION
    data["more_hitboxes_perf_patch_0_1_9_22"] = release_metadata(sha256, sha512)
    data["quest_runtime_status_2026_09_15"] = {
        "screenshot_received": True,
        "getting_started_quest_rendered": True,
        "observed_no_subtitle_in_editor": True,
        "observed_air_reward_slot": True,
        "repo_runtime_reward_mismatch": True,
        "repo_make_a_home_rewards": ["16 torches", "8 bread", "100 XP"],
        "action": "Capture the live getting_started.snbt before syncing quest changes.",
    }
    dump_json(path, data)


def patch_validation(path: Path, inventory_count: int, sha256: str, sha512: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pack_version"] = VERSION
    if "mod_files" in data:
        data["mod_files"] = inventory_count
    data["more_hitboxes_perf_patch_0_1_9_22"] = {
        "enabled": True,
        "filename": JAR,
        "sha256": sha256,
        "sha512": sha512,
        "official_manifest_entry_removed": True,
        "client_override_jar": True,
        "server_bundled_jar": True,
        "crafty_local_file_id": 0,
        "known_good_entry_fingerprints_verified": True,
    }
    dump_json(path, data)


def patch_validate_sh(sha512: str) -> None:
    path = ROOT / "scripts/validate.sh"
    text = path.read_text(encoding="utf-8").replace("0.1.9-21", VERSION)

    old = f'''test "$(jq '[.files[] | select(.projectID == {PROJECT_ID} and .fileID == {FILE_ID})] | length' "$manifest")" = "1" || {{ echo "Expected More Hitboxes 1.9.2 client pin" >&2; exit 1; }}
test "$(awk -F '\\t' '$4 == "{SLUG}" && $1 == "{FILE_ID}" && $2 == "{OLD_JAR}" {{n++}} END {{print n+0}}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || {{ echo "Expected More Hitboxes 1.9.2 on server" >&2; exit 1; }}
if grep -Fxq '{OLD_JAR}' "$repo_dir/server/_crafty/remove-mods.txt"; then
  echo "More Hitboxes is still scheduled for Crafty deletion" >&2
  exit 1
fi
'''
    new = f'''test "$(jq '[.files[] | select(.projectID == {PROJECT_ID} or .fileID == {FILE_ID})] | length' "$manifest")" = "0" || {{ echo "Official More Hitboxes entry must be absent from client manifest" >&2; exit 1; }}
client_mh="$repo_dir/client/overrides/mods/{JAR}"
server_mh="$repo_dir/server/mods/{JAR}"
test -f "$client_mh" && test -f "$server_mh" || {{ echo "Patched More Hitboxes jar missing" >&2; exit 1; }}
printf '%s  %s\n' '{sha512}' "$client_mh" | sha512sum --check - >/dev/null
printf '%s  %s\n' '{sha512}' "$server_mh" | sha512sum --check - >/dev/null
cmp -s "$client_mh" "$server_mh" || {{ echo "Client/server More Hitboxes patch differs" >&2; exit 1; }}
test "$(awk -F '\\t' '$4 == "{SLUG}" && $1 == "0" && $2 == "{JAR}" && $3 == "{sha512}" {{n++}} END {{print n+0}}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || {{ echo "Expected local More Hitboxes patch pin" >&2; exit 1; }}
grep -Fxq '{OLD_JAR}' "$repo_dir/server/_crafty/remove-mods.txt" || {{ echo "Old More Hitboxes cleanup missing" >&2; exit 1; }}
if grep -Fxq '{JAR}' "$repo_dir/server/_crafty/remove-mods.txt"; then
  echo "Patched More Hitboxes is scheduled for deletion" >&2
  exit 1
fi
jq -e '.more_hitboxes_perf_patch_0_1_9_22.enabled == true' "$validation" >/dev/null
'''
    if old in text:
        text = text.replace(old, new)
    elif "Official More Hitboxes entry must be absent from client manifest" not in text:
        raise SystemExit("Could not locate More Hitboxes validation block")

    old_overlay = '''overlay="$repo_dir/dist/Amber-and-Arcana-${version}-Crafty-JEI-Overlay.zip"
test -f "$overlay" || { echo "Crafty JEI overlay missing" >&2; exit 1; }
unzip -tq "$overlay"
test "$(unzip -Z1 "$overlay" | grep -Fxc '_crafty/server-mods.tsv')" = "1" || { echo "Crafty JEI overlay has unexpected layout" >&2; exit 1; }
'''
    new_overlay = f'''overlay="$repo_dir/dist/Amber-and-Arcana-${{version}}-Crafty-Update-Overlay.zip"
test -f "$overlay" || {{ echo "Crafty update overlay missing" >&2; exit 1; }}
unzip -tq "$overlay"
test "$(unzip -Z1 "$overlay" | grep -Fxc '_crafty/server-mods.tsv')" = "1" || {{ echo "Crafty update overlay missing server-mods.tsv" >&2; exit 1; }}
test "$(unzip -Z1 "$overlay" | grep -Fxc '_crafty/remove-mods.txt')" = "1" || {{ echo "Crafty update overlay missing remove-mods.txt" >&2; exit 1; }}
test "$(unzip -Z1 "$overlay" | grep -Fxc 'mods/{JAR}')" = "1" || {{ echo "Crafty update overlay missing patched jar" >&2; exit 1; }}
'''
    if old_overlay in text:
        text = text.replace(old_overlay, new_overlay)
    elif "Crafty update overlay missing" not in text:
        raise SystemExit("Could not locate Crafty overlay validation block")

    path.write_text(text, encoding="utf-8")


def main() -> None:
    sha256, sha512 = verify_patch()
    manifest_count = patch_manifest()
    client_inventory_count = patch_inventory(ROOT / "client/overrides/pack-information/mod-files.json", sha512)
    server_inventory_count = patch_inventory(ROOT / "server/pack-information/mod-files.json", sha512)
    server_count = patch_server_tsv(sha512)
    patch_remove_list()
    patch_summary(manifest_count, client_inventory_count, server_count, sha256, sha512)
    patch_validation(ROOT / "client/overrides/pack-information/validation.json", client_inventory_count, sha256, sha512)
    patch_validation(ROOT / "server/pack-information/validation.json", server_inventory_count, sha256, sha512)
    patch_validate_sh(sha512)
    print(f"Prepared Amber & Arcana {VERSION} with client-safe More Hitboxes 1.9.2.1")


if __name__ == "__main__":
    main()
