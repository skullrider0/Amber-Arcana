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
jq -e '.version == "0.1.9-29" and .minecraft.version == "1.20.1" and .minecraft.modLoaders[0].id == "forge-47.4.10"' "$manifest" >/dev/null
jq -e '.pack_version == "0.1.9-29" and .recipe_viewer_0_1_9_15.rei_removed == true and .recipe_viewer_0_1_9_15.polymorph_removed == true and .recipe_tag_compat_0_1_9_14.disabled_recipe_ids == 36 and .recipe_tag_compat_0_1_9_14.repaired_tag_files == 4 and .content_cleanup_0_1_9_17.twilight_forest_removed == true and .content_cleanup_0_1_9_17.eternal_steak_chest_loot_blocked == true and .jei_dependency_fix_0_1_9_18.file_id == 6075247' "$validation" >/dev/null

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
printf '%s  %s
' 'd7dce29e3e791cd27af0d217d699583112d07b5d5f8700f9852a353013a554934fa5bbf1bb1d4d64f452ac6942e37315ba70081d700bf60e022836fe32354cb5' "$client_mh" | sha512sum --check - >/dev/null
printf '%s  %s
' 'd7dce29e3e791cd27af0d217d699583112d07b5d5f8700f9852a353013a554934fa5bbf1bb1d4d64f452ac6942e37315ba70081d700bf60e022836fe32354cb5' "$server_mh" | sha512sum --check - >/dev/null
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


# 0.1.9-29 live quest sync checks
for qroot in "$client_quests" "$server_quests"; do
  test -f "$qroot/chapter_groups.snbt" || { echo "Quest chapter_groups.snbt missing" >&2; exit 1; }
  test "$(find "$qroot/chapters" -maxdepth 1 -name '*.snbt' -type f | wc -l)" = "26" || { echo "Expected 26 live quest chapters" >&2; exit 1; }
  test "$(find "$qroot/reward_tables" -maxdepth 1 -name '*.snbt' -type f | wc -l)" = "31" || { echo "Expected 31 live reward tables" >&2; exit 1; }
done
grep -Fq 'subtitle: "Build your first safe shelter and claim starter supplies."' "$client_quests/chapters/getting_started.snbt" || { echo "Make a home subtitle missing" >&2; exit 1; }
for item in minecraft:torch minecraft:bread minecraft:iron_ingot minecraft:compass minecraft:diamond minecraft:golden_carrot create:andesite_alloy create:brass_ingot minecraft:copper_block minecraft:powered_rail; do
  rg -F "$item" "$client_quests/chapters/getting_started.snbt" "$client_quests/chapters/create_engineering.snbt" >/dev/null || { echo "Repaired quest reward item missing: $item" >&2; exit 1; }
done
jq -e '.quest_live_sync_0_1_9_23.broken_item_rewards_fixed == 12' "$validation" >/dev/null


# 0.1.9-29 completed quest progression checks
jq -e '.quest_completion_0_1_9_24.quests_checked == 106 and .quest_completion_0_1_9_24.item_requirements_present == 106' "$validation" >/dev/null

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

unzip -tq "$repo_dir/dist/Amber-and-Arcana-${version}-Client.zip"
unzip -tq "$repo_dir/dist/Amber-and-Arcana-${version}-Server.zip"
( cd "$repo_dir/dist" && sha256sum -c SHA256SUMS.txt )
python3 "$repo_dir/scripts/validate-viewer.py"

echo "Amber & Arcana 0.1.9-29 static validation passed"

# 0.1.9-26 weighted Wheel of Fortune checks
jq -e '.wheel_of_fortune_0_1_9_26.chapters_checked == 25 and .wheel_of_fortune_0_1_9_26.finale_loot_rewards == 25 and .wheel_of_fortune_0_1_9_26.generated_wheel_tables == 25 and .wheel_of_fortune_0_1_9_26.total_reward_tables == 30 and .wheel_of_fortune_0_1_9_26.modded_item_entries >= 25 and .wheel_of_fortune_0_1_9_26.client_server_quest_files_identical == true' "$validation" >/dev/null
grep -Fq '"ftbquests.rewards": "Wheel of Fortune"' "$repo_dir/client/overrides/kubejs/assets/ftbquests/lang/en_us.json" || { echo "Wheel of Fortune client heading override missing" >&2; exit 1; }

# 0.1.9-27 Productive Bees family-tree checks
jq -e '.productive_bees_0_1_9_27.productive_bees_version == "1.20.1-12.6.0" and .productive_bees_0_1_9_27.upstream_commit == "2190d6b4c0f4a35acc26415759c3be731d1eac22" and .productive_bees_0_1_9_27.setup_quests == 6 and .productive_bees_0_1_9_27.bee_quests >= 40 and .productive_bees_0_1_9_27.root_bees >= 2 and .productive_bees_0_1_9_27.generated_branches >= 3 and .productive_bees_0_1_9_27.total_chapters == 26 and .productive_bees_0_1_9_27.total_reward_tables == 31 and .productive_bees_0_1_9_27.total_finale_loot_rewards == 26 and .productive_bees_0_1_9_27.client_server_quest_files_identical == true' "$validation" >/dev/null
pb_chapter="$client_quests/chapters/productive_bees.snbt"
test -f "$pb_chapter" || { echo "Productive Bees chapter missing" >&2; exit 1; }
for item in productivebees:bee_cage productivebees:advanced_oak_beehive productivebees:expansion_box_oak productivebees:feeder productivebees:centrifuge productivebees:breeding_chamber; do
  grep -Fq "$item" "$pb_chapter" || { echo "Productive Bees setup item missing: $item" >&2; exit 1; }
done
grep -Fq 'title: "Master Apiarist"' "$pb_chapter" || { echo "Master Apiarist finale missing" >&2; exit 1; }
grep -Fq 'Wheel of Fortune — Productive Bees' "$client_quests/reward_tables/wheel_productive_bees.snbt" || { echo "Productive Bees wheel table missing" >&2; exit 1; }

# 0.1.9-28 Create progression checks
jq -e '.create_progression_0_1_9_28.create_version == "1.20.1-6.0.8" and .create_progression_0_1_9_28.upstream_commit == "1a1a9a2819b4f89f78caec41b55ed8cb222fa24b" and .create_progression_0_1_9_28.quests == 41 and .create_progression_0_1_9_28.new_quests == 35 and .create_progression_0_1_9_28.preserved_anchor_quests == 6 and .create_progression_0_1_9_28.milestone_item_tasks >= 50 and .create_progression_0_1_9_28.required_dependency_edges >= 45 and .create_progression_0_1_9_28.validated_create_item_ids >= 50 and .create_progression_0_1_9_28.historical_create_quest_ids_preserved == true and .create_progression_0_1_9_28.client_server_quest_files_identical == true' "$validation" >/dev/null
create_chapter="$client_quests/chapters/create_engineering.snbt"
test -f "$create_chapter" || { echo "Create Engineering chapter missing" >&2; exit 1; }
for item in create:andesite_alloy create:mechanical_press create:mechanical_mixer create:blaze_burner create:brass_ingot create:deployer create:precision_mechanism create:mechanical_crafter create:crushing_wheel create:packager create:stock_ticker create:steam_engine create:track_station create:schedule; do
  grep -Fq "$item" "$create_chapter" || { echo "Create milestone missing: $item" >&2; exit 1; }
done
for qid in 1ED63F4805934997 49A0DF8BF8B13288 2B415B8CDDC3ACFF 6A19120000000401 42BD2E092F753492 6A19120000000601; do
  grep -Fq "id: \"$qid\"" "$create_chapter" || { echo "Historical Create quest ID missing: $qid" >&2; exit 1; }
done
grep -Fq 'title: "A Reliable Factory"' "$create_chapter" || { echo "Create finale missing" >&2; exit 1; }
grep -Fq 'Wheel of Fortune — Create Engineering' "$client_quests/reward_tables/wheel_create_engineering.snbt" || { echo "Create wheel table missing" >&2; exit 1; }
grep -Fq 'create:stock_ticker' "$client_quests/reward_tables/wheel_create_engineering.snbt" || { echo "Create wheel was not refreshed" >&2; exit 1; }

# 0.1.9-29 mechanics-based quest grouping checks
jq -e '.quest_organization_0_1_9_29.chapter_groups == 9 and .quest_organization_0_1_9_29.chapters_grouped == 26 and .quest_organization_0_1_9_29.all_chapters_explicitly_assigned == true and .quest_organization_0_1_9_29.historical_ids_preserved == true and .quest_organization_0_1_9_29.client_server_quest_files_identical == true' "$validation" >/dev/null
groups="$client_quests/chapter_groups.snbt"
test -f "$groups" || { echo "chapter_groups.snbt missing" >&2; exit 1; }
for pair in \
  '5A29000000000001|Start Here' \
  '5A29000000000002|Machines & Production' \
  '5A29000000000003|Storage & Networks' \
  '5A29000000000004|Resources & Farming' \
  '5A29000000000005|Magic & Rituals' \
  '5A29000000000006|Exploration & Creatures' \
  '5A29000000000007|Building & Settlements' \
  '5A29000000000008|Tools, Combat & Equipment' \
  '5A29000000000009|Collections & Endgame'; do
  gid="${pair%%|*}"; title="${pair#*|}"
  grep -Fq "{ id: \"$gid\", title: \"$title\" }" "$groups" || { echo "Quest group missing: $title" >&2; exit 1; }
done
test "$(rg -n '^\s*group: "5A2900000000000[1-9]"\s*$' "$client_quests/chapters" | wc -l)" = "26" || { echo "Not all 26 chapters are assigned to mechanics groups" >&2; exit 1; }
grep -Fq 'group: "5A29000000000002"' "$client_quests/chapters/create_engineering.snbt" || { echo "Create Engineering is not under Machines & Production" >&2; exit 1; }
grep -Fq 'group: "5A29000000000002"' "$client_quests/chapters/mekanism.snbt" || { echo "Mekanism is not under Machines & Production" >&2; exit 1; }
grep -Fq 'group: "5A29000000000004"' "$client_quests/chapters/productive_bees.snbt" || { echo "Productive Bees is not under Resources & Farming" >&2; exit 1; }
cmp "$client_quests/chapter_groups.snbt" "$server_quests/chapter_groups.snbt" >/dev/null || { echo "Client/server chapter groups differ" >&2; exit 1; }

test "$(rg -n 'type: "loot"' "$client_quests/chapters" | wc -l)" = "26" || { echo "Expected 26 finale loot rewards" >&2; exit 1; }
test "$(find "$client_quests/reward_tables" -maxdepth 1 -name 'wheel_*.snbt' -type f | wc -l)" = "26" || { echo "Expected 26 generated client wheel tables" >&2; exit 1; }
test "$(find "$server_quests/reward_tables" -maxdepth 1 -name 'wheel_*.snbt' -type f | wc -l)" = "26" || { echo "Expected 26 generated server wheel tables" >&2; exit 1; }
quest_overlay="$repo_dir/dist/Amber-and-Arcana-${version}-Crafty-Quest-Overlay.zip"
test -f "$quest_overlay" || { echo "Quest-only Crafty overlay missing" >&2; exit 1; }
test "$(unzip -Z1 "$quest_overlay" | grep -Fxc 'config/ftbquests/quests/chapter_groups.snbt')" = "1" || { echo "chapter_groups.snbt missing from quest overlay" >&2; exit 1; }
test "$(unzip -Z1 "$quest_overlay" | grep -Fxc 'config/ftbquests/quests/chapters/productive_bees.snbt')" = "1" || { echo "Productive Bees chapter missing from quest overlay" >&2; exit 1; }
test "$(unzip -Z1 "$quest_overlay" | grep -Fxc 'config/ftbquests/quests/chapters/create_engineering.snbt')" = "1" || { echo "Create chapter missing from quest overlay" >&2; exit 1; }
