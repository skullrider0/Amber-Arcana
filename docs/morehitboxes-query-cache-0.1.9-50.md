# More Hitboxes query-cache performance patch — 0.1.9-50

## Why this patch exists

The September 18, 2026 Spark capture from the live Amber & Arcana server showed the Forge More Hitboxes typed entity-query hook as a major main-thread hotspot. The profile was roughly 120 seconds long, with about 7.3 TPS and about 130 ms median MSPT. Entity ticking dominated the server thread, while `LevelMixin.addMultiPartsToEntityQuery` accounted for roughly 22% of sampled main-thread time.

The same capture had many unrelated Forge multipart entities from Ice & Fire. More Hitboxes 1.9.2 scans Forge's level-wide `getPartEntities()` collection for every typed entity query, even though it only needs entries implementing More Hitboxes' `MultiPart` interface.

## Change

Amber More Hitboxes 1.9.2.2 keeps the existing 1.9.2.1 unchanged-position optimization and adds a per-`Level`, per-game-tick cache of only More Hitboxes-owned `PartEntity` objects.

Before:

- every typed entity query iterates the full Forge multipart collection;
- unrelated Ice & Fire multipart pieces are repeatedly visited;
- only after visiting each entry can More Hitboxes reject non-`MultiPart` entries.

After:

- the full Forge multipart collection is filtered at most once per level tick;
- the hot query path iterates only More Hitboxes-owned parts;
- the existing bounding-box-first rejection remains;
- Fossils and Archeology Revival keeps the `morehitboxes` dependency and multipart parent-query behavior.

A source-size change forces a same-tick cache rebuild for normal multipart spawn/despawn activity.

## Compatibility guardrails

The build starts from upstream More Hitboxes 1.9.2 commit
`bbe929da2bb5480e83ba266bf3138e431f196d3f`.

Only these runtime classes are transplanted into the official 1.9.2 JAR:

- `com.github.darkpred.morehitboxes.mixin.LevelMixin`
- `com.github.darkpred.morehitboxes.api.MultiPart`

The official 1.9.2 client `MinecraftMixin` and `mixins.morehitboxes.refmap.json` must remain byte-for-byte unchanged.

Minecraft stays at 1.20.1, Forge stays at 47.4.10, and no quest/world/player data is changed.

## Acceptance matrix

| Check | Expected |
| --- | --- |
| Exact upstream source pinned | PASS in CI |
| Forge 1.20.1 JAR compiles on Java 17 | PASS in CI |
| Official client MinecraftMixin unchanged | PASS in CI |
| Official mixin refmap unchanged | PASS in CI |
| Patched LevelMixin differs from official | PASS in CI |
| Patched MultiPart differs from official | PASS in CI |
| Client/server pack validation | PASS before merge |
| Fresh Forge dedicated-server startup | Required after deployment |
| Fresh client login and Fossils multipart hit test | Required after deployment |
| 60–120 second Spark profile under comparable load | Required after deployment |

## Runtime success criteria

The main criterion is not a specific synthetic benchmark number. Under a comparable live workload, `addMultiPartsToEntityQuery` should cease to be a dominant server-thread hotspot and should no longer scale with unrelated Ice & Fire multipart population.

Record post-update TPS/MSPT, entity counts, and a fresh Spark profile before considering additional entity-AI reductions.
