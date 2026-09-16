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
rm -f "$update_overlay" "$legacy_overlay" "$quest_overlay"
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

(
  cd "$dist_dir"
  sha256sum \
    "Amber-and-Arcana-${version}-Client.zip" \
    "Amber-and-Arcana-${version}-Server.zip" \
    "Amber-and-Arcana-${version}-Crafty-Update-Overlay.zip" \
    "Amber-and-Arcana-${version}-Crafty-JEI-Overlay.zip" \
    "Amber-and-Arcana-${version}-Crafty-Quest-Overlay.zip" \
    > SHA256SUMS.txt
)

echo "Built Amber & Arcana ${version}"
