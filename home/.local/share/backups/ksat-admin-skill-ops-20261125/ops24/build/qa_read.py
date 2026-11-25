# -*- coding: utf-8 -*-
"""읽기 결과를 기계로 훑어 다시 볼 칸을 고른다(AI 없음).

쓰기: venv/bin/python qa_read.py <cells.pkl> <ops 폴더> <review.pkl>
고르는 것: ① 읽은 글자와 모양 비교 점수가 크게 어긋나는 칸 ② 위·아래 첨자 판정이 글리프 높이와 안 맞는 칸
          ③ 같은 글꼴 가족·같은 코드인데 읽은 글자가 서로 다른 칸 ④ 무작위 표본(나머지의 4%)
"""
import sys, os, json, pickle, re, random, collections
import glyphcore as gc
import mk_cells as mc

random.seed(20261125)
cells_pkl, ops, outp = sys.argv[1], sys.argv[2], sys.argv[3]
D = pickle.load(open(cells_pkl, 'rb'))
shapes = D['shapes']; cells = {c['id']: c for c in D['cells']}
man = json.load(open(os.path.join(ops, 'sheets', 'manifest.json')))
rows = []
missing = []
for m in man:
    rf = os.path.join(ops, 'read', m['sheet'] + '.json')
    if not os.path.exists(rf):
        missing.append(m['sheet']); continue
    cj = json.load(open(os.path.join(ops, 'sheets', m['sheet'] + '.cells.json')))
    rd = json.load(open(rf)).get('cells', {})
    for no, ci in cj.items():
        r = rd.get(no)
        if r is None:
            continue
        c = cells[ci['cell']]
        if m['type'] in ('B', 'C') and r.get('same') is True:
            text, status, pos, role = ci['cand'], '확정', r.get('pos', 'base'), 'char'
        elif m['type'] == 'C':
            text, status, pos, role = '', '미확정', 'base', 'char'
        else:
            text, status, pos, role = r.get('text', ''), r.get('status', '미확정'), r.get('pos', 'base'), r.get('role', 'char')
        rows.append({'sheet': m['sheet'], 'no': no, 'type': m['type'], 'group': m['group'], 'cell': c, 'text': text, 'status': status, 'pos': pos, 'role': role, 'desc': r.get('desc', ''), 'same': r.get('same')})
print('읽은 칸', len(rows), '· 읽기 없는 견본', len(missing), missing[:8])
st = collections.Counter((r['group'], r['status']) for r in rows)
print('상태:', {('%s/%s' % k): v for k, v in sorted(st.items())})
flags = collections.defaultdict(list)
STYLE = re.compile(r'-?(Plain|Italic|BoldItalic|Bold|Regular|NormalBold|ItalicBold|Normal)$')
grp = collections.defaultdict(list)
for r in rows:
    c = r['cell']; sh = shapes[c['id']]
    if r['type'] != 'C' and r['status'] != '미확정' and r['role'] == 'char':
        ybot = (sh[1] + sh[3]) / gc.S; ytop = sh[1] / gc.S; hgt = sh[3] / gc.S
        alnum = len(r['text']) == 1 and r['text'].isalnum()
        if r['pos'] == 'sup' and ybot > -0.10:
            flags[(r['sheet'], r['no'])].append('위첨자라는데 기준선에 닿음')
        if r['pos'] == 'sub' and ybot < -0.05 and ytop < -0.45:
            flags[(r['sheet'], r['no'])].append('아래첨자라는데 높이 있음')
        if r['pos'] == 'base' and alnum and ybot < -0.22 and hgt < 0.6:
            flags[(r['sheet'], r['no'])].append('보통 자리라는데 떠 있음(위첨자?)')
        if r['pos'] == 'base' and alnum and r['text'].isdigit() and ybot > 0.10:
            flags[(r['sheet'], r['no'])].append('보통 자리라는데 숫자가 기준선 아래로 내려감(아래첨자?)')
    if r['type'] == 'A' and r['group'] not in ('SYM',) and r['status'] == '확정' and len(r['text']) == 1 and r['role'] == 'char':
        best = mc.mech(sh)
        if best and r['text'] in best:
            top = next(iter(best.items()))
            if best[r['text']] < 0.40 and top[1] >= 0.72:
                flags[(r['sheet'], r['no'])].append('모양 점수 낮음 %.2f (가장 닮은 것 %s %.2f)' % (best[r['text']], top[0], top[1]))
    if r['type'] in ('A', 'B') and r['group'] not in ('SYM',):
        for (cn, u), n in c['keys'].items():
            if u != 0xFFFD:
                grp[(r['group'], STYLE.sub('', re.sub(r'-(KSC|Identity).*$', '', cn)), u)].append(r)
for k, lst in grp.items():
    ts = {(x['text'], x['pos']) for x in lst if x['status'] != '미확정'}
    ids = {x['cell']['id'] for x in lst}
    if len(ts) > 1 and len(ids) > 1:
        for x in lst:
            flags[(x['sheet'], x['no'])].append('같은 글꼴 가족·코드 U+%04X 인데 읽기가 갈림: %s' % (k[2], ' / '.join(sorted('%s%s' % (t, '' if p == 'base' else '(' + p + ')') for t, p in ts))[:60]))
byk = {(r['sheet'], r['no']): r for r in rows}
rest = [k for k, r in byk.items() if k not in flags and r['type'] == 'A' and r['status'] != '미확정']
samp = random.sample(rest, max(1, len(rest) // 25)) if rest else []
for k in samp:
    flags[k].append('무작위 표본')
print('다시 볼 칸', len(flags), '(무작위', len(samp), ')')
kinds = collections.Counter(f.split(' ')[0] + ' ' + f.split(' ')[1] if ' ' in f else f for fl in flags.values() for f in fl)
print(kinds.most_common(12))
out = []
for k, fl in sorted(flags.items()):
    r = byk[k]
    c = dict(r['cell'])
    c['sheet'] = 'B'; c['fam'] = 'REV'; c['inscope'] = True
    t = r['text'] if r['status'] != '미확정' else '?'
    c['cand_text'] = t + ('' if r['pos'] == 'base' else ('↑' if r['pos'] == 'sup' else '↓'))
    c['rev'] = {'sheet': r['sheet'], 'no': r['no'], 'text': r['text'], 'pos': r['pos'], 'role': r['role'], 'status': r['status'], 'desc': r['desc'], 'flags': fl}
    out.append(c)
pickle.dump({'paths': D['paths'], 'cells': out, 'shapes': shapes}, open(outp, 'wb'))
json.dump([{'sheet': c['rev']['sheet'], 'no': c['rev']['no'], 'text': c['rev']['text'], 'pos': c['rev']['pos'], 'status': c['rev']['status'], 'flags': c['rev']['flags'], 'desc': c['rev']['desc']} for c in out],
          open(os.path.join(ops, 'review_flags.json'), 'w'), ensure_ascii=False, indent=0)
nb = [(r['sheet'], r['no'], r['cell']['label'], r['text'], r['pos']) for r in rows if r['type'] == 'B' and r['same'] is False]
print('B형에서 후보와 다르다고 본 칸', len(nb), [(a, b, chr(l), t) for a, b, l, t, p in nb[:25]])
nc = [(r['sheet'], r['no'], r['desc'][:30]) for r in rows if r['type'] == 'C' and r['same'] is False]
print('C형에서 후보와 다르다고 본 칸', len(nc), nc[:25])
