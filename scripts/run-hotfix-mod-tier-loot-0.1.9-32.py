#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/hotfix-mod-tier-loot-0.1.9-32.py"

spec = importlib.util.spec_from_file_location("aa_mod_tier_loot_32", TARGET)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load 0.1.9-32 mod-tier loot hotfix")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

_original = mod.tiered_items_for_chapter


def robust_tiered_items(stem, local_text, catalog, chapter_namespaces):
    buckets = _original(stem, local_text, catalog, chapter_namespaces)

    # Only broad, non-mod-specific chapters are allowed to borrow from core-pack
    # namespaces. Real mod chapters stay namespace-pure: Create pays Create,
    # Powah pays Powah, Mekanism pays Mekanism, etc.
    broad_chapters = {"getting_started", "endgame"}
    if stem in broad_chapters:
        preferred = ("create", "mekanism", "powah", "productivebees", "ars_nouveau", "ae2", "refinedstorage")
        fallback = []
        seen = set()
        for ns in preferred:
            for item, _depth in sorted(catalog.get(ns, {}).items(), key=lambda kv: (kv[1], kv[0])):
                if item not in seen:
                    seen.add(item)
                    fallback.append(item)
                if len(fallback) >= 24:
                    break
            if len(fallback) >= 24:
                break

        for tier in range(1, 5):
            if len(buckets[tier]) >= 6:
                continue
            for item in fallback:
                if item not in buckets[tier]:
                    buckets[tier].append(item)
                if len(buckets[tier]) >= 6:
                    break

    for tier in range(1, 5):
        if len(buckets[tier]) < 2:
            raise RuntimeError(f"{stem} tier {tier} still has fewer than two modded choices")
    return buckets


mod.tiered_items_for_chapter = robust_tiered_items
mod.main()
