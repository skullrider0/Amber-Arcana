# Prompt for Future Agents

Copy the prompt below into a new agent session.

---

You are continuing development of **Amber & Arcana**, owned by GitHub user **skullrider0** in repository **skullrider0/Amber-Arcana**.

The authoritative target is Minecraft **1.20.1**, Forge **47.4.10**, and Java **17**. The previous alpha was named **Amber-and-Arcana-0.1.0-alpha-CurseForge** and contained approximately **262 mods**. The known dedicated-server memory preset was 4 GB minimum and 10 GB maximum.

Read `README.md`, `WORKLOAD.md`, and `CHECKLIST.md` before changing anything. Inspect repository state, releases, open issues, recent commits, and attached test logs. Update the checklist as verified work is completed.

Hard requirements:

- Preserve **Just Dire Things** and **DecoCraft**.
- Evaluate replacing JEI with **Roughly Enough Items** for Forge 1.20.1, including dependencies and integrations; do not remove JEI until compatibility is proven.
- Remove **Ad Astra**, **AmbientSounds**, and **The Aether**, plus only dependencies proven to be unused.
- Remove stale references from configs, KubeJS, datapacks, recipes, tags, quests, loot tables, advancements, and world generation.
- Diagnose the persistent recipe/item-tag errors by comparing client and server mod versions, configs, tags, scripts, and load behavior.
- Investigate the red-X/incompatible-version indicator as a possible symptom without assuming it is the root cause.
- Preserve an untouched source archive and back up any world before destructive testing.
- Do not commit secrets, GitHub tokens, account credentials, server addresses, player data, worlds, or mod JARs lacking redistribution permission.
- Keep client-only mods out of the server export.
- Use small, documented commits and record evidence for every claimed fix.
- Validate clean client launch, server launch, login, datapack reload, recipe browsing/crafting, quests, new-world generation, and a backed-up existing-world copy.
- Deliver a valid CurseForge client export, Crafty 4 server import, mod/version inventory, SHA-256 checksums, changelog, and known issues.
- If recipe/tag diagnostics remain unresolved after a disciplined client/server diff, document the blocker and proceed with the next quest-line milestone without hiding the unresolved issue.

Before acting, summarize the current repository state and name the next unchecked checklist items. After acting, update `CHECKLIST.md`, add findings under `docs/`, and report exactly what was tested, what passed, what failed, and what remains uncertain.
