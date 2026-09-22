#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dist_dir="$repo_dir/dist"
patch_jar="morehitboxes-forge-1.20.1-1.9.2.3.jar"
validation="$repo_dir/server/pack-information/validation.json"

# Do not replay historical release migrations over canonical 0.1.9-42 data.
if ! grep -Fq '"bee_integrations_0_1_9_42"' "$validation"; then
# The repository stores the canonical current pack source. Only replay the old
# 0.1.9-35 deepening transform on genuinely pre-deepening sources. The 0.1.9-38
# ATM10-inspired rebuild intentionally replaces the old AA35 marker text, so its
# validation marker is also a canonical "already deepened" signal.
if ! grep -Fq 'AA35 deep progression milestone' \
     "$repo_dir/client/overrides/config/ftbquests/quests/chapters/ae2.snbt" && \
   ! grep -Fq '"atm10_major_progression_0_1_9_38"' "$validation"; then
  python3 "$repo_dir/scripts/run-hotfix-deep-short-progression-0.1.9-35.py"
fi

if ! grep -Fq $'\tmining-gadgets\tMining Gadgets' "$repo_dir/server/_crafty/server-mods.tsv" || \
   ! grep -Fq $'\tdraconic-evolution\tDraconic Evolution' "$repo_dir/server/_crafty/server-mods.tsv"; then
  python3 "$repo_dir/scripts/hotfix-tech-expansion-0.1.9-36.py"
fi

# 0.1.9-37 compacted the old quest geometry. Once its canonical marker exists,
# never rescale later quest releases again; 0.1.9-38 supplies its own tight branch
# coordinates for the rebuilt major chapters.
if ! grep -Fq '"atm10_layout_0_1_9_37"' "$validation"; then
  python3 "$repo_dir/scripts/hotfix-atm10-compact-layout-0.1.9-37.py"
fi

# 0.1.9-38 replaces generic generated milestone chains in the major tech/magic
# chapters with concrete mechanics-based branches inspired by ATM10's progression
# style, while retaining Amber & Arcana's weighted tier rolls and Fortune Wheels.
python3 "$repo_dir/scripts/hotfix-atm10-major-progression-0.1.9-38.py"
python3 "$repo_dir/scripts/fix-current-validator-0.1.9-38.py"

# 0.1.9-39 adds No Recipe Book Reborn to the CurseForge client manifest only.
# It intentionally does not change the dedicated-server mod list.
python3 "$repo_dir/scripts/hotfix-no-recipe-book-reborn-0.1.9-39.py"

# 0.1.9-40 repairs Crafty's server-mod downloader for CurseForge's July 2026
# direct-CDN API-key requirement. Project IDs are embedded in server-mods.tsv,
# the launcher gains validated web/CurseMaven fallbacks and optional API-key CDN
# support, and the update overlay now ships the current launcher itself.
python3 "$repo_dir/scripts/hotfix-curseforge-downloads-0.1.9-40.py"

# 0.1.9-41 restores recipe-conflict selection now that the pack is back on JEI,
# extends that selector into AE2 and Refined Storage, and adds Spartan Weaponry.
python3 "$repo_dir/scripts/hotfix-recipe-conflicts-spartan-0.1.9-41.py"

fi

python3 "$repo_dir/scripts/hotfix-bee-integrations-0.1.9-42.py"
python3 "$repo_dir/scripts/hotfix-stone-generators-0.1.9-43.py"

# Repair the historical dependency cycle first; 0.1.9-45 then becomes the final
# version-setting quest transform for this release.
python3 "$repo_dir/scripts/hotfix-quest-cycles-0.1.9-44.py"

# 0.1.9-45 removes the generic AA35 filler chains and re-themes chapter reward
# tables. This pass preserves every non-filler quest ID and synchronizes the
# client/server quest sources.
if ! grep -Fq '"quest_curation_0_1_9_45"' "$validation"; then
  python3 "$repo_dir/scripts/run-hotfix-quest-curation-0.1.9-45.py"
fi
python3 "$repo_dir/scripts/validate-quest-themes.py"
python3 "$repo_dir/scripts/validate-quest-graph.py"

# 0.1.9-46 expands Vampirism integrations and removes Iron Chests without
# changing FTB Quest progression. Existing worlds are never packaged here.
python3 "$repo_dir/scripts/hotfix-vampirism-expansion-0.1.9-46.py"

# 0.1.9-47 adds Tinker's Domain, the required tcondiadema dependency for Vampirism Tinker 1.6.
python3 "$repo_dir/scripts/hotfix-vampirism-tinker-dependency-0.1.9-47.py"

# 0.1.9-48 removes Vampirism Tinker 1.6 from the pack.
python3 "$repo_dir/scripts/hotfix-vampirism-tinker-server-fix-0.1.9-48.py"

# 0.1.9-49 removes Mowzie\'s Mobs and Untamed Wilds after Spark profiling.
python3 "$repo_dir/scripts/hotfix-performance-mod-cleanup-0.1.9-49.py"

# 0.1.9-50 removes unrelated Forge multipart entities from More Hitboxes typed-query hot loops.
python3 "$repo_dir/scripts/hotfix-morehitboxes-query-cache-0.1.9-50.py"

# 0.1.9-51 promotes the boot-tested spatial MoreHitboxes query index.
python3 "$repo_dir/scripts/hotfix-morehitboxes-spatial-cache-0.1.9-51.py"

# 0.1.9-52 adds Mobtimizations and required CoroUtil to both sides after Spark profiling.
python3 "$repo_dir/scripts/hotfix-mobtimizations-0.1.9-52.py"

# 0.1.9-53 tunes ServerCore/Mobtimizations and lowers monster/Vampirism mobcaps after 4-player Spark profiling.
python3 "$repo_dir/scripts/hotfix-performance-tuning-0.1.9-53.py"

# 0.1.9-54 adds Powah Thermo Generator compatibility for Central Kitchen
# Dragon's Breath and Tinkers' Blazing Blood, including the client JEI display fix.
python3 "$repo_dir/scripts/hotfix-powah-thermo-compat-0.1.9-54.py"

# 0.1.9-55 reacts sooner to the sustained chunk-load stalls in the 2026-09-21 log.
python3 "$repo_dir/scripts/hotfix-chunk-load-performance-0.1.9-55.py"

# 0.1.9-56 disables malformed upstream data entries reported during startup.
python3 "$repo_dir/scripts/hotfix-startup-data-errors-0.1.9-56.py"


bash "$repo_dir/scripts/build-launcher.sh"

version="$(jq -r '.version' "$repo_dir/client/manifest.json")"

"$repo_dir/scripts/generate-recipe-compat.sh"

mkdir -p "$dist_dir"

(
  cd "$repo_dir/client"
  zip -qr -FS "$dist_dir/Amber-and-Arcana-${version}-Client.zip" .
)

(
  cd "$repo_dir/server"
  zip -qr -FS "$dist_dir/Amber-and-Arcana-${version}-Server.zip" .
)

# World-safe Crafty update overlay. It updates only pack/bootstrap/mod-management
# data, the locally patched More Hitboxes jar, and synchronized quests. World save
# directories are never included.
update_overlay="$dist_dir/Amber-and-Arcana-${version}-Crafty-Update-Overlay.zip"
legacy_overlay="$dist_dir/Amber-and-Arcana-${version}-Crafty-JEI-Overlay.zip"
quest_overlay="$dist_dir/Amber-and-Arcana-${version}-Crafty-Quest-Overlay.zip"
quest_spawn_overlay="$dist_dir/Amber-and-Arcana-${version}-Crafty-Quest-Spawn-Balance-Overlay.zip"
rm -f "$update_overlay" "$legacy_overlay" "$quest_overlay" "$quest_spawn_overlay"
(
  cd "$repo_dir/server"
  test -f "mods/$patch_jar" || { echo "Missing patched More Hitboxes jar: server/mods/$patch_jar" >&2; exit 1; }
  test -f "AmberArcana-Crafty-Launcher.jar" || { echo "Missing rebuilt Crafty launcher" >&2; exit 1; }
  zip -qr "$update_overlay" AmberArcana-Crafty-Launcher.jar _crafty/server-mods.tsv _crafty/remove-mods.txt "mods/$patch_jar" config/ftbquests/quests config/servercore config/mobtimizations config/modernfix-mixins.properties config/spark kubejs/data kubejs/assets kubejs/server_scripts/amber_arcana_spawn_balance.js kubejs/startup_scripts/amber_arcana_powah_thermo_compat.js _crafty/build-summary.json pack-information/validation.json
)
cp "$update_overlay" "$legacy_overlay"

(
  cd "$repo_dir/server"
  zip -qr "$quest_overlay" config/ftbquests/quests
)

# Combined quest + spawn-balance overlay. No world data is ever included.
tmp_overlay_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_overlay_dir"' EXIT
mkdir -p "$tmp_overlay_dir/config/ftbquests" "$tmp_overlay_dir/kubejs/server_scripts"
cp -a "$repo_dir/server/config/ftbquests/quests" "$tmp_overlay_dir/config/ftbquests/"
cp "$repo_dir/overlays/spawn-balance/kubejs/server_scripts/amber_arcana_spawn_balance.js" \
   "$tmp_overlay_dir/kubejs/server_scripts/amber_arcana_spawn_balance.js"
cp "$repo_dir/overlays/spawn-balance/README-SPAWN-BALANCE.txt" \
   "$tmp_overlay_dir/README-SPAWN-BALANCE.txt"
(
  cd "$tmp_overlay_dir"
  zip -qr "$quest_spawn_overlay" README-SPAWN-BALANCE.txt config/ftbquests/quests kubejs/server_scripts/amber_arcana_spawn_balance.js
)
rm -rf "$tmp_overlay_dir"
trap - EXIT

(
  cd "$dist_dir"
  sha256sum \
    "Amber-and-Arcana-${version}-Client.zip" \
    "Amber-and-Arcana-${version}-Server.zip" \
    "Amber-and-Arcana-${version}-Crafty-Update-Overlay.zip" \
    "Amber-and-Arcana-${version}-Crafty-JEI-Overlay.zip" \
    "Amber-and-Arcana-${version}-Crafty-Quest-Overlay.zip" \
    "Amber-and-Arcana-${version}-Crafty-Quest-Spawn-Balance-Overlay.zip" \
    > SHA256SUMS.txt
)

echo "Built Amber & Arcana ${version}"
