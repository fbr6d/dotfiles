p = 'glyphcore.py'
s = open(p).read()
old = """    def _is_t3(self, xref):
"""
new = """    def gray_any(self, xrefs, gid, px):
        \"\"\"같은 이름의 글꼴 객체가 여럿이면 그릴 수 있는 첫 객체로 그린다.\"\"\"
        for x in xrefs:
            g = self.gray(x, gid, px)
            if g is not None and g[2].size:
                return g
        return None

    def _is_t3(self, xref):
"""
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)

p = 'mk_sheets.py'
s = open(p).read()
old = """                    g = dg.gray(xref, gid, gpx) if xref else None
"""
new = """                    cands = [xref] if xref else []
                    if xref:
                        if pno not in maps:
                            maps[pno] = dg.page_map(page)
                        for lst in maps[pno].values():
                            if lst and lst[0] == xref:
                                cands += [x for x in lst[1:] if x not in cands]
                    g = dg.gray_any(cands, gid, gpx)
"""
assert old in s; s = s.replace(old, new)
old = """        pages = {}
        for (cid, slot, pno, ox, oy, size, gid, xref, gpx, cpx, cwem, chem, tick) in reqs:
"""
new = """        pages = {}
        maps = {}
        for (cid, slot, pno, ox, oy, size, gid, xref, gpx, cpx, cwem, chem, tick) in reqs:
"""
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)

p = 'proj/tools/pdf_glyph_text.py'
s = open(p).read()
old = "            g = dg.gray(xr[0], c['gid'], 40)\n"
new = "            g = dg.gray_any(xr, c['gid'], 40)\n"
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
