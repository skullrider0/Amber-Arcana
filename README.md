# Amber & Arcana

Amber & Arcana is a Forge 1.20.1 modpack maintained as matching client and Crafty 4 dedicated-server packages.

## Direct downloads

[⬇️ Download Client 0.1.9-22](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-0.1.9-22-Client.zip) · [⬇️ Download Crafty Server 0.1.9-22](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-0.1.9-22-Server.zip) · [⬇️ Update an existing Crafty server](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-0.1.9-22-Crafty-Update-Overlay.zip)

## Current release

| Component | Version |
| --- | --- |
| Pack | 0.1.9-22 |
| Minecraft | 1.20.1 |
| Forge | 47.4.10 |
| Java | 17 |
| Client manifest entries | 276 + 1 local patched JAR |
| Server managed mod entries | 257 |
| Manual quests | 106 across 25 chapters |

Release 0.1.9-22 keeps JEI 15.20.0.106 on client and server and replaces stock More Hitboxes 1.9.2 with the Amber `1.9.2.1` performance patch required by Fossils and Archeology Revival 9.3.4.0.

The More Hitboxes patch changes only the expensive global `Level` entity-query behavior and multipart position update path. The official 1.9.2 client `MinecraftMixin` and Mixin refmap are preserved, which fixes the client crash seen in the first beta rebuild. The release validates the runtime-critical class/refmap fingerprints against the client-safe beta that successfully booted on Forge 47.4.10. The patched JAR is bundled directly instead of being declared as the stock CurseForge file, preventing duplicate `morehitboxes` mod IDs.

## Repository layout

- `client/` — CurseForge-compatible manifest and client overrides.
- `server/` — Crafty-ready server package source, launcher, config, quests, and validation records.
- `dist/` — ready-to-import client/server ZIPs, Crafty update overlay, and checksums.
- `vendor/morehitboxes/` — the client-safe local More Hitboxes patch plus upstream MIT license and checksums.
- `patches/` — source-level More Hitboxes performance changes used to build the patched classes.
- `scripts/` — repeatable validation and packaging helpers.
- `docs/` — investigation notes and runtime findings.
- `GOAL-MAP.md`, `GOALS.md`, `WORKLOAD.md`, and `CHECKLIST.md` — project goals, queue, and validation gates.

## Install

### Client

Import `dist/Amber-and-Arcana-0.1.9-22-Client.zip` into CurseForge/Prism. Allocate about 10 GB RAM and use Java 17. The patched More Hitboxes JAR is included under the pack overrides, so do not add the stock More Hitboxes 1.9.2 JAR alongside it.

### Fresh Crafty server

Create a fresh server from `dist/Amber-and-Arcana-0.1.9-22-Server.zip`. The included launcher downloads normal managed server mods, accepts the bundled local More Hitboxes patch by exact SHA-512, removes the replaced stock 1.9.2 JAR, chooses Java 17, and starts Forge with the configured memory limits.

Back up an existing world before replacing a complete server package. Removed content mods can leave missing blocks, items, or dimensions in an existing world.

### Existing Crafty server

Stop the server and extract `dist/Amber-and-Arcana-0.1.9-22-Crafty-Update-Overlay.zip` into the existing server root with overwrite enabled. The overlay contains only:

- `_crafty/server-mods.tsv`
- `_crafty/remove-mods.txt`
- `mods/morehitboxes-forge-1.20.1-1.9.2.1.jar`

It does **not** contain or overwrite the world. On the next start Crafty removes the old stock `morehitboxes-forge-1.20.1-1.9.2.jar` and validates the patched JAR instead of redownloading the original.

The historical `Crafty-JEI-Overlay.zip` filename is also rebuilt as a compatibility alias to the same 0.1.9-22 update overlay.

## Quest runtime status — 2026-09-15

The latest in-game editor screenshot confirms the `Make a home` quest renders, but it also shows `[No Subtitle]` in editor view and one reward resolving to `minecraft:air`.

The repository copy does **not** currently match those live rewards: `getting_started.snbt` still defines 16 torches, 8 bread, and 100 XP for `Make a home`. Because the live server quest data has diverged, 0.1.9-22 records the discrepancy but does not overwrite the quest file. The next quest-sync pass should capture the live `config/ftbquests/quests/chapters/getting_started.snbt` first, then fix the Air reward and subtitle without losing current live edits.

## Validate and rebuild

Requirements: Bash, Java 17, `jq`, `zip`, `unzip`, `sha256sum`, `sha512sum`, and Python 3. Rebuild the launcher after Java-source edits with `bash scripts/build-launcher.sh`.

```bash
bash scripts/validate.sh
bash scripts/build.sh
```

Static validation checks client/server quest parity, recipe/tag compatibility data, JEI pins, the local More Hitboxes JAR and class fingerprints, Crafty mod-management state, archive layouts, and checksums. It does not replace an in-game multiplayer test or a Spark profile.

## More Hitboxes performance investigation

More Hitboxes 1.9.2 has no per-mod or per-entity whitelist and no valid `fossils_only` option. Its Forge `Level` entity-query hooks are global. The 1.9.2.1 patch reduces unnecessary work without removing multipart Fossils support, but a fresh 60-second Spark profile is still required to quantify the improvement under the same laggy workload.
