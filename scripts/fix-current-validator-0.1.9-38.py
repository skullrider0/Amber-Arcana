#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "scripts/validate.sh"
text = path.read_text()
text = text.replace(
    '= "26" || { echo "Not all 26 chapters are assigned to mechanics groups"',
    '= "28" || { echo "Not all 28 chapters are assigned to mechanics groups"',
)
text = text.replace(
    '= "26" || { echo "Expected 26 generated client wheel tables"',
    '= "28" || { echo "Expected 28 generated client wheel tables"',
)
text = text.replace(
    '= "26" || { echo "Expected 26 generated server wheel tables"',
    '= "28" || { echo "Expected 28 generated server wheel tables"',
)
text = text.replace(
    '= "104" || { echo "Mod-specific tier table count mismatch"',
    '= "112" || { echo "Mod-specific tier table count mismatch"',
)
text = text.replace(
    '= "24" || { echo "Deep progression marker missing from one or more expanded chapters"',
    '= "17" || { echo "Expected AA35 marker in the 17 untouched expanded chapters"',
)
path.write_text(text)
print("Updated live 0.1.9-38 validation for 28 chapters, 28 Fortune Wheels, 112 tier tables, and seven rebuilt AA35 chapters")
