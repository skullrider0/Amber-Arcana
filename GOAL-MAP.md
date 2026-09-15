# Amber & Arcana Goal Map

## Session 2026-09-15 — AA-006 quest repair

- Priority: user confirms recipe/tag fixes and requests quest work next.
- Baseline: current main 0ddd809, pack 0.1.9-20; earlier 0.1.9-15 notes below are historical.
- Changes: repaired nine quests in Welcome/Create Engineering, replaced twelve broken
  item rewards with five themed weighted tables, and added non-consuming item tasks.
- Preserved: existing IDs, dependencies, XP, mod set and recipe/tag fixes.
- Validation: quest parser/reference checks and repository build/validation pass.
- Runtime evidence: pending paired client/server in-game testing; do not claim runtime completion.
- Result: reviewable quest-repair candidate; remaining 23 chapters are not finished.
- Exact next action: apply quest overlay and test item detection, random claims and progress persistence.
- Details: [quest requirements, reward odds, evidence and installation](docs/quest-repair-AA-006.md).

## Active update — 2026-09-15 / AA-004

Current diagnostic release: **0.1.9-15**, Minecraft 1.20.1 / Forge 47.4.10 / Java 17.
Client: 278 manifest entries. Server: 258 mod downloads.
**JEI 15.59.0.211 Forge (beta) replaces REI on client and server.** This supersedes
the earlier REI-only requirement below. Polymorph, Ad Astra, AmbientSounds,
The Aether, and Every Compat remain removed. Preserve Just Dire Things,
DecoCraft, the 36 recipe overrides, four tag repairs, and every quest ID.

Evidence: the supplied 0.1.9-14 client log fails twice in REI's
DefaultClientPlugin.registerDisplays at line 403 (null armor repair ingredient);
base Create and Mekanism do not appear in its native REI plugin list. The paired
server reaches ready state with the targeted previous recipe/tag errors absent.
JEI's pinned source uses an explicit vanilla-material list for anvil displays,
avoiding that REI scan. This is not proof of all machine recipes working.

- [x] Confirm REI display exception against the exact 12.1.785 source.
- [x] Pin JEI equally in the client manifest and server download list.
- [x] Preserve recipe/tag fixes and synchronize quest wording without changing IDs.
- [ ] Retest 0.1.9-15 imports, join, JEI plugin loading, and machine operations.
- [ ] Resolve remaining marine_snow JSON, loot-table, and NTGL errors separately.

Artifacts: `dist/Amber-and-Arcana-0.1.9-15-Client.zip` and
`dist/Amber-and-Arcana-0.1.9-15-Server.zip`. Use the current SHA256SUMS.txt.
See [diagnosis and validation](docs/jei-display-0.1.9-15.md) for the exact
remaining runtime checklist. Older baseline sections below are historical.


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
