# Amber & Arcana Workload Guide

## Priority order

1. Recover and inventory the authoritative alpha pack.
2. Establish a clean baseline on Minecraft 1.20.1, Forge 47.4.10, and Java 17.
3. Diff client and server mods by filename, mod ID, version, side, and dependency.
4. Diff `config/`, `defaultconfigs/`, `kubejs/`, datapacks, recipes, and tags.
5. Reproduce recipe/tag failures from fresh client and server logs.
6. Make requested mod changes in dependency-safe groups.
7. Validate single-player, dedicated-server startup, login, recipes, tags, quests, and world generation.
8. Export both CurseForge client and Crafty 4 server packages.
9. Publish an alpha release with hashes and known issues.
10. Resume quest-line work.

## Requested mod changes

- Keep: Just Dire Things, DecoCraft.
- Replace: JEI → Roughly Enough Items, subject to Forge 1.20.1 compatibility and required integrations.
- Remove: Ad Astra, AmbientSounds, The Aether.
- Remove only dependencies proven unused after those removals.
- Search KubeJS, quests, configs, recipes, tags, loot tables, advancements, and worldgen for removed mod IDs.

## Diagnostic method

Create normalized inventories for client and server containing:

- JAR filename and SHA-256
- mod ID, display name, and version
- client/server/both side classification
- required and optional dependencies
- duplicate mod IDs or multiple versions

Then compare:

- Forge registry and missing-mapping warnings
- datapack validation failures
- recipe serializer/type failures
- unresolved or empty tags
- KubeJS startup/server/data errors
- network-channel and incompatible-version warnings
- quest references to deleted items
- worldgen references to deleted dimensions or biomes

Treat the red-X/incompatible-version indicator as evidence to investigate, not proof of the root cause.

## Change-control rules

- One logical change per commit.
- Record removed files and why.
- Never delete configs blindly; archive or document migrations.
- Keep client-only mods out of the server package.
- Do not bundle third-party mod JARs in Git unless their licenses permit redistribution.
- Do not claim a fix until a new world and a representative existing-world copy both pass.
- Back up worlds before testing removals involving dimensions or world generation.

## Validation matrix

| Test | Client | Server | Required result |
| --- | --- | --- | --- |
| Clean launch | Yes | Yes | No fatal mod/dependency errors |
| Datapack reload | Yes | Yes | No recipe/tag validation failures |
| Join | Yes | Yes | No registry/network mismatch |
| Recipe browsing | Yes | N/A | Requested recipe viewer works |
| Crafting sample | Yes | Yes | Recipes agree on both sides |
| Quest sample | Yes | Yes | No missing item/task references |
| Existing world copy | Yes | Yes | Loads after explicit backup |
| New world | Yes | Yes | Normal generation and progression |

## Release artifacts

Each release should contain:

- CurseForge-compatible client export with a valid manifest
- Crafty 4 import package or documented server installation archive
- exact mod/version inventory
- configuration and script overrides
- changelog
- known issues
- SHA-256 checksums
