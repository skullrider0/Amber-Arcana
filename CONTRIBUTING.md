# Contributing

Use an issue or task ID before changing the pack. Keep each change narrow, update client and server together where required, and preserve existing quest IDs.

Before opening a pull request:

1. Run `bash scripts/validate.sh`.
2. Import and boot a clean client and server when the change affects mods, configs, recipes, tags, or quests.
3. Attach paired logs from the same test session.
4. State what changed, what was tested, and what remains unverified.
5. Never include credentials, player data, world saves, or private network addresses.
