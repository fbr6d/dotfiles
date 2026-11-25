"""국어 산출물의 PUA 코드를, 원본 PDF 전수에서 그 코드를 쓴 글꼴 종류로 나누기"""
import json, collections, re
fam = json.load(open('census_ko_fam.json'))
HY = re.compile(r'^(Haansoft-?\s?Batang|Haansoft-Dotum|HaansoftBatang|\*옛한글|HCRBatang|T\d\d|\*신명-중명조|TT3678AC74tCID|NewGulim)$')
cls = collections.defaultdict(lambda: collections.Counter())
for f, a in fam.items():
    kind = 'old' if HY.match(f) else 'sym'
    for k, v in a['codes'].items():
        u = int(k, 16)
        if 0xE000 <= u <= 0xF8FF: cls[u][kind] += v
codes = {ord(k): v for k, v in json.load(open('ko_codes.json')).items()}
tab = {int(k, 16) for k in json.load(open('hanyang_table_composed.json'))}
res = collections.Counter(); kinds = collections.Counter(); ex = collections.defaultdict(list)
for u, n in codes.items():
    c = cls.get(u)
    if u not in tab: k = '한양 표에 없는 코드'
    elif not c: k = '원본 전수(207권)에서 못 본 코드'
    elif c['old'] and not c['sym']: k = '옛한글 글꼴에서만 나온 코드'
    elif c['sym'] and not c['old']: k = '기호 글꼴에서만 나온 코드'
    else: k = '두 종류 글꼴 모두에서 나온 코드'
    res[k] += n; kinds[k] += 1; ex[k].append((n, f'{u:04X}'))
tot = sum(codes.values())
print('국어 산출물 PUA', tot, '자', len(codes), '종')
for k, n in res.most_common():
    print(f'  {k}: {n}자 ({n * 100 / tot:.1f}%), 코드 {kinds[k]}종, 많은 것: ' + ' '.join(f'{c}({m})' for m, c in sorted(ex[k], reverse=True)[:7]))
both = sorted([(codes[u], u) for u in codes if cls.get(u) and cls[u]['old'] and cls[u]['sym']], reverse=True)[:8]
print('두 종류 모두:', [(f'{u:04X}', n, dict(cls[u])) for n, u in both])
