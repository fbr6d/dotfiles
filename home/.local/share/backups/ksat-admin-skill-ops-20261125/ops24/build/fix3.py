p = 'mk_cells.py'
s = open(p).read()
old = "                ok = ls >= TH_SCORE and ls >= top - TH_GAP and u == c['label']\n"
new = "                r = c['label_rank']\n                ok = u == c['label'] and ls >= 0.60 and (r == 1 or (r <= 3 and ls >= top - 0.03))\n"
assert old in s; s = s.replace(old, new)
old = "    pickle.dump({'paths': D['paths'], 'cells': cells, 'shapes': shapes, 'noshape': dict(noshape)}, open(sys.argv[2], 'wb'))\n"
new = """    # 범위: 수식 가족은 전부, PUA 칸은 먼저 볼 묶음(국어·수학·과학 목록)에 나온 것만
    first = None
    if len(sys.argv) > 3:
        first = set(pickle.load(open(sys.argv[3], 'rb'))['clusters'].keys())
    sc = collections.Counter()
    for c in cells:
        if c['fam'] != 'PUA' or first is None:
            c['inscope'] = True
        else:
            c['inscope'] = any((cn, u, h) in first for (cn, u) in c['keys'] for h in c['hashes'])
        sc[(c['fam'], c.get('sheet'), c['inscope'])] += 1
    print('범위:', {k: v for k, v in sorted(sc.items()) if k[0] == 'PUA'})
    pickle.dump({'paths': D['paths'], 'cells': cells, 'shapes': shapes, 'noshape': dict(noshape), 'fonts': D.get('fonts')}, open(sys.argv[2], 'wb'))
"""
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
