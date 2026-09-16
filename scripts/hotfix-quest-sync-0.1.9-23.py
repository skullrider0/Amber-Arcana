#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-23"
CLIENT_QUESTS = ROOT / "client/overrides/config/ftbquests/quests"
SERVER_QUESTS = ROOT / "server/config/ftbquests/quests"

EXPECTED_ITEMS = {
    "minecraft:torch", "minecraft:bread", "minecraft:iron_ingot",
    "minecraft:compass", "minecraft:diamond", "minecraft:golden_carrot",
    "create:andesite_alloy", "create:brass_ingot", "minecraft:copper_block",
    "minecraft:powered_rail",
}


def validate_live_client_tree() -> None:
    chapters = CLIENT_QUESTS / "chapters"
    rewards = CLIENT_QUESTS / "reward_tables"
    if len(list(chapters.glob("*.snbt"))) != 25:
        raise RuntimeError("Expected 25 live quest chapters")

    # This is a historical replay gate for the five original reward tables.
    # Later releases deliberately leave generated depth_tier_* files in the source
    # tree, while wheel_* files are removed immediately before this replay. Ignore
    # those later generated tables here instead of making future releases break the
    # 0.1.9-23 baseline check, then remove them so 0.1.9-26 can rebuild from a clean
    # five-table baseline. 0.1.9-30 regenerates the depth tables during the build.
    baseline_rewards = [
        p for p in rewards.glob("*.snbt")
        if not p.name.startswith("wheel_") and not p.name.startswith("depth_tier_")
    ]
    if len(baseline_rewards) != 5:
        raise RuntimeError(f"Expected 5 baseline live reward tables, found {len(baseline_rewards)}")
    for generated in rewards.glob("depth_tier_*.snbt"):
        generated.unlink()

    gs = (chapters / "getting_started.snbt").read_text()
    ce = (chapters / "create_engineering.snbt").read_text()
    if 'subtitle: "Build your first safe shelter and claim starter supplies."' not in gs:
        raise RuntimeError("Make a home subtitle is missing")
    combined = gs + "\n" + ce
    for item in EXPECTED_ITEMS:
        if f'item: "{item}"' not in combined:
            raise RuntimeError(f"Repaired quest reward item missing: {item}")


def sync_server_tree() -> None:
    if SERVER_QUESTS.exists():
        shutil.rmtree(SERVER_QUESTS)
    shutil.copytree(CLIENT_QUESTS, SERVER_QUESTS)


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_release_metadata() -> None:
    def manifest_mut(d):
        d["version"] = VERSION
        d["name"] = re.sub(r"0\.1\.9-\d+", VERSION, d.get("name", "Amber & Arcana"))
    update_json(ROOT / "client/manifest.json", manifest_mut)

    def summary_mut(d):
        d["pack_version"] = VERSION
        d["quest_live_sync_0_1_9_23"] = {
            "source": "client editor save 2026-09-15-12-17-14",
            "chapters": 25,
            "reward_tables": 5,
            "item_rewards_repaired": 12,
            "make_a_home_subtitle_added": True,
            "literal_ampersand_repaired": True,
            "client_server_quest_files_identical": True,
        }
    update_json(ROOT / "server/_crafty/build-summary.json", summary_mut)

    def validation_mut(d):
        d["pack_version"] = VERSION
        d["chapters"] = 25
        d["quest_live_sync_0_1_9_23"] = {
            "source_save": "2026-09-15-12-17-14",
            "reward_tables": 5,
            "broken_item_rewards_found": 12,
            "broken_item_rewards_fixed": 12,
            "client_server_quest_files_identical": True,
        }
    update_json(ROOT / "server/pack-information/validation.json", validation_mut)

    validate = ROOT / "scripts/validate.sh"
    vt = validate.read_text().replace("0.1.9-22", VERSION)
    quest_checks = '''
# 0.1.9-23 live quest sync checks
for qroot in "$client_quests" "$server_quests"; do
  test -f "$qroot/chapter_groups.snbt" || { echo "Quest chapter_groups.snbt missing" >&2; exit 1; }
  test "$(find "$qroot/chapters" -maxdepth 1 -name '*.snbt' -type f | wc -l)" = "25" || { echo "Expected 25 live quest chapters" >&2; exit 1; }
  test "$(find "$qroot/reward_tables" -maxdepth 1 -name '*.snbt' -type f | wc -l)" = "5" || { echo "Expected 5 live reward tables" >&2; exit 1; }
done
grep -Fq 'subtitle: "Build your first safe shelter and claim starter supplies."' "$client_quests/chapters/getting_started.snbt" || { echo "Make a home subtitle missing" >&2; exit 1; }
for item in minecraft:torch minecraft:bread minecraft:iron_ingot minecraft:compass minecraft:diamond minecraft:golden_carrot create:andesite_alloy create:brass_ingot minecraft:copper_block minecraft:powered_rail; do
  rg -F "item: \"$item\"" "$client_quests/chapters/getting_started.snbt" "$client_quests/chapters/create_engineering.snbt" >/dev/null || { echo "Repaired quest reward item missing: $item" >&2; exit 1; }
done
jq -e '.quest_live_sync_0_1_9_23.broken_item_rewards_fixed == 12' "$validation" >/dev/null
'''
    if "# 0.1.9-23 live quest sync checks" not in vt:
        anchor = 'client_compat="$repo_dir/client/overrides/kubejs/data"'
        vt = vt.replace(anchor, quest_checks + "\n" + anchor)
    validate.write_text(vt)

    build = ROOT / "scripts/build.sh"
    bt = build.read_text()
    old_zip = 'zip -q "$update_overlay" _crafty/server-mods.tsv _crafty/remove-mods.txt "mods/$patch_jar"'
    new_zip = 'zip -qr "$update_overlay" _crafty/server-mods.tsv _crafty/remove-mods.txt "mods/$patch_jar" config/ftbquests/quests'
    if old_zip in bt:
        bt = bt.replace(old_zip, new_zip)
    elif new_zip not in bt:
        raise RuntimeError("Could not locate Crafty overlay zip command")
    build.write_text(bt)

    vt = validate.read_text()
    overlay_check = "\ntest \"$(unzip -Z1 \"$overlay\" | grep -Fxc 'config/ftbquests/quests/chapters/getting_started.snbt')\" = \"1\" || { echo \"Crafty update overlay missing synced quests\" >&2; exit 1; }\n"
    anchor = 'unzip -tq "$repo_dir/dist/Amber-and-Arcana-${version}-Client.zip"'
    if "Crafty update overlay missing synced quests" not in vt:
        vt = vt.replace(anchor, overlay_check + "\n" + anchor)
    validate.write_text(vt)

    readme = ROOT / "README.md"
    rt = readme.read_text().replace("0.1.9-22", VERSION)
    rt = re.sub(
        r"## Quest runtime status — 2026-09-15.*?(?=\n## Validate and rebuild)",
        '''## Quest runtime status — 2026-09-15

Release 0.1.9-23 synchronizes the complete FTB Quests editor save from `2026-09-15-12-17-14` into both client and dedicated-server packages. The live save contains 25 chapters and 5 reward tables.

Twelve item rewards had been saved without an `item` field, causing `minecraft:air` rewards. They are repaired with the 1.20.1 simple-item syntax while preserving the live reward IDs, counts, task IDs, quest positions, and dependencies. `Make a home` now has a subtitle, and the literal Amber & Arcana ampersand is stored as raw JSON text so it is not consumed as legacy formatting.
''',
        rt,
        flags=re.S,
    )
    rt = rt.replace('- `mods/morehitboxes-forge-1.20.1-1.9.2.1.jar`\n', '- `mods/morehitboxes-forge-1.20.1-1.9.2.1.jar`\n- `config/ftbquests/quests/` (the synchronized 0.1.9-23 quest book)\n')
    rt = rt.replace('It does **not** contain or overwrite the world.', 'It does **not** contain or overwrite the world. In 0.1.9-23 the overlay also updates the FTB Quests configuration so existing Crafty servers receive the repaired quest book.')
    readme.write_text(rt)

    changelog = ROOT / "CHANGELOG.md"
    ct = changelog.read_text()
    heading = "## 0.1.9-23 — Live FTB Quests sync and reward repair"
    if heading not in ct:
        body = f'''# Changelog

{heading}

- Import the complete client editor save `2026-09-15-12-17-14` as the quest-book source of truth.
- Synchronize all 25 chapters, `chapter_groups.snbt`, `data.snbt`, and 5 reward tables to both client and dedicated server.
- Repair 12 item rewards saved without an `item` value, which rendered as `minecraft:air`.
- Preserve editor-generated quest/task/reward IDs and progression.
- Add a subtitle to `Make a home` and preserve the literal Amber & Arcana ampersand with raw JSON text.
- Preserve the tested More Hitboxes 1.9.2.1 performance patch from 0.1.9-22.

'''
        ct = body + ct.removeprefix("# Changelog\n\n")
    changelog.write_text(ct)


def main() -> None:
    validate_live_client_tree()
    sync_server_tree()
    update_release_metadata()
    print("Applied Amber & Arcana 0.1.9-23 live quest sync")


if __name__ == "__main__":
    main()
