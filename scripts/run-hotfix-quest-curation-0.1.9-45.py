#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/hotfix-quest-curation-0.1.9-45.py"
spec = importlib.util.spec_from_file_location("aa45", TARGET)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load 0.1.9-45 quest curation")
aa45 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aa45)

# Some exploration/general chapters intentionally use vanilla evidence items
# (spyglass, brush, minecart, food, etc.) even though their reward tables were
# previously polluted by the old Create-first fallback. Vanilla supplies are a
# safe themed fallback; unrelated mod namespaces remain forbidden.
_base_allowed = aa45.allowed

def allowed(stem: str, item: str) -> bool:
    if aa45.namespace(item) == "minecraft":
        return True
    return _base_allowed(stem, item)

aa45.allowed = allowed

aa45.main()
