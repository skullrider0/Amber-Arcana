# Goals

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


This is the live, short-form progress tracker. `GOAL-MAP.md` contains the full milestones and acceptance gates.

Updated: 2026-09-14

## Status legend

- `[x]` Completed and recorded.
- `[~]` In progress or awaiting runtime proof.
- `[ ]` Not started.
- `[!]` Blocked; the blocker must be written beside the goal.

## Completed

- `[x]` Create matching Amber & Arcana 0.1.9-14 client and Crafty server packages.
- `[x]` Replace JEI with client-only REI 12.1.785.
- `[x]` Remove Polymorph because it hard-requires JEI.
- `[x]` Remove Ad Astra, AmbientSounds, and The Aether as requested.
- `[x]` Preserve established quest IDs and synchronize client/server quest files.
- `[x]` Preserve Just Dire Things, DecoCraft, Moonlight/Selene, and earlier confirmed fixes.
- `[x]` Add static validation, reproducible build scripts, checksums, and GitHub Actions.
- `[x]` Add repository state, automation, contribution, onboarding, and goal documents.
- `[x]` Reproduce and classify the remaining 0.1.9-13 recipe/tag failures.
- `[x]` Build matching 0.1.9-14 compatibility overrides for all confirmed failures.

## Active

- `[~]` Retest recipe and item-tag loading on a fresh 0.1.9-14 Crafty server.
- `[~]` Identify why the multiplayer list shows a red X/incompatible version while joining still works.
- `[~]` Compare loaded client/server mod versions, network channels, registries, configs, and tags from the same session.
- `[~]` Reproduce or clear the login packet failure: `unable to fit 2202990 into 3`.

## Next

- `[ ]` Import the client ZIP into a clean CurseForge profile and launch on Java 17.
- `[ ]` Import the server ZIP into a clean Crafty 4 instance and reach the ready state.
- `[ ]` Save paired client/server logs from one clean connection attempt.
- `[ ]` Run `/reload`, REI lookup, recipe usage, and representative crafting tests.
- `[ ]` Test a new world and an existing-world copy after content removal.
- `[ ]` Complete the next quest line after the P0 compatibility work is stable.
- `[ ]` Record startup, heap, TPS/MSPT, and packet-size performance baselines.

## Update rule

Every completed item must include evidence in `PROJECT_STATE.md` or the related pull request. At the end of each work session, update this file's date and move goals between Completed, Active, and Next. Do not mark runtime work complete using static checks alone.
