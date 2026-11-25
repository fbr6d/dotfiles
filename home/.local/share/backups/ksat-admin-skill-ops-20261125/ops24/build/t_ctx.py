# (글꼴, 코드)가 실제 쪽에서 어떻게 찍혔는지 문맥 그림을 모은다(눈 확인용).
# 쓰기: /usr/bin/python3 t_ctx.py <PDF 목록> <글꼴 이름 정규식> <코드 16진> <결과.png> [최대 칸=12] [경로 거르는 말]
import sys, re, os
import pymupdf, numpy as np
from PIL import Image, ImageDraw, ImageFont
import glyphcore as gc
pymupdf.TOOLS.mupdf_display_errors(False)
lst, rx, code, out = sys.argv[1], re.compile(sys.argv[2]), int(sys.argv[3], 16), sys.argv[4]
mx = int(sys.argv[5]) if len(sys.argv) > 5 else 12
flt = sys.argv[6] if len(sys.argv) > 6 else ''
paths = [p.strip() for p in open(lst) if p.strip() and flt in p]
F = ImageFont.truetype('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', 13, index=1)
tiles = []
npdf = 0
for p in paths:
    if len(tiles) >= mx or npdf >= 400:
        break
    try:
        doc = pymupdf.open(p)
    except Exception:
        continue
    npdf += 1
    got = 0
    for pno in range(doc.page_count):
        if got >= 2 or len(tiles) >= mx:
            break
        page = doc[pno]
        for sp in page.get_texttrace():
            cn = gc.clean_name(sp['font'])
            if not rx.search(cn):
                continue
            for (ucs, gid, org, bbox) in sp['chars']:
                if ucs != code:
                    continue
                size = sp['size'] or 10
                z = max(1.0, min(10.0, 26 / size))
                clip = pymupdf.Rect(org[0] - 7 * size, org[1] - 1.7 * size, org[0] + 8 * size, org[1] + 0.9 * size) & page.rect
                if clip.is_empty:
                    continue
                pm = page.get_pixmap(matrix=pymupdf.Matrix(z, z), clip=clip, colorspace=pymupdf.csRGB, alpha=False)
                im = Image.frombytes('RGB', (pm.width, pm.height), pm.samples)
                d = ImageDraw.Draw(im)
                tx = (org[0] + 0.25 * size - clip.x0) * z
                for yy, dy in ((0, 1), (im.height - 1, -1)):
                    d.polygon([(tx - 5, yy), (tx + 5, yy), (tx, yy + dy * 8)], fill=(230, 0, 0))
                tiles.append((im, '%s p%d %s gid%d' % (os.path.basename(p)[:34], pno + 1, cn[:18], gid)))
                got += 1
                break
            if got >= 2 or len(tiles) >= mx:
                break
print('본 PDF', npdf, '· 모은 문맥', len(tiles))
if tiles:
    cw, chh, cols = 480, 100, 3
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cw * cols, chh * rows), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for i, (im, lab) in enumerate(tiles):
        x0, y0 = (i % cols) * cw, (i // cols) * chh
        im = im.crop((0, 0, min(im.width, cw - 6), min(im.height, chh - 22)))
        sheet.paste(im, (x0 + 3, y0 + 18))
        d.text((x0 + 3, y0 + 1), '%d. %s' % (i + 1, lab), font=F, fill=(0, 0, 160))
        d.rectangle([x0, y0, x0 + cw - 1, y0 + chh - 1], outline=(190, 190, 190))
    sheet.quantize(colors=24, dither=Image.Dither.NONE).save(out, optimize=True)
    print(out, os.path.getsize(out))
