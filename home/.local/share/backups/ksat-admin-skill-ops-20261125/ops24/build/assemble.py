# -*- coding: utf-8 -*-
"""칸 목록(cells.pkl) + 견본 칸 목록(sheets/*.cells.json) + 읽기 결과(read/*.json) → 대응표 tools/glyph/tbl_*.json

쓰기: /usr/bin/python3 assemble.py <cells.pkl> <ops 폴더(sheets/, read/ 가 든 곳)> <glyph 폴더> [--provisional]
--provisional: 읽기 결과가 아직 없는 견본을 시험용으로 채운다(A=미확정, B·C=같음). 실제 표에는 쓰지 않는다.
"""
import sys, os, json, pickle, base64, collections, datetime

FAM_RX = {'HyhwpEQ': r'^HyhwpEQ', 'HancomEQN': r'^HancomEQN', 'EH': r'^EH[A-Za-z]', 'Kab': r'^Kab', 'Amsusic': r'^Amsusic', 'ASusic': r'^ASusic',
          'GS': r'^GS(Medium|MediIta|Symbol)', 'TK': r'^TK(up|yak|down)'}
TITLE = {'HyhwpEQ': '한글(HWP) 수식 글꼴 HyhwpEQ — 평가원·교육청 기출', 'HancomEQN': '한컴 수식 글꼴 HancomEQN', 'EH': 'EH 계열 수식 글꼴 — EBS 교재·교과서',
         'Kab': 'KabMath 수식 글꼴 — 교과서', 'Amsusic': 'Amsusic 수식 글꼴 — 교과서', 'ASusic': 'ASusic 수식 글꼴 — 교과서', 'GS': 'GS 글꼴 — 과학탐구 시험지',
         'TK': 'TK 글꼴 — EBS 과학 교재', 'KO': '옛한글(한양 PUA) — 한컴·한양 계열 글꼴', 'SYM': '본문 글꼴의 PUA 기호'}
CANON = {'\u00b5': '\u03bc', '\u2206': '\u0394', '\u2126': '\u03a9', '\u2215': '/', '\u2010': '-', '\u2011': '-', '\u2044': '/', '\u02b9': '\u2032', '\u02ba': '\u2033'}
ST = {'확정', '근사', '미확정'}; POS = {'base', 'sup', 'sub'}; ROLE = {'char', 'bar', 'radical', 'piece', 'accent', 'deco', 'space'}
# 모양만으로는 가릴 수 없는 글자 묶음(I·l·1, O·0, 대소문자)과 사소한 꼴 차이(쌍점·대괄호·가운뎃점·빗금·별표).
# 이 묶음 안에서 읽은 글자와 글자층 코드가 다르면, 그 글꼴의 코드가 믿을 만할 때 글자층 코드를 따른다.
FOLLOW_SETS = ['Il1|\u2223', 'O0o', 'cC', 'sS', 'vV', 'wW', 'xX', 'zZ', 'uU', 'kK', 'pP', ':\u2236', '[\u3014', ']\u3015', '\u00b7\u22c5\u2219\u2022', '/\u2215\u2044', '*\u2217']
FOLLOW = {ch: i for i, st in enumerate(FOLLOW_SETS) for ch in st}
REL_MIN, REL_N = 0.6, 10          # 글꼴의 ASCII 코드 글리프 가운데 읽기가 코드와 같은 비율·개수의 하한


def canon(s):
    return ''.join(CANON.get(ch, ch) for ch in s)


def main():
    cells_pkl, ops, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    prov = '--provisional' in sys.argv
    D = pickle.load(open(cells_pkl, 'rb'))
    shapes = D['shapes']
    cells = {c['id']: c for c in D['cells']}
    man = json.load(open(os.path.join(ops, 'sheets', 'manifest.json')))
    tables = collections.defaultdict(list)
    stat = collections.Counter()
    problems = []
    fixes = {}
    ff = os.path.join(ops, 'fixes.json')
    if os.path.exists(ff):
        fixes = json.load(open(ff, encoding='utf-8'))
    used_fix = 0
    for m in man:
        name, t, g = m['sheet'], m['type'], m['group']
        g = {'KO3': 'KO', 'SYM3': 'SYM', 'SYM4': 'SYM'}.get(g, g[:-1] if g.endswith('3') and g[:-1] in FAM_RX else g)
        cj = json.load(open(os.path.join(ops, 'sheets', name + '.cells.json')))
        rf = os.path.join(ops, 'read', name + '.json')
        rd = None
        if os.path.exists(rf):
            try:
                rd = json.load(open(rf)).get('cells', {})
            except Exception as e:
                problems.append('%s: 읽기 파일 JSON 오류 %s' % (name, e))
        if rd is None:
            stat['읽기 없는 견본'] += 1
            if not prov:
                continue
            rd = {}
        for no, cinfo in cj.items():
            c = cells[cinfo['cell']]
            r = rd.get(no)
            src = t
            if r is None:
                if not prov:
                    problems.append('%s %s번: 읽기 없음' % (name, no)); continue
                r = {'text': '', 'status': '미확정', 'desc': '(시험용)'} if t == 'A' else {'same': True}
                src = t + ':시험용'
            e = {'id': c['id'], 'sheet': '%s#%s' % (name, no), 'src': src, 'n': c['n'], 'npdf': c['npdf']}
            fx = fixes.get('%s#%s' % (name, no))
            if fx is not None:
                r = dict(fx); r.pop('same', None)
                if r.pop('use_cand', False):
                    r.update(text=cinfo.get('cand', ''), status='확정'); r.setdefault('role', 'char')
                t_eff = 'A'; e['src'] = src + '+고침'; used_fix += 1
            else:
                t_eff = t
            if t_eff in ('B', 'C') and r.get('same') is True:
                e.update(text=cinfo['cand'], status='확정', pos=r.get('pos', 'base') if t == 'B' else 'base', role='char', desc=r.get('desc', ''))
            elif t_eff == 'C':
                e.update(text='', status='미확정', pos='base', role='char', desc='한양 표 후보(%s)와 다름: %s' % (cinfo['cand'], r.get('desc', '')))
            else:
                e.update(text=canon(r.get('text', '')), status=r.get('status', '미확정'), pos=r.get('pos', 'base'), role=r.get('role', 'char'), desc=r.get('desc', ''))
                if e['status'] == '미확정':
                    e['text'] = ''
            if e['status'] not in ST or e['pos'] not in POS or e['role'] not in ROLE:
                problems.append('%s %s번: 값 오류 %s/%s/%s' % (name, no, e['status'], e['pos'], e['role']))
                e.update(status='미확정', text='', pos='base', role='char')
            if e['status'] != '미확정' and e['text'] == '' and e['role'] != 'space':
                problems.append('%s %s번: 글이 비었음' % (name, no)); e['status'] = '미확정'
            e['shapes'] = [[shapes[h][0], shapes[h][1], shapes[h][2], shapes[h][3], base64.b64encode(shapes[h][4]).decode()] for h in c['hashes']]
            e['keys'] = [[k[0], '%04X' % k[1], v] for k, v in sorted(c['keys'].items(), key=lambda kv: -kv[1])]
            g2 = g
            if g == 'KO' and e['status'] != '미확정' and not any(
                    0x1100 <= ord(ch) <= 0x11FF or 0xA960 <= ord(ch) <= 0xA97F or 0xD7B0 <= ord(ch) <= 0xD7FF or 0xAC00 <= ord(ch) <= 0xD7A3 for ch in e['text']):
                g2 = 'SYM'          # 옛한글 후보였지만 눈으로 보니 기호인 칸은 기호 표로 보낸다
            tables[g2].append(e)
            stat[(g2, e['status'])] += 1
    rel = collections.defaultdict(lambda: [0, 0])
    for g, ents in tables.items():
        for e in ents:
            if e['status'] == '미확정':
                continue
            for cn, u, n in e['keys']:
                u = int(u, 16)
                if 0x21 <= u <= 0x7E:
                    rel[cn][1] += 1
                    if e['text'] == chr(u):
                        rel[cn][0] += 1
    nalt = altn = 0
    odd = []
    for g, ents in tables.items():
        if g in ('KO', 'SYM'):
            continue
        for e in ents:
            T = e['text']
            if e['status'] == '미확정' or len(T) != 1:
                continue
            alt = []
            for cn, u, n in e['keys']:
                K = chr(int(u, 16))
                a, b = rel[cn]
                if K == T or b < REL_N or a / b < REL_MIN:
                    continue
                if FOLLOW.get(K) is not None and FOLLOW.get(K) == FOLLOW.get(T):
                    alt.append([cn, u, K]); nalt += 1; altn += n
                elif 0x21 <= ord(K) <= 0x7E and 0x21 <= ord(T) <= 0x7E:
                    odd.append('%s %s: 읽기 %s ← 코드 %s (%s, %d자, 글꼴 일치 %d/%d)' % (g, e['sheet'], T, K, cn, n, a, b))
            if alt:
                e['alt'] = alt
    print('글자층 코드를 따르는 (항목, 글꼴·코드)', nalt, '쌍 ·', altn, '자')
    print('믿을 만한 글꼴인데 ASCII 읽기와 ASCII 코드가 다른 것(확인 거리)', len(odd))
    for o in odd[:40]:
        print('   ', o)
    os.makedirs(outdir, exist_ok=True)
    today = datetime.date.today().isoformat()
    for g, ents in sorted(tables.items()):
        ents.sort(key=lambda e: (e['keys'][0][0], e['keys'][0][1]))
        d = {'version': 1, 'family': g, 'title': TITLE.get(g, g), 'font': FAM_RX.get(g), 'made': today,
             'render': {'px_per_em': 48, 'threshold': 96, 'note': '기준 모양 = [x, y, 너비, 높이, 비트(base64)]. 기준선 원점, y는 아래로 +'},
             'provisional': prov, 'entries': ents}
        fn = os.path.join(outdir, 'tbl_%s.json' % g.lower())
        json.dump(d, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        st = collections.Counter(e['status'] for e in ents)
        print('%-10s 항목 %5d (확정 %d · 근사 %d · 미확정 %d)  글자 수 %d  → %s  %d KB' % (g, len(ents), st['확정'], st['근사'], st['미확정'], sum(e['n'] for e in ents), os.path.basename(fn), os.path.getsize(fn) // 1024))
    if 'KO' in tables:
        fc = collections.defaultdict(lambda: [0, 0, 0, 0])
        for e in tables['KO']:
            for cn, u, n in e['keys']:
                f = fc[cn]
                if e['status'] == '미확정':
                    f[2] += 1; f[3] += n
                else:
                    f[0] += 1; f[1] += n
        fl = [{'font': cn, 'verified_glyphs': v[0], 'verified_chars': v[1], 'unverified_glyphs': v[2], 'unverified_chars': v[3]} for cn, v in sorted(fc.items(), key=lambda kv: -kv[1][1])]
        json.dump({'version': 1, 'made': today,
                   'note': '옛한글(한양 PUA) 글리프가 실제로 확인된 글꼴 목록(근거 자료). 도구는 글꼴 이름이 아니라 글리프 모양으로 판정한다. verified = 한양 표 후보와 글리프 그림이 같은 글자임을 눈으로 확인한 것.',
                   'fonts': fl}, open(os.path.join(outdir, 'hanyang_fonts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('옛한글 글꼴 목록', len(fl), '종 → hanyang_fonts.json')
    print('읽기 없는 견본', stat['읽기 없는 견본'], '· 고친 값 적용', used_fix, '/', len(fixes), '· 문제', len(problems))
    for p in problems[:40]:
        print('   ', p)
    json.dump(problems, open(os.path.join(ops, 'assemble_problems.json'), 'w'), ensure_ascii=False, indent=0)


if __name__ == '__main__':
    main()
