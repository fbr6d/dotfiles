from PIL import features, Image, ImageDraw, ImageFont
print('raqm', features.check('raqm'), 'freetype', features.version('freetype2'), 'harfbuzz', features.version('harfbuzz'), 'fribidi', features.version('fribidi'))
f = ImageFont.truetype('/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc', 96, index=1, layout_engine=ImageFont.Layout.RAQM if features.check('raqm') else ImageFont.Layout.BASIC)
print(f.getname())
for idx in range(6):
    try:
        ff = ImageFont.truetype('/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc', 40, index=idx)
        print(idx, ff.getname())
    except Exception as e:
        print(idx, 'X', e); break
s = '\u110b\u119e\u11af/\u1105\u119e\u11af \u1112\u119e\u1140\u119e\u11b8\u1102\u1175'
im = Image.new('L', (900, 160), 255)
d = ImageDraw.Draw(im)
d.text((10, 20), s, font=f, fill=0)
im.save('raqm_test.png')
print('len', f.getlength(s))
