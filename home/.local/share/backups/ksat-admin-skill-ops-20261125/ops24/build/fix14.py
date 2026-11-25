p = 'proj/tools/pdf_glyph_text.py'
s = open(p).read()

# 1) 수식 글꼴: 같은 모양(같은 윤곽선)이 다른 가족의 표에 들어 있을 수 있다(EH·TK·ASusic·Amsusic은 글리프를 함께 쓴다).
#    제 가족 표를 먼저 보고, 없으면 다른 수식 표도 본다.
old = """        if h == 'ambig':
            tabs = [t] if t is not None else [x[2] for x in self.tb.pua]
            found = {}
"""
new = """        if t is not None:
            tabs = [t] + [x[2] for x in self.tb.math if x[2] is not t]
        else:
            tabs = [x[2] for x in self.tb.pua]
        if h == 'ambig':
            found = {}
"""
assert old in s; s = s.replace(old, new)
old = """        tabs = [t] if t is not None else [x[2] for x in self.tb.pua]
        for tt in tabs:
            e = tt['by_hash'].get(h)
            if e is not None:
                return self._out(e, mark, '모양 일치', cname, ucs)
        for tt in tabs:
            e = _tol_find(sh, tt['by_key'].get((cname, ucs), ()))
            if e is None:
                e = _tol_find(sh, tt['by_ucs'].get(ucs, ()))
            if e is None and ucs == 0xFFFD:
                e = _tol_find(sh, tt['entries'])
            if e is not None:
                return self._out(e, mark, '모양 거의 일치', cname, ucs)
"""
new = """        for tt in tabs:
            e = tt['by_hash'].get(h)
            if e is not None:
                return self._out(e, mark, '모양 일치' if (tt is t or t is None) else '모양 일치(다른 수식 글꼴 표의 같은 윤곽선)', cname, ucs)
        for tt in tabs:
            own = (tt is t or t is None)
            e = _tol_find(sh, tt['by_key'].get((cname, ucs), ()))
            if e is None and own:
                e = _tol_find(sh, tt['by_ucs'].get(ucs, ()))
            if e is None and own and ucs == 0xFFFD:
                e = _tol_find(sh, tt['entries'])
            if e is not None:
                return self._out(e, mark, '모양 거의 일치', cname, ucs)
"""
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)

p = 'assemble.py'
s = open(p).read()
old = """            tables[g].append(e)
            stat[(g, e['status'])] += 1
"""
new = """            g2 = g
            if g == 'KO' and e['status'] != '미확정' and not any(
                    0x1100 <= ord(ch) <= 0x11FF or 0xA960 <= ord(ch) <= 0xA97F or 0xD7B0 <= ord(ch) <= 0xD7FF or 0xAC00 <= ord(ch) <= 0xD7A3 for ch in e['text']):
                g2 = 'SYM'          # 옛한글 후보였지만 눈으로 보니 기호인 칸은 기호 표로 보낸다
            tables[g2].append(e)
            stat[(g2, e['status'])] += 1
"""
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
