"""국어 원본에서 기호 글꼴(윤고딕·윤명조 등)의 PUA 코드가 실제로 어떤 모양인지 견본 (읽기 전용)"""
import json, collections, re
import pymupdf
from PIL import Image, ImageDraw, ImageFont
R = '/home/leejaeik/Projects/ksat-10000/raw/수능자료/'
rows = [json.loads(l) for l in open('census_ko.jsonl')]
HY = re.compile(r'^(Haansoft-?\s?Batang|Haansoft-Dotum|HaansoftBatang|\*옛한글|HCRBatang|T\d\d|\*신명-중명조|TT3678AC74tCID|NewGulim)$')
codes = {ord(k): v for k, v in json.load(open('ko_codes.json')).items()}
score = []
for r in rows:
    n = 0
    for f, d in r.get('fonts', {}).items():
        if HY.match(f) or f.startswith('Wingdings'): continue
        n += sum(v for k, v in d['codes'].items() if 0xE000 <= int(k, 16) <= 0xF8FF)
    if n: score.append((n, r['path']))
score.sort(reverse=True)
occ = {}; fonts_of = collections.defaultdict(set)
for n, p in score[:14]:
    doc = pymupdf.open(R + p)
    for pno in range(len(doc)):
        for sp in doc[pno].get_texttrace():
            f = sp['font']
            try: f = f.encode('latin-1').decode('cp949')
            except Exception: pass
            if HY.match(f): continue
            for ucs, gid, org, bbox in sp['chars']:
                if 0xE000 <= ucs <= 0xF8FF:
                    fonts_of[ucs].add(f[:10])
                    if ucs not in occ or (sp['size'] > occ[ucs][3] and sp['size'] < 20):
                        occ[ucs] = (p, pno, bbox, sp['size'], f)
sel = sorted(occ, key=lambda u: -codes.get(u, 0))[:50]
small = ImageFont.truetype('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', 13, index=1)
cols = 10; cw, chh = 150, 112
sheet = Image.new('RGB', (cols * cw, ((len(sel) + cols - 1) // cols) * chh), 'white'); d = ImageDraw.Draw(sheet)
cache = {}
for i, u in enumerate(sel):
    p, pno, bbox, size, f = occ[u]
    doc = cache.setdefault(p, pymupdf.open(R + p))
    r = pymupdf.Rect(bbox); m = r.height * 0.9
    clip = pymupdf.Rect(r.x0 - 2.2 * m, r.y0 - 0.25 * m, r.x1 + 2.2 * m, r.y1 + 0.25 * m)
    pix = doc[pno].get_pixmap(matrix=pymupdf.Matrix(4, 4), clip=clip)
    g = Image.frombytes('RGB', (pix.width, pix.height), pix.samples); g.thumbnail((146, 70))
    x0, y0 = (i % cols) * cw, (i // cols) * chh
    sheet.paste(g, (x0 + 2, y0 + 2))
    cx = x0 + 2 + g.width / 2; d.line([(cx, y0 + 72), (cx, y0 + 78)], fill='red', width=2)
    d.text((x0 + 3, y0 + 79), f'U+{u:04X} 산출물 {codes.get(u, 0)}회', font=small, fill='black')
    d.text((x0 + 3, y0 + 95), ','.join(sorted(fonts_of[u]))[:22], font=small, fill=(90, 90, 90))
    d.rectangle([x0, y0, x0 + cw - 1, y0 + chh - 1], outline=(210, 210, 210))
sheet.save('ko_sym_sheet.png'); print('기호 코드', len(occ), '종 중', len(sel), '개 견본', sheet.size)
