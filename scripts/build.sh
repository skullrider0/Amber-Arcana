#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version="$(jq -r '.version' "$repo_dir/client/manifest.json")"
dist_dir="$repo_dir/dist"
patch_jar="morehitboxes-forge-1.20.1-1.9.2.1.jar"

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
