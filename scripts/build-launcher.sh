#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
compiler="${AA_JDK_BIN:+$AA_JDK_BIN/}javac"
archiver="${AA_JDK_BIN:+$AA_JDK_BIN/}jar"
source_dir="$repo_dir/server/_crafty/source"
"$compiler" --release 17 "$source_dir/AmberArcanaCraftyLauncher.java"
"$archiver" --create --file "$repo_dir/server/AmberArcana-Crafty-Launcher.jar" \
  --main-class AmberArcanaCraftyLauncher \
  -C "$source_dir" AmberArcanaCraftyLauncher.class \
  -C "$source_dir" 'AmberArcanaCraftyLauncher$Mod.class'
