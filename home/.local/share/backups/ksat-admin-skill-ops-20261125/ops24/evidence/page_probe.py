"""한 쪽의 수식 글꼴 글자·선(그림 요소)을 좌표와 함께 보기 (읽기 전용)"""
import sys, re, collections
import pymupdf
path, pno = sys.argv[1], int(sys.argv[2])
PAT = re.compile(sys.argv[3]) if len(sys.argv) > 3 else re.compile('.')
doc = pymupdf.open(path); page = doc[pno]
print('쪽 크기', page.rect, '회전', page.rotation)
dr = page.get_drawings()
kinds = collections.Counter()
hl = []
for d in dr:
    r = d['rect']
    w, h = r.width, r.height
    if w > 3 and h < 1.5:
        kinds['가로 가는 선·상자'] += 1; hl.append((round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1), d.get('width'), d['type']))
    elif h > 3 and w < 1.5:
        kinds['세로 가는 선'] += 1
    else:
        kinds['그 밖'] += 1
print('그림 요소', len(dr), dict(kinds))
print('가로 선 예(짧은 것부터):', sorted(hl, key=lambda t: t[2] - t[0])[:25])
n = 0
fonts = collections.Counter()
for sp in page.get_texttrace():
    fonts[sp['font']] += len(sp['chars'])
print('글꼴별 글자 수:', dict(fonts.most_common(14)))
pix = page.get_pixmap(matrix=pymupdf.Matrix(1.6, 1.6)); pix.save(f'probe_p{pno+1}.png'); print('그림', pix.width, pix.height)
