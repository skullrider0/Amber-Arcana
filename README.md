# Amber & Arcana

Amber & Arcana is a Forge 1.20.1 modpack maintained as matching CurseForge client and Crafty 4 dedicated-server packages.

## Current release

| Component | Version |
| --- | --- |
| Pack | 0.1.9-13 |
| Minecraft | 1.20.1 |
| Forge | 47.4.10 |
| Java | 17 |
| Client manifest entries | 278 |
| Server mod downloads | 257 |
| Manual quests | 106 across 25 chapters |

Release 0.1.9-13 replaces JEI with client-only Roughly Enough Items 12.1.785, removes Polymorph because it hard-depends on JEI, and removes Ad Astra, AmbientSounds, and The Aether. Existing quest IDs and earlier compatibility fixes are preserved.

## Repository layout

- `client/` — CurseForge manifest and client overrides.
- `server/` — Crafty-ready server package source, launcher, config, quests, and validation records.
- `dist/` — ready-to-import client and server ZIPs plus checksums.
- `scripts/` — repeatable validation and packaging helpers.
- `GOAL-MAP.md` — ordered project goals and acceptance gates.
- `GOALS.md` — live goal status and next-action list.
- `WORK-ONBOARDING.md` — starting instructions for future ChatGPT Work sessions.
- `CURRENT_STATE.md` — what is known, tested, and still unverified.
- `PROJECT_STATE.md` — release history and active work queue.
- `AUTOMATION_RULES.md` — safe rules for future automated changes.

## Install

### Client

Import `dist/Amber-and-Arcana-0.1.9-13-Client.zip` into CurseForge. Allocate about 10 GB RAM and use Java 17.

### Crafty server

Create a fresh server from `dist/Amber-and-Arcana-0.1.9-13-Server.zip`. The included launcher downloads the declared server mods, removes known stale client-only/content jars, chooses Java 17, and starts Forge with the configured memory limits.

Back up an existing world before replacing a server package. Removed content mods can leave missing blocks, items, or dimensions in an existing world.

## Validate and rebuild

Requirements: Bash, Java 17, `jq`, `zip`, `unzip`, and `sha256sum`.

```bash
bash scripts/validate.sh
bash scripts/build.sh
```

Static validation checks structure, JSON, client/server quest parity, required REI metadata, removed-project exclusions, archives, and checksums. It does not replace a fresh CurseForge import, Forge boot, dedicated-server connection, or in-game recipe/tag test.

## Known investigation

The highest-priority work is reproducing and isolating the recipe/tag reload errors and the red-X/incompatible-server indicator while client connections still succeed. See `GOAL-MAP.md` for the test matrix and stop conditions.
