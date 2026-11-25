# 견본 칸의 글리프를 크게 그려 확대해 본다(눈 확인용).
# 쓰기: /usr/bin/python3 t_big.py <cells.pkl> <ops 폴더> <견본 이름> <칸 번호,칸 번호,…> <결과.png> [px=230]
import sys, os, json, pickle
import pymupdf, numpy as np
from PIL import Image, ImageDraw, ImageFont
import glyphcore as gc
pymupdf.TOOLS.mupdf_display_errors(False)
D = pickle.load(open(sys.argv[1], 'rb'))
ops, name, nos, out = sys.argv[2], sys.argv[3], sys.argv[4].split(','), sys.argv[5]
px = int(sys.argv[6]) if len(sys.argv) > 6 else 230
cells = {c['id']: c for c in D['cells']}
cj = json.load(open(os.path.join(ops, 'sheets', name + '.cells.json')))
F = ImageFont.truetype('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', 15, index=1)
tiles = []
for no in nos:
    ci = cj[no]; c = cells[ci['cell']]
    got = None
    for s in c['samples'][:6]:
        doc = pymupdf.open(D['paths'][s[0]]); page = doc[s[1]]
        dg = gc.DocGlyphs(doc); n2x = dg.page_map(page)
        for sp in page.get_texttrace():
            for (ucs, gid, org, bbox) in sp['chars']:
                if gid == s[5] and abs(org[0] - s[2]) < 0.3 and abs(org[1] - s[3]) < 0.3:
                    g = dg.gray_any(list(n2x.get(sp['font'], ())), gid, px)
                    if g is not None and g[2].size:
                        got = (g, ucs, gc.clean_name(sp['font']), sp['size'], page, org)
                    break
            if got:
                break
        if got:
            break
    cand = ci.get('cand') or ''
    lab = '%s#%s  후보 %s  [%s]' % (name, no, cand, ' '.join('%04X' % ord(ch) for ch in cand))
    if not got:
        tiles.append((None, lab + '  (그림 없음)', None)); continue
    (x0, y0, a), ucs, cn, size, page, org = got
    gi = Image.fromarray((255 - a).astype(np.uint8)).convert('RGB')
    z = max(1.0, min(12.0, 40 / (size or 10)))
    clip = pymupdf.Rect(org[0] - 4 * size, org[1] - 1.5 * size, org[0] + 5 * size, org[1] + 0.7 * size) & page.rect
    pm = page.get_pixmap(matrix=pymupdf.Matrix(z, z), clip=clip, colorspace=pymupdf.csRGB, alpha=False)
    ctx = Image.frombytes('RGB', (pm.width, pm.height), pm.samples)
    dd = ImageDraw.Draw(ctx); tx = (org[0] + 0.5 * size - clip.x0) * z
    dd.polygon([(tx - 6, 0), (tx + 6, 0), (tx, 9)], fill=(230, 0, 0))
    tiles.append((gi, lab + '  U+%04X %s' % (ucs, cn[:16]), ctx))
cw, chh, cols = 490, px + 150, 3
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new('RGB', (cw * cols, chh * rows), (255, 255, 255))
d = ImageDraw.Draw(sheet)
for i, (gi, lab, ctx) in enumerate(tiles):
    x0, y0 = (i % cols) * cw, (i // cols) * chh
    d.text((x0 + 4, y0 + 2), lab[:60], font=F, fill=(0, 0, 160))
    if gi is not None:
        gi = gi.crop((0, 0, min(gi.width, cw - 8), min(gi.height, px + 30)))
        sheet.paste(gi, (x0 + 6, y0 + 24))
        ctx = ctx.crop((0, 0, min(ctx.width, cw - 8), min(ctx.height, 86)))
        sheet.paste(ctx, (x0 + 4, y0 + chh - 90))
    d.rectangle([x0, y0, x0 + cw - 1, y0 + chh - 1], outline=(190, 190, 190))
sheet.quantize(colors=16, dither=Image.Dither.NONE).save(out, optimize=True)
print(out, os.path.getsize(out), sheet.size)
