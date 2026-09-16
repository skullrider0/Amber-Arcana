#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/hotfix-short-chain-rewards-0.1.9-34.py"

spec = importlib.util.spec_from_file_location("aa_short34", TARGET)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load 0.1.9-34 short-chain reward hotfix")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def bundle_count(item: str, tier: int, variant: int) -> int:
    if mod.component_like(item):
        base = {1: 2, 2: 4, 3: 6, 4: 8}[tier]
        return min(16, base * (variant + 1))
    # Short chapters often expose only a handful of machines. Later tiers may
    # therefore award a small multi-machine bundle as one of the common outcomes,
    # while the deepest/jackpot entry stays single-count and low weight.
    if tier == 1:
        return 1
    if tier == 2:
        return min(2, 1 + variant)
    return min(3, 1 + variant)


def robust_expand_pool(stem, tier, source_by_tier):
    current = mod.dedupe_items(source_by_tier[tier])
    prev = mod.dedupe_items(source_by_tier[max(1, tier - 1)])
    nxt = mod.dedupe_items(source_by_tier[min(4, tier + 1)])
    deepest = mod.dedupe_items(source_by_tier[4])

    ordered = []
    seen = set()
    for band, items in (("prev", prev), ("current", current), ("preview", nxt if tier >= 2 else []), ("deep", deepest if tier >= 3 else [])):
        for item in items:
            if item not in seen:
                seen.add(item)
                ordered.append((band, item))
    if not ordered:
        raise RuntimeError(f"No modded reward items available for short chapter {stem} tier {tier}")

    target = mod.TARGET_ENTRIES[tier]
    out = []
    for band, item in ordered:
        if band == "prev":
            weight = 14.0 if tier >= 3 else 16.0
        elif band == "current":
            weight = 9.0 if tier <= 2 else 7.0
        elif band == "preview":
            weight = 2.0 if tier == 2 else 1.25
        else:
            weight = 0.55
        original = [w for _c, i, w in source_by_tier.get(4, []) if i == item]
        if tier == 4 and original and min(original) < 1.0:
            weight = min(original)
        out.append((1, item, weight))

    variant = 0
    idx = 0
    while len(out) < target:
        band, item = ordered[idx % len(ordered)]
        count = bundle_count(item, tier, variant % 4)
        if mod.component_like(item):
            weight = max(1.5, 11.0 - variant * 1.35)
        else:
            base = 5.0 if band in {"prev", "current"} else 0.9
            weight = max(0.35, base - variant * 0.55)
        candidate = (count, item, weight)
        if candidate not in out:
            out.append(candidate)
        idx += 1
        if idx % len(ordered) == 0:
            variant += 1
        if idx > target * 20:
            break

    if len(out) < target:
        raise RuntimeError(f"Could only build {len(out)}/{target} weighted outcomes for {stem} tier {tier}")
    return out[:target]


mod.bulky_count = bundle_count
mod.expand_pool = robust_expand_pool
mod.main()
