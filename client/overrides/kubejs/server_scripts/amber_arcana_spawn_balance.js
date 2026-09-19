// Amber & Arcana - Spawn Balance Patch
// Minecraft 1.20.1 / Forge / KubeJS
//
// Goals:
// - Reduce normal mob spawn attempts by 50%.
// - Keep Vampire Barons exempt from spawn thinning.
// - Allow other Vampirism natural spawn attempts at 30% of unpatched behavior.
// - Reduce Ice & Fire natural spawn attempts by an additional 70%.
//   Net Ice & Fire acceptance rate ~= 15% of unpatched behavior.
//   This explicitly includes iceandfire:pixie.
// - Reduce Untamed Wilds natural spawn attempts by an additional 50%.
//   Net Untamed Wilds acceptance rate ~= 25% of unpatched behavior.
// - Completely disable Mekanism Additions baby mobs.
// - Leave mob spawners, breeding, commands, summons, and existing mobs alone.
//
// This is intentionally server-side only and does not modify MoreHitboxes.

const AA_MEKANISM_BABIES = [
  'mekanismadditions:baby_creeper',
  'mekanismadditions:baby_enderman',
  'mekanismadditions:baby_skeleton',
  'mekanismadditions:baby_stray',
  'mekanismadditions:baby_wither_skeleton'
]

// Completely disable Mekanism Additions baby mobs regardless of spawn source.
EntityEvents.spawned(event => {
  const id = String(event.entity.type)
  if (AA_MEKANISM_BABIES.includes(id)) {
    event.cancel()
  }
})

// Thin normal spawn checks before entities enter the world.
// KubeJS/Forge exposes a nullable spawner on this event.
// If a vanilla/modded mob spawner is responsible, leave it untouched.
EntityEvents.checkSpawn(event => {
  let spawner = null

  try {
    spawner = event.spawner
  } catch (ignored) {
    // Older KubeJS builds may not expose the property cleanly.
    // In that case this event is still primarily used by normal spawn checks.
  }

  if (spawner != null) {
    return
  }

  const id = String(event.entity.type)

  // Vampire Barons are intentionally exempt from all Amber spawn thinning.
  if (id === 'vampirism:vampire_baron') {
    return
  }

  // Vampirism: allow exactly ~30% of normal natural spawn attempts.
  // Handle this before the global layer so reductions do not multiply.
  if (id.startsWith('vampirism:')) {
    if (Math.random() < 0.70) {
      event.cancel()
    }
    return
  }

  // First layer: 50% fewer normal mob spawn attempts across the rest of the pack.
  if (Math.random() < 0.50) {
    event.cancel()
    return
  }

  // Ice & Fire: remove another 70% of attempts that survived the global layer.
  // 50% global pass rate * 30% Ice & Fire pass rate = ~15% of unpatched throughput.
  // iceandfire:pixie is intentionally included here.
  if (id.startsWith('iceandfire:') && Math.random() < 0.70) {
    event.cancel()
    return
  }

  // Untamed Wilds: halve surviving natural spawns again.
  // Combined with the global layer, ~25% of unpatched attempts pass.
  if (id.startsWith('untamedwilds:') && Math.random() < 0.50) {
    event.cancel()
    return
  }

})

console.info('[Amber & Arcana] Spawn balance patch loaded: global -50%, Vampirism 30% except Baron (exempt), Ice & Fire additional -70% (pixies included), Untamed Wilds additional -50%, Mekanism babies disabled.')
