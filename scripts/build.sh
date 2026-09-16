#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dist_dir="$repo_dir/dist"
patch_jar="morehitboxes-forge-1.20.1-1.9.2.1.jar"

# 0.1.9-30 is assembled from small source parts in the same style as the older
# quest24 generator. Running it here keeps the existing historical workflow
# replay intact while ensuring every normal build receives the latest quest UX.
cat "$repo_dir"/scripts/quest30-parts/*.part > "$repo_dir/scripts/hotfix-quest-ux-0.1.9-30.py"
python3 "$repo_dir/scripts/hotfix-quest-ux-0.1.9-30.py"
python3 "$repo_dir/scripts/normalize-validation-0.1.9-30.py"

# 0.1.9-31 keeps the exact Productive Bees NBT matching from 0.1.9-30 but gives
# every species-specific Bee Cage task an explicit species label in FTB Quests.
python3 "$repo_dir/scripts/hotfix-bee-cage-labels-0.1.9-31.py"

# 0.1.9-32 replaces the four global vanilla-heavy depth pools with four
# chapter/mod-specific tiers, rethemes finale wheels, and keeps top-tier machines
# as genuinely rare jackpots even though high-tier rolls return multiple items.
python3 "$repo_dir/scripts/run-hotfix-mod-tier-loot-0.1.9-32.py"

# 0.1.9-33 makes Productive Bees rewards scale more strongly with progression:
# larger mod-specific pools, more draws at higher tiers, and rare Omega jackpots.
python3 "$repo_dir/scripts/hotfix-productive-bees-rewards-0.1.9-33.py"

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

# Existing Crafty-server update overlay. This is intentionally world-safe: it
# contains only the mod-management files plus the locally patched More Hitboxes jar.
update_overlay="$dist_dir/Amber-and-Arcana-${version}-Crafty-Update-Overlay.zip"
legacy_overlay="$dist_dir/Amber-and-Arcana-${version}-Crafty-JEI-Overlay.zip"
quest_overlay="$dist_dir/Amber-and-Arcana-${version}-Crafty-Quest-Overlay.zip"
quest_spawn_overlay="$dist_dir/Amber-and-Arcana-${version}-Crafty-Quest-Spawn-Balance-Overlay.zip"
rm -f "$update_overlay" "$legacy_overlay" "$quest_overlay" "$quest_spawn_overlay"
(
  cd "$repo_dir/server"
  test -f "mods/$patch_jar" || { echo "Missing patched More Hitboxes jar: server/mods/$patch_jar" >&2; exit 1; }
  zip -qr "$update_overlay" _crafty/server-mods.tsv _crafty/remove-mods.txt "mods/$patch_jar" config/ftbquests/quests
)
# Keep the old overlay filename as a compatibility alias for anyone following an
# older README/bookmark, but its contents are now the full update overlay.
cp "$update_overlay" "$legacy_overlay"

# Quest-only overlay for an already-correct Crafty server. This intentionally
# contains no world, mods, launcher files, or mod-management state.
(
  cd "$repo_dir/server"
  zip -qr "$quest_overlay" config/ftbquests/quests
)

# Combined quest + spawn-balance overlay requested for the active Crafty server.
# It contains only the synchronized quest tree, the server-side KubeJS spawn
# balance script, and its README. It does not contain or modify any world data.
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
