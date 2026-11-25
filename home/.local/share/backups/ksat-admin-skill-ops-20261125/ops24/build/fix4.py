p = 'mk_sheets.py'
s = open(p).read()
old = """    (w, h, samples), (tx, ty) = c
    im = Image.frombytes('RGB', (w, h), samples)
"""
new = """    (w, h, samples), (tx, ty) = c
    im = Image.frombytes('RGB', (w, h), samples).convert('L').convert('RGB')   # 문맥은 회색으로(그림 용량 줄이기)
"""
assert old in s; s = s.replace(old, new)
old = "            sheet.save(os.path.join(out, name + '.png'), optimize=True)\n"
new = """            # 보는 도구가 그림 한 장을 256KB(base64) 안으로 줄여 버리므로, 색 수를 줄여 원래 크기로 전달되게 한다
            fn = os.path.join(out, name + '.png')
            for ncol in (24, 16, 12, 8):
                sheet.quantize(colors=ncol, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(fn, optimize=True)
                if os.path.getsize(fn) <= 180_000:
                    break
"""
assert old in s; s = s.replace(old, new)
old = "            manifest.append({'sheet': name, 'group': g, 'type': t, 'cells': len(chunk), 'size': [Wd, Hd]})\n"
new = "            manifest.append({'sheet': name, 'group': g, 'type': t, 'cells': len(chunk), 'size': [Wd, Hd], 'bytes': os.path.getsize(fn)})\n"
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
