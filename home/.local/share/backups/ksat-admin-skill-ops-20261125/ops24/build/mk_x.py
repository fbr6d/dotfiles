# 수식 글꼴의 글리프인데 본문 글꼴 PUA 칸으로 묶여 눈 확인 범위 밖에 남은 칸을 골라 낸다.
# 쓰기: /usr/bin/python3 mk_x.py <cells_all.pkl> <cells_x.pkl>
import sys, pickle, re, collections
MATH = re.compile(r'^(HyhwpEQ|HancomEQN|EH[A-Za-z]|Kab|Amsusic|ASusic|GS(Medium|MediIta|Symbol)|TK(up|yak|down))')
D = pickle.load(open(sys.argv[1], 'rb'))
out = []
for c in D['cells']:
    if c['fam'] != 'PUA' or c.get('inscope', True) or c.get('sheet') not in ('A', 'B', 'C'):
        continue
    mk = {k: v for k, v in c['keys'].items() if MATH.search(k[0])}
    if not mk:
        continue
    c = dict(c); c['group'] = 'SYM4'; c['sheet'] = 'A'; c['inscope'] = True
    out.append(c)
    print('  ', c['id'][:8], '수식 글꼴 쪽', sorted(((k[0], '%04X' % k[1], v) for k, v in mk.items()), key=lambda t: -t[2])[:3], '· 전체', c['n'])
print('고른 칸', len(out), '· 수식 글꼴 글자', sum(v for c in out for k, v in c['keys'].items() if MATH.search(k[0])))
pickle.dump({'paths': D['paths'], 'cells': out, 'shapes': D['shapes']}, open(sys.argv[2], 'wb'))
