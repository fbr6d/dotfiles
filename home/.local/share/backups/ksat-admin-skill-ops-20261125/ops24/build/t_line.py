import sys, json, subprocess, os
TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proj/tools/pdf_glyph_text.py')
pdf, pages, pat = sys.argv[1], sys.argv[2], sys.argv[3]
r = subprocess.run(['/usr/bin/python3', TOOL, pdf, '--pages', pages, '--format', 'jsonl', '--report', '/dev/null'], capture_output=True, text=True)
n = 0
for l in r.stdout.split('\n'):
    if not l: continue
    d = json.loads(l)
    if pat in d['text']:
        n += 1
        print(repr(d['text'][:80]))
        print('   ', [(c['i'], c['ucs'], c['text'], c['status'], c['how']) for c in d['chars']][:6])
        if n >= int(sys.argv[4]) if len(sys.argv) > 4 else 3: break
print(r.stderr[-300:])
