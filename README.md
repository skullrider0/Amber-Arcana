# Amber & Arcana

Amber & Arcana is a Forge 1.20.1 modpack maintained as matching client and Crafty 4 dedicated-server packages.

## Direct downloads

[Download Client 0.1.9-52](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-0.1.9-52-Client.zip) · [Download Crafty Server 0.1.9-52](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-0.1.9-52-Server.zip) · [Update existing Crafty server](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-0.1.9-52-Crafty-Update-Overlay.zip)

## Current release

| Component | Version |
| --- | --- |
| Pack | 0.1.9-52 |
| Minecraft | 1.20.1 |
| Forge | 47.4.10 |
| Java | 17 |
| Client manifest entries | 296 + 1 local patched JAR |
| Server managed mod entries | 276 |
| Quests | 334 across 28 chapters |

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

Import `dist/Amber-and-Arcana-0.1.9-44-Client.zip` into CurseForge/Prism. Allocate about 10 GB RAM and use Java 17. The patched More Hitboxes JAR is included under the pack overrides, so do not add the stock More Hitboxes 1.9.2 JAR alongside it.

### Fresh Crafty server

Create a fresh server from `dist/Amber-and-Arcana-0.1.9-44-Server.zip`. The included launcher downloads normal managed server mods, accepts the bundled local More Hitboxes patch by exact SHA-512, removes the replaced stock 1.9.2 JAR, chooses Java 17, and starts Forge with the configured memory limits.

Back up an existing world before replacing a complete server package. Removed content mods can leave missing blocks, items, or dimensions in an existing world.

### Existing Crafty server

Stop the server and extract `dist/Amber-and-Arcana-0.1.9-44-Crafty-Update-Overlay.zip` into the existing server root with overwrite enabled. The full update overlay includes the current Crafty launcher, managed mod lists, the pinned More Hitboxes patch, synchronized quests, KubeJS data/assets and release metadata. It contains no world or player data. Start through `AmberArcana-Crafty-Launcher.jar` afterward so newly required mods are downloaded. Quest-only overlays do not install recipe fixes.

For a checksummed update with a backup of replaced files, use [the stopped-server updater](scripts/update-crafty-0.1.9-49.py) as described in [the bee integration notes](docs/bee-integrations-0.1.9-42.md).

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

For an existing Crafty server that already has the correct mods, use `dist/Amber-and-Arcana-0.1.9-44-Crafty-Quest-Overlay.zip`. Stop the server, back up the world, extract the ZIP into the server root with overwrite enabled, and start the server again. If you copy the quest files while the server is already running, run `/ftbquests reload` from the server console or with sufficient in-game permission. The quest-only overlay contains only `config/ftbquests/quests/`; it does not contain a world, mods, or Crafty launcher files.

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


### 0.1.9-41 recipe conflicts and Spartan Weaponry
Adds Polymorph plus AE2/Refined Storage integrations so conflicting recipes can be selected in crafting/storage terminals, and adds Spartan Weaponry 3.2.1. This is a client-and-server content update; the Crafty update overlay remains world-safe.


### 0.1.9-42 bee integrations
Adds five Just Dire Things resource bees and nine bee quests. The full update overlay now includes KubeJS data/assets and release metadata, required for existing servers to receive recipes. See [bee integration notes](docs/bee-integrations-0.1.9-42.md) and [the stopped-server updater](scripts/update-crafty-0.1.9-49.py). Cobblegen Galore and Tiny Soldiers have no compatible 1.20.1 Forge release and are not added.


### 0.1.9-43 stone generators
Adds [Create: Easy Stone Generators 1.0.0 for Forge 1.20.1](https://www.curseforge.com/minecraft/mc-mods/create-stone-generators/files/6224618) to client and server. Includes six mixer/basin recipes for cobblestone, stone, obsidian, basalt, limestone and scoria. Both sides must update because the mod registers a required network channel. Keeps Create 6.0.8, all 0.1.9-42 bee data, quest progress and existing pack patches. The stopped-server updater backs up overwritten pack files and never writes world data.


### 0.1.9-44 quest-cycle repair
Repairs circular FTB Quests dependency paths that could recurse through `TeamData.isExcludedByOtherQuestline()` until the dedicated server crashed. Quest IDs and world/player data are preserved. The build now validates the complete dependency graph as acyclic before packaging.


### 0.1.9-45 quest curation
Removes the generated AA35 filler chains (for example Prepare/Build/Connect copies of the same milestone), reconnects the meaningful quests directly, and replaces the old Create-first generic reward fallback with explicit per-chapter reward themes. Build validation now rejects leftover AA35 filler markers and unrelated reward namespaces. Existing non-filler quest IDs and world/player data are preserved.


### 0.1.9-46 Vampirism expansion
Adds seven Forge 1.20.1 Vampirism addons without changing FTB Quest progression: Vampirism Iron's Spells Compatibility, Vampire's Delight, Vampiric Ageing, Werewolves, Vampirism Tinker, Create Vampirism, and Vampirism Umbrella Curios Support. Iron Chests is removed from client/server packaging and existing Crafty installs delete ironchest-1.20.1-14.4.4.jar on the next launcher start. Create Vampirism's WIP Blood Feeding feature is not enabled.


### 0.1.9-47 Vampirism Tinker dependency fix
Adds Tinker's Domain (tcondiadema) 1.9fix, required by Vampirism Tinker 1.6. No quests or world/player data are changed.


### 0.1.9-48 dedicated-server compatibility fix
Removes Vampirism Tinker 1.6 because it crashes Forge dedicated servers by loading the client-only ClientDiademaRegister class during mod construction. Tinker's Domain is removed with it because it was added only as Vampirism Tinker's dependency. The other six Vampirism addons remain. Quests and world/player data are unchanged.


### 0.1.9-49 performance mod cleanup
Removes Mowzie's Mobs and Untamed Wilds from client and server after the latest Spark performance pass. Existing Crafty installs delete mowziesmobs-1.8.2.jar and untamedwilds-1.20.1-4.0.4.jar on the next launcher start. Quest progression and world/player data are unchanged.

### 0.1.9-50 More Hitboxes query-cache performance patch
Upgrades Amber's local More Hitboxes patch to 1.9.2.2. The Forge typed-entity-query hook now snapshots only More Hitboxes-owned multipart pieces once per level tick instead of rescanning every Forge PartEntity on every query. This keeps Fossils multipart hitboxes while preventing unrelated multipart mobs such as Ice & Fire dragons from multiplying normal mob-AI query cost. Client mixins/refmap remain based on the official More Hitboxes 1.9.2 JAR. World/player data and quest progression are unchanged.

### 0.1.9-51 More Hitboxes spatial-query performance patch
Promotes the client-boot-tested More Hitboxes 1.9.2.3 patch. Typed entity queries now use a per-tick spatial chunk-bucket index instead of walking the full level-wide MoreHitboxes multipart set for every AI query. Fossils and Archeology Revival compatibility is preserved, as are the official More Hitboxes 1.9.2 client mixin/refmap. The client test build reached the Minecraft main menu on Forge 47.4.10. World/player data and quest progression are unchanged; a post-deployment Spark comparison is still required.

### 0.1.9-52 Mob AI optimization
Adds Mobtimizations 1.0.1 and its CoroUtil 1.3.7 dependency to both client and dedicated server. This targets repeated entity AI/pathfinding/target-search work identified in Spark profiles while preserving the More Hitboxes 1.9.2.3 spatial-query patch. No world/player or quest data is changed; a post-deployment Spark comparison is recommended.
