p = 'proj/tools/pdf_glyph_text.py'
s = open(p).read()

old = """            for e in d['entries']:
                e['_shapes'] = []
"""
new = """            for e in d['entries']:
                e['_shapes'] = []
                e['_fonts'] = {k[0] for k in e.get('keys', [])}
"""
assert old in s; s = s.replace(old, new)

old = """        if t is not None:
            tabs = [t] + [x[2] for x in self.tb.math if x[2] is not t]
        else:
            tabs = [x[2] for x in self.tb.pua]
        if h == 'ambig':
"""
new = """        # 제 표를 먼저 본다. 같은 윤곽선이 다른 표에 들어 있을 수도 있다(EH·TK·ASusic·Amsusic은 글리프를 함께 쓰고,
        # 수식 글꼴의 글리프가 본문 글꼴 PUA 칸에 묶인 경우도 있다). 다른 표의 항목은 '전수 조사에서 바로 이 글꼴 이름이
        # 그 모양을 쓴 적이 있을 때'만 받아들인다.
        if t is not None:
            own = [t]
            tabs = [t] + [x[2] for x in self.tb.math if x[2] is not t] + [x[2] for x in self.tb.pua]
        else:
            own = [x[2] for x in self.tb.pua]
            tabs = own + [x[2] for x in self.tb.math]
        if h == 'ambig':
"""
assert old in s; s = s.replace(old, new)

old = """        for tt in tabs:
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
new = """        for tt in tabs:
            e = tt['by_hash'].get(h)
            if e is None:
                continue
            if any(tt is o for o in own):
                return self._out(e, mark, '모양 일치', cname, ucs)
            if cname in e['_fonts']:
                return self._out(e, mark, '모양 일치(다른 표에 든 같은 윤곽선)', cname, ucs)
        for tt in tabs:
            isown = any(tt is o for o in own)
            e = _tol_find(sh, tt['by_key'].get((cname, ucs), ()))
            if e is None and isown:
                e = _tol_find(sh, tt['by_ucs'].get(ucs, ()))
            if e is None and isown and ucs == 0xFFFD:
                e = _tol_find(sh, tt['entries'])
            if e is not None:
                return self._out(e, mark, '모양 거의 일치', cname, ucs)
"""
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
