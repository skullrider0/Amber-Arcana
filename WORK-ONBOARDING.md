# ChatGPT Work Onboarding

Use this file as the entry point for every future Amber & Arcana work session.

## Project identity

- Repository: `skullrider0/Amber-Arcana`
- Pack: Amber & Arcana
- Active baseline: 0.1.9-13
- Minecraft: 1.20.1
- Forge: 47.4.10
- Java: 17
- Deployment: CurseForge client plus Crafty 4 server on Unraid

## Read first, in this order

1. `WORK-ONBOARDING.md`
2. `GOALS.md`
3. `CURRENT_STATE.md`
4. `PROJECT_STATE.md`
5. `GOAL-MAP.md`
6. `AUTOMATION_RULES.md`
7. The newest relevant release note in `client/` or `server/pack-information/`

Treat these repository files as the current source of truth. If a chat summary conflicts with a newer committed state file, use the committed file and call out the conflict.

## Current focus

P0 is client/server runtime parity:

1. Reproduce the recipe and item-tag failures from a clean server boot.
2. Explain and remove the red-X/incompatible-server indicator.
3. Compare the actual loaded client/server mods, versions, network channels, registries, configs, and tags.
4. Investigate the login packet error `unable to fit 2202990 into 3` if it recurs.

Do not start broad mod removals or a Minecraft/Forge migration while this diagnostic work is active. Continue quest-line work only after the P0 runtime checks are stable, unless the user explicitly changes priority.

## Required session workflow

1. Pull or inspect the latest `main` state before editing.
2. Choose one goal/task ID from `PROJECT_STATE.md`.
3. Use a focused branch named `agent/<task-id>-<short-name>`.
4. Make the smallest change that can test the current hypothesis.
5. Keep client and server synchronized when the changed mod or config is required on both.
6. Preserve existing FTB Quests IDs and earlier confirmed fixes.
7. Run `bash scripts/validate.sh`.
8. For runtime changes, test a clean client and server and retain paired logs from the same session.
9. Record results, including failed hypotheses, in `PROJECT_STATE.md`.
10. Update `GOALS.md`, `CURRENT_STATE.md`, and `GOAL-MAP.md` when status or priorities change.

## Definition of done

A task is complete only when:

- Its acceptance condition is met.
- Static validation passes.
- Required runtime testing passes, when applicable.
- Client/server changes are both included.
- Evidence and remaining uncertainty are recorded.
- Goal and project-state files are updated in the same pull request.

Static inspection is not proof of a successful CurseForge import, Forge boot, multiplayer connection, recipe reload, or quest completion.

## Handoff template

At the end of a session, add or update a dated entry in `PROJECT_STATE.md`:

```markdown
## Session YYYY-MM-DD — AA-###

- Goal:
- Changes made:
- Files changed:
- Validation:
- Runtime evidence:
- Result:
- Remaining issue:
- Exact next action:
```

## Safety and scope

- Never commit tokens, passwords, server authentication data, private IP addresses, player data, or world saves.
- Back up an existing world before testing packages that remove content.
- Do not erase unrelated user changes from a dirty worktree.
- Stop after two failed automated repair attempts and record the smallest reproducible failure.
