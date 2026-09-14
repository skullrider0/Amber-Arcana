# Amber & Arcana Workload Guide

## Current baseline

- Release: `0.1.9-14`
- Minecraft: 1.20.1
- Forge: 47.4.10
- Java: 17
- Client manifest entries: 278
- Server mod downloads: 257
- Manual quests: 106 across 25 chapters
- Distribution files:
  - `dist/Amber-and-Arcana-0.1.9-14-Client.zip`
  - `dist/Amber-and-Arcana-0.1.9-14-Server.zip`

The pack has already been ported. Release 0.1.9-14 adds the targeted recipe/tag compatibility layer over the 0.1.9-13 REI and requested content-removal baseline. Just Dire Things and DecoCraft remain required.

## Priority order

1. Preserve the current artifacts and their checksums.
2. Import the client ZIP into a clean CurseForge profile.
3. Import the server ZIP into a fresh Crafty 4 test server.
4. Capture fresh client and server logs from the same test run.
5. Reproduce the recipe/tag reload errors and red-X/incompatible-server indicator.
6. Diff client/server mod IDs, versions, configs, KubeJS data, tags, recipes, and network channels.
7. Fix one verified root cause per commit and repeat the test matrix.
8. Test a new world, then a backed-up copy of an existing world.
9. Publish a tested release with changelog, known issues, and hashes.
10. Continue the next quest-line milestone.

## Diagnostic method

Generate normalized client/server inventories containing JAR filename, SHA-256, mod ID, version, side, and dependencies. Then compare:

- duplicate or mismatched mod IDs and versions
- client-only mods accidentally shipped server-side
- Forge missing mappings and registry warnings
- datapack validation and recipe serializer failures
- unresolved or empty tags
- KubeJS startup/server/data errors
- network-channel and incompatible-version warnings
- quest references to removed content
- worldgen references to removed dimensions or biomes

Treat the red X as evidence to investigate, not proof of the root cause. Find the earliest relevant error before analyzing cascading errors.

## Change-control rules

- One logical change per commit.
- Update `CHECKLIST.md` with evidence, not assumptions.
- Keep Just Dire Things and DecoCraft.
- Keep JEI, Polymorph, Ad Astra, AmbientSounds, and The Aether removed unless a documented design decision reverses that.
- Do not commit access tokens, credentials, private server addresses, worlds, player data, or third-party mod JARs without redistribution permission.
- Keep client-only mods out of the Crafty package.
- Back up worlds before testing content or world-generation removals.
- Do not claim a fix until both a fresh import and an in-game join test pass.

## Validation matrix

| Test | Client | Server | Required result |
| --- | --- | --- | --- |
| Static validation | Yes | Yes | `scripts/validate.sh` passes |
| Clean import/launch | Yes | Yes | No fatal dependency errors |
| Datapack reload | Yes | Yes | No recipe/tag validation failures |
| Join | Yes | Yes | No registry/network mismatch |
| REI recipe browsing | Yes | N/A | Recipes display correctly |
| Representative crafting | Yes | Yes | Client and server agree |
| Quest sample | Yes | Yes | No missing item/task references |
| Existing-world copy | Yes | Yes | Loads after explicit backup |
| New world | Yes | Yes | Normal generation and progression |

## Release deliverables

- CurseForge-compatible client export with valid manifest
- Crafty 4 server import
- exact mod/version inventories
- configuration, KubeJS, and quest overrides
- changelog and known issues
- SHA-256 checksums
- recorded validation evidence under `docs/`
