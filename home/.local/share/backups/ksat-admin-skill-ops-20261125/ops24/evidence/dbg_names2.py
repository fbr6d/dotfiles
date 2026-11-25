import pymupdf, collections, re
pymupdf.TOOLS.set_subset_fontnames(True)
doc = pymupdf.open('/home/leejaeik/Projects/ksat-10000/raw/수능자료/교과서/공통수학1-미래엔.pdf')
page = doc[30]
gf = page.get_fonts(full=True)
print('get_fonts EH:', [(x[0], x[1], x[2], x[3], x[5], x[6]) for x in gf if 'EH' in x[3]][:10])
print('texttrace EH:', sorted({sp['font'] for sp in page.get_texttrace() if 'EH' in sp['font']})[:10])
x = [x for x in gf if 'EHsang' in x[3]][0][0]
print(doc.xref_object(x, compressed=True)[:400])
