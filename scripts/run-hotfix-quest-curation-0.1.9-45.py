#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/hotfix-quest-curation-0.1.9-45.py"
spec = importlib.util.spec_from_file_location("aa45", TARGET)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load 0.1.9-45 quest curation")
aa45 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aa45)

# Some exploration/general chapters intentionally use vanilla evidence/support
# items (spyglass, brush, minecart, food, etc.) even though their reward tables
# were previously polluted by the old Create-first fallback. Vanilla supplies are
# allowed, but generic diamond/emerald currency is still rejected.
_base_allowed = aa45.allowed
GENERIC_CURRENCY = {
    "minecraft:diamond",
    "minecraft:diamond_block",
    "minecraft:emerald",
    "minecraft:emerald_block",
}

def allowed(stem: str, item: str) -> bool:
    if item in GENERIC_CURRENCY:
        return False
    if aa45.namespace(item) == "minecraft":
        return True
    return _base_allowed(stem, item)

aa45.allowed = allowed

aa45.main()

# Keep both historical build-summary version fields aligned with the manifest.
# Several compatibility validators inspect pack_version inside release archives.
summary_path = ROOT / "server/_crafty/build-summary.json"
summary = json.loads(summary_path.read_text())
summary["version"] = aa45.VERSION
summary["pack_version"] = aa45.VERSION
summary_path.write_text(json.dumps(summary, indent=2) + "\n")

# The historical validator still expected the deliberately generated AA35 filler
# nodes and the previous release number. Update only those current-release gates;
# historical metadata checks remain intact.
validate = ROOT / "scripts/validate.sh"
text = validate.read_text()
text = text.replace('.version == "0.1.9-44"', '.version == "0.1.9-45"', 1)
text = text.replace('.pack_version == "0.1.9-44"', '.pack_version == "0.1.9-45"', 1)
text = text.replace('echo "Amber & Arcana 0.1.9-44 static validation passed"', 'echo "Amber & Arcana 0.1.9-45 static validation passed"', 1)
old = '''test "$(rg -l 'AA35 deep progression milestone' "$client_quests/chapters" | wc -l)" = "17" || { echo "Expected AA35 marker in the 17 untouched expanded chapters" >&2; exit 1; }'''
new = '''if rg -F 'AA35 deep progression milestone' "$client_quests/chapters" >/dev/null; then echo "AA35 filler milestone remains after 0.1.9-45 curation" >&2; exit 1; fi'''
if old not in text:
    raise RuntimeError("Could not update legacy AA35 validator gate")
text = text.replace(old, new, 1)
# Require the new curation record so a stale 0.1.9-44 build cannot pass by only
# changing the version string.
anchor = "jq -e '.quest_live_sync_0_1_9_23.broken_item_rewards_fixed == 12' \"$validation\" >/dev/null"
addition = anchor + "\njq -e '.quest_curation_0_1_9_45.create_generic_fallback_removed == true and .quest_curation_0_1_9_45.aa35_filler_quests_removed > 0 and .quest_curation_0_1_9_45.client_server_quest_files_identical == true' \"$validation\" >/dev/null"
if addition not in text:
    if anchor not in text:
        raise RuntimeError("Could not insert 0.1.9-45 validation marker check")
    text = text.replace(anchor, addition, 1)
validate.write_text(text)
