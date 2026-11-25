# 따로 그린 글리프가 실제 쪽 그림과 같은지 확인 (글꼴 객체 잇기·gid 검증)
import sys, collections, re
import numpy as np
import pymupdf
import glyphcore as gc

MATH = re.compile(r'^(HyhwpEQ|HancomEQN|EH|Kab|Amsusic|ASusic|GS|TK)')


def check(path, pnos, only_math=True):
    doc = pymupdf.open(path)
    dg = gc.DocGlyphs(doc)
    res = collections.Counter()
    scores = []
    bad = []
    for pno in pnos:
        if pno >= doc.page_count:
            continue
        page = doc[pno]
        n2x = dg.page_map(page)
        tr = page.get_texttrace()
        by_size = collections.defaultdict(list)
        for sp in tr:
            cn = gc.clean_name(sp['font'])
            if only_math and not MATH.search(cn):
                continue
            if tuple(round(v, 3) for v in sp['dir']) != (1.0, 0.0):
                res['회전'] += len(sp['chars'])
                continue
            xr = n2x.get(sp['font'], [])
            for (ucs, gid, org, bbox) in sp['chars']:
                h = dg.span_hash(xr, gid)
                if h in ('nolink', 'noembed', 'ambig', 'norender'):
                    res[h] += 1
                    continue
                by_size[round(sp['size'], 3)].append((cn, ucs, gid, org, h))
        for size, lst in by_size.items():
            z = gc.S / size
            pm = page.get_pixmap(matrix=pymupdf.Matrix(z, z), colorspace=pymupdf.csGRAY, alpha=False)
            img = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.stride)[:, :pm.width]
            ink = img < (255 - gc.THR)
            ox, oy = page.rect.x0, page.rect.y0
            for (cn, ucs, gid, org, h) in lst:
                sh = dg.shapes[h]
                x, y, w, hh, bits = sh
                if w == 0:
                    res['빈 글리프'] += 1
                    continue
                best = 0.0
                px0 = (org[0] - ox) * z
                py0 = (org[1] - oy) * z
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        X = int(round(px0)) + x + dx
                        Y = int(round(py0)) + y + dy
                        if X < 1 or Y < 1 or X + w + 1 > ink.shape[1] or Y + hh + 1 > ink.shape[0]:
                            continue
                        crop = ink[Y:Y + hh, X:X + w]
                        m = gc.shape_mask(sh)
                        # 글리프 잉크가 쪽 그림에 얼마나 들어 있는가 + 그 칸의 쪽 잉크가 글리프와 얼마나 맞는가
                        a = (m & gc._dil(crop)).sum() / max(1, m.sum())
                        b = (crop & gc._dil(m)).sum() / max(1, crop.sum())
                        best = max(best, min(a, b) if crop.sum() else 0.0)
                scores.append(best)
                res['비교'] += 1
                if best < 0.8:
                    bad.append((pno, cn, hex(ucs), gid, round(best, 2)))
    s = np.array(scores) if scores else np.zeros(1)
    print(path.split('/')[-1][:50], dict(res), '| 점수 중앙값 %.3f, 0.9 이상 %.1f%%, 0.8 미만 %d' % (np.median(s), 100 * (s >= 0.9).mean(), (s < 0.8).sum()))
    cnt = collections.Counter((b[1], b[2]) for b in bad)
    print('   낮은 것:', cnt.most_common(8))


if __name__ == '__main__':
    R = '/home/leejaeik/Projects/ksat-10000/raw/수능자료/'
    eq = open('../list_eq.txt').read().split('\n')
    check(eq[0], [0, 1, 2])
    check(eq[-2] if eq[-1] == '' else eq[-1], [0, 1, 2])
    for nm, pn in [('교과서/대수-천재.pdf', [13, 14, 40]), ('교과서/미적분Ⅰ-천재.pdf', [20, 21, 60]), ('교과서/공통수학1-미래엔.pdf', [20, 21, 60]), ('교과서/확률과통계-천재.pdf', [30, 31])]:
        check(R + nm, pn)
