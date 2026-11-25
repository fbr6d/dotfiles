# -*- coding: utf-8 -*-
"""전수 검증: 대응표와 도구로 PDF 묶음 전체를 돌려, 수식 글꼴 글자와 PUA 글자가 어떤 상태로 나오는지 센다.

쓰기: /usr/bin/python3 verify_corpus.py <목록.txt[,목록…]> <결과.json> <프로세스 수> <tools 폴더>
"""
import sys, os, re, json, time, collections
from multiprocessing import Pool

TOOLS = sys.argv[4] if len(sys.argv) > 4 else None
if TOOLS:
    sys.path.insert(0, TOOLS)
import pymupdf                      # noqa: E402
import pdf_glyph_text as pgt        # noqa: E402
import glyphcore as gc              # noqa: E402

OLD = re.compile(r'^(Haansoft|\*옛한글|HCRBatang|T\d\d$|\*신명-중명조|TT3678AC74tCID|NewGulim)')
_conv = None
_tab = None


def init():
    global _conv, _tab
    tb = pgt.Tables(os.path.join(TOOLS, 'glyph'))
    _conv = pgt.Converter(tb)
    _tab = {}
    for nm, rx, t in tb.math + tb.pua:
        for e in t['entries']:
            _tab[e['id']] = nm


def work(path):
    cnt = collections.Counter(); unk = collections.Counter(); fixed = collections.Counter(); puatab = collections.Counter()
    err = None
    try:
        doc = pymupdf.open(path)
        dg = gc.DocGlyphs(doc)
        _conv._memo.clear()
        for pno in range(doc.page_count):
            try:
                page = doc[pno]; tr = page.get_texttrace()
            except Exception:
                continue
            n2x = None
            for sp in tr:
                chars = sp['chars']
                if not chars:
                    continue
                cn = gc.clean_name(sp['font'])
                fam, t = _conv.tb.family(cn)
                if t is None and not any(0xE000 <= c[0] <= 0xF8FF for c in chars):
                    continue
                if n2x is None:
                    n2x = dg.page_map(page)
                xr = tuple(n2x.get(sp['font'], ()))
                grp = fam or ('PUA·옛한글 글꼴' if OLD.search(cn) else 'PUA·그 밖 글꼴')
                for (ucs, gid, org, bbox) in chars:
                    if t is None and not (0xE000 <= ucs <= 0xF8FF):
                        continue
                    text, status, pos, role, eid, how = _conv.char(dg, cn, ucs, gid, xr)
                    cnt[(grp, status)] += 1
                    if status == '미확정':
                        unk[(grp, cn, '%04X' % ucs, how)] += 1
                    elif status in ('확정', '근사') and text != chr(ucs):
                        fixed[grp] += 1
                    if t is None:
                        puatab[(grp, _tab.get(eid, '표 없음') if status != '미확정' else '미확정')] += 1
        doc.close()
    except Exception as e:
        err = '%s: %s' % (type(e).__name__, str(e)[:160])
    return path, cnt, unk, fixed, puatab, err


def main():
    paths = []
    seen = set()
    for l in sys.argv[1].split(','):
        for p in open(l).read().split('\n'):
            p = p.strip()
            if p and p not in seen:
                seen.add(p); paths.append(p)
    paths.sort(key=lambda p: -os.path.getsize(p))
    cnt = collections.Counter(); unk = collections.Counter(); fixed = collections.Counter(); puatab = collections.Counter(); errs = {}
    t0 = time.time()
    with Pool(int(sys.argv[3]), initializer=init) as pool:
        for i, (path, c, u, f, pt, err) in enumerate(pool.imap_unordered(work, paths, chunksize=2)):
            cnt.update(c); unk.update(u); fixed.update(f); puatab.update(pt)
            if err:
                errs[path] = err
    groups = sorted({k[0] for k in cnt})
    print('PDF', len(paths), '권', round(time.time() - t0), 's', '오류', len(errs))
    print('%-16s %10s %10s %8s %9s %9s %7s   %s' % ('묶음', '글자', '확정', '근사', '미확정', '그대로', '확정률', '코드와 다르게 바로잡음'))
    for g in groups:
        a = {s: cnt[(g, s)] for s in ('확정', '근사', '미확정', '그대로')}
        tot = sum(a.values())
        print('%-16s %10d %10d %8d %9d %9d %6.2f%%   %d' % (g, tot, a['확정'], a['근사'], a['미확정'], a['그대로'], 100 * (a['확정'] + a['근사'] + a['그대로']) / max(1, tot), fixed[g]))
    print('PUA 글자가 어느 표로 풀렸나:', {('%s→%s' % k): v for k, v in sorted(puatab.items())})
    hows = collections.Counter()
    for (g, cn, u, how), v in unk.items():
        hows[(g, how.split(':')[0])] += v
    print('미확정 까닭:', {('%s/%s' % k): v for k, v in hows.most_common(30)})
    json.dump({'n': len(paths), 'cnt': [[k[0], k[1], v] for k, v in cnt.items()], 'fixed': dict(fixed), 'puatab': [[k[0], k[1], v] for k, v in puatab.items()],
               'unk': [[k[0], k[1], k[2], k[3], v] for k, v in unk.most_common(3000)], 'errs': errs}, open(sys.argv[2], 'w'), ensure_ascii=False)


if __name__ == '__main__':
    main()
