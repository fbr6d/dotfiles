"""글리프 윤곽선 ↔ 표준 글꼴 글자 모양 비교 시험 (읽기 전용). 대응표 후보를 프로그램이 어디까지 낼 수 있는지 잰다."""
import collections, json, pickle, sys, unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont, TTCollection
EM = 64; W, H = int(EM * 1.7), int(EM * 1.7); OX, BASE = int(EM * 0.25), int(EM * 1.2)
class Flat(BasePen):
    def __init__(self):
        super().__init__(None); self.contours = []; self.cur = None
    def _moveTo(self, p): self.cur = [p]; self.contours.append(self.cur)
    def _lineTo(self, p): self.cur.append(p)
    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8; a = (1 - t) ** 3; b = 3 * t * (1 - t) ** 2; c = 3 * t * t * (1 - t); d = t ** 3
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, 7):
            t = i / 6; a = (1 - t) ** 2; b = 2 * t * (1 - t); c = t * t
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    def _closePath(self): pass
    def _endPath(self): pass
def raster(rec, upm):
    r = RecordingPen(); r.value = rec; pen = Flat(); r.replay(pen)
    S = 3; img = Image.new('1', (W * S, H * S), 0)
    for c in pen.contours:
        if len(c) < 3: continue
        pts = [((OX + x / upm * EM) * S, (BASE - y / upm * EM) * S) for x, y in c]
        m = Image.new('1', (W * S, H * S), 0); ImageDraw.Draw(m).polygon(pts, fill=1)
        img = ImageChops.logical_xor(img, m)
    return img.convert('L').resize((W, H), Image.LANCZOS)
def vec_em(im):
    v = np.asarray(im.filter(ImageFilter.GaussianBlur(2.0)), dtype=np.float32).ravel(); v = v - v.mean(); n = np.linalg.norm(v)
    return v / n if n > 0 else None
def vec_tight(im, N=32):
    a = np.asarray(im, dtype=np.float32); ys, xs = np.where(a > 60)
    if len(xs) == 0: return None, None
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; h, w = a.shape
    s = (N - 4) / max(h, w)
    t = Image.fromarray(a.astype(np.uint8)).resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    c = Image.new('L', (N, N), 0); c.paste(t, ((N - t.width) // 2, (N - t.height) // 2))
    v = np.asarray(c.filter(ImageFilter.GaussianBlur(1.0)), dtype=np.float32).ravel(); v = v - v.mean(); n = np.linalg.norm(v)
    geo = (w / EM, h / EM, (BASE - ys.max()) / EM)   # 폭, 높이, 아래끝(기준선 위)
    return (v / n if n > 0 else None), geo
# ---- 후보 글자
cands = [chr(c) for c in range(0x21, 0x7F)]
cands += list('×÷±·°¬µ«»´¨¯§¶¹²³¼½¾')
cands += [chr(c) for c in range(0x391, 0x3CA) if c != 0x3A2] + list('ϑϕϖϵ')
cands += list('–—‖†‡•…‥′″‴‹›※⁄℃ℓℕℚℝℤℂÅ')
cands += [chr(c) for c in range(0x2190, 0x21A0)] + list('⇒⇔⇐⇑⇓')
cands += [chr(c) for c in range(0x2200, 0x2300)]
cands += list('⌈⌉⌊⌋⌒□■△▲▽▼◇◆○●◎★☆▷▶◁◀♠♣♥♦✓「」『』〈〉《》【】〔〕')
cands += [chr(c) for c in range(0x2460, 0x2474)] + [chr(c) for c in range(0x24D0, 0x24EA)] + [chr(c) for c in range(0x3260, 0x3270)]
cands += list('⁰⁴⁵⁶⁷⁸⁹ⁿ⁺⁻₀₁₂₃₄₅₆₇₈₉₊₋')
cands = list(dict.fromkeys(cands))
REF = [('/usr/share/fonts/gnu-free/FreeSerif.otf', 0, 'R'), ('/usr/share/fonts/gnu-free/FreeSerifItalic.otf', 0, 'I'), ('/usr/share/fonts/gnu-free/FreeSerifBold.otf', 0, 'B'),
       ('/usr/share/fonts/gnu-free/FreeSerifBoldItalic.otf', 0, 'BI'), ('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', 1, 'G'), ('/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc', 1, 'M')]
refs = []   # (char, style, vec_em, vec_tight, geo)
for path, idx, st in REF:
    cm = (TTCollection(path).fonts[idx] if path.endswith('.ttc') else TTFont(path)).getBestCmap()
    f = ImageFont.truetype(path, EM, index=idx)
    for ch in cands:
        if ord(ch) not in cm: continue
        if st in ('I', 'B', 'BI') and not (ch.isalnum() or 0x391 <= ord(ch) <= 0x3D6): continue
        im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).text((OX, BASE), ch, font=f, fill=255, anchor='ls')
        ve = vec_em(im); vt, geo = vec_tight(im)
        if ve is None or vt is None: continue
        refs.append((ch, st, ve, vt, geo))
ME = np.stack([r[2] for r in refs]); MT = np.stack([r[3] for r in refs]); GEO = np.array([r[4] for r in refs], dtype=np.float32)
print('후보 글자', len(cands), '기준 그림', len(refs))
G = pickle.load(open(sys.argv[1], 'rb'))
res = {}
for k, g in G.items():
    if not k[1].startswith('h:') or not g['rec']: continue
    im = raster(g['rec'], g['upm'] or 1000)
    ve = vec_em(im); vt, geo = vec_tight(im)
    if ve is None or vt is None: continue
    geo = np.array(geo, dtype=np.float32)
    gs = np.exp(-(((GEO - geo) ** 2).sum(axis=1)) / 0.02)       # 크기·높이 닮음
    sc = 0.4 * (ME @ ve) + 0.45 * (MT @ vt) + 0.15 * gs
    best = {}
    for i in np.argsort(-sc)[:40]:
        ch = refs[i][0]
        if ch not in best: best[ch] = float(sc[i])
        if len(best) >= 5: break
    u = g['ucs'].most_common(1)[0][0]
    res[k] = {'ucs': u, 'n': g['n'], 'top': list(best.items()), 'im': im}
pickle.dump(res, open(sys.argv[2], 'wb'))
def catg(u):
    if 0xE000 <= u <= 0xF8FF: return 'PUA'
    if u == 0xFFFD: return 'U+FFFD'
    if 0x80 <= u <= 0xFF: return '라틴-1 보충'
    if u < 0x20: return '제어문자'
    if u < 0x80 and chr(u).isalnum(): return 'ASCII 영문·숫자'
    if u < 0x80: return 'ASCII 기호'
    return '그 밖 유니코드'
st = collections.defaultdict(lambda: collections.Counter())
for k, r in res.items():
    c = catg(r['ucs']); s = st[c]; ch = chr(r['ucs']); tops = [t[0] for t in r['top']]
    s['종'] += 1; s['자'] += r['n']
    fold = lambda x: unicodedata.normalize('NFKC', x).casefold()
    if tops and tops[0] == ch: s['1등=뽑힌 글자'] += 1
    if ch in tops[:3]: s['3등 안'] += 1
    if any(fold(t) == fold(ch) for t in tops[:3]): s['3등 안(대소문자·호환 글자 묶음)'] += 1
    if r['top'] and r['top'][0][1] >= 0.80: s['1등 점수 0.80↑'] += 1
for c, s in st.items(): print(c, dict(s))
