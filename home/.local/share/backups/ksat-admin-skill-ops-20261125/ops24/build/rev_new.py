# 다시 볼 칸 목록(review2.pkl)에서, 앞서 이미 본 칸(<ops>/review/*.cells.json)을 뺀다.
# 쓰기: /usr/bin/python3 rev_new.py <review2.pkl> <ops 폴더> <review_new.pkl>
import sys, os, json, pickle, glob, collections
D = pickle.load(open(sys.argv[1], 'rb')); ops = sys.argv[2]
seen = set()
for d in ('review', 'review_new'):
    for fn in glob.glob(os.path.join(ops, d, '*.cells.json')):
        for no, ci in json.load(open(fn)).items():
            r = ci.get('rev') or {}
            seen.add('%s#%s' % (r.get('sheet'), r.get('no')))
keep = []
kinds = collections.Counter()
for c in D['cells']:
    r = c.get('rev') or {}
    k = '%s#%s' % (r.get('sheet'), r.get('no'))
    fl = [f for f in r.get('flags', []) if not f.startswith('무작위')]
    if k in seen:
        continue
    keep.append(c)
    kinds['까닭 있음' if fl else '무작위 표본'] += 1
print('앞서 본 칸', len(seen), '· 이번 목록', len(D['cells']), '· 새로 볼 칸', len(keep), dict(kinds))
D2 = dict(D); D2['cells'] = keep
pickle.dump(D2, open(sys.argv[3], 'wb'))
