p = 'proj/tools/pdf_glyph_text.py'
s = open(p).read()

# 1) 기록에 x 좌표도 넣는다
old = "                    recs.append((o[1], size or 0, cen, up, role == 'char' and status in ('그대로', '확정')))\n"
new = "                    recs.append((o[0], o[1], size or 0, cen, up, role == 'char' and status in ('그대로', '확정')))\n"
assert old in s; s = s.replace(old, new)

# 2) 글자층 대조가 안 된 공백(뷰어가 낱말 사이에 끼워 넣은 것)은 그냥 공백으로 낸다
old = """                        if t is not None or is_pua(u) or u == 0xFFFD:
                            res = ('⟦U+%04X⟧' % u, '미확정', 'base', 'char', None, '글자층 대조 실패')
"""
new = """                        if u in SPACES:
                            res = (' ', '그대로', 'base', 'space', None, '')
                        elif t is not None or is_pua(u) or u == 0xFFFD:
                            res = ('⟦U+%04X⟧' % u, '미확정', 'base', 'char', None, '글자층 대조 실패')
"""
assert old in s; s = s.replace(old, new)

# 3) 자리 규칙을 '가까운 본문 글자의 기준선'으로 바꾼다
a = s.index('def _fix_pos(buf, info, recs):')
b = s.index('def _join(buf):')
new_fn = '''def _fix_pos(buf, info, recs):
    """첨자 꼴 글리프의 위·아래를 '실제로 놓인 자리'로 정한다.

    표의 자리(sup/sub)는 글리프 자체가 작게, 위나 아래로 치우쳐 그려진 첨자 꼴이라는 표시다.
    - 같은 기준선 위에 본문 글자가 가까이 있으면(보통의 식) 표의 자리를 그대로 쓴다.
    - 그런 글자가 없으면 글리프를 따로 올리거나 내려 놓은 것이다(그림 속 표지, 지수 자리의 분수, 적분의 위끝·아래끝 등).
      이때는 바로 왼쪽 본문 글자의 기준선과 견줘, 잉크 가운데가 그 글자 크기의 POS_CUT 배보다 높으면 위첨자, 아니면 아래첨자로 본다.
    - 견줄 본문 글자가 없으면 표의 자리를 그대로 둔다.
    """
    bases = [r for (t, p), r in zip(buf, recs) if p == 'base' and r[5] and r[4] and r[2] and t.strip()]
    if not bases:
        return
    imap = None
    for i, ((t, p), r) in enumerate(zip(buf, recs)):
        x, y, size, cen, up, isb = r
        if p == 'base' or cen is None or not up or not size:
            continue
        if any(abs(b[1] - y) < 0.12 * size and abs(b[0] - x) < 8 * max(size, b[2]) for b in bases):
            continue
        near = [b for b in bases if -0.1 * size <= x - b[0] <= 1.6 * b[2]]
        if not near:
            near = [b for b in bases if abs(x - b[0]) <= 3 * max(size, b[2])]
        if not near:
            continue
        b = min(near, key=lambda b: (abs(b[1] - y), -b[0]))
        rel = (b[1] - (y + cen * size)) / b[2]
        if POS_DEBUG is not None:
            POS_DEBUG.append((p, round(rel, 2), t))
        np_ = 'sup' if rel > POS_CUT else 'sub'
        if np_ != p:
            buf[i] = (t, np_)
            if imap is None:
                imap = {c['i']: c for c in info}
            c = imap.get(i)
            if c is not None:
                c['pos'] = np_
                c['how'] = (c['how'] + ' · ' if c['how'] else '') + '놓인 자리로 위아래를 정함(표는 %s)' % p


'''
s = s[:a] + new_fn + s[b:]
s = s.replace("POS_CUT = 0.33          # 잉크 가운데가 기준선에서 본문 글자 크기의 이 비율보다 높으면 위첨자, 아니면 아래첨자",
              "POS_CUT = 0.33          # 잉크 가운데가 견준 본문 글자의 기준선에서 그 글자 크기의 이 비율보다 높으면 위첨자, 아니면 아래첨자")
open(p, 'w').write(s)
print('ok')
