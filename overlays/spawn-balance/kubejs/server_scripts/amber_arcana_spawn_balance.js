// Amber & Arcana - Spawn Balance Patch
// Minecraft 1.20.1 / Forge / KubeJS
//
// Goals:
// - Reduce normal mob spawn attempts by 50%.
// - Reduce Vampirism natural spawn attempts by an additional 50%.
//   Net vampire acceptance rate ~= 25% of current behavior.
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

  // First layer: 50% fewer normal mob spawn attempts across the pack.
  if (Math.random() < 0.50) {
    event.cancel()
    return
  }

  // Second layer: halve Vampirism again.
  // Combined with the global layer, ~25% of current vampire spawn attempts pass.
  if (id.startsWith('vampirism:') && Math.random() < 0.50) {
    event.cancel()
  }
})

console.info('[Amber & Arcana] Spawn balance patch loaded: global natural spawns -50%, Vampirism additional -50%, Mekanism babies disabled.')
