package dev.wateralt.mc.tfa_dims;

import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.util.Identifier;
import net.minecraft.world.World;

public class Dimensions {
  public static final RegistryKey<World> SKY_DIM = RegistryKey.of(RegistryKeys.WORLD, Identifier.of("tfadim:sky"));
  public static final RegistryKey<World> AQUILO_DIM = RegistryKey.of(RegistryKeys.WORLD, Identifier.of("tfadim:aquilo"));
}
