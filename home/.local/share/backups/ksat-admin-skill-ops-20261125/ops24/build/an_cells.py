# 전수 모양 조사 결과를 가족별로 요약한다
import sys, pickle, re, collections, json
import glyphcore as gc

D = pickle.load(open(sys.argv[1], 'rb'))
cl = D['clusters']; shapes = D['shapes']
FAM = [('HyhwpEQ', r'^HyhwpEQ'), ('HancomEQN', r'^HancomEQN'), ('EH', r'^EH[A-Za-z]'), ('Kab', r'^Kab'), ('Amsusic', r'^Amsusic'), ('ASusic', r'^ASusic'), ('GS', r'^GS(Medium|MediIta|Symbol)'), ('TK', r'^TK(up|yak|down)')]
OLD = re.compile(r'^(Haansoft|\*옛한글|HCRBatang|T\d\d$|\*신명-중명조|TT3678AC74tCID|NewGulim)')
HY = json.load(open('../hanyang_table_composed.json'))
HYK = set(int(k, 16) if isinstance(k, str) else k for k in (HY.get('map', HY)).keys()) if isinstance(HY, dict) else set()


def fam(cn):
    for nm, pat in FAM:
        if re.search(pat, cn):
            return nm
    return 'PUA:옛한글글꼴' if OLD.search(cn) else 'PUA:그밖'


BAD = ('noembed', 'nolink', 'ambig', 'norender')
st = collections.defaultdict(lambda: collections.Counter())
keyh = collections.defaultdict(set)
hkeys = collections.defaultdict(set)
for (cn, ucs, h), (n, npdf, smp) in cl.items():
    f = fam(cn)
    s = st[f]
    s['묶음'] += 1; s['글자'] += n
    if h in BAD:
        s['모양 없음:' + h] += n
    else:
        keyh[(f, cn, ucs)].add(h); hkeys[(f, h)].add((cn, ucs))
for f in st:
    ks = [k for k in keyh if k[0] == f]
    hs = [k for k in hkeys if k[0] == f]
    st[f]['(글꼴,코드) 쌍'] = len(ks)
    st[f]['모양 가짓수'] = len(hs)
    st[f]['모양 여럿인 쌍'] = sum(1 for k in ks if len(keyh[k]) > 1)
    st[f]['글꼴 이름'] = len({k[1] for k in ks})
for f, s in sorted(st.items(), key=lambda kv: -kv[1]['글자']):
    print(f, dict(s))
print('한양 표 코드 수', len(HYK))
# 모양 여럿인 쌍: 서로 얼마나 닮았나
import itertools
for f in st:
    multi = [k for k in keyh if k[0] == f and len(keyh[k]) > 1]
    sc = []
    for k in multi:
        hs = sorted(keyh[k], key=lambda h: -sum(cl[(k[1], k[2], h)][0] for _ in [0]))
        for a, b in itertools.combinations(hs[:6], 2):
            sc.append(gc.tol_score(shapes[a], shapes[b]))
    if sc:
        import numpy as np
        sc = np.array(sc)
        print(f, '모양 여럿인 쌍', len(multi), '짝 비교', len(sc), '0.97 이상', int((sc >= 0.97).sum()), '0.9~0.97', int(((sc >= 0.9) & (sc < 0.97)).sum()), '0.9 미만', int((sc < 0.9).sum()))
# PUA 그밖: 글꼴 이름 많은 순
oc = collections.Counter(); ok = collections.defaultdict(set)
for (cn, ucs, h), (n, npdf, smp) in cl.items():
    if fam(cn) == 'PUA:그밖':
        oc[cn] += n; ok[cn].add(ucs)
print('PUA 그밖 글꼴', len(oc), '종. 많은 순:')
for cn, n in oc.most_common(40):
    inhy = sum(1 for u in ok[cn] if u in HYK)
    print(f'   {cn[:34]:34s} {n:7d}자 코드 {len(ok[cn]):4d}종 (한양 표 안 {inhy})')
oc = collections.Counter(); ok = collections.defaultdict(set)
for (cn, ucs, h), (n, npdf, smp) in cl.items():
    if fam(cn) == 'PUA:옛한글글꼴':
        oc[cn] += n; ok[cn].add(ucs)
print('PUA 옛한글글꼴', len(oc), '종:')
for cn, n in oc.most_common(40):
    inhy = sum(1 for u in ok[cn] if u in HYK)
    print(f'   {cn[:34]:34s} {n:7d}자 코드 {len(ok[cn]):4d}종 (한양 표 안 {inhy})')
