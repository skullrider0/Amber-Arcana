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
jq -e '.version == "0.1.9-25" and .minecraft.version == "1.20.1" and .minecraft.modLoaders[0].id == "forge-47.4.10"' "$manifest" >/dev/null
jq -e '.pack_version == "0.1.9-25" and .recipe_viewer_0_1_9_15.rei_removed == true and .recipe_viewer_0_1_9_15.polymorph_removed == true and .recipe_tag_compat_0_1_9_14.disabled_recipe_ids == 36 and .recipe_tag_compat_0_1_9_14.repaired_tag_files == 4 and .content_cleanup_0_1_9_17.twilight_forest_removed == true and .content_cleanup_0_1_9_17.eternal_steak_chest_loot_blocked == true and .jei_dependency_fix_0_1_9_18.file_id == 6075247' "$validation" >/dev/null

manifest_count="$(jq '.files | length' "$manifest")"
recorded_count="$(jq '.manifest_entries' "$summary")"
test "$manifest_count" = "$recorded_count" || { echo "Manifest count differs from build summary" >&2; exit 1; }

test "$(jq '[.files[] | select(.projectID == 238222 and .fileID == 6075247)] | length' "$manifest")" = "1" || { echo "Expected JEI 15.20.0.106 client pin" >&2; exit 1; }
for removed_project in 310111 521393 388800 628539 544031 430127 255717 227639; do
  test "$(jq --argjson id "$removed_project" '[.files[] | select(.projectID == $id)] | length' "$manifest")" = "0" || { echo "Removed project still present: $removed_project" >&2; exit 1; }
done

if rg -i 'polymorph|roughlyenoughitems|roughly_enough_items|reiplugincompatibilities|twilightforest|the-twilight-forest' "$repo_dir/server/_crafty/server-mods.tsv" >/dev/null; then
  echo "Removed viewer or Twilight Forest found in server mod list" >&2
  exit 1
fi
test "$(awk -F '\t' '$4 == "jei" && $1 == "6075247" && $2 == "jei-1.20.1-forge-15.20.0.106.jar" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Expected matching JEI 15.20.0.106 on server" >&2; exit 1; }

test "$(jq '[.files[] | select(.projectID == 1115989 or .fileID == 6942239)] | length' "$manifest")" = "0" || { echo "Official More Hitboxes entry must be absent from client manifest" >&2; exit 1; }
client_mh="$repo_dir/client/overrides/mods/morehitboxes-forge-1.20.1-1.9.2.1.jar"
server_mh="$repo_dir/server/mods/morehitboxes-forge-1.20.1-1.9.2.1.jar"
test -f "$client_mh" && test -f "$server_mh" || { echo "Patched More Hitboxes jar missing" >&2; exit 1; }
printf '%s  %s\n' 'd7dce29e3e791cd27af0d217d699583112d07b5d5f8700f9852a353013a554934fa5bbf1bb1d4d64f452ac6942e37315ba70081d700bf60e022836fe32354cb5' "$client_mh" | sha512sum --check - >/dev/null
printf '%s  %s\n' 'd7dce29e3e791cd27af0d217d699583112d07b5d5f8700f9852a353013a554934fa5bbf1bb1d4d64f452ac6942e37315ba70081d700bf60e022836fe32354cb5' "$server_mh" | sha512sum --check - >/dev/null
cmp -s "$client_mh" "$server_mh" || { echo "Client/server More Hitboxes patch differs" >&2; exit 1; }
test "$(awk -F '\t' '$4 == "more-hitboxes" && $1 == "0" && $2 == "morehitboxes-forge-1.20.1-1.9.2.1.jar" && $3 == "d7dce29e3e791cd27af0d217d699583112d07b5d5f8700f9852a353013a554934fa5bbf1bb1d4d64f452ac6942e37315ba70081d700bf60e022836fe32354cb5" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Expected local More Hitboxes patch pin" >&2; exit 1; }
grep -Fxq 'morehitboxes-forge-1.20.1-1.9.2.jar' "$repo_dir/server/_crafty/remove-mods.txt" || { echo "Old More Hitboxes cleanup missing" >&2; exit 1; }
if grep -Fxq 'morehitboxes-forge-1.20.1-1.9.2.1.jar' "$repo_dir/server/_crafty/remove-mods.txt"; then
  echo "Patched More Hitboxes is scheduled for deletion" >&2
  exit 1
fi
jq -e '.more_hitboxes_perf_patch_0_1_9_22.enabled == true' "$validation" >/dev/null

grep -Fxq 'twilightforest-1.20.1-4.3.2508-universal.jar' "$repo_dir/server/_crafty/remove-mods.txt" || { echo "Twilight Forest stale-jar cleanup missing" >&2; exit 1; }

client_loot="$repo_dir/client/overrides/kubejs/server_scripts/amber_arcana_loot_blacklist.js"
server_loot="$repo_dir/server/kubejs/server_scripts/amber_arcana_loot_blacklist.js"
test -f "$client_loot" && test -f "$server_loot" || { echo "Loot blacklist missing" >&2; exit 1; }
cmp -s "$client_loot" "$server_loot" || { echo "Client/server loot blacklist differs" >&2; exit 1; }
grep -Fq 'LootType.CHEST' "$server_loot" || { echo "Eternal Steak filter is not chest-scoped" >&2; exit 1; }
grep -Fq "removeLoot('artifacts:eternal_steak')" "$server_loot" || { echo "Eternal Steak loot removal missing" >&2; exit 1; }

client_quests="$repo_dir/client/overrides/config/ftbquests/quests"
server_quests="$repo_dir/server/config/ftbquests/quests"
diff -qr "$client_quests" "$server_quests" >/dev/null || { echo "Client/server quest files differ" >&2; exit 1; }

# 0.1.9-25 live quest sync checks
for qroot in "$client_quests" "$server_quests"; do
  test -f "$qroot/chapter_groups.snbt" || { echo "Quest chapter_groups.snbt missing" >&2; exit 1; }
  test "$(find "$qroot/chapters" -maxdepth 1 -name '*.snbt' -type f | wc -l)" = "25" || { echo "Expected 25 live quest chapters" >&2; exit 1; }
  test "$(find "$qroot/reward_tables" -maxdepth 1 -name '*.snbt' -type f | wc -l)" = "5" || { echo "Expected 5 live reward tables" >&2; exit 1; }
done
grep -Fq 'subtitle: "Build your first safe shelter and claim starter supplies."' "$client_quests/chapters/getting_started.snbt" || { echo "Make a home subtitle missing" >&2; exit 1; }
for item in minecraft:torch minecraft:bread minecraft:iron_ingot minecraft:compass minecraft:diamond minecraft:golden_carrot create:andesite_alloy create:brass_ingot minecraft:copper_block minecraft:powered_rail; do
  rg -F "$item" "$client_quests/chapters/getting_started.snbt" "$client_quests/chapters/create_engineering.snbt" >/dev/null || { echo "Repaired quest reward item missing: $item" >&2; exit 1; }
done
jq -e '.quest_live_sync_0_1_9_23.broken_item_rewards_fixed == 12' "$validation" >/dev/null

# 0.1.9-24 completed quest progression checks
jq -e '.quest_completion_0_1_9_24.quests_checked == 106 and .quest_completion_0_1_9_24.item_requirements_present == 106' "$validation" >/dev/null

# Final quest runtime-format checks
python3 "$repo_dir/scripts/hotfix-quest-finalize-0.1.9-25.py" --check-only
jq -e '.quest_finalize_0_1_9_25.quests_checked == 106 and .quest_finalize_0_1_9_25.malformed_item_stacks_remaining == 0 and .quest_finalize_0_1_9_25.optional_confirmation_tasks > 0 and .quest_finalize_0_1_9_25.required_confirmation_tasks > 0 and .quest_finalize_0_1_9_25.ids_preserved == true and .quest_finalize_0_1_9_25.client_server_quest_files_identical == true' "$validation" >/dev/null
if rg -n 'item:\s*\{\s*count:\s*1([bBsSlL])?\s*,\s*id:' "$client_quests/chapters" "$server_quests/chapters" >/dev/null; then
  echo "Malformed lowercase-count FTB Quests ItemStack remains" >&2
  exit 1
fi
grep -Fq 'item: "mekanism:metallurgic_infuser"' "$client_quests/chapters/mekanism.snbt" || { echo "Canonical Mekanism quest item filter missing" >&2; exit 1; }
grep -Fq 'optional_task: true' "$client_quests/chapters/mekanism.snbt" || { echo "Automatic Mekanism milestone confirmation is not optional" >&2; exit 1; }
if grep -Fq 'optional_task: true' "$client_quests/chapters/settlement.snbt"; then
  echo "Settlement build confirmations must remain manual" >&2
  exit 1
fi

client_compat="$repo_dir/client/overrides/kubejs/data"
server_compat="$repo_dir/server/kubejs/data"
diff -qr "$client_compat" "$server_compat" >/dev/null || { echo "Client/server compatibility data differs" >&2; exit 1; }
test "$(find "$client_compat" -path '*/recipes/*.json' -type f | wc -l)" = "36" || { echo "Expected 36 disabled recipe overrides" >&2; exit 1; }
test "$(find "$client_compat" -path '*/tags/*.json' -type f | wc -l)" = "4" || { echo "Expected 4 repaired tag files" >&2; exit 1; }
find "$client_compat" -name '*.json' -type f -print0 | xargs -0 -n1 jq -e . >/dev/null

overlay="$repo_dir/dist/Amber-and-Arcana-${version}-Crafty-Update-Overlay.zip"
test -f "$overlay" || { echo "Crafty update overlay missing" >&2; exit 1; }
unzip -tq "$overlay"
test "$(unzip -Z1 "$overlay" | grep -Fxc '_crafty/server-mods.tsv')" = "1" || { echo "Crafty update overlay missing server-mods.tsv" >&2; exit 1; }
test "$(unzip -Z1 "$overlay" | grep -Fxc '_crafty/remove-mods.txt')" = "1" || { echo "Crafty update overlay missing remove-mods.txt" >&2; exit 1; }
test "$(unzip -Z1 "$overlay" | grep -Fxc 'mods/morehitboxes-forge-1.20.1-1.9.2.1.jar')" = "1" || { echo "Crafty update overlay missing patched jar" >&2; exit 1; }
test "$(unzip -Z1 "$overlay" | grep -Fxc 'config/ftbquests/quests/chapters/getting_started.snbt')" = "1" || { echo "Crafty update overlay missing synced quests" >&2; exit 1; }

quest_overlay="$repo_dir/dist/Amber-and-Arcana-${version}-Crafty-Quest-Overlay.zip"
test -f "$quest_overlay" || { echo "Crafty quest-only overlay missing" >&2; exit 1; }
unzip -tq "$quest_overlay"
test "$(unzip -Z1 "$quest_overlay" | grep -Fxc 'config/ftbquests/quests/chapters/getting_started.snbt')" = "1" || { echo "Crafty quest-only overlay missing quest data" >&2; exit 1; }
if unzip -Z1 "$quest_overlay" | grep -Eq '^(world/|mods/|_crafty/)'; then
  echo "Crafty quest-only overlay contains non-quest server state" >&2
  exit 1
fi

unzip -tq "$repo_dir/dist/Amber-and-Arcana-${version}-Client.zip"
unzip -tq "$repo_dir/dist/Amber-and-Arcana-${version}-Server.zip"
( cd "$repo_dir/dist" && sha256sum -c SHA256SUMS.txt )
python3 "$repo_dir/scripts/validate-viewer.py"

echo "Amber & Arcana 0.1.9-25 static validation passed"
