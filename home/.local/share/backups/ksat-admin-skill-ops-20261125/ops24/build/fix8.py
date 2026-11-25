p = 'proj/tools/pdf_glyph_text.py'
s = open(p).read()

# 1) 보통 글꼴의 U+FFFD: 글리프가 비어 있으면 공백으로 본다
old = """            if ucs == 0xFFFD:
                return ('⟦?⟧', '미확정', 'base', 'char', None, '글자층에 코드가 없음(U+FFFD)')
"""
new = """            if ucs == 0xFFFD:
                h = dg.span_hash(xrefs, gid) if xrefs else 'nolink'
                if h not in NOSHAPE and dg.shapes[h][2] == 0:
                    return (' ', '그대로', 'base', 'space', None, '코드 없는 빈 글리프를 공백으로 봄')
                return ('⟦?⟧', '미확정', 'base', 'char', None, '글자층에 코드가 없음(U+FFFD)')
"""
assert old in s; s = s.replace(old, new)

# 2) 같은 이름의 글꼴 객체가 여럿일 때: 표에 (글꼴 이름, 코드)와 함께 적힌 모양을 가진 쪽을 고른다
old = """        h = dg.span_hash(xrefs, gid)
        if h in NOSHAPE:
            return (mark, '미확정', 'base', 'char', None, '모양 확인 불가: ' + NOSHAPE_KO[h])
"""
new = """        h = dg.span_hash(xrefs, gid)
        if h == 'ambig':
            tabs = [t] if t is not None else [x[2] for x in self.tb.pua]
            found = {}
            for x in xrefs:
                hx = dg.glyph_hash(x, gid)
                for tt in tabs:
                    e = tt['by_hash'].get(hx)
                    if e is not None and any(k[0] == cname and int(k[1], 16) == ucs for k in e.get('keys', ())):
                        found[(e['text'], e.get('pos', 'base'), e['status'])] = e
            if len(found) == 1:
                return self._out(next(iter(found.values())), mark, '모양 일치(같은 이름 글꼴 여럿 가운데 코드가 맞는 쪽)')
        if h in NOSHAPE:
            return (mark, '미확정', 'base', 'char', None, '모양 확인 불가: ' + NOSHAPE_KO[h])
"""
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
