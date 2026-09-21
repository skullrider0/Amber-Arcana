// Amber & Arcana - Powah Thermo Generator cross-mod compatibility
// Minecraft 1.20.1 / Forge / Powah 5.0.11
//
// Dragon's Breath is intentionally a modest enhanced coolant.
// Blazing Blood is a stronger heat source than magma, but below Powah's
// Blazing Crystal Block, keeping the cross-mod combo useful without being extreme.

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
// Powah coolant temperature: -5 C.
// Powah 5.0.9+ uses coolant temperature in Thermo Generator generation,
// making this a modest upgrade over water without creating a huge multiplier.
const dragonBreath = aaFluid('create_dragons_plus:dragon_breath')
if (dragonBreath != null) {
  $PowahAPI.registerCoolant(dragonBreath, -5)
  console.info("[Amber & Arcana] Powah compat: create_dragons_plus:dragon_breath registered as Thermo Generator coolant (-5 C).")
} else {
  console.warn("[Amber & Arcana] Powah compat: create_dragons_plus:dragon_breath was not found; coolant registration skipped.")
}

// Tinkers' Construct - Blazing Blood
// Heat 1500: hotter than the usual magma-block class of heat source,
// but intentionally below Powah's high-end Blazing Crystal Block.
const blazingBlood = aaBlock('tconstruct:blazing_blood')
if (blazingBlood != null) {
  $PowahAPI.registerHeatSource(blazingBlood, 1500)
  console.info("[Amber & Arcana] Powah compat: tconstruct:blazing_blood registered as Thermo Generator heat source (1500).")
} else {
  console.warn("[Amber & Arcana] Powah compat: tconstruct:blazing_blood block was not found; heat-source registration skipped.")
}
