#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture="$(mktemp -d)"
trap 'rm -rf "$fixture"' EXIT
mkdir -p "$fixture/mods" "$fixture/_crafty"
cp "$repo_dir/server/_crafty/server-mods.tsv" "$fixture/_crafty/"
cp "$repo_dir/server/_crafty/remove-mods.txt" "$fixture/_crafty/"
touch "$fixture/mods/jei-1.20.1-forge-15.59.0.211.jar" \
  "$fixture/mods/jei-1.20.1-forge-15.57.0.207.jar" \
  "$fixture/mods/RoughlyEnoughItems-12.1.785-forge.jar" \
  "$fixture/mods/REIPluginCompatibilities-forge-12.0.93.jar" \
  "$fixture/mods/polymorph-old.jar" "$fixture/mods/create.jar"
cat > "$fixture/CleanupCheck.java" <<'JAVA'
public class CleanupCheck {
    public static void main(String[] args) throws Exception {
        AmberArcanaCraftyLauncher.cleanupRemovedMods();
        AmberArcanaCraftyLauncher.cleanupReplacedRecipeViewers();
    }
}
JAVA
compiler="${AA_JDK_BIN:+$AA_JDK_BIN/}javac"
runtime="${AA_JDK_BIN:+$AA_JDK_BIN/}java"
launcher="$repo_dir/server/AmberArcana-Crafty-Launcher.jar"
"$compiler" --release 17 -cp "$launcher" "$fixture/CleanupCheck.java"
(cd "$fixture" && "$runtime" -cp "$fixture:$launcher" CleanupCheck)
test -f "$fixture/mods/jei-1.20.1-forge-15.59.0.211.jar"
test -f "$fixture/mods/create.jar"
test "$(find "$fixture/mods" -type f | wc -l)" = 2
echo "Launcher cleanup retained pinned JEI and unrelated mods; removed stale viewers"
