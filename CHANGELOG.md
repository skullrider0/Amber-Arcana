# Changelog

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
