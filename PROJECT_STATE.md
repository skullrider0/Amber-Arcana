# Project State

## Active release

`0.1.9-14` is the active diagnostic release. It layers a targeted recipe/tag compatibility data pack over the 0.1.9-13 REI and content-cleanup baseline.

## Active work queue

| ID | Priority | Work | Exit condition |
| --- | --- | --- | --- |
| AA-001 | P0 | Clean client/server boot pair | Both reach ready state on Java 17 |
| AA-002 | P0 | Red-X/channel parity report | Exact mismatching mod/channel identified or warning cleared |
| AA-003 | P0 | Recipe/tag failure inventory | Each failure mapped to owner and missing registry/tag entry |
| AA-004 | P1 | REI and crafting smoke test | Search, usage, recipe transfer, and crafting pass |
| AA-005 | P1 | Existing-world copy test | Missing content is documented; world remains stable |
| AA-006 | P2 | Next quest line | One chapter completed and validated end-to-end |
| AA-007 | P2 | Performance baseline | Startup, heap, TPS/MSPT, and packet measurements recorded |

## Release history carried forward

- `0.1.9-5`: packet/session compatibility work.
- `0.1.9-6`: FTB Quests item-reward serialization repair.
- `0.1.9-11`: Every Compat removal and recipe cleanup.
- `0.1.9-12`: Create Engineering quest expansion.
- `0.1.9-13`: REI migration and requested content removals.
- `0.1.9-14`: 36 invalid recipe overrides and four tag repairs, pending a fresh runtime retest.
