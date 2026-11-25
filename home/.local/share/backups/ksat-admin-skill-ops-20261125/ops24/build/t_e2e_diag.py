# -*- coding: utf-8 -*-
"""출력 단계(convert_page)와 판정 단계(Converter.char)의 글자 수가 왜 다른지 가른다(진단용).

쓰기: /usr/bin/python3 t_e2e_diag.py <목록.txt> <프로세스 수> <tools 폴더> [결과.json]
"""
import sys, os, re, json, collections
sys.dont_write_bytecode = True
from multiprocessing import Pool

TOOLS = sys.argv[3]
sys.path.insert(0, TOOLS)
import pymupdf                      # noqa: E402
import pdf_glyph_text as pgt        # noqa: E402
import glyphcore as gc              # noqa: E402

OLD = re.compile(r'^(Haansoft|\*옛한글|HCRBatang|T\d\d$|\*신명-중명조|TT3678AC74tCID|NewGulim)')
_conv = None


def init():
    global _conv
    _conv = pgt.Converter(pgt.Tables(os.path.join(TOOLS, 'glyph')))


def K(p):
    return (round(p[0], 1), round(p[1], 1))


def work(path):
    C = collections.Counter
    lab, fffd_font, unm, rot = C(), C(), C(), C()
    ex = []
    nchar = nfffd = 0
    name = os.path.basename(path)
    try:
        doc = pymupdf.open(path)
        dg = gc.DocGlyphs(doc)
        _conv._memo.clear()
        for pno in range(doc.page_count):
            page = doc[pno]
            try:
                tr = page.get_texttrace()
            except Exception:
                continue
            tk = C()
            ins = []
            allc = []
            n2x = None
            for sp in tr:
                chars = sp['chars']
                if not chars:
                    continue
                cn = gc.clean_name(sp['font'])
                fam, t = _conv.tb.family(cn)
                need = t is not None or any(0xE000 <= c[0] <= 0xF8FF or c[0] == 0xFFFD for c in chars)
                if need and n2x is None:
                    n2x = dg.page_map(page)
                xr = tuple(n2x.get(sp['font'], ())) if need else ()
                for (ucs, gid, org, bbox) in chars:
                    k = K(org)
                    tk[k] += 1
                    nchar += 1
                    allc.append((ucs, org))
                    if t is not None or 0xE000 <= ucs <= 0xF8FF:
                        r = _conv.char(dg, cn, ucs, gid, xr)
                        if r[1] in ('확정', '근사', '미확정'):
                            ins.append((k, ucs, org, bbox, sp.get('type'), fam or ('옛한글 글꼴' if OLD.search(cn) else '그 밖 글꼴 PUA'), cn))
                    elif ucs == 0xFFFD:
                        r = _conv.char(dg, cn, ucs, gid, xr)
                        if r[1] == '미확정':
                            nfffd += 1
                            fffd_font[cn] += 1
            rd = page.get_text('rawdict', flags=pgt.RAW_FLAGS)
            rk = C()
            rchars = []
            for b in rd.get('blocks', []):
                for ln in b.get('lines', []):
                    for sp in ln.get('spans', []):
                        for ch in sp.get('chars', []):
                            k = K(ch['origin'])
                            rk[k] += 1
                            rchars.append((k, ch['c']))
            R = page.rotation
            ratio = 1.0
            if tk:
                hit = sum(min(v, rk.get(k, 0)) for k, v in tk.items())
                ratio = hit / max(1, sum(tk.values()))
                rot[('돌려 놓은 쪽 %d도' % R if R else '바로 놓인 쪽', '자리 맞음' if ratio > 0.9 else ('일부만 맞음' if ratio > 0.1 else '안 맞음'))] += 1
                if ratio <= 0.9 and len(ex) < 2 and allc:
                    res = {}
                    for nm, M in (('rotation_matrix', page.rotation_matrix), ('derotation_matrix', page.derotation_matrix)):
                        h = 0
                        for (ucs, org) in allc[:400]:
                            p = pymupdf.Point(org[0], org[1]) * M
                            if rk.get(K((p.x, p.y)), 0):
                                h += 1
                        res[nm] = round(h / max(1, min(400, len(allc))), 2)
                    ex.append(['자리 안 맞는 쪽', name[:44], pno + 1, 'R=%d' % R, '맞는 비율 %.2f' % ratio, res, 'rect ' + str(page.rect), 'mediabox ' + str(page.mediabox), 'cropbox ' + str(page.cropbox)])
            used = C()
            for (k, ucs, org, bbox, typ, g, cn) in ins:
                used[k] += 1
                if used[k] <= rk.get(k, 0):
                    lab[(g, '출력에 있음')] += 1
                elif rk.get(k, 0) > 0:
                    lab[(g, '같은 자리에 겹쳐 찍음')] += 1
                elif ratio <= 0.1:
                    lab[(g, '쪽 전체가 자리 대조 안 됨')] += 1
                else:
                    near = any(u2 == ucs and (o2[0] != org[0] or o2[1] != org[1]) and abs(o2[0] - org[0]) < 1.5 and abs(o2[1] - org[1]) < 1.5 for (u2, o2) in allc)
                    inside = page.rect.contains(pymupdf.Point(org[0], org[1]))
                    l = '가까이 겹쳐 찍음' if near else ('쪽 밖' if not inside else '사라짐')
                    lab[(g, l)] += 1
                    if l == '사라짐' and len(ex) < 6:
                        ex.append(['사라짐', name[:44], pno + 1, '%04X' % ucs, [round(v, 1) for v in org], [round(v, 1) for v in bbox], 'type %s' % typ, cn[:20]])
            usedr = C()
            for (k, c) in rchars:
                usedr[k] += 1
                if usedr[k] > tk.get(k, 0):
                    u = ord(c)
                    cl = 'U+FFFD' if u == 0xFFFD else ('PUA' if 0xE000 <= u <= 0xF8FF else ('공백' if c.isspace() else '보통 글자'))
                    unm[(cl, '자리 안 맞는 쪽' if ratio <= 0.9 else '자리 맞는 쪽')] += 1
        doc.close()
    except Exception as e:
        ex.append(['오류', name[:44], '%s: %s' % (type(e).__name__, str(e)[:100])])
    return name, lab, nfffd, fffd_font, unm, rot, ex, nchar


def main():
    paths = [p.strip() for p in open(sys.argv[1]).read().split('\n') if p.strip()]
    paths.sort(key=lambda p: -os.path.getsize(p))
    C = collections.Counter
    lab, fonts, unm, rot = C(), C(), C(), C()
    per = []
    exs = []
    with Pool(int(sys.argv[2]), initializer=init) as pool:
        for (name, a, nf, ff, u, r, ex, nchar) in pool.imap_unordered(work, paths, chunksize=1):
            lab.update(a); fonts.update(ff); unm.update(u); rot.update(r)
            if nf:
                per.append((nf, nchar, name))
            exs.extend(ex)
    print('범위 안 글자(판정 단계)가 출력에서 어떻게 됐나:')
    for g in sorted({k[0] for k in lab}):
        print('   %-14s' % g, {k[1]: v for k, v in sorted(lab.items()) if k[0] == g})
    print('쪽의 자리 대조:', {('%s·%s' % k): v for k, v in sorted(rot.items())})
    print('글자층 대조가 안 된 출력 글자:', {('%s·%s' % k): v for k, v in sorted(unm.items())})
    per.sort(reverse=True)
    tot = sum(p[0] for p in per)
    print('보통 글꼴의 코드 없는 글자(U+FFFD, 빈 글리프 아님): %d자 · %d권' % (tot, len(per)))
    for nf, nchar, name in per[:14]:
        print('   %7d자 (그 PDF 글자의 %5.1f%%)  %s' % (nf, 100 * nf / max(1, nchar), name[:70]))
    print('   상위 14권 합', sum(p[0] for p in per[:14]), '· 글자의 절반 넘게 코드가 없는 PDF', sum(1 for p in per if p[0] > 0.5 * p[1]), '권')
    print('   글꼴 상위:', [(k[:24], v) for k, v in fonts.most_common(12)])
    for e in exs[:14]:
        print('  ', e)
    if len(sys.argv) > 4:
        json.dump({'lab': [[k[0], k[1], v] for k, v in lab.items()], 'rot': [[k[0], k[1], v] for k, v in rot.items()], 'unm': [[k[0], k[1], v] for k, v in unm.items()],
                   'fffd_pdf': per, 'fffd_font': fonts.most_common(200), 'ex': exs[:100]}, open(sys.argv[4], 'w'), ensure_ascii=False)


if __name__ == '__main__':
    main()
