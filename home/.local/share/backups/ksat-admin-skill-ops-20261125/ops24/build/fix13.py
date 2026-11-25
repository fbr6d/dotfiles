p = 'assemble.py'
s = open(p).read()
old = """ST = {'확정', '근사', '미확정'}; POS = {'base', 'sup', 'sub'}; ROLE = {'char', 'bar', 'radical', 'piece', 'accent', 'deco', 'space'}
"""
new = """ST = {'확정', '근사', '미확정'}; POS = {'base', 'sup', 'sub'}; ROLE = {'char', 'bar', 'radical', 'piece', 'accent', 'deco', 'space'}
# 모양만으로는 가릴 수 없는 글자 묶음(I·l·1, O·0, 대소문자)과 사소한 꼴 차이(쌍점·대괄호·가운뎃점·빗금·별표).
# 이 묶음 안에서 읽은 글자와 글자층 코드가 다르면, 그 글꼴의 코드가 믿을 만할 때 글자층 코드를 따른다.
FOLLOW_SETS = ['Il1|\\u2223', 'O0o', 'cC', 'sS', 'vV', 'wW', 'xX', 'zZ', 'uU', 'kK', 'pP', ':\\u2236', '[\\u3014', ']\\u3015', '\\u00b7\\u22c5\\u2219\\u2022', '/\\u2215\\u2044', '*\\u2217']
FOLLOW = {ch: i for i, st in enumerate(FOLLOW_SETS) for ch in st}
REL_MIN, REL_N = 0.6, 10          # 글꼴의 ASCII 코드 글리프 가운데 읽기가 코드와 같은 비율·개수의 하한
"""
assert old in s; s = s.replace(old, new)
old = """    os.makedirs(outdir, exist_ok=True)
    today = datetime.date.today().isoformat()
"""
new = """    rel = collections.defaultdict(lambda: [0, 0])
    for g, ents in tables.items():
        for e in ents:
            if e['status'] == '미확정':
                continue
            for cn, u, n in e['keys']:
                u = int(u, 16)
                if 0x21 <= u <= 0x7E:
                    rel[cn][1] += 1
                    if e['text'] == chr(u):
                        rel[cn][0] += 1
    nalt = altn = 0
    odd = []
    for g, ents in tables.items():
        if g in ('KO', 'SYM'):
            continue
        for e in ents:
            T = e['text']
            if e['status'] == '미확정' or len(T) != 1:
                continue
            alt = []
            for cn, u, n in e['keys']:
                K = chr(int(u, 16))
                a, b = rel[cn]
                if K == T or b < REL_N or a / b < REL_MIN:
                    continue
                if FOLLOW.get(K) is not None and FOLLOW.get(K) == FOLLOW.get(T):
                    alt.append([cn, u, K]); nalt += 1; altn += n
                elif 0x21 <= ord(K) <= 0x7E and 0x21 <= ord(T) <= 0x7E:
                    odd.append('%s %s: 읽기 %s ← 코드 %s (%s, %d자, 글꼴 일치 %d/%d)' % (g, e['sheet'], T, K, cn, n, a, b))
            if alt:
                e['alt'] = alt
    print('글자층 코드를 따르는 (항목, 글꼴·코드)', nalt, '쌍 ·', altn, '자')
    print('믿을 만한 글꼴인데 ASCII 읽기와 ASCII 코드가 다른 것(확인 거리)', len(odd))
    for o in odd[:40]:
        print('   ', o)
    os.makedirs(outdir, exist_ok=True)
    today = datetime.date.today().isoformat()
"""
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)

p = 'proj/tools/pdf_glyph_text.py'
s = open(p).read()
for old, new in [
    ("return self._out(next(iter(found.values())), mark, '모양 일치(같은 이름 글꼴 여럿 가운데 코드가 맞는 쪽)')",
     "return self._out(next(iter(found.values())), mark, '모양 일치(같은 이름 글꼴 여럿 가운데 코드가 맞는 쪽)', cname, ucs)"),
    ("return self._out(e, mark, '모양 일치')", "return self._out(e, mark, '모양 일치', cname, ucs)"),
    ("return self._out(e, mark, '모양 거의 일치')", "return self._out(e, mark, '모양 거의 일치', cname, ucs)"),
    ("""    def _out(e, mark, how):
        if e['status'] == '미확정':
            return (mark, '미확정', e.get('pos', 'base'), e.get('role', 'char'), e['id'], '표에서 아직 못 정한 글리프')
""",
     """    def _out(e, mark, how, cname=None, ucs=None):
        if e['status'] == '미확정':
            return (mark, '미확정', e.get('pos', 'base'), e.get('role', 'char'), e['id'], '표에서 아직 못 정한 글리프')
        for a in e.get('alt', ()):
            # 모양으로는 가릴 수 없는 글자(I·l, O·0 …): 표가 '이 글꼴은 코드가 믿을 만하다'고 적어 둔 경우 글자층 코드를 따른다
            if a[0] == cname and int(a[1], 16) == ucs:
                return (a[2], e['status'], e.get('pos', 'base'), e.get('role', 'char'), e['id'], how + ' · 모양이 같은 글자라 글자층 코드를 따름')
"""),
]:
    assert old in s, old[:50]
    s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
