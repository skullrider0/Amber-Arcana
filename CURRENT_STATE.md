# Current State

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


## Source of truth

- Release: Amber & Arcana 0.1.9-14
- Minecraft: 1.20.1
- Forge: 47.4.10
- Runtime: Java 17
- Deployment: CurseForge client and Crafty 4 dedicated server on Unraid

## Completed in this release

- Matching client/server overrides disable 36 recipe resources that Forge 47.4.10 rejected before registration.
- Reborn Storage item-tier parents, I Wanna Skate block tags, and the Just Dire Things paradox deny list are repaired.
- REI 12.1.785 is the client-only recipe viewer.
- JEI and server-side recipe viewers are absent.
- Polymorph is absent because the selected build hard-requires JEI.
- Ad Astra, AmbientSounds, and The Aether are removed.
- Every Compat remains removed; Moonlight/Selene remains because other mods require it.
- Just Dire Things and DecoCraft remain on both client and server.
- Client/server quest files are synchronized.
- 106 manually authored quests exist across 25 chapters.
- The Crafty launcher cleans known stale jars before server launch.

## Static validation result

- All 80 compatibility JSON files parse successfully and client/server data is identical.
- No duplicate CurseForge project IDs.
- No declared required dependency is missing from the client manifest.
- Client ZIP and server ZIP are readable.
- Quest SNBT passed the project’s structural checks.

## Not yet proven at runtime

- Clean CurseForge import and Minecraft launch.
- Clean 0.1.9-14 Crafty import and full Forge startup.
- In-game connection without the red-X compatibility indicator.
- Recipe/tag reload behavior after the 0.1.9-14 changes.
- REI display and representative crafting recipes.
- Existing-world safety after content removals.

The next evidence needed is a fresh 0.1.9-14 Crafty log, followed by a paired client log from the same connection session.
