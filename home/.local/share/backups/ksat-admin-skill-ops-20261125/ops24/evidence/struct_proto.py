"""수식 구조 복원 시험(읽기 전용): 가는 가로선 + 글자 좌표로 분수·근호·위아래 첨자를 묶어 한 줄 수식으로 적는다."""
import collections, re, statistics, sys
import pymupdf
EQ = {}
for i in range(26): EQ[0xE000 + i] = chr(65 + i)
for i in range(9): EQ[0xE034 + i] = str(i + 1)
EQ[0xE03D] = '0'
for i in range(26): EQ[0xE0E5 + i] = chr(97 + i)
EQ.update({0xE06D: '-', 0xE045: ')', 0xE044: '(', 0xE047: '=', 0xE048: '+', 0xE046: '—', 0xE05C: '√', 0xE052: ',', 0xE053: '.', 0xE101: '|', 0xE0AC: 'π', 0xE06E: '→',
           0xE0A4: 'θ', 0xE055: '<', 0xE056: '>', 0xE04B: '{', 0xE04C: '}', 0xE067: 'Σ', 0xE07B: '|', 0xE05B: '∫', 0xE09D: 'α', 0xE04F: ':', 0xE049: '[', 0xE0AE: 'σ', 0xE09E: 'β', 0xE04A: ']'})
class N:
    __slots__ = ('x0', 'x1', 'yb', 'size', 'tex', 'top', 'bot', 'used', 'math')
    def __init__(s, x0, x1, yb, size, tex, top, bot, math=True):
        s.x0, s.x1, s.yb, s.size, s.tex, s.top, s.bot, s.used, s.math = x0, x1, yb, size, tex, top, bot, False, math
def lin(nodes):
    """같은 줄의 마디를 왼쪽부터 읽으며 위·아래 첨자를 붙인다"""
    nodes = sorted(nodes, key=lambda n: n.x0)
    out = []; base = None; mode = None; buf = []
    def flush():
        nonlocal buf, mode
        if buf:
            out.append(('^' if mode == 'sup' else '_') + '{' + ''.join(buf) + '}')
        buf = []; mode = None
    for n in nodes:
        m = None
        if base is not None and n.size <= base.size * 0.86:
            if n.yb < base.yb - 0.22 * base.size: m = 'sup'
            elif n.yb > base.yb + 0.08 * base.size: m = 'sub'
        if m is None:
            flush(); out.append(n.tex); base = n
        else:
            if mode != m: flush(); mode = m
            buf.append(n.tex)
    flush()
    return ''.join(out)
def lines_of(nodes):
    """기준선이 비슷한 마디끼리 줄로 묶기(첨자는 가까운 큰 글자 줄에 붙음)"""
    big = sorted(nodes, key=lambda n: (n.yb, n.x0)); rows = []
    for n in big:
        for r in rows:
            if abs(r[0] - n.yb) < 0.62 * max(n.size, r[1]) and (n.size <= r[1] * 0.86 or abs(r[0] - n.yb) < 0.2 * r[1]):
                r[2].append(n); break
        else:
            rows.append([n.yb, n.size, [n]])
    return rows
def run(path, pno, mathpat, table=None, verbose=True):
    doc = pymupdf.open(path); page = doc[pno]
    nodes = []
    for sp in page.get_texttrace():
        f = sp['font']; ismath = bool(mathpat.search(f))
        for ucs, gid, org, bbox in sp['chars']:
            if ucs in (32, 0xA0): continue
            t = (table or {}).get(ucs) if ismath else None
            t = t if t is not None else (chr(ucs) if not (0xE000 <= ucs <= 0xF8FF) else f'⟨{ucs:04X}⟩')
            nodes.append(N(bbox[0], bbox[2], org[1], sp['size'], t, bbox[1], bbox[3], ismath))
    bars = []
    for d in page.get_drawings():
        for it in d['items']:
            if it[0] == 'l':
                p, q = it[1], it[2]
                if abs(p.y - q.y) < 0.35 and 2.5 < abs(p.x - q.x) < 260 and (d.get('width') or 1) < 1.2:
                    bars.append((min(p.x, q.x), max(p.x, q.x), (p.y + q.y) / 2))
            elif it[0] == 're':
                r = it[1]
                if r.height < 0.9 and 2.5 < r.width < 260: bars.append((r.x0, r.x1, (r.y0 + r.y1) / 2))
    bars = sorted(set((round(a, 1), round(b, 1), round(c, 1)) for a, b, c in bars), key=lambda b: b[1] - b[0])
    stat = collections.Counter(); made = []
    for bx0, bx1, by in bars:
        cand = [n for n in nodes if not n.used and n.x0 >= bx0 - 1.2 and n.x1 <= bx1 + 1.2]
        if not cand:
            stat['글자 없는 선(표·밑줄 등)'] += 1; continue
        s = statistics.median(n.size for n in cand)
        up = [n for n in cand if by - 1.9 * s < n.yb <= by - 0.12 * s and n.bot <= by + 0.25 * s]
        dn = [n for n in cand if by + 0.45 * s < n.yb < by + 1.75 * s and n.top >= by - 0.3 * s]
        under = [n for n in cand if by < n.yb <= by + 1.2 * s and n.top >= by - 0.15 * s]
        mathy = lambda L: any(n.math for n in L)
        if up and dn and (mathy(up) or mathy(dn)):
            node = N(bx0, bx1, by + 0.28 * s, s, '\\frac{' + lin(up) + '}{' + lin(dn) + '}', min(n.top for n in up), max(n.bot for n in dn))
            for n in up + dn: n.used = True
            nodes.append(node); made.append(node); stat['분수'] += 1
        elif under and mathy(under):
            rad = [n for n in nodes if not n.used and n.tex == '√' and bx0 - 1.3 * s < n.x1 <= bx0 + 0.6 * s and abs(n.yb - under[0].yb) < 1.0 * s]
            if rad:
                node = N(rad[0].x0, bx1, under[0].yb, max(n.size for n in under), '\\sqrt{' + lin(under) + '}', by, max(n.bot for n in under))
                for n in under + rad: n.used = True
                nodes.append(node); made.append(node); stat['근호'] += 1
            else:
                node = N(bx0, bx1, under[0].yb, max(n.size for n in under), '\\overline{' + lin(under) + '}', by, max(n.bot for n in under))
                for n in under: n.used = True
                nodes.append(node); made.append(node); stat['윗줄(선분·평균 등)'] += 1
        else:
            stat['수식 아닌 선(밑줄 등)' if not (mathy(up) or mathy(dn) or mathy(under)) else '못 묶은 선'] += 1
    left = [n for n in nodes if not n.used]
    rows = lines_of(left)
    outl = []
    for yb, size, ns in sorted(rows, key=lambda r: (round(r[0] / 6), min(n.x0 for n in r[2]))):
        if any(n.math for n in ns): outl.append((yb, min(n.x0 for n in ns), lin(ns)))
    stat['√ 글리프(선과 못 묶임)'] = sum(1 for n in left if n.tex == '√')
    stat['위·아래 첨자 묶음'] = sum(l[2].count('^{') + l[2].count('_{') for l in outl)
    stat['모르는 PUA'] = sum(l[2].count('⟨') for l in outl)
    return outl, stat, len(bars)
if __name__ == '__main__':
    path = sys.argv[1]; mathpat = re.compile(sys.argv[2]); pages = [int(x) for x in sys.argv[3].split(',')]
    use = EQ if 'Hyhwp' in sys.argv[2] else None
    tot = collections.Counter()
    for pno in pages:
        outl, stat, nb = run(path, pno, mathpat, use)
        tot.update(stat)
        if len(sys.argv) > 4:
            print(f'--- {pno + 1}쪽: 가는 가로선 {nb}개 {dict(stat)}')
            for yb, x0, s in outl[:int(sys.argv[4])]: print(f'   y{yb:6.1f} x{x0:6.1f} | {s[:150]}')
    print('합계', dict(tot))
