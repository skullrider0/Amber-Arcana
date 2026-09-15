# MoreHitboxes 1.9.2 performance review — Amber & Arcana

## Scope

This experiment targets the exact MoreHitboxes 1.9.2 source commit used by Amber & Arcana's Fossils dependency:

- Upstream: `DarkPred/MoreHitboxes`
- Minecraft: 1.20.1
- Forge: 47.x
- Baseline commit: `bbe929da2bb5480e83ba266bf3138e431f196d3f`
- Baseline version: 1.9.2
- Experimental version: 1.9.2.1

The production pack remains unchanged while this branch is tested.

## Hot path 1: typed Level.getEntities queries scan every Forge PartEntity

`forge/.../mixin/LevelMixin.java` injects into typed `Level.getEntities(EntityTypeTest, AABB, Predicate)` and loops over `getPartEntities()` on every call.

Baseline order for every MoreHitboxes part:

1. Cast the parent through `EntityTypeTest.tryCast`.
2. Search the query result with `list.contains(parent)`.
3. Test whether the part bounding box intersects the query AABB.
4. Run the caller predicate.

Most Minecraft/AI queries use a small local AABB, so distant multipart hitboxes should be rejected before the cast, linear list search, and predicate.

### v1 change

Perform the bounding-box intersection test immediately after confirming the part belongs to MoreHitboxes. Only intersecting parts proceed to casting, `list.contains`, and the predicate.

This preserves query results while reducing work per global part scanned.

## Hot path 2: every multipart Mob moves every custom hitbox every aiStep

`forge/.../mixin/MobMixin.java` runs after every `Mob.aiStep()` and calls `MultiPart.updatePosition()` for every custom part.

`MultiPart.updatePosition()` computes the new hitbox position and calls `Entity.setPos()` unconditionally, including when the calculated position is identical to the current position.

### v1 change

Keep all existing position calculations and old-position bookkeeping, but skip `Entity.setPos()` when X/Y/Z are exactly unchanged.

This is intentionally conservative. It does not reduce hitbox update frequency and does not approximate animation state.

## Why Fossils amplifies the cost

Fossils and Archeology Revival's `Prehistoric` base entity implements MoreHitboxes multipart support and creates `EntityHitboxData` for prehistoric mobs. A collection of dinosaurs therefore creates many Forge `PartEntity` hitboxes. Cost grows with both the number of dinosaur hitbox parts and the number of entity queries performed by the rest of the modpack.

## Test plan

1. Verify the patched Forge jar starts on both client and dedicated server with Fossils 9.3.4.0.
2. Verify dinosaur body/head hitboxes still take damage correctly.
3. Verify arrows/projectiles still hit multipart dinosaurs correctly.
4. Verify dinosaur melee/attack-box behavior still works.
5. Capture a 60-second Spark profile in the same world/area used for the 0.1.9-20/0.1.9-21 comparison.
6. Compare:
   - `Level.getEntities`
   - MoreHitboxes `LevelMixin`
   - `Mob.aiStep`
   - `MultiPart.updatePosition`
   - Forge entity-section movement callbacks
   - MSPT / TPS

## Follow-up candidates if v1 is not enough

- Cache/deduplicate multipart parents per typed entity query after the AABB filter.
- Add a spatial index for MoreHitboxes parts instead of scanning the world's full PartEntity collection.
- Avoid vector allocation in static-offset hitbox transforms.
- Add a namespace allow-list such as `fossil` for pack-specific deployments.
- Add parent-pose caching so static dinosaurs do not recompute all custom hitbox transforms each tick.

The spatial index and pose-cache ideas are higher-risk than v1 and should only be attempted after profiling the conservative patch.
