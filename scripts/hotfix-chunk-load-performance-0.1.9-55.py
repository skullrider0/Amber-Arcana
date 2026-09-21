#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-55"


def dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_servercore(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("autosave-interval-seconds: 300", "autosave-interval-seconds: 600")
    text = text.replace("target-mspt: 35", "target-mspt: 30")
    text = text.replace("max: 6\n      min: 4\n      increment: 1\n      interval: 15", "max: 6\n      min: 3\n      increment: 1\n      interval: 10", 1)
    text = text.replace("max: 6\n      min: 4\n      increment: 1\n      interval: 30", "max: 6\n      min: 3\n      increment: 1\n      interval: 15", 1)
    text = text.replace(
        "# Keep the visible server view distance fixed at the existing 8 chunks.\n"
        "    - setting: 'VIEW_DISTANCE'\n      max: 8\n      min: 8\n      increment: 1\n      interval: 300",
        "# Preserve an 8-chunk maximum, but shed distant chunk delivery under sustained load.\n"
        "    - setting: 'VIEW_DISTANCE'\n      max: 8\n      min: 6\n      increment: 1\n      interval: 30",
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    for rel in ("server/config/servercore/config.yml", "client/overrides/config/servercore/config.yml"):
        patch_servercore(ROOT / rel)

    marker = {
        "enabled": True,
        "source_log": "2026-09-21-5.log.gz",
        "sustained_tick_debt_seconds_max": 19.233,
        "cause_class": "distant chunk loading and legacy removed-mod world data",
        "target_mspt": 30,
        "chunk_tick_distance": {"max": 6, "min": 3, "interval_seconds": 10},
        "simulation_distance": {"max": 6, "min": 3, "interval_seconds": 15},
        "view_distance": {"max": 8, "min": 6, "interval_seconds": 30},
        "autosave_interval_seconds": 600,
        "removed_mods_restored": False,
        "more_hitboxes_patch_preserved": True,
        "mobcaps_changed": False,
        "quest_progression_changed": False,
        "world_data_touched": False,
    }
    for rel in ("server/_crafty/build-summary.json", "client/overrides/pack-information/validation.json", "server/pack-information/validation.json"):
        path = ROOT / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        if rel.endswith("build-summary.json"):
            data["version"] = VERSION
            data["pack_version"] = VERSION
        else:
            data["pack_version"] = VERSION
        data["chunk_load_performance_0_1_9_55"] = marker
        dump(path, data)

    manifest_path = ROOT / "client/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = VERSION
    manifest["name"] = "Amber & Arcana " + VERSION
    dump(manifest_path, manifest)

    modlist = ROOT / "client/modlist.html"
    text = modlist.read_text(encoding="utf-8")
    text = re.sub(r"Amber &amp; Arcana 0\.1\.9-\d+", f"Amber &amp; Arcana {VERSION}", text)
    modlist.write_text(text, encoding="utf-8")

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = text.replace("0.1.9-54", VERSION)
    note = """### 0.1.9-55 chunk-load performance tuning
Based on the 2026-09-21 server log, ServerCore now reacts sooner to sustained chunk-loading pressure: target 30 MSPT; chunk-tick and simulation distance 6→3; view distance 8→6 only while overloaded; autosaves every 10 minutes. Mob caps, spawners, quests, and the client-safe MoreHitboxes patch are unchanged. Missing Untamed Wilds entities and Mowzie's structure references are legacy data being discarded after their intentional 0.1.9-49 removal; those performance-heavy mods remain removed. No world/player data is changed by this release.
"""
    if "### 0.1.9-55 chunk-load performance tuning" not in text:
        text = text.rstrip() + "\n\n" + note
    readme.write_text(text, encoding="utf-8")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    if "## 0.1.9-55" not in text:
        entry = """## 0.1.9-55 — Chunk-load performance tuning

- Lower ServerCore's dynamic target from 35 to 30 MSPT so load shedding starts before tick debt becomes severe.
- Allow chunk-tick and simulation distances to fall from 6 to 3 under sustained load, with faster adjustment intervals.
- Allow view distance to fall from 8 to 6 only while overloaded; it returns toward 8 after recovery.
- Extend autosaves from 5 to 10 minutes to reduce save pressure during exploration.
- Keep MONSTER 30, VAMPIRISM_VAMPIRE 10, spawner behavior, quests, and MoreHitboxes 1.9.2.3 unchanged.
- Keep Mowzie's Mobs and Untamed Wilds removed; their log warnings are stale world data being discarded as chunks load.
- No world or player data is included or modified.

"""
        text = entry + text
    changelog.write_text(text, encoding="utf-8")

    validator = ROOT / "scripts/validate.sh"
    text = validator.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-54"', '.version == "0.1.9-55"', 1)
    text = text.replace('.pack_version == "0.1.9-54"', '.pack_version == "0.1.9-55"', 1)
    text = text.replace("Amber & Arcana 0.1.9-54 static validation passed", "Amber & Arcana 0.1.9-55 static validation passed", 1)
    # The 0.1.9-53 block validates the live canonical config, which 0.1.9-55
    # intentionally supersedes with an earlier load-shedding target.
    text = text.replace("grep -q 'target-mspt: 35'", "grep -q 'target-mspt: 30'", 2)
    if "# 0.1.9-55 chunk-load performance checks" not in text:
        text += """

# 0.1.9-55 chunk-load performance checks
client_sc="$repo_dir/client/overrides/config/servercore/config.yml"
server_sc="$repo_dir/server/config/servercore/config.yml"
cmp -s "$client_sc" "$server_sc" || { echo "Client/server ServerCore configs differ" >&2; exit 1; }
grep -Fq 'target-mspt: 30' "$server_sc" || { echo "30 MSPT target missing" >&2; exit 1; }
test "$(grep -c 'min: 3' "$server_sc")" -ge 2 || { echo "Dynamic chunk/simulation minimums missing" >&2; exit 1; }
grep -Fq 'autosave-interval-seconds: 600' "$server_sc" || { echo "Autosave tuning missing" >&2; exit 1; }
jq -e '.chunk_load_performance_0_1_9_55.enabled == true and .chunk_load_performance_0_1_9_55.more_hitboxes_patch_preserved == true and .chunk_load_performance_0_1_9_55.mobcaps_changed == false and .chunk_load_performance_0_1_9_55.world_data_touched == false' "$validation" >/dev/null
"""
    validator.write_text(text, encoding="utf-8")

    print(f"Prepared Amber & Arcana {VERSION}: conservative chunk-load performance tuning")


if __name__ == "__main__":
    main()
