#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
compiler="${AA_JDK_BIN:+$AA_JDK_BIN/}javac"
archiver="${AA_JDK_BIN:+$AA_JDK_BIN/}jar"
source_dir="$repo_dir/server/_crafty/source"
launcher="$repo_dir/server/AmberArcana-Crafty-Launcher.jar"
if ! command -v "$compiler" >/dev/null 2>&1 || ! command -v "$archiver" >/dev/null 2>&1; then
  test -f "$launcher" || { echo "JDK tools are unavailable and no checked-in launcher exists" >&2; exit 1; }
  unzip -tq "$launcher" >/dev/null || { echo "Checked-in launcher is not a valid JAR" >&2; exit 1; }
  echo "JDK tools unavailable; reusing validated checked-in launcher"
  exit 0
fi
"$compiler" --release 17 "$source_dir/AmberArcanaCraftyLauncher.java"
"$archiver" --create --file "$launcher" \
  --main-class AmberArcanaCraftyLauncher \
  -C "$source_dir" AmberArcanaCraftyLauncher.class \
  -C "$source_dir" 'AmberArcanaCraftyLauncher$Mod.class'
