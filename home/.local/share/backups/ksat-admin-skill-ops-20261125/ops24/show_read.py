# 읽기 결과 한 장을 한 줄씩 찍는다.  쓰기: /usr/bin/python3 show_read.py <견본 이름> …
import sys, json, os
O = os.path.dirname(os.path.abspath(__file__))
for name in sys.argv[1:]:
    fn = os.path.join(O, 'read', name + '.json')
    if not os.path.exists(fn):
        print(name, ': 아직 없음'); continue
    d = json.load(open(fn))['cells']
    out = []
    for k in sorted(d, key=int):
        c = d[k]
        if 'same' in c and c['same'] is True:
            out.append('%s:=%s' % (k, '' if c.get('pos', 'base') == 'base' else c['pos']))
        elif 'same' in c and 'text' not in c:
            out.append('%s:≠(%s)' % (k, c.get('desc', '')[:16]))
        else:
            out.append('%s:%s%s%s%s' % (k, c.get('text', ''), '' if c.get('pos', 'base') == 'base' else '^' if c['pos'] == 'sup' else '_', '' if c.get('role', 'char') == 'char' else '[' + c['role'] + ']', '' if c.get('status') == '확정' else '(' + str(c.get('status')) + ')'))
    print(name, '|', '  '.join(out))
