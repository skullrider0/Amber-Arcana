# Amber & Arcana

Amber & Arcana is a Forge 1.20.1 modpack maintained as matching client and Crafty 4 dedicated-server packages.

## Direct downloads

[⬇️ Download Client 0.1.9-33](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-0.1.9-33-Client.zip) · [⬇️ Download Crafty Server 0.1.9-33](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-0.1.9-33-Server.zip) · [⬇️ Update an existing Crafty server](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-0.1.9-33-Crafty-Update-Overlay.zip)

## Current release

| Component | Version |
| --- | --- |
| Pack | 0.1.9-33 |
| Minecraft | 1.20.1 |
| Forge | 47.4.10 |
| Java | 17 |
| Client manifest entries | 276 + 1 local patched JAR |
| Server managed mod entries | 257 |
| Quests | 106 across 25 chapters |

Release 0.1.9-25 keeps JEI 15.20.0.106 on client and server and replaces stock More Hitboxes 1.9.2 with the Amber `1.9.2.1` performance patch required by Fossils and Archeology Revival 9.3.4.0.

The More Hitboxes patch changes only the expensive global `Level` entity-query behavior and multipart position update path. The official 1.9.2 client `MinecraftMixin` and Mixin refmap are preserved, which fixes the client crash seen in the first beta rebuild. The release validates the runtime-critical class/refmap fingerprints against the client-safe beta that successfully booted on Forge 47.4.10. The patched JAR is bundled directly instead of being declared as the stock CurseForge file, preventing duplicate `morehitboxes` mod IDs.

## Repository layout

- `client/` — CurseForge-compatible manifest and client overrides.
- `server/` — Crafty-ready server package source, launcher, config, quests, and validation records.
- `dist/` — ready-to-import client/server ZIPs, Crafty update overlays, and checksums.
- `overlays/spawn-balance/` — server-side spawn-balance patch source used for the combined quest + spawn overlay.
- `vendor/morehitboxes/` — the client-safe local More Hitboxes patch plus upstream MIT license and checksums.
- `patches/` — source-level More Hitboxes performance changes used to build the patched classes.
- `scripts/` — repeatable validation and packaging helpers.
- `docs/` — investigation notes and runtime findings.
- `GOAL-MAP.md`, `GOALS.md`, `WORKLOAD.md`, and `CHECKLIST.md` — project goals, queue, and validation gates.

## Install

### Client

Import `dist/Amber-and-Arcana-0.1.9-33-Client.zip` into CurseForge/Prism. Allocate about 10 GB RAM and use Java 17. The patched More Hitboxes JAR is included under the pack overrides, so do not add the stock More Hitboxes 1.9.2 JAR alongside it.

### Fresh Crafty server

Create a fresh server from `dist/Amber-and-Arcana-0.1.9-33-Server.zip`. The included launcher downloads normal managed server mods, accepts the bundled local More Hitboxes patch by exact SHA-512, removes the replaced stock 1.9.2 JAR, chooses Java 17, and starts Forge with the configured memory limits.

Back up an existing world before replacing a complete server package. Removed content mods can leave missing blocks, items, or dimensions in an existing world.

### Existing Crafty server

Stop the server and extract `dist/Amber-and-Arcana-0.1.9-33-Crafty-Update-Overlay.zip` into the existing server root with overwrite enabled. The overlay contains only:

- `_crafty/server-mods.tsv`
- `_crafty/remove-mods.txt`
- `mods/morehitboxes-forge-1.20.1-1.9.2.1.jar`
- `config/ftbquests/quests/` (the synchronized 0.1.9-25 quest book)

It does **not** contain or overwrite the world. In 0.1.9-25 the overlay also updates the FTB Quests configuration so existing Crafty servers receive the repaired quest book. On the next start Crafty removes the old stock `morehitboxes-forge-1.20.1-1.9.2.jar` and validates the patched JAR instead of redownloading the original.

The historical `Crafty-JEI-Overlay.zip` filename is also rebuilt as a compatibility alias to the same 0.1.9-25 update overlay.

## Quest runtime status — 2026-09-15

Release 0.1.9-33 makes Productive Bees rewards scale much more strongly with chapter depth. Its four tier rolls now contain 73 weighted entries across progressively stronger pools, Tier 3 gives three draws, Tier 4 gives four, and the Master Apiarist Wheel gives five. Later pools emphasize Productive Bees upgrades and machines instead of generic diamonds/emeralds. Omega Productivity (`productivebees:upgrade_productivity_4`) is a genuine jackpot at weight 0.30 in Tier 4 and 0.20 in the finale wheel.

Release 0.1.9-32 replaces the four global diamond/emerald-style depth pools with 104 chapter/mod-specific tier tables. 149 existing quest rolls now point at themed mod loot, and 26 finale wheels were rebuilt around modded items. Tier 2+ rolls can return multiple results; Tier 4 returns three results, but top machines remain low-weight jackpots. Powah's Nitro Thermo Generator, Nitro Reactor, Nitro Energy Cell, and Nitro Energizing Rod use sub-1 weights instead of becoming guaranteed endgame handouts.

Release 0.1.9-31 gives all 26 species-specific Productive Bees cage tasks explicit task labels such as `Capture Ashy Mining Bee`. The existing NBT filters were already species-specific; this release fixes the misleading generic `Bee Cage ()` tooltip without loosening or changing completion matching.

Release 0.1.9-30 repairs FTB quest-group labels so literal ampersands no longer trigger formatting errors, re-lays out all 26 quest chapters as compact dependency layers, and adds depth-tiered supply rolls to 175 of 228 quests (76.8%). Productive Bees species milestones now complete from exact NBT-matched evidence: 40 species use their typed honeycomb and 26 species use a filled Bee Cage when a comb is not appropriate. Historical quest/task IDs are preserved.

Release 0.1.9-29 reorganizes every quest chapter by gameplay mechanic instead of leaving the quest book mostly flat. The new chapter groups are Start Here, Machines & Production, Storage & Networks, Resources & Farming, Magic & Rituals, Exploration & Creatures, Building & Settlements, Tools/Combat & Equipment, and Collections & Endgame. Create, Mekanism, Ender IO, Powah and the other production chapters now live together; Productive Bees is placed in Resources & Farming, with an intentional ordering slot reserved for a future Mystical Agriculture chapter if that mod is added. Only chapter grouping/order metadata changes; quest/task/reward IDs and progression remain intact.

Release 0.1.9-28 rebuilds Create Engineering into a 41-quest progression tree pinned to Create 1.20.1-6.0.8. It preserves the six historical Create quest IDs while adding 35 machine/setup milestones and 72 explicit dependency edges. The tree walks from Andesite Alloy and first rotation through processing, fluids, contraptions, brass, precision mechanisms, crushing, package/stock logistics, steam, schematics, and scheduled railways. Concrete machines and components complete automatically from inventory; the final factory retains its Create Wheel of Fortune reward.

Release 0.1.9-27 adds a generated Productive Bees family-tree chapter pinned to Productive Bees 1.20.1-12.6.0. It contains 6 setup quests, 66 bee milestones, 14 branch completion nodes, and a Master Apiarist Wheel of Fortune finale. The generator screened 52 active breeding/conversion routes against the installed mod set and 93 active configurable bee definitions. Bee progression is rendered from real upstream breeding/conversion recipes; species milestones use manual confirmation while concrete equipment remains inventory-detected.

Release 0.1.9-26 adds a weighted Wheel of Fortune bonus to every chapter finale. The build generates 30 chapter-themed wheel tables from already-validated quest rewards and requirement items, including 35 modded-item entries. The wheel uses FTB Quests' native `loot` reward path, which requires a deliberate click, rolls server-side, and opens the full-screen reward reveal. Existing fixed rewards and all historical quest/task/reward IDs remain intact.

Release 0.1.9-25 finalizes the FTB Quests 1.20.1 runtime format. Simple item filters are now stored as canonical item-id strings instead of malformed compound stacks with a lowercase inner `count`. Concrete mod-item milestones in the core technology and magic chapters complete automatically; their historical checkmark task IDs remain present as optional verification tasks. Build, claim, habitat, routing, and other behavior-based objectives keep required manual confirmations.

Release 0.1.9-24 finishes the full 25-chapter / 106-quest progression pass. Every quest now has at least one automatically detected item requirement, a named manual completion check for build/behavior objectives, a subtitle, an icon, and a reward. Requirements do not consume the player's items.

All progression branches unlock after `Tools for the journey`. `The Mechanical City` additionally requires the Create Engineering and Settlement finales. The Endgame chapter requires the Create Engineering, Mekanism, Ritual Magic, Settlement, and Dinosaur Laboratory finales.

The stale Twilight Forest objective is removed because Twilight Forest is no longer in the pack; that quest ID is preserved and repurposed as a Nether expedition so existing dependency links remain stable.

### Quest-only Crafty update

For an existing Crafty server that already has the correct mods, use `dist/Amber-and-Arcana-0.1.9-33-Crafty-Quest-Overlay.zip`. Stop the server, back up the world, extract the ZIP into the server root with overwrite enabled, and start the server again. If you copy the quest files while the server is already running, run `/ftbquests reload` from the server console or with sufficient in-game permission. The quest-only overlay contains only `config/ftbquests/quests/`; it does not contain a world, mods, or Crafty launcher files.

## Validate and rebuild

Requirements: Bash, Java 17, `jq`, `zip`, `unzip`, `sha256sum`, `sha512sum`, and Python 3. Rebuild the launcher after Java-source edits with `bash scripts/build-launcher.sh`.

```bash
bash scripts/validate.sh
bash scripts/build.sh
```

Static validation checks client/server quest parity, recipe/tag compatibility data, JEI pins, the local More Hitboxes JAR and class fingerprints, Crafty mod-management state, archive layouts, and checksums. It does not replace an in-game multiplayer test or a Spark profile.

## More Hitboxes performance investigation

More Hitboxes 1.9.2 has no per-mod or per-entity whitelist and no valid `fossils_only` option. Its Forge `Level` entity-query hooks are global. The 1.9.2.1 patch reduces unnecessary work without removing multipart Fossils support, but a fresh 60-second Spark profile is still required to quantify the improvement under the same laggy workload.

Historical More Hitboxes note (0.1.9-21): stock 1.9.2 was temporarily restored only to satisfy the Fossils dependency; it is superseded by the client-safe 1.9.2.1 performance patch in 0.1.9-24.

## 0.1.9-17 content cleanup

- The Twilight Forest has been removed from the client and dedicated server package.
- Existing Crafty installs automatically delete `twilightforest-1.20.1-4.3.2508-universal.jar` during bootstrap.
- `Eternal Steak` (`artifacts:eternal_steak`) is removed from chest-generated loot with LootJS while Artifacts remains installed.
- Glitchy Mantle is not included in this Minecraft 1.20.1 pack, so no unrelated Relics/GlitchCore content was removed.


## Crafty JEI overlay

For an existing server, download `dist/Amber-and-Arcana-0.1.9-19-Crafty-JEI-Overlay.zip`, stop the server, and extract it into the Crafty server root (the folder containing `AmberArcana-Crafty-Launcher.jar`) with overwrite enabled. The overlay contains only `_crafty/server-mods.tsv`; on the next start the launcher downloads `jei-1.20.1-forge-15.20.0.106.jar` into `mods/`. It does not contain or overwrite the world.


## 0.1.9-34 short-chain reward progression

Compact quest chapters now use a compressed but much richer reward curve. Every quest in chapters with at most 10 quests receives a mod-specific tier roll, tiers 3/4 use 3/4 draws, and chapter finales use five draws. Reward tables are expanded with weighted quantity variants and rare deep-progression outcomes using only modded item IDs already validated by the preceding reward pass. Productive Bees and Create Engineering retain their dedicated deeper reward systems.


## 0.1.9-35 deep progression pass

The 24 formerly compact quest chapters now use real multi-step progression trees instead of three-to-ten broad milestones. Historical item-acquisition quests are preserved, but every local dependency is gated through required hands-on mechanics milestones such as commissioning machines, routing storage, automating production, performing rituals, exploring safely, or scaling a system. The pass adds 215 hands-on quests, raises the compact chapters to 339 total quests, keeps tiered mod-specific loot on 100% of those quests, moves each Wheel of Fortune reward to a true chapter-mastery finale, removes remaining fixed diamond/emerald rewards from the expanded chapters, and preserves the existing historical quest IDs. Create Engineering and Productive Bees retain their dedicated custom trees.


### 0.1.9-36 tech expansion
Adds Mining Gadgets, Iron Jetpacks, Mekanism Lasers, Draconic Evolution, Hostile Neural Networks, Infernos Otter Taming, and required missing libraries. The Crafty update overlay never contains world data.


### 0.1.9-37 compact quest layout
Quest chapters now use a denser ATM10-inspired visual scale with visible dependency chains while retaining Amber & Arcana's own progression, tier rolls, and Wheel of Fortune system.


### 0.1.9-38 major quest progression
ATM10-inspired milestone/branch audit for the major tech and magic chapters, plus new Hostile Neural Networks and Draconic Evolution progression. Amber & Arcana keeps its own tier-roll and Fortune Wheel reward system.


### 0.1.9-39 client QoL
Adds No Recipe Book Reborn 1.0.5 to the client manifest only. It is not installed on the dedicated server and does not touch world data.


### 0.1.9-40 CurseForge downloader
Crafty can again populate a missing server mods directory after CurseForge's July 2026 CDN authentication change. The launcher first uses an authenticated CDN when CURSEFORGE_API_KEY is configured, otherwise it uses validated CurseForge web and CurseMaven fallbacks. The update overlay contains no world save data.
