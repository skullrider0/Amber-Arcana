#!/usr/bin/env python3
"""Crafty updater for Amber & Arcana 0.1.9-59."""
from pathlib import Path

_source = Path(__file__).with_name("update-crafty-0.1.9-57.py").read_text(encoding="utf-8")
_source = _source.replace("VERSION = '0.1.9-57'", "VERSION = '0.1.9-59'", 1)
_source = _source.replace("matching 0.1.9-57 Client ZIP", "matching 0.1.9-59 Client ZIP", 1)
_scope = {"__name__": "amber_arcana_updater_0_1_9_59", "__file__": __file__}
exec(compile(_source, str(Path(__file__)), "exec"), _scope)

_original_install = _scope["install"]


def _install_and_remove_stale_nitro_recipe(blob, root):
    _original_install(blob, root)
    stale = root / "kubejs/data/amber_arcana/recipes/powah/energizing/nitro_crystal_block_bulk.json"
    if stale.exists():
        stale.unlink()
        print("Removed stale 0.1.9-58 Nitro block recipe: " + str(stale))


_scope["install"] = _install_and_remove_stale_nitro_recipe
globals().update({key: value for key, value in _scope.items() if not key.startswith("__")})

if __name__ == "__main__":
    _scope["main"]()
