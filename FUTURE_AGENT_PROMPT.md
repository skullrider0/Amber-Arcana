# Prompt for Future Agents

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


Copy the prompt below into a new agent session.

---

Continue development of **Amber & Arcana** in **skullrider0/Amber-Arcana**.

Current repository baseline:

- Release: **0.1.9-14**
- Minecraft: **1.20.1**
- Forge: **47.4.10**
- Java: **17**
- Client manifest entries: **278**
- Server mod downloads: **257**
- Manual quests: **106 across 25 chapters**
- Client artifact: `dist/Amber-and-Arcana-0.1.9-14-Client.zip`
- Crafty artifact: `dist/Amber-and-Arcana-0.1.9-14-Server.zip`

Read `README.md`, `CURRENT_STATE.md`, `PROJECT_STATE.md`, `GOAL-MAP.md`, `GOALS.md`, `WORK-ONBOARDING.md`, `AUTOMATION_RULES.md`, `WORKLOAD.md`, and `CHECKLIST.md` before editing. Inspect the current main branch, recent commits, open issues, releases, and test evidence. Do not assume unchecked work is complete.

Hard requirements:

- Preserve **Just Dire Things** and **DecoCraft**.
- Keep the established 0.1.9-13 migration: client-only **REI 12.1.785** replaces JEI; **Polymorph** is removed because it hard-depends on JEI; **Ad Astra**, **AmbientSounds**, and **The Aether** are removed.
- Preserve the 0.1.9-14 compatibility layer unless runtime evidence proves an individual override should be repaired or removed.
- Do not silently reintroduce removed mods or delete dependencies without proving whether they are still used.
- Diagnose persistent recipe/item-tag errors by comparing client and server mod IDs, versions, sides, configs, KubeJS data, datapacks, tags, recipes, and load/network behavior.
- Investigate the red-X/incompatible-server indicator as a symptom without assuming it is the root cause.
- Preserve quest IDs and earlier compatibility fixes.
- Preserve an untouched release artifact and back up worlds before destructive tests.
- Never commit GitHub tokens, credentials, private server addresses, player data, worlds, or third-party mod JARs lacking redistribution permission.
- Keep client-only mods out of the Crafty server package.
- Use small, documented commits. Update the checklist only when evidence exists.
- Validate static scripts, clean CurseForge import, clean Crafty import, client launch, server launch, login, datapack reload, REI recipe browsing, representative crafting, quests, new-world generation, and a backed-up existing-world copy.
- Deliver updated client/server ZIPs, inventories, checksums, changelog, known issues, and evidence under `docs/`.
- If disciplined client/server comparison does not isolate the recipe/tag issue, document the reproducer and blocker, then proceed with the next quest-line milestone without describing the issue as fixed.

At the start, report:

1. Current branch and latest commit.
2. Existing release artifacts and hashes.
3. Checked and unchecked items in `CHECKLIST.md`.
4. The next smallest testable task.
5. Any missing files or access.

At the end, report exactly what changed, what was tested, what passed, what failed, and what remains uncertain. Update `CHECKLIST.md` and the appropriate state/goal documents in the same change.
