#!/usr/bin/env python3
"""Run inside Crafty-4 with Python 3 after stopping Amber & Arcana in Crafty."""
import argparse
import datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import urllib.request
import zipfile

VERSION = '0.1.9-46'
DEFAULT_ROOT = '/crafty/servers/b6356e28-2508-4bad-8869-133860f04f83'
ARCHIVE = f'Amber-and-Arcana-{VERSION}-Crafty-Update-Overlay.zip'
EXACT_FILES = {
    'AmberArcana-Crafty-Launcher.jar', '_crafty/server-mods.tsv', '_crafty/remove-mods.txt',
    '_crafty/build-summary.json', 'pack-information/validation.json',
    'mods/morehitboxes-forge-1.20.1-1.9.2.1.jar',
}
PREFIXES = ('config/ftbquests/quests/', 'kubejs/data/', 'kubejs/assets/')


def ensure_stopped(root, proc=Path('/proc')):
    for p in proc.iterdir():
        if not p.name.isdigit():
            continue
        try:
            raw=(p/'cmdline').read_bytes()
            executable=raw.split(b'\0',1)[0].decode(errors='replace')
            if not Path(executable).name.startswith('java'):
                continue
            cmd=raw.replace(b'\0',b' ').decode(errors='replace')
            cwd=(p/'cwd').resolve(strict=True)
        except FileNotFoundError:
            continue
        except PermissionError as exc:
            raise RuntimeError('Cannot inspect processes. Run updater through docker exec as root.') from exc
        if 'java' in cmd.lower() and (cwd == root or root in cwd.parents or str(root) in cmd):
            raise RuntimeError(f'Server Java process {p.name} is still running. Stop Amber & Arcana in Crafty first.')


def checked_members(archive, root):
    members=[]
    for entry in archive.infolist():
        p=PurePosixPath(entry.filename)
        if p.is_absolute() or '..' in p.parts or '\\' in entry.filename:
            raise RuntimeError('Unsafe archive path: '+entry.filename)
        if entry.is_dir():
            continue
        if entry.filename not in EXACT_FILES and not entry.filename.startswith(PREFIXES):
            raise RuntimeError('Unexpected overlay file: '+entry.filename)
        if (entry.external_attr >> 16) & 0o170000 == 0o120000:
            raise RuntimeError('Archive contains a symlink: '+entry.filename)
        target=root/entry.filename
        if any(part.is_symlink() for part in (target, *target.parents)):
            raise RuntimeError('Refusing to overwrite through symlink: '+str(target))
        members.append(entry)
    names=[e.filename for e in members]
    if len(names)!=len(set(names)) or not EXACT_FILES.issubset(names):
        raise RuntimeError('Incomplete or duplicate overlay contents')
    return members


def install(blob, root):
    root=root.resolve()
    if not (root/'server.properties').is_file() or not (root/'_crafty/server-mods.tsv').is_file():
        raise RuntimeError('This is not the expected existing Amber & Arcana server root: '+str(root))
    ensure_stopped(root)
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        members=checked_members(archive,root)
        if archive.testzip() is not None:
            raise RuntimeError('ZIP integrity failure')
        metadata=json.loads(archive.read('_crafty/build-summary.json'))
        if metadata['pack_version'] != VERSION:
            raise RuntimeError('Release metadata does not match updater')
        owner=(root/'_crafty/server-mods.tsv').stat()
        backup_base=root/'_amber_updates'
        if backup_base.is_symlink():
            raise RuntimeError('Backup directory must not be a symlink')
        backup_base.mkdir(exist_ok=True)
        backup=Path(tempfile.mkdtemp(prefix=VERSION+'-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-',dir=backup_base))
        records=[]
        for entry in members:
            target=root/entry.filename
            existed=target.exists()
            if existed:
                if not target.is_file(): raise RuntimeError('Target is not a regular file: '+str(target))
                saved=backup/'files'/entry.filename
                saved.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(target,saved)
            records.append({'path':entry.filename,'existed':existed})
        (backup/'restore-manifest.json').write_text(json.dumps(records,indent=2)+'\n')
        ensure_stopped(root)
        applied=[]
        try:
            for entry in members:
                ensure_stopped(root)
                target=root/entry.filename
                target.parent.mkdir(parents=True,exist_ok=True)
                applied.append(next(r for r in records if r['path']==entry.filename))
                fd,tmp=tempfile.mkstemp(prefix='.amber-update-',dir=target.parent)
                try:
                    with os.fdopen(fd,'wb') as out: out.write(archive.read(entry))
                    os.chmod(tmp,0o644)
                    if os.geteuid()==0:
                        os.chown(tmp,owner.st_uid,owner.st_gid)
                        parent=target.parent
                        while parent!=root:
                            os.chown(parent,owner.st_uid,owner.st_gid)
                            parent=parent.parent
                    os.replace(tmp,target)
                finally:
                    if os.path.exists(tmp):os.unlink(tmp)
        except Exception:
            for record in reversed(applied):
                target=root/record['path']
                if record['existed']:
                    shutil.copy2(backup/'files'/record['path'],target)
                    if os.geteuid()==0: os.chown(target,owner.st_uid,owner.st_gid)
                else:
                    target.unlink(missing_ok=True)
            raise
    print(f'Applied Amber & Arcana {VERSION}. Backup of replaced files: {backup}')
    print('World and player data were not modified. This backup is not a full world backup.')
    print('Start this server in Crafty using AmberArcana-Crafty-Launcher.jar; let managed mod downloads finish.')
    print('Every player should import the matching 0.1.9-46 Client ZIP before reconnecting.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref',required=True,help='Published 40-character Git commit, pinning archive and checksums')
    parser.add_argument('--root',default=DEFAULT_ROOT)
    args=parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.ref):parser.error('--ref must be a full Git commit SHA')
    root=Path(args.root).resolve()
    ensure_stopped(root)
    base=f'https://raw.githubusercontent.com/skullrider0/Amber-Arcana/{args.ref}/dist/'
    with urllib.request.urlopen(base+'SHA256SUMS.txt',timeout=60) as response:
        checks=response.read().decode()
    wanted=[line.split()[0] for line in checks.splitlines() if line.split()[-1]==ARCHIVE]
    if len(wanted)!=1:raise RuntimeError('Release checksum missing or ambiguous')
    print('Downloading '+ARCHIVE,flush=True)
    with urllib.request.urlopen(base+ARCHIVE,timeout=120) as response:
        blob=response.read()
    if hashlib.sha256(blob).hexdigest()!=wanted[0]:raise RuntimeError('Downloaded overlay checksum mismatch')
    install(blob,root)


if __name__=='__main__':
    main()
