# Goals

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
