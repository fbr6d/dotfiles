p = 'mk_sheets.py'
s = open(p).read()
old = "        g = c['fam'] if c['fam'] != 'PUA' else ('KO' if c['sheet'] == 'C' else 'SYM')\n"
new = "        g = c.get('group') or (c['fam'] if c['fam'] != 'PUA' else ('KO' if c['sheet'] == 'C' else 'SYM'))\n"
assert old in s; s = s.replace(old, new)
# Type3 글꼴도 그릴 수 있게 dg.gray 를 쓴다
old = """                    f = dg.font(xref) if xref else None
                    if f is not None:
                        g = gc.render_gray(f, gid, gpx)
                        if g is not None:
                            item['glyph'] = (g[0], g[1], g[2].tobytes(), g[2].shape)
                            try:
                                item['adv'] = float(mupdf.fz_advance_glyph(f.this, gid, 0))
                            except Exception:
                                item['adv'] = None
"""
new = """                    g = dg.gray(xref, gid, gpx) if xref else None
                    if g is not None:
                        item['glyph'] = (g[0], g[1], g[2].tobytes(), g[2].shape)
                        item['adv'] = dg.advance(xref, gid)
"""
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)

p = 'assemble.py'
s = open(p).read()
old = "        name, t, g = m['sheet'], m['type'], m['group']\n"
new = "        name, t, g = m['sheet'], m['type'], m['group']\n        g = {'KO3': 'KO', 'SYM3': 'SYM'}.get(g, g[:-1] if g.endswith('3') and g[:-1] in FAM_RX else g)\n"
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)

p = 'proj/tools/pdf_glyph_text.py'
s = open(p).read()
old = """        if c['gid'] is not None and len(xr) >= 1:
            f = dg.font(xr[0])
            if f is not None:
                g = gc.render_gray(f, c['gid'], 40)
"""
new = """        if c['gid'] is not None and len(xr) >= 1:
            g = dg.gray(xr[0], c['gid'], 40)
"""
assert old in s; s = s.replace(old, new)
old = "        xr = name2x.get(font, ())\n"
new = "        xr = name2x.get(font) or n2x.get(font, ())\n"
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
