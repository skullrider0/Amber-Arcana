# AA-006 — Quest repair candidate on 0.1.9-20

The user reports recipes and tags fixed and has moved the active priority to quests.
This first pass repairs the two previously polished chapters: Welcome to Amber & Arcana
and Create Engineering (nine quests). The other 23 chapters remain future work.

## Cause and repair

All twelve existing item rewards stored `{count: 1, id: ...}` inside `item`.
FTB Quests 2001.4.14 `NBTUtils.read` passes compounds to `MissingItem.readItem`,
which reads uppercase `Count`. The old compounds therefore deserialize as empty stacks.
New reward-table entries use the supported string item ID plus a separate reward count.
Random rewards use numeric SNBT `table_id` longs and tables have `loot_size: 1`.

Source checked at FTB Quests tag v2001.4.14, commit
58d6514a5631abb98ea4fbb6074559834ed9286d:
- https://github.com/FTBTeam/FTB-Quests/blob/v2001.4.14/common/src/main/java/dev/ftb/mods/ftbquests/util/NBTUtils.java
- https://github.com/FTBTeam/FTB-Quests/blob/v2001.4.14/common/src/main/java/dev/ftb/mods/ftbquests/item/MissingItem.java
- https://github.com/FTBTeam/FTB-Quests/blob/v2001.4.14/common/src/main/java/dev/ftb/mods/ftbquests/quest/reward/RandomReward.java
- https://github.com/FTBTeam/FTB-Quests/blob/v2001.4.14/common/src/main/java/dev/ftb/mods/ftbquests/quest/loot/RewardTable.java

## Behavior

All nine quests now require inventory items, without consuming them. Build instructions
remain guidance: inventory possession cannot prove a claimed chunk, working machine,
or completed train journey. The quest text explicitly explains this limit.
All existing chapter, quest, task and reward IDs, dependency edges and XP rewards are
preserved. New task IDs are added only where a quest needs multiple items.
Previously claimed rewards are not reissued. Existing completed progress is not reset;
this patch does not compensate for rewards previously claimed as air.

Starter quests each grant two independent bundles (materials and provisions).
Create quests grant one bundle from a tier-appropriate supply table. Every table has
five entries weighted 35/30/20/10/5 or 35/25/20/15/5, totaling 100. No zero-weight
entry, air, empty reward, progression machine, or Eternal Steak is included.

## Item requirements

| Quest | Required inventory items (kept) |
| --- | --- |
| Make a home | 1 × `minecraft:crafting_table`, 1 × `minecraft:furnace` |
| Claim your workshop | 2 × `minecraft:chest` |
| Tools for the journey | 1 × `sophisticatedbackpacks:backpack`, 1 × `waystones:waystone` |
| First rotation | 1 × `create:iron_sheet`, 1 × `create:goggles` |
| A processing line | 64 × `create:iron_sheet`, 1 × `create:mechanical_mixer`, 1 × `create:encased_fan` |
| Precision mechanisms | 4 × `create:precision_mechanism` |
| Steam under control | 1 × `create:steam_engine`, 1 × `create:mechanical_pump`, 1 × `create:clutch` |
| Rails and schedules | 2 × `create:track_station`, 1 × `create:schedule` |
| A reliable factory | 2 × `create:smart_chute`, 1 × `create:stockpile_switch` |

## Reward tables

### Create workshop supplies

| Item | Quantity | Chance per roll |
| --- | ---: | ---: |
| `create:andesite_alloy` | Int(8) | Int(35)% |
| `create:shaft` | Int(8) | Int(25)% |
| `create:cogwheel` | Int(8) | Int(20)% |
| `create:andesite_casing` | Int(4) | Int(15)% |
| `create:large_cogwheel` | Int(4) | Int(5)% |

### Create factory and railway supplies

| Item | Quantity | Chance per roll |
| --- | ---: | ---: |
| `create:track` | Int(16) | Int(35)% |
| `create:fluid_pipe` | Int(12) | Int(25)% |
| `create:brass_funnel` | Int(4) | Int(20)% |
| `create:brass_tunnel` | Int(2) | Int(15)% |
| `create:sturdy_sheet` | Int(4) | Int(5)% |

### Create precision supplies

| Item | Quantity | Chance per roll |
| --- | ---: | ---: |
| `create:brass_ingot` | Int(8) | Int(35)% |
| `create:electron_tube` | Int(4) | Int(25)% |
| `create:brass_casing` | Int(4) | Int(20)% |
| `create:brass_funnel` | Int(2) | Int(15)% |
| `create:sturdy_sheet` | Int(2) | Int(5)% |

### Starter workshop materials

| Item | Quantity | Chance per roll |
| --- | ---: | ---: |
| `minecraft:iron_ingot` | Int(8) | Int(35)% |
| `minecraft:copper_ingot` | Int(12) | Int(30)% |
| `minecraft:coal` | Int(12) | Int(20)% |
| `minecraft:redstone` | Int(8) | Int(10)% |
| `minecraft:gold_ingot` | Int(4) | Int(5)% |

### Starter provisions

| Item | Quantity | Chance per roll |
| --- | ---: | ---: |
| `minecraft:bread` | Int(8) | Int(35)% |
| `minecraft:torch` | Int(16) | Int(30)% |
| `minecraft:cooked_salmon` | Int(8) | Int(20)% |
| `minecraft:golden_carrot` | Int(4) | Int(10)% |
| `minecraft:golden_apple` | Int(1) | Int(5)% |

## Validation and remaining runtime test

- `python3 scripts/validate-quests.py`: PASS. All 106 quests parse; five tables and
  twelve references resolve; IDs are unique; dependency graph is acyclic; no invalid
  item stacks; all quest files are identical between client and server.
- All 41 original object IDs in the two chapters are retained (16 Welcome, 25 Create).
- Referenced modded items have item models in the exact SHA512-verified Create 6.0.8,
  Sophisticated Backpacks 3.24.9.1391, and Waystones 14.1.21 jars. This is asset evidence,
  not a live registry or craftability test.
- `bash scripts/build.sh` and `bash scripts/validate.sh`: PASS on the candidate.
- Recipe/tag data and mod lists are unchanged by the quest edit.
- Clean client/server runtime test: NOT RUN. No live Minecraft client or user server
  is connected here. Do not mark this chapter's in-game acceptance gate complete yet.

Test on a backed-up world copy: start the matching client/server, confirm the log
loads five reward tables, use an uncompleted test team, obtain each listed item,
confirm items remain, claim each bundle and XP once, reconnect, and confirm no reclaims.
Check that each later quest stays locked until its prerequisite completes. For earlier
players, verify previous claims and progress remain intact. Do not globally reset quests.

## Applying the quest-only patch

1. Stop the server and close Minecraft before replacing quest files.
2. Back up `config/ftbquests/quests` and the world's quest/team progress.
3. Extract the ZIP into the Crafty server root (the folder containing `config`).
   Apply the same ZIP to each client's Minecraft instance folder containing `config`.
   This is an overlay, not a CurseForge modpack import ZIP.
4. Merge/overwrite the included files. Keep other chapters and all world/player files.
5. Restart the server and client, then run the checks above.

The patch contains only the two edited chapter files, five new reward tables and
installation notes. It does not replace recipes, tags, mods or world data.
