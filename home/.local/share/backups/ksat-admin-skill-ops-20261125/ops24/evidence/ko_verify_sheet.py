"""검증에서 순위가 낮았던 코드를 눈으로 보기 위한 견본 그림 (PDF 글리프 | 표준 글꼴로 그린 변환 결과)"""
import json, re, sys, collections
import pymupdf
from PIL import Image, ImageDraw, ImageFont
TAB = {int(k, 16): v for k, v in json.load(open('hanyang_table_composed.json')).items()}
res = json.load(open('ko_verify.json'))
R = '/home/leejaeik/Projects/ksat-10000/raw/수능자료/EBS_수능특강·수능완성_2000-2026/본문/2026/국어/2026발행_2027학년도_수능특강_국어_언어와 매체_본문.pdf'
doc = pymupdf.open(R)
want = {}
for name, f, rows in res:
    if f == 'Haansoft-Batang':
        for code, rank, sc, top in rows:
            want[int(code, 16)] = (rank, sc, top)
occ = {}
for pno in range(len(doc)):
    for sp in doc[pno].get_texttrace():
        if 'Haansoft-Batang' not in sp['font']: continue
        for ucs, gid, org, bbox in sp['chars']:
            if ucs in want and ucs not in occ:
                occ[ucs] = (pno, bbox)
bad = sorted([u for u in want if want[u][0] and want[u][0] > 10], key=lambda u: -want[u][0])
good = sorted([u for u in want if want[u][0] and want[u][0] <= 1])[:10]
sel = bad[:30] + good
font = ImageFont.truetype('/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc', 64, index=1, layout_engine=ImageFont.Layout.RAQM)
small = ImageFont.truetype('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', 15, index=1)
cols = 8; cw, chh = 230, 130
rows_n = (len(sel) + cols - 1) // cols
sheet = Image.new('RGB', (cols * cw, rows_n * chh), 'white')
d = ImageDraw.Draw(sheet)
for i, u in enumerate(sel):
    x0, y0 = (i % cols) * cw, (i // cols) * chh
    pno, bbox = occ[u]
    r = pymupdf.Rect(bbox); r = pymupdf.Rect(r.x0 - 1, r.y0 - 1, r.x1 + 1, r.y1 + 1)
    pix = doc[pno].get_pixmap(matrix=pymupdf.Matrix(7, 7), clip=r, colorspace=pymupdf.csGRAY)
    g = Image.frombytes('L', (pix.width, pix.height), pix.samples)
    g.thumbnail((100, 95))
    sheet.paste(g, (x0 + 5, y0 + 5))
    d.text((x0 + 118, y0 + 5), TAB[u], font=font, fill='black')
    rank, sc, top = want[u]
    d.text((x0 + 5, y0 + 106), f'U+{u:04X} 순위{rank} 점수{sc} p{pno+1}', font=small, fill=(180, 0, 0) if rank > 10 else (0, 110, 0))
    d.rectangle([x0, y0, x0 + cw - 1, y0 + chh - 1], outline=(200, 200, 200))
sheet.save('ko_verify_sheet.png')
print('견본', len(sel), '개 (순위 낮은 것', len(bad[:30]), '+ 1등', len(good), ') 전체 순위 낮은 것', len(bad))
