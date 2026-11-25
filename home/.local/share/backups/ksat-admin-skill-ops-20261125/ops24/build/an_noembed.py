import pickle, collections, sys
import pymupdf, glyphcore as gc
D = pickle.load(open('census_first.pkl', 'rb'))
cl = D['clusters']; paths = D['paths']
c = collections.Counter(); ex = {}
for (cn, u, h), (n, npdf, smp) in cl.items():
    if h in ('noembed', 'nolink', 'ambig', 'norender'):
        c[(h, cn)] += n; ex.setdefault((h, cn), smp[0])
for (h, cn), n in c.most_common(14):
    s = ex[(h, cn)]
    doc = pymupdf.open(paths[s[0]]); page = doc[s[1]]
    fl = [f for f in page.get_fonts(full=True) if cn in gc.clean_name(f[3]) or any(gc.clean_name(x) == cn for x in gc.font_names(doc, f[0]))]
    print(f'{h:8s} {cn[:26]:26s} {n:6d}자  {paths[s[0]].split("/")[-1][:46]} 쪽{s[1]+1}  객체 {[(f[0], f[1], f[2]) for f in fl][:3]}')
