# Amber & Arcana Checklist

## Source recovery

- [ ] Add the authoritative `Amber-and-Arcana-0.1.0-alpha-CurseForge.zip`.
- [ ] Verify the archive hash and preserve an untouched source copy.
- [ ] Confirm manifest, overrides, configs, scripts, quests, and server files.
- [ ] Confirm no secrets, worlds, player data, or access tokens are included.

## Baseline

- [ ] Confirm Minecraft 1.20.1.
- [ ] Confirm Forge 47.4.10.
- [ ] Confirm Java 17.
- [ ] Generate client and server mod inventories.
- [ ] Record a clean baseline startup and join attempt.

## Recipe/tag investigation

- [ ] Compare client and server JAR filenames and versions.
- [ ] Compare mod IDs and dependencies.
- [ ] Compare `config/` and `defaultconfigs/`.
- [ ] Compare KubeJS scripts and generated data.
- [ ] Compare datapacks, recipes, and tags.
- [ ] Locate the first relevant error, not only cascading errors.
- [ ] Identify the source of the red-X/incompatible-version status.
- [ ] Test `/reload` and representative broken recipes on a test copy.

## Requested changes

- [ ] Keep Just Dire Things.
- [ ] Keep DecoCraft.
- [ ] Verify REI availability and integrations for Forge 1.20.1.
- [ ] Replace JEI only after dependency checks.
- [ ] Remove Ad Astra and unused exclusive dependencies.
- [ ] Remove AmbientSounds and unused exclusive dependencies.
- [ ] Remove The Aether and unused exclusive dependencies.
- [ ] Remove stale quest/config/script/tag/recipe/worldgen references.

## Quality gates

- [ ] Client launches.
- [ ] Dedicated server launches.
- [ ] Client joins server.
- [ ] No fatal registry/network mismatch.
- [ ] No recipe/tag validation failures attributable to pack files.
- [ ] Existing-world copy loads after backup.
- [ ] New world generates correctly.
- [ ] Core magic, exploration, building, creature, and progression loops work.
- [ ] Quest dependencies are valid.

## Distribution

- [ ] Produce valid CurseForge client manifest.
- [ ] Produce Crafty 4 server import.
- [ ] Generate mod/version inventory and checksums.
- [ ] Write changelog and known issues.
- [ ] Tag the tested alpha release.
- [ ] Start the next quest-line milestone.
