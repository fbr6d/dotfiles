p = 'proj/tools/pdf_glyph_text.py'
s = open(p).read()

old = """    for sp in page.get_texttrace():
        fname = sp['font']
        xr = tuple(n2x.get(fname, ()))
        cn = gc.clean_name(fname)
        for (ucs, gid, org, bbox) in sp['chars']:
            trace[(round(org[0], 1), round(org[1], 1))].append((ucs, gid, cn, xr, sp['size']))
"""
new = """    for sp in page.get_texttrace():
        fname = sp['font']
        xr = tuple(n2x.get(fname, ()))
        cn = gc.clean_name(fname)
        d = sp.get('dir') or (1.0, 0.0)
        up = abs(d[0] - 1.0) < 1e-3 and abs(d[1]) < 1e-3
        for (ucs, gid, org, bbox) in sp['chars']:
            trace[(round(org[0], 1), round(org[1], 1))].append((ucs, gid, cn, xr, sp['size'], up))
"""
assert old in s; s = s.replace(old, new)

old = """            buf = []
            info = []
            for sp in ln.get('spans', []):
"""
new = """            buf = []
            info = []
            recs = []
            for sp in ln.get('spans', []):
"""
assert old in s; s = s.replace(old, new)

old = """                        ucs, gid, size = u, None, sp.get('size')
                    else:
                        ucs, gid, cn, xr, size = hit
                        res = conv.char(dg, cn, ucs, gid, xr)
                    text, status, pos, role, eid, how = res
"""
new = """                        ucs, gid, size, up, xr = u, None, sp.get('size'), False, ()
                    else:
                        ucs, gid, cn, xr, size, up = hit
                        res = conv.char(dg, cn, ucs, gid, xr)
                    text, status, pos, role, eid, how = res
                    cen = None
                    if pos != 'base' and gid is not None and xr:
                        hh = dg.span_hash(xr, gid)
                        if hh not in NOSHAPE:
                            shp = dg.shapes[hh]
                            cen = (shp[1] + shp[3] / 2.0) / gc.S       # 글리프 잉크의 가운데(기준선에서 아래로 +, em)
                    recs.append((o[1], size or 0, cen, up, role == 'char' and status in ('그대로', '확정')))
"""
assert old in s; s = s.replace(old, new)

old = """            if not buf:
                continue
            lines.append({'bbox': [round(v, 1) for v in ln['bbox']], 'text': _join(buf), 'chars': info})
"""
new = """            if not buf:
                continue
            _fix_pos(buf, info, recs)
            lines.append({'bbox': [round(v, 1) for v in ln['bbox']], 'text': _join(buf), 'chars': info})
"""
assert old in s; s = s.replace(old, new)

old = """def _join(buf):
"""
new = """POS_CUT = 0.33          # 잉크 가운데가 기준선에서 본문 글자 크기의 이 비율보다 높으면 위첨자, 아니면 아래첨자
POS_DEBUG = None        # 시험용: 목록을 넣어 두면 (표의 자리, 높이 비율, 글자)를 모은다


def _fix_pos(buf, info, recs):
    \"\"\"첨자 꼴 글리프의 위·아래를 '실제로 놓인 자리'로 정한다.

    표의 자리(sup/sub)는 글리프가 작게 그려진 첨자 꼴이라는 표시다. 같은 글리프가 본문 식에서는 위첨자로,
    그림 속 표지에서는 내려 놓여 아래첨자로 쓰이기도 해서, 같은 줄의 본문 글자 기준선과 견줘 위·아래를 다시 정한다.
    같은 줄에 본문 글자가 없으면 표의 자리를 그대로 둔다.
    \"\"\"
    base = [(r[0], r[1]) for (t, p), r in zip(buf, recs) if p == 'base' and r[4] and r[3] and r[1] and t.strip()]
    if not base:
        return
    mx = max(sz for y, sz in base)
    ys = sorted(y for y, sz in base if sz >= 0.85 * mx)
    by = ys[len(ys) // 2]
    imap = {c['i']: c for c in info}
    for i, ((t, p), r) in enumerate(zip(buf, recs)):
        y, size, cen, up, isb = r
        if p == 'base' or cen is None or not up or not size:
            continue
        rel = (by - (y + cen * size)) / mx
        if POS_DEBUG is not None:
            POS_DEBUG.append((p, round(rel, 2), t))
        np_ = 'sup' if rel > POS_CUT else 'sub'
        if np_ != p:
            buf[i] = (t, np_)
            c = imap.get(i)
            if c is not None:
                c['pos'] = np_
                c['how'] = (c['how'] + ' · ' if c['how'] else '') + '놓인 자리로 위아래를 정함(표는 %s)' % p


def _join(buf):
"""
assert old in s; s = s.replace(old, new, 1)
open(p, 'w').write(s)
print('ok', 'S' in dir(__import__('importlib').import_module('glyphcore')))
