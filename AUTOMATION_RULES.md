# Automation Rules

These rules apply to automated or agent-assisted changes.

1. Use a focused branch named `agent/<task-id>-<short-name>`.
2. Change one suspected compatibility group per diagnostic build.
3. Update client and server together when a mod is required on both sides.
4. Preserve existing FTB Quests IDs and previously confirmed fixes.
5. Never commit credentials, CurseForge API keys, server tokens, player data, world saves, crash dumps containing private addresses, or authentication caches.
6. Run `bash scripts/validate.sh` before proposing a merge.
7. Record acceptance evidence in the pull request: versions, test environment, client log, server log, and pass/fail matrix.
8. Do not merge or publish a release with a failed validation gate.
9. Retry an automated repair at most twice; then stop with the smallest reproducible failure and evidence.
10. Do not migrate Minecraft or Forge versions during recipe/tag diagnosis unless a separate approved goal explicitly requests it.
