#!/usr/bin/env python3
"""Check viewer pins and packaged files; catches stale or truncated uploads."""
import json
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "client/manifest.json").read_text())
version = manifest["version"]
expected = (238222, 8879628)
files = manifest["files"]
assert len({f["projectID"] for f in files}) == len(files), "Duplicate projects"
assert [(f["projectID"], f["fileID"]) for f in files if f["projectID"] == 238222] == [expected]
assert not {310111, 521393, 388800} & {f["projectID"] for f in files}, "Old viewer/Polymorph present"
rows = [line.split("\t") for line in (root / "server/_crafty/server-mods.tsv").read_text().splitlines() if line and not line.startswith("#")]
rows = [row for row in rows if row[0].isdigit()]
jei = [row for row in rows if row[3] == "jei"]
assert len(jei) == 1 and jei[0][0] == str(expected[1]), "Server JEI pin differs"
assert jei[0][1] == "jei-1.20.1-forge-15.59.0.211.jar"
assert jei[0][1] not in (root / "server/_crafty/remove-mods.txt").read_text().splitlines()
summary = json.loads((root / "server/_crafty/build-summary.json").read_text())
assert summary["server_mod_downloads"] == len(rows), "Server count differs"
for side, prefix in [("Client", "client/overrides"), ("Server", "server")]:
    inventory = json.loads((root / prefix / "pack-information/mod-files.json").read_text())
    entry = [entry for entry in inventory if entry["projectID"] == expected[0]]
    assert len(entry) == 1 and entry[0]["fileID"] == expected[1]
    assert entry[0]["sha512"] == jei[0][2], "Client/server checksum differs"
    with zipfile.ZipFile(root / f"dist/Amber-and-Arcana-{version}-{side}.zip") as archive:
        assert archive.testzip() is None, "Archive CRC failure"
        source = root / side.lower()
        for path in source.rglob("*"):
            if path.is_file():
                name = path.relative_to(source).as_posix()
                assert archive.read(name) == path.read_bytes(), f"Stale archive file: {name}"
print("Viewer pins, inventory, archive CRCs, and archive/source parity passed")
