#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.9-53"

SERVERCORE_CONFIG = """# Amber & Arcana tuned ServerCore 1.5.2 configuration.
# Caps target the mob-AI saturation seen in 4-player Spark profiles while
# preserving spawner farms and keeping view distance stable.

features:
  prevent-moving-into-unloaded-chunks: true
  autosave-interval-seconds: 300
  xp-merge-fraction: 8
  xp-merge-radius: 3.0
  item-merge-radius: 2.0
  lobotomize-villagers:
    enabled: true
    tick-interval: 20

dynamic:
  enabled: true
  target-mspt: 35
  dynamic-settings:
    # Keep the requested mob caps fixed; do not stack a dynamic percentage on top.
    - setting: 'MOBCAP_PERCENTAGE'
      max: 100
      min: 100
      increment: 1
      interval: 15

    # Reduce active chunk work before touching simulation distance.
    - setting: 'CHUNK_TICK_DISTANCE'
      max: 6
      min: 4
      increment: 1
      interval: 15

    - setting: 'SIMULATION_DISTANCE'
      max: 6
      min: 4
      increment: 1
      interval: 30

    # Keep the visible server view distance fixed at the existing 8 chunks.
    - setting: 'VIEW_DISTANCE'
      max: 8
      min: 8
      increment: 1
      interval: 300

breeding-cap:
  enabled: true
  villagers:
    limit: 24
    range: 64
  animals:
    limit: 32
    range: 64

mob-spawning:
  zombie-reinforcements:
    enforce-mobcap: true
    additional-capacity: 16

  nether-portal-randomticks:
    enforce-mobcap: true
    additional-capacity: 16

  # Keep player/dungeon spawners functional even when natural caps are full.
  monster-spawners:
    enforce-mobcap: false
    additional-capacity: 32

  infested:
    enforce-mobcap: true
    additional-capacity: 16

  categories:
    - category: 'MONSTER'
      mobcap: 30
      spawn-interval: 1

    - category: 'CREATURE'
      mobcap: 10
      spawn-interval: 100

    - category: 'AMBIENT'
      mobcap: 15
      spawn-interval: 1

    - category: 'AXOLOTLS'
      mobcap: 5
      spawn-interval: 1

    - category: 'UNDERGROUND_WATER_CREATURE'
      mobcap: 5
      spawn-interval: 1

    - category: 'WATER_CREATURE'
      mobcap: 5
      spawn-interval: 1

    - category: 'WATER_AMBIENT'
      mobcap: 20
      spawn-interval: 1

    - category: 'VAMPIRISM_HUNTER'
      mobcap: 15
      spawn-interval: 1

    - category: 'VAMPIRISM_VAMPIRE'
      mobcap: 10
      spawn-interval: 4

    - category: 'WEREWOLVES_WEREWOLF'
      mobcap: 8
      spawn-interval: 1

    - category: 'RATS'
      mobcap: 25
      spawn-interval: 1

commands:
  status-enabled: true
  mobcaps-enabled: true
  colors:
    primary: 'dark_aqua'
    secondary: 'green'
    tertiary: 'aqua'

# Deliberately left disabled for this modpack. Entity Activation Range is powerful,
# but skipped ticks can break modded mobs/farms. Caps + Mobtimizations are the
# safer first-line fix for the measured AI bottleneck.
activation-range:
  enabled: false
  tick-new-entities: true
  use-vertical-range: false
  skip-non-immune: false
  villager-tick-panic: true
  villager-work-immunity-after: 20
  villager-work-immunity-for: 20
  excluded-entity-types:
    - 'minecraft:ghast'
    - 'minecraft:hopper_minecart'
    - 'minecraft:warden'
  default-activation-type:
    activation-range: 16
    tick-interval: 20
    wakeup-interval: -1
    extra-height-up: false
    extra-height-down: false
  custom-activation-types:
    - name: 'raider'
      activation-range: 48
      tick-interval: 20
      wakeup-interval: 20
      extra-height-up: true
      extra-height-down: false
      entity-matcher:
        - 'typeof:raider'
    - name: 'water'
      activation-range: 24
      tick-interval: 20
      wakeup-interval: 60
      extra-height-up: false
      extra-height-down: false
      entity-matcher:
        - 'typeof:water_animal'
    - name: 'villager'
      activation-range: 16
      tick-interval: 20
      wakeup-interval: 30
      extra-height-up: false
      extra-height-down: false
      entity-matcher:
        - 'typeof:villager'
    - name: 'zombie'
      activation-range: 16
      tick-interval: 20
      wakeup-interval: 20
      extra-height-up: true
      extra-height-down: false
      entity-matcher:
        - 'minecraft:zombie'
        - 'minecraft:husk'
    - name: 'monster-below'
      activation-range: 32
      tick-interval: 20
      wakeup-interval: 20
      extra-height-up: true
      extra-height-down: true
      entity-matcher:
        - 'minecraft:creeper'
        - 'minecraft:slime'
        - 'minecraft:magma_cube'
        - 'minecraft:hoglin'
    - name: 'flying-monster'
      activation-range: 48
      tick-interval: 20
      wakeup-interval: 20
      extra-height-up: true
      extra-height-down: false
      entity-matcher:
        - 'minecraft:ghast'
        - 'minecraft:phantom'
    - name: 'monster'
      activation-range: 32
      tick-interval: 20
      wakeup-interval: 20
      extra-height-up: true
      extra-height-down: false
      entity-matcher:
        - 'typeof:monster'
    - name: 'animal'
      activation-range: 16
      tick-interval: 20
      wakeup-interval: 60
      extra-height-up: false
      extra-height-down: false
      entity-matcher:
        - 'typeof:animal'
        - 'typeof:ambient'
    - name: 'creature'
      activation-range: 24
      tick-interval: 20
      wakeup-interval: 30
      extra-height-up: false
      extra-height-down: false
      entity-matcher:
        - 'typeof:mob'
"""

SERVERCORE_OPTIMIZATIONS = """# Amber & Arcana tuned ServerCore 1.5.2 optimizations.
# These require a full server restart.
reduce-sync-loads: true
cache-ticking-chunks: true
fast-biome-lookups: true
# Keep this off for broad mod compatibility; duplicate fluid ticks can be
# gameplay-significant in heavily modded fluid/fire setups.
cancel-duplicate-fluid-ticks: false
"""

MOBTIM_FEATURES = """
# Amber & Arcana Mobtimizations feature configuration.
[general]
\toptimizationZombieVillageRaid = true
\toptimizationMobEnemyTargeting = true
\toptimizationMobWandering = true
\toptimizationMobRepathfinding = true
\toptimizationZombieSearchAndDestroyTurtleEgg = true
\toptimizationMonsterHazardAvoidingPathfollowing = true
\tmod_ArmorSetBonuses_fixServerEffectImmunityCheckingOnNonPlayers = true
\tplayerProximityReducedRate = true
"""

MOBTIM_CUSTOM = """
# Amber & Arcana Mobtimizations tuning.
# Nearby combat remains responsive; far-away AI searches run less often.
[general]
\tzombieVillageRaidPercentChance = 20
\tzombieSearchAndDestroyTurtleEggPercentChance = 0
\tmobWanderingPercentChance = 100
\tmobWanderingDelay = 160
\tmobWanderingReducedRateMultiplier = 8
\tmobEnemyTargetingReducedRatePercentChance = 10
\tplayerProximityReducedRateRangeCutoff = 12
\tplayerProximityReducedRatePlayerScanRate = 60
"""


def dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_tuned_configs() -> None:
    for base in (ROOT / "client/overrides/config", ROOT / "server/config"):
        (base / "servercore").mkdir(parents=True, exist_ok=True)
        (base / "mobtimizations").mkdir(parents=True, exist_ok=True)
        (base / "servercore/config.yml").write_text(SERVERCORE_CONFIG, encoding="utf-8")
        (base / "servercore/optimizations.yml").write_text(SERVERCORE_OPTIMIZATIONS, encoding="utf-8")
        (base / "mobtimizations/features.toml").write_text(MOBTIM_FEATURES.lstrip(), encoding="utf-8")
        (base / "mobtimizations/features-customization.toml").write_text(MOBTIM_CUSTOM.lstrip(), encoding="utf-8")


def patch_spawn_balance() -> None:
    source = ROOT / "overlays/spawn-balance/kubejs/server_scripts/amber_arcana_spawn_balance.js"
    text = source.read_text(encoding="utf-8")

    old_intro = """// - Reduce Vampirism natural spawn attempts by an additional 50%.
//   Net vampire acceptance rate ~= 25% of unpatched behavior.
"""
    text = text.replace(old_intro, """// - Keep Vampire Barons exempt from spawn thinning.
// - Allow other Vampirism natural spawn attempts at 30% of unpatched behavior.
""")

    old_global = """  const id = String(event.entity.type)

  // First layer: 50% fewer normal mob spawn attempts across the pack.
  if (Math.random() < 0.50) {
    event.cancel()
    return
  }
"""
    new_global = """  const id = String(event.entity.type)

  // Vampire Barons are intentionally exempt from all Amber spawn thinning.
  if (id === 'vampirism:vampire_baron') {
    return
  }

  // Vampirism: allow exactly ~30% of normal natural spawn attempts.
  // Handle this before the global layer so reductions do not multiply.
  if (id.startsWith('vampirism:')) {
    if (Math.random() < 0.70) {
      event.cancel()
    }
    return
  }

  // First layer: 50% fewer normal mob spawn attempts across the rest of the pack.
  if (Math.random() < 0.50) {
    event.cancel()
    return
  }
"""
    if old_global not in text:
        raise SystemExit("Expected spawn-balance global block not found")
    text = text.replace(old_global, new_global)

    old_vamp = """  // Vampirism: halve surviving natural spawns again.
  // Combined with the global layer, ~25% of unpatched attempts pass.
  if (id.startsWith('vampirism:') && Math.random() < 0.50) {
    event.cancel()
  }
"""
    text = text.replace(old_vamp, "")
    text = text.replace(
        "global -50%, Ice & Fire additional -70% (pixies included), Untamed Wilds additional -50%, Vampirism additional -50%, Mekanism babies disabled.",
        "global -50%, Vampirism 30% except Baron (exempt), Ice & Fire additional -70% (pixies included), Untamed Wilds additional -50%, Mekanism babies disabled."
    )
    source.write_text(text, encoding="utf-8")

    # Make the canonical client and server packages match the live spawn policy.
    for dest in (
        ROOT / "client/overrides/kubejs/server_scripts/amber_arcana_spawn_balance.js",
        ROOT / "server/kubejs/server_scripts/amber_arcana_spawn_balance.js",
    ):
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)


def patch_release_metadata() -> None:
    manifest_path = ROOT / "client/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = VERSION
    manifest["name"] = "Amber & Arcana " + VERSION
    dump(manifest_path, manifest)

    marker = {
        "enabled": True,
        "reason": "4-player Spark profiles showed entity AI saturation from monster and Vampirism populations",
        "monster_mobcap": 30,
        "vampirism_vampire_mobcap": 10,
        "vampirism_natural_spawn_acceptance_percent": 30,
        "vampire_baron_spawn_thinning_exempt": True,
        "servercore_dynamic_target_mspt": 35,
        "servercore_dynamic_mobcap_percentage_fixed": 100,
        "servercore_dynamic_view_distance_fixed": 8,
        "servercore_dynamic_chunk_tick_distance": {"max": 6, "min": 4},
        "servercore_dynamic_simulation_distance": {"max": 6, "min": 4},
        "servercore_activation_range_enabled": False,
        "mobtimizations_wander_delay_ticks": 160,
        "mobtimizations_far_target_chance_percent": 10,
        "mobtimizations_far_wander_multiplier": 8,
        "client_update_required": True,
        "server_update_required": True,
        "quest_progression_changed": False,
        "world_data_touched": False,
        "runtime_spark_retest_required": True,
    }

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
        else:
            data["pack_version"] = VERSION
        data["performance_tuning_0_1_9_53"] = marker
        dump(path, data)


def patch_readme_changelog() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    direct = (
        f"[Download Client {VERSION}](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Client.zip) · "
        f"[Download Crafty Server {VERSION}](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Server.zip) · "
        f"[Update existing Crafty server](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-Crafty-Update-Overlay.zip)"
    )
    text = re.sub(r"\[Download Client[^\n]+", direct, text, count=1)
    text = re.sub(r"\| Pack \| [^|]+\|", f"| Pack | {VERSION} |", text, count=1)
    note = """### 0.1.9-53 AI population and optimization tuning
Caps ServerCore's MONSTER category at 30 and VAMPIRISM_VAMPIRE at 10, with Vampire Barons exempt from Amber's 30% natural-spawn thinning. Enables ServerCore's safe chunk/spawn optimizations, dynamic chunk-tick/simulation reduction around a 35 MSPT target while keeping mobcap percentage at 100% and view distance at 8, villager lobotomization, wider item/XP merging, and tuned Mobtimizations far-away AI rates. Entity Activation Range remains disabled for mod compatibility. No world/player or quest data is changed.
"""
    if "### 0.1.9-53 AI population and optimization tuning" not in text:
        text = text.rstrip() + "\n\n" + note
    path.write_text(text, encoding="utf-8")

    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.1.9-53" not in text:
        entry = """## 0.1.9-53 — AI population and optimization tuning

- Set ServerCore MONSTER mobcap to 30 and VAMPIRISM_VAMPIRE mobcap to 10.
- Keep Vampire Barons exempt and set other Vampirism natural-spawn acceptance to 30%.
- Enable ServerCore reduce-sync-loads, ticking-chunk cache and fast biome lookups; keep duplicate-fluid-tick cancellation off for compatibility.
- Enable dynamic performance control at a 35 MSPT target, adjusting chunk-tick distance 6→4 and simulation distance 6→4 while keeping mobcap percentage fixed at 100% and view distance fixed at 8.
- Enable villager breeding/lobotomization safeguards and more aggressive XP/item merging.
- Tune Mobtimizations: 160-tick wander delay, 8x far wander multiplier, 10% far target-search chance, 60-tick player proximity scans.
- Keep ServerCore Entity Activation Range disabled to avoid breaking modded entity behavior.
- Include ServerCore, Mobtimizations, ModernFix, Spark and spawn-balance configuration in the stopped-server Crafty overlay.
- No world/player or quest data changes; run a new 4-player Spark profile after deployment.

"""
        text = entry + text
    path.write_text(text, encoding="utf-8")


def patch_validator() -> None:
    path = ROOT / "scripts/validate.sh"
    text = path.read_text(encoding="utf-8")
    text = text.replace('.version == "0.1.9-52"', '.version == "0.1.9-53"', 1)
    text = text.replace('.pack_version == "0.1.9-52"', '.pack_version == "0.1.9-53"', 1)
    text = text.replace('Amber & Arcana 0.1.9-52 static validation passed', 'Amber & Arcana 0.1.9-53 static validation passed', 1)

    block = r'''
# 0.1.9-53 AI population/performance config checks
for base in "$repo_dir/client/overrides/config" "$repo_dir/server/config"; do
  test -f "$base/servercore/config.yml"
  test -f "$base/servercore/optimizations.yml"
  test -f "$base/mobtimizations/features.toml"
  test -f "$base/mobtimizations/features-customization.toml"
  grep -A2 "category: 'MONSTER'" "$base/servercore/config.yml" | grep -q 'mobcap: 30'
  grep -A2 "category: 'VAMPIRISM_VAMPIRE'" "$base/servercore/config.yml" | grep -q 'mobcap: 10'
  grep -q 'target-mspt: 35' "$base/servercore/config.yml"
  grep -q 'mobWanderingDelay = 160' "$base/mobtimizations/features-customization.toml"
  grep -q 'mobEnemyTargetingReducedRatePercentChance = 10' "$base/mobtimizations/features-customization.toml"
done
cmp -s "$repo_dir/client/overrides/config/servercore/config.yml" "$repo_dir/server/config/servercore/config.yml"
cmp -s "$repo_dir/client/overrides/config/servercore/optimizations.yml" "$repo_dir/server/config/servercore/optimizations.yml"
cmp -s "$repo_dir/client/overrides/config/mobtimizations/features.toml" "$repo_dir/server/config/mobtimizations/features.toml"
cmp -s "$repo_dir/client/overrides/config/mobtimizations/features-customization.toml" "$repo_dir/server/config/mobtimizations/features-customization.toml"
grep -q "id === 'vampirism:vampire_baron'" "$repo_dir/server/kubejs/server_scripts/amber_arcana_spawn_balance.js"
grep -q "Math.random() < 0.70" "$repo_dir/server/kubejs/server_scripts/amber_arcana_spawn_balance.js"
jq -e '.performance_tuning_0_1_9_53.monster_mobcap == 30 and .performance_tuning_0_1_9_53.vampirism_vampire_mobcap == 10 and .performance_tuning_0_1_9_53.servercore_activation_range_enabled == false and .performance_tuning_0_1_9_53.world_data_touched == false' "$validation" >/dev/null
'''
    if "# 0.1.9-53 AI population/performance config checks" not in text:
        text = text.rstrip() + "\n\n" + block.lstrip()
    path.write_text(text, encoding="utf-8")


def main() -> None:
    write_tuned_configs()
    patch_spawn_balance()
    patch_release_metadata()
    patch_readme_changelog()
    patch_validator()
    print("Prepared Amber & Arcana 0.1.9-53: mobcaps + ServerCore/Mobtimizations tuning")


if __name__ == "__main__":
    main()
