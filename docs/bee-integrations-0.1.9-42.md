# Bee integration repair — 0.1.9-42

This is an actual recipe/data update for Minecraft 1.20.1 Forge, not only a quest update.

## Findings

- The installed Just Dire Things Forge backport 1.1.7 uses mod ID `justdirethings`. Its material and goo IDs were checked against the pinned JAR.
- Productive Bees 1.20.1-12.6.0 contains no Just Dire Things bee definitions or recipes. Restarting or deleting a config cannot create this missing integration.
- Productive Bees loads bee definitions through its resource reload listener and checks loaded mod IDs. The world creation date does not lock the available integrations.
- The same Productive Bees JAR already contains Draconium, Awakened and Chaos definitions, fusion recipes, hive production and centrifuge outputs, conditional on `draconicevolution`. Their ingredient IDs/tags and fusion serializer were checked against Draconic Evolution 3.1.2.621. These use Fusion Crafting, not ordinary breeding.
- The existing full update overlay omitted `kubejs/data`. It now includes data/assets and current release metadata. Quest-only overlays remain quest-only and cannot install the bee repair.
- Other mods added in 0.1.9-36 and 0.1.9-41 (Mining Gadgets, Iron Jetpacks, Mekanism Lasers, Hostile Neural Networks, Otter Taming, Polymorph integrations and Spartan Weaponry) have no dedicated native integration species in Productive Bees 12.6.0. Existing Mekanism bees remain available.

## Added resource bees

| Bee | Obtain | Pollinate | Centrifuge output |
| --- | --- | --- | --- |
| Ferricore | Iron Bee + tier 1 Goo Block | Ferricore Block | Raw Ferricore, 80% |
| Blazegold | Gold Bee + tier 2 Goo Block | Blazegold Block | Raw Blazegold, 60% |
| Celestigem | Diamond Bee + tier 3 Goo Block | Celestigem Block | Celestigem, 40% |
| Eclipse Alloy | Netherite Bee + tier 4 Goo Block | Eclipse Alloy Block | Raw Eclipse Alloy, 20% |
| Time Crystal | Tiered spawn-egg crafting recipe in JEI | Time Crystal Block | Time Crystal, 10%, plus 25 mB Time Fluid |

Every comb also provides wax. Conversions use Productive Bees' native bee-conversion mechanic; right-click the source bee with the goo block. Higher-tier bees cannot self-breed. The Time Crystal egg retains gates requiring Celestigem, Eclipse Alloy, Sculk and Draconic bee eggs, Time Crystal Blocks and a Time Fluid Bucket. This is the Just Dire Things resource-bee family (Direwolf20's mod), not a separate species literally called `direwolf`.

New definitions use built-in tinted bee renderers, avoiding dependencies on newer-version textures or renderer code. Recipes use Forge NBT ingredients, 1.20.1 directory names, integer percent chances and the 12.6.0 fluid-output schema. Nine additive quest nodes track exact honeycomb NBT. Historical IDs, the existing finale and its rewards are preserved.

## Apply to an existing Crafty server

Stop only Amber & Arcana in Crafty; keep the Crafty-4 container running. Run `scripts/update-crafty-0.1.9-42.py` inside the container as root with `--ref <published commit SHA>`. It verifies the archive SHA-256, refuses an active Java process for this server, rejects paths outside the overlay allowlist, and backs up replaced files. It does not overwrite world/player data or restart the server. Avoid starting the server while it runs.

After it completes, start through `AmberArcana-Crafty-Launcher.jar` so all pinned mods are installed, then reconnect using the 0.1.9-42 client. No world reset or bee-config deletion is required. For remaining missing native species, provide `logs/latest.log` after this restart; the live server cannot be inspected remotely from this build.

## Compatibility limits

[Cobblegen Galore](https://www.curseforge.com/minecraft/mc-mods/cobblegen-galore) supports NeoForge 1.21.1/26.1.2; [Tiny Soldiers](https://www.curseforge.com/minecraft/mc-mods/tiny-soldiers) supports Fabric/NeoForge starting at 1.21.1. Neither is added to this Forge 1.20.1 pack. No unrelated replacement mods are silently installed.

## Verification

The build validates source/archive parity, typed bee inputs/outputs, preserved quest IDs, matched mod manifests, pinned More Hitboxes and JEI, and safe update contents. Updater tests cover a stopped fixture server, active-process refusal and archive path rejection. This is static validation, not a multiplayer runtime test.

Reference schemas: Productive Bees source commit `2190d6b4c0f4a35acc26415759c3be731d1eac22` (the installed 12.6.0); modern Just Dire Things integration inspected at `3c818315d67abc16801626ce292bb207a7383f06`. Compatibility JSON here is authored for this pack's Forge schema. No new mod JARs are included.
