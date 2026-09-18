package com.github.darkpred.morehitboxes.mixin;

import com.github.darkpred.morehitboxes.api.MultiPart;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.llamalad7.mixinextras.sugar.Local;
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
import java.util.Collection;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Predicate;

/**
 * Match the logic we add in fabric. MultiParts can only be added if the test is also true for the parent.
 */
@Debug(export = true)
@Mixin(Level.class)
public abstract class LevelMixin implements IForgeLevel {

    /*
     * Forge's getPartEntities() contains multipart pieces from every mod in the
     * level. Scanning that global collection for every typed entity query turns
     * unrelated multipart mobs (notably Ice & Fire dragons) into a multiplier
     * on normal mob AI.
     *
     * Keep a per-Level, per-game-tick snapshot containing only MoreHitboxes
     * MultiParts. A source-size change forces a same-tick rebuild for the common
     * spawn/despawn case. This preserves the original query semantics while
     * removing unrelated Forge PartEntity instances from the hot loop.
     */
    @Unique
    private long moreHitboxes$partCacheGameTime = Long.MIN_VALUE;

    @Unique
    private int moreHitboxes$partCacheSourceSize = -1;

    @Unique
    private PartEntity<?>[] moreHitboxes$partCache = new PartEntity<?>[0];

    @Unique
    private PartEntity<?>[] moreHitboxes$getCachedParts() {
        Collection<PartEntity<?>> allParts = getPartEntities();
        long gameTime = ((Level) (Object) this).getGameTime();
        int sourceSize = allParts.size();

        if (gameTime != moreHitboxes$partCacheGameTime || sourceSize != moreHitboxes$partCacheSourceSize) {
            List<PartEntity<?>> filtered = new ArrayList<>();
            for (PartEntity<?> partEntity : allParts) {
                if (partEntity instanceof MultiPart<?>) {
                    filtered.add(partEntity);
                }
            }
            moreHitboxes$partCache = filtered.toArray(new PartEntity<?>[0]);
            moreHitboxes$partCacheGameTime = gameTime;
            moreHitboxes$partCacheSourceSize = sourceSize;
        }

        return moreHitboxes$partCache;
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
                //Parent also needs to pass test. This way things like piercing in AbstractArrow work
                return original.call(predicate, entity);
            }
            return false;
        } else {
            return original.call(predicate, entity);
        }
    }

    @Inject(method = "getEntities(Lnet/minecraft/world/level/entity/EntityTypeTest;Lnet/minecraft/world/phys/AABB;Ljava/util/function/Predicate;)Ljava/util/List;", at = @At(value = "RETURN"))
    public <T extends Entity> void addMultiPartsToEntityQuery(EntityTypeTest<Entity, T> entityTypeTest, AABB area, Predicate<? super T> predicate, CallbackInfoReturnable<List<T>> cir, @Local List<Entity> list) {
        for (PartEntity<?> partEntity : moreHitboxes$getCachedParts()) {
            // Most entity queries are local. Reject distant MoreHitboxes parts
            // before parent type casts, linear result-list searches, or caller predicates.
            if (!partEntity.getBoundingBox().intersects(area)) {
                continue;
            }
            T parent = entityTypeTest.tryCast(partEntity.getParent());
            //No check for the MultiPart entity itself since that doesn't make much sense
            if (parent != null && !list.contains(parent) && predicate.test(parent)) {
                list.add(parent);
            }
        }
    }

    //TODO: Shelf if above works
    //Lambda mixin just doesn't want to work. 1st one doesn't apply in forge production and architectury dev(unless setting is set) and 2nd one doesn't apply in forge dev
    /*@WrapOperation(method = "lambda$getEntities$1",
            at = @At(value = "INVOKE", target = "Ljava/util/function/Predicate;test(Ljava/lang/Object;)Z"), require = 0)
    private static boolean limitMultiPartInEntityQuery2(Predicate<Entity> predicate, Object entity, Operation<Boolean> original) {
        if (entity instanceof MultiPart<?> part) {
            MoreHitboxesMod.LOGGER.info("Testing MultiPart2 {}", part.getEntity().getId());
            MoreHitboxesMod.LOGGER.info("Would work2: {} {}", predicate.test(part.getParent()), original.call(predicate, entity));
            if (predicate.test(part.getParent())) {
                //Parent also needs to pass test. This way things like piercing in AbstractArrow work
                return original.call(predicate, entity);
            }
            return false;
        } else {
            return original.call(predicate, entity);
        }
    }

    //For architectury since it still maps to yarn names in bytecode
    @WrapOperation(method = "method_31593",
            at = @At(value = "INVOKE", target = "Ljava/util/function/Predicate;test(Ljava/lang/Object;)Z"), require = 0)
    private static boolean limitMultiPartInEntityQuery3(Predicate<Entity> predicate, Object entity, Operation<Boolean> original) {
        if (entity instanceof MultiPart<?> part) {
            if (predicate.test(part.getParent())) {
                //Parent also needs to pass test. This way things like piercing in AbstractArrow work
                return original.call(predicate, entity);
            }
            return false;
        } else {
            return original.call(predicate, entity);
        }
    }*/
}
