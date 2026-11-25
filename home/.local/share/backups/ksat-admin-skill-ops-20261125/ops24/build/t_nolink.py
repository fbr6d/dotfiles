import pymupdf, re, collections, sys
import glyphcore as gc
R = '/home/leejaeik/Projects/ksat-10000/raw/수능자료/'
doc = pymupdf.open(R + '교과서/공통수학1-미래엔.pdf')
dg = gc.DocGlyphs(doc)
for pno in (20, 21, 60):
    page = doc[pno]
    n2x = dg.page_map(page)
    miss = collections.Counter()
    for sp in page.get_texttrace():
        if sp['font'] not in n2x: miss[sp['font']] += len(sp['chars'])
    if miss:
        print('쪽', pno, '못 이은 이름', dict(miss))
        fl = page.get_fonts(full=True)
        for f in fl:
            if any(k.split('+')[-1] in f[3] or f[3].split('+')[-1] in k for k in miss):
                print('    후보', f, gc.font_names(doc, f[0]))
                print('       ', doc.xref_object(f[0], compressed=True)[:300])
