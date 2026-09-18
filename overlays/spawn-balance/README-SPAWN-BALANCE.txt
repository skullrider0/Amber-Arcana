AMBER & ARCANA - CRAFTY SPAWN BALANCE PATCH
===========================================

Target:
Minecraft 1.20.1
Forge 47.4.10
Amber & Arcana
Crafty server UUID: b6356e28-2508-4bad-8869-133860f04f83

WHAT THIS DOES
--------------
1. Keeps the existing Amber & Arcana quest/spawn-balance overlay behavior.
2. Cuts normal natural mob spawn attempts by 50% across the pack.
3. Cuts Vampirism natural spawn attempts by another 50%.
   Combined result: about 25% of unpatched vampire spawn throughput.
4. Cuts Ice & Fire natural spawn attempts by another 70%.
   Combined result: about 15% of unpatched Ice & Fire natural spawn throughput.
   This explicitly includes iceandfire:pixie.
5. Cuts Untamed Wilds natural spawn attempts by another 50%.
   Combined result: about 25% of unpatched Untamed Wilds natural spawn throughput.
6. Untamed Wilds ocean generation rarity is also raised from 96 to 192
   (about half as many new ocean feature placement opportunities as before).
7. Completely blocks these Mekanism Additions baby mobs:
   - baby creeper
   - baby enderman
   - baby skeleton
   - baby stray
   - baby wither skeleton
8. Does NOT modify MoreHitboxes.
9. Does NOT delete existing mobs.

INSTALL IN CRAFTY
-----------------
1. STOP Amber & Arcana.
2. Make a backup/snapshot first.
3. Extract the current Crafty spawn-balance/update overlay into the Crafty server root:
   /crafty/servers/b6356e28-2508-4bad-8869-133860f04f83
4. Start the server normally.

After extraction these paths should exist:
- config/untamedwilds-common.toml
- kubejs/server_scripts/amber_arcana_spawn_balance.js

VERIFY
------
Look in the server log for:
[Amber & Arcana] Spawn balance patch loaded

Then play normally for 5-10 minutes and run:
spark healthreport

If lag returns while mobs are moving slowly, run:
spark profiler start --only-ticks-over 50 --timeout 60

NOTES
-----
- Existing mobs are not mass-killed. Overpopulation should fall as normal despawning occurs.
- Spawners, breeding, commands and summons are intentionally left alone.
- Pixies are covered by the Ice & Fire 70% mod-specific natural-spawn reduction.
- Untamed Wilds receives both a live natural-spawn reduction and a new-chunk ocean generation reduction.
