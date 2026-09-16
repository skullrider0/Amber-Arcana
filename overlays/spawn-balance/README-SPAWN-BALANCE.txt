AMBER & ARCANA - CRAFTY SPAWN BALANCE PATCH
===========================================

Target:
Minecraft 1.20.1
Forge 47.4.10
Amber & Arcana 0.1.9-25 quest overlay + spawn-balance bundle
Crafty server UUID: b6356e28-2508-4bad-8869-133860f04f83

WHAT THIS DOES
--------------
1. Includes the finalized Amber & Arcana 0.1.9-25 quest system.
2. Cuts normal mob spawn attempts by 50% across the pack.
3. Cuts Vampirism natural spawn attempts by another 50%.
   Combined result: about 25% of the current vampire spawn throughput.
4. Completely blocks these Mekanism Additions baby mobs:
   - baby creeper
   - baby enderman
   - baby skeleton
   - baby stray
   - baby wither skeleton
5. Does NOT modify MoreHitboxes.
6. Does NOT delete existing mobs.

INSTALL IN CRAFTY
-----------------
1. STOP Amber & Arcana.
2. Make a backup/snapshot first.
3. Extract this ZIP into the Crafty server root:
   /crafty/servers/b6356e28-2508-4bad-8869-133860f04f83
4. Start the server normally.

After extraction these paths should exist:
- config/ftbquests/quests/
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
- If the world is still too crowded after existing mobs despawn, the global 50% value can be increased to 60-70% reduction in a follow-up patch.
- If vampires become too rare, the second Vampirism 50% layer can be reduced independently.
