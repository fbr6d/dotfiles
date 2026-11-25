import pymupdf, sys, hashlib, time
from pymupdf import mupdf
pymupdf.TOOLS.set_subset_fontnames(True)
path = open('../list_eq.txt').read().split('\n')[0]
doc = pymupdf.open(path)
page = doc[0]
fonts = page.get_fonts(full=True)
for f in fonts[:12]: print('  font', f)
tr = page.get_texttrace()
names = {}
for sp in tr:
    names.setdefault(sp['font'], []).extend(sp['chars'][:3])
for n, ch in names.items(): print('  span font', repr(n), len(ch), ch[:2])
# 글꼴 객체 잇기
def cand_names(doc, xref):
    out = set()
    t, v = doc.xref_get_key(xref, 'BaseFont'); out.add(v.lstrip('/'))
    t, v = doc.xref_get_key(xref, 'DescendantFonts')
    if t != 'null':
        import re
        m = re.search(r'(\d+) 0 R', v)
        if t == 'xref': 
            v2 = doc.xref_object(int(m.group(1)))
            m = re.search(r'(\d+) 0 R', v2)
        if m:
            d = int(m.group(1)); t2, v2 = doc.xref_get_key(d, 'BaseFont'); out.add(v2.lstrip('/'))
    return out
target = [n for n in names if 'HyhwpEQ' in n][0]
xr = [f[0] for f in fonts if target in cand_names(doc, f[0])]
print('대상', target, 'xref', xr)
name, ext, typ, buf = doc.extract_font(xr[0])
print('extract', name, ext, typ, len(buf))
font = pymupdf.Font(fontbuffer=buf)
ff = font.this
t0 = time.time()
seen = set()
for sp in tr:
    if sp['font'] != target: continue
    for (ucs, gid, org, bbox) in sp['chars']:
        if gid in seen: continue
        seen.add(gid)
        ctm = mupdf.FzMatrix(48, 0, 0, 48, 0, 0)
        try:
            pm = mupdf.fz_render_glyph_pixmap(ff, gid, ctm, mupdf.FzIrect(mupdf.fz_infinite_irect), 8)
            px = pymupdf.Pixmap(pm) if not isinstance(pm, pymupdf.Pixmap) else pm
            if len(seen) <= 6: print('  gid', gid, hex(ucs), 'pix', px.width, px.height, px.x, px.y, px.n, px.alpha, len(px.samples))
        except Exception as e:
            print('  render 실패', gid, type(e).__name__, str(e)[:150]); break
print('글리프', len(seen), '개', round(time.time() - t0, 3), 's')
