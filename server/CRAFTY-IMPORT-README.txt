AMBER & ARCANA 0.1.9-14 — REI + CONTENT CLEANUP

0.1.9-14 RECIPE VIEWER AND CONTENT CHANGE
JEI and Polymorph were removed from the server. REI 12.1.785 is installed by the matching client manifest only. Ad Astra and The Aether were removed from both sides; AmbientSounds was removed from the client. The launcher now removes stale JEI, Polymorph, REI, Ad Astra, Aether, and AmbientSounds jars before checking the dedicated-server set.

0.1.9-12 QUEST UPDATE
Expanded Create Engineering from four basic milestones to six guided milestones with icons, clearer safety and overflow checks, and twelve claimable item/XP rewards. Existing quest and task IDs were preserved. The removed Local Looks objective was replaced with a vanilla banner-building objective. Client and server quest files are identical.

0.1.9-11 RECIPE CLEANUP
Every Compat (everycomp-1.20-2.9.26-forge.jar) has been removed from client and server because its generated compatibility recipes were the largest source of invalid recipe data in the latest server log. Moonlight/Selene remains because other mods use it.


Performance defaults in this build:
- view-distance=8
- simulation-distance=6
- Spark continuous background profiler disabled
- Untamed Wilds freqocean=96 for newly generated ocean areas
- Java 17 remains preferred by the launcher

See OPTIMIZATION-0.1.9.txt for details and rollback values.

Amber & Arcana 0.1.8-alpha - Crafty 4 Import

Minecraft: 1.20.1
Forge: 47.4.10
Recommended Java: 17
Server mod downloads: 257
Excluded client-only mod JARs: 20
Excluded shader entries: 1 (Complementary Reimagined)

CRAFTY IMPORT
1. Crafty -> Create New Server -> Minecraft Java -> Import a Server -> Zip Import.
2. Upload this ZIP.
3. Select the archive root as the server root (the level containing AmberArcana-Crafty-Launcher.jar).
4. Server Executable: AmberArcana-Crafty-Launcher.jar
5. Java: 17
6. Pack memory preset: 4096 MB initial / 10240 MB maximum for the real Forge server process.
7. Internal server port: 25565. Your Unraid/Docker host port may be different.
8. Start the server. Crafty should handle Minecraft's EULA prompt normally.

FIRST START
The launcher downloads the exact CurseForge files pinned by the original pack, verifies SHA-512 checksums, installs Forge 1.20.1-47.4.10 if it is not already installed, and then launches Forge. It requires outbound internet access from the Crafty container.

CRAFTY EXECUTION COMMAND
Crafty may initially show its normal 4096 MB import default. That is safe for the tiny bootstrap only.
Amber & Arcana 0.1.9-14 explicitly launches the real Forge child with -Xms4096M -Xmx10240M, so the modded server is not limited to Crafty's 4 GB import default.
If you enter a manual command, this is still fine:
java -Xms4G -Xmx10G -jar AmberArcana-Crafty-Launcher.jar nogui

NOTES
- eula.txt is intentionally not pre-accepted.
- Config/FTB Quest files from the CurseForge overrides are already included.
- Untamed Wilds ocean tuning and the pack's ModernFix settings are preserved; Every Compat is removed in 0.1.9-11.
- Client-only UI/rendering/audio/map mods are not downloaded on the dedicated server.
- The source CurseForge ZIP has 278 manifest entries; one is the Complementary shader, and mod-files.json contains 277 JAR entries.
- If a mod's upstream CDN blocks an automated download, the launcher prints the exact filename/file ID that failed.

Files under _crafty/ document exactly what is included/excluded.

Compatibility correction:
- More Hitboxes 1.9.2 is retained server-side because Fossils and Archeology Revival 9.3.4.0 requires it.
- Colorwheel is excluded server-side because this release requires Oculus, which is client-only.
- The bootstrap removes stale excluded JARs when reusing an existing Crafty server directory.

Runtime stability correction:
- Spark 1.10.53 is kept for server diagnostics, but its background profiler is forced to the built-in Java sampler instead of native async-profiler.
- This avoids the native libasyncProfiler SIGSEGV seen when Crafty launched the server with Java 25.
- The bootstrap now searches for an installed Java 17 runtime (including update-alternatives and common JVM paths) and uses it for Forge automatically when found.
- You should still select Java 17 in Crafty when available.

Compatibility fix v3:
- Wiki Zoomer 1.3.0 is retained on the dedicated server. It registers blocks/items and must participate in server registry sync; excluding it can crash a connected client when the creative/inventory tabs rebuild with "Registry Object not present: wikizoomer:item_zoomer".

0.1.9-alpha-r3 content sync:
- Added Just Dire Things [Forge] 1.1.7 to dedicated server downloads.
- Added DecoCraft 3.0.4 (Forge 1.20.1) to dedicated server downloads.
- Matching CurseForge client pack contains the same two mods.


0.1.9-alpha-r3 QUEST + ART PASS
- Finished the first FTB Quests line: Welcome to Amber & Arcana.
- Added visible icons to all three starter quests.
- Added 3 claimable rewards per quest (items + XP), 9 rewards total.
- Added the Amber & Arcana crystal artwork to the opening quest page through KubeJS assets.
- Replaced the bundled pack icon with the supplied amber-crystal artwork.
- Added a 64x64 server-icon.png to the Crafty build.
- Mod list and optimization settings are unchanged from r2.


0.1.9-5 MEMORY PRESET
- Real Forge server child: Xms4096M / Xmx10240M.
- Inherited Crafty -Xms/-Xmx values are intentionally ignored by the child so a 4096 MB import default cannot crash the pack during startup.


0.1.9-5 PACKET + SESSION FIX
- Added Packet Fixer 2.0.0 to dedicated-server downloads. Matching clients must also have Packet Fixer.
- NeoAuth 1.20.1-1.0.3 is included in the matching client pack only; it is deliberately excluded here because it is client-side only.
- Existing Java 17 and Xms4096M / Xmx10240M presets are unchanged.
