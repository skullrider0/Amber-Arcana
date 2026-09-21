// Amber & Arcana - Powah Thermo Generator cross-mod compatibility
// Minecraft 1.20.1 / Forge / Powah 5.0.11
//
// Custom Amber & Arcana thermo balance:
// - Create: Dragons Plus Dragon's Breath coolant: -20 C
// - Tinkers' Construct Blazing Blood heat source: 3500

const $PowahAPI = Java.loadClass('owmii.powah.api.PowahAPI')
const $ForgeRegistries = Java.loadClass('net.minecraftforge.registries.ForgeRegistries')
const $ResourceLocation = Java.loadClass('net.minecraft.resources.ResourceLocation')

function aaId(id) {
  return new $ResourceLocation(id)
}

function aaFluid(id) {
  return $ForgeRegistries.FLUIDS.getValue(aaId(id))
}

function aaBlock(id) {
  return $ForgeRegistries.BLOCKS.getValue(aaId(id))
}

// Create: Dragons Plus - Liquid Dragon's Breath
// Registered as a high-end Thermo Generator coolant at -20 C.
const dragonBreath = aaFluid('create_dragons_plus:dragon_breath')
if (dragonBreath != null) {
  $PowahAPI.registerCoolant(dragonBreath, -20)
  console.info("[Amber & Arcana] Powah compat: create_dragons_plus:dragon_breath registered as Thermo Generator coolant (-20 C).")
} else {
  console.warn("[Amber & Arcana] Powah compat: create_dragons_plus:dragon_breath was not found; coolant registration skipped.")
}

// Tinkers' Construct - Blazing Blood
// Registered as a very high-temperature Thermo Generator heat source at 3500.
const blazingBlood = aaBlock('tconstruct:blazing_blood')
if (blazingBlood != null) {
  $PowahAPI.registerHeatSource(blazingBlood, 3500)
  console.info("[Amber & Arcana] Powah compat: tconstruct:blazing_blood registered as Thermo Generator heat source (3500).")
} else {
  console.warn("[Amber & Arcana] Powah compat: tconstruct:blazing_blood block was not found; heat-source registration skipped.")
}
