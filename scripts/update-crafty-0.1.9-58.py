#!/usr/bin/env python3
"""Crafty updater for Amber & Arcana 0.1.9-58."""
from pathlib import Path

_source = Path(__file__).with_name("update-crafty-0.1.9-57.py").read_text(encoding="utf-8")
_source = _source.replace("VERSION = '0.1.9-57'", "VERSION = '0.1.9-58'", 1)
_source = _source.replace("matching 0.1.9-57 Client ZIP", "matching 0.1.9-58 Client ZIP", 1)
exec(compile(_source, str(Path(__file__)), "exec"), globals())
