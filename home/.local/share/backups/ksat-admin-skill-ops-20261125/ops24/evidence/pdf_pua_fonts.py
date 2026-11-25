"""PDF 한 권에서 PUA·수상한 글자를 글꼴별로 세기 (읽기 전용). texttrace 사용."""
import collections, re, sys, json
import pymupdf
path = sys.argv[1]
maxpages = int(sys.argv[2]) if len(sys.argv) > 2 else 10**9
doc = pymupdf.open(path)
meta = doc.metadata
per = collections.defaultdict(collections.Counter)   # font -> code counter
tot_font = collections.Counter()
n = 0
for pno in range(min(len(doc), maxpages)):
    for sp in doc[pno].get_texttrace():
        f = re.sub(r'^[A-Z]{6}\+', '', sp['font'])
        for ucs, gid, org, bbox in sp['chars']:
            n += 1
            tot_font[f] += 1
            if 0xE000 <= ucs <= 0xF8FF or ucs == 0xFFFD:
                per[f][ucs] += 1
print(f'{path.split("/")[-1]}: 쪽 {len(doc)}, producer={meta.get("producer")!r}, creator={meta.get("creator")!r}, 글자 {n}')
def hy(o):
    return 0xE0BC <= o <= 0xEFFF or 0xF100 <= o <= 0xF66E or 0xF784 <= o <= 0xF8F7
for f, c in sorted(per.items(), key=lambda kv: -sum(kv[1].values())):
    tot = sum(c.values())
    inhy = sum(v for k, v in c.items() if hy(k))
    print(f'  {f[:38]:38s} PUA {tot:6d}자 / 글꼴 전체 {tot_font[f]:7d}자, 코드 {len(c):3d}종, 한양 구역 안 {inhy:6d}자 | 예: ' + ' '.join(f'{k:04X}({v})' for k, v in c.most_common(8)))
json.dump({f: {hex(k): v for k, v in c.items()} for f, c in per.items()}, open('pdfpua_' + re.sub(r'\W+', '_', path.split('/')[-1])[:60] + '.json', 'w'))
