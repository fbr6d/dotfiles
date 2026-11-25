import json, collections, re
rows = [json.loads(l) for l in open('census_math.jsonl')]
ex = [r for r in rows if r['path'].startswith('시험지/평가원원본')]
print('평가원 수학 문제 PDF', len(ex))
grp = collections.Counter(); yr = collections.defaultdict(collections.Counter)
for r in ex:
    fs = r.get('fonts', {})
    y = r['path'].split('/')[2]
    if r.get('chars', 0) < 200: k = '글자층 없음(그림)'
    elif 'HyhwpEQ' in fs: k = 'HyhwpEQ'
    else:
        mf = [f for f in fs if re.search(r'EQ|Math|Symbol|MT|Euclid|수식', f, re.I)]
        k = '다른 수식 글꼴: ' + ','.join(sorted(mf)[:3]) if mf else '수식 글꼴 표시 없음'
    grp[k] += 1; yr[k][y] += 1
for k, n in grp.most_common(12): print(f'  {n:4d}  {k[:70]}  연도 {dict(sorted(yr[k].items()))}')
# HyhwpEQ 코드 전체
codes = collections.Counter()
for r in rows:
    d = r.get('fonts', {}).get('HyhwpEQ')
    if d:
        for k, v in d['codes'].items(): codes[int(k, 16)] += v
print('HyhwpEQ 코드', len(codes), '종, 구역:', collections.Counter('PUA' if 0xE000 <= k <= 0xF8FF else 'ASCII' if k < 0x80 else '라틴-1' if k <= 0xFF else '기타' for k in codes))
print('코드 범위', hex(min(k for k in codes if k >= 0xE000)), hex(max(codes)))
# EBS 수학 본문 글꼴
eb = [r for r in rows if r['path'].startswith('EBS')]
print('EBS 수학 본문 PDF', len(eb), '글자층 없음', sum(1 for r in eb if r.get('chars', 0) < 200), 'EHsang 있는 PDF', sum(1 for r in eb if any(f.startswith('EHsang') for f in r.get('fonts', {}))))
tb = [r for r in rows if r['path'].startswith('교과서')]
for r in tb:
    fs = r.get('fonts', {}); mf = sorted({re.sub(r'-.*', '', f) for f in fs if re.search(r'^EH|Kab|susic|Math|Symbol|EQ', f)})
    print('  교과서', r['path'].split('/')[-1][:22], '쪽', r.get('pages'), '글자', r.get('chars'), '수식 글꼴:', mf[:8])
