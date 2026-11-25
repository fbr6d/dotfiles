# 다시 볼 견본(REV_Bnn)의 칸마다 읽은 값과 고른 까닭을 찍는다.  쓰기: /usr/bin/python3 show_rev.py <REV 견본 이름> [시작 끝]
import sys, json, os
O = os.path.expanduser('~/.local/share/backups/ksat-admin-skill-ops-20261125/ops24')
name = sys.argv[1]
a, b = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (1, 999)
cj = json.load(open(os.path.join(O, os.environ.get('REVDIR', 'review'), name + '.cells.json')))
for no in sorted(cj, key=int):
    if not (a <= int(no) <= b):
        continue
    r = cj[no].get('rev') or {}
    t = r.get('text', '')
    cps = ' '.join('%04X' % ord(c) for c in t)
    fl = '; '.join(f[:44] for f in r.get('flags', []))
    print('%2s %-13s %-4s [%s] %s/%s/%s | %s | %s' % (no, r.get('sheet', '') + '#' + r.get('no', ''), t, cps, r.get('pos'), r.get('role'), r.get('status'), fl, (r.get('desc') or '')[:46]))
