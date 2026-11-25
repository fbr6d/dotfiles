"""hypua2jamo 표 전체를 JSON으로 뽑기(시험용) + 성질 확인"""
import json, re, unicodedata, collections
import hypua2jamo
print('hypua2jamo', getattr(hypua2jamo, '__version__', '?'))
pua = re.compile('[\ue000-\uf8ff]')
tab_c, tab_d = {}, {}
for o in range(0xE000, 0xF900):
    ch = chr(o)
    c = hypua2jamo.translate(ch, composed=True)
    d = hypua2jamo.translate(ch, composed=False)
    if c != ch: tab_c[o] = c
    if d != ch: tab_d[o] = d
print('표 크기(composed)', len(tab_c), '(decomposed)', len(tab_d))
ks = sorted(tab_c)
# 구역
runs = []; s = ks[0]; p = ks[0]
for k in ks[1:]:
    if k != p + 1:
        runs.append((s, p)); s = k
    p = k
runs.append((s, p))
print('코드 구역:', [(hex(a), hex(b), b - a + 1) for a, b in runs])
# 결과 글자의 블록 분포
blk = collections.Counter()
for v in tab_c.values():
    for x in v:
        o = ord(x)
        b = ('첫소리·가운뎃소리·끝소리 U+1100-11FF' if 0x1100 <= o <= 0x11FF else '자모 확장A U+A960-A97F' if 0xA960 <= o <= 0xA97F else '자모 확장B U+D7B0-D7FF' if 0xD7B0 <= o <= 0xD7FF else '완성형 U+AC00-D7A3' if 0xAC00 <= o <= 0xD7A3 else '방점 U+302E-302F' if o in (0x302E, 0x302F) else f'기타 U+{o:04X}')
        blk[b] += 1
print('결과 글자 블록:', dict(blk))
diff = sum(1 for k in tab_c if tab_c[k] != tab_d.get(k))
print('composed와 decomposed 결과가 다른 코드', diff)
# NFC를 걸면 바뀌는가
ch_nfc = sum(1 for v in tab_c.values() if unicodedata.normalize('NFC', v) != v)
print('NFC로 바뀌는 결과 수', ch_nfc, '예:', [(hex(k), v, unicodedata.normalize('NFC', v)) for k, v in tab_c.items() if unicodedata.normalize('NFC', v) != v][:5])
json.dump({hex(k): v for k, v in tab_c.items()}, open('hanyang_table_composed.json', 'w'), ensure_ascii=False)
import os
print('표 JSON 크기', os.path.getsize('hanyang_table_composed.json'))
