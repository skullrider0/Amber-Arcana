package com.github.darkpred.morehitboxes.mixin;

import com.github.darkpred.morehitboxes.api.MultiPart;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.llamalad7.mixinextras.sugar.Local;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.entity.EntityTypeTest;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.common.extensions.IForgeLevel;
import net.minecraftforge.entity.PartEntity;
import org.spongepowered.asm.mixin.Debug;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Predicate;

/**
 * Match the logic we add in fabric. MultiParts can only be added if the test is also true for the parent.
 */
@Debug(export = true)
@Mixin(Level.class)
public abstract class LevelMixin implements IForgeLevel {

    /*
     * Amber & Arcana performance patch v3.
     *
     * Forge's getPartEntities() is level-global. MoreHitboxes' typed entity-query
     * injection runs in extremely hot AI paths, so even a once-per-tick filtered
     * array still makes every nearby-mob query walk every MoreHitboxes part in
     * the loaded level.
     *
     * Build a spatial index once per game tick and bucket MoreHitboxes parts by
     * the 16x16 chunk columns touched by their bounding boxes. Normal AI queries
     * then scan only the buckets overlapped by the query AABB.
     */
    @Unique
    private long moreHitboxes$spatialCacheGameTime = Long.MIN_VALUE;

    @Unique
    private int moreHitboxes$spatialCacheSourceSize = -1;

    @Unique
    private Map<Long, PartEntity<?>[]> moreHitboxes$spatialCache = Map.of();

    @Unique
    private static long moreHitboxes$bucketKey(int chunkX, int chunkZ) {
        return ((long) chunkX << 32) ^ (chunkZ & 0xffffffffL);
    }

    @Unique
    private static int moreHitboxes$minChunk(double value) {
        return Mth.floor(value) >> 4;
    }

    @Unique
    private static int moreHitboxes$maxChunk(double value) {
        // Treat an AABB ending exactly on a chunk edge as belonging to the
        // preceding chunk, matching intersection semantics more closely.
        return Mth.floor(Math.nextDown(value)) >> 4;
    }

    @Unique
    private void moreHitboxes$rebuildSpatialCacheIfNeeded() {
        var allParts = getPartEntities();
        long gameTime = ((Level) (Object) this).getGameTime();
        int sourceSize = allParts.size();

        if (gameTime == moreHitboxes$spatialCacheGameTime
                && sourceSize == moreHitboxes$spatialCacheSourceSize) {
            return;
        }

        Map<Long, List<PartEntity<?>>> building = new HashMap<>();

        for (PartEntity<?> partEntity : allParts) {
            if (!(partEntity instanceof MultiPart<?>)) {
                continue;
            }

            AABB bounds = partEntity.getBoundingBox();
            int minChunkX = moreHitboxes$minChunk(bounds.minX);
            int maxChunkX = moreHitboxes$maxChunk(bounds.maxX);
            int minChunkZ = moreHitboxes$minChunk(bounds.minZ);
            int maxChunkZ = moreHitboxes$maxChunk(bounds.maxZ);

            for (int chunkX = minChunkX; chunkX <= maxChunkX; chunkX++) {
                for (int chunkZ = minChunkZ; chunkZ <= maxChunkZ; chunkZ++) {
                    building.computeIfAbsent(
                            moreHitboxes$bucketKey(chunkX, chunkZ),
                            ignored -> new ArrayList<>()
                    ).add(partEntity);
                }
            }
        }

        Map<Long, PartEntity<?>[]> finished = new HashMap<>(building.size() * 2);
        for (Map.Entry<Long, List<PartEntity<?>>> entry : building.entrySet()) {
            finished.put(entry.getKey(), entry.getValue().toArray(new PartEntity<?>[0]));
        }

        moreHitboxes$spatialCache = finished;
        moreHitboxes$spatialCacheGameTime = gameTime;
        moreHitboxes$spatialCacheSourceSize = sourceSize;
    }

    @Inject(method = "getEntities(Lnet/minecraft/world/entity/Entity;Lnet/minecraft/world/phys/AABB;Ljava/util/function/Predicate;)Ljava/util/List;",
            at = @At(value = "INVOKE", shift = At.Shift.AFTER, target = "Lnet/minecraft/world/level/entity/LevelEntityGetter;get(Lnet/minecraft/world/phys/AABB;Ljava/util/function/Consumer;)V"))
    public void limitMultiPartInEntityQuery(Entity pEntity, AABB pBoundingBox, Predicate<Entity> predicate, CallbackInfoReturnable<List<Entity>> cir, @Local List<Entity> list) {
        Set<Entity> set = new HashSet<>();
        for (Entity entity : list) {
            if (entity instanceof MultiPart<?> part && (part.getParent() == pEntity || (!predicate.test(part.getParent()) || !predicate.test(entity)))) {
                set.add(entity);
            }
        }
        list.removeIf(set::contains);
    }

    @WrapOperation(method = "getEntities(Lnet/minecraft/world/entity/Entity;Lnet/minecraft/world/phys/AABB;Ljava/util/function/Predicate;)Ljava/util/List;",
            at = @At(value = "INVOKE", target = "Ljava/util/function/Predicate;test(Ljava/lang/Object;)Z"))
    private boolean limitMultiPartInEntityQuery(Predicate<Entity> predicate, Object entity, Operation<Boolean> original) {
        if (entity instanceof MultiPart<?> part) {
            if (predicate.test(part.getParent())) {
                return original.call(predicate, entity);
            }
            return false;
        } else {
            return original.call(predicate, entity);
        }
    }

    @Inject(method = "getEntities(Lnet/minecraft/world/level/entity/EntityTypeTest;Lnet/minecraft/world/phys/AABB;Ljava/util/function/Predicate;)Ljava/util/List;", at = @At(value = "RETURN"))
    public <T extends Entity> void addMultiPartsToEntityQuery(EntityTypeTest<Entity, T> entityTypeTest, AABB area, Predicate<? super T> predicate, CallbackInfoReturnable<List<T>> cir, @Local List<Entity> list) {
        moreHitboxes$rebuildSpatialCacheIfNeeded();

        int minChunkX = moreHitboxes$minChunk(area.minX);
        int maxChunkX = moreHitboxes$maxChunk(area.maxX);
        int minChunkZ = moreHitboxes$minChunk(area.minZ);
        int maxChunkZ = moreHitboxes$maxChunk(area.maxZ);

        boolean multiBucket = minChunkX != maxChunkX || minChunkZ != maxChunkZ;
        Set<PartEntity<?>> seen = multiBucket
                ? java.util.Collections.newSetFromMap(new IdentityHashMap<>())
                : null;

        for (int chunkX = minChunkX; chunkX <= maxChunkX; chunkX++) {
            for (int chunkZ = minChunkZ; chunkZ <= maxChunkZ; chunkZ++) {
                PartEntity<?>[] bucket = moreHitboxes$spatialCache.get(moreHitboxes$bucketKey(chunkX, chunkZ));
                if (bucket == null) {
                    continue;
                }

                for (PartEntity<?> partEntity : bucket) {
                    if (seen != null && !seen.add(partEntity)) {
                        continue;
                    }
                    if (!partEntity.getBoundingBox().intersects(area)) {
                        continue;
                    }

                    T parent = entityTypeTest.tryCast(partEntity.getParent());
                    if (parent != null && !list.contains(parent) && predicate.test(parent)) {
                        list.add(parent);
                    }
                }
            }
        }
    }

    //TODO: Shelf if above works
    //Lambda mixin just doesn't want to work. 1st one doesn't apply in forge production and architectury dev(unless setting is set) and 2nd one doesn't apply in forge dev
    /*@WrapOperation(method = "lambda$getEntities$1",
            at = @At(value = "INVOKE", target = "Ljava/util/function/Predicate;test(Ljava/lang/Object;)Z"), require = 0)
    private static boolean limitMultiPartInEntityQuery2(Predicate<Entity> predicate, Object entity, Operation<Boolean> original) {
        if (entity instanceof MultiPart<?> part) {
            if (predicate.test(part.getParent())) {
                return original.call(predicate, entity);
            }
            return false;
        } else {
            return original.call(predicate, entity);
        }
    }

    @WrapOperation(method = "method_31593",
            at = @At(value = "INVOKE", target = "Ljava/util/function/Predicate;test(Ljava/lang/Object;)Z"), require = 0)
    private static boolean limitMultiPartInEntityQuery3(Predicate<Entity> predicate, Object entity, Operation<Boolean> original) {
        if (entity instanceof MultiPart<?> part) {
            if (predicate.test(part.getParent())) {
                return original.call(predicate, entity);
            }
            return false;
        } else {
            return original.call(predicate, entity);
        }
    }*/
}
