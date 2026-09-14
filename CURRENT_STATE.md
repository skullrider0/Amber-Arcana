# Current State

## Source of truth

- Release: Amber & Arcana 0.1.9-13
- Minecraft: 1.20.1
- Forge: 47.4.10
- Runtime: Java 17
- Deployment: CurseForge client and Crafty 4 dedicated server on Unraid

## Completed in this release

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

- No duplicate CurseForge project IDs.
- No declared required dependency is missing from the client manifest.
- Client ZIP and server ZIP are readable.
- Quest SNBT passed the project’s structural checks.

## Not yet proven at runtime

- Clean CurseForge import and Minecraft launch.
- Clean Crafty import and full Forge startup.
- In-game connection without the red-X compatibility indicator.
- Recipe/tag reload behavior after the 0.1.9-13 changes.
- REI display and representative crafting recipes.
- Existing-world safety after content removals.

The next evidence needed is a paired client/server log from the same clean test session.
