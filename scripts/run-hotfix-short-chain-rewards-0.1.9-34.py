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
    if tier == 1:
        return 1
    if tier == 2:
        return min(2, 1 + variant)
    return min(3, 1 + variant)


def robust_expand_pool(stem, tier, source_by_tier):
    current = mod.dedupe_items(source_by_tier[tier])
    prev = mod.dedupe_items(source_by_tier.get(max(1, tier - 1), source_by_tier[tier]))
    nxt = mod.dedupe_items(source_by_tier.get(min(4, tier + 1), source_by_tier[tier]))
    deepest = mod.dedupe_items(source_by_tier[max(source_by_tier)])

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


def robust_render_wheel(table_id, order, title, pools):
    candidates = pools[3] + pools[4]
    unique = []
    seen = set()
    for count, item, weight in candidates:
        key = (count, item)
        if key in seen:
            continue
        seen.add(key)
        if weight < 1.0:
            final_weight = min(weight, 0.45)
        elif mod.component_like(item):
            final_weight = min(9.0, max(3.0, weight))
        else:
            final_weight = min(6.0, max(1.0, weight * 0.75))
        unique.append((count, item, final_weight))
        if len(unique) >= 24:
            break

    idx = 0
    while len(unique) < 24:
        _count, item, _weight = candidates[idx % len(candidates)]
        count = 2 + ((idx // max(1, len(candidates))) % 3)
        key = (count, item)
        if key not in seen:
            seen.add(key)
            final_weight = 2.0 if mod.component_like(item) else 0.8
            unique.append((count, item, final_weight))
        idx += 1
        if idx > 500:
            break

    if not unique:
        raise RuntimeError(f"No finale rewards generated for {title}")

    lines = [
        "{",
        f'\ticon: "{unique[0][1]}"',
        f'\tid: "{table_id}"',
        f"\tloot_size: {mod.FINALE_LOOT_SIZE}",
        f"\torder_index: {order}",
        "\trewards: [",
    ]
    for count, item, weight in unique:
        cp = f"count: {count}, " if count != 1 else ""
        lines.append(f'\t\t{{ {cp}item: "{item}", weight: {weight:.2f}f }}')
    lines += [
        "\t]",
        f'\ttitle: "Wheel of Fortune — {title}"',
        "\tuse_title: true",
        "}",
        "",
    ]
    return "\n".join(lines), len(unique)


mod.bulky_count = bundle_count
mod.expand_pool = robust_expand_pool
mod.render_wheel = robust_render_wheel
mod.main()

# 0.1.9-32 originally asserted exactly three T4 draws for Powah. The 0.1.9-34
# short-chain pass intentionally upgrades compact chapters, including Powah, to
# four T4 draws. Keep the original jackpot checks but accept the richer draw count.
validate = ROOT / "scripts/validate.sh"
text = validate.read_text()
text = text.replace(
    "grep -Fq 'loot_size: 3' \"$client_quests/reward_tables/modroll_powah_tier_4.snbt\" || { echo \"High-tier multi-item roll missing\" >&2; exit 1; }",
    "grep -Eq 'loot_size: [34]' \"$client_quests/reward_tables/modroll_powah_tier_4.snbt\" || { echo \"High-tier multi-item roll missing\" >&2; exit 1; }",
)
validate.write_text(text)
