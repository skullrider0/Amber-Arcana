// Amber & Arcana 0.1.9-17
// Keep Artifacts installed, but prevent Eternal Steak from generating in chest loot.
LootJS.modifiers(event => {
    event.addLootTypeModifier(LootType.CHEST)
        .removeLoot('artifacts:eternal_steak')
})
