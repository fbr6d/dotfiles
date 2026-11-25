import json, collections, re
R = '/home/leejaeik/Projects/ksat-10000/raw/수능자료/'
rows = [json.loads(l) for l in open('census_ko.jsonl')]
want = ['T23', 'T17', '*신명-중명조', 'HaansoftBatang', 'HCRBatang', 'Haansoft-Dotum', '*옛한글', 'T19', 'T16']
pick = {}
for w in want:
    best = None
    for r in rows:
        d = r.get('fonts', {}).get(w)
        if not d: continue
        n = sum(v for k, v in d['codes'].items() if 0xE000 <= int(k, 16) <= 0xF8FF)
        if n and (best is None or n > best[0]): best = (n, r['path'])
    if best: pick[w] = best
for w, (n, p) in pick.items(): print(w, n, p.split('/')[-1][:70])
open('list_ko_verify.txt', 'w').write('\n'.join(sorted({R + p for _, p in pick.values()})) + '\n')
