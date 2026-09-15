#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version="$(jq -r '.version' "$repo_dir/client/manifest.json")"
dist_dir="$repo_dir/dist"

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

(
  cd "$dist_dir"
  sha256sum "Amber-and-Arcana-${version}-Client.zip" "Amber-and-Arcana-${version}-Server.zip" > SHA256SUMS.txt
)

# Small overlay for an existing Crafty server: extract at the server root.
rm -f "$dist_dir/Amber-and-Arcana-${version}-Crafty-JEI-Overlay.zip"
(
  cd "$repo_dir/server"
  zip -q "$dist_dir/Amber-and-Arcana-${version}-Crafty-JEI-Overlay.zip" _crafty/server-mods.tsv
)

echo "Built Amber & Arcana ${version}"
