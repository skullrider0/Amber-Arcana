#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "scripts/validate.sh"
text = path.read_text()
text = text.replace(
    '= "26" || { echo "Not all 26 chapters are assigned to mechanics groups"',
    '= "28" || { echo "Not all 28 chapters are assigned to mechanics groups"',
)
path.write_text(text)
print("Updated live mechanics-group validation for 28 chapters")
