import json, collections, re
rows = [json.loads(l) for l in open('census_sci.jsonl')]
for r in rows:
    if '2028' in r['path'] or '통합과학' in r['path']:
        print(r['path'].split('/')[-1][:60], '쪽', r.get('pages'), '글자', r.get('chars'), r.get('producer'))
        for f, d in sorted(r.get('fonts', {}).items(), key=lambda kv: -kv[1]['n'])[:8]:
            print(f'    {f[:26]:26s} {d["n"]:7d}자 {d["cat"]}')
grp = collections.Counter()
for r in rows:
    p = r['path']; k = 'EBS 과학 본문' if p.startswith('EBS') else '평가원 과학탐구 문제' if '평가원원본' in p else '교과서·예시문항'
    fs = r.get('fonts', {})
    tag = '글자층 없음' if r.get('chars', 0) < 200 else '+'.join(sorted({'HyhwpEQ' if 'HyhwpEQ' in fs else '', 'EH' if any(f.startswith('EH') for f in fs) else '', 'GS' if any(f.startswith('GS') for f in fs) else '', 'TK' if any(f.startswith('TK') for f in fs) else ''} - {''})) or '수식 글꼴 표시 없음'
    grp[(k, tag)] += 1
for (k, t), n in sorted(grp.items()): print(f'{k:14s} {t:22s} {n}')
eq = collections.Counter()
for r in rows:
    d = r.get('fonts', {}).get('HyhwpEQ')
    if d:
        for c, v in d['codes'].items(): eq[c] += v
m = set(json.load(open('census_math_fam.json'))['HyhwpEQ']['codes'])
print('과학 쪽 HyhwpEQ 코드', len(eq), '종, 수학 쪽에 없던 코드', len(set(hex(int(c, 16)) for c in eq) - m))
