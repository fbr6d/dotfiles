# 읽기 결과에서 견본#칸의 온전한 값을 찍는다.  쓰기: /usr/bin/python3 show_cell.py EH_A12#3 GS_A04#3 …
import sys, os, json
O = os.path.dirname(os.path.abspath(__file__))
for a in sys.argv[1:]:
    name, no = a.split('#')
    try:
        r = json.load(open(os.path.join(O, 'read', name + '.json')))['cells'].get(no)
    except Exception as e:
        r = '읽기 없음: %s' % e
    cj = json.load(open(os.path.join(O, 'sheets', name + '.cells.json'))).get(no, {})
    print(a, '| 읽기:', json.dumps(r, ensure_ascii=False))
    print('     후보:', repr(cj.get('cand')), '· 글자 수', cj.get('n'), '· keys', cj.get('keys', [])[:8])
