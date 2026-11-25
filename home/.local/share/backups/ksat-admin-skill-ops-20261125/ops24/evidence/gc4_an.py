import pickle, collections, hashlib
G = pickle.load(open('gc4_textbook.pkl', 'rb'))
def nh(g):
    u = g['upm'] or 1000
    s = repr([(op, tuple(tuple(round(c * 1000 / u / 4) for c in pt) if pt is not None else None for pt in pts)) for op, pts in g['rec']])
    return hashlib.md5(s.encode()).hexdigest()[:12]
out = [k for k in G if k[1].startswith('h:')]
print('upm 분포', collections.Counter((G[k]['upm'], G[k]['ext']) for k in out))
rev = collections.defaultdict(set); revn = collections.Counter(); rev2 = collections.defaultdict(set)
for k in out:
    for u, n in G[k]['ucs'].items():
        rev[(k[0], u)].add(k[1]); rev2[(k[0], u)].add(nh(G[k])); revn[(k[0], u)] += n
print('(글꼴, 뽑힌 글자) 쌍', len(rev), '→ 윤곽선 여러 가지', sum(len(v) > 1 for v in rev.values()), '→ 크기 맞춘 뒤에도 여러 가지', sum(len(v) > 1 for v in rev2.values()))
ex = [k for k in rev if len(rev2[k]) > 1]
for k in sorted(ex, key=lambda k: -revn[k])[:6]:
    ks = [kk for kk in out if kk[0] == k[0] and k[1] in G[kk]['ucs']]
    print('  ', k[0], repr(chr(k[1])), [(G[kk]['upm'], G[kk]['ext'], len(G[kk]['rec']), dict(G[kk]['books']).keys().__len__(), G[kk]['n'], G[kk]['occ'][0][:2]) for kk in ks])
# 글꼴 객체 연결 실패가 어느 글꼴에서 났는지
no = collections.Counter(); non = collections.Counter()
for k in G:
    if k[1].startswith('k:'):
        no[k[0]] += 1; non[k[0]] += G[k]['n']
print('윤곽선 없는 열쇠가 많은 글꼴:', [(f, no[f], non[f]) for f, _ in non.most_common(12)])
