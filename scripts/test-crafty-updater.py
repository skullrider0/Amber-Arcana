#!/usr/bin/env python3
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('updater',ROOT/'scripts/update-crafty-0.1.9-42.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)

class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'server';self.root.mkdir()
        (self.root/'_crafty').mkdir();(self.root/'_crafty/server-mods.tsv').write_text('old manifest')
        (self.root/'server.properties').write_text('level-name=world\n')
        (self.root/'world').mkdir();(self.root/'world/level.dat').write_bytes(b'WORLD SENTINEL')
        self.blob=(ROOT/'dist/Amber-and-Arcana-0.1.9-42-Crafty-Update-Overlay.zip').read_bytes()
    def test_apply_and_backup_without_world_changes(self):
        u.install(self.blob,self.root)
        backups=list((self.root/'_amber_updates').iterdir());self.assertEqual(len(backups),1)
        self.assertEqual((backups[0]/'files/_crafty/server-mods.tsv').read_text(),'old manifest')
        self.assertEqual((self.root/'world/level.dat').read_bytes(),b'WORLD SENTINEL')
        data=json.loads((self.root/'kubejs/data/productivebees/productivebees/justdirethings/ferricore.json').read_text())
        self.assertEqual(data['flowerBlock'],'justdirethings:ferricore_block')
    def test_active_java_refused(self):
        proc=Path(self.tmp.name)/'proc';p=proc/'123';p.mkdir(parents=True)
        (p/'cmdline').write_bytes(b'java\0-jar\0AmberArcana-Crafty-Launcher.jar\0')
        (p/'cwd').symlink_to(self.root,target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError,'still running'):u.ensure_stopped(self.root,proc)
    def test_other_server_does_not_block(self):
        proc=Path(self.tmp.name)/'proc';p=proc/'456';p.mkdir(parents=True)
        (p/'cmdline').write_bytes(b'java\0-jar\0server.jar\0');(p/'cwd').symlink_to(Path(self.tmp.name))
        u.ensure_stopped(self.root,proc)
    def test_reject_unexpected_and_traversal_paths(self):
        for name in ['../world/level.dat','world/level.dat','/tmp/bad']:
            stream=io.BytesIO()
            with zipfile.ZipFile(stream,'w') as z:z.writestr(name,b'bad')
            with zipfile.ZipFile(stream) as z:
                with self.assertRaises(RuntimeError):u.checked_members(z,self.root)
    def test_rollback_on_failure(self):
        original=u.os.replace
        calls=0
        def fail_second(*args,**kwargs):
            nonlocal calls
            calls+=1
            if calls==2:raise OSError('simulated write failure')
            return original(*args,**kwargs)
        with patch.object(u.os,'replace',fail_second):
            with self.assertRaisesRegex(OSError,'simulated'):u.install(self.blob,self.root)
        self.assertEqual((self.root/'_crafty/server-mods.tsv').read_text(),'old manifest')
        self.assertEqual((self.root/'world/level.dat').read_bytes(),b'WORLD SENTINEL')
        self.assertFalse((self.root/'AmberArcana-Crafty-Launcher.jar').exists())

if __name__=='__main__':unittest.main()
