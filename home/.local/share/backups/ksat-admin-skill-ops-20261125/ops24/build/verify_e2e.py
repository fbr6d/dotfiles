# -*- coding: utf-8 -*-
"""도구의 실제 출력 길(convert_page)로 하는 전수 검증.

verify_corpus.py 는 글자 판정(Converter.char)만 센다. 이 스크립트는 쪽마다 실제로 줄을 만들어(convert_page)
나온 결과를 세고, 같은 쪽의 판정 단계 수와 견준다. 쪽에서 오류가 나는지도 함께 본다.

쓰기: /usr/bin/python3 verify_e2e.py <목록.txt[,목록…]> <결과.json> <프로세스 수> <tools 폴더> [all|scope]
  all = 모든 쪽을 돌린다(기본). scope = 수식 글꼴이나 PUA 글자가 있는 쪽만 돌린다.
"""
import sys, os, re, json, time, collections
sys.dont_write_bytecode = True
from multiprocessing import Pool

TOOLS = sys.argv[4]
MODE = sys.argv[5] if len(sys.argv) > 5 else 'all'
sys.path.insert(0, TOOLS)
import pymupdf                      # noqa: E402
import pdf_glyph_text as pgt        # noqa: E402
import glyphcore as gc              # noqa: E402

OLD = re.compile(r'^(Haansoft|\*옛한글|HCRBatang|T\d\d$|\*신명-중명조|TT3678AC74tCID|NewGulim)')
JAMO = re.compile('[\u1100-\u11ff\ua960-\ua97f\ud7b0-\ud7ff]')
ST3 = ('확정', '근사', '미확정')
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


def grp_of(cn, fam):
    return fam or ('PUA·옛한글 글꼴' if OLD.search(cn) else 'PUA·그 밖 글꼴')


def work(path):
    C = collections.Counter
    cls, e2e, extra, posc, koh, misc = C(), C(), C(), C(), C(), C()
    perr = []
    err = None
    try:
        doc = pymupdf.open(path)
        dg = gc.DocGlyphs(doc)
        _conv._memo.clear()
        for pno in range(doc.page_count):
            try:
                page = doc[pno]
                tr = page.get_texttrace()
            except Exception as e:
                perr.append([pno + 1, 'texttrace ' + type(e).__name__])
                continue
            n2x = None
            inscope = 0
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
                grp = grp_of(cn, fam)
                for (ucs, gid, org, bbox) in chars:
                    if t is None and not (0xE000 <= ucs <= 0xF8FF):
                        continue
                    r = _conv.char(dg, cn, ucs, gid, xr)
                    cls[(grp, r[1])] += 1
                    inscope += 1
            if MODE == 'scope' and not inscope:
                continue
            misc['쪽'] += 1
            if inscope:
                misc['범위 안 글자가 있는 쪽'] += 1
            if page.rotation:
                misc['돌려 놓은 쪽(/Rotate)'] += 1
            try:
                lines, stat = pgt.convert_page(_conv, doc, dg, pno)
            except Exception as e:
                perr.append([pno + 1, '%s: %s' % (type(e).__name__, str(e)[:120])])
                continue
            misc['줄'] += len(lines)
            nmark = nunk = 0
            for ln in lines:
                nmark += ln['text'].count('⟦')
                for c in ln['chars']:
                    cn = c['font']
                    u = int(c['ucs'], 16)
                    fam, t = _conv.tb.family(cn)
                    st = c['status']
                    how = c['how'] or ''
                    if st == '미확정':
                        nunk += 1
                    if t is None and not (0xE000 <= u <= 0xF8FF):
                        if st != '그대로':
                            extra[('범위 밖 글자', st + ' · ' + how[:22])] += 1
                        continue
                    grp = grp_of(cn, fam)
                    if how == '글자층 대조 실패':
                        extra[(grp, '글자층 대조 실패')] += 1
                        continue
                    if st in ST3:
                        e2e[(grp, st)] += 1
                    if c['pos'] != 'base':
                        posc[(grp, c['pos'], '놓인 자리로 바꿈' if '놓인 자리' in how else '표대로')] += 1
                    if st in ('확정', '근사') and JAMO.search(c['text']):
                        koh[(grp, _tab.get(c['id'], '표 없음'))] += 1
            if nmark != nunk:
                misc['⟦ 표시 수와 미확정 글자 수가 다른 쪽'] += 1
        doc.close()
    except Exception as e:
        err = '%s: %s' % (type(e).__name__, str(e)[:160])
    return path, cls, e2e, extra, posc, koh, misc, perr, err


def main():
    paths = []
    seen = set()
    for l in sys.argv[1].split(','):
        for p in open(l).read().split('\n'):
            p = p.strip()
            if p and p not in seen:
                seen.add(p)
                paths.append(p)
    paths.sort(key=lambda p: -os.path.getsize(p))
    C = collections.Counter
    cls, e2e, extra, posc, koh, misc = C(), C(), C(), C(), C(), C()
    errs = {}
    perrs = []
    diffpdf = []
    t0 = time.time()
    with Pool(int(sys.argv[3]), initializer=init) as pool:
        for i, (path, a, b, x, pc, kh, ms, perr, err) in enumerate(pool.imap_unordered(work, paths, chunksize=1)):
            cls.update(a); e2e.update(b); extra.update(x); posc.update(pc); koh.update(kh); misc.update(ms)
            if err:
                errs[path] = err
            for pe in perr:
                perrs.append([os.path.basename(path)] + pe)
            d = sum(b[k] for k in b) - sum(v for k, v in a.items() if k[1] in ST3)
            if d:
                diffpdf.append([os.path.basename(path), d])
            if (i + 1) % 100 == 0:
                print(i + 1, '권', round(time.time() - t0), 's', flush=True)
    print('PDF %d권 · %d쪽(범위 안 글자가 있는 쪽 %d) · %d줄 · %ds · PDF 오류 %d · 쪽 오류 %d' % (
        len(paths), misc['쪽'], misc['범위 안 글자가 있는 쪽'], misc['줄'], round(time.time() - t0), len(errs), len(perrs)))
    print('%-16s | 판정 단계  확정      근사    미확정 | 출력 단계  확정      근사    미확정 | 차이(출력−판정) | 대조 실패' % '묶음')
    for g in sorted({k[0] for k in cls} | {k[0] for k in e2e}):
        a = [cls[(g, s)] for s in ST3]
        b = [e2e[(g, s)] for s in ST3]
        print('%-16s | %14d %8d %8d | %14d %8d %8d | %6d %5d %5d | %d' % (g, a[0], a[1], a[2], b[0], b[1], b[2], b[0] - a[0], b[1] - a[1], b[2] - a[2], extra[(g, '글자층 대조 실패')]))
    ta = [sum(cls[(g, s)] for g in {k[0] for k in cls}) for s in ST3]
    tb = [sum(e2e[(g, s)] for g in {k[0] for k in e2e}) for s in ST3]
    print('%-16s | %14d %8d %8d | %14d %8d %8d |' % ('합계', ta[0], ta[1], ta[2], tb[0], tb[1], tb[2]))
    print('출력 단계에서만 생긴 것:', {('%s / %s' % k): v for k, v in extra.most_common(12)})
    print('옛한글 자모로 나온 글자(묶음→표):', {('%s→%s' % k): v for k, v in sorted(koh.items())})
    print('첨자:', {('%s/%s/%s' % k): v for k, v in sorted(posc.items())})
    print('그 밖:', {k: v for k, v in misc.items() if k not in ('쪽', '줄', '범위 안 글자가 있는 쪽')})
    diffpdf.sort(key=lambda t: -abs(t[1]))
    print('출력과 판정의 글자 수가 다른 PDF', len(diffpdf), diffpdf[:6])
    for pe in perrs[:8]:
        print('   쪽 오류:', pe)
    for k, v in list(errs.items())[:5]:
        print('   PDF 오류:', os.path.basename(k), v)
    json.dump({'n': len(paths), 'mode': MODE, 'sec': round(time.time() - t0), 'misc': dict(misc),
               'cls': [[k[0], k[1], v] for k, v in cls.items()], 'e2e': [[k[0], k[1], v] for k, v in e2e.items()],
               'extra': [[k[0], k[1], v] for k, v in extra.items()], 'pos': [[k[0], k[1], k[2], v] for k, v in posc.items()],
               'koh': [[k[0], k[1], v] for k, v in koh.items()], 'diffpdf': diffpdf[:200], 'page_errors': perrs[:500], 'errs': errs},
              open(sys.argv[2], 'w'), ensure_ascii=False)


if __name__ == '__main__':
    main()
