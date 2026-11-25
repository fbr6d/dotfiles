# -*- coding: utf-8 -*-
"""전수 모양 조사: 수식 글꼴의 모든 글자와, 그 밖 글꼴의 PUA 글자를 (글꼴 이름, 뽑힌 코드, 모양)으로 센다.

쓰기: /usr/bin/python3 shape_census2.py <먼저 볼 목록.txt,...> <전체 목록.txt> <결과.pkl> <프로세스 수>
- 먼저 볼 목록이 다 끝나면 <결과>.part.pkl 을 한 번 써 둔다.
"""
import sys, os, re, time, pickle, collections
from multiprocessing import Pool
import pymupdf
import glyphcore as gc

pymupdf.TOOLS.mupdf_display_errors(False)
MATH = re.compile(r'^(HyhwpEQ|HancomEQN|EH[A-Za-z]|Kab|Amsusic|ASusic|GS(Medium|MediIta|Symbol)|TK(up|yak|down))')


def work(arg):
    idx, path = arg
    t0 = time.time()
    cl = {}
    shapes = {}
    fsum = {}
    stat = collections.Counter()
    err = None
    try:
        doc = pymupdf.open(path)
        if doc.needs_pass:
            raise RuntimeError('암호 필요')
        dg = gc.DocGlyphs(doc)
        for pno in range(doc.page_count):
            try:
                page = doc[pno]
                tr = page.get_texttrace()
            except Exception as e:
                stat['쪽 오류'] += 1
                continue
            n2x = None
            for sp in tr:
                fname = sp['font']
                chars = sp['chars']
                if not chars:
                    continue
                cname = gc.clean_name(fname)
                us = [c[0] for c in chars]
                fs = fsum.get(cname)
                if fs is None:
                    fs = fsum[cname] = [0, 0, 0, 0, 0]
                fs[0] += len(us)
                mx = max(us)
                math = MATH.search(cname) is not None
                if mx < 0x80 and not math:
                    if min(us) < 0x20:
                        fs[4] += sum(1 for u in us if u < 0x20 and u not in (9, 10, 13))
                    continue
                npua = 0
                for u in us:
                    if u >= 0xE000:
                        if u <= 0xF8FF:
                            npua += 1
                        elif u == 0xFFFD:
                            fs[2] += 1
                    elif u >= 0x80:
                        if u < 0xA0:
                            fs[4] += 1
                        elif u < 0x100:
                            fs[3] += 1
                    elif u < 0x20 and u not in (9, 10, 13):
                        fs[4] += 1
                fs[1] += npua
                if not math and not npua:
                    continue
                if n2x is None:
                    n2x = dg.page_map(page)
                xr = n2x.get(fname, ())
                d = sp['dir']
                upright = abs(d[0] - 1.0) < 1e-3 and abs(d[1]) < 1e-3
                size = round(sp['size'], 2)
                for (ucs, gid, org, bbox) in chars:
                    if not math and not (0xE000 <= ucs <= 0xF8FF):
                        continue
                    h = dg.span_hash(xr, gid)
                    key = (cname, ucs, h)
                    c = cl.get(key)
                    if c is None:
                        cl[key] = [1, (idx, pno, round(org[0], 1), round(org[1], 1), size, gid, xr[0] if xr else 0, upright)]
                    else:
                        c[0] += 1
                        if not c[1][7] and upright:
                            c[1] = (idx, pno, round(org[0], 1), round(org[1], 1), size, gid, xr[0] if xr else 0, upright)
        shapes = dg.shapes
        stat['쪽'] = doc.page_count
        stat['글꼴 객체'] = len(dg._font)
        doc.close()
    except Exception as e:
        err = '%s: %s' % (type(e).__name__, str(e)[:200])
    return idx, cl, shapes, fsum, dict(stat), err, round(time.time() - t0, 1)


def main():
    first_lists, all_list, out, nproc = sys.argv[1].split(','), sys.argv[2], sys.argv[3], int(sys.argv[4])
    first = []
    seen = set()
    for l in first_lists:
        for p in open(l).read().split('\n'):
            p = p.strip()
            if p and p not in seen:
                seen.add(p); first.append(p)
    rest = []
    for p in open(all_list).read().split('\n'):
        p = p.strip()
        if p and p not in seen:
            seen.add(p); rest.append(p)
    first.sort(key=lambda p: -os.path.getsize(p))
    rest.sort(key=lambda p: -os.path.getsize(p))
    paths = first + rest
    nfirst = len(first)
    print('PDF', len(paths), '(먼저', nfirst, ')', flush=True)
    clusters, shapes, fonts, stats, errs = {}, {}, {}, {}, {}
    t0 = time.time()
    done_first = 0
    part_written = False

    def dump(fn):
        pickle.dump({'paths': paths, 'nfirst': nfirst, 'clusters': clusters, 'shapes': shapes, 'fonts': fonts, 'stats': stats, 'errs': errs}, open(fn + '.tmp', 'wb'))
        os.replace(fn + '.tmp', fn)

    with Pool(nproc) as pool:
        for n, (idx, cl, sh, fsum, st, err, sec) in enumerate(pool.imap_unordered(work, list(enumerate(paths)), chunksize=1)):
            stats[idx] = (st, sec)
            if err:
                errs[idx] = err
            for k, (cnt, smp) in cl.items():
                c = clusters.get(k)
                if c is None:
                    clusters[k] = [cnt, 1, [smp]]
                else:
                    c[0] += cnt; c[1] += 1
                    if len(c[2]) < 12:
                        c[2].append(smp)
            for h, s in sh.items():
                if h not in shapes:
                    shapes[h] = s
            for nm, v in fsum.items():
                f = fonts.get(nm)
                if f is None:
                    fonts[nm] = v + [1]
                else:
                    for i in range(5):
                        f[i] += v[i]
                    f[5] += 1
            if idx < nfirst:
                done_first += 1
                if done_first == nfirst and not part_written:
                    dump(out + '.part.pkl'); part_written = True
                    print('먼저 볼 것 끝', round(time.time() - t0), 's', '묶음', len(clusters), '모양', len(shapes), flush=True)
            if (n + 1) % 500 == 0:
                print(n + 1, '권', round(time.time() - t0), 's', '묶음', len(clusters), '모양', len(shapes), '글꼴', len(fonts), '오류', len(errs), flush=True)
    dump(out)
    print('끝', len(paths), '권', round(time.time() - t0), 's', '묶음', len(clusters), '모양', len(shapes), '글꼴', len(fonts), '오류', len(errs), flush=True)


if __name__ == '__main__':
    main()
