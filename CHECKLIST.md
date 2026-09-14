# Amber & Arcana Checklist

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
