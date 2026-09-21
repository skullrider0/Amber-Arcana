// Amber & Arcana - Powah JEI display compatibility
// Client only.
//
// Powah 5.0.11 correctly uses tconstruct:blazing_blood_fluid as the placed
// Thermo Generator heat-source block, but its JEI category only discovers
// block heat sources that have BlockItems. Tinkers' placed fluid block has
// no BlockItem, so it works in-world but is omitted from JEI.
//
// Do NOT modify PowahAPI.HEAT_SOURCES with the fluid ID here; doing that can
// break Powah's Heat Sources category. Instead, inject one display recipe
// directly after JEI's runtime becomes available.

const $HeatSourceCategory = Java.loadClass('owmii.powah.compat.jei.HeatSourceCategory')
const $HeatSourceRecipe = Java.loadClass('owmii.powah.compat.jei.HeatSourceCategory$Recipe')
const $BuiltInRegistries = Java.loadClass('net.minecraft.core.registries.BuiltInRegistries')
const $ResourceLocation = Java.loadClass('net.minecraft.resources.ResourceLocation')

JEIEvents.addItems(event => {
  const blazingBloodId = new $ResourceLocation('tconstruct', 'blazing_blood')

  if (!$BuiltInRegistries.FLUID.containsKey(blazingBloodId)) {
    console.warn('[Amber & Arcana] Powah JEI compat: tconstruct:blazing_blood fluid is missing; JEI entry skipped.')
    return
  }

  if (global.jeiRuntime == null) {
    console.warn('[Amber & Arcana] Powah JEI compat: JEI runtime is unavailable; JEI entry skipped.')
    return
  }

  const blazingBlood = $BuiltInRegistries.FLUID.get(blazingBloodId)
  const recipe = new $HeatSourceRecipe(null, blazingBlood, 3500)

  global.jeiRuntime.getRecipeManager().addRecipes(
    $HeatSourceCategory.TYPE,
    [recipe]
  )

  console.info('[Amber & Arcana] Powah JEI compat: added Blazing Blood heat-source display recipe (3500).')
})
