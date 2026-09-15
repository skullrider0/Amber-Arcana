# Project State

## Session 2026-09-15 — AA-006 quest repair

- Priority: user confirms recipe/tag fixes and requests quest work next.
- Baseline: current main 0ddd809, pack 0.1.9-20; earlier 0.1.9-15 notes below are historical.
- Changes: repaired nine quests in Welcome/Create Engineering, replaced twelve broken
  item rewards with five themed weighted tables, and added non-consuming item tasks.
- Preserved: existing IDs, dependencies, XP, mod set and recipe/tag fixes.
- Validation: quest parser/reference checks and repository build/validation pass.
- Runtime evidence: pending paired client/server in-game testing; do not claim runtime completion.
- Result: reviewable quest-repair candidate; remaining 23 chapters are not finished.
- Exact next action: apply quest overlay and test item detection, random claims and progress persistence.
- Details: [quest requirements, reward odds, evidence and installation](docs/quest-repair-AA-006.md).

## Active update — 2026-09-15 / AA-004

Current diagnostic release: **0.1.9-15**, Minecraft 1.20.1 / Forge 47.4.10 / Java 17.
Client: 278 manifest entries. Server: 258 mod downloads.
**JEI 15.59.0.211 Forge (beta) replaces REI on client and server.** This supersedes
the earlier REI-only requirement below. Polymorph, Ad Astra, AmbientSounds,
The Aether, and Every Compat remain removed. Preserve Just Dire Things,
DecoCraft, the 36 recipe overrides, four tag repairs, and every quest ID.

Evidence: the supplied 0.1.9-14 client log fails twice in REI's
DefaultClientPlugin.registerDisplays at line 403 (null armor repair ingredient);
base Create and Mekanism do not appear in its native REI plugin list. The paired
server reaches ready state with the targeted previous recipe/tag errors absent.
JEI's pinned source uses an explicit vanilla-material list for anvil displays,
avoiding that REI scan. This is not proof of all machine recipes working.

- [x] Confirm REI display exception against the exact 12.1.785 source.
- [x] Pin JEI equally in the client manifest and server download list.
- [x] Preserve recipe/tag fixes and synchronize quest wording without changing IDs.
- [ ] Retest 0.1.9-15 imports, join, JEI plugin loading, and machine operations.
- [ ] Resolve remaining marine_snow JSON, loot-table, and NTGL errors separately.

Artifacts: `dist/Amber-and-Arcana-0.1.9-15-Client.zip` and
`dist/Amber-and-Arcana-0.1.9-15-Server.zip`. Use the current SHA256SUMS.txt.
See [diagnosis and validation](docs/jei-display-0.1.9-15.md) for the exact
remaining runtime checklist. Older baseline sections below are historical.


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
