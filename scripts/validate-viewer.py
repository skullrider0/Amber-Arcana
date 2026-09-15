#!/usr/bin/env python3
"""Validate the Mekanism-compatible JEI client pin and release archives."""
import json
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "client/manifest.json").read_text())
version = manifest["version"]
expected = (238222, 4712868)
files = manifest["files"]
assert len({f["projectID"] for f in files}) == len(files), "Duplicate projects"
assert [(f["projectID"], f["fileID"]) for f in files if f["projectID"] == 238222] == [expected], "Client JEI pin differs"
assert not {310111, 521393, 388800} & {f["projectID"] for f in files}, "Old viewer/Polymorph present"
rows = [line.split("\t") for line in (root / "server/_crafty/server-mods.tsv").read_text().splitlines() if line and not line.startswith("#")]
assert not [row for row in rows if len(row) >= 4 and (row[3] == "jei" or row[1].startswith("jei-"))], "JEI should be client-only for this hotfix"
summary = json.loads((root / "server/_crafty/build-summary.json").read_text())
assert summary["server_mod_downloads"] == len(rows), "Server count differs"
for side, prefix in [("Client", "client"), ("Server", "server")]:
    archive_path = root / f"dist/Amber-and-Arcana-{version}-{side}.zip"
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None, "Archive CRC failure"
        source = root / prefix
        for p in source.rglob("*"):
            if p.is_file():
                name = p.relative_to(source).as_posix()
                assert archive.read(name) == p.read_bytes(), f"Stale archive file: {name}"
print("Mekanism-compatible JEI pin, server viewer cleanup, archive CRCs, and source parity passed")
