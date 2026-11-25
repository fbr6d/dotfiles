# -*- coding: utf-8 -*-
"""전수 모양 조사 결과 → 눈으로 볼 '칸' 목록.

- 칸 하나 = 글리프 모양 하나(같은 가족 안에서 거의 같은 모양은 한 칸으로 묶음).
- 수식 글꼴: 뽑힌 글자(코드)와 모양이 기계 비교로 맞으면 '후보 대조(B)' 칸, 아니면 '빈칸 읽기(A)' 칸.
- 그 밖 글꼴의 PUA: 한양 옛한글 표의 후보와 모양이 맞거나 옛한글 글꼴이면 '옛한글 대조(C)' 칸, 아니면 A 칸.
실행: venv/bin/python mk_cells.py <census.pkl> <cells.pkl>
"""
import sys, pickle, re, json, collections, itertools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fontTools.ttLib import TTFont, TTCollection
import glyphcore as gc

EM = gc.S
W = H = int(EM * 1.7); OX = int(EM * 0.25); BASE = int(EM * 1.2)
FAM = [('HyhwpEQ', r'^HyhwpEQ'), ('HancomEQN', r'^HancomEQN'), ('EH', r'^EH[A-Za-z]'), ('Kab', r'^Kab'), ('Amsusic', r'^Amsusic'), ('ASusic', r'^ASusic'), ('GS', r'^GS(Medium|MediIta|Symbol)'), ('TK', r'^TK(up|yak|down)')]
OLD = re.compile(r'^(Haansoft|\*옛한글|HCRBatang|T\d\d$|\*신명-중명조|TT3678AC74tCID|NewGulim)')
BAD = ('noembed', 'nolink', 'ambig', 'norender')
TH_SCORE, TH_GAP = 0.80, 0.03
HY = {int(k, 16): v for k, v in json.load(open('../hanyang_table_composed.json')).items()}


def fam_of(cn):
    for nm, pat in FAM:
        if re.search(pat, cn):
            return nm
    return 'PUA'


def canvas(shape):
    im = np.zeros((H, W), np.uint8)
    x, y, w, h, bits = shape
    if w == 0:
        return Image.fromarray(im)
    m = gc.shape_mask(shape)
    X, Y = OX + x, BASE + y
    x0, y0 = max(0, X), max(0, Y); x1, y1 = min(W, X + w), min(H, Y + h)
    if x1 > x0 and y1 > y0:
        im[y0:y1, x0:x1] = m[y0 - Y:y1 - Y, x0 - X:x1 - X] * 255
    return Image.fromarray(im)


def vec_em(im):
    v = np.asarray(im.filter(ImageFilter.GaussianBlur(1.5)), dtype=np.float32).ravel(); v = v - v.mean(); n = np.linalg.norm(v)
    return v / n if n > 0 else None


def vec_tight(im, N=32):
    a = np.asarray(im, dtype=np.float32); ys, xs = np.where(a > 60)
    if len(xs) == 0:
        return None, None
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; h, w = a.shape
    s = (N - 4) / max(h, w)
    t = Image.fromarray(a.astype(np.uint8)).resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    c = Image.new('L', (N, N), 0); c.paste(t, ((N - t.width) // 2, (N - t.height) // 2))
    v = np.asarray(c.filter(ImageFilter.GaussianBlur(1.0)), dtype=np.float32).ravel(); v = v - v.mean(); n = np.linalg.norm(v)
    geo = (w / EM, h / EM, (BASE - ys.max()) / EM)
    return (v / n if n > 0 else None), geo


# ---- 수식 후보 글자
cands = [chr(c) for c in range(0x21, 0x7F)]
cands += [chr(c) for c in range(0xA1, 0x100) if c != 0xAD]
cands += [chr(c) for c in range(0x391, 0x3CA) if c != 0x3A2] + list('ϑϕϖϵ')
cands += list('–—‖†‡•…‥′″‴‹›※⁄℃ℓℕℚℝℤℂÅ‘’“”')
cands += [chr(c) for c in range(0x2190, 0x21A0)] + list('⇒⇔⇐⇑⇓⇌')
cands += [chr(c) for c in range(0x2200, 0x2300)]
cands += list('⌈⌉⌊⌋⌒□■△▲▽▼◇◆○●◎★☆▷▶◁◀♠♣♥♦✓「」『』〈〉《》【】〔〕')
cands += [chr(c) for c in range(0x2460, 0x2474)] + [chr(c) for c in range(0x24D0, 0x24EA)] + [chr(c) for c in range(0x3260, 0x3270)]
cands += list('⁰⁴⁵⁶⁷⁸⁹ⁿ⁺⁻₀₁₂₃₄₅₆₇₈₉₊₋')
cands = list(dict.fromkeys(cands))
REF = [('/usr/share/fonts/gnu-free/FreeSerif.otf', 0, 'R'), ('/usr/share/fonts/gnu-free/FreeSerifItalic.otf', 0, 'I'), ('/usr/share/fonts/gnu-free/FreeSerifBold.otf', 0, 'B'),
       ('/usr/share/fonts/gnu-free/FreeSerifBoldItalic.otf', 0, 'BI'), ('/usr/share/fonts/gnu-free/FreeSans.otf', 0, 'S'), ('/usr/share/fonts/gnu-free/FreeSansOblique.otf', 0, 'SI'),
       ('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', 1, 'G'), ('/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc', 1, 'M')]
refs = []
import os
for path, idx, st in REF:
    if not os.path.exists(path):
        print('기준 글꼴 없음', path); continue
    cm = (TTCollection(path).fonts[idx] if path.endswith('.ttc') else TTFont(path)).getBestCmap()
    f = ImageFont.truetype(path, EM, index=idx)
    for ch in cands:
        if ord(ch) not in cm:
            continue
        if st in ('I', 'B', 'BI', 'S', 'SI') and not (ch.isalnum() or 0x391 <= ord(ch) <= 0x3D6):
            continue
        im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).text((OX, BASE), ch, font=f, fill=255, anchor='ls')
        ve = vec_em(im); vt, geo = vec_tight(im)
        if ve is None or vt is None:
            continue
        refs.append((ch, st, ve, vt, geo))
ME = np.stack([r[2] for r in refs]); MT = np.stack([r[3] for r in refs]); GEO = np.array([r[4] for r in refs], dtype=np.float32)
RCH = [r[0] for r in refs]
print('후보 글자', len(cands), '기준 그림', len(refs))


def mech(shape):
    im = canvas(shape)
    ve = vec_em(im); vt, geo = vec_tight(im)
    if ve is None or vt is None:
        return None
    geo = np.array(geo, dtype=np.float32)
    gs = np.exp(-(((GEO - geo) ** 2).sum(axis=1)) / 0.02)
    sc = 0.4 * (ME @ ve) + 0.45 * (MT @ vt) + 0.15 * gs
    best = {}
    for i in np.argsort(-sc):
        ch = RCH[i]
        if ch not in best:
            best[ch] = float(sc[i])
    return best


# ---- 옛한글 후보 그림 (Noto, raqm)
KF = [ImageFont.truetype('/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc', EM, index=1, layout_engine=ImageFont.Layout.RAQM),
      ImageFont.truetype('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', EM, index=1, layout_engine=ImageFont.Layout.RAQM)]


def hy_vecs(text):
    out = []
    for f in KF:
        im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).text((OX, BASE), text, font=f, fill=255, anchor='ls')
        vt, geo = vec_tight(im)
        if vt is not None:
            out.append(vt)
    return out


def main():
    D = pickle.load(open(sys.argv[1], 'rb'))
    cl = D['clusters']; shapes = D['shapes']
    # 1) 모양별로 모으기
    byh = collections.defaultdict(lambda: {'keys': collections.Counter(), 'npdf': 0, 'samples': []})
    noshape = collections.Counter()
    for (cn, ucs, h), (n, npdf, smp) in cl.items():
        if h in BAD:
            noshape[(fam_of(cn), cn, h)] += n
            continue
        b = byh[h]
        b['keys'][(cn, ucs)] += n
        b['npdf'] = max(b['npdf'], npdf)
        for s in smp:
            if len(b['samples']) < 16:
                b['samples'].append(s)
    # 2) 거의 같은 모양 묶기: 같은 (글꼴, 코드)를 함께 쓰는 모양끼리 점수 0.97 이상
    parent = {h: h for h in byh}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    bykey = collections.defaultdict(list)
    for h, b in byh.items():
        for k in b['keys']:
            bykey[k].append(h)
    nmerge = 0
    for k, hs in bykey.items():
        if len(hs) < 2:
            continue
        for a, b in itertools.combinations(hs, 2):
            ra, rb = find(a), find(b)
            if ra == rb:
                continue
            if gc.tol_score(shapes[a], shapes[b]) >= 0.97:
                parent[ra] = rb; nmerge += 1
    groups = collections.defaultdict(list)
    for h in byh:
        groups[find(h)].append(h)
    print('모양', len(byh), '→ 칸', len(groups), '(묶은 횟수', nmerge, ')')
    cells = []
    for root, hs in groups.items():
        hs.sort(key=lambda h: -sum(byh[h]['keys'].values()))
        keys = collections.Counter(); samples = []; npdf = 0
        for h in hs:
            keys.update(byh[h]['keys']); npdf = max(npdf, byh[h]['npdf'])
            for s in byh[h]['samples']:
                samples.append(s + (h,))
        famc = collections.Counter()
        for (cn, ucs), n in keys.items():
            famc[fam_of(cn)] += n
        fam = famc.most_common(1)[0][0]
        n = sum(keys.values())
        label = collections.Counter()
        for (cn, ucs), v in keys.items():
            label[ucs] += v
        cells.append({'id': hs[0], 'hashes': hs, 'fam': fam, 'keys': dict(keys), 'n': n, 'npdf': npdf, 'samples': samples, 'label': label.most_common(1)[0][0], 'labels': dict(label)})
    # 3) 기계 비교
    # 옛한글 후보 풀: 이번 전수에 나온 한양 코드 전부
    pool = sorted({ucs for c in cells if c['fam'] == 'PUA' for (cn, ucs) in c['keys'] if ucs in HY})
    PV = []; PU = []
    for u in pool:
        for v in hy_vecs(HY[u]):
            PV.append(v); PU.append(u)
    PV = np.stack(PV) if PV else np.zeros((0, 1024), np.float32)
    PU = np.array(PU)
    print('옛한글 후보', len(pool), '자, 기준 그림', len(PV))
    kind = collections.Counter()
    for c in cells:
        sh = shapes[c['id']]
        if sh[2] == 0:
            c['sheet'] = 'space'; kind[(c['fam'], 'space')] += 1
            continue
        if c['fam'] != 'PUA':
            best = mech(sh)
            c['top'] = list(best.items())[:5] if best else []
            lab = [u for u in c['labels'] if chr(u) in (best or {})]
            ok = False
            if best and lab:
                top = c['top'][0][1]
                u = max(lab, key=lambda u: c['labels'][u])
                ls = best[chr(u)]
                c['label_score'] = ls
                c['label_rank'] = 1 + sum(1 for ch, v in best.items() if v > ls)
                r = c['label_rank']
                ok = u == c['label'] and ls >= 0.60 and (r == 1 or (r <= 3 and ls >= top - 0.03))
            c['sheet'] = 'B' if ok else 'A'
        else:
            us = [u for (cn, u) in c['keys'] if u in HY]
            oldfont = any(OLD.search(cn) for (cn, u) in c['keys'])
            c['oldfont'] = oldfont
            if us:
                u = max(us, key=lambda u: sum(v for (cn, uu), v in c['keys'].items() if uu == u))
                im = canvas(sh); vt, geo = vec_tight(im)
                if vt is not None and len(PV):
                    sc = PV @ vt
                    per = collections.defaultdict(float)
                    for uu, s in zip(PU, sc):
                        if s > per[int(uu)]:
                            per[int(uu)] = float(s)
                    mine = per.get(u, 0.0)
                    rank = 1 + sum(1 for uu, s in per.items() if s > mine)
                    c['hy'] = {'ucs': u, 'text': HY[u], 'rank': rank, 'score': mine}
                    c['sheet'] = 'C' if (oldfont or rank <= 5) else 'A'
                else:
                    c['sheet'] = 'A'
            else:
                c['sheet'] = 'A'
        kind[(c['fam'], c['sheet'])] += 1
    for k, v in sorted(kind.items()):
        print('  ', k, v)
    # 범위: 수식 가족은 전부, PUA 칸은 먼저 볼 묶음(국어·수학·과학 목록)에 나온 것만
    first = None
    if len(sys.argv) > 3:
        first = set(pickle.load(open(sys.argv[3], 'rb'))['clusters'].keys())
    sc = collections.Counter()
    for c in cells:
        if c['fam'] != 'PUA' or first is None:
            c['inscope'] = True
        else:
            c['inscope'] = any((cn, u, h) in first for (cn, u) in c['keys'] for h in c['hashes'])
        sc[(c['fam'], c.get('sheet'), c['inscope'])] += 1
    print('범위:', {k: v for k, v in sorted(sc.items()) if k[0] == 'PUA'})
    pickle.dump({'paths': D['paths'], 'cells': cells, 'shapes': shapes, 'noshape': dict(noshape), 'fonts': D.get('fonts')}, open(sys.argv[2], 'wb'))
    print('모양 없음(글꼴 가족별 글자 수):', dict(collections.Counter({f: 0 for f in []})), sum(noshape.values()))
    nsf = collections.Counter()
    for (f, cn, h), n in noshape.items():
        nsf[(f, h)] += n
    print('   ', dict(nsf))


if __name__ == '__main__':
    main()
