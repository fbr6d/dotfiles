import json, collections, re, pymupdf
R = '/home/leejaeik/Projects/ksat-10000/raw/수능자료/'
rows = [json.loads(l) for l in open('census_math.jsonl')]
ex = [r for r in rows if r['path'].startswith('시험지/평가원원본') and r.get('chars', 0) >= 200 and 'HyhwpEQ' not in r.get('fonts', {}) and r['path'].split('/')[2] >= '2021']
print('2021년 뒤 HyhwpEQ 없는 문제 PDF', len(ex))
names = collections.Counter(re.sub(r'^\d{4}-\d{2}_\d{4}학년도_', '', r['path'].split('/')[-1])[:60] for r in ex)
for n, c in names.most_common(8): print('  ', c, n)
r = ex[0]; print(r['path'], r['pages'], r['chars'], r.get('producer'))
doc = pymupdf.open(R + r['path'])
fc = collections.Counter()
for pg in doc:
    for sp in pg.get_texttrace(): fc[sp['font']] += len(sp['chars'])
print(dict(fc.most_common(12)))
print('1쪽 그림 요소', len(doc[0].get_drawings()), '이미지', len(doc[0].get_images()))
print(doc[0].get_text()[:300].replace('\n', '⏎'))
