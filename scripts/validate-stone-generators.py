#!/usr/bin/env python3
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JAR='create_generators-1.0.0-forge-1.20.1.jar'
HASH='757b86c857c81e9bca12b7308814699c5ecbb9cd34c9d43b614c3c76adc4208fc8edc58c907983b50b768020b8244f33dd6b9137172f5cdcfd1165c5badab961'
manifest=json.loads((ROOT/'client/manifest.json').read_text())
VERSION=manifest['version']
parts=tuple(int(x) for x in VERSION.split('-')[-1].split('.')) if VERSION.count('.') == 2 and '-' not in VERSION.split('-')[-1] else None
assert VERSION.startswith('0.1.9-') and int(VERSION.rsplit('-',1)[1]) >= 43
pins=[f for f in manifest['files'] if f['projectID']==1206505]
assert pins==[{'projectID':1206505,'fileID':6224618,'required':True}]
text=(ROOT/'server/_crafty/server-mods.tsv').read_text()
rows=[l.split('\t') for l in text.splitlines() if l and not l.startswith('#')]
assert [r for r in rows if r[5]=='1206505']==[['6224618',JAR,HASH,'create-stone-generators','Create: Easy Stone Generators','1206505']]
# 0.1.9-46 bundles the patched More Hitboxes JAR locally instead of listing it
# as a fake CurseForge fileID=0 row, so the managed download count is now 270.
assert len(rows)==270
assert all(r[0] != '0' for r in rows)
assert not any(r[1].startswith('morehitboxes-forge-1.20.1-') for r in rows)
assert len(manifest['files'])==291
assert any(r[1]=='create-1.20.1-6.0.8.jar' and r[5]=='328085' for r in rows)
assert JAR not in (ROOT/'server/_crafty/remove-mods.txt').read_text()
with zipfile.ZipFile(ROOT/f'dist/Amber-and-Arcana-{VERSION}-Client.zip') as z:
    assert json.loads(z.read('manifest.json'))==manifest
for suffix in ['Server','Crafty-Update-Overlay']:
    with zipfile.ZipFile(ROOT/f'dist/Amber-and-Arcana-{VERSION}-{suffix}.zip') as z:
        assert z.read('_crafty/server-mods.tsv').decode()==text
        assert json.loads(z.read('_crafty/build-summary.json'))['pack_version']==VERSION
if len(sys.argv)>1:
    # Optional audit against the actual upstream JAR (not bundled or modified).
    blob=Path(sys.argv[1]).read_bytes();assert hashlib.sha512(blob).hexdigest()==HASH
    with zipfile.ZipFile(sys.argv[1]) as z:
        toml=z.read('META-INF/mods.toml').decode()
        assert 'modId="create_generators"' in toml and 'versionRange="[1.20.1]"' in toml
        recipes=[n for n in z.namelist() if '/recipes/' in n and n.endswith('.json')]
        assert len(recipes)==6
        for name in recipes:
            recipe=json.loads(z.read(name))
            assert recipe['type']=='create:mixing'
            assert all('item' in x or 'fluid' in x for x in recipe['ingredients']+recipe['results'])
        assert [n for n in z.namelist() if n.endswith('.class')]==['create_generators/CreateGeneratorsMod.class']
        assert not any('mixin' in n.lower() for n in z.namelist())
print(f'Stone Generators validation passed for {VERSION}: matching client/server pin, checksum, archives, unchanged Create version')
