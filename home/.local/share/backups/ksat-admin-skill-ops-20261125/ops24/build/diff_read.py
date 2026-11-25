# 두 사람의 읽기 결과를 칸마다 견준다(AI 없음).
# 쓰기: /usr/bin/python3 diff_read.py <읽기 폴더 가> <읽기 폴더 나> [<결과.json>]
#   견본 칸 목록은 이 파일 옆 sheets/ 에서 읽는다. 같은 견본이 두 폴더에 다 있을 때만 견준다.
import sys, os, json, collections, unicodedata
BASE = os.path.dirname(os.path.abspath(__file__))
SH = os.path.join(BASE, 'sheets')
A, B = sys.argv[1], sys.argv[2]
man = json.load(open(os.path.join(SH, 'manifest.json')))
CANON = {'\u00b5': '\u03bc', '\u2206': '\u0394', '\u2126': '\u03a9', '\u2215': '/', '\u2010': '-', '\u2011': '-', '\u2044': '/', '\u02b9': '\u2032', '\u02ba': '\u2033', '\u2014': '\u2015', '\u2500': '\u2015', '\u23af': '\u2015'}


def eff(t, r, ci):
    """읽기 한 칸 → (글, 자리, 상태 갈래)"""
    if r is None:
        return None
    if t in ('B', 'C') and r.get('same') is True:
        return (ci.get('cand', ''), r.get('pos', 'base') if t == 'B' else 'base', '정함')
    if t == 'C':
        return ('', 'base', '다름')
    st = r.get('status')
    if st == '미확정':
        return ('', 'base', '미확정')
    text = ''.join(CANON.get(c, c) for c in r.get('text', ''))
    return (text, r.get('pos', 'base'), '정함')


stat = collections.Counter(); out = []
for m in man:
    fa, fb = os.path.join(A, m['sheet'] + '.json'), os.path.join(B, m['sheet'] + '.json')
    if not (os.path.exists(fa) and os.path.exists(fb)):
        stat['한쪽만 있는 견본'] += 1; continue
    ra, rb = json.load(open(fa)).get('cells', {}), json.load(open(fb)).get('cells', {})
    cj = json.load(open(os.path.join(SH, m['sheet'] + '.cells.json')))
    for no, ci in cj.items():
        ea, eb = eff(m['type'], ra.get(no), ci), eff(m['type'], rb.get(no), ci)
        stat['칸'] += 1
        if ea is None or eb is None:
            stat['한쪽이 빈 칸'] += 1; kind = '한쪽 없음'
        elif ea == eb:
            stat['같음'] += 1; continue
        elif ea[0] == eb[0] and ea[2] == eb[2]:
            stat['글자는 같고 자리(위·아래 첨자)만 다름'] += 1; kind = '자리'
        elif '미확정' in (ea[2], eb[2]) or '다름' in (ea[2], eb[2]):
            stat['한쪽만 정함'] += 1; kind = '한쪽만 정함'
        else:
            stat['글자가 다름'] += 1; kind = '글자'
        out.append({'sheet': m['sheet'], 'no': no, 'kind': kind, 'a': ea, 'b': eb, 'n': ci.get('n'), 'keys': ci.get('keys', [])[:3]})
print({k: v for k, v in stat.items()})
out.sort(key=lambda d: -(d.get('n') or 0))
for d in out[:60]:
    print('  %s#%s [%s] 가=%s 나=%s (글자 수 %s)' % (d['sheet'], d['no'], d['kind'], d['a'], d['b'], d['n']))
if len(sys.argv) > 3:
    json.dump({'stat': dict(stat), 'diff': out}, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
