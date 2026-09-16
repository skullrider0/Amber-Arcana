#!/usr/bin/env python3
"""Pin Create: Easy Stone Generators on both sides without changing Create."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.1.9-43'
PROJECT=1206505
FILE=6224618
FILENAME='create_generators-1.0.0-forge-1.20.1.jar'
SHA512='757b86c857c81e9bca12b7308814699c5ecbb9cd34c9d43b614c3c76adc4208fc8edc58c907983b50b768020b8244f33dd6b9137172f5cdcfd1165c5badab961'

def save(path,data):path.write_text(json.dumps(data,indent=2)+'\n')

def main():
    p=ROOT/'client/manifest.json';m=json.loads(p.read_text())
    m['files']=[f for f in m['files'] if f['projectID']!=PROJECT]+[{'projectID':PROJECT,'fileID':FILE,'required':True}]
    m['files'].sort(key=lambda f:(f['projectID'],f['fileID']))
    m.update(version=VERSION,name='Amber & Arcana '+VERSION);save(p,m)
    p=ROOT/'server/_crafty/server-mods.tsv'
    lines=p.read_text().splitlines();header=lines[0]
    rows=[l.split('\t') for l in lines if l and not l.startswith('#')]
    rows=[r for r in rows if r[5]!=str(PROJECT)]
    rows.append([str(FILE),FILENAME,SHA512,'create-stone-generators','Create: Easy Stone Generators',str(PROJECT)])
    rows.sort(key=lambda r:(r[3].lower(),r[1].lower()))
    p.write_text(header+'\n'+'\n'.join('\t'.join(r) for r in rows)+'\n')
    for rel in ['server/_crafty/build-summary.json','server/pack-information/validation.json']:
        p=ROOT/rel;data=json.loads(p.read_text());data['pack_version']=VERSION
        data['stone_generators_0_1_9_43']={'project_id':PROJECT,'file_id':FILE,'filename':FILENAME,'sha512':SHA512,'mod_version':'1.0.0','create_version':'6.0.8','client_update_required':True,'server_update_required':True,'runtime_tested':False,'bee_integration_preserved':True}
        if rel.endswith('build-summary.json'):
            data.update(manifest_entries=len(m['files']),mod_metadata_entries=len(m['files']),server_mod_downloads=len(rows),server_mod_count=len(rows))
        save(p,data)
    p=ROOT/'scripts/validate.sh';t=p.read_text().replace('.version == "0.1.9-42"','.version == "0.1.9-43"').replace('.pack_version == "0.1.9-42"','.pack_version == "0.1.9-43"').replace('Amber & Arcana 0.1.9-42 static validation passed','Amber & Arcana 0.1.9-43 static validation passed')
    check='python3 "$repo_dir/scripts/validate-stone-generators.py"'
    if check not in t:t+='\n'+check+'\n'
    p.write_text(t)
    p=ROOT/'README.md';t=p.read_text()
    t=t.replace('Download Client 0.1.9-42','Download Client '+VERSION).replace('Download Crafty Server 0.1.9-42','Download Crafty Server '+VERSION).replace('Amber-and-Arcana-0.1.9-42-',f'Amber-and-Arcana-{VERSION}-').replace('| Pack | 0.1.9-42 |',f'| Pack | {VERSION} |').replace('| Client manifest entries | 290 + 1 local patched JAR |','| Client manifest entries | 291 + 1 local patched JAR |').replace('| Server managed mod entries | 270 |','| Server managed mod entries | 271 |')
    t=t.replace('(scripts/update-crafty-0.1.9-42.py)','(scripts/update-crafty-0.1.9-43.py)')
    if '### 0.1.9-43 stone generators' not in t:
        t+='\n\n### 0.1.9-43 stone generators\nAdds [Create: Easy Stone Generators 1.0.0 for Forge 1.20.1](https://www.curseforge.com/minecraft/mc-mods/create-stone-generators/files/6224618) to client and server. Includes six mixer/basin recipes for cobblestone, stone, obsidian, basalt, limestone and scoria. Both sides must update because the mod registers a required network channel. Keeps Create 6.0.8, all 0.1.9-42 bee data, quest progress and existing pack patches. The stopped-server updater backs up overwritten pack files and never writes world data.\n'
    p.write_text(t)
    p=ROOT/'CHANGELOG.md';t=p.read_text()
    if '## '+VERSION not in t:
        p.write_text('## '+VERSION+'\n\n- Add Create: Easy Stone Generators 1.0.0 (Forge 1.20.1) to both sides, with SHA-512-pinned server download.\n- Keep Create 6.0.8, bee recipes, quests, JEI and patched More Hitboxes unchanged.\n- Publish matching client/server archives and a checksummed stopped-server update command.\n\n'+t)
    print('Prepared '+VERSION+': Create Easy Stone Generators; 291 client entries, 271 managed server entries')

if __name__=='__main__':main()
