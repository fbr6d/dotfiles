"""프로젝트 글 파일의 PUA 글자 전수 세기 (읽기 전용). 결과는 scratch에만 쓴다."""
import os, re, collections, json, sys, time
import hypua2jamo
ROOT = '/home/leejaeik/Projects/ksat-10000'
EXT = ('.md', '.json', '.jsonl', '.csv', '.tsv', '.txt', '.html', '.htm', '.yaml', '.yml', '.tex', '.xml', '.svg')
pua = re.compile('[\ue000-\uf8ff]')
per_file = []
codes = collections.Counter()
t0 = time.time()
nfiles = 0
skipped_big = 0
for top in ('derived', 'wiki', 'plan', 'docs', 'tests', 'assets', 'sync', 'ops', 'cd'):
    for dp, dn, fn in os.walk(os.path.join(ROOT, top)):
        for f in fn:
            if not f.lower().endswith(EXT):
                continue
            p = os.path.join(dp, f)
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            if sz > 60_000_000:
                skipped_big += 1
                continue
            nfiles += 1
            try:
                b = open(p, 'rb').read()
            except OSError:
                continue
            esc = b'\\ue' in b or b'\\uf' in b or b'\\uE' in b or b'\\uF' in b
            if b'\xee' not in b and b'\xef' not in b and not esc:
                continue
            s = b.decode('utf-8', errors='ignore')
            cs = pua.findall(s)
            # JSON 안에 \uXXXX 이스케이프로 든 PUA
            esc_cs = [chr(int(m, 16)) for m in re.findall(r'\\u([eE][0-9a-fA-F]{3}|[fF][0-8][0-9a-fA-F]{2})', s)] if esc else []
            if not cs and not esc_cs:
                continue
            for c in cs + esc_cs:
                codes[ord(c)] += 1
            per_file.append((os.path.relpath(p, ROOT), len(cs), len(esc_cs)))
conv = {}
for c in codes:
    o = hypua2jamo.translate(chr(c))
    conv[c] = o if (o != chr(c) and not pua.search(o)) else None
json.dump({'per_file': per_file, 'codes': {hex(k): v for k, v in codes.items()},
           'conv': {hex(k): v for k, v in conv.items()}}, open('scan_pua_all.json', 'w'), ensure_ascii=False)
tot = sum(codes.values())
ok = sum(v for k, v in codes.items() if conv[k])
print('글 파일', nfiles, '큰 파일 건너뜀', skipped_big, '초', round(time.time() - t0, 1))
print('PUA 든 파일', len(per_file), 'PUA 글자', tot, '(직접', sum(x[1] for x in per_file), '이스케이프', sum(x[2] for x in per_file), ')')
print('서로 다른 코드', len(codes), '한양 표로 바뀌는 글자', ok, '안 바뀌는 글자', tot - ok, '안 바뀌는 코드 종류', sum(1 for k in codes if not conv[k]))
grp = collections.Counter(); grpf = collections.Counter()
for p, a, b in per_file:
    k = '/'.join(p.split('/')[:4])
    grp[k] += a + b; grpf[k] += 1
for k, v in grp.most_common(40):
    print(f'  {v:7d}자 {grpf[k]:5d}파일  {k}')
print('안 바뀌는 코드 상위:', [(hex(k), v) for k, v in codes.most_common() if not conv[k]][:30])
