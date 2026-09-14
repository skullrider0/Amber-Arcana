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

## Static verification

- [ ] Run `bash scripts/validate.sh` against the latest main branch.
- [ ] Run `bash scripts/build.sh` in a clean checkout and compare generated checksums.
- [ ] Confirm every manifest project/file ID resolves.
- [ ] Confirm every declared server download resolves.
- [ ] Confirm no removed project IDs or mod IDs remain.
- [ ] Confirm no secrets, worlds, player data, or private addresses are tracked.

## Recipe/tag investigation

- [ ] Import the client ZIP into a fresh CurseForge profile.
- [ ] Import the server ZIP into a fresh Crafty 4 server.
- [ ] Capture client and server logs from the same attempt.
- [ ] Compare JAR names, mod IDs, versions, sides, and dependencies.
- [ ] Compare `config/`, `defaultconfigs/`, KubeJS, datapacks, recipes, and tags.
- [ ] Locate the first relevant recipe/tag error before cascading errors.
- [ ] Identify the actual source of the red-X/incompatible-server status.
- [ ] Test datapack reload.
- [ ] Test representative previously broken recipes through REI and crafting.
- [ ] Record findings under `docs/`.

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
