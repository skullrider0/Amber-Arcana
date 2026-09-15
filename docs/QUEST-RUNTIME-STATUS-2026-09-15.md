# Quest runtime status — 2026-09-15

## Evidence received

An in-game FTB Quests editor screenshot from the running Amber & Arcana server shows the `Make a home` quest loading successfully.

Observed in the editor view:

- the quest title and description render;
- `[No Subtitle]` is visible in the editor;
- at least one reward slot resolves to `minecraft:air` instead of a usable reward.

## Repository mismatch

The repository copy at `config/ftbquests/quests/chapters/getting_started.snbt` still defines these `Make a home` rewards:

- 16 `minecraft:torch`;
- 8 `minecraft:bread`;
- 100 XP.

That does not match the live reward display in the screenshot. The live server quest file has therefore diverged from the repository copy.

## Release decision for 0.1.9-22

Do not overwrite the quest data while publishing the More Hitboxes performance patch. First capture the live server file:

`config/ftbquests/quests/chapters/getting_started.snbt`

Then compare it with the repository copy and make a targeted quest patch that:

1. preserves the live quest IDs and intentional edits;
2. replaces the `minecraft:air` reward with the intended item/reward type;
3. adds a subtitle only if the `[No Subtitle]` editor placeholder is actually unwanted in the live design;
4. copies the corrected quest file to both client and server sources so static parity validation remains valid.
