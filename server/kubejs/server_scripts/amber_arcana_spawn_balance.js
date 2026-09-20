// Amber & Arcana - Spawn Balance Patch
// Minecraft 1.20.1 / Forge / KubeJS
//
// Goals:
// - Restore vanilla Minecraft mobs (passive + monsters) to 100% of normal natural spawn attempts.
// - Keep Vampire Barons exempt from spawn thinning.
// - Allow other Vampirism natural spawn attempts at 30% of unpatched behavior.
// - Reduce other modded mob spawn attempts by 50%.
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
EntityEvents.checkSpawn(event => {
  let spawner = null

  try {
    spawner = event.spawner
  } catch (ignored) {
    // Older KubeJS builds may not expose the property cleanly.
  }

  if (spawner != null) {
    return
  }

  const id = String(event.entity.type)

  // Vanilla Minecraft mobs now use normal, unthinned spawn behavior.
  // This includes hostile monsters, passive animals, ambient mobs, and water mobs.
  if (id.startsWith('minecraft:')) {
    return
  }

  // Vampire Barons are intentionally exempt from all Amber spawn thinning.
  if (id === 'vampirism:vampire_baron') {
    return
  }

  // Vampirism: allow exactly ~30% of normal natural spawn attempts.
  // Handle this before the global modded-mob layer so reductions do not multiply.
  if (id.startsWith('vampirism:')) {
    if (Math.random() < 0.70) {
      event.cancel()
    }
    return
  }

  // Other modded mobs: 50% fewer normal natural spawn attempts.
  if (Math.random() < 0.50) {
    event.cancel()
    return
  }

  // Ice & Fire: remove another 70% of attempts that survived the modded layer.
  // 50% base pass rate * 30% Ice & Fire pass rate = ~15% of unpatched throughput.
  if (id.startsWith('iceandfire:') && Math.random() < 0.70) {
    event.cancel()
    return
  }

  // Untamed Wilds: halve surviving natural spawns again.
  // Combined with the modded layer, ~25% of unpatched attempts pass.
  if (id.startsWith('untamedwilds:') && Math.random() < 0.50) {
    event.cancel()
    return
  }
})

console.info('[Amber & Arcana] Spawn balance patch loaded: vanilla 100%, other modded mobs 50%, Vampirism 30% except Baron (exempt), Ice & Fire ~15% (pixies included), Untamed Wilds ~25%, Mekanism babies disabled.')
