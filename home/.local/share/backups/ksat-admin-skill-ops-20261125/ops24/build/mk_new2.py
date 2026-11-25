# 새 전수(Type3·새로 이은 글꼴 포함)를 앞 칸 목록에 합친다.
#  - 앞 칸과 겹치는 새 칸: 새로 생긴 모양(해시)을 그 앞 칸에 붙이고, 글꼴·코드 집계를 새 전수로 다시 센다.
#  - 앞 칸과 안 겹치는 새 칸: 눈으로 볼 범위(PUA·묶음 안)면 새 견본 묶음(KO3·SYM3)으로 낸다.
# 쓰기: /usr/bin/python3 mk_new2.py <cells.pkl(앞)> <cells_t3.pkl(새)> <census_shapes_t3.pkl> <cells_new.pkl> <cells_all.pkl>
import sys, pickle, collections
import glyphcore as gc
old = pickle.load(open(sys.argv[1], 'rb')); new = pickle.load(open(sys.argv[2], 'rb')); S = pickle.load(open(sys.argv[3], 'rb'))
assert old['paths'] == new['paths'], '목록 순서가 달라졌어요'
shapes = dict(old['shapes']); shapes.update(new['shapes'])
oldh = {}
for i, c in enumerate(old['cells']):
    for h in c['hashes']:
        oldh[h] = i
add = []; extra = collections.defaultdict(list); multi = 0; st = collections.Counter()
for c in new['cells']:
    O = {oldh[h] for h in c['hashes'] if h in oldh}
    if not O:
        st[(c['fam'], c.get('sheet'), c.get('inscope'))] += 1
        if c.get('sheet') in ('A', 'B', 'C') and c.get('inscope', True):
            c = dict(c)
            c['group'] = (c['fam'] + '3') if c['fam'] != 'PUA' else ('KO3' if c['sheet'] == 'C' else 'SYM3')
            add.append(c)
        continue
    for h in c['hashes']:
        if h in oldh:
            continue
        if len(O) == 1:
            i = next(iter(O))
        else:
            multi += 1
            i = max(O, key=lambda j: max(gc.tol_score(shapes[h], shapes[h2]) for h2 in old['cells'][j]['hashes']))
        extra[i].append(h)
for i, hs in extra.items():
    for h in hs:
        oldh[h] = i
newh = {}
for j, c in enumerate(add):
    for h in c['hashes']:
        newh[h] = j
bykey = collections.defaultdict(collections.Counter); bykey_new = collections.defaultdict(collections.Counter)
for (cn, u, h), (cnt, npdf, smp) in S['clusters'].items():
    i = oldh.get(h)
    if i is not None:
        bykey[i][(cn, u)] += cnt
    elif h in newh:
        bykey_new[newh[h]][(cn, u)] += cnt
cells2 = []; grown = collections.Counter(); nchar_before = nchar_after = 0
for i, c in enumerate(old['cells']):
    c = dict(c)
    nchar_before += c['n']
    if extra.get(i):
        c['hashes'] = list(c['hashes']) + extra[i]
        grown[c['fam']] += len(extra[i])
    if i in bykey:
        nk = dict(bykey[i])
        for k, v in c['keys'].items():
            nk.setdefault(k, v)
        c['keys'] = nk; c['n'] = sum(nk.values())
    nchar_after += c['n']
    cells2.append(c)
print('새 칸(앞 칸과 안 겹침):', {('%s/%s/%s' % k): v for k, v in sorted(st.items(), key=str)}, '→ 읽을 새 칸', len(add))
print('앞 칸에 붙인 새 모양', sum(len(v) for v in extra.values()), '개 (칸', len(extra), '개, 가족별', dict(grown), ') · 앞 칸 여럿과 겹쳐 닮은 쪽에 붙인 모양', multi)
print('앞 칸의 글자 수', nchar_before, '→', nchar_after)
pickle.dump({'paths': new['paths'], 'cells': add, 'shapes': shapes}, open(sys.argv[4], 'wb'))
pickle.dump({'paths': new['paths'], 'cells': cells2 + add, 'shapes': shapes, 'noshape': new.get('noshape'), 'fonts': new.get('fonts')}, open(sys.argv[5], 'wb'))
