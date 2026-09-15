#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TSV="$ROOT/server/_crafty/server-mods.tsv"
BACKUP="$ROOT/server/_crafty/server-mods.tsv.before-morehitboxes-perf-v1"

if [[ ! -f "$TSV" ]]; then
  echo "ERROR: beta branch server mod list not found: $TSV" >&2
  exit 1
fi
if [[ ! -f "$BACKUP" ]]; then
  cp -p "$TSV" "$BACKUP"
fi
TMP="$(mktemp "${TSV}.tmp.XXXXXX")"
awk -F '\t' 'BEGIN{OFS="\t"}
  /^#/ || NF==0 { print; next }
  $1=="6942239" { next }
  $4=="more-hitboxes" { next }
  $2=="morehitboxes-forge-1.20.1-1.9.2.jar" { next }
  { print }
' "$TSV" > "$TMP"
mv "$TMP" "$TSV"

echo "Removed the official More Hitboxes 1.9.2 CurseForge row from the beta Crafty mod list."
echo "This allows the locally supplied 1.9.2.1 performance-beta JAR to remain installed."
