package dev.wateralt.mc.tfa_dims.mixin;

import dev.wateralt.mc.tfa_dims.Dimensions;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.world.LightType;
import net.minecraft.world.World;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyArg;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(LivingEntity.class)
public abstract class LivingEntityMixin {
  @Inject(method = "tickMovement", at = @At("HEAD"))
  public void tick(CallbackInfo ci) {
    Entity that = (Entity) (Object) this;
    World world = that.getEntityWorld();
    if(world.getRegistryKey().equals(Dimensions.AQUILO_DIM) && that.canFreeze()) {
      if(world.getLightLevel(LightType.BLOCK, that.getBlockPos()) < 12) {
        that.setInPowderSnow(true);
        that.setFrozenTicks(Math.min(that.getMinFreezeDamageTicks() * 5, that.getFrozenTicks() + 1));
      }
      if(world.getLightLevel(LightType.BLOCK, that.getBlockPos()) == 15) {
        that.setFrozenTicks(Math.max(0, that.getFrozenTicks() - 5));
      }
      if(that.isTouchingWater()) {
        that.setInPowderSnow(true);
        that.setFrozenTicks(Math.min(that.getMinFreezeDamageTicks() * 5, that.getFrozenTicks() + 5));
      }
    }
  }
  
  @ModifyArg(method = "tickMovement", at = @At(value = "INVOKE", target = "Lnet/minecraft/entity/LivingEntity;damage(Lnet/minecraft/server/world/ServerWorld;Lnet/minecraft/entity/damage/DamageSource;F)Z", ordinal = 0), index = 2)
  public float modifyFreezeDamage(float amount) {
    LivingEntity that = (LivingEntity) (Object) this;
    return amount * (float)that.getFrozenTicks() / that.getMinFreezeDamageTicks();
  }
}
