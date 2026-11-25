import json, re
fam = json.load(open('census_ko_fam.json'))
HY = re.compile(r'^(Haansoft-?Batang|Haansoft-Dotum|HaansoftBatang|\*옛한글|HCRBatang|T\d\d|\*신명-중명조|TT3678AC74tCID|NewGulim)$')
old = sym = 0; oldf = []; symf = []
for f, a in fam.items():
    n = sum(v for k, v in a['codes'].items() if 0xE000 <= int(k, 16) <= 0xF8FF)
    if not n: continue
    if HY.match(f): old += n; oldf.append((n, f, a['pdfs']))
    else: sym += n; symf.append((n, f, a['pdfs']))
print('옛한글 글꼴 PUA', old, '자,', len(oldf), '글꼴 /', '그 밖 글꼴 PUA', sym, '자,', len(symf), '글꼴 / 합', old + sym)
print('옛한글 글꼴:', ', '.join(f'{f}({n}자·{p}권)' for n, f, p in sorted(oldf, reverse=True)))
jam = sum(a['n'] for a in fam.values() if False)
