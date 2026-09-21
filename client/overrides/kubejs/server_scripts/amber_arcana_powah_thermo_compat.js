// Amber & Arcana - Powah Thermo Generator cross-mod compatibility
// Minecraft 1.20.1 / Forge / Powah 5.0.11
//
// Custom balance:
// - Create: Dragons Plus Liquid Dragon's Breath: -20 coolant
// - Tinkers' Construct Blazing Blood: 3500 heat
//
// IMPORTANT for Powah 5.0.11:
// registerCoolant() and registerHeatSource() expect ResourceLocation IDs.
// Do not pass Fluid or Block objects.

const $PowahAPI = Java.loadClass('owmii.powah.api.PowahAPI')
const $ResourceLocation = Java.loadClass('net.minecraft.resources.ResourceLocation')
const $BuiltInRegistries = Java.loadClass('net.minecraft.core.registries.BuiltInRegistries')

const dragonBreathId = new $ResourceLocation('create_dragons_plus', 'dragon_breath')
const blazingBloodBlockId = new $ResourceLocation('tconstruct', 'blazing_blood_fluid')

// Create: Dragons Plus - Liquid Dragon's Breath
// -20 gives Powah 5.0.11 a cooling ratio of 10.5x.
if ($BuiltInRegistries.FLUID.containsKey(dragonBreathId)) {
  $PowahAPI.registerCoolant(dragonBreathId, -20)
  console.info("[Amber & Arcana] Powah compat: create_dragons_plus:dragon_breath registered as Thermo coolant (-20).")
} else {
  console.warn("[Amber & Arcana] Powah compat: create_dragons_plus:dragon_breath is not present in the fluid registry. Check the installed Create: Dragons Plus version/feature config.")
}

// Tinkers' Construct - Blazing Blood placed-fluid block.
// Tinkers uses tconstruct:blazing_blood_fluid for the world block,
// while tconstruct:blazing_blood is the fluid registry ID.
if ($BuiltInRegistries.BLOCK.containsKey(blazingBloodBlockId)) {
  $PowahAPI.registerHeatSource(blazingBloodBlockId, 3500)
  console.info("[Amber & Arcana] Powah compat: tconstruct:blazing_blood_fluid registered as Thermo heat source (3500).")
} else {
  console.warn("[Amber & Arcana] Powah compat: tconstruct:blazing_blood_fluid is not present in the block registry.")
}
