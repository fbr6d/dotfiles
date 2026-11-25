import sys, os
from PIL import Image
for p in sys.argv[1:]:
    im = Image.open(p).convert('RGB')
    for n in (8, 12, 16):
        q = im.quantize(colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        out = p.replace('.png', '.q%d.png' % n)
        q.save(out, optimize=True)
        print(os.path.basename(p), im.size, os.path.getsize(p), '→', n, '색', os.path.getsize(out))
