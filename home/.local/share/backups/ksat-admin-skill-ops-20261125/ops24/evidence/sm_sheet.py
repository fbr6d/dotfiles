"""모양 비교 결과 견본 그림: 글리프 | 뽑힌 글자 → 모양 1·2등"""
import pickle, sys, random
from PIL import Image, ImageDraw, ImageFont, ImageOps
res = pickle.load(open(sys.argv[1], 'rb')); mode = sys.argv[2]; outp = sys.argv[3]; lim = int(sys.argv[4])
def catg(u):
    if u == 0xFFFD: return 'fffd'
    if 0x80 <= u <= 0xFF: return 'l1'
    if u < 0x80 and chr(u).isalnum(): return 'alnum'
    if u < 0x80: return 'sym'
    return 'etc'
items = []
for k, r in res.items():
    ch = chr(r['ucs']); tops = [t[0] for t in r['top']]
    c = catg(r['ucs'])
    if mode == 'alnum_bad' and c == 'alnum' and ch not in tops[:3]: items.append((k, r))
    if mode == 'sym' and c == 'sym': items.append((k, r))
    if mode == 'l1' and c in ('l1', 'etc', 'fffd'): items.append((k, r))
items.sort(key=lambda kr: -kr[1]['n'])
print(mode, '대상', len(items), '글자 수', sum(r['n'] for _, r in items))
items = items[:lim]
f1 = ImageFont.truetype('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', 13, index=1)
f2 = ImageFont.truetype('/usr/share/fonts/gnu-free/FreeSerif.otf', 22)
cols = 10; cw, chh = 150, 118
sheet = Image.new('RGB', (cols * cw, ((len(items) + cols - 1) // cols) * chh), 'white'); d = ImageDraw.Draw(sheet)
for i, (k, r) in enumerate(items):
    x0, y0 = (i % cols) * cw, (i // cols) * chh
    g = ImageOps.invert(r['im']).resize((76, 76))
    sheet.paste(g, (x0 + 2, y0 + 2))
    d.line([(x0 + 2, y0 + 2 + 76 * 1.2 / 1.7), (x0 + 78, y0 + 2 + 76 * 1.2 / 1.7)], fill=(170, 200, 255))
    ch = chr(r['ucs'])
    d.text((x0 + 84, y0 + 4), ch if ch.isprintable() else '?', font=f2, fill=(0, 0, 160))
    d.text((x0 + 84, y0 + 34), '→' + ''.join(t[0] for t in r['top'][:3]), font=f2, fill=(160, 0, 0))
    d.text((x0 + 3, y0 + 82), f'{k[0][:16]}', font=f1, fill='black')
    d.text((x0 + 3, y0 + 98), f'U+{r["ucs"]:04X} {r["n"]}자 {r["top"][0][1]:.2f}', font=f1, fill='black')
    d.rectangle([x0, y0, x0 + cw - 1, y0 + chh - 1], outline=(210, 210, 210))
sheet.save(outp); print(outp, sheet.size)
