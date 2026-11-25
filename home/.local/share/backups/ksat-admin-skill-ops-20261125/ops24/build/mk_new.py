# Type3 글꼴까지 넣은 새 전수에서, 앞 칸 목록에 없던 칸만 골라 낸다
# 쓰기: /usr/bin/python3 mk_new.py <cells.pkl(앞)> <cells_t3.pkl(새)> <cells_new.pkl> <cells_all.pkl>
import sys, pickle, collections
old = pickle.load(open(sys.argv[1], 'rb')); new = pickle.load(open(sys.argv[2], 'rb'))
oldh = set()
for c in old['cells']:
    oldh.update(c['hashes'])
add = []
st = collections.Counter()
for c in new['cells']:
    if any(h in oldh for h in c['hashes']):
        continue
    st[(c['fam'], c.get('sheet'), c.get('inscope'))] += 1
    if c.get('sheet') in ('A', 'B', 'C') and c.get('inscope', True):
        c = dict(c)
        c['group'] = (c['fam'] + '3') if c['fam'] != 'PUA' else ('KO3' if c['sheet'] == 'C' else 'SYM3')
        add.append(c)
print('새 칸:', {('%s/%s/%s' % k): v for k, v in sorted(st.items(), key=lambda kv: str(kv[0]))})
fc = collections.Counter()
for c in add:
    fc[(c['group'], max(c['keys'].items(), key=lambda kv: kv[1])[0][0])] += 1
print('읽을 새 칸', len(add), dict(fc.most_common(30)))
shapes = dict(old['shapes']); shapes.update(new['shapes'])
pickle.dump({'paths': new['paths'], 'cells': add, 'shapes': shapes}, open(sys.argv[3], 'wb'))
assert old['paths'] == new['paths'], '목록 순서가 달라졌어요'
pickle.dump({'paths': new['paths'], 'cells': old['cells'] + add, 'shapes': shapes, 'noshape': new.get('noshape'), 'fonts': new.get('fonts')}, open(sys.argv[4], 'wb'))
print('모양 없음(새 전수):', sum((new.get('noshape') or {}).values()))
ns = collections.Counter()
for (f, cn, h), n in (new.get('noshape') or {}).items():
    ns[(f, h)] += n
print('   ', dict(ns))
