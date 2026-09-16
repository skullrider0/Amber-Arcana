#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parent / 'validate.sh'
text = path.read_text()

# The workflow's historical normalizer leaves the validator at the 0.1.9-29
# release state. The build step applies 0.1.9-30 immediately afterward, so move
# only the current-release gates forward while preserving historical metadata.
text = text.replace('0.1.9-29', '0.1.9-30')
text = text.replace(
    'test "$(find "$qroot/reward_tables" -maxdepth 1 -name \'*.snbt\' -type f | wc -l)" = "31" || { echo "Expected 31 live reward tables" >&2; exit 1; }',
    'test "$(find "$qroot/reward_tables" -maxdepth 1 -name \'*.snbt\' -type f | wc -l)" = "35" || { echo "Expected 35 live reward tables" >&2; exit 1; }',
)

for old, new in (
    ('Machines & Production', 'Machines and Production'),
    ('Storage & Networks', 'Storage and Networks'),
    ('Resources & Farming', 'Resources and Farming'),
    ('Magic & Rituals', 'Magic and Rituals'),
    ('Exploration & Creatures', 'Exploration and Creatures'),
    ('Building & Settlements', 'Building and Settlements'),
    ('Tools, Combat & Equipment', 'Tools, Combat and Equipment'),
    ('Collections & Endgame', 'Collections and Endgame'),
):
    text = text.replace(old, new)

old_loot = 'test "$(rg -n \'type: "loot"\' "$client_quests/chapters" | wc -l)" = "26" || { echo "Expected 26 finale loot rewards" >&2; exit 1; }'
# 0.1.9-30 deliberately adds loot rewards to most quests, so the historical
# exact finale-only count is no longer valid. Metadata checks below become the
# authoritative coverage gate.
text = text.replace(old_loot, '# 0.1.9-30 loot coverage is validated from release metadata below')

marker = '# 0.1.9-30 quest UX checks'
if marker in text:
    text = text.split(marker, 1)[0].rstrip() + '\n'

text += r'''

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

test "$(find "$client_quests/reward_tables" -maxdepth 1 -name 'depth_tier_*.snbt' -type f | wc -l)" = "4" || { echo "Expected four client depth-tier reward tables" >&2; exit 1; }
test "$(find "$server_quests/reward_tables" -maxdepth 1 -name 'depth_tier_*.snbt' -type f | wc -l)" = "4" || { echo "Expected four server depth-tier reward tables" >&2; exit 1; }
loot_count="$(rg -n 'type: "loot"' "$client_quests/chapters" | wc -l)"
covered="$(jq -r '.quest_ux_0_1_9_30.loot_covered_quests' "$validation")"
test "$loot_count" -ge "$covered" || { echo "Quest loot reward count is below recorded coverage" >&2; exit 1; }

quest_overlay="$repo_dir/dist/Amber-and-Arcana-${version}-Crafty-Quest-Overlay.zip"
test "$(unzip -Z1 "$quest_overlay" | grep -Fxc 'config/ftbquests/quests/reward_tables/depth_tier_4.snbt')" = "1" || { echo "Depth-tier tables missing from quest overlay" >&2; exit 1; }
'''

path.write_text(text)
