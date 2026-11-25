# -*- coding: utf-8 -*-
"""수식 글꼴·PUA 글자 가운데 바로 놓이지 않은 것(돌림·거울 뒤집기)을 센다(진단용).
쓰기: /usr/bin/python3 t_mirror.py <목록,목록…> <프로세스 수> <tools 폴더> [결과.json]
"""
import sys, os, json, collections
sys.dont_write_bytecode = True
from multiprocessing import Pool
TOOLS = sys.argv[3]
sys.path.insert(0, TOOLS)
import pymupdf, pdf_glyph_text as pgt, glyphcore as gc
_conv = None


def init():
    global _conv
    _conv = pgt.Converter(pgt.Tables(os.path.join(TOOLS, 'glyph')))


def work(path):
    C = collections.Counter
    kinds = C(); mir = C(); ex = {}
    name = os.path.basename(path)
    try:
        doc = pymupdf.open(path); dg = gc.DocGlyphs(doc); _conv._memo.clear()
        for pno in range(doc.page_count):
            page = doc[pno]
            try:
                tr = page.get_texttrace()
            except Exception:
                continue
            n2x = None
            for sp in tr:
                chars = sp['chars']
                if not chars:
                    continue
                cn = gc.clean_name(sp['font']); fam, t = _conv.tb.family(cn)
                if t is None and not any(0xE000 <= c[0] <= 0xF8FF for c in chars):
                    continue
                d = sp['dir']
                for (ucs, gid, org, bb) in chars:
                    if t is None and not (0xE000 <= ucs <= 0xF8FF):
                        continue
                    if bb[2] - bb[0] < 0.01 and bb[3] - bb[1] < 0.01:
                        kinds['상자 없음'] += 1; continue
                    right = (bb[0] + bb[2]) / 2 >= org[0] - 0.01
                    above = (bb[1] + bb[3]) / 2 <= org[1] + 0.01
                    if abs(d[0] - 1) < 1e-3 and abs(d[1]) < 1e-3:
                        k = '바로 놓임' if above else '위아래 뒤집힘'
                    elif abs(d[0] + 1) < 1e-3 and abs(d[1]) < 1e-3:
                        k = '좌우 거울 뒤집힘' if above else '180도 돌림'
                    elif abs(d[0]) < 1e-3:
                        k = '90도 돌림'
                    else:
                        k = '비스듬히 돌림'
                    kinds[k] += 1
                    if k in ('좌우 거울 뒤집힘', '위아래 뒤집힘'):
                        if n2x is None:
                            n2x = dg.page_map(page)
                        r = _conv.char(dg, cn, ucs, gid, tuple(n2x.get(sp['font'], ())))
                        key = (k, fam or 'PUA', r[0], r[1])
                        mir[key] += 1
                        ex.setdefault(key, '%s p%d' % (name[:40], pno + 1))
        doc.close()
    except Exception as e:
        kinds['오류'] += 1
    return name, kinds, mir, ex


def main():
    paths = []; seen = set()
    for l in sys.argv[1].split(','):
        for p in open(l).read().split('\n'):
            p = p.strip()
            if p and p not in seen:
                seen.add(p); paths.append(p)
    C = collections.Counter
    kinds = C(); mir = C(); ex = {}; pdfs = collections.defaultdict(set)
    with Pool(int(sys.argv[2]), initializer=init) as pool:
        for name, k, m, e in pool.imap_unordered(work, paths, chunksize=2):
            kinds.update(k); mir.update(m)
            for key, v in e.items():
                ex.setdefault(key, v); pdfs[key].add(name)
    print('PDF', len(paths), '권 · 범위 안 글자가 놓인 꼴:', dict(kinds.most_common()))
    print('뒤집어 찍은 글자: %d자 · %d종' % (sum(mir.values()), len(mir)))
    for key, v in mir.most_common(40):
        print('   %-10s %-8s %-6s %-4s %6d자 · %3d권 · 예 %s' % (key[0], key[1], key[2], key[3], v, len(pdfs[key]), ex[key]))
    if len(sys.argv) > 4:
        json.dump({'kinds': dict(kinds), 'mirror': [[k[0], k[1], k[2], k[3], v, len(pdfs[k]), ex[k]] for k, v in mir.most_common()]}, open(sys.argv[4], 'w'), ensure_ascii=False)


if __name__ == '__main__':
    main()
