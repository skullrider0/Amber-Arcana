#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dist_dir="$repo_dir/dist"
patch_jar="morehitboxes-forge-1.20.1-1.9.2.1.jar"
validation="$repo_dir/server/pack-information/validation.json"

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
  zip -qr "$update_overlay" AmberArcana-Crafty-Launcher.jar _crafty/server-mods.tsv _crafty/remove-mods.txt "mods/$patch_jar" config/ftbquests/quests
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
