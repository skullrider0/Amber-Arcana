# JEI display diagnosis — 0.1.9-15

## Evidence and decision

The supplied September 15 client log identifies REI 12.1.785. At 01:04:59 and
01:14:58 its DefaultClientPluginImpl fails DisplayRegistryImpl registration:
`NullPointerException: ingredient is null`, at DefaultClientPlugin.java:403.
The exact Maven sources locate that line inside a scan of all registered armor
items: it converts ArmorMaterial.getRepairIngredient() without a null check.
The log does not identify which armor material returned null. This is a repair
display failure, not evidence that a particular crafting JSON is malformed.

Its client-plugin list includes AE2, Chipped and several other native REI
plugins, but not base Create or Mekanism. REIPC can bridge JEI plugins, but was
absent. Adding it introduces another compatibility layer for this Forge pack.
The user asked whether returning to JEI would be preferable during the repair.
This build follows that direction while retaining all previous data repairs.

JEI 15.59.0.211 Forge (beta) is pinned to CurseForge project/file
238222:8879628. The downloaded binary declares Forge >=47.0 and
Minecraft >=1.20.1,<1.20.2. Its exact published sources show AnvilRecipeMaker
using an explicit list of vanilla repair materials, avoiding REI's global
modded armor-material scan. This does not rule out errors in individual JEI
plugins; only an actual client session can establish full plugin coverage.

## Scope

Replace the viewer on client and server, retain the pinned server jar during
launcher cleanup, refresh inventories, release notes, download links and quest
viewer wording. Polymorph is not restored. No new recipe suppression or gameplay
mod removal is introduced. Existing 36 overrides and four tag repairs remain.

## Validation

Static gate: scripts/build.sh then scripts/validate.sh. Validation checks the
JEI pins, server count, matching inventory checksum, quest/data parity, ZIP CRCs,
SHA256SUMS and byte-for-byte archive/source parity. Launcher cleanup has a
focused fixture check for retaining the pinned JEI and removing old viewers.
No local graphical Minecraft client or paired live Crafty test was run here.

## Runtime acceptance checklist

- [ ] Import both 0.1.9-15 distributions into fresh test instances using Java 17.
- [ ] Client and server boot; client joins.
- [ ] JEI loads Create and Mekanism recipe plugins without plugin exceptions.
- [ ] R/U displays iron-sheet pressing and precision-mechanism assembly.
- [ ] Mekanism enrichment/crushing and Farmer's Delight cooking categories work.
- [ ] At least one magic recipe category works.
- [ ] Execute one real machine recipe and verify its output.
- [ ] Confirm quests and previous tag repairs remain intact.

If anything fails, retain the full client and server latest.log after one
failed lookup. Do not infer success from CI alone or remove more recipes merely
to suppress plugin errors. The prior server log still contains malformed
marine_snow JSON, loot-table errors and NTGL equipment errors.

## Sources

- REI exact sources: https://maven.shedaniel.me/me/shedaniel/RoughlyEnoughItems-forge/12.1.785/RoughlyEnoughItems-forge-12.1.785-sources.jar
- JEI exact sources: https://maven.blamejared.com/mezz/jei/jei-1.20.1-forge/15.59.0.211/jei-1.20.1-forge-15.59.0.211-sources.jar
- JEI pinned download: https://www.curseforge.com/minecraft/mc-mods/jei/files/8879628
- REIPC role: https://www.curseforge.com/minecraft/mc-mods/roughly-enough-items-hacks

Raw user logs are not committed because they contain player and connection data.

## Local results

Passed: Java 17 launcher compilation; cleanup fixture (pinned JEI and unrelated
jar retained, obsolete JEI/REI/REIPC/Polymorph removed); build.sh; validate.sh;
quest ID comparison against the previous commit. CurseForge CDN and Modrinth
JEI binaries have identical SHA-512 hashes. No third-party mod binary is bundled
in the export; the manifest and server launcher fetch the pinned file.
