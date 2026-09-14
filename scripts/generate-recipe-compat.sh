#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
client_root="$repo_dir/client/overrides/kubejs/data"
server_root="$repo_dir/server/kubejs/data"

broken_recipes=(
  alexsdelight:barbecue_on_a_stick
  cgs:ore_vein_type/lead
  create:crushing/compat/biomeswevegone/blue_nether_gold_ore
  create:crushing/compat/biomeswevegone/blue_nether_quartz_ore
  create:crushing/compat/biomeswevegone/brimstone_nether_gold_ore
  create:crushing/compat/biomeswevegone/brimstone_nether_quartz_ore
  create:crushing/compat/biomeswevegone/cryptic_redstone_ore
  create:milling/compat/biomeswevegone/compat/biomeswevegone/white_sage
  create:milling/compat/biomeswevegone/compat/biomeswevegone/winter_cyclamen
  create:milling/compat/biomeswevegone/lolipop_flower
  create:milling/compat/biomeswevegone/orchid
  create:milling/compat/biomeswevegone/purple_rose
  create:milling/compat/biomeswevegone/torch_ginger
  create:pressing/compat/biomeswevegone/lush_grass_path
  create_aquatic_ambitions:channeling/upgrade_aquatic/prismarine_coral
  create_aquatic_ambitions:channeling/upgrade_aquatic/prismarine_coral_block
  create_aquatic_ambitions:channeling/upgrade_aquatic/prismarine_coral_fan
  create_aquatic_ambitions:channeling/upgrade_aquatic/prismarine_coral_shower
  create_things_and_misc:acacia_sailcraft
  create_things_and_misc:canon_craft
  create_things_and_misc:chorus_sail_craft
  create_things_and_misc:copper_scaffolding_craft
  create_things_and_misc:jaboticaba_sail_craft
  create_things_and_misc:mangrove_sail_craft_backport
  create_things_and_misc:raboutan_sail_c_raft
  create_things_and_misc:schematic_chair
  forbidden_arcanus:aurum_chest_boat
  forbidden_arcanus:aurum_fence
  forbidden_arcanus:aurum_fence_gate
  forbidden_arcanus:corrupted_pixie
  forbidden_arcanus:edelwood_chest_boat
  forbidden_arcanus:edelwood_fence
  forbidden_arcanus:edelwood_fence_gate
  forbidden_arcanus:fungyss_fence
  forbidden_arcanus:fungyss_fence_gate
  rusticdelight:cooking/batter
)

write_disabled_recipe() {
  local root="$1" id="$2" namespace="${2%%:*}" path="${2#*:}"
  local destination="$root/$namespace/recipes/$path.json"
  mkdir -p "$(dirname "$destination")"
  printf '%s\n' '{' \
    '  "type": "minecraft:crafting_shapeless",' \
    '  "conditions": [{ "type": "forge:false" }],' \
    '  "ingredients": [{ "item": "minecraft:barrier" }],' \
    '  "result": { "item": "minecraft:barrier" }' \
    '}' > "$destination"
}

write_compat_tags() {
  local root="$1"
  mkdir -p \
    "$root/refinedstorage/tags/items/parts" \
    "$root/refinedstorage/tags/items/disks" \
    "$root/iwannaskate/tags/blocks" \
    "$root/justdirethings/tags/blocks"

  printf '%s\n' '{' '  "replace": true,' '  "values": [' \
    '    "#refinedstorage:parts/items/256k",' \
    '    "#refinedstorage:parts/items/1024k",' \
    '    "#refinedstorage:parts/items/4096k",' \
    '    "#refinedstorage:parts/items/16384k"' \
    '  ]' '}' > "$root/refinedstorage/tags/items/parts/items.json"

  printf '%s\n' '{' '  "replace": true,' '  "values": [' \
    '    "#refinedstorage:disks/items/256k",' \
    '    "#refinedstorage:disks/items/1024k",' \
    '    "#refinedstorage:disks/items/4096k",' \
    '    "#refinedstorage:disks/items/16384k"' \
    '  ]' '}' > "$root/refinedstorage/tags/items/disks/items.json"

  printf '%s\n' '{' '  "replace": true,' '  "values": [' \
    '    "#minecraft:wooden_stairs",' \
    '    "#minecraft:wooden_slabs",' \
    '    "#minecraft:planks",' \
    '    "#minecraft:stone_bricks",' \
    '    "#minecraft:stairs",' \
    '    "#minecraft:slabs",' \
    '    "#minecraft:ice",' \
    '    "minecraft:stone",' \
    '    "minecraft:blackstone",' \
    '    "minecraft:blackstone_slab",' \
    '    "minecraft:blackstone_stairs",' \
    '    "minecraft:calcite"' \
    '  ]' '}' > "$root/iwannaskate/tags/blocks/high_skate_quality.json"

  printf '%s\n' '{' '  "replace": true,' '  "values": [' \
    '    "minecraft:bedrock",' \
    '    "minecraft:end_portal_frame",' \
    '    "minecraft:end_portal",' \
    '    "minecraft:nether_portal",' \
    '    "#minecraft:portals"' \
    '  ]' '}' > "$root/justdirethings/tags/blocks/paradox_deny.json"
}

for root in "$client_root" "$server_root"; do
  for recipe in "${broken_recipes[@]}"; do
    write_disabled_recipe "$root" "$recipe"
  done
  write_compat_tags "$root"
done

echo "Generated ${#broken_recipes[@]} recipe overrides and 4 tag repairs for client and server"
