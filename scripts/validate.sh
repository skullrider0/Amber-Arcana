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
jq -e '.version == "0.1.9-56" and .minecraft.version == "1.20.1" and .minecraft.modLoaders[0].id == "forge-47.4.10"' "$manifest" >/dev/null
jq -e '.pack_version == "0.1.9-56" and .recipe_viewer_0_1_9_15.rei_removed == true and .recipe_viewer_0_1_9_15.polymorph_removed == true and .recipe_tag_compat_0_1_9_14.disabled_recipe_ids == 36 and .recipe_tag_compat_0_1_9_14.repaired_tag_files == 4 and .content_cleanup_0_1_9_17.twilight_forest_removed == true and .content_cleanup_0_1_9_17.eternal_steak_chest_loot_blocked == true and .jei_dependency_fix_0_1_9_18.file_id == 6075247' "$validation" >/dev/null

manifest_count="$(jq '.files | length' "$manifest")"
recorded_count="$(jq '.manifest_entries' "$summary")"
test "$manifest_count" = "$recorded_count" || { echo "Manifest count differs from build summary" >&2; exit 1; }

test "$(jq '[.files[] | select(.projectID == 238222 and .fileID == 6075247)] | length' "$manifest")" = "1" || { echo "Expected JEI 15.20.0.106 client pin" >&2; exit 1; }
for removed_project in 310111 521393 628539 544031 430127 255717 227639; do
  test "$(jq --argjson id "$removed_project" '[.files[] | select(.projectID == $id)] | length' "$manifest")" = "0" || { echo "Removed project still present: $removed_project" >&2; exit 1; }
done

if rg -i 'roughlyenoughitems|roughly_enough_items|reiplugincompatibilities|twilightforest|the-twilight-forest' "$repo_dir/server/_crafty/server-mods.tsv" >/dev/null; then
  echo "Removed viewer or Twilight Forest found in server mod list" >&2
  exit 1
fi
test "$(awk -F '\t' '$4 == "jei" && $1 == "6075247" && $2 == "jei-1.20.1-forge-15.20.0.106.jar" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Expected matching JEI 15.20.0.106 on server" >&2; exit 1; }

test "$(jq '[.files[] | select(.projectID == 1115989 or .fileID == 6942239)] | length' "$manifest")" = "0" || { echo "Official More Hitboxes entry must be absent from client manifest" >&2; exit 1; }
mh_sha512="$(awk 'NR==1 {print $1}' "$repo_dir/vendor/morehitboxes/1.9.2.3/SHA512SUMS.txt")"
client_mh="$repo_dir/client/overrides/mods/morehitboxes-forge-1.20.1-1.9.2.3.jar"
server_mh="$repo_dir/server/mods/morehitboxes-forge-1.20.1-1.9.2.3.jar"
test -f "$client_mh" && test -f "$server_mh" || { echo "Patched More Hitboxes jar missing" >&2; exit 1; }
printf '%s  %s
' "$mh_sha512" "$client_mh" | sha512sum --check - >/dev/null
printf '%s  %s
' "$mh_sha512" "$server_mh" | sha512sum --check - >/dev/null
cmp -s "$client_mh" "$server_mh" || { echo "Client/server More Hitboxes patch differs" >&2; exit 1; }
test "$(awk -F '\t' -v sha="$mh_sha512" '$4 == "more-hitboxes" && $1 == "0" && $2 == "morehitboxes-forge-1.20.1-1.9.2.3.jar" && $3 == sha {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Expected local More Hitboxes patch pin" >&2; exit 1; }
grep -Fxq 'morehitboxes-forge-1.20.1-1.9.2.jar' "$repo_dir/server/_crafty/remove-mods.txt" || { echo "Stock More Hitboxes cleanup missing" >&2; exit 1; }
grep -Fxq 'morehitboxes-forge-1.20.1-1.9.2.1.jar' "$repo_dir/server/_crafty/remove-mods.txt" || { echo "Old Amber More Hitboxes patch cleanup missing" >&2; exit 1; }
if grep -Fxq 'morehitboxes-forge-1.20.1-1.9.2.3.jar' "$repo_dir/server/_crafty/remove-mods.txt"; then
  echo "Patched More Hitboxes is scheduled for deletion" >&2
  exit 1
fi
jq -e '.more_hitboxes_perf_patch_0_1_9_22.enabled == true' "$validation" >/dev/null
jq -e '.more_hitboxes_spatial_cache_0_1_9_51.enabled == true and .more_hitboxes_spatial_cache_0_1_9_51.amber_patch_version == "1.9.2.3" and .more_hitboxes_spatial_cache_0_1_9_51.fossils_dependency_preserved == true and .more_hitboxes_spatial_cache_0_1_9_51.client_boot_tested == true and .more_hitboxes_spatial_cache_0_1_9_51.world_data_touched == false and .more_hitboxes_spatial_cache_0_1_9_51.runtime_spark_retest_required == true' "$validation" >/dev/null

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


# 0.1.9-30 live quest sync checks
for qroot in "$client_quests" "$server_quests"; do
  test -f "$qroot/chapter_groups.snbt" || { echo "Quest chapter_groups.snbt missing" >&2; exit 1; }
  test "$(find "$qroot/chapters" -maxdepth 1 -name '*.snbt' -type f | wc -l)" = "28" || { echo "Expected 28 live quest chapters" >&2; exit 1; }
  test "$(find "$qroot/reward_tables" -maxdepth 1 -name '*.snbt' -type f | wc -l)" = "145" || { echo "Expected 145 live reward tables" >&2; exit 1; }
done
grep -Fq 'subtitle: "Build your first safe shelter and claim starter supplies."' "$client_quests/chapters/getting_started.snbt" || { echo "Make a home subtitle missing" >&2; exit 1; }
for item in minecraft:torch minecraft:bread minecraft:iron_ingot minecraft:compass minecraft:diamond minecraft:golden_carrot create:andesite_alloy create:brass_ingot minecraft:copper_block minecraft:powered_rail; do
  rg -F "$item" "$client_quests/chapters/getting_started.snbt" "$client_quests/chapters/create_engineering.snbt" >/dev/null || { echo "Repaired quest reward item missing: $item" >&2; exit 1; }
done
jq -e '.quest_live_sync_0_1_9_23.broken_item_rewards_fixed == 12' "$validation" >/dev/null
jq -e '.quest_curation_0_1_9_45.create_generic_fallback_removed == true and .quest_curation_0_1_9_45.aa35_filler_quests_removed > 0 and .quest_curation_0_1_9_45.client_server_quest_files_identical == true' "$validation" >/dev/null


# 0.1.9-30 completed quest progression checks
jq -e '.quest_completion_0_1_9_24.quests_checked == 106 and .quest_completion_0_1_9_24.item_requirements_present == 106' "$validation" >/dev/null

client_compat="$repo_dir/client/overrides/kubejs/data"
server_compat="$repo_dir/server/kubejs/data"
diff -qr "$client_compat" "$server_compat" >/dev/null || { echo "Client/server compatibility data differs" >&2; exit 1; }
test "$(find "$client_compat" -path '*/recipes/*.json' -type f | wc -l)" = "65" || { echo "Expected 65 recipe compatibility files" >&2; exit 1; }
test "$(find "$client_compat" -path '*/tags/*.json' -type f | wc -l)" = "4" || { echo "Expected 4 repaired tag files" >&2; exit 1; }
find "$client_compat" -name '*.json' -type f -print0 | xargs -0 -n1 jq -e . >/dev/null

overlay="$repo_dir/dist/Amber-and-Arcana-${version}-Crafty-Update-Overlay.zip"
test -f "$overlay" || { echo "Crafty update overlay missing" >&2; exit 1; }
unzip -tq "$overlay"
test "$(unzip -Z1 "$overlay" | grep -Fxc '_crafty/server-mods.tsv')" = "1" || { echo "Crafty update overlay missing server-mods.tsv" >&2; exit 1; }
test "$(unzip -Z1 "$overlay" | grep -Fxc '_crafty/remove-mods.txt')" = "1" || { echo "Crafty update overlay missing remove-mods.txt" >&2; exit 1; }
test "$(unzip -Z1 "$overlay" | grep -Fxc 'mods/morehitboxes-forge-1.20.1-1.9.2.3.jar')" = "1" || { echo "Crafty update overlay missing patched jar" >&2; exit 1; }
test "$(unzip -Z1 "$overlay" | grep -Fxc 'mods/morehitboxes-forge-1.20.1-1.9.2.1.jar')" = "0" || { echo "Crafty update overlay still contains old More Hitboxes patch jar" >&2; exit 1; }


test "$(unzip -Z1 "$overlay" | grep -Fxc 'config/ftbquests/quests/chapters/getting_started.snbt')" = "1" || { echo "Crafty update overlay missing synced quests" >&2; exit 1; }

unzip -tq "$repo_dir/dist/Amber-and-Arcana-${version}-Client.zip"
unzip -tq "$repo_dir/dist/Amber-and-Arcana-${version}-Server.zip"
( cd "$repo_dir/dist" && sha256sum -c SHA256SUMS.txt )
python3 "$repo_dir/scripts/validate-viewer.py"

echo "Amber & Arcana 0.1.9-56 static validation passed"

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

# 0.1.9-30 mechanics-based quest grouping checks
jq -e '.quest_organization_0_1_9_29.chapter_groups == 9 and .quest_organization_0_1_9_29.chapters_grouped == 26 and .quest_organization_0_1_9_29.all_chapters_explicitly_assigned == true and .quest_organization_0_1_9_29.historical_ids_preserved == true and .quest_organization_0_1_9_29.client_server_quest_files_identical == true' "$validation" >/dev/null
groups="$client_quests/chapter_groups.snbt"
test -f "$groups" || { echo "chapter_groups.snbt missing" >&2; exit 1; }
for pair in \
  '5A29000000000001|Start Here' \
  '5A29000000000002|Machines and Production' \
  '5A29000000000003|Storage and Networks' \
  '5A29000000000004|Resources and Farming' \
  '5A29000000000005|Magic and Rituals' \
  '5A29000000000006|Exploration and Creatures' \
  '5A29000000000007|Building and Settlements' \
  '5A29000000000008|Tools, Combat and Equipment' \
  '5A29000000000009|Collections and Endgame'; do
  gid="${pair%%|*}"; title="${pair#*|}"
  grep -Fq "{ id: \"$gid\", title: \"$title\" }" "$groups" || { echo "Quest group missing: $title" >&2; exit 1; }
done
test "$(rg -n '^\s*group: "5A2900000000000[1-9]"\s*$' "$client_quests/chapters" | wc -l)" = "28" || { echo "Not all 28 chapters are assigned to mechanics groups" >&2; exit 1; }
grep -Fq 'group: "5A29000000000002"' "$client_quests/chapters/create_engineering.snbt" || { echo "Create Engineering is not under Machines and Production" >&2; exit 1; }
grep -Fq 'group: "5A29000000000002"' "$client_quests/chapters/mekanism.snbt" || { echo "Mekanism is not under Machines and Production" >&2; exit 1; }
grep -Fq 'group: "5A29000000000004"' "$client_quests/chapters/productive_bees.snbt" || { echo "Productive Bees is not under Resources and Farming" >&2; exit 1; }
cmp "$client_quests/chapter_groups.snbt" "$server_quests/chapter_groups.snbt" >/dev/null || { echo "Client/server chapter groups differ" >&2; exit 1; }

# 0.1.9-30 loot coverage is validated from release metadata below
test "$(find "$client_quests/reward_tables" -maxdepth 1 -name 'wheel_*.snbt' -type f | wc -l)" = "28" || { echo "Expected 28 generated client wheel tables" >&2; exit 1; }
test "$(find "$server_quests/reward_tables" -maxdepth 1 -name 'wheel_*.snbt' -type f | wc -l)" = "28" || { echo "Expected 28 generated server wheel tables" >&2; exit 1; }
quest_overlay="$repo_dir/dist/Amber-and-Arcana-${version}-Crafty-Quest-Overlay.zip"
test -f "$quest_overlay" || { echo "Quest-only Crafty overlay missing" >&2; exit 1; }
test "$(unzip -Z1 "$quest_overlay" | grep -Fxc 'config/ftbquests/quests/chapter_groups.snbt')" = "1" || { echo "chapter_groups.snbt missing from quest overlay" >&2; exit 1; }
test "$(unzip -Z1 "$quest_overlay" | grep -Fxc 'config/ftbquests/quests/chapters/productive_bees.snbt')" = "1" || { echo "Productive Bees chapter missing from quest overlay" >&2; exit 1; }
test "$(unzip -Z1 "$quest_overlay" | grep -Fxc 'config/ftbquests/quests/chapters/create_engineering.snbt')" = "1" || { echo "Create chapter missing from quest overlay" >&2; exit 1; }


# 0.1.9-30 quest UX checks
jq -e '.quest_ux_0_1_9_30.group_labels_fixed == true and .quest_ux_0_1_9_30.chapters_relaid_out == 26 and .quest_ux_0_1_9_30.total_quests >= 220 and .quest_ux_0_1_9_30.loot_coverage_percent >= 70 and .quest_ux_0_1_9_30.tier_tables == 4 and .quest_ux_0_1_9_30.total_reward_tables == 35 and .quest_ux_0_1_9_30.bee_species_item_detection == .productive_bees_0_1_9_27.bee_quests and .quest_ux_0_1_9_30.bee_manual_species_tasks_remaining == 0 and .quest_ux_0_1_9_30.historical_ids_preserved == true and .quest_ux_0_1_9_30.client_server_quest_files_identical == true' "$validation" >/dev/null

groups="$client_quests/chapter_groups.snbt"
for label in 'Machines and Production' 'Storage and Networks' 'Resources and Farming' 'Magic and Rituals' 'Exploration and Creatures' 'Building and Settlements' 'Tools, Combat and Equipment' 'Collections and Endgame'; do
  grep -Fq "title: \"$label\"" "$groups" || { echo "Parser-safe group label missing: $label" >&2; exit 1; }
done
if rg -F ' & ' "$client_quests" >/dev/null; then
  echo "Literal ampersand-space remains in FTB Quests text" >&2
  exit 1
fi

pb_chapter="$client_quests/chapters/productive_bees.snbt"
grep -Fq 'id: "productivebees:configurable_honeycomb"' "$pb_chapter" || { echo "Typed Productive Bees honeycomb tasks missing" >&2; exit 1; }
grep -Fq 'id: "productivebees:bee_cage"' "$pb_chapter" || { echo "Filled Productive Bees cage tasks missing" >&2; exit 1; }
grep -Fq 'match_nbt: true' "$pb_chapter" || { echo "Productive Bees NBT matching missing" >&2; exit 1; }
grep -Fq 'weak_nbt_match: true' "$pb_chapter" || { echo "Productive Bees weak NBT matching missing" >&2; exit 1; }

loot_count="$(rg -n 'type: "loot"' "$client_quests/chapters" | wc -l)"
covered="$(jq -r '.quest_ux_0_1_9_30.loot_covered_quests' "$validation")"
test "$loot_count" -ge "$covered" || { echo "Quest loot reward count is below recorded coverage" >&2; exit 1; }

quest_overlay="$repo_dir/dist/Amber-and-Arcana-${version}-Crafty-Quest-Overlay.zip"


# 0.1.9-32 Productive Bees cage-label checks
jq -e '.bee_cage_ui_0_1_9_31.cage_tasks_labeled == 26 and .bee_cage_ui_0_1_9_31.species_filters_verified == 26 and .bee_cage_ui_0_1_9_31.matching_behavior_changed == false and .bee_cage_ui_0_1_9_31.client_server_quest_files_identical == true' "$validation" >/dev/null
test "$(grep -Ec '^\s*title: "Capture .*Bee"' "$client_quests/chapters/productive_bees.snbt")" -ge "26" || { echo "Productive Bees cage task species labels missing" >&2; exit 1; }


# 0.1.9-32 mod-specific tier loot checks
jq -e '.mod_tier_loot_0_1_9_32.tier_tables == 104 and .mod_tier_loot_0_1_9_32.depth_rewards_retargeted >= 100 and .mod_tier_loot_0_1_9_32.generic_depth_tables_remaining == 0 and .mod_tier_loot_0_1_9_32.powah_nitro_jackpots == 4 and .mod_tier_loot_0_1_9_32.client_server_quest_files_identical == true' "$validation" >/dev/null
test "$(find "$client_quests/reward_tables" -maxdepth 1 -name 'modroll_*_tier_*.snbt' -type f | wc -l)" = "112" || { echo "Mod-specific tier table count mismatch" >&2; exit 1; }
test "$(find "$client_quests/reward_tables" -maxdepth 1 -name 'depth_tier_*.snbt' -type f | wc -l)" = "0" || { echo "Legacy generic depth tables still present" >&2; exit 1; }
if rg -n 'minecraft:(diamond|emerald|emerald_block)' "$client_quests/reward_tables/modroll_"* >/dev/null; then echo "Generic diamond/emerald leaked into mod tier tables" >&2; exit 1; fi
grep -Fq 'item: "powah:thermo_generator_nitro", weight: 0.25f' "$client_quests/reward_tables/modroll_powah_tier_4.snbt" || { echo "Rare Nitro Thermo Generator jackpot missing" >&2; exit 1; }
grep -Fq 'item: "powah:reactor_nitro", weight: 0.20f' "$client_quests/reward_tables/modroll_powah_tier_4.snbt" || { echo "Rare Nitro Reactor jackpot missing" >&2; exit 1; }
grep -Eq 'loot_size: [34]' "$client_quests/reward_tables/modroll_powah_tier_4.snbt" || { echo "High-tier multi-item roll missing" >&2; exit 1; }


# 0.1.9-33 Productive Bees reward progression checks
jq -e '.productive_bees_rewards_0_1_9_33.tier_tables_rebalanced == 4 and .productive_bees_rewards_0_1_9_33.tier_entry_counts["1"] >= 10 and .productive_bees_rewards_0_1_9_33.tier_entry_counts["2"] >= 15 and .productive_bees_rewards_0_1_9_33.tier_entry_counts["3"] >= 18 and .productive_bees_rewards_0_1_9_33.tier_entry_counts["4"] >= 20 and .productive_bees_rewards_0_1_9_33.tier_loot_sizes["4"] == 4 and .productive_bees_rewards_0_1_9_33.finale_loot_size == 5 and .productive_bees_rewards_0_1_9_33.unique_productive_bees_rewards >= 30 and .productive_bees_rewards_0_1_9_33.generic_vanilla_items_in_new_bee_tables == 0 and .productive_bees_rewards_0_1_9_33.historical_table_ids_preserved == true and .productive_bees_rewards_0_1_9_33.client_server_quest_files_identical == true' "$validation" >/dev/null
pb_t4="$client_quests/reward_tables/modroll_productive_bees_tier_4.snbt"
pb_wheel="$client_quests/reward_tables/wheel_productive_bees.snbt"
grep -Fq 'loot_size: 4' "$pb_t4" || { echo "Productive Bees Tier 4 should return four draws" >&2; exit 1; }
grep -Fq 'item: "productivebees:upgrade_productivity_4", weight: 0.30f' "$pb_t4" || { echo "Productive Bees Omega Tier 4 jackpot missing" >&2; exit 1; }
grep -Fq 'loot_size: 5' "$pb_wheel" || { echo "Productive Bees finale should return five draws" >&2; exit 1; }
grep -Fq 'item: "productivebees:upgrade_productivity_4", weight: 0.20f' "$pb_wheel" || { echo "Productive Bees finale Omega jackpot missing" >&2; exit 1; }
if rg -n 'minecraft:(diamond|emerald|emerald_block)' "$client_quests/reward_tables/modroll_productive_bees_tier_"*.snbt "$pb_wheel" >/dev/null; then
  echo "Generic diamond/emerald reward leaked into Productive Bees progression tables" >&2
  exit 1
fi


# 0.1.9-34 short-chain reward progression checks
jq -e '.short_chain_rewards_0_1_9_34.short_chapters_rebalanced >= 10 and .short_chain_rewards_0_1_9_34.short_quests_rebalanced >= 30 and .short_chain_rewards_0_1_9_34.short_quest_roll_coverage_percent == 100 and .short_chain_rewards_0_1_9_34.generic_vanilla_items_added == 0 and .short_chain_rewards_0_1_9_34.client_server_quest_files_identical == true' "$validation" >/dev/null
for table in "$client_quests"/reward_tables/modroll_*_tier_4.snbt; do
  stem="$(basename "$table")"
  if [ "$stem" = "modroll_productive_bees_tier_4.snbt" ] || [ "$stem" = "modroll_create_engineering_tier_4.snbt" ]; then continue; fi
  grep -Eq 'loot_size: [34]' "$table" || { echo "Expanded T4 table has too few draws: $stem" >&2; exit 1; }
done


# 0.1.9-39 deep compact-chapter progression checks
jq -e '.deep_short_progression_0_1_9_35.chapters_expanded == 24 and .deep_short_progression_0_1_9_35.historical_short_quests_preserved >= 100 and .deep_short_progression_0_1_9_35.generated_mechanics_quests >= 100 and .deep_short_progression_0_1_9_35.minimum_quests_per_expanded_chapter >= 10 and .deep_short_progression_0_1_9_35.minimum_dependency_depth >= 4 and .deep_short_progression_0_1_9_35.tier_roll_coverage_percent == 100 and .deep_short_progression_0_1_9_35.finale_wheels_moved_to_true_mastery == 24 and .deep_short_progression_0_1_9_35.historical_quest_ids_preserved == true and .deep_short_progression_0_1_9_35.client_server_quest_files_identical == true' "$validation" >/dev/null
if rg -F 'AA35 deep progression milestone' "$client_quests/chapters" >/dev/null; then echo "AA35 filler milestone remains after 0.1.9-45 curation" >&2; exit 1; fi
diff -qr "$client_quests" "$server_quests" >/dev/null || { echo "Client/server quest trees differ after 0.1.9-39" >&2; exit 1; }


# 0.1.9-39 requested technology/content expansion checks
for pin in 351748:4864220 284497:6880323 1060096:5870964 223565:6793843 231382:5422013 242818:8491810 552574:5895036 283644:6274231 1632230:8670714; do
  project="${pin%%:*}"
  file="${pin##*:}"
  test "$(jq --argjson p "$project" --argjson f "$file" '[.files[] | select(.projectID == $p and .fileID == $f)] | length' "$manifest")" = "1" || { echo "Missing 0.1.9-39 client manifest pin $pin" >&2; exit 1; }
done
test "$(awk -F '\\t' '$1 == "4864220" && $2 == "mininggadgets-1.15.6.jar" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-39 server mod pin: Mining Gadgets" >&2; exit 1; }
test "$(awk -F '\\t' '$1 == "6880323" && $2 == "IronJetpacks-1.20.1-7.0.9.jar" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-39 server mod pin: Iron Jetpacks" >&2; exit 1; }
test "$(awk -F '\\t' '$1 == "5870964" && $2 == "mekanism_lasers-1.0.10.jar" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-39 server mod pin: Mekanism Lasers" >&2; exit 1; }
test "$(awk -F '\\t' '$1 == "6793843" && $2 == "Draconic-Evolution-1.20.1-3.1.2.621-universal.jar" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-39 server mod pin: Draconic Evolution" >&2; exit 1; }
test "$(awk -F '\\t' '$1 == "5422013" && $2 == "BrandonsCore-1.20.1-3.2.1.302-universal.jar" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-39 server mod pin: Brandon's Core" >&2; exit 1; }
test "$(awk -F '\\t' '$1 == "8491810" && $2 == "CodeChickenLib-1.20.1-4.4.0.528-universal.jar" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-39 server mod pin: CodeChicken Lib" >&2; exit 1; }
test "$(awk -F '\\t' '$1 == "5895036" && $2 == "HostileNeuralNetworks-1.20.1-5.3.3.jar" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-39 server mod pin: Hostile Neural Networks" >&2; exit 1; }
test "$(awk -F '\\t' '$1 == "6274231" && $2 == "Placebo-1.20.1-8.6.3.jar" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-39 server mod pin: Placebo" >&2; exit 1; }
test "$(awk -F '\\t' '$1 == "8670714" && $2 == "ottertaming-1.20.1-Forge-1.0.2.jar" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-39 server mod pin: Infernos Otter Taming" >&2; exit 1; }
jq -e '.tech_expansion_0_1_9_36.curseforge_entries_added == 9 and .tech_expansion_0_1_9_36.requires_client_update == true and .tech_expansion_0_1_9_36.world_data_touched == false and .tech_expansion_0_1_9_36.crafty_update_overlay_world_safe == true and .tech_expansion_0_1_9_36.server_downloads_on_next_start == true' "$validation" >/dev/null


# 0.1.9-39 ATM10-inspired compact layout checks
jq -e '.atm10_layout_0_1_9_37.reference_pack == "AllTheMods/ATM-10" and .atm10_layout_0_1_9_37.reference_commit == "ab6f65e07b88423cdae1724864ba42a573ba758a" and .atm10_layout_0_1_9_37.chapters_compacted == 26 and .atm10_layout_0_1_9_37.quest_ids_preserved == true and .atm10_layout_0_1_9_37.tasks_preserved == true and .atm10_layout_0_1_9_37.rewards_preserved == true and .atm10_layout_0_1_9_37.fortune_wheel_preserved == true and .atm10_layout_0_1_9_37.client_server_quest_files_identical == true and .atm10_layout_0_1_9_37.max_chapter_width_after < .atm10_layout_0_1_9_37.max_chapter_width_before' "$validation" >/dev/null
test "$(grep -Rhc $'\tprogression_mode: "flexible"' "$client_quests/chapters"/*.snbt | awk '{s+=$1} END {print s+0}')" = "28" || { echo "Expected flexible progression mode in all 28 chapters" >&2; exit 1; }
diff -qr "$client_quests" "$server_quests" >/dev/null || { echo "Client/server quest trees differ after 0.1.9-39" >&2; exit 1; }


# 0.1.9-39 ATM10-inspired semantic major progression checks
jq -e '.atm10_major_progression_0_1_9_38.reference_pack == "AllTheMods/ATM-10" and .atm10_major_progression_0_1_9_38.reference_commit == "ab6f65e07b88423cdae1724864ba42a573ba758a" and .atm10_major_progression_0_1_9_38.existing_chapters_rebuilt == 7 and .atm10_major_progression_0_1_9_38.new_chapters_added == 2 and .atm10_major_progression_0_1_9_38.final_chapters == 28 and .atm10_major_progression_0_1_9_38.preserved_existing_quest_ids == 91 and .atm10_major_progression_0_1_9_38.reward_tables_final == 145 and .atm10_major_progression_0_1_9_38.fortune_wheels_touched == 9 and .atm10_major_progression_0_1_9_38.client_server_quest_files_identical == true' "$validation" >/dev/null
for chapter in hostile_neural_networks draconic_evolution; do
  test -f "$client_quests/chapters/$chapter.snbt" || { echo "Missing new 0.1.9-39 chapter: $chapter" >&2; exit 1; }
done
for chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage; do
  if rg -F 'AA35 deep progression milestone' "$client_quests/chapters/$chapter.snbt" >/dev/null; then
    echo "Generic AA35 filler remains in rebuilt major chapter: $chapter" >&2
    exit 1
  fi
done
for chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage hostile_neural_networks draconic_evolution; do
  for tier in 1 2 3 4; do
    test -f "$client_quests/reward_tables/modroll_${chapter}_tier_${tier}.snbt" || { echo "Missing hand-curated tier table: $chapter tier $tier" >&2; exit 1; }
  done
  test -f "$client_quests/reward_tables/wheel_${chapter}.snbt" || { echo "Missing Fortune Wheel: $chapter" >&2; exit 1; }
done
diff -qr "$client_quests" "$server_quests" >/dev/null || { echo "Client/server quest trees differ after 0.1.9-39" >&2; exit 1; }


# 0.1.9-39 No Recipe Book Reborn client-only checks
test "$(jq '[.files[] | select(.projectID == 551314 and .fileID == 4725571)] | length' "$manifest")" = "1" || { echo "Expected No Recipe Book Reborn 1.0.5 client pin" >&2; exit 1; }
if rg -F 'norecipebookreborn-1.0.5.jar' "$repo_dir/server/_crafty/server-mods.tsv" >/dev/null || rg -F $'\tno-recipe-book-reborn\t' "$repo_dir/server/_crafty/server-mods.tsv" >/dev/null; then
  echo "No Recipe Book Reborn is client-only and must not be installed on the dedicated server" >&2
  exit 1
fi
jq -e '.no_recipe_book_reborn_0_1_9_39.project_id == 551314 and .no_recipe_book_reborn_0_1_9_39.file_id == 4725571 and .no_recipe_book_reborn_0_1_9_39.environment == "client-only" and .no_recipe_book_reborn_0_1_9_39.requires_server_update == false and .no_recipe_book_reborn_0_1_9_39.world_data_touched == false' "$validation" >/dev/null


# 0.1.9-39 ATM10-inspired semantic major progression checks
jq -e '.atm10_major_progression_0_1_9_38.reference_pack == "AllTheMods/ATM-10" and .atm10_major_progression_0_1_9_38.reference_commit == "ab6f65e07b88423cdae1724864ba42a573ba758a" and .atm10_major_progression_0_1_9_38.existing_chapters_rebuilt == 7 and .atm10_major_progression_0_1_9_38.new_chapters_added == 2 and .atm10_major_progression_0_1_9_38.final_chapters == 28 and .atm10_major_progression_0_1_9_38.preserved_existing_quest_ids == 91 and .atm10_major_progression_0_1_9_38.reward_tables_final == 145 and .atm10_major_progression_0_1_9_38.fortune_wheels_touched == 9 and .atm10_major_progression_0_1_9_38.client_server_quest_files_identical == true' "$validation" >/dev/null
for chapter in hostile_neural_networks draconic_evolution; do
  test -f "$client_quests/chapters/$chapter.snbt" || { echo "Missing new 0.1.9-39 chapter: $chapter" >&2; exit 1; }
done
for chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage; do
  if rg -F 'AA35 deep progression milestone' "$client_quests/chapters/$chapter.snbt" >/dev/null; then
    echo "Generic AA35 filler remains in rebuilt major chapter: $chapter" >&2
    exit 1
  fi
done
for chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage hostile_neural_networks draconic_evolution; do
  for tier in 1 2 3 4; do
    test -f "$client_quests/reward_tables/modroll_${chapter}_tier_${tier}.snbt" || { echo "Missing hand-curated tier table: $chapter tier $tier" >&2; exit 1; }
  done
  test -f "$client_quests/reward_tables/wheel_${chapter}.snbt" || { echo "Missing Fortune Wheel: $chapter" >&2; exit 1; }
done
diff -qr "$client_quests" "$server_quests" >/dev/null || { echo "Client/server quest trees differ after 0.1.9-39" >&2; exit 1; }


# 0.1.9-39 ATM10-inspired semantic major progression checks
jq -e '.atm10_major_progression_0_1_9_38.reference_pack == "AllTheMods/ATM-10" and .atm10_major_progression_0_1_9_38.reference_commit == "ab6f65e07b88423cdae1724864ba42a573ba758a" and .atm10_major_progression_0_1_9_38.existing_chapters_rebuilt == 7 and .atm10_major_progression_0_1_9_38.new_chapters_added == 2 and .atm10_major_progression_0_1_9_38.final_chapters == 28 and .atm10_major_progression_0_1_9_38.preserved_existing_quest_ids == 91 and .atm10_major_progression_0_1_9_38.reward_tables_final == 145 and .atm10_major_progression_0_1_9_38.fortune_wheels_touched == 9 and .atm10_major_progression_0_1_9_38.client_server_quest_files_identical == true' "$validation" >/dev/null
for chapter in hostile_neural_networks draconic_evolution; do
  test -f "$client_quests/chapters/$chapter.snbt" || { echo "Missing new 0.1.9-39 chapter: $chapter" >&2; exit 1; }
done
for chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage; do
  if rg -F 'AA35 deep progression milestone' "$client_quests/chapters/$chapter.snbt" >/dev/null; then
    echo "Generic AA35 filler remains in rebuilt major chapter: $chapter" >&2
    exit 1
  fi
done
for chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage hostile_neural_networks draconic_evolution; do
  for tier in 1 2 3 4; do
    test -f "$client_quests/reward_tables/modroll_${chapter}_tier_${tier}.snbt" || { echo "Missing hand-curated tier table: $chapter tier $tier" >&2; exit 1; }
  done
  test -f "$client_quests/reward_tables/wheel_${chapter}.snbt" || { echo "Missing Fortune Wheel: $chapter" >&2; exit 1; }
done
diff -qr "$client_quests" "$server_quests" >/dev/null || { echo "Client/server quest trees differ after 0.1.9-39" >&2; exit 1; }


# 0.1.9-39 ATM10-inspired semantic major progression checks
jq -e '.atm10_major_progression_0_1_9_38.reference_pack == "AllTheMods/ATM-10" and .atm10_major_progression_0_1_9_38.reference_commit == "ab6f65e07b88423cdae1724864ba42a573ba758a" and .atm10_major_progression_0_1_9_38.existing_chapters_rebuilt == 7 and .atm10_major_progression_0_1_9_38.new_chapters_added == 2 and .atm10_major_progression_0_1_9_38.final_chapters == 28 and .atm10_major_progression_0_1_9_38.preserved_existing_quest_ids == 91 and .atm10_major_progression_0_1_9_38.reward_tables_final == 145 and .atm10_major_progression_0_1_9_38.fortune_wheels_touched == 9 and .atm10_major_progression_0_1_9_38.client_server_quest_files_identical == true' "$validation" >/dev/null
for chapter in hostile_neural_networks draconic_evolution; do
  test -f "$client_quests/chapters/$chapter.snbt" || { echo "Missing new 0.1.9-39 chapter: $chapter" >&2; exit 1; }
done
for chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage; do
  if rg -F 'AA35 deep progression milestone' "$client_quests/chapters/$chapter.snbt" >/dev/null; then
    echo "Generic AA35 filler remains in rebuilt major chapter: $chapter" >&2
    exit 1
  fi
done
for chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage hostile_neural_networks draconic_evolution; do
  for tier in 1 2 3 4; do
    test -f "$client_quests/reward_tables/modroll_${chapter}_tier_${tier}.snbt" || { echo "Missing hand-curated tier table: $chapter tier $tier" >&2; exit 1; }
  done
  test -f "$client_quests/reward_tables/wheel_${chapter}.snbt" || { echo "Missing Fortune Wheel: $chapter" >&2; exit 1; }
done
diff -qr "$client_quests" "$server_quests" >/dev/null || { echo "Client/server quest trees differ after 0.1.9-39" >&2; exit 1; }


# 0.1.9-40 CurseForge downloader compatibility checks
jq -e '.curseforge_download_fix_0_1_9_40.server_manifest_has_project_ids == true and .curseforge_download_fix_0_1_9_40.curseforge_web_download_fallback == true and .curseforge_download_fix_0_1_9_40.cursemaven_fallback == true and .curseforge_download_fix_0_1_9_40.authenticated_cdn_supported == true and .curseforge_download_fix_0_1_9_40.launcher_in_update_overlay == true and .curseforge_download_fix_0_1_9_40.world_data_touched == false and .curseforge_download_fix_0_1_9_40.world_data_in_update_overlay == false' "$validation" >/dev/null
awk -F '\t' 'BEGIN{bad=0} /^#/ || NF==0 {next} NF!=6 {bad++} $1!="0" && ($6=="" || $6=="0") {bad++} END{exit bad?1:0}' "$repo_dir/server/_crafty/server-mods.tsv" || { echo "0.1.9-40 server mod rows are missing project IDs" >&2; exit 1; }
grep -Fq 'CURSEFORGE_API_KEY' "$repo_dir/server/_crafty/source/AmberArcanaCraftyLauncher.java" || { echo "Launcher API-key support missing" >&2; exit 1; }
grep -Fq 'www.curseforge.com/api/v1/mods/' "$repo_dir/server/_crafty/source/AmberArcanaCraftyLauncher.java" || { echo "Launcher CurseForge web fallback missing" >&2; exit 1; }
grep -Fq 'cursemaven.com' "$repo_dir/server/_crafty/source/AmberArcanaCraftyLauncher.java" || { echo "Launcher CurseMaven fallback missing" >&2; exit 1; }
update_overlay="$repo_dir/dist/Amber-and-Arcana-${version}-Crafty-Update-Overlay.zip"
test "$(unzip -Z1 "$update_overlay" | grep -Fxc 'AmberArcana-Crafty-Launcher.jar')" = "1" || { echo "Updated Crafty launcher missing from update overlay" >&2; exit 1; }
if unzip -Z1 "$update_overlay" | grep -Ei '(^|/)(world|world_nether|world_the_end)(/|$)' >/dev/null; then echo "World data leaked into update overlay" >&2; exit 1; fi


# 0.1.9-39 ATM10-inspired semantic major progression checks
jq -e '.atm10_major_progression_0_1_9_38.reference_pack == "AllTheMods/ATM-10" and .atm10_major_progression_0_1_9_38.reference_commit == "ab6f65e07b88423cdae1724864ba42a573ba758a" and .atm10_major_progression_0_1_9_38.existing_chapters_rebuilt == 7 and .atm10_major_progression_0_1_9_38.new_chapters_added == 2 and .atm10_major_progression_0_1_9_38.final_chapters == 28 and .atm10_major_progression_0_1_9_38.preserved_existing_quest_ids == 91 and .atm10_major_progression_0_1_9_38.reward_tables_final == 145 and .atm10_major_progression_0_1_9_38.fortune_wheels_touched == 9 and .atm10_major_progression_0_1_9_38.client_server_quest_files_identical == true' "$validation" >/dev/null
for chapter in hostile_neural_networks draconic_evolution; do
  test -f "$client_quests/chapters/$chapter.snbt" || { echo "Missing new 0.1.9-39 chapter: $chapter" >&2; exit 1; }
done
for chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage; do
  if rg -F 'AA35 deep progression milestone' "$client_quests/chapters/$chapter.snbt" >/dev/null; then
    echo "Generic AA35 filler remains in rebuilt major chapter: $chapter" >&2
    exit 1
  fi
done
for chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage hostile_neural_networks draconic_evolution; do
  for tier in 1 2 3 4; do
    test -f "$client_quests/reward_tables/modroll_${chapter}_tier_${tier}.snbt" || { echo "Missing hand-curated tier table: $chapter tier $tier" >&2; exit 1; }
  done
  test -f "$client_quests/reward_tables/wheel_${chapter}.snbt" || { echo "Missing Fortune Wheel: $chapter" >&2; exit 1; }
done
diff -qr "$client_quests" "$server_quests" >/dev/null || { echo "Client/server quest trees differ after 0.1.9-39" >&2; exit 1; }


# 0.1.9-41 recipe conflict + Spartan Weaponry checks
test "$(jq '[.files[] | select(.projectID == 388800 and .fileID == 6450982)] | length' "$manifest")" = "1" || { echo "Missing 0.1.9-41 client pin: Polymorph" >&2; exit 1; }
test "$(awk -F '\t' '$1 == "6450982" && $2 == "polymorph-forge-0.49.10+1.20.1.jar" && $4 == "polymorph" && $6 == "388800" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-41 server pin: Polymorph" >&2; exit 1; }
test "$(jq '[.files[] | select(.projectID == 941096 and .fileID == 5282394)] | length' "$manifest")" = "1" || { echo "Missing 0.1.9-41 client pin: Polymorphic Energistics" >&2; exit 1; }
test "$(awk -F '\t' '$1 == "5282394" && $2 == "polyeng-forge-0.1.1-1.20.1.jar" && $4 == "polymorphic-energistics" && $6 == "941096" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-41 server pin: Polymorphic Energistics" >&2; exit 1; }
test "$(jq '[.files[] | select(.projectID == 943086 and .fileID == 5227282)] | length' "$manifest")" = "1" || { echo "Missing 0.1.9-41 client pin: Refined Polymorphism" >&2; exit 1; }
test "$(awk -F '\t' '$1 == "5227282" && $2 == "refinedpolymorph-0.1.1-1.20.1.jar" && $4 == "refined-polymorphism" && $6 == "943086" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-41 server pin: Refined Polymorphism" >&2; exit 1; }
test "$(jq '[.files[] | select(.projectID == 278141 and .fileID == 6842571)] | length' "$manifest")" = "1" || { echo "Missing 0.1.9-41 client pin: Spartan Weaponry" >&2; exit 1; }
test "$(awk -F '\t' '$1 == "6842571" && $2 == "SpartanWeaponry-1.20.1-forge-3.2.1-all.jar" && $4 == "spartan-weaponry" && $6 == "278141" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-41 server pin: Spartan Weaponry" >&2; exit 1; }
if grep -Fxq 'polymorph-forge-0.49.10+1.20.1.jar' "$repo_dir/server/_crafty/remove-mods.txt"; then echo "Current Polymorph jar is scheduled for deletion" >&2; exit 1; fi
jq -e '.recipe_conflicts_spartan_0_1_9_41.polymorph_selector == true and .recipe_conflicts_spartan_0_1_9_41.ae2_selector_integration == true and .recipe_conflicts_spartan_0_1_9_41.refined_storage_selector_integration == true and .recipe_conflicts_spartan_0_1_9_41.spartan_weaponry == true and .recipe_conflicts_spartan_0_1_9_41.client_update_required == true and .recipe_conflicts_spartan_0_1_9_41.world_data_touched == false' "$validation" >/dev/null

python3 "$repo_dir/scripts/validate-bee-integrations.py"


# 0.1.9-39 ATM10-inspired semantic major progression checks
jq -e '.atm10_major_progression_0_1_9_38.reference_pack == "AllTheMods/ATM-10" and .atm10_major_progression_0_1_9_38.reference_commit == "ab6f65e07b88423cdae1724864ba42a573ba758a" and .atm10_major_progression_0_1_9_38.existing_chapters_rebuilt == 7 and .atm10_major_progression_0_1_9_38.new_chapters_added == 2 and .atm10_major_progression_0_1_9_38.final_chapters == 28 and .atm10_major_progression_0_1_9_38.preserved_existing_quest_ids == 91 and .atm10_major_progression_0_1_9_38.reward_tables_final == 145 and .atm10_major_progression_0_1_9_38.fortune_wheels_touched == 9 and .atm10_major_progression_0_1_9_38.client_server_quest_files_identical == true' "$validation" >/dev/null
for chapter in hostile_neural_networks draconic_evolution; do
  test -f "$client_quests/chapters/$chapter.snbt" || { echo "Missing new 0.1.9-39 chapter: $chapter" >&2; exit 1; }
done
for chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage; do
  if rg -F 'AA35 deep progression milestone' "$client_quests/chapters/$chapter.snbt" >/dev/null; then
    echo "Generic AA35 filler remains in rebuilt major chapter: $chapter" >&2
    exit 1
  fi
done
for chapter in ae2 mekanism powah ars_nouveau irons_spells ender_io refined_storage hostile_neural_networks draconic_evolution; do
  for tier in 1 2 3 4; do
    test -f "$client_quests/reward_tables/modroll_${chapter}_tier_${tier}.snbt" || { echo "Missing hand-curated tier table: $chapter tier $tier" >&2; exit 1; }
  done
  test -f "$client_quests/reward_tables/wheel_${chapter}.snbt" || { echo "Missing Fortune Wheel: $chapter" >&2; exit 1; }
done
diff -qr "$client_quests" "$server_quests" >/dev/null || { echo "Client/server quest trees differ after 0.1.9-39" >&2; exit 1; }

python3 "$repo_dir/scripts/validate-stone-generators.py"

# 0.1.9-44: FTB Quests must never contain directed dependency cycles.
python3 "$repo_dir/scripts/validate-quest-graph.py"


# 0.1.9-46 Vampirism addon expansion checks
test "$(jq '[.files[] | select(.projectID == 228756 or .fileID == 4614852)] | length' "$manifest")" = "0" || { echo "Iron Chests remains in client manifest" >&2; exit 1; }
grep -Fxq 'ironchest-1.20.1-14.4.4.jar' "$repo_dir/server/_crafty/remove-mods.txt" || { echo "Iron Chests stale-jar cleanup missing" >&2; exit 1; }
test "$(jq '[.files[] | select(.projectID == 1350048 and .fileID == 8525675)] | length' "$manifest")" = "1" || { echo "Missing 0.1.9-46 client pin: Vampirism Iron's Spells Compatibility" >&2; exit 1; }
test "$(awk -F '\t' '$1 == "8525675" && $2 == "vampire_spells_addon-forge-1.20.1-0.0.9.jar" && $4 == "vampirism-irons-spells-compatibility" && $6 == "1350048" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-46 server pin: Vampirism Iron's Spells Compatibility" >&2; exit 1; }
test "$(jq '[.files[] | select(.projectID == 939092 and .fileID == 8200186)] | length' "$manifest")" = "1" || { echo "Missing 0.1.9-46 client pin: Vampire's Delight" >&2; exit 1; }
test "$(awk -F '\t' '$1 == "8200186" && $2 == "VampiresDelight-1.20.1-0.1.13c.jar" && $4 == "vampires-delight" && $6 == "939092" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-46 server pin: Vampire's Delight" >&2; exit 1; }
test "$(jq '[.files[] | select(.projectID == 906331 and .fileID == 6125994)] | length' "$manifest")" = "1" || { echo "Missing 0.1.9-46 client pin: Vampiric Ageing" >&2; exit 1; }
test "$(awk -F '\t' '$1 == "6125994" && $2 == "vampiricageing-1.20.1-1.3.26.jar" && $4 == "vampiric-ageing-a-vampirism-addon" && $6 == "906331" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-46 server pin: Vampiric Ageing" >&2; exit 1; }
test "$(jq '[.files[] | select(.projectID == 417851 and .fileID == 6722563)] | length' "$manifest")" = "1" || { echo "Missing 0.1.9-46 client pin: Werewolves - Become a Beast!" >&2; exit 1; }
test "$(awk -F '\t' '$1 == "6722563" && $2 == "Werewolves-1.20.1-2.0.2.7.jar" && $4 == "werewolves-become-a-beast" && $6 == "417851" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-46 server pin: Werewolves - Become a Beast!" >&2; exit 1; }
test "$(jq '[.files[] | select(.projectID == 1238539 and .fileID == 6775688)] | length' "$manifest")" = "1" || { echo "Missing 0.1.9-46 client pin: Create Vampirism" >&2; exit 1; }
test "$(awk -F '\t' '$1 == "6775688" && $2 == "create_vampirism-1.20.1_0.5.0.jar" && $4 == "create-vampirism" && $6 == "1238539" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-46 server pin: Create Vampirism" >&2; exit 1; }
test "$(jq '[.files[] | select(.projectID == 1565325 and .fileID == 8219863)] | length' "$manifest")" = "1" || { echo "Missing 0.1.9-46 client pin: Vampirism Umbrella Curios Support" >&2; exit 1; }
test "$(awk -F '\t' '$1 == "8219863" && $2 == "RIP_vampirismcurioscompat-1.0.0.jar" && $4 == "vampirism-umbrella-curios-support" && $6 == "1565325" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing 0.1.9-46 server pin: Vampirism Umbrella Curios Support" >&2; exit 1; }
if rg -F $'	iron-chests	' "$repo_dir/server/_crafty/server-mods.tsv" >/dev/null; then echo "Iron Chests remains in server mod list" >&2; exit 1; fi
jq -e '.vampirism_expansion_0_1_9_46.addons_added == 7 and .vampirism_expansion_0_1_9_46.iron_chests_removed == true and .vampirism_expansion_0_1_9_46.quest_progression_changed == false and .vampirism_expansion_0_1_9_46.create_vampirism_blood_feeding_enabled == false and .vampirism_expansion_0_1_9_46.world_data_touched == false' "$validation" >/dev/null
test "$(jq '.files | length' "$manifest")" = "296" || { echo "Expected 296 client manifest entries" >&2; exit 1; }
test "$(awk -F '\t' '!/^#/ && NF {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "276" || { echo "Expected 276 server mod rows" >&2; exit 1; }

# 0.1.9-47 Vampirism Tinker dependency checks

# 0.1.9-48 Vampirism Tinker dedicated-server fix
test "$(jq '[.files[] | select(.projectID == 1314650 or .fileID == 6814093 or .projectID == 1218668 or .fileID == 6862342)] | length' "$manifest")" = "0" || { echo "Dedicated-server-incompatible Vampirism Tinker or its orphan dependency remains in client manifest" >&2; exit 1; }
if rg -F $'	vampirism-tinker	|	tcondiadema	' "$repo_dir/server/_crafty/server-mods.tsv" >/dev/null; then echo "Vampirism Tinker or Tinker Domain remains in server mod list" >&2; exit 1; fi
grep -Fxq 'vampirismtinker-1.6.jar' "$repo_dir/server/_crafty/remove-mods.txt" || { echo "Vampirism Tinker stale-jar cleanup missing" >&2; exit 1; }
grep -Fxq 'Tinkers Domain-1.9fix.jar' "$repo_dir/server/_crafty/remove-mods.txt" || { echo "Tinker Domain stale-jar cleanup missing" >&2; exit 1; }
jq -e '.vampirism_tinker_dedicated_server_fix_0_1_9_48.vampirism_tinker_removed == true and .vampirism_tinker_dedicated_server_fix_0_1_9_48.tinkers_domain_removed == true and .vampirism_tinker_dedicated_server_fix_0_1_9_48.active_vampirism_addons_from_0_1_9_46 == 6 and .vampirism_tinker_dedicated_server_fix_0_1_9_48.quest_progression_changed == false and .vampirism_tinker_dedicated_server_fix_0_1_9_48.world_data_touched == false' "$validation" >/dev/null

# 0.1.9-49 performance mod cleanup
test "$(jq '[.files[] | select(.projectID == 250498 or .fileID == 7815705 or .projectID == 457252 or .fileID == 4779746)] | length' "$manifest")" = "0" || { echo "Removed performance-heavy mods remain in client manifest" >&2; exit 1; }
if awk -F '\t' '$1=="7815705" || $1=="4779746" || $6=="250498" || $6=="457252" {bad=1} END{exit bad?0:1}' "$repo_dir/server/_crafty/server-mods.tsv"; then echo "Mowzie's Mobs or Untamed Wilds remains in server mod list" >&2; exit 1; fi
grep -Fxq 'mowziesmobs-1.8.2.jar' "$repo_dir/server/_crafty/remove-mods.txt" || { echo "Mowzie's Mobs stale-jar cleanup missing" >&2; exit 1; }
grep -Fxq 'untamedwilds-1.20.1-4.0.4.jar' "$repo_dir/server/_crafty/remove-mods.txt" || { echo "Untamed Wilds stale-jar cleanup missing" >&2; exit 1; }
jq -e '.performance_mod_cleanup_0_1_9_49.mowzies_mobs_removed == true and .performance_mod_cleanup_0_1_9_49.untamed_wilds_removed == true and .performance_mod_cleanup_0_1_9_49.quest_progression_changed == false and .performance_mod_cleanup_0_1_9_49.world_data_touched == false' "$validation" >/dev/null

# 0.1.9-52 Mobtimizations + CoroUtil checks
test "$(jq '[.files[] | select(.projectID == 974401 and .fileID == 7594372)] | length' "$manifest")" = "1" || { echo "Missing Mobtimizations client pin" >&2; exit 1; }
test "$(jq '[.files[] | select(.projectID == 237749 and .fileID == 5096038)] | length' "$manifest")" = "1" || { echo "Missing CoroUtil client pin" >&2; exit 1; }
test "$(awk -F '	' '$1 == "7594372" && $2 == "mobtimizations-forge-1.20.1-1.0.1.jar" && $4 == "mobtimizations" && $6 == "974401" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing Mobtimizations server pin" >&2; exit 1; }
test "$(awk -F '	' '$1 == "5096038" && $2 == "coroutil-forge-1.20.1-1.3.7.jar" && $4 == "coroutil" && $6 == "237749" {n++} END {print n+0}' "$repo_dir/server/_crafty/server-mods.tsv")" = "1" || { echo "Missing CoroUtil server pin" >&2; exit 1; }
jq -e '.mobtimizations_0_1_9_52.enabled == true and .mobtimizations_0_1_9_52.world_data_touched == false and .mobtimizations_0_1_9_52.runtime_spark_retest_required == true' "$validation" >/dev/null

# 0.1.9-53 AI population/performance config checks
for base in "$repo_dir/client/overrides/config" "$repo_dir/server/config"; do
  test -f "$base/servercore/config.yml"
  test -f "$base/servercore/optimizations.yml"
  test -f "$base/mobtimizations/features.toml"
  test -f "$base/mobtimizations/features-customization.toml"
  grep -A2 "category: 'MONSTER'" "$base/servercore/config.yml" | grep -q 'mobcap: 30'
  grep -A2 "category: 'VAMPIRISM_VAMPIRE'" "$base/servercore/config.yml" | grep -q 'mobcap: 10'
  grep -q 'target-mspt: 30' "$base/servercore/config.yml"
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

# 0.1.9-54 Powah Thermo compatibility checks
client_powah="$repo_dir/client/overrides/kubejs/startup_scripts/amber_arcana_powah_thermo_compat.js"
server_powah="$repo_dir/server/kubejs/startup_scripts/amber_arcana_powah_thermo_compat.js"
client_powah_jei="$repo_dir/client/overrides/kubejs/client_scripts/amber_arcana_powah_jei_compat.js"
test -f "$client_powah" && test -f "$server_powah" && test -f "$client_powah_jei" || { echo "Powah compatibility scripts missing" >&2; exit 1; }
cmp -s "$client_powah" "$server_powah" || { echo "Client/server Powah startup scripts differ" >&2; exit 1; }
grep -Fq "StartupEvents.postInit" "$client_powah" || { echo "Powah compatibility is not post-init" >&2; exit 1; }
grep -Fq "create_central_kitchen', 'dragon_breath" "$client_powah" || { echo "Central Kitchen Dragon Breath coolant ID missing" >&2; exit 1; }
grep -Fq "tconstruct', 'blazing_blood_fluid" "$client_powah" || { echo "Blazing Blood block heat-source ID missing" >&2; exit 1; }
grep -Fq "registerCoolant(dragonBreathId, -20)" "$client_powah" || { echo "Dragon Breath -20 coolant value missing" >&2; exit 1; }
grep -Fq "registerHeatSource(blazingBloodBlockId, 3500)" "$client_powah" || { echo "Blazing Blood 3500 heat value missing" >&2; exit 1; }
grep -Fq "HeatSourceCategory\$Recipe" "$client_powah_jei" || { echo "Safe Powah JEI recipe injection missing" >&2; exit 1; }
grep -Fq "tconstruct', 'blazing_blood" "$client_powah_jei" || { echo "Blazing Blood JEI fluid ID missing" >&2; exit 1; }
jq -e '.powah_thermo_compat_0_1_9_54.enabled == true and .powah_thermo_compat_0_1_9_54.coolant_value == -20 and .powah_thermo_compat_0_1_9_54.heat_value == 3500 and .powah_thermo_compat_0_1_9_54.client_jei_direct_recipe_injection == true and .powah_thermo_compat_0_1_9_54.world_data_touched == false' "$validation" >/dev/null

test "$(unzip -Z1 "$update_overlay" | grep -Fxc 'kubejs/startup_scripts/amber_arcana_powah_thermo_compat.js')" = "1" || { echo "Crafty update overlay missing Powah startup compatibility" >&2; exit 1; }
test "$(unzip -Z1 "$repo_dir/dist/Amber-and-Arcana-${version}-Client.zip" | grep -Fxc 'overrides/kubejs/startup_scripts/amber_arcana_powah_thermo_compat.js')" = "1" || { echo "Client ZIP missing Powah startup compatibility" >&2; exit 1; }
test "$(unzip -Z1 "$repo_dir/dist/Amber-and-Arcana-${version}-Client.zip" | grep -Fxc 'overrides/kubejs/client_scripts/amber_arcana_powah_jei_compat.js')" = "1" || { echo "Client ZIP missing Powah JEI compatibility" >&2; exit 1; }
test "$(unzip -Z1 "$repo_dir/dist/Amber-and-Arcana-${version}-Server.zip" | grep -Fxc 'kubejs/startup_scripts/amber_arcana_powah_thermo_compat.js')" = "1" || { echo "Server ZIP missing Powah startup compatibility" >&2; exit 1; }


# 0.1.9-55 chunk-load performance checks
client_sc="$repo_dir/client/overrides/config/servercore/config.yml"
server_sc="$repo_dir/server/config/servercore/config.yml"
cmp -s "$client_sc" "$server_sc" || { echo "Client/server ServerCore configs differ" >&2; exit 1; }
grep -Fq 'target-mspt: 30' "$server_sc" || { echo "30 MSPT target missing" >&2; exit 1; }
test "$(grep -c 'min: 3' "$server_sc")" -ge 2 || { echo "Dynamic chunk/simulation minimums missing" >&2; exit 1; }
grep -Fq 'autosave-interval-seconds: 600' "$server_sc" || { echo "Autosave tuning missing" >&2; exit 1; }
jq -e '.chunk_load_performance_0_1_9_55.enabled == true and .chunk_load_performance_0_1_9_55.more_hitboxes_patch_preserved == true and .chunk_load_performance_0_1_9_55.mobcaps_changed == false and .chunk_load_performance_0_1_9_55.world_data_touched == false' "$validation" >/dev/null


# 0.1.9-56 startup data repair checks
client_data="$repo_dir/client/overrides/kubejs/data"
server_data="$repo_dir/server/kubejs/data"
diff -qr "$client_data" "$server_data" >/dev/null || { echo "Client/server KubeJS data differ" >&2; exit 1; }
test "$(find "$server_data" -type f -path '*/recipes/*.json' -exec grep -l 'forge:false' {} + | wc -l)" -ge 14 || { echo "Malformed recipe overrides missing" >&2; exit 1; }
test "$(find "$server_data" -type f -path '*/advancements/*.json' -exec grep -l 'minecraft:impossible' {} + | wc -l)" -ge 4 || { echo "Invalid advancement overrides missing" >&2; exit 1; }
jq -e '.startup_data_repairs_0_1_9_56.enabled == true and .startup_data_repairs_0_1_9_56.disabled_malformed_recipes == 14 and .startup_data_repairs_0_1_9_56.replaced_invalid_advancements == 4 and .startup_data_repairs_0_1_9_56.world_data_touched == false' "$validation" >/dev/null
