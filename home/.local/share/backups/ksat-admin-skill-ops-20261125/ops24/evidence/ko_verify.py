"""옛한글 PUA 대응 기계 검증 시험 (읽기 전용).
PDF 속 글리프 그림과, 한양 표로 바꾼 첫가끝을 표준 글꼴로 그린 그림을 비교한다.
표가 맞는 글꼴이면 '표가 가리키는 글자'가 수백 개 후보 가운데 1등 근처에 와야 한다."""
import collections, json, random, re, sys
import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
TAB = {int(k, 16): v for k, v in json.load(open('hanyang_table_composed.json')).items()}
N = 40
def norm(im):
    """잉크 영역만 잘라 N×N 칸에 비율 유지로 넣고 살짝 흐림"""
    a = 255 - np.asarray(im.convert('L'), dtype=np.float32)
    ys, xs = np.where(a > 80)
    if len(xs) == 0:
        return None
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = a.shape
    s = (N - 4) / max(h, w)
    im2 = Image.fromarray(a.astype(np.uint8)).resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    canvas = Image.new('L', (N, N), 0)
    canvas.paste(im2, ((N - im2.width) // 2, (N - im2.height) // 2))
    canvas = canvas.filter(ImageFilter.GaussianBlur(1.2))
    v = np.asarray(canvas, dtype=np.float32).ravel()
    v -= v.mean()
    n = np.linalg.norm(v)
    return v / n if n else None
FONTS = [ImageFont.truetype('/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc', 96, index=1, layout_engine=ImageFont.Layout.RAQM),
         ImageFont.truetype('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', 96, index=1, layout_engine=ImageFont.Layout.RAQM)]
def ref(s):
    out = []
    for f in FONTS:
        im = Image.new('L', (400, 220), 255)
        ImageDraw.Draw(im).text((60, 40), s, font=f, fill=0)
        v = norm(im)
        if v is not None:
            out.append(v)
    return out
def scan(path):
    doc = pymupdf.open(path)
    occ = collections.defaultdict(list)
    for pno in range(len(doc)):
        for sp in doc[pno].get_texttrace():
            f = re.sub(r'^[A-Z]{6}\+', '', sp['font'])
            try:
                f = f.encode('latin-1').decode('cp949')
            except Exception:
                pass
            for ucs, gid, org, bbox in sp['chars']:
                if 0xE000 <= ucs <= 0xF8FF and len(occ[(f, ucs)]) < 3:
                    occ[(f, ucs)].append((pno, bbox))
    return doc, occ
def glyph(doc, pno, bbox):
    r = pymupdf.Rect(bbox)
    r = pymupdf.Rect(r.x0 - 0.3, r.y0 - 0.5, r.x1 + 0.3, r.y1 + 0.5)
    pix = doc[pno].get_pixmap(matrix=pymupdf.Matrix(10, 10), clip=r, colorspace=pymupdf.csGRAY, alpha=False)
    return Image.frombytes('L', (pix.width, pix.height), pix.samples)
random.seed(20261125)
res = []
for path in sys.argv[1:]:
    doc, occ = scan(path)
    seen_codes = sorted({u for (_, u) in occ if u in TAB})
    pool = sorted(set(seen_codes) | set(random.sample(sorted(TAB), 600)))
    # 비슷한 글자(같은 첫·가운뎃소리, 다른 끝소리)도 후보에 넣기
    refs = {u: ref(TAB[u]) for u in pool}
    refs = {u: v for u, v in refs.items() if v}
    M = np.stack([v for u in refs for v in refs[u]]); owner = [u for u in refs for _ in refs[u]]
    print(f'== {path.split("/")[-1][:60]}: PUA (글꼴, 코드) 쌍 {len(occ)}개, 후보 {len(refs)}자')
    by_font = collections.defaultdict(list)
    for (f, u), lst in sorted(occ.items()):
        if u not in TAB:
            by_font[f].append((u, None, None, None)); continue
        best = None
        for pno, bbox in lst:
            v = norm(glyph(doc, pno, bbox))
            if v is None: continue
            sims = M @ v
            score = collections.defaultdict(float)
            for o, s in zip(owner, sims):
                score[o] = max(score[o], float(s))
            order = sorted(score, key=lambda k: -score[k])
            rank = order.index(u) + 1
            cand = (rank, score[u], order[0], score[order[0]])
            if best is None or cand[0] < best[0]:
                best = cand
        by_font[f].append((u,) + (best if best else (None, None, None, None)))
    for f, rows in by_font.items():
        ok = [r for r in rows if r[1] is not None]
        if not ok:
            print(f'  {f}: 표에 있는 코드 0 / {len(rows)}'); continue
        ranks = np.array([r[1] for r in ok]); sc = np.array([r[2] for r in ok])
        print(f'  {f}: 코드 {len(rows)}종 → 1등 {int((ranks == 1).sum())}, 3등 안 {int((ranks <= 3).sum())}, 10등 안 {int((ranks <= 10).sum())}, 순위 중앙값 {int(np.median(ranks))}, 닮음 점수 중앙값 {np.median(sc):.2f}')
        res.append((path.split('/')[-1], f, [(hex(r[0]), r[1], None if r[2] is None else round(r[2], 3), None if r[3] is None else hex(r[3])) for r in rows]))
json.dump(res, open('ko_verify.json', 'w'), ensure_ascii=False)
