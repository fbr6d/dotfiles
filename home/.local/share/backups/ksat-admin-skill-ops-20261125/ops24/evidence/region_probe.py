"""쪽의 한 구역: 글자(글꼴·크기·기준선·뽑힌 글자)와 가는 선을 나란히 찍고 그림으로 저장 (읽기 전용)"""
import sys, re
import pymupdf
path, pno = sys.argv[1], int(sys.argv[2]); x0, y0, x1, y1 = map(float, sys.argv[3:7]); tag = sys.argv[7]
doc = pymupdf.open(path); page = doc[pno]; clip = pymupdf.Rect(x0, y0, x1, y1)
rows = []
for sp in page.get_texttrace():
    for ucs, gid, org, bbox in sp['chars']:
        if clip.contains(pymupdf.Point(org)):
            rows.append((round(org[1], 1), round(org[0], 1), sp['font'][:18], round(sp['size'], 1), f'U+{ucs:04X}', chr(ucs) if ucs >= 32 else '?', gid, round(bbox[2] - bbox[0], 1)))
rows.sort()
print('기준선y  x     글꼴               크기  코드   글자 gid 폭')
for r in rows[:int(sys.argv[8]) if len(sys.argv) > 8 else 80]:
    print(f'{r[0]:6.1f} {r[1]:6.1f} {r[2]:18s} {r[3]:4.1f} {r[4]} {r[5]!r:5} {r[6]:4d} {r[7]}')
for d in page.get_drawings():
    r = d['rect']
    if clip.intersects(r) and (r.height < 1.5 or r.width < 1.5):
        print('선', [round(v, 1) for v in r], '굵기', d.get('width'), d['type'], [it[0] for it in d['items']][:4])
pix = page.get_pixmap(matrix=pymupdf.Matrix(5, 5), clip=clip); pix.save(f'region_{tag}.png'); print('그림', pix.width, pix.height)
