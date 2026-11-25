import pymupdf, collections
doc = pymupdf.open('/home/leejaeik/Projects/ksat-10000/raw/수능자료/교과서/대수-천재.pdf')
page = doc[20]
print('get_fonts:', [(x[0], x[3], x[4]) for x in page.get_fonts(full=True)][:8])
tt = page.get_texttrace()
print('texttrace 글꼴 이름:', sorted({sp['font'] for sp in tt})[:12])
print('span 키:', list(tt[0].keys()))
sp = [s for s in tt if 'susic' in s['font'].lower()][:2]
for s in sp: print({k: (v if k != 'chars' else v[:3]) for k, v in s.items()})
