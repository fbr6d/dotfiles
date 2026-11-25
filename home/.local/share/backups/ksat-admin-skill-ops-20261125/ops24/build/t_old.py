import sys, pickle, collections, re
import pymupdf
from pymupdf import mupdf
import glyphcore as gc

D = pickle.load(open('census_shapes.pkl.part.pkl', 'rb'))
paths = D['paths']
p = [x for x in paths if '2025-06_2026학년도_모의평가_한국교육과정평가원_국어_문제' in x][0]
doc = pymupdf.open(p); page = doc[17]
for f in page.get_fonts(full=True):
    print(f, sorted(gc.font_names(doc, f[0])))
    if '*' in f[3] or f[2] == 'Type0':
        print('    ', doc.xref_object(f[0], compressed=True)[:200])
        t, v = doc.xref_get_key(f[0], 'DescendantFonts')
        print('     Desc', t, v[:120])
print([ (sp['font'], len(sp['chars'])) for sp in page.get_texttrace() if '¿' in sp['font']][:3])
# pdf_load_font 시험
pdf = pymupdf._as_pdf_document(doc)
for f in page.get_fonts(full=True)[:3]:
    try:
        obj = mupdf.pdf_new_indirect(pdf, f[0], 0)
        fd = mupdf.pdf_load_font(pdf, mupdf.PdfObj(), obj)
        print('pdf_load_font OK', f[0], type(fd).__name__, [a for a in dir(fd) if 'font' in a.lower()][:8])
        raw = fd.m_internal.font
        ff = mupdf.FzFont(mupdf.ll_fz_keep_font(raw))
        print('   이름', mupdf.fz_font_name(ff))
    except Exception as e:
        print('pdf_load_font 실패', f[0], type(e).__name__, str(e)[:200])
