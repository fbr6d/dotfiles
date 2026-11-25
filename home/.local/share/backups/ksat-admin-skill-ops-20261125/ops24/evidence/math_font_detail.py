"""수식 글꼴 객체의 속: 인코딩 사전, 글리프 이름, cmap (읽기 전용)"""
import collections, re, sys, io
import pymupdf
from fontTools.ttLib import TTFont
from fontTools.cffLib import CFFFontSet
ROOT = '/home/leejaeik/Projects/ksat-10000/raw/수능자료/교과서/'
book = sys.argv[1]
pat = re.compile(sys.argv[2])
doc = pymupdf.open(ROOT + book)
seen = collections.defaultdict(list)
for pno in range(len(doc)):
    for xref, ext, typ, base, name, enc in doc.get_page_fonts(pno):
        nm = re.sub(r'^[A-Z]{6}\+', '', base)
        if pat.search(nm) and xref not in [x for x, _ in seen[nm]]:
            seen[nm].append((xref, pno))
for nm, lst in seen.items():
    print(f'=== {nm}: 객체 {len(lst)}개')
    shown = 0
    for xref, pno in lst:
        obj = doc.xref_object(xref, compressed=True)
        has_tu = '/ToUnicode' in obj
        if shown >= 2:
            break
        shown += 1
        print(f' - xref {xref} (쪽 {pno+1}) ToUnicode={has_tu}')
        print('   사전:', obj[:420])
        m = re.search(r'/Encoding (\d+) 0 R', obj)
        if m:
            print('   인코딩 객체:', doc.xref_object(int(m.group(1)), compressed=True)[:600])
        try:
            bn, ext, typ, buf = doc.extract_font(xref)
        except Exception as e:
            print('   글꼴 꺼내기 실패', e); continue
        print(f'   글꼴 파일: {ext} {typ} {len(buf)}바이트')
        try:
            if ext in ('ttf', 'otf'):
                f = TTFont(io.BytesIO(buf), lazy=True)
                go = f.getGlyphOrder()
                named = [g for g in go if not re.fullmatch(r'(glyph|gid|cid|index|uni)?[0-9A-Fa-f]*|\.notdef', g)]
                print(f'   표: {sorted(f.keys())}')
                print(f'   글리프 {len(go)}개, 이름 예: {go[:12]} … 뜻 있는 이름 {len(named)}개: {named[:25]}')
                if 'cmap' in f:
                    for t in f['cmap'].tables:
                        items = sorted(t.cmap.items())
                        print(f'   cmap ({t.platformID},{t.platEncID}) fmt{t.format} {len(items)}개: {[(hex(k), v) for k, v in items[:10]]}')
                if 'post' in f:
                    print('   post 형식', f['post'].formatType)
            elif ext == 'cff':
                cff = CFFFontSet(); cff.decompile(io.BytesIO(buf), None)
                top = cff[0]
                names = top.charset
                print(f'   CFF 글리프 {len(names)}개: {names[:60]}')
        except Exception as e:
            print('   분석 실패', type(e).__name__, e)
