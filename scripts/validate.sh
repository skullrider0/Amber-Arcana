#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
manifest="$repo_dir/client/manifest.json"
summary="$repo_dir/server/_crafty/build-summary.json"
validation="$repo_dir/server/pack-information/validation.json"

for required in "$manifest" "$summary" "$validation" "$repo_dir/server/_crafty/server-mods.tsv" "$repo_dir/server/AmberArcana-Crafty-Launcher.jar"; do
  test -f "$required" || { echo "Missing required file: $required" >&2; exit 1; }
done

version="$(jq -r '.version' "$manifest")"
jq -e '.version == "0.1.9-14" and .minecraft.version == "1.20.1" and .minecraft.modLoaders[0].id == "forge-47.4.10"' "$manifest" >/dev/null
jq -e '.pack_version == "0.1.9-14" and .recipe_viewer_0_1_9_13.jei_removed == true and .recipe_viewer_0_1_9_13.polymorph_removed == true and .recipe_tag_compat_0_1_9_14.disabled_recipe_ids == 36 and .recipe_tag_compat_0_1_9_14.repaired_tag_files == 4' "$validation" >/dev/null

manifest_count="$(jq '.files | length' "$manifest")"
recorded_count="$(jq '.manifest_entries' "$summary")"
test "$manifest_count" = "$recorded_count" || { echo "Manifest count differs from build summary" >&2; exit 1; }

test "$(jq '[.files[] | select(.projectID == 310111 and .fileID == 5846923)] | length' "$manifest")" = "1" || { echo "Expected exactly one REI entry" >&2; exit 1; }

for removed_project in 238222 388800 628539 544031 430127 255717; do
  test "$(jq --argjson id "$removed_project" '[.files[] | select(.projectID == $id)] | length' "$manifest")" = "0" || { echo "Removed project still present: $removed_project" >&2; exit 1; }
done

if rg -i 'jei|polymorph|roughlyenoughitems|roughly_enough_items' "$repo_dir/server/_crafty/server-mods.tsv" >/dev/null; then
  echo "Recipe viewer or Polymorph found in server mod list" >&2
  exit 1
fi

client_quests="$repo_dir/client/overrides/config/ftbquests/quests"
server_quests="$repo_dir/server/config/ftbquests/quests"
diff -qr "$client_quests" "$server_quests" >/dev/null || { echo "Client/server quest files differ" >&2; exit 1; }

client_compat="$repo_dir/client/overrides/kubejs/data"
server_compat="$repo_dir/server/kubejs/data"
diff -qr "$client_compat" "$server_compat" >/dev/null || { echo "Client/server compatibility data differs" >&2; exit 1; }
test "$(find "$client_compat" -path '*/recipes/*.json' -type f | wc -l)" = "36" || { echo "Expected 36 disabled recipe overrides" >&2; exit 1; }
test "$(find "$client_compat" -path '*/tags/*.json' -type f | wc -l)" = "4" || { echo "Expected 4 repaired tag files" >&2; exit 1; }
if ! find "$client_compat" -name '*.json' -type f -print0 | xargs -0 -n1 jq -e . >/dev/null; then
  echo "Invalid compatibility JSON" >&2
  exit 1
fi

unzip -tq "$repo_dir/dist/Amber-and-Arcana-${version}-Client.zip" >/dev/null
unzip -tq "$repo_dir/dist/Amber-and-Arcana-${version}-Server.zip" >/dev/null
(
  cd "$repo_dir/dist"
  sha256sum -c SHA256SUMS.txt
)

echo "Amber & Arcana static validation passed"
