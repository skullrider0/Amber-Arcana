#!/usr/bin/env python3
"""Forge 1.20.1 data integration; no new mod JAR or world mutation."""
import hashlib
import importlib.util
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.1.9-42'
SPECIES = {
    'ferricore': ('Ferricore', 'iron', 1, 'raw_ferricore', 80, '#536e78', '#c4e1dc'),
    'blazegold': ('Blazegold', 'gold', 2, 'raw_blazegold', 60, '#a24a36', '#ffbf64'),
    'celestigem': ('Celestigem', 'diamond', 3, 'celestigem', 40, '#1d8e92', '#b0f3eb'),
    'eclipsealloy': ('Eclipse Alloy', 'netherite', 4, 'raw_eclipsealloy', 20, '#353647', '#989cb5'),
    'time_crystal': ('Time Crystal', None, 4, 'time_crystal', 10, '#1b8e3f', '#c4ffa3'),
}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def bee_condition(bee):
    return {'type': 'productivebees:bee_exists', 'bee': 'productivebees:' + bee}


def typed(item, bee):
    return {'type': 'forge:nbt', 'item': 'productivebees:' + item,
            'nbt': {'EntityTag': {'type': 'productivebees:' + bee}}}


def data_files():
    files = {}
    for bee, (name, source, tier, output, chance, primary, secondary) in SPECIES.items():
        cond = [{'type': 'forge:mod_loaded', 'modid': 'justdirethings'}]
        files[f'productivebees/justdirethings/{bee}.json'] = {
            'primaryColor': primary, 'secondaryColor': secondary,
            'flowerBlock': 'justdirethings:' + bee + '_block',
            'selfbreed': tier < 3, 'conditions': cond,
        }
        if source:
            files[f'recipes/bee_conversion/justdirethings/{bee}_bee.json'] = {
                'type': 'productivebees:bee_conversion', 'source': 'productivebees:' + source,
                'result': 'productivebees:' + bee,
                'item': {'item': f'justdirethings:gooblock_tier{tier}'},
                'conditions': cond + [bee_condition(source), bee_condition(bee)],
            }
        files[f'recipes/bee_produce/justdirethings/{bee}_bee.json'] = {
            'type': 'productivebees:advanced_beehive', 'ingredient': 'productivebees:' + bee,
            'results': [{'item': typed('configurable_honeycomb', bee)}],
            'conditions': cond + [bee_condition(bee)],
        }
        outputs = [{'item': {'item': 'justdirethings:' + output}, 'chance': chance},
                   {'item': {'item': 'productivebees:wax'}}]
        if bee == 'time_crystal':
            # 12.6.0 expects a fluid entry IN outputs, and integer percentage chances.
            outputs.append({'fluid': {'fluid': 'justdirethings:time_fluid'}, 'amount': 25})
        files[f'recipes/centrifuge/justdirethings/honeycomb_{bee}.json'] = {
            'type': 'productivebees:centrifuge',
            'ingredient': typed('configurable_honeycomb', bee),
            'outputs': outputs, 'conditions': cond + [bee_condition(bee)],
        }
    # Keep time crystals behind the existing high-tier resource and bee gates.
    result = typed('spawn_egg_configurable_bee', 'time_crystal')
    result.pop('type')
    files['recipes/shaped/amber_time_bee_spawn_egg.json'] = {
        'type': 'minecraft:crafting_shaped', 'pattern': ['PRP', 'EME', 'HCH'],
        'key': {'P': typed('spawn_egg_configurable_bee', 'celestigem'),
                'R': typed('spawn_egg_configurable_bee', 'draconic'),
                'E': {'item': 'justdirethings:time_crystal_block'},
                'M': typed('spawn_egg_configurable_bee', 'sculk'),
                'H': typed('spawn_egg_configurable_bee', 'eclipsealloy'),
                'C': {'item': 'justdirethings:time_fluid_bucket'}},
        'result': result,
        'conditions': [{'type': 'forge:mod_loaded', 'modid': 'justdirethings'}] +
                      [bee_condition(b) for b in ['time_crystal', 'celestigem', 'draconic', 'sculk', 'eclipsealloy']],
    }
    for base in [ROOT/'client/overrides', ROOT/'server']:
        for rel, value in files.items():
            write_json(base/'kubejs/data/productivebees'/rel, value)
        lang_path = base/'kubejs/assets/productivebees/lang/en_us.json'
        lang = json.loads(lang_path.read_text()) if lang_path.exists() else {}
        for bee, (name, *_) in SPECIES.items():
            lang['entity.productivebees.' + bee + '_bee'] = name + ' Bee'
        write_json(lang_path, lang)
    return files


def hid(seed):
    return f'{int.from_bytes(hashlib.sha256(("aa42:" + seed).encode()).digest()[:8], "big") & ((1<<63)-1):016X}'


def update_quests():
    spec = importlib.util.spec_from_file_location('bee_labels', ROOT/'scripts/hotfix-bee-cage-labels-0.1.9-31.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    path = ROOT/'client/overrides/config/ftbquests/quests/chapters/productive_bees.snbt'
    text = path.read_text()
    if 'AA42 bee integrations' in text:
        return
    blocks = [text[a:b] for a,b in helper.quest_positions(text)]
    by_title = {helper.quest_title(b): re.search(r'(?m)^\t{3}id: "([A-F0-9]+)"', b).group(1) for b in blocks}
    y_max = max(float(v) for v in re.findall(r'(?m)^\t{3}y: ([-\d.]+)d', text))
    table_ids = {}
    for tier in range(1,5):
        table = path.parent.parent/'reward_tables'/f'modroll_productive_bees_tier_{tier}.snbt'
        table_ids[tier] = int(re.search(r'(?m)^\s*id: "([A-F0-9]+)"', table.read_text()).group(1), 16)
    additions = []
    entries = []
    for i,(bee,(name,source,tier,*_)) in enumerate(SPECIES.items()):
        if source:
            desc = f'Convert a {source.capitalize()} Bee with Just Dire Things Goo Block Tier {tier}. Pollinate the {name} Block, then centrifuge its typed comb.'
            deps = [by_title[source.capitalize()+' Bee']]
        else:
            desc = 'Craft the Time Crystal Bee spawn egg in JEI using Celestigem, Eclipse Alloy, Sculk and Draconic bee eggs, Time Crystal Blocks and a Time Fluid Bucket. Pollinate a Time Crystal Block.'
            deps = [hid('quest:celestigem'), hid('quest:eclipsealloy')]
        entries.append((bee,name,tier,deps,desc,-6.0+i*3.0,y_max+3.0))
    entries.append(('draconic','Draconic',2,[by_title['Advanced Beehive']], 'Attract a Draconic Bee into an Obsidian Nest in the End with Dragon Breath. Use an advanced hive or Dragon Egg Hive to obtain its comb. JEI shows the nest attraction recipe.', -6.0,y_max+5.0))
    for i,(bee,name,tier,source) in enumerate([
        ('draconium','Draconium',2,'Draconic Bee'),
        ('awakened','Awakened',3,'Draconium Bee'),
        ('chaos','Chaos',4,'Awakened Bee')]):
        dep = hid('quest:draconic') if i == 0 else hid('quest:'+['draconium','awakened'][i-1])
        desc = ('Use Draconic Evolution Fusion Crafting to upgrade the previous bee spawn egg. '
                'Search the typed spawn egg in JEI: these are fusion recipes, not bee breeding recipes. '
                + ('Pollinate Draconium Blocks.' if i == 0 else 'Pollinate Awakened Draconium Blocks.' if i == 1 else 'Supply a Chaos Shard as the flowering item.'))
        entries.append((bee,name,tier,[dep],desc,-3.0+i*3.0,y_max+5.0))
    for bee,name,tier,deps,desc,x,y in entries:
        dep_text = '\n'.join('\t\t\t\t"'+d+'"' for d in deps)
        additions.append(f'''\t\t{{
\t\t\tdependencies: [
{dep_text}
\t\t\t]
\t\t\tdescription: [{json.dumps(desc)} "Carry this species' honeycomb to complete automatically. Existing bee progress is preserved."]
\t\t\tid: "{hid('quest:'+bee)}"
\t\t\trewards: [{{ id: "{hid('reward:'+bee)}", type: "loot", table_id: {table_ids[tier]}L, title: "Productive Bees Tier {tier} Roll" }}]
\t\t\tsubtitle: "AA42 bee integrations"
\t\t\ttasks: [{{
\t\t\t\tid: "{hid('task:'+bee)}"
\t\t\t\ttype: "item"
\t\t\t\ttitle: "Produce {name} Bee Honeycomb"
\t\t\t\titem: {{ Count: 1b, id: "productivebees:configurable_honeycomb", tag: {{ EntityTag: {{ type: "productivebees:{bee}" }} }} }}
\t\t\t\tmatch_nbt: true
\t\t\t\tweak_nbt_match: true
\t\t\t}}]
\t\t\ttitle: "{name} Bee"
\t\t\tx: {x}d
\t\t\ty: {y}d
\t\t}}''')
    # Optional expansion branches preserve already-earned Master Apiarist completion.
    _, end = helper.named_array(text, 'quests')
    text = text[:end].rstrip() + '\n' + '\n'.join(additions) + '\n\t' + text[end:]
    path.write_text(text)
    shutil.copyfile(path, ROOT/'server/config/ftbquests/quests/chapters/productive_bees.snbt')


def metadata():
    manifest_path = ROOT/'client/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest.update(name='Amber & Arcana '+VERSION, version=VERSION)
    write_json(manifest_path,manifest)
    for rel in ['server/_crafty/build-summary.json','server/pack-information/validation.json']:
        path=ROOT/rel
        data=json.loads(path.read_text())
        data['pack_version']=VERSION
        data['bee_integrations_0_1_9_42']={
            'new_species':list(SPECIES), 'new_recipes':15, 'new_quests':9,
            'draconic_species':['draconium','awakened','chaos'],
            'draconic_native_recipes_preserved':True, 'world_data_touched':False,
            'runtime_multiplayer_tested':False,
            'incompatible_requests':['Cobblegen Galore','Tiny Soldiers'],
        }
        write_json(path,data)
    p=ROOT/'scripts/validate.sh'
    t=p.read_text().replace('.version == "0.1.9-41"','.version == "0.1.9-42"').replace('.pack_version == "0.1.9-41"','.pack_version == "0.1.9-42"')
    t=t.replace('= "36" || { echo "Expected 36 disabled recipe overrides"','= "51" || { echo "Expected 36 disabled recipe overrides plus 15 bee recipes"')
    t=t.replace('Amber & Arcana 0.1.9-41 static validation passed','Amber & Arcana 0.1.9-42 static validation passed')
    check='python3 "$repo_dir/scripts/validate-bee-integrations.py"'
    if check not in t:t+='\n'+check+'\n'
    p.write_text(t)
    p=ROOT/'README.md'; t=p.read_text()
    # Repair stale current download links, without rewriting historical release notes.
    a=t.index('## Direct downloads'); b=t.index('## Current release')
    links=' · '.join(f'[{label}](https://github.com/skullrider0/Amber-Arcana/raw/refs/heads/main/dist/Amber-and-Arcana-{VERSION}-{suffix}.zip)' for label,suffix in [('Download Client '+VERSION,'Client'),('Download Crafty Server '+VERSION,'Server'),('Update existing Crafty server','Crafty-Update-Overlay')])
    t=t[:a]+'## Direct downloads\n\n'+links+'\n\n'+t[b:]
    t=re.sub(r'\| Pack \| .*? \|',f'| Pack | {VERSION} |',t)
    t=t.replace('Amber-and-Arcana-0.1.9-33-',f'Amber-and-Arcana-{VERSION}-')
    t=re.sub(r'\| Client manifest entries \|.*',f'| Client manifest entries | {len(manifest["files"])} + 1 local patched JAR |',t)
    t=re.sub(r'\| Server managed mod entries \|.*','| Server managed mod entries | 270 |',t)
    count=sum(len(re.findall(r'(?m)^\t{3}id: "',q.read_text())) for q in (ROOT/'client/overrides/config/ftbquests/quests/chapters').glob('*.snbt'))
    t=re.sub(r'\| Quests \|.*',f'| Quests | {count} across 28 chapters |',t)
    marker='### 0.1.9-42 bee integrations'
    if marker not in t:t+='\n\n'+marker+'\nAdds five Just Dire Things resource bees and nine bee quests. The full update overlay now includes KubeJS data/assets and release metadata, required for existing servers to receive recipes. See [bee integration notes](docs/bee-integrations-0.1.9-42.md) and [the stopped-server updater](scripts/update-crafty-0.1.9-42.py). Cobblegen Galore and Tiny Soldiers have no compatible 1.20.1 Forge release and are not added.\n'
    p.write_text(t)
    p=ROOT/'CHANGELOG.md';t=p.read_text()
    if '## '+VERSION not in t:p.write_text('## '+VERSION+'\n\n- Add Ferricore, Blazegold, Celestigem, Eclipse Alloy and Time Crystal bee definitions and 15 Forge 1.20.1 recipes.\n- Add nine species-specific bee quests; preserve all existing quest IDs and finale progress.\n- Include recipe data in the full Crafty update overlay; add checksummed stopped-server updater with rollback backup.\n- Repair stale current download links. No mod JAR additions: the two requested mods do not support 1.20.1 Forge.\n\n'+t)


if __name__=='__main__':
    data_files();update_quests();metadata()
    print('Prepared '+VERSION+' bee integration')
