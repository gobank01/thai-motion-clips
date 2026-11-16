import os, sys, json; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'ten', 'shared'))
from mixkit import Mix
o = sys.argv[1]; ev = json.load(open(os.path.join(o, 'events.json')))['ev']
m = next((e for e in ev if e['type'] == '_music'), {}); kw = {k: (tuple(v) if isinstance(v, list) else v) for k, v in m.items() if k not in ('t', 'type', 'db', 'verb')}
Mix(o).score(**kw).foley().write(music_db=m.get('db', -14), verb=m.get('verb', .25))
