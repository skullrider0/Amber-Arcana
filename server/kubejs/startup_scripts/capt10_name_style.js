// Amber & Arcana - Capt10_america display-name override
// Keeps Vampirism faction coloring enabled for everyone else.
// This uses explicit per-character styles so Vampirism's later faction color
// does not wash the custom red/black pattern into vampire purple.

const CAPT10_TARGET_NAME = 'Capt10_america'

function amberArcanaCapt10StyledName() {
  const out = Text.of('')

  // Obfuscated characters render as constantly changing symbols.
  out.append(Text.of('X').color('red').obfuscated(true))

  for (let i = 0; i < CAPT10_TARGET_NAME.length; i++) {
    out.append(
      Text.of(CAPT10_TARGET_NAME.charAt(i))
        .color((i % 2) === 0 ? 'red' : 'black')
    )
  }

  out.append(Text.of('X').color('red').obfuscated(true))
  return out
}

function amberArcanaIsCapt10(player) {
  return player != null &&
    String(player.getGameProfile().getName()) === CAPT10_TARGET_NAME
}

// Chat / nametag / normal player display name.
// Vampirism listens to the same Forge event at LOW priority and applies a
// faction color to the root component. Every visible piece here has its own
// explicit color, so the red/black styling is retained.
ForgeEvents.onEvent(
  'net.minecraftforge.event.entity.player.PlayerEvent$NameFormat',
  event => {
    if (amberArcanaIsCapt10(event.getEntity())) {
      event.setDisplayname(amberArcanaCapt10StyledName())
    }
  }
)

// Server-provided tab-list name. The client-side companion script below also
// reapplies this because FTB Essentials can send its own tab-name packet.
ForgeEvents.onEvent(
  'net.minecraftforge.event.entity.player.PlayerEvent$TabListNameFormat',
  event => {
    if (amberArcanaIsCapt10(event.getEntity())) {
      event.setDisplayName(amberArcanaCapt10StyledName())
    }
  }
)
