# Prompt for Future Agents

Copy the prompt below into a new agent session.

---

Continue development of **Amber & Arcana** in **skullrider0/Amber-Arcana**.

Current repository baseline:

- Release: **0.1.9-13**
- Minecraft: **1.20.1**
- Forge: **47.4.10**
- Java: **17**
- Client manifest entries: **278**
- Server mod downloads: **257**
- Manual quests: **106 across 25 chapters**
- Client artifact: `dist/Amber-and-Arcana-0.1.9-13-Client.zip`
- Crafty artifact: `dist/Amber-and-Arcana-0.1.9-13-Server.zip`

Read `README.md`, `CURRENT_STATE.md`, `PROJECT_STATE.md`, `GOAL-MAP.md`, `GOALS.md`, `WORK-ONBOARDING.md`, `AUTOMATION_RULES.md`, `WORKLOAD.md`, and `CHECKLIST.md` before editing. Inspect the current main branch, recent commits, open issues, releases, and test evidence. Do not assume unchecked work is complete.

Hard requirements:

- Preserve **Just Dire Things** and **DecoCraft**.
- Keep the established 0.1.9-13 migration: client-only **REI 12.1.785** replaces JEI; **Polymorph** is removed because it hard-depends on JEI; **Ad Astra**, **AmbientSounds**, and **The Aether** are removed.
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
