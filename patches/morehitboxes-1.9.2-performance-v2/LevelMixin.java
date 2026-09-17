package com.github.darkpred.morehitboxes.mixin;

import com.github.darkpred.morehitboxes.api.MultiPart;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.llamalad7.mixinextras.sugar.Local;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.common.extensions.IForgeLevel;
import org.spongepowered.asm.mixin.Debug;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Predicate;

/**
 * Preserve multipart filtering for ordinary entity collision/projectile queries.
 *
 * Amber performance v2 intentionally does not inject into
 * Level#getEntities(EntityTypeTest, AABB, Predicate). Spark profiling showed
 * that global typed-query hook walking every Forge PartEntity for AI proximity
 * searches consumed roughly a quarter of the dedicated-server thread.
 */
@Debug(export = true)
@Mixin(Level.class)
public abstract class LevelMixin implements IForgeLevel {

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
                // Parent also needs to pass the test. This preserves behavior for
                // collision/projectile queries such as piercing arrows.
                return original.call(predicate, entity);
            }
            return false;
        }
        return original.call(predicate, entity);
    }
}
