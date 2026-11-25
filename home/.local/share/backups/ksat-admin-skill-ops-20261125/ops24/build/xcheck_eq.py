# HyhwpEQ 읽기 결과를, 검토 때 따로 만든 시험용 대응(규칙적 배치)과 견준다
import json, os, sys, collections
O = os.path.expanduser('~/.local/share/backups/ksat-admin-skill-ops-20261125/ops24')
exp = {}
for i in range(26): exp[0xE000 + i] = chr(65 + i)
for i in range(9): exp[0xE034 + i] = chr(49 + i)
exp[0xE03D] = '0'
for i in range(26): exp[0xE0E5 + i] = chr(97 + i)
exp.update({0xE06D: '−', 0xE045: ')', 0xE044: '(', 0xE047: '=', 0xE048: '+', 0xE05C: '√', 0xE052: ',', 0xE053: '.', 0xE0AC: 'π', 0xE06E: '→', 0xE0A4: 'θ', 0xE055: '<', 0xE056: '>',
            0xE04B: '{', 0xE04C: '}', 0xE067: 'Σ', 0xE05B: '∫', 0xE09D: 'α', 0xE04F: ':', 0xE049: '[', 0xE0AE: 'σ', 0xE09E: 'β', 0xE04A: ']'})
EQ = {'Σ': '∑', '−': '-'}
man = json.load(open(os.path.join(O, 'sheets', 'manifest.json')))
agree = 0; dis = []; n = 0
for m in man:
    if m['group'] != 'HyhwpEQ': continue
    rf = os.path.join(O, 'read', m['sheet'] + '.json')
    if not os.path.exists(rf): continue
    cj = json.load(open(os.path.join(O, 'sheets', m['sheet'] + '.cells.json')))
    rd = json.load(open(rf))['cells']
    for no, ci in cj.items():
        r = rd.get(no)
        if not r: continue
        us = {int(k[1], 16) for k in ci['keys'] if k[0] == 'HyhwpEQ'}
        e = {exp[u] for u in us if u in exp}
        if len(e) != 1: continue
        e = e.pop(); n += 1
        t = ci.get('cand') if r.get('same') is True else r.get('text', '')
        if t == e or EQ.get(e) == t or EQ.get(t) == e:
            agree += 1
        else:
            dis.append((m['sheet'], no, sorted('%04X' % u for u in us)[:2], '예상 ' + e, '읽기 ' + repr(t), r.get('pos', ''), r.get('status', ''), (r.get('desc') or '')[:40]))
print('견준 칸', n, '같음', agree, '다름', len(dis))
for d in dis[:40]: print('  ', d)
