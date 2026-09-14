# Recipe and Tag Analysis for 0.1.9-14

## Evidence

A fresh 0.1.9-13 Crafty server started on Java 17 and Forge 47.4.10. Every
Compat was absent and its previous 65 generated recipe failures did not recur.
The server accepted player connections and remained running.

The reload rejected 36 unique recipe IDs:

| Namespace | Count | Cause |
| --- | ---: | --- |
| `create` | 12 | Built-in BWG compatibility refers to renamed/removed BWG items. |
| `forbidden_arcanus` | 9 | Malformed cross-loader ingredients and removed internal items. |
| `create_things_and_misc` | 8 | Deleted internal items or absent optional-mod items. |
| `create_aquatic_ambitions` | 4 | Upgrade Aquatic coral item IDs no longer exist. |
| `alexsdelight` | 1 | Optional addon item is absent. |
| `rusticdelight` | 1 | Malformed ingredient. |
| `cgs` | 1 | Malformed JSON. |

The tag loader also rejected four source files/chains:

- Reborn Storage's `refinedstorage:parts/items` and
  `refinedstorage:disks/items` parents list three high-capacity item tiers that
  do not exist. Its high-capacity fluid tiers are valid and remain untouched.
- I Wanna Skate refers to nonexistent singular vanilla tags
  `minecraft:stone_stairs` and `minecraft:stone_slab`.
- Just Dire Things includes the nonexistent block
  `justdirethings:paradox_machine` in `paradox_deny`.

## Patch design

The KubeJS data pack has high resource priority on both client and server.
Version 0.1.9-14 uses that pack to override each already-invalid recipe with a
Forge-false conditional recipe. This prevents its broken serializer or missing
item from being evaluated while preserving the owning mod and every valid
recipe it supplies.

Four replacement tag files retain all valid entries while dropping or
correcting only nonexistent references. Client and server copies are generated
from one script and validated as identical.

## Runtime acceptance test

1. Import the 0.1.9-14 server package into a fresh Crafty instance.
2. Reach the ready state on Java 17 and Forge 47.4.10.
3. Confirm none of the 36 recipe IDs logs a parsing error.
4. Confirm none of the four repaired tags logs a missing reference.
5. Join using a fresh 0.1.9-14 client import.
6. Run `/reload` and repeat steps 3–4.
7. Test representative Create, Refined Storage, Just Dire Things, Forbidden &
   Arcanus, and ordinary crafting recipes.

Static validation cannot substitute for this runtime test.
