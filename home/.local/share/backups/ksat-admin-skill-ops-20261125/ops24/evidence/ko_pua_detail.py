"""국어 쪽 산출물의 PUA 코드 분포·문맥 (읽기 전용)"""
import json, collections, re, os, sys, unicodedata
import hypua2jamo
ROOT = '/home/leejaeik/Projects/ksat-10000/'
d = json.load(open('scan_pua_all.json'))
pua = re.compile('[\ue000-\uf8ff]')
def is_ko(p):
    return ('국어' in p or 'korean' in p) and not p.startswith('derived/llm-wiki/staging/math')
files = [(p, a, b) for p, a, b in d['per_file'] if is_ko(p)]
print('국어 경로의 PUA 파일', len(files), '글자', sum(a + b for _, a, b in files))
grp = collections.Counter()
for p, a, b in files:
    grp['/'.join(p.split('/')[:5])] += a + b
for k, v in grp.most_common(25):
    print(f'  {v:6d}  {k}')
codes = collections.Counter(); ctx = collections.defaultdict(list); fcount = collections.defaultdict(set)
for p, a, b in files:
    s = open(ROOT + p, encoding='utf-8', errors='ignore').read()
    s2 = re.sub(r'\\u([eE][0-9a-fA-F]{3}|[fF][0-8][0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), s)
    for m in pua.finditer(s2):
        c = m.group(0); codes[c] += 1; fcount[c].add(p)
        if len(ctx[c]) < 3:
            ctx[c].append(s2[max(0, m.start() - 8): m.end() + 8].replace('\n', '⏎'))
print('서로 다른 코드', len(codes), '총', sum(codes.values()))
def block(o):
    if 0xE0BC <= o <= 0xEFFF: return '한양 음절 구역(E0BC-EFFF)'
    if 0xF100 <= o <= 0xF66E: return '한양 자모 구역(F100-F66E)'
    if 0xF784 <= o <= 0xF8F7: return '한양 자모·방점 구역(F784-F8F7)'
    return '한양 표 밖'
bl = collections.Counter(); blk = collections.Counter()
for c, n in codes.items():
    bl[block(ord(c))] += n; blk[block(ord(c))] += 1
print('구역별 글자 수', dict(bl)); print('구역별 코드 종류', dict(blk))
json.dump({c: n for c, n in codes.items()}, open('ko_codes.json', 'w'), ensure_ascii=False)
print('--- 가장 많이 나온 30개')
for c, n in codes.most_common(30):
    o = hypua2jamo.translate(c)
    print(f'U+{ord(c):04X} {n:5d}회 {len(fcount[c]):3d}파일 → {o!r:14} {[hex(ord(x)) for x in o]} | {ctx[c][0]!r}')
print('--- 드물게 나온 것 25개')
for c, n in codes.most_common()[-25:]:
    o = hypua2jamo.translate(c)
    print(f'U+{ord(c):04X} {n:5d}회 → {o!r:14} | {ctx[c][0]!r}')
