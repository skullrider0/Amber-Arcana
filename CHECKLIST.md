# Amber & Arcana Checklist

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


## Port and requested changes

- [x] Port project into `skullrider0/Amber-Arcana`.
- [x] Confirm Minecraft 1.20.1, Forge 47.4.10, and Java 17.
- [x] Preserve Just Dire Things.
- [x] Preserve DecoCraft.
- [x] Replace JEI with client-only REI 12.1.785.
- [x] Remove Polymorph because it hard-depends on JEI.
- [x] Remove Ad Astra.
- [x] Remove AmbientSounds.
- [x] Remove The Aether.
- [x] Create CurseForge client ZIP.
- [x] Create Crafty 4 server ZIP.
- [x] Add validation/build scripts and checksums.
- [x] Preserve the existing quest IDs and compatibility fixes.
- [x] Add workload guide and future-agent prompt.
- [x] Reproduce the remaining errors on a fresh 0.1.9-13 Crafty server.
- [x] Identify all 36 rejected recipe IDs and four broken tag files.
- [x] Add identical 0.1.9-14 client/server compatibility data.

## Static verification

- [x] Run `bash scripts/validate.sh` against the 0.1.9-14 source.
- [x] Run `bash scripts/build.sh` and generate new checksums.
- [ ] Confirm every manifest project/file ID resolves.
- [ ] Confirm every declared server download resolves.
- [ ] Confirm no removed project IDs or mod IDs remain.
- [ ] Confirm no secrets, worlds, player data, or private addresses are tracked.

## Recipe/tag investigation

- [ ] Import the client ZIP into a fresh CurseForge profile.
- [x] Import the 0.1.9-13 server ZIP into a fresh Crafty 4 server.
- [ ] Capture client and server logs from the same attempt.
- [ ] Compare JAR names, mod IDs, versions, sides, and dependencies.
- [ ] Compare `config/`, `defaultconfigs/`, KubeJS, datapacks, recipes, and tags.
- [x] Locate and enumerate the remaining recipe/tag errors after Every Compat removal.
- [ ] Identify the actual source of the red-X/incompatible-server status.
- [ ] Test datapack reload.
- [ ] Test representative previously broken recipes through REI and crafting.
- [x] Record findings under `docs/`.

## Runtime quality gates

- [ ] Client launches from a fresh import.
- [ ] Dedicated Crafty server launches from a fresh import.
- [ ] Client joins the server.
- [ ] No fatal registry or network mismatch.
- [ ] Recipe/tag errors are fixed or isolated with a documented reproducer.
- [ ] New world generates correctly.
- [ ] Backed-up existing-world copy loads.
- [ ] Core magic, exploration, building, creature, and progression loops work.
- [ ] Representative quests contain no missing item/task references.

## Next content milestone

- [ ] Define the next quest-line scope and acceptance criteria.
- [ ] Implement quests without masking unresolved runtime issues.
- [ ] Validate quest dependencies on both client and server.
- [ ] Update changelog, known issues, hashes, and release tag.
