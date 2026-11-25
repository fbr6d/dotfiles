import json, collections
R = '/home/leejaeik/Projects/ksat-10000/raw/수능자료/'
rows = [json.loads(l) for l in open('census_math.jsonl')]
ex = sorted([r for r in rows if 'HyhwpEQ' in r.get('fonts', {}) and r['fonts']['HyhwpEQ']['n'] > 1500], key=lambda r: r['path'])
by = collections.defaultdict(list)
for r in ex: by[r['path'].split('/')[2]].append(r)
pick = []
for y in sorted(by):
    pick.append(by[y][-1])
print(len(ex), '개 중', len(pick), '개 고름')
open('list_eq.txt', 'w').write('\n'.join(R + r['path'] for r in pick) + '\n')
for r in pick: print(r['path'].split('/')[-1][:70], r['fonts']['HyhwpEQ']['n'], r.get('producer'))
