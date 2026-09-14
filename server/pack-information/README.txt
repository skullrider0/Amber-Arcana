AMBER & ARCANA 0.1.9-13 — REI + CONTENT CLEANUP

0.1.9-13 RECIPE VIEWER AND CONTENT CHANGE
Replaced JEI 15.57.0.207 with Roughly Enough Items (REI) 12.1.785 for Forge 1.20.1. Polymorph was removed because this installed build requires JEI. Ad Astra, AmbientSounds, and The Aether were removed at the pack owner's request. Existing Create Engineering quest work and all other pack fixes are preserved.

0.1.9-12 QUEST UPDATE
Expanded Create Engineering from four basic milestones to six guided milestones with icons, clearer safety and overflow checks, and twelve claimable item/XP rewards. Existing quest and task IDs were preserved. The removed Local Looks objective was replaced with a vanilla banner-building objective.

0.1.9-11 RECIPE CLEANUP
Every Compat (everycomp-1.20-2.9.26-forge.jar) has been removed from client and server because its generated compatibility recipes were the largest source of invalid recipe data in the latest server log. Moonlight/Selene remains because other mods use it.

Minecraft 1.20.1 / Forge 47.4.10 / Create 6.0.8

INSTALL
1. Open CurseForge, choose Minecraft, and choose Import.
2. Select Amber-and-Arcana-0.1.9-13-Client.zip without extracting it.
3. Let CurseForge download the pinned mods. The small ZIP contains a download manifest, not the mod JARs.
4. Keep the bundled override files when importing: they contain the pack settings and quests.
5. Launch the new profile. Use a new world for this alpha.

CONTENTS
277 pinned mod/library files plus Complementary Reimagined r5.6.1.
25 FTB Quests chapters with 106 manual checkmark milestones.
Butchery Farmer's Delight and Vampirism compatibility settings are enabled.
Apotheosis and Apothic Attributes/Enchanting are excluded.

VISUALS
Embeddium, Oculus, Colorwheel, sound physics, animations, and building/world content are included.
Complementary Reimagined is supplied as a selectable shader pack. Select it through Video Settings > Shader Packs after the first successful launch. Shader appearance, performance, and mod rendering have not been tested in-game.

PACK ICON 0.1.8
Added the custom golden amber / purple magical flame icon. The original artwork is included as icon.png at the ZIP root and as overrides/amber-and-arcana-icon.png. After import, amber-and-arcana-icon.png is available in the instance Minecraft folder beside mods and config.
If your launcher does not select an icon automatically, choose this PNG using its custom instance/profile icon control. Automatic launcher icon selection has not been verified; no nonstandard manifest fields are used.
This revision changes branding only. All mod versions, quests and gameplay/performance configuration files remain the same as 0.1.7.

OCEAN POPULATION TUNING 0.1.7
Reduced Untamed Wilds ocean world-generation spawn opportunities by changing gencontrol.freqocean from its default 16 to 64. This setting uses a 1-in-N rarity filter: the configured probability is now one quarter of the default. Actual fish numbers depend on eligible chunks, species/groups and breeding; this is not a guarantee of 75% fewer fish or a measured RAM reduction.
Existing installation: close Minecraft, open config/untamedwilds-common.toml, find [gencontrol], and change freqocean = 16 to freqocean = 64. Preserve the rest of your existing configuration. If the file does not exist, copy overrides/config/untamedwilds-common.toml from this ZIP into config. Restart the game; on a dedicated server apply the setting there and restart it. No full re-import needed.
Rollback: restore freqocean = 16 and restart. The setting affects newly generated ocean areas; it does not remove existing animals or replenish animals in already-generated chunks when reverted.
This change retains the mod, all fish species, aquarium animals, ordinary breeding, land animals, freshwater spawning, sessile ocean spawning, and other mods' spawns. The mod's natural-breeding toggle is global, so it was not disabled for this ocean-only request. Fish already loaded still need to be simulated.
The installed 4.0.4 JAR was checked for the exact config filename, key, default/range and use in an ocean RarityFilter. Archive contents were checked. This revision has not been launch-tested or benchmarked.
The supplied CPU profile identifies EntitySpadefish.aiStep at 16.35% and EntityTrevally.aiStep at 3.04% of sampled server-thread time. This supports targeting these fish, but does not establish that spawning is the cause of rapid heap refill; existing fish AI can also allocate temporary objects.

HOME COMMANDS 0.1.6
Added FTB Essentials 2001.2.3 (official Forge 1.20.1 file 6555287). Its required FTB Library dependency is already installed. This adds /sethome base, /home base, /delhome base and /listhomes with the mod's default limits and cooldowns. Default home limit: one. The getting-started quest explains the commands.
For your existing instance: close Minecraft, download ftb-essentials-forge-2001.2.3.jar from https://www.curseforge.com/minecraft/mc-mods/ftb-essentials/files/6555287 and add it to the instance mods folder, then restart. No full re-import is needed for the commands. A dedicated multiplayer server also needs this mod; adding it only to a client will not supply server commands.
Just Dire Things could not be included: its official project has no Forge 1.20.1 release. See https://www.curseforge.com/minecraft/mc-mods/just-dire-things .
All earlier mod versions, removals and memory settings are retained. The new command mod was statically inspected for dependencies and command registration but has not been launched in this pack.
The latest supplied gameplay excerpt contains 34 GC events over 312 seconds: median pause 9 ms, maximum 42 ms. It contains no OutOfMemoryError and no allocation-profile link. This does not identify a culprit or establish a memory leak. The user reports roughly 8000 MB used after enabling dynamic resources.
To investigate ongoing stutters, run /sparkc profiler start --alloc --timeout 120, play normally for two minutes, and send the resulting report link. If Spark reports an error, send that error instead. Keep the current heap and graphics settings for comparison.

MEMORY TEST 0.1.5
The user reports that the preceding revision runs, but memory reaches the 10 GB limit.
Enabled mixin.perf.dynamic_resources=true in config/modernfix-mixins.properties to load block/item models on demand. This optional ModernFix feature can reduce model memory but may introduce loading or rendering incompatibilities. The setting exists in the exact bundled JAR. This revision needs a client launch and before/after memory comparison; no RAM savings are claimed yet.
Existing installations: close Minecraft and add or update this one setting in the existing file. Keep other properties. Set it back to false and restart if loading or textures break. See MEMORY-TEST.txt for instructions, measurement, and rollback.
No mods or registered blocks changed in this revision. The ZIP does not change launcher heap limits.

HOTFIX 0.1.4 — DINOSAUR FOOD COMPATIBILITY
The fourth user log confirms the Every Compat fix took effect: Rechiseled/Chipped/Macaws Furniture integrations are absent and generated compatibility blocks fell from 33,097 to 13,021. The previous Duplicate key Rechiseled crash is absent.
A subsequent world-selection crash occurs in Fossils and Archeologys EndDelightCompat.registerFoodMappings: the installed End's Delight 2.6.1 no longer contains cn/foggyhillside/ends_delight/registry/ItemRegistry or BlockRegistry. Removed End's Delight; Fossils gates this integration on the addon being installed. It is not a required dependency of another included mod.
For an existing installation: disable or remove ends_delight-2.6.1+forge.1.20.1.jar, then relaunch. Keep the earlier config change and addon removals. No re-import is needed for this hotfix.
The Every Compat change is confirmed in a user launch. The user subsequently reports the pack runs. A complete gameplay test and RAM savings have not been demonstrated by these logs.

HOTFIX 0.1.3 — STARTUP AND MEMORY
The third user log shows Every Compat failing while reporting Rechiseled integration errors (Duplicate key Rechiseled), preceded by a NoSuchMethodError for RechiseledBlock. It contains no OutOfMemoryError.
Added config/everycomp-hazardous.toml with module blacklist: rechiseled, chipped, mcwfurnitures. This skips the incompatible Rechiseled integration and reduces generated building variants. The Chipped and Macaws Furniture compatibility modules registered 20,076 blocks in the supplied log, out of Every Compats 33,097. Actual RAM savings require another launch to measure.
All three base building mods remain installed. The existing ModernFix, FerriteCore, Embeddium, ImmediatelyFast, and Entity Culling versions are retained. No extra performance mod or experimental mixin override was added.
For an existing installation: close Minecraft, copy overrides/config/everycomp-hazardous.toml from this ZIP into the instance minecraft/config folder, replacing the existing file, and launch again. Keep the earlier Eat Andesite and Alexs Caves Delight removals. No full re-import is needed.
Keep roughly 10 GB maximum heap while measuring this revision. The supplied launch already used -Xmx10122m. The crash report shows a largely occupied heap, but the fatal exception is the mod integration failure, not an allocation failure.
Use the same config on all clients and any dedicated server. Apply before creating a world; removing generated variants from an established world can remove blocks already placed there.

HOTFIX 0.1.2
Removed Alexs Caves Delight at the pack owners request after a confirmed NoClassDefFoundError for vectorwing/farmersdelight/common/block/ShepherdsPieBlock. No included mod declares a dependency on this addon, and no bundled quest requires it.
Existing installations: disable or remove alexscavesdelight-1.0.27-final.jar, then relaunch.

HOTFIX 0.1.1
Removed Create: Eat Andesite after the first user launch failed in its EdibleItemUseMixin (could not find target use in Minecraft Item). Its JAR lacks the referenced mixin.refmap.json. No installed mod declares a dependency on it.
Existing installations: disable or remove eatandesite-forge-1.20.1-1.0.0-1.20.1.jar in your launcher, then relaunch. No re-import is required for this hotfix.
The download filename retains 0.1.0; manifest version 0.1.8-alpha identifies this revision.

STATUS AND LIMITS
This is an initial import build, not a finished or gameplay-tested release.
Archive structure, project/file IDs, downloaded mod JAR metadata, declared dependency presence, version-range screening, and quest identifiers were checked.
The initial user launch reached Forge and failed in Eat Andesite. The next reported loading failure was Alexs Caves Delight. Both failing addons are now removed. A later user launch reached the accessibility screen and failed in Every Compat; the 0.1.3 config addresses that integration and reduces generated blocks. The fourth user log confirms the Every Compat fix and reaches world selection before failing in Fossils/End's Delight food mapping. Version 0.1.4 removes End's Delight; the user subsequently reports the pack runs. Version 0.1.5 enables an optional memory optimization and still needs a launch/rendering test. Runtime/mixin conflicts, world generation, recipes, graphics, multiplayer, and quest loading still require in-game testing.
Quests use manual checkmarks. Automatic item detection, rewards, and custom recipe/progression gates are not implemented. Default mod recipes remain in effect.
The client pack is not a dedicated-server ZIP; it includes client rendering mods.

If importing or launching fails, provide the complete error and the profile's logs/latest.log or crash-reports file so the exact pinned build can be corrected.

SCOPE
Some requested or proposed additions are not in this alpha. See omitted-additions.txt for the full list and reasons. All included versions are listed in mod-files.json.


0.1.9-alpha-r3 QUEST + ART PASS
- Finished the first FTB Quests line: Welcome to Amber & Arcana.
- Added visible icons to all three starter quests.
- Added 3 claimable rewards per quest (items + XP), 9 rewards total.
- Added the Amber & Arcana crystal artwork to the opening quest page through KubeJS assets.
- Replaced the bundled pack icon with the supplied amber-crystal artwork.
- Added a 64x64 server-icon.png to the Crafty build.
- Mod list and optimization settings are unchanged from r2.
