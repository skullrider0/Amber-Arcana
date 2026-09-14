# Amber & Arcana Goal Map

Updated: 2026-09-14
Baseline: 0.1.9-14 / Minecraft 1.20.1 / Forge 47.4.10

Status: `[done]`, `[active]`, `[next]`, `[later]`, `[blocked]`.

## North star

Ship a stable, reproducible client/server modpack where a fresh CurseForge client can join a fresh Crafty server without registry, recipe, tag, channel, or version warnings, while preserving the intended progression and existing quest IDs.

## G1 — Reproducible baseline `[active]`

Goal: prove that the repository can reproduce the exact 0.1.9-14 packages.

- `[done]` Keep matching client and server sources in one repository.
- `[done]` Preserve release ZIPs and SHA-256 checksums.
- `[done]` Record manifest, server-mod, quest, and dependency validation.
- `[next]` Import the client ZIP into a clean CurseForge profile.
- `[next]` Import the server ZIP into a new Crafty instance.
- `[next]` Capture client and server logs from the same test session.

Acceptance gate: clean imports boot on Java 17, produce no missing required dependency, and the packaged files match their recorded checksums.

## G2 — Client/server compatibility `[active]`

Goal: eliminate the red-X/incompatible-server indicator and prove registry/network parity.

- `[next]` Compare the final loaded mod IDs and versions from both logs, not just manifests.
- `[next]` Compare Forge network channels and accepted version predicates.
- `[next]` Compare registry counts and datapack/resource-pack selections.
- `[next]` Test a connection with a brand-new player and no cached server resource pack.
- `[next]` Reproduce or clear the oversized packet symptom (`unable to fit 2202990 into 3`).
- `[later]` Add an automated report that classifies client-only, server-only, required-both, and version-mismatched mods.

Acceptance gate: the multiplayer list shows compatible status, the client joins twice after restart, and neither log reports rejected channels or registry synchronization errors.

## G3 — Recipe and item-tag integrity `[active]`

Goal: remove all actionable recipe/tag errors and verify recipe viewing without JEI.

- `[done]` Remove Every Compat, a major source of generated invalid recipe JSON.
- `[done]` Replace JEI with client-only REI 12.1.785.
- `[done]` Remove Polymorph because it hard-requires JEI.
- `[next]` Capture the first recipe/tag failure from a fresh server boot with complete stack context.
- `[next]` Group failures by owning namespace and missing item/tag.
- `[next]` Verify each referenced item exists in the loaded registry on both sides.
- `[next]` Test `/reload`, recipe book use, crafting, and REI lookup on a clean world.
- `[later]` Add a generated compatibility datapack only for confirmed bad recipes/tags; avoid blanket recipe removal.

Acceptance gate: no unresolved tag entries, no invalid recipe cascade, `/reload` succeeds, and representative crafting/REI checks pass.

## G4 — Content cleanup and world safety `[next]`

Goal: make the 0.1.9-14 removals explicit and safe to deploy.

- `[done]` Remove Ad Astra from client and server.
- `[done]` Remove The Aether from client and server.
- `[done]` Remove AmbientSounds from the client.
- `[done]` Repurpose two dimension quests without changing established quest IDs.
- `[next]` Test a new world for dimension/datapack startup warnings.
- `[next]` Test an existing-world copy and record every missing-registry warning.
- `[later]` Publish a world-upgrade checklist before declaring the release stable.

Acceptance gate: a new world is clean; an upgraded copy has documented, accepted losses and no crash or save corruption.

## G5 — Quest progression `[next]`

Goal: continue the questbook in deliberate, testable lines.

- `[done]` Polish Welcome to Amber & Arcana.
- `[done]` Expand Create Engineering while preserving its existing quest IDs.
- `[next]` Choose and complete the next quest line after runtime stability is proven.
- `[later]` Validate every task item, dependency edge, reward, icon, and description.
- `[later]` Add a progression smoke-test checklist for each finished chapter.

Acceptance gate: all edited SNBT parses, client/server quest files are identical, rewards deserialize correctly, and the chapter can be completed in-game.

## G6 — Performance and operations `[later]`

Goal: keep the pack playable on the Crafty 4 / Unraid server without hiding correctness failures.

- `[done]` Use Java 17 automatically and explicit 4–10 GB server heap settings.
- `[done]` Disable background Spark profiling and use the built-in Java sampler when profiling.
- `[done]` Set view distance 8, simulation distance 6, and reduce ocean mob pressure.
- `[next]` Measure idle, exploration, chunk-generation, and multi-player tick time.
- `[later]` Set budgets for startup time, heap use, tick time, and network packet size.

Acceptance gate: measurements meet recorded budgets in two consecutive clean test runs.

## G7 — Release automation `[later]`

Goal: make every release reviewable and hard to publish incorrectly.

- `[done]` Add repository validation and build scripts.
- `[done]` Add GitHub Actions static validation.
- `[next]` Add a client/server runtime test host with Java 17 and a fixed timeout.
- `[next]` Upload logs and comparison reports as workflow artifacts.
- `[later]` Build signed release ZIPs and checksums from a version tag.
- `[later]` Block release publication unless all acceptance gates pass.

## Milestones

| Milestone | Outcome | Required goals |
| --- | --- | --- |
| M1 — Baseline | Both clean packages boot and connect | G1 |
| M2 — Compatibility | No red X, channel, registry, or packet failure | G2 |
| M3 — Recipe clean | Recipe/tag reload and REI tests pass | G3 |
| M4 — Safe content set | New and upgraded-world checks are documented | G4 |
| M5 — Quest expansion | Next complete quest line is playable | G5 |
| M6 — Release candidate | Performance budgets and automated gates pass | G6, G7 |

## Change discipline

Only one suspected compatibility group should change per diagnostic build. Client and server must be rebuilt together. Preserve quest IDs and earlier fixes. Do not migrate Minecraft/Forge versions or broadly purge gameplay mods while investigating the current failures.
