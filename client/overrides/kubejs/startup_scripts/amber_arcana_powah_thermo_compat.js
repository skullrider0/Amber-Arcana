// Amber & Arcana - Powah Thermo Generator cross-mod compatibility
// Minecraft 1.20.1 / Forge / Powah 5.0.11
//
// Custom balance:
// - Create: Central Kitchen Liquid Dragon's Breath: -20 coolant
// - Tinkers' Construct Blazing Blood: 3500 heat
//
// IMPORTANT:
// KubeJS startup scripts themselves load before Forge finishes populating every
// modded block/fluid registry. The actual Powah registrations therefore run in
// StartupEvents.postInit(), after mod initialization, but still during startup.

const $PowahAPI = Java.loadClass('owmii.powah.api.PowahAPI')
const $ResourceLocation = Java.loadClass('net.minecraft.resources.ResourceLocation')
const $BuiltInRegistries = Java.loadClass('net.minecraft.core.registries.BuiltInRegistries')

StartupEvents.postInit(event => {
  const dragonBreathId = new $ResourceLocation('create_central_kitchen', 'dragon_breath')
  const blazingBloodBlockId = new $ResourceLocation('tconstruct', 'blazing_blood_fluid')

  // Create: Central Kitchen - Liquid Dragon's Breath
  // Powah 5.0.11 cooling ratio at -20 = (1 + abs(-20)) / 2 = 10.5x.
  if ($BuiltInRegistries.FLUID.containsKey(dragonBreathId)) {
    $PowahAPI.registerCoolant(dragonBreathId, -20)
    console.info("[Amber & Arcana] Powah compat POST-INIT: create_central_kitchen:dragon_breath registered as Thermo coolant (-20).")
  } else {
    console.warn("[Amber & Arcana] Powah compat POST-INIT: create_central_kitchen:dragon_breath is still missing from the fluid registry.")
  }

  // Tinkers' Construct - Blazing Blood placed-fluid block.
  if ($BuiltInRegistries.BLOCK.containsKey(blazingBloodBlockId)) {
    $PowahAPI.registerHeatSource(blazingBloodBlockId, 3500)
    console.info("[Amber & Arcana] Powah compat POST-INIT: tconstruct:blazing_blood_fluid registered as Thermo heat source (3500).")
  } else {
    console.warn("[Amber & Arcana] Powah compat POST-INIT: tconstruct:blazing_blood_fluid is still missing from the block registry.")
  }
})
