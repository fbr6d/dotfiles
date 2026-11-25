p = 'glyphcore.py'
s = open(p).read()
old = """def _unesc(s):
    return _ESC.sub(lambda m: chr(int(m.group(1), 16)), s.lstrip('/'))
"""
new = """_ESCB = re.compile(rb'#([0-9A-Fa-f]{2})')


def _unesc(s):
    \"\"\"PDF 이름 값을 글자층이 쓰는 꼴(바이트를 라틴-1로 읽은 글)로 바꾼다.

    xref_get_key 는 이름의 바이트를 UTF-8(surrogateescape)로 읽어 주므로, 다시 바이트로 되돌린 뒤 라틴-1로 읽는다.
    \"\"\"
    s = s.lstrip('/')
    try:
        b = s.encode('utf-8', 'surrogateescape')
    except Exception:
        b = s.encode('utf-8', 'replace')
    b = _ESCB.sub(lambda m: bytes([int(m.group(1), 16)]), b)
    return b.decode('latin-1')
"""
assert old in s
s = s.replace(old, new)
old2 = """        for f in fl:
            xr = f[0]
            nm = self._names.get(xr)
            if nm is None:
                nm = self._names[xr] = font_names(self.doc, xr)
"""
new2 = """        for f in fl:
            xr = f[0]
            nm = self._names.get(xr)
            if nm is None:
                nm = font_names(self.doc, xr)
                if f[3]:
                    nm.add(f[3])
                self._names[xr] = nm
"""
assert old2 in s
s = s.replace(old2, new2)
open(p, 'w').write(s)
print('고침')
