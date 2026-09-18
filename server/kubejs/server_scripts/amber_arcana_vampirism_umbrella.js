// Amber & Arcana - Vampirism umbrella recipe
// Adds a survival crafting recipe for Vampirism's umbrella.

ServerEvents.recipes(event => {
  event.shaped('vampirism:umbrella', [
    'WWW',
    ' S ',
    ' I '
  ], {
    W: 'minecraft:black_wool',
    S: 'minecraft:stick',
    I: 'minecraft:iron_ingot'
  }).id('amber_arcana:vampirism_umbrella')
})
