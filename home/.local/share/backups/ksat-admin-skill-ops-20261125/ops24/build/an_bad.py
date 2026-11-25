# 모양을 못 구한 묶음(nolink·ambig·noembed)을 글꼴 이름별로 보고, 한 권을 골라 글꼴 객체를 들여다본다
import sys, pickle, collections, re
import pymupdf
import glyphcore as gc

D = pickle.load(open(sys.argv[1], 'rb'))
cl = D['clusters']; paths = D['paths']
bad = collections.defaultdict(lambda: [0, None])
for (cn, ucs, h), (n, npdf, smp) in cl.items():
    if h in ('nolink', 'ambig', 'noembed', 'norender'):
        b = bad[(h, cn)]
        b[0] += n
        if b[1] is None:
            b[1] = smp[0]
tot = collections.Counter()
for (h, cn), (n, s) in bad.items():
    tot[h] += n
print(dict(tot))
shown = 0
for (h, cn), (n, s) in sorted(bad.items(), key=lambda kv: -kv[1][0])[:14]:
    idx, pno = s[0], s[1]
    print(f'{h:8s} {cn[:28]:28s} {n:6d}자  예: {paths[idx].split("/")[-1][:50]} 쪽 {pno + 1}')
    if shown < 6:
        shown += 1
        doc = pymupdf.open(paths[idx]); page = doc[pno]
        names = collections.Counter(sp['font'] for sp in page.get_texttrace() if gc.clean_name(sp['font']) == cn)
        print('      글자층 이름:', dict(names))
        for f in page.get_fonts(full=True):
            nm = gc.font_names(doc, f[0])
            if any(gc.clean_name(x) == cn for x in nm) or f[2] == 'Type3' or cn.split('-')[0] in f[3]:
                print('      글꼴 객체:', f, sorted(nm)[:3])
