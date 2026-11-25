# 칸 목록에서 기계 비교 점수 분포를 본다
import sys, pickle, collections
D = pickle.load(open(sys.argv[1], 'rb'))
cells = D['cells']


def cat(u):
    if 0xE000 <= u <= 0xF8FF: return 'PUA'
    if u == 0xFFFD: return 'FFFD'
    if u < 0x20 or 0x7F <= u < 0xA0: return '제어'
    if u < 0x80: return 'ASCII 영숫자' if chr(u).isalnum() else 'ASCII 기호'
    if u < 0x100: return '라틴-1'
    return '그 밖'


st = collections.defaultdict(lambda: collections.Counter())
ex = collections.defaultdict(list)
for c in cells:
    if c['fam'] == 'PUA' or c['sheet'] == 'space':
        continue
    k = cat(c['label'])
    s = st[(c['fam'], k)]
    s['칸'] += 1; s['자'] += c['n']
    if c['sheet'] == 'B':
        s['B'] += 1; s['B자'] += c['n']
    r = c.get('label_rank'); ls = c.get('label_score')
    if r is not None:
        s['1등' if r == 1 else ('2~3등' if r <= 3 else '4등 밖')] += 1
        if ls >= 0.8: s['점수0.8↑'] += 1
        elif ls >= 0.7: s['점수0.7~0.8'] += 1
        else: s['점수0.7↓'] += 1
        if k == 'ASCII 영숫자' and c['sheet'] == 'A' and len(ex[c['fam']]) < 14:
            ex[c['fam']].append((chr(c['label']), r, round(ls, 2), [(t[0], round(t[1], 2)) for t in c['top'][:3]], c['n']))
for k, s in sorted(st.items()):
    print(k, dict(s))
for f, l in ex.items():
    print(f, 'A로 간 영숫자 예:')
    for e in l: print('    ', e)
