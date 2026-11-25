# 시험: 견본 칸에 적힌 PDF·쪽으로 도구를 돌려 본다
import json, os, subprocess, sys
O = os.path.expanduser('~/.local/share/backups/ksat-admin-skill-ops-20261125/ops24')
RAW = '/home/leejaeik/Projects/ksat-10000/raw/'
TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proj/tools/pdf_glyph_text.py')
sheet, no = sys.argv[1], sys.argv[2]
cj = json.load(open(os.path.join(O, 'sheets', sheet + '.cells.json')))[no]
pdf, page = RAW + cj['pdf'], cj['page']
print('PDF:', cj['pdf'], '쪽', page, '| 칸의 열쇠', cj['keys'][:3])
ev = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ev_test')
r = subprocess.run(['/usr/bin/python3', TOOL, pdf, '--pages', str(page), '--out', '/dev/stdout', '--report', os.path.join(ev + '_report.md'), '--evidence', ev], capture_output=True, text=True)
out = r.stdout.split('\n')
print('\n'.join(l[:150] for l in out[:int(sys.argv[3]) if len(sys.argv) > 3 else 40]))
print('--- 오류 출력:', r.stderr[-600:])
print(open(ev + '_report.md').read()[:1800])
