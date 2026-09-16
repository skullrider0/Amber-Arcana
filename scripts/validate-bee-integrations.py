#!/usr/bin/env python3
"""Validate Forge 1.20.1 bee schemas and actual packaged update payloads."""
import importlib.util
import json
import re
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.1.9-42'
SPECIES={'ferricore','blazegold','celestigem','eclipsealloy','time_crystal'}

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
    return obj


def main():
    client=ROOT/'client/overrides'
    server=ROOT/'server'
    data=client/'kubejs/data/productivebees'
    definitions={p.stem:json.loads(p.read_text()) for p in (data/'productivebees/justdirethings').glob('*.json')}
    assert set(definitions)==SPECIES
    recipes={p.relative_to(data).as_posix():json.loads(p.read_text()) for p in (data/'recipes').rglob('*.json')}
    assert len(recipes)==15
    for bee,definition in definitions.items():
        assert definition['conditions']==[{'type':'forge:mod_loaded','modid':'justdirethings'}]
        assert definition['flowerBlock']=='justdirethings:'+bee+'_block'
        hive=recipes[f'recipes/bee_produce/justdirethings/{bee}_bee.json']
        centrifuge=recipes[f'recipes/centrifuge/justdirethings/honeycomb_{bee}.json']
        assert hive['ingredient']=='productivebees:'+bee
        assert hive['results'][0]['item']==centrifuge['ingredient']
        assert centrifuge['ingredient']['nbt']['EntityTag']['type']=='productivebees:'+bee
        for output in centrifuge['outputs']:
            if 'item' in output:
                assert isinstance(output.get('chance',100),int) and 0<output.get('chance',100)<=100
        assert 'fluid' not in centrifuge, '1.21 root fluid field is not supported by 12.6.0'
        if bee!='time_crystal':
            conversion=recipes[f'recipes/bee_conversion/justdirethings/{bee}_bee.json']
            assert conversion['result']==hive['ingredient']
            assert conversion['source'] in {'productivebees:iron','productivebees:gold','productivebees:diamond','productivebees:netherite'}
    for recipe in recipes.values():
        raw=json.dumps(recipe)
        assert 'neoforge:' not in raw and 'components' not in raw
        assert {'type':'forge:mod_loaded','modid':'justdirethings'} in recipe['conditions']
    helper=load_module('labels',ROOT/'scripts/hotfix-bee-cage-labels-0.1.9-31.py')
    text=(client/'config/ftbquests/quests/chapters/productive_bees.snbt').read_text()
    added=[text[a:b] for a,b in helper.quest_positions(text) if 'AA42 bee integrations' in text[a:b]]
    assert len(added)==9
    for bee in SPECIES|{'draconic','draconium','awakened','chaos'}:
        matches=[b for b in added if f'type: "productivebees:{bee}"' in b]
        assert len(matches)==1 and 'match_nbt: true' in matches[0]
    # All quest IDs, including dependencies in additive branches, must resolve.
    all_ids=[]
    for chapter in (client/'config/ftbquests/quests/chapters').glob('*.snbt'):
        t=chapter.read_text()
        for a,b in helper.quest_positions(t):
            q=t[a:b]
            match=re.search(r'(?m)^\t{3}id: "([A-F0-9]+)"',q)
            assert match,(chapter,q[:80])
            all_ids.append(match.group(1))
    assert len(all_ids)==len(set(all_ids))
    for block in added:
        start,end=helper.named_array(block,'dependencies')
        assert set(re.findall(r'"([A-F0-9]{16})"',block[start:end])).issubset(all_ids)
    mods=(server/'_crafty/server-mods.tsv').read_text()
    assert '\tjust-dire-things-forge\t' in mods and '\tdraconic-evolution\t' in mods
    manifest=json.loads((ROOT/'client/manifest.json').read_text())
    pins={f['projectID']:f['fileID'] for f in manifest['files']}
    for project,fileid in [(1533501,8733229),(223565,6793843),(377897,5566102)]:
        assert pins[project]==fileid
    assert not ({1108467,1297089}&pins.keys()),'Incompatible requested mods must not be inserted'
    installer=load_module('installer',ROOT/'scripts/update-crafty-0.1.9-42.py')
    with zipfile.ZipFile(ROOT/f'dist/Amber-and-Arcana-{VERSION}-Crafty-Update-Overlay.zip') as update, zipfile.ZipFile(ROOT/f'dist/Amber-and-Arcana-{VERSION}-Client.zip') as clientzip, zipfile.ZipFile(ROOT/f'dist/Amber-and-Arcana-{VERSION}-Server.zip') as serverzip:
        installer.checked_members(update,server)
        for p in data.rglob('*.json'):
            rel=p.relative_to(client).as_posix()
            expected=p.read_bytes()
            assert (server/rel).read_bytes()==expected
            assert update.read(rel)==expected
            assert clientzip.read('overrides/'+rel)==expected
            assert serverzip.read(rel)==expected
        lang='kubejs/assets/productivebees/lang/en_us.json'
        assert update.read(lang)==clientzip.read('overrides/'+lang)==serverzip.read(lang)
    print('Bee integration validation passed: 5 species, 15 recipes, 9 quests, complete client/server/update archives')

if __name__=='__main__':main()
