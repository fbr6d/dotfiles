# '표에 없는 모양'으로 남은 글자가 표의 어느 기준 모양과 얼마나 닮았는지 본다(진단용).
# 쓰기: /usr/bin/python3 t_unk.py <PDF> <표 폴더> [쪽 수 한도=40]
import sys, os, collections
sys.path.insert(0, 'proj/tools'); sys.path.insert(0, 'proj/tools/glyph')
import pymupdf
import glyphcore as gc
import pdf_glyph_text as T
pymupdf.TOOLS.mupdf_display_errors(False)
conv = T.Converter(T.Tables(sys.argv[2]))
doc = pymupdf.open(sys.argv[1]); dg = gc.DocGlyphs(doc)
lim = int(sys.argv[3]) if len(sys.argv) > 3 else 40
seen = {}
cnt = collections.Counter(); st = collections.Counter()
step = max(1, doc.page_count // lim)
for pno in range(0, doc.page_count, step):
    page = doc[pno]; n2x = dg.page_map(page)
    for sp in page.get_texttrace():
        cn = gc.clean_name(sp['font']); fam, t = conv.tb.family(cn)
        if t is None:
            continue
        xr = tuple(n2x.get(sp['font'], ()))
        for (ucs, gid, org, bbox) in sp['chars']:
            res = conv.char(dg, cn, ucs, gid, xr)
            st[(fam, res[1])] += 1
            if res[1] != '미확정':
                continue
            k = (cn, ucs, gid, xr)
            cnt[k] += 1
            if k in seen:
                continue
            h = dg.span_hash(xr, gid)
            if h in T.NOSHAPE:
                seen[k] = (h, None, None, None, None); continue
            sh = dg.shapes[h]
            def best(ents):
                b = (0.0, None)
                for e in ents:
                    for r in e['_shapes']:
                        s = gc.tol_score(sh, r)
                        if s > b[0]:
                            b = (s, e)
                return b
            bk = best(t['by_key'].get((cn, ucs), ())); bu = best(t['by_ucs'].get(ucs, ())); ba = best(t['entries'])
            typ = 'T3' if (xr and dg._is_t3(xr[0])) else '보통'
            seen[k] = (typ, bk, bu, ba, res[5])
print('상태:', dict(st))
hist = collections.Counter(); rows = []
for k, v in seen.items():
    n = cnt[k]
    if v[1] is None:
        hist[('모양 없음', v[0])] += n; continue
    typ, bk, bu, ba, how = v
    b = '%.2f' % (int(bk[0] * 20) / 20)
    hist[(typ, '같은 글꼴·코드 기준과 닮음 ' + b)] += n
    rows.append((n, k[0], '%04X' % k[1], typ, round(bk[0], 3), bk[1]['text'] if bk[1] else None, round(bu[0], 3), round(ba[0], 3), ba[1]['text'] if ba[1] else None, ba[1]['sheet'] if ba[1] else None, how))
for k, v in sorted(hist.items()):
    print('  ', k, v)
rows.sort(reverse=True)
for r in rows[:28]:
    print('  ', r)
