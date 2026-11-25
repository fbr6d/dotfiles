# -*- coding: utf-8 -*-
"""한 쪽에서 texttrace 글자와 rawdict 글자의 자리가 왜 안 맞는지 들여다본다(진단용).
쓰기: /usr/bin/python3 t_probe_match.py <목록.txt> <tools 폴더> <PDF 이름 일부> <쪽(1부터, 0=PUA 글자가 안 맞는 첫 쪽)> [보기 수=8]
"""
import sys, os, collections
sys.dont_write_bytecode = True
TOOLS = sys.argv[2]
sys.path.insert(0, TOOLS)
import numpy as np
import pymupdf
import pdf_glyph_text as pgt
import glyphcore as gc

path = next(p.strip() for p in open(sys.argv[1]) if sys.argv[3] in p)
want = int(sys.argv[4]); nshow = int(sys.argv[5]) if len(sys.argv) > 5 else 8
doc = pymupdf.open(path)
K = lambda p: (round(p[0], 1), round(p[1], 1))


def look(pno, show):
    page = doc[pno]
    T = []
    for sp in page.get_texttrace():
        cn = gc.clean_name(sp['font'])
        for (ucs, gid, org, bbox) in sp['chars']:
            T.append((ucs, org, cn, sp.get('dir'), sp.get('type'), round(sp['size'], 1), sp.get('seqno'), sp.get('wmode')))
    R = []
    rd = page.get_text('rawdict', flags=pgt.RAW_FLAGS)
    for b in rd.get('blocks', []):
        for ln in b.get('lines', []):
            for sp in ln.get('spans', []):
                for ch in sp.get('chars', []):
                    R.append((ch['c'], ch['origin'], sp.get('font', ''), ln.get('dir'), ln.get('wmode')))
    rk = collections.Counter(K(r[1]) for r in R)
    used = collections.Counter(); um = []
    for t in T:
        k = K(t[1]); used[k] += 1
        if used[k] > rk.get(k, 0):
            um.append(t)
    if not show:
        return any(0xE000 <= t[0] <= 0xF8FF for t in um)
    RA = np.array([r[1] for r in R], dtype=np.float64) if R else np.zeros((0, 2))
    hist = collections.Counter(); same = 0; rows = []
    byfont = collections.Counter(t[2] for t in um)
    for t in um:
        if len(RA):
            d = np.hypot(RA[:, 0] - t[1][0], RA[:, 1] - t[1][1]); j = int(d.argmin()); dist = float(d[j])
        else:
            j, dist = -1, 999.0
        b = '<0.06' if dist < 0.06 else '<0.15' if dist < 0.15 else '<0.5' if dist < 0.5 else '<2' if dist < 2 else '>=2'
        hist[b] += 1
        eq = j >= 0 and ord(R[j][0]) == t[0]
        same += eq
        rows.append((t, R[j] if j >= 0 else None, dist, eq))
    print('== %s  %d쪽 · texttrace %d자 · rawdict %d자 · 자리가 안 맞는 texttrace 글자 %d자' % (os.path.basename(path)[:50], pno + 1, len(T), len(R), len(um)))
    print('   가장 가까운 rawdict 글자까지 거리:', dict(hist), '· 그 글자와 코드가 같은 것', same)
    print('   안 맞는 글자의 글꼴:', byfont.most_common(6))
    print('   wmode·dir:', collections.Counter((t[7], tuple(round(v, 2) for v in (t[3] or ()))) for t in um).most_common(4))
    pri = sorted(rows, key=lambda r: (not (0xE000 <= r[0][0] <= 0xF8FF), -r[2]))
    for (t, r, dist, eq) in pri[:show]:
        print('   U+%04X %s (%.2f, %.2f) %s 크기 %s type %s  →  가까운 rawdict: %s (%.2f, %.2f) 거리 %.3f%s' % (
            t[0], repr(chr(t[0]))[:6], t[1][0], t[1][1], t[2][:18], t[5], t[4],
            ('U+%04X %s' % (ord(r[0]), repr(r[0])[:6])) if r else '-', r[1][0] if r else 0, r[1][1] if r else 0, dist, ' · 코드 같음' if eq else ''))
    return True


if want:
    look(want - 1, nshow)
else:
    n = 0
    for pno in range(doc.page_count):
        if look(pno, 0):
            look(pno, nshow); n += 1
            if n >= 2:
                break
    if not n:
        print('PUA 글자가 안 맞는 쪽이 없어요:', os.path.basename(path))
