import pickle, collections
G = pickle.load(open('gc3_textbook.pkl', 'rb'))
out = [k for k in G if k[1].startswith('h:')]; noout = [k for k in G if k[1].startswith('k:')]
print('윤곽선 있는 (글꼴, 윤곽선) 종', len(out), '글자', sum(G[k]['n'] for k in out))
print('윤곽선 없는 (글꼴, 코드) 종', len(noout), '글자', sum(G[k]['n'] for k in noout))
multi_u = [k for k in out if len(G[k]['ucs']) > 1]; multi_k = [k for k in out if len(G[k]['keys']) > 1]
print('같은 윤곽선인데 뽑힌 글자가 여러 가지', len(multi_u), '/ 글리프 번호가 여러 가지', len(multi_k))
for k in multi_u[:12]:
    g = G[k]; print('  ', k[0], {f'U+{u:04X}{chr(u)!r}': n for u, n in g['ucs'].items()}, dict(g['keys']), dict(g['books']))
# 뽑힌 글자 종류별
cat = collections.Counter(); catn = collections.Counter()
for k in out + noout:
    g = G[k]; u = g['ucs'].most_common(1)[0][0]
    c = 'PUA' if 0xE000 <= u <= 0xF8FF else 'U+FFFD' if u == 0xFFFD else '라틴-1 보충(80-FF)' if 0x80 <= u <= 0xFF else '제어문자(<20)' if u < 0x20 else 'ASCII 영문·숫자' if (u < 0x80 and chr(u).isalnum()) else 'ASCII 기호' if u < 0x80 else '한글' if 0xAC00 <= u <= 0xD7A3 else '그 밖 유니코드'
    cat[c] += 1; catn[c] += g['n']
print('뽑힌 글자 종류별 (글리프 종 / 글자 수):')
for c, n in cat.most_common(): print(f'   {c:18s} {n:4d}종 {catn[c]:7d}자')
shared = sum(1 for k in out if len(G[k]['books']) > 1)
print('두 책 이상에 같은 윤곽선으로 나온 글리프', shared)
fams = collections.Counter(k[0] for k in out + noout)
print('글꼴 이름', len(fams))
