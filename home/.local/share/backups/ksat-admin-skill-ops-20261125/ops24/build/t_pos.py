# 첨자 자리(위·아래)를 놓인 자리로 다시 정하는 규칙을 시험한다.
# 쓰기: /usr/bin/python3 t_pos.py <표 폴더> <쪽 수 한도> <PDF> [<PDF> …]
import sys, os, collections
sys.path.insert(0, 'proj/tools'); sys.path.insert(0, 'proj/tools/glyph')
import pymupdf
import glyphcore as gc
import pdf_glyph_text as T
pymupdf.TOOLS.mupdf_display_errors(False)
conv = T.Converter(T.Tables(sys.argv[1]))
lim = int(sys.argv[2])
for path in sys.argv[3:]:
    doc = pymupdf.open(path); dg = gc.DocGlyphs(doc)
    T.POS_DEBUG = []
    flips = collections.Counter(); ex = collections.defaultdict(list); nscript = 0; nobase = 0
    step = max(1, doc.page_count // lim)
    for pno in range(0, doc.page_count, step):
        lines, stat = T.convert_page(conv, doc, dg, pno)
        for ln in lines:
            for c in ln['chars']:
                if c['pos'] != 'base' or '놓인 자리' in (c['how'] or ''):
                    nscript += 1
                if '놓인 자리' in (c['how'] or ''):
                    k = (c['font'][:14], '표 sup→sub' if c['pos'] == 'sub' else '표 sub→sup')
                    flips[k] += 1
                    if len(ex[k]) < 3:
                        ex[k].append('p%d %s | %s' % (pno + 1, c['text'], ln['text'][:60]))
    h = collections.Counter()
    for p, rel, t in T.POS_DEBUG:
        b = max(-0.5, min(1.2, round(rel * 10) / 10))
        h[(p, b)] += 1
    print('==', os.path.basename(path)[:50], '· 첨자 꼴 글자', nscript, '· 같은 줄 본문과 견준 것', len(T.POS_DEBUG), '· 뒤집힌 것', sum(flips.values()))
    for p in ('sup', 'sub'):
        print('   표 %s 의 높이 비율 분포:' % p, ' '.join('%.1f:%d' % (b, n) for (pp, b), n in sorted(h.items()) if pp == p))
    for k, v in flips.most_common(8):
        print('   ', k, v, ex[k])
