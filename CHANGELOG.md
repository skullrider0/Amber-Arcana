## 0.1.9-53 — AI population and optimization tuning

- Set ServerCore MONSTER mobcap to 30 and VAMPIRISM_VAMPIRE mobcap to 10.
- Keep Vampire Barons exempt and set other Vampirism natural-spawn acceptance to 30%.
- Enable ServerCore reduce-sync-loads, ticking-chunk cache and fast biome lookups; keep duplicate-fluid-tick cancellation off for compatibility.
- Enable dynamic performance control at a 35 MSPT target, adjusting chunk-tick distance 6→4 and simulation distance 6→4 while keeping mobcap percentage fixed at 100% and view distance fixed at 8.
- Enable villager breeding/lobotomization safeguards and more aggressive XP/item merging.
- Tune Mobtimizations: 160-tick wander delay, 8x far wander multiplier, 10% far target-search chance, 60-tick player proximity scans.
- Keep ServerCore Entity Activation Range disabled to avoid breaking modded entity behavior.
- Include ServerCore, Mobtimizations, ModernFix, Spark and spawn-balance configuration in the stopped-server Crafty overlay.
- No world/player or quest data changes; run a new 4-player Spark profile after deployment.

## 0.1.9-52 — Mob AI optimization

- Add Mobtimizations 1.0.1 for Forge 1.20.1 (CurseForge 974401:7594372) to client and server.
- Add required CoroUtil 1.3.7 (CurseForge 237749:5096038) to client and server.
- Target repeated entity AI, pathfinding, avoidance, and target-search overhead seen in Spark profiles.
- Preserve the Amber More Hitboxes 1.9.2.3 spatial-query patch.
- No quest, world, or player-data changes; run a fresh Spark profile after deployment.

## 0.1.9-51 — More Hitboxes spatial-query performance patch

- Promote the boot-tested Amber More Hitboxes patch to 1.9.2.3.
- Replace the level-wide typed-query multipart scan with a once-per-tick spatial chunk-bucket index.
- Preserve Fossils and Archeology Revival's required More Hitboxes dependency and multipart hit behavior.
- Preserve the official More Hitboxes 1.9.2 client MinecraftMixin and refmap.
- Remove stale 1.9.2, 1.9.2.1 and 1.9.2.2 local patch JARs during Crafty updates.
- Client boot test passed on Minecraft 1.20.1 / Forge 47.4.10.
- No quest, world, or player-data changes; runtime Spark comparison remains required.

## 0.1.9-50 — More Hitboxes query-cache performance patch

- Upgrade the local More Hitboxes patch from 1.9.2.1 to 1.9.2.2.
- Cache only More Hitboxes-owned Forge multipart pieces once per level tick for typed entity queries.
- Stop unrelated Forge PartEntity collections, including Ice & Fire multipart entities, from being rescanned by every More Hitboxes typed query.
- Preserve Fossils and Archeology Revival's required More Hitboxes dependency and multipart hit behavior.
- Preserve the official More Hitboxes 1.9.2 client MinecraftMixin and refmap.
- Preserve the existing unchanged-position multipart update optimization.
- Add stale-JAR cleanup for 1.9.2.1 on existing Crafty servers.
- No quest, world, or player data changes.

## 0.1.9-45
- Removed generated AA35 filler milestone chains and rewired real quest dependencies.
- Removed Create-first generic reward fallback; reward tables are now constrained by explicit chapter themes.
- Preserved all non-filler quest IDs and synchronized client/server quest data.

## 0.1.9-44

- Repair circular FTB Quests dependency paths that caused recursive `isExcludedByOtherQuestline` crashes.
- Preserve all quest IDs and player/team quest progress; only cycle-closing dependency edges are removed.
- Add a build-time directed-cycle validator so cyclic quest graphs cannot be packaged again.

## 0.1.9-43

- Add Create: Easy Stone Generators 1.0.0 (Forge 1.20.1) to both sides, with SHA-512-pinned server download.
- Keep Create 6.0.8, bee recipes, quests, JEI and patched More Hitboxes unchanged.
- Publish matching client/server archives and a checksummed stopped-server update command.

## 0.1.9-42

- Add Ferricore, Blazegold, Celestigem, Eclipse Alloy and Time Crystal bee definitions and 15 Forge 1.20.1 recipes.
- Add nine species-specific bee quests; preserve all existing quest IDs and finale progress.
- Include recipe data in the full Crafty update overlay; add checksummed stopped-server updater with rollback backup.
- Repair stale current download links. No mod JAR additions: the two requested mods do not support 1.20.1 Forge.

## 0.1.9-41

- Restored Polymorph 0.49.10 for selectable conflicting crafting/smelting/smithing outputs.
- Added Polymorphic Energistics 0.1.1 for AE2 terminal recipe selection.
- Added Refined Polymorphism 0.1.1 for Refined Storage grid recipe selection.
- Added Spartan Weaponry 3.2.1 for the expanded weapon arsenal.
- Client and server must both update; the world-safe Crafty overlay contains no world save data.

## 0.1.9-40

- Fixed Crafty server mod downloads after CurseForge enforced API-key authentication on direct CDN requests.
- Added project IDs to the dedicated-server mod manifest and no-key CurseForge website/CurseMaven fallbacks.
- Added optional authenticated CDN support through CURSEFORGE_API_KEY or _crafty/curseforge-api-key.txt.
- The world-safe Crafty update overlay now includes the updated bootstrap launcher itself.

## 0.1.9-39

- Added No Recipe Book Reborn 1.0.5 for Forge 1.20.1.
- Client-only quality-of-life change: removes the vanilla recipe-book buttons from supported crafting/furnace-style screens.
- Dedicated-server mod list is intentionally unchanged.

## 0.1.9-38

- Rebuilt AE2, Mekanism, Powah, Ars Nouveau, Iron's Spells, Ender IO, and Refined Storage into real mechanics-based progression branches using ATM10 only as a layout/progression reference.
- Added dedicated 13-quest Hostile Neural Networks and 15-quest Draconic Evolution chapters.
- Replaced generic AA35 filler milestones in the rebuilt chapters with concrete mod mechanics and item milestones.
- Hand-curated four weighted reward tiers plus a five-draw Fortune Wheel for all nine touched chapters.
- Corrected the Ender IO reward pools so they no longer contain Create items.
- Preserved all 91 existing quest IDs across the seven rebuilt chapters.

## 0.1.9-37

- Reworked the quest-book display using ATM10's compact visual density and dependency-chain readability as a reference, without copying ATM10 quest text or rewards.
- Compacted all 26 Amber & Arcana chapters adaptively toward ~1.75 quest-node dependency spacing instead of the previous large gaps.
- Preserved every existing quest ID, task, reward, tier roll, and Wheel of Fortune reward.
- Enabled flexible chapter progression display and kept dependency lines visible.
- Reference snapshot: AllTheMods/ATM-10 `ab6f65e07b88423cdae1724864ba42a573ba758a`.

## 0.1.9-36

- Added Mining Gadgets 1.15.6.
- Added Iron Jetpacks 7.0.9, reusing the pack's existing Cucumber Library.
- Added Mekanism Lasers 1.0.10, using the existing Mekanism installation.
- Added Draconic Evolution 3.1.2.621 with Brandon's Core and CodeChicken Lib.
- Added Hostile Neural Networks 5.3.3 with Placebo.
- Added Infernos Otter Taming 1.0.2, reusing Critters and Companions and GeckoLib.
- Crafty update remains world-safe: the update overlay changes pack/mod metadata and quests only; world saves are not included.

# Changelog

## 0.1.9-49 — Performance mod cleanup

- Remove Mowzie's Mobs from client and server.
- Remove Untamed Wilds from client and server.
- Add stale-JAR cleanup for mowziesmobs-1.8.2.jar and untamedwilds-1.20.1-4.0.4.jar on existing Crafty installs.
- Preserve the More Hitboxes Fossils compatibility patch and all existing quest progression.
- No world/player data is included in the update overlay.

## 0.1.9-48 — Vampirism Tinker dedicated-server compatibility fix

- Remove Vampirism Tinker 1.6 from client and server.
- Remove Tinker's Domain / tcondiadema, which was only required by Vampirism Tinker.
- Add stale-JAR cleanup for vampirismtinker-1.6.jar and Tinkers Domain-1.9fix.jar on existing Crafty installs.
- Keep the other six Vampirism addons from 0.1.9-46.
- Preserve Iron Chests removal, More Hitboxes/performance fixes, spawn balancing, and all existing quest progression.
- No world/player data is included in the update overlay.

## 0.1.9-47 — Vampirism Tinker dependency fix

- Add Tinker's Domain / tcondiadema (CurseForge 1218668:6862342, Tinkers Domain-1.9fix.jar).
- Fix dedicated-server startup: Vampirism Tinker 1.6 requires tcondiadema 1.5 or newer.
- Add the dependency to both client and Crafty managed server lists.
- Preserve the seven Vampirism addons, Iron Chests removal, More Hitboxes/performance fixes, and existing quests.
- No world/player data is included in the update overlay.

## 0.1.9-46 — Vampirism addon expansion and Iron Chests removal

- Add Vampirism Iron's Spells Compatibility 0.0.9 (1350048:8525675).
- Add Vampire's Delight 0.1.13c (939092:8200186).
- Add Vampiric Ageing 1.3.26 (906331:6125994).
- Add Werewolves - Become a Beast! 2.0.2.7 (417851:6722563).
- Add Vampirism Tinker 1.6 (1314650:6814093).
- Add Create Vampirism 0.5.0 (1238539:6775688).
- Add Vampirism Umbrella Curios Support 1.0.0 (1565325:8219863).
- Remove Iron Chests (228756:4614852) and clean up ironchest-1.20.1-14.4.4.jar on existing Crafty installs.
- Do not add or change Vampirism/Werewolf FTB Quest progression.
- Leave Create Vampirism Blood Feeding disabled/default-off.
- Preserve the local More Hitboxes performance patch and existing spawn/performance fixes.

## 0.1.9-35 — Deep progression for compact chapters

- Expand all 24 formerly compact chapters into multi-step mechanics progression trees while preserving their historical quest IDs.
- Add 215 required hands-on progression quests for commissioning, operation, automation, exploration, rituals, scaling, and other chapter-specific mechanics.
- Gate historical local dependencies through the new mechanics milestones so the added depth is real progression rather than optional decoration.
- Give every original and new quest one depth-appropriate mod-specific Tier 1-4 loot roll.
- Move every compact chapter's Wheel of Fortune reward to a new true mastery finale that depends on all branch leaves.
- Remove fixed diamond/emerald currency rewards from the expanded chapters; XP and useful starter materials remain.
- Re-layout the expanded trees in a compact serpentine dependency layout and synchronize the complete quest tree client/server.

## 0.1.9-34 — Richer rewards for short progression chapters

- Rebalance every compact chapter with at most 10 quests.
- Give 100% of quests in those short chains a depth-appropriate mod-specific loot roll.
- Expand tier pools to 12/16/20/24 weighted outcomes with 1/2/3/4 draws.
- Expand short-chapter finales to five draws with deeper items kept in a low-weight jackpot band.
- Add no generic vanilla filler and preserve existing quest IDs and reward-table IDs.

## 0.1.9-33 — Productive Bees reward progression

- Rebuild all four Productive Bees tier tables around a much larger pool of mod-specific upgrades, machines, bee tools, and advanced materials.
- Scale reward volume with progression: Tier 1 gives 1 draw, Tier 2 gives 2, Tier 3 gives 3, Tier 4 gives 4, and Master Apiarist gives 5.
- Add the Productive Bees productivity upgrade ladder to later tiers, including an intentionally rare Omega Productivity jackpot.
- Keep Omega rare despite multi-draw tables: weight 0.10 as a Tier 3 preview, 0.30 in Tier 4, and 0.20 in the finale wheel.
- Remove generic diamond/emerald-style filler from the new bee reward pools and preserve existing reward-table IDs.

## 0.1.9-32 — Mod-specific tier loot rolls

- Replace the four generic depth reward pools with four themed tiers per quest chapter/mod.
- Remove diamonds, emeralds, and other generic vanilla filler from the new tier tables; rewards are selected from items belonging to the chapter's actual mods.
- Make Tier 2 rolls award two results, Tier 3 two results, and Tier 4 three results.
- Keep the strongest Tier 4 equipment rare instead of guaranteed; Powah Nitro generators/cells/reactors/rods are explicit sub-1-weight jackpots.
- Re-theme chapter finale Wheel of Fortune tables around the same mod-specific progression pools.
- Preserve quest/reward IDs and current player progression while changing only loot-table targets and contents.

## 0.1.9-31 — Productive Bees cage task labels

- Give all 26 species-specific Bee Cage tasks explicit species labels in FTB Quests.
- Preserve the existing `match_nbt: true` + weak-NBT species filters; only the task presentation changes.
- Keep quest/task/reward IDs and existing player progression intact.

## 0.1.9-30 — Quest UX, tiered rewards, and automatic bee verification

- Replace literal ampersands in player-facing FTB Quests labels with parser-safe wording, fixing red `Invalid formatting` group headers.
- Re-layout every chapter into compact left-to-right dependency layers to reduce giant empty gaps and long crossing lines.
- Give at least 70% of quests a loot roll, counting existing chapter finales; new rolls use four depth tiers and never replace fixed rewards.
- Make Productive Bees species milestones inventory-detected: comb-producing configurable bees require their exact typed honeycomb, while non-comb or non-configurable bees require the exact species in a filled Bee Cage.
- Use `match_nbt: true` plus weak NBT matching so cage metadata can contain normal extra bee state without defeating species detection.
- Preserve existing quest, task, reward, chapter, and group IDs; client/server quest trees remain identical.

## 0.1.9-29 — Mechanics-based quest organization

- Reorganize all 26 FTB Quests chapters into stable mechanic-based chapter groups.
- Put Create Engineering/Workshops/City, Mekanism, Ender IO and Powah under Machines & Production.
- Put Applied Energistics 2 and Refined Storage under Storage & Networks.
- Put Productive Bees and resource/food-production content under Resources & Farming, reserving order index 1 for a future Mystical Agriculture chapter.
- Separate magic, exploration/creatures, settlements, tools/combat, and collection/endgame content into their own groups.
- Preserve every existing chapter, quest, task and reward ID; this is navigation/order only.
  - Start Here: 1 chapter(s)
  - Machines & Production: 6 chapter(s)
  - Storage & Networks: 2 chapter(s)
  - Resources & Farming: 3 chapter(s)
  - Magic & Rituals: 3 chapter(s)
  - Exploration & Creatures: 5 chapter(s)
  - Building & Settlements: 1 chapter(s)
  - Tools, Combat & Equipment: 3 chapter(s)
  - Collections & Endgame: 2 chapter(s)

## 0.1.9-28 — Create progression tree

- Expand Create Engineering from 6 quests to 41 machine and setup milestones.
- Pin validation to Create 1.20.1-6.0.8 / upstream commit `1a1a9a2819b4f89f78caec41b55ed8cb222fa24b`.
- Guide progression through kinetics, processing, fluids, contraptions, brass, precision assembly, logistics, steam power, schematics, and trains.
- Preserve the six historical Create quest IDs and their task/reward IDs so existing progression is not discarded.
- Keep concrete machine milestones inventory-detected and retain the Create Wheel of Fortune finale.
- Keep client and dedicated-server quest trees byte-identical.

## 0.1.9-27 — Productive Bees progression tree

- Add a Productive Bees quest chapter generated from the exact 1.20.1-12.6.0 upstream breeding and conversion data.
- Start with Bee Cage, Advanced Beehive, Expansion Box, Feeder, Centrifuge, and Breeding Chamber setup.
- Lay out wild/base bees and their descendants as visual branches with actual parent dependencies and integration-specific lanes.
- Filter configurable bees by installed-mod conditions so removed or unavailable integrations do not become required progression.
- Add branch completion milestones and a Master Apiarist finale with a Productive Bees weighted Wheel of Fortune table.
- Keep client/server quest trees identical and preserve all pre-existing quest IDs.

## 0.1.9-26 — Weighted Wheel of Fortune finale rewards

- Add a server-authoritative weighted `loot` reward to every chapter finale using FTB Quests 2001.4.14's native reward-table system.
- Generate chapter-themed weighted tables from existing validated rewards and item requirements, with modded requirement items used as rarer jackpot results.
- Preserve all existing fixed rewards and historical quest/task/reward IDs; wheel rewards are additive.
- Brand the native full-screen reward reveal as `Wheel of Fortune` on updated clients.
- Keep client and dedicated-server quest trees byte-identical after generation.

## 0.1.9-25 — Finalize quest runtime format and automatic milestones

- Repair all malformed FTB Quests simple item stacks by serializing item filters in the canonical 1.20.1 format.
- Preserve every existing 16-character quest/task/reward ID while making concrete mod-item milestones complete automatically.
- Keep historical checkmark task IDs as optional verification tasks for automatic milestones; keep manual confirmation required for build/claim/behavior objectives.
- Add static validation for canonical item-task serialization, mixed automatic/manual progression, ID preservation, and client/server quest parity.
- Add a quest-only Crafty overlay so existing servers can update `config/ftbquests/quests/` without touching worlds or mods.

## 0.1.9-24 — Complete quest requirements and rewards

- Finish the full 25-chapter / 106-quest pass.
- Give every quest at least one non-consuming item requirement plus a named manual confirmation task.
- Add rewards, subtitles, and quest/chapter icons across the unfinished chapters while preserving all existing quest IDs and dependency chains.
- Gate normal progression branches behind `Tools for the journey`; gate Create City behind the Create Engineering and Settlement finales.
- Gate Endgame behind the Create Engineering, Mekanism, Ritual Magic, Settlement, and Dinosaur Laboratory finales.
- Replace the impossible Twilight Forest quest with a Nether expedition while preserving its quest ID.
- Preserve the client-safe More Hitboxes 1.9.2.1 patch and the 0.1.9-23 live quest save synchronization.

## 0.1.9-23 — Live FTB Quests sync and reward repair

- Import the complete client editor save `2026-09-15-12-17-14` as the quest-book source of truth.
- Synchronize all 25 chapters, `chapter_groups.snbt`, `data.snbt`, and 5 reward tables to both client and dedicated server.
- Repair 12 item rewards saved without an `item` value, which rendered as `minecraft:air`.
- Preserve editor-generated quest/task/reward IDs and progression.
- Add a subtitle to `Make a home` and preserve the literal Amber & Arcana ampersand with raw JSON text.
- Preserve the tested More Hitboxes 1.9.2.1 performance patch from 0.1.9-22.

## 0.1.9-22 — Client-safe More Hitboxes performance patch

- Replace the stock More Hitboxes 1.9.2 runtime with Amber's `1.9.2.1` performance patch while retaining the `morehitboxes` mod ID required by Fossils and Archeology Revival 9.3.4.0.
- Patch only the global `Level` entity-query path and multipart position update path; preserve the official 1.9.2 client `MinecraftMixin` and Mixin refmap.
- Verify the runtime-critical class/refmap fingerprints against the client-safe beta that successfully booted on Forge 47.4.10.
- Bundle the patched JAR directly in both client and dedicated-server packages and remove the official CurseForge More Hitboxes entry from the client manifest to avoid duplicate mod IDs.
- Pin Crafty to the local patched JAR by exact filename and SHA-512; remove the old stock `morehitboxes-forge-1.20.1-1.9.2.jar` on existing servers.
- Replace the old one-file Crafty JEI overlay with a world-safe Crafty update overlay containing `_crafty/server-mods.tsv`, `_crafty/remove-mods.txt`, and the patched More Hitboxes JAR.
- Record the 2026-09-15 quest editor screenshot as a live-data sync issue: `Make a home` renders, but the live editor shows `[No Subtitle]` and a reward resolving to `minecraft:air`, while the repository copy still defines 16 torches, 8 bread, and 100 XP. The live quest file must be captured before quest data is synchronized.
- Runtime Spark profiling is still required to measure the actual server-thread improvement.

## 0.1.9-21 — Restore More Hitboxes dependency

- Restore More Hitboxes 1.9.2 (CurseForge 1115989:6942239) on client and dedicated server.
- Remove `morehitboxes-forge-1.20.1-1.9.2.jar` from Crafty's stale-mod deletion list.
- Restore the exact pre-0.1.9-20 download metadata and checksum.
- Confirm upstream More Hitboxes 1.9.2 has no per-mod/entity whitelist or `fossils_only` config option; no nonfunctional config is added.
- Fossils and Archeology Revival 9.3.4.0 remains the dependency requiring More Hitboxes.
- Runtime Spark re-profile is still required because the upstream Forge Level entity-query mixins are global.

## 0.1.9-20 — More Hitboxes performance removal

- Remove More Hitboxes 1.9.2 from both client and dedicated server.
- Remove CurseForge project 1115989 / file 6942239 from the client manifest and pack inventories.
- Remove `morehitboxes-forge-1.20.1-1.9.2.jar` from Crafty's managed server mod list.
- Add `morehitboxes-forge-1.20.1-1.9.2.jar` to `_crafty/remove-mods.txt` so an updated Crafty server deletes the stale jar automatically.
- Preserve JEI 15.20.0.106 on both client and server, Twilight Forest removal, and the Eternal Steak chest-loot filter.

## 0.1.9-19 — Server JEI / Crafty overlay

- Add JEI 15.20.0.106 (CurseForge 238222:6075247) to the Crafty dedicated-server managed mod list.
- Keep client and server on the exact same JEI build.
- Add a tiny Crafty-root overlay ZIP containing only `_crafty/server-mods.tsv` for existing servers.
- Preserve Twilight Forest removal and the Eternal Steak chest-loot filter.

## 0.1.9-18 — JEI dependency compatibility

- Raise client JEI from 15.2.0.27 to 15.20.0.106 (CurseForge 238222:6075247).
- Fix Forge startup failures from Create, Sophisticated Core, ModernFix, Chipped, and Tinkers' Construct requiring newer JEI APIs.
- Keep JEI client-only on the dedicated-server package.
- Preserve the 0.1.9-17 Twilight Forest removal and Eternal Steak chest-loot filter.
- Retest Mekanism machine recipe categories in-game after launch.

## 0.1.9-17 — Content cleanup

- Remove The Twilight Forest (CurseForge 227639:5468648) from client and server packaging.
- Add `twilightforest-1.20.1-4.3.2508-universal.jar` to Crafty stale-mod cleanup for existing server installs.
- Block `artifacts:eternal_steak` from CHEST loot only using the pack's existing LootJS integration.
- Leave Artifacts installed and leave non-chest Eternal Steak acquisition untouched.
- No Glitchy Mantle removal was necessary; that relic is not present in this Forge 1.20.1 pack.
- Preserve the Mekanism-compatible JEI 15.2.0.27 client pin from 0.1.9-16.

## 0.1.9-16 — Mekanism machine-recipe JEI compatibility

- Pin client JEI to 15.2.0.27 (CurseForge file 4712868), matching Mekanism 10.4.16's 1.20.x JEI baseline.
- Remove JEI from the dedicated-server mod download list; the viewer is not required server-side.
- Target missing Mekanism machine categories, including Metallurgic Infuser recipes such as Atomic Alloy.
- Preserve the 0.1.9-14 recipe/tag fixes, quests, and all non-viewer content.
- Rebuild client/server archives and validate archive/source parity.

## 0.1.9-15 — Native JEI display diagnostic

- Replace REI 12.1.785 with JEI 15.59.0.211 Forge (beta), matching client/server pins.
- Avoid REI's null armor repair ingredient display-loading failure.
- Restore native JEI plugin discovery for machine recipes without REIPC.
- Retain the selected JEI during launcher cleanup; remove obsolete viewer jars.
- Preserve all previous recipe/tag overrides and quest IDs; update viewer wording.
- Validate archive/source parity so truncated or stale distributions fail clearly.
- Runtime browsing/crafting acceptance remains pending; see docs/jei-display-0.1.9-15.md.


## 0.1.9-14 — 2026-09-14

- Added identical client/server KubeJS data overrides for 36 recipes that Forge
  rejected in a fresh 0.1.9-13 Crafty startup.
- Repaired Reborn Storage's invalid item-tier parent tags without changing its
  valid fluid tiers.
- Corrected I Wanna Skate's stale vanilla stair/slab tag references.
- Removed only the nonexistent Just Dire Things `paradox_machine` entry while
  preserving the rest of its paradox deny list.
- Preserved all requested content mods, including Just Dire Things and
  DecoCraft.
- Extended static validation to enforce compatibility-data parity and JSON
  validity.

## 0.1.9-13 — 2026-09-14

### Changed

- Replaced JEI with Roughly Enough Items 12.1.785 for Forge 1.20.1.
- Kept REI client-only and removed recipe viewers from the dedicated server.
- Removed launcher logic that forced JEI installation.
- Repurposed two dimension-related quests while preserving established quest IDs.

### Removed

- JEI.
- Polymorph, because the installed build hard-requires JEI.
- Ad Astra from client and server.
- The Aether from client and server.
- AmbientSounds from the client.

### Preserved

- Every Compat remains removed.
- Moonlight/Selene remains installed.
- Just Dire Things and DecoCraft remain installed on both sides.
- Earlier network, quest serialization, memory, and Crafty launcher fixes.
