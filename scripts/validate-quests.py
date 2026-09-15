#!/usr/bin/env python3
"""Validate FTB Quests SNBT, references and the AA-006 reward regression.

Install with: python3 -m pip install -r scripts/requirements-quests.txt
"""
from pathlib import Path
import re
import nbtlib

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / 'server/config/ftbquests/quests'
CLIENT = ROOT / 'client/overrides/config/ftbquests/quests'


def validate():
    paths = sorted(SERVER.rglob('*.snbt'))
    assert {p.relative_to(SERVER) for p in paths} == {p.relative_to(CLIENT) for p in CLIENT.rglob('*.snbt')}
    docs = {}
    for path in paths:
        rel = path.relative_to(SERVER)
        assert path.read_bytes() == (CLIENT / rel).read_bytes(), f'Client/server mismatch: {rel}'
        docs[rel] = nbtlib.parse_nbt(path.read_text())
    ids, quests, tables = set(), {}, {}

    def register(obj):
        key = str(obj['id'])
        assert re.fullmatch(r'[0-9A-F]{16}', key), f'Invalid ID: {key}'
        assert key not in ids, f'Duplicate ID: {key}'
        ids.add(key)

    def item(value):
        if isinstance(value, nbtlib.Compound):
            assert int(value.get('Count', 0)) > 0, f'Empty item stack: {value}'
            value = value['id']
        assert re.fullmatch(r'[a-z0-9_.-]+:[a-z0-9_./-]+', str(value)), value
        assert str(value) not in ('minecraft:air', 'ftbquests:missing_item'), value

    for rel, doc in docs.items():
        if rel.parts[0] == 'chapters':
            register(doc)
            for quest in doc['quests']:
                register(quest)
                quests[str(quest['id'])] = quest
                for obj in [*quest['tasks'], *quest.get('rewards', [])]:
                    register(obj)
                    if obj['type'] == 'item':
                        item(obj['item'])
                        assert int(obj.get('count', 1)) > 0
        elif rel.parts[0] == 'reward_tables':
            register(doc)
            tables[int(str(doc['id']), 16)] = doc
            assert int(doc['loot_size']) == 1, 'Expected one bundle per roll'
            assert float(doc.get('empty_weight', 0)) == 0
            assert len(doc['rewards']) >= 2
            for reward in doc['rewards']:
                assert reward['type'] == 'item'
                item(reward['item'])
                assert int(reward['count']) > 0
                assert float(reward['weight']) > 0, 'Zero weight grants a guaranteed extra reward'
            assert sum(float(r['weight']) for r in doc['rewards']) == 100
    visiting, done = set(), set()

    def visit(qid):
        assert qid not in visiting, f'Dependency cycle: {qid}'
        if qid in done:
            return
        visiting.add(qid)
        for dep in quests[qid].get('dependencies', []):
            assert str(dep) in quests, f'Missing dependency: {dep}'
            visit(str(dep))
        visiting.remove(qid)
        done.add(qid)

    random_rewards = 0
    for qid, quest in quests.items():
        visit(qid)
        for reward in quest.get('rewards', []):
            if reward['type'] == 'random':
                assert isinstance(reward['table_id'], nbtlib.Long), 'table_id must be a numeric SNBT long'
                assert int(reward['table_id']) in tables, 'Dangling random reward table'
                random_rewards += 1
    changed = [docs[Path('chapters') / f'{name}.snbt'] for name in ('getting_started', 'create_engineering')]
    for chapter in changed:
        for quest in chapter['quests']:
            assert quest['tasks']
            assert all(t['type'] == 'item' and int(t['consume_items']) == 0 for t in quest['tasks'])
            assert all(r['type'] in ('random', 'xp') for r in quest['rewards'])
            assert any(r['type'] == 'random' for r in quest['rewards'])
    assert len(quests) == 106 and len(tables) == 5 and random_rewards == 12
    print(f'Quest validation passed: {len(quests)} quests, {len(tables)} tables, {random_rewards} random rewards; item stacks, references, cycles and client/server parity checked.')


if __name__ == '__main__':
    validate()
