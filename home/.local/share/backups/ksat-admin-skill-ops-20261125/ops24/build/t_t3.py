# Type3 글꼴 글리프를 임시 쪽으로 그린 것이 실제 쪽 그림과 같은지 확인
import sys, re, collections
import numpy as np
import pymupdf
import glyphcore as gc


def check(path, pnos, rx):
    doc = pymupdf.open(path)
    dg = gc.DocGlyphs(doc)
    res = collections.Counter(); scores = []; kinds = set()
    for pno in pnos:
        page = doc[pno]
        n2x = dg.page_map(page)
        by_size = collections.defaultdict(list)
        for sp in page.get_texttrace():
            cn = gc.clean_name(sp['font'])
            if not rx.search(cn):
                continue
            xr = n2x.get(sp['font'], [])
            for (ucs, gid, org, bbox) in sp['chars']:
                h = dg.span_hash(xr, gid)
                if h in ('nolink', 'noembed', 'ambig', 'norender'):
                    res[h] += 1; continue
                kinds.add((cn, ucs, h))
                by_size[round(sp['size'], 3)].append((org, h))
        for size, lst in by_size.items():
            z = gc.S / size
            if z > 14:
                res['너무 작은 글자'] += len(lst); continue
            pm = page.get_pixmap(matrix=pymupdf.Matrix(z, z), colorspace=pymupdf.csGRAY, alpha=False)
            ink = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.stride)[:, :pm.width] < (255 - gc.THR)
            for org, h in lst:
                sh = dg.shapes[h]; x, y, w, hh, _ = sh
                if w == 0:
                    res['빈 글리프'] += 1; continue
                m = gc.shape_mask(sh); best = 0.0
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        X = int(round((org[0] - page.rect.x0) * z)) + x + dx; Y = int(round((org[1] - page.rect.y0) * z)) + y + dy
                        if X < 0 or Y < 0 or X + w > ink.shape[1] or Y + hh > ink.shape[0]:
                            continue
                        crop = ink[Y:Y + hh, X:X + w]
                        if crop.sum():
                            best = max(best, min((m & gc._dil(crop)).sum() / max(1, m.sum()), (crop & gc._dil(m)).sum() / max(1, crop.sum())))
                scores.append(best); res['비교'] += 1
    s = np.array(scores) if scores else np.zeros(1)
    print(path.split('/')[-1][:48], dict(res), '모양', len(kinds), '| 점수 중앙값 %.3f, 0.9 이상 %.1f%%' % (np.median(s), 100 * (s >= 0.9).mean()))


R = '/home/leejaeik/Projects/ksat-10000/raw/수능자료/'
ko = [l for l in open('../list_ko.txt').read().split('\n') if '2003-11_2004학년도_대학수학능력시험_한국교육과정평가원_국어_홀수형_문제' in l][0]
check(ko, [9, 10], re.compile(r'^T\d\d$'))
check(R + '교과서/공통수학1-YBM.pdf', [4, 33, 142], re.compile(r'^Type3'))
check(R + '교과서/공통수학2-YBM.pdf', [5, 119], re.compile(r'^Type3'))
