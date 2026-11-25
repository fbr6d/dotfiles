"""수학 교과서 PDF의 글꼴 객체 조사 (읽기 전용): 종류·인코딩·ToUnicode·글꼴 파일 형식"""
import collections, re, sys, json
import pymupdf
ROOT = '/home/leejaeik/Projects/ksat-10000/raw/수능자료/교과서/'
BOOKS = sys.argv[1:] or ['미적분Ⅰ-천재.pdf', '대수-천재.pdf', '확률과통계-천재.pdf', '공통수학1-미래엔.pdf', '공통수학2-미래엔.pdf']
out = {}
for b in BOOKS:
    doc = pymupdf.open(ROOT + b)
    meta = doc.metadata
    fonts = {}   # xref -> info
    pages_of = collections.Counter()
    for pno in range(len(doc)):
        for xref, ext, typ, base, name, enc in doc.get_page_fonts(pno):
            pages_of[xref] += 1
            if xref not in fonts:
                fonts[xref] = dict(ext=ext, type=typ, base=base, enc=enc)
    # 기본 이름(부분집합 꼬리표 제거)별로 묶기
    by = collections.defaultdict(list)
    for x, f in fonts.items():
        nm = re.sub(r'^[A-Z]{6}\+', '', f['base'])
        by[nm].append(x)
    print(f'== {b}: 쪽 {len(doc)}, 만든 프로그램 {meta.get("producer")!r} / {meta.get("creator")!r}, 글꼴 객체 {len(fonts)}개, 기본 이름 {len(by)}종')
    rows = []
    for nm, xs in sorted(by.items(), key=lambda kv: -sum(pages_of[x] for x in kv[1])):
        f = fonts[xs[0]]
        obj = doc.xref_object(xs[0], compressed=True)
        tou = sum('/ToUnicode' in doc.xref_object(x, compressed=True) for x in xs)
        rows.append((nm, len(xs), sum(pages_of[x] for x in xs), f['type'], f['ext'], f['enc'], tou))
    for r in rows[:60]:
        print(f'   {r[0][:34]:34s} 객체 {r[1]:4d} 쪽합 {r[2]:5d} {r[3]:9s} {r[4]:5s} enc={r[5]!s:22s} ToUnicode {r[6]}/{r[1]}')
    out[b] = rows
json.dump(out, open('math_fonts.json', 'w'), ensure_ascii=False)
