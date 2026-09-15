# Amber & Arcana

Amber & Arcana is a Forge 1.20.1 modpack maintained as matching CurseForge client and Crafty 4 dedicated-server packages.

## Direct downloads

[⬇️ Download Client 0.1.9-17](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-0.1.9-17-Client.zip) · [⬇️ Download Crafty Server 0.1.9-17](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-0.1.9-17-Server.zip)

## Current release

| Component | Version |
| --- | --- |
| Pack | 0.1.9-17 |
| Minecraft | 1.20.1 |
| Forge | 47.4.10 |
| Java | 17 |
| Client manifest entries | 278 |
| Server mod downloads | 258 |
| Manual quests | 106 across 25 chapters |

Release 0.1.9-17 pins the **client** to JEI 15.2.0.27 (CurseForge file 4712868), the JEI line used by Mekanism 10.4.16's 1.20.x build. JEI is removed from the dedicated-server download set because recipe browsing is client-side. This hotfix specifically targets missing Mekanism machine categories such as the Metallurgic Infuser recipe used for Atomic Alloy. All 0.1.9-14 recipe/tag overrides and established quest IDs remain preserved.

## Repository layout

- `client/` — CurseForge manifest and client overrides.
- `server/` — Crafty-ready server package source, launcher, config, quests, and validation records.
- `dist/` — ready-to-import client and server ZIPs plus checksums.
- `scripts/` — repeatable validation and packaging helpers.
- `GOAL-MAP.md` — ordered project goals and acceptance gates.
- `GOALS.md` — live goal status and next-action list.
- `WORKLOAD.md` — prioritized technical workload and validation matrix.
- `CHECKLIST.md` — evidence-based completion checklist.
- `FUTURE_AGENT_PROMPT.md` — copy-ready handoff prompt for future agents.
- `WORK-ONBOARDING.md` — starting instructions for future ChatGPT Work sessions.
- `CURRENT_STATE.md` — what is known, tested, and still unverified.
- `PROJECT_STATE.md` — release history and active work queue.
- `AUTOMATION_RULES.md` — safe rules for future automated changes.

## Install

### Client

Import `dist/Amber-and-Arcana-0.1.9-17-Client.zip` into CurseForge. Allocate about 10 GB RAM and use Java 17.

### Crafty server

Create a fresh server from `dist/Amber-and-Arcana-0.1.9-17-Server.zip`. The included launcher downloads the declared server mods, removes known stale client-only/content jars, chooses Java 17, and starts Forge with the configured memory limits.

Back up an existing world before replacing a server package. Removed content mods can leave missing blocks, items, or dimensions in an existing world.

## Validate and rebuild

Requirements: Bash, Java 17, `jq`, `zip`, `unzip`, and `sha256sum`, and Python 3. Rebuild the launcher after Java-source edits with `bash scripts/build-launcher.sh` (requires a Java 17+ JDK).

```bash
bash scripts/validate.sh
bash scripts/build.sh
```

Static validation checks structure, JSON, client/server quest parity, pinned JEI metadata and archive/source parity, removed-project exclusions, archives, and checksums. It does not replace a fresh CurseForge import, Forge boot, dedicated-server connection, or in-game recipe/tag test.

## Known investigation

The highest-priority work is reproducing and isolating the recipe/tag reload errors and the red-X/incompatible-server indicator while client connections still succeed. Follow `WORKLOAD.md` and update `CHECKLIST.md` with actual test evidence.

## 0.1.9-17 content cleanup

- The Twilight Forest has been removed from the client and dedicated server package.
- Existing Crafty installs automatically delete `twilightforest-1.20.1-4.3.2508-universal.jar` during bootstrap.
- `Eternal Steak` (`artifacts:eternal_steak`) is removed from chest-generated loot with LootJS while Artifacts remains installed.
- Glitchy Mantle is not included in this Minecraft 1.20.1 pack, so no unrelated Relics/GlitchCore content was removed.

