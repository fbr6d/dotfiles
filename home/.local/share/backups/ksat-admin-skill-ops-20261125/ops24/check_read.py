# 읽기 결과 파일이 형식에 맞는지 확인한다.  쓰기: /usr/bin/python3 check_read.py <견본 이름> [<견본 이름> …]
import sys, os, json
BASE = os.path.dirname(os.path.abspath(__file__))
SH = os.path.join(BASE, 'sheets'); RD = os.path.join(BASE, 'read')
man = {m['sheet']: m for m in json.load(open(os.path.join(SH, 'manifest.json')))}
ST = {'확정', '근사', '미확정'}; POS = {'base', 'sup', 'sub'}; ROLE = {'char', 'bar', 'radical', 'piece', 'accent', 'deco', 'space'}
bad = 0
for name in sys.argv[1:]:
    name = name.replace('.png', '').replace('.json', '')
    if name not in man:
        print(name, ': 그런 견본이 없어요'); bad += 1; continue
    fn = os.path.join(RD, name + '.json')
    if not os.path.exists(fn):
        print(name, ': 읽기 파일이 없어요 →', fn); bad += 1; continue
    try:
        d = json.load(open(fn))
    except Exception as e:
        print(name, ': JSON 오류', e); bad += 1; continue
    cells = d.get('cells', {})
    n = man[name]['cells']; t = man[name]['type']
    errs = []
    miss = [str(i) for i in range(1, n + 1) if str(i) not in cells]
    extra = [k for k in cells if not k.isdigit() or not (1 <= int(k) <= n)]
    if miss: errs.append('빠진 칸 ' + ','.join(miss[:20]))
    if extra: errs.append('없는 칸 번호 ' + ','.join(extra[:20]))
    nun = 0
    for k, c in cells.items():
        if not isinstance(c, dict):
            errs.append(f'{k}번: 값이 객체가 아님'); continue
        if t in ('B', 'C'):
            if not isinstance(c.get('same'), bool):
                errs.append(f'{k}번: same 이 true/false 가 아님'); continue
            if c['same'] and t == 'B':
                if c.get('pos', 'base') not in POS: errs.append(f'{k}번: pos 값')
                continue
            if c['same']:
                continue
            if t == 'C':
                if not c.get('desc'): errs.append(f'{k}번: 다르다고 했는데 desc 가 없음')
                continue
        st = c.get('status')
        if st not in ST: errs.append(f'{k}번: status 값 {st!r}'); continue
        if st == '미확정': nun += 1
        if c.get('pos', 'base') not in POS: errs.append(f'{k}번: pos 값 {c.get("pos")!r}')
        if c.get('role', 'char') not in ROLE: errs.append(f'{k}번: role 값 {c.get("role")!r}')
        if not isinstance(c.get('text'), str): errs.append(f'{k}번: text 가 글이 아님')
        elif st != '미확정' and c['text'] == '' and c.get('role', 'char') not in ('space',): errs.append(f'{k}번: text 가 비었는데 미확정이 아님')
        if (st != '확정' or c.get('role', 'char') != 'char') and not c.get('desc'): errs.append(f'{k}번: desc 가 필요함')
    if errs:
        bad += 1
        print(name, f'({t}, {n}칸): 문제 {len(errs)}건 →', ' / '.join(errs[:12]))
    else:
        print(name, f'({t}, {n}칸): 형식 맞음' + (f', 미확정 {nun}칸' if nun else ''))
sys.exit(1 if bad else 0)
