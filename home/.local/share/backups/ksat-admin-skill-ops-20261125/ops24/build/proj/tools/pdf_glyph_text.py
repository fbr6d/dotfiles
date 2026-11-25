#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""PDF 글자층을 '글리프 모양'으로 확인해서 표준 글자로 바꿔 내는 도구.

왜 필요한가
  PDF에서 뽑히는 글자 코드는 글꼴마다 뜻이 다르다. 같은 U+E287이 한컴 바탕에서는 옛한글이고
  윤고딕에서는 ○ 이다. 수식 글꼴에서는 θ가 'h'로, ≤가 '<'로 뽑힌다. 그래서 코드를 믿지 않고,
  글자마다 (글꼴 객체, 글리프 번호)로 글리프를 따로 그려 그 모양이 대응표(tools/glyph/tbl_*.json)의
  기준 모양과 같을 때만 표의 글자로 바꾼다.

쓰는 법 (/usr/bin/python3 로 실행. pymupdf·numpy·PIL 만 쓴다)
  /usr/bin/python3 tools/pdf_glyph_text.py <PDF> --pages 12-14 [--format text|jsonl] [--out 파일]
                                           [--report 파일] [--evidence 폴더]
  /usr/bin/python3 tools/pdf_glyph_text.py --selftest

결과에 붙는 상태
  확정    글리프 모양이 표의 기준 모양과 같고, 표가 정확한 유니코드 글자를 준 것
  근사    모양은 같지만 정확한 유니코드가 없어 풀어 쓴 표기(예: 네모 안 1 → [1])
  미확정  표에 없는 모양, 모양을 확인할 수 없는 글꼴, 표에서 아직 못 정한 글리프. ⟦U+E123⟧ 꼴로 남긴다
  그대로  보통 글꼴의 보통 글자(표를 거치지 않음)
옛한글은 유니코드 첫가끝 자모로 낸다. NFC·NFKC 정규화를 걸지 않는다(받침이 떨어져 깨진다).
"""
import argparse
import base64
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GLYPH_DIR = os.path.join(HERE, 'glyph')
if GLYPH_DIR not in sys.path:
    sys.path.insert(0, GLYPH_DIR)

import numpy as np          # noqa: E402
import pymupdf              # noqa: E402
import glyphcore as gc      # noqa: E402

pymupdf.TOOLS.mupdf_display_errors(False)
TOL = 0.97                      # 기준 모양과 '같다'고 보는 점수
SPACES = {0x20, 0xA0, 0x3000, 0x2002, 0x2003, 0x2009, 0x200A, 0x202F}
ZERO_WIDTH = {0x200B, 0xFEFF, 0x2060}
NOSHAPE = ('noembed', 'nolink', 'ambig', 'norender')
NOSHAPE_KO = {'noembed': '글꼴이 PDF에 안 들어 있음', 'nolink': '글꼴 객체를 못 이음(Type3 등)', 'ambig': '같은 이름의 글꼴이 여럿', 'norender': '글리프를 못 그림'}


def is_pua(u):
    return 0xE000 <= u <= 0xF8FF


class Tables:
    """tools/glyph/tbl_*.json 을 읽어 모양으로 찾을 수 있게 해 둔다."""

    def __init__(self, tdir=GLYPH_DIR):
        self.dir = tdir
        self.math = []          # (이름, 정규식, 표)
        self.pua = []           # 수식 글꼴이 아닌 글꼴의 PUA 용 표 (옛한글, 기호)
        self.version = {}
        self.hanyang = {}       # 한양 PUA 표(참고용): 코드 → 첫가끝 자모
        hp = os.path.join(tdir, 'hanyang_pua.json')
        if os.path.exists(hp):
            self.hanyang = {int(k, 16): v for k, v in json.load(open(hp, encoding='utf-8'))['map'].items()}
        for fn in sorted(os.listdir(tdir)):
            if not (fn.startswith('tbl_') and fn.endswith('.json')):
                continue
            d = json.load(open(os.path.join(tdir, fn), encoding='utf-8'))
            t = {'name': d['family'], 'by_hash': {}, 'by_key': collections.defaultdict(list), 'entries': d['entries'], 'by_ucs': collections.defaultdict(list)}
            for e in d['entries']:
                e['_shapes'] = []
                e['_fonts'] = {k[0] for k in e.get('keys', [])}
                for (x, y, w, h, b64) in e['shapes']:
                    sh = (x, y, w, h, base64.b64decode(b64))
                    e['_shapes'].append(sh)
                    t['by_hash'][gc.shape_hash(sh)] = e
                for k in e.get('keys', []):
                    t['by_key'][(k[0], int(k[1], 16))].append(e)
                    t['by_ucs'][int(k[1], 16)].append(e)
            self.version[d['family']] = d.get('version')
            if d.get('font'):
                self.math.append((d['family'], re.compile(d['font']), t))
            else:
                self.pua.append((d['family'], None, t))

    def family(self, cname):
        for nm, rx, t in self.math:
            if rx.search(cname):
                return nm, t
        return None, None


def _tol_find(shape, cands):
    """기준 모양 가운데 점수 TOL 이상인 항목이 하나뿐이면 그것을 돌려준다."""
    best = None
    hits = []
    for e in cands:
        s = max((gc.tol_score(shape, r) for r in e['_shapes']), default=0.0)
        if s >= TOL:
            hits.append((s, e))
    if not hits:
        return None
    ids = {id(e) for s, e in hits}
    if len(ids) > 1:
        texts = {(e['text'], e.get('pos', 'base'), e['status']) for s, e in hits}
        if len(texts) > 1:
            return None            # 닮은 기준이 여럿이고 뜻이 다르면 정하지 않는다
    hits.sort(key=lambda t: -t[0])
    return hits[0][1]


class Converter:
    def __init__(self, tables=None):
        self.tb = tables or Tables()
        self._memo = {}

    def char(self, dg, cname, ucs, gid, xrefs):
        """글자 하나 → (글, 상태, 자리, 구실, 항목 id, 방법)."""
        fam, t = self.tb.family(cname)
        if t is None and not is_pua(ucs):
            if ucs == 0xFFFD:
                h = dg.span_hash(xrefs, gid) if xrefs else 'nolink'
                if h not in NOSHAPE and dg.shapes[h][2] == 0:
                    return (' ', '그대로', 'base', 'space', None, '코드 없는 빈 글리프를 공백으로 봄')
                return ('⟦?⟧', '미확정', 'base', 'char', None, '글자층에 코드가 없음(U+FFFD)')
            if ucs in ZERO_WIDTH:
                return ('', '그대로', 'base', 'space', None, '폭 없는 공백을 뺌')
            return (chr(ucs), '그대로', 'base', 'char', None, '')
        key = (id(dg), cname, ucs, gid, tuple(xrefs))
        r = self._memo.get(key)
        if r is None:
            r = self._memo[key] = self._lookup(dg, fam, t, cname, ucs, gid, xrefs)
        return r

    def _lookup(self, dg, fam, t, cname, ucs, gid, xrefs):
        mark = '⟦U+%04X⟧' % ucs if ucs != 0xFFFD else '⟦?⟧'
        h = dg.span_hash(xrefs, gid)
        # 제 표를 먼저 본다. 같은 윤곽선이 다른 표에 들어 있을 수도 있다(EH·TK·ASusic·Amsusic은 글리프를 함께 쓰고,
        # 수식 글꼴의 글리프가 본문 글꼴 PUA 칸에 묶인 경우도 있다). 다른 표의 항목은 '전수 조사에서 바로 이 글꼴 이름이
        # 그 모양을 쓴 적이 있을 때'만 받아들인다.
        if t is not None:
            own = [t]
            tabs = [t] + [x[2] for x in self.tb.math if x[2] is not t] + [x[2] for x in self.tb.pua]
        else:
            own = [x[2] for x in self.tb.pua]
            tabs = own + [x[2] for x in self.tb.math]
        if h == 'ambig':
            found = {}
            for x in xrefs:
                hx = dg.glyph_hash(x, gid)
                for tt in tabs:
                    e = tt['by_hash'].get(hx)
                    if e is not None and any(k[0] == cname and int(k[1], 16) == ucs for k in e.get('keys', ())):
                        found[(e['text'], e.get('pos', 'base'), e['status'])] = e
            if len(found) == 1:
                return self._out(next(iter(found.values())), mark, '모양 일치(같은 이름 글꼴 여럿 가운데 코드가 맞는 쪽)', cname, ucs)
        if h in NOSHAPE:
            return (mark, '미확정', 'base', 'char', None, '모양 확인 불가: ' + NOSHAPE_KO[h])
        sh = dg.shapes[h]
        if sh[2] == 0:                                   # 빈 글리프
            return (' ' if (ucs in SPACES or t is not None) else '', '그대로', 'base', 'space', None, '빈 글리프')
        for tt in tabs:
            e = tt['by_hash'].get(h)
            if e is None:
                continue
            if any(tt is o for o in own):
                return self._out(e, mark, '모양 일치', cname, ucs)
            if cname in e['_fonts']:
                return self._out(e, mark, '모양 일치(다른 표에 든 같은 윤곽선)', cname, ucs)
        for tt in tabs:
            isown = any(tt is o for o in own)
            e = _tol_find(sh, tt['by_key'].get((cname, ucs), ()))
            if e is None and isown:
                e = _tol_find(sh, tt['by_ucs'].get(ucs, ()))
            if e is None and isown and ucs == 0xFFFD:
                e = _tol_find(sh, tt['entries'])
            if e is not None:
                return self._out(e, mark, '모양 거의 일치', cname, ucs)
        how = '표에 없는 모양'
        if t is None and ucs in self.tb.hanyang:
            how += ' (옛한글 글꼴이면 한양 표 후보: %s)' % self.tb.hanyang[ucs]
        return (mark, '미확정', 'base', 'char', None, how)

    @staticmethod
    def _out(e, mark, how, cname=None, ucs=None):
        if e['status'] == '미확정':
            return (mark, '미확정', e.get('pos', 'base'), e.get('role', 'char'), e['id'], '표에서 아직 못 정한 글리프')
        for a in e.get('alt', ()):
            # 모양으로는 가릴 수 없는 글자(I·l, O·0 …): 표가 '이 글꼴은 코드가 믿을 만하다'고 적어 둔 경우 글자층 코드를 따른다
            if a[0] == cname and int(a[1], 16) == ucs:
                return (a[2], e['status'], e.get('pos', 'base'), e.get('role', 'char'), e['id'], how + ' · 모양이 같은 글자라 글자층 코드를 따름')
        return (e['text'], e['status'], e.get('pos', 'base'), e.get('role', 'char'), e['id'], how)


RAW_FLAGS = pymupdf.TEXT_PRESERVE_LIGATURES | pymupdf.TEXT_PRESERVE_WHITESPACE | pymupdf.TEXT_MEDIABOX_CLIP


def convert_page(conv, doc, dg, pno, sort=False):
    """한 쪽 → 줄 목록. 줄 = {'bbox', 'text', 'chars': [바뀐 글자·미확정 글자 정보]}"""
    page = doc[pno]
    n2x = dg.page_map(page)
    trace = collections.defaultdict(list)
    for sp in page.get_texttrace():
        fname = sp['font']
        xr = tuple(n2x.get(fname, ()))
        cn = gc.clean_name(fname)
        d = sp.get('dir') or (1.0, 0.0)
        up = abs(d[0] - 1.0) < 1e-3 and abs(d[1]) < 1e-3
        for (ucs, gid, org, bbox) in sp['chars']:
            trace[(round(org[0], 1), round(org[1], 1))].append((ucs, gid, cn, xr, sp['size'], up))
    lines = []
    stat = collections.Counter()
    rd = page.get_text('rawdict', flags=RAW_FLAGS, sort=sort)
    for b in rd.get('blocks', []):
        for ln in b.get('lines', []):
            buf = []
            info = []
            recs = []
            for sp in ln.get('spans', []):
                for ch in sp.get('chars', []):
                    c = ch['c']
                    o = ch['origin']
                    lst = trace.get((round(o[0], 1), round(o[1], 1)))
                    hit = None
                    if lst:
                        for i, tc in enumerate(lst):
                            if tc[0] == ord(c) or len(lst) == 1:
                                hit = lst.pop(i)
                                break
                        if hit is None:
                            hit = lst.pop(0)
                    if hit is None:
                        u = ord(c)
                        cn = gc.clean_name(sp.get('font', ''))
                        fam, t = conv.tb.family(cn)
                        if u in SPACES:
                            res = (' ', '그대로', 'base', 'space', None, '')
                        elif t is not None or is_pua(u) or u == 0xFFFD:
                            res = ('⟦U+%04X⟧' % u, '미확정', 'base', 'char', None, '글자층 대조 실패')
                        else:
                            res = (c, '그대로', 'base', 'char', None, '')
                        ucs, gid, size, up, xr = u, None, sp.get('size'), False, ()
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
                    recs.append((o[0], o[1], size or 0, cen, up, role == 'char' and status in ('그대로', '확정')))
                    stat[status] += 1
                    if status != '그대로' or pos != 'base':
                        info.append({'i': len(buf), 'ucs': '%04X' % ucs, 'font': cn, 'text': text, 'status': status, 'pos': pos, 'role': role, 'id': eid, 'how': how,
                                     'x': round(o[0], 1), 'y': round(o[1], 1), 'size': round(size or 0, 1), 'gid': gid, '_xr': list(xr)})
                    buf.append((text, pos))
            if not buf:
                continue
            _fix_pos(buf, info, recs)
            lines.append({'bbox': [round(v, 1) for v in ln['bbox']], 'text': _join(buf), 'chars': info})
    return lines, stat


POS_CUT = 0.33          # 잉크 가운데가 견준 본문 글자의 기준선에서 그 글자 크기의 이 비율보다 높으면 위첨자, 아니면 아래첨자
POS_DEBUG = None        # 시험용: 목록을 넣어 두면 (표의 자리, 높이 비율, 글자)를 모은다


def _fix_pos(buf, info, recs):
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


def _join(buf):
    """위·아래 첨자 모양 글리프는 ^{…} _{…} 로 묶어 적는다."""
    out = []
    cur = 'base'
    for text, pos in buf:
        if pos != cur:
            if cur != 'base':
                out.append('}')
            if pos == 'sup':
                out.append('^{')
            elif pos == 'sub':
                out.append('_{')
            cur = pos
        out.append(text)
    if cur != 'base':
        out.append('}')
    return ''.join(out)


def parse_pages(spec, n):
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            a, b = part.split('-', 1)
            a = int(a) if a else 1
            b = int(b) if b else n
        else:
            a = b = int(part)
        for p in range(a, b + 1):
            if 1 <= p <= n and (p - 1) not in out:
                out.append(p - 1)
    return out


def write_evidence(conv, doc, dg, pno, lines, outdir):
    """쪽마다 바뀐 글리프의 그림 표를 만든다: 글리프 그림 | 바꾼 글자 | 상태 | 횟수 | 실제 쪽 문맥."""
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(outdir, exist_ok=True)
    fn = '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc'
    fs = '/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc'
    try:
        F = ImageFont.truetype(fn, 14, index=1)
        try:
            FT = ImageFont.truetype(fs, 30, index=1, layout_engine=ImageFont.Layout.RAQM)
        except Exception:
            FT = ImageFont.truetype(fs, 30, index=1)
    except Exception:
        F = FT = ImageFont.load_default()
    FS = None
    for fp in ('/usr/share/fonts/gnu-free/FreeSerif.otf', '/usr/share/fonts/TTF/DejaVuSerif.ttf'):
        if os.path.exists(fp):
            try:
                FS = ImageFont.truetype(fp, 30)
                break
            except Exception:
                pass

    def pick(text):
        if FS is None or any(0x1100 <= ord(ch) <= 0x11FF or 0x2E80 <= ord(ch) <= 0xD7FF or 0xF900 <= ord(ch) <= 0xFAFF or 0xA960 <= ord(ch) <= 0xA97F for ch in text):
            return FT
        try:
            if FS.getmask(text).getbbox() is None:
                return FT
        except Exception:
            return FT
        return FS
    page = doc[pno]
    n2x = dg.page_map(page)
    name2x = {}
    for k, v in n2x.items():
        name2x.setdefault(gc.clean_name(k), v)
    seen = collections.OrderedDict()
    for ln in lines:
        for c in ln['chars']:
            if c['status'] == '그대로':
                continue
            k = (c['font'], c['ucs'], c['id'], c['text'], c['status'], c['pos'])
            if k not in seen:
                seen[k] = [0, c]
            seen[k][0] += 1
    if not seen:
        return None
    rowh, W = 70, 900
    im = Image.new('RGB', (W, 26 + rowh * len(seen)), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.text((6, 4), '%s  %d쪽  — 글리프 | 바꾼 글자 | 상태·글꼴·코드·횟수 | 문맥(빨간 세모 사이)' % (os.path.basename(doc.name)[:40], pno + 1), font=F, fill=(0, 0, 0))
    col = {'확정': (0, 110, 0), '근사': (170, 110, 0), '미확정': (200, 0, 0)}
    for r, ((font, ucs, eid, text, status, pos), (cnt, c)) in enumerate(seen.items()):
        y0 = 26 + r * rowh
        d.line([(0, y0), (W, y0)], fill=(200, 200, 200))
        xr = c.get('_xr') or name2x.get(font) or n2x.get(font, ())
        g = None
        if c['gid'] is not None and len(xr) >= 1:
            g = dg.gray_any(xr, c['gid'], 40)
        if g is not None and g[2].size:
            a = g[2]
            if a.shape[0] > 62 or a.shape[1] > 80:
                s = min(62 / a.shape[0], 80 / a.shape[1])
                a = np.asarray(Image.fromarray(a).resize((max(1, int(a.shape[1] * s)), max(1, int(a.shape[0] * s)))))
            gi = Image.fromarray((255 - a).astype(np.uint8)).convert('RGB')
            im.paste(gi, (8 + (80 - gi.width) // 2, y0 + 4 + (62 - gi.height) // 2))
        shown = text if len(text) <= 6 else text[:6]
        d.text((100, y0 + 14), shown, font=pick(shown), fill=col.get(status, (0, 0, 0)))
        d.text((250, y0 + 6), '%s%s' % (status, '' if pos == 'base' else (' · 위첨자' if pos == 'sup' else ' · 아래첨자')), font=F, fill=col.get(status, (0, 0, 0)))
        d.text((250, y0 + 26), '%s  U+%s  ×%d' % (font[:24], ucs, cnt), font=F, fill=(70, 70, 70))
        d.text((250, y0 + 46), (c['how'] or '')[:30], font=F, fill=(110, 110, 110))
        size = c['size'] or 10
        z = max(0.8, min(12.0, 20 / size))
        clip = pymupdf.Rect(c['x'] - 5 * size, c['y'] - 1.9 * size, c['x'] + 9 * size, c['y'] + 1.0 * size) & page.rect
        if not clip.is_empty:
            pm = page.get_pixmap(matrix=pymupdf.Matrix(z, z), clip=clip, colorspace=pymupdf.csRGB, alpha=False)
            ci = Image.frombytes('RGB', (pm.width, pm.height), pm.samples)
            tx = (c['x'] + 0.3 * size - clip.x0) * z
            dd = ImageDraw.Draw(ci)
            for yy, dy in ((0, 1), (ci.height - 1, -1)):
                dd.polygon([(tx - 4, yy), (tx + 4, yy), (tx, yy + dy * 6)], fill=(230, 0, 0))
            ci = ci.crop((0, 0, min(ci.width, 400), min(ci.height, rowh - 6)))
            im.paste(ci, (490, y0 + 3))
    out = os.path.join(outdir, '글자근거_p%04d.png' % (pno + 1))
    im.quantize(colors=24, dither=Image.Dither.NONE).save(out, optimize=True)
    return out


def run(args):
    conv = Converter(Tables(args.tables))
    doc = pymupdf.open(args.pdf)
    dg = gc.DocGlyphs(doc)
    pages = parse_pages(args.pages, doc.page_count)
    out = open(args.out, 'w', encoding='utf-8') if args.out else sys.stdout
    total = collections.Counter()
    unk = collections.Counter()
    appr = collections.Counter()
    conv_n = collections.Counter()
    for pno in pages:
        lines, stat = convert_page(conv, doc, dg, pno, sort=args.sort)
        total.update(stat)
        for ln in lines:
            for c in ln['chars']:
                if c['status'] == '미확정':
                    unk[(c['font'], c['ucs'], c['how'])] += 1
                elif c['status'] == '근사':
                    appr[(c['font'], c['ucs'], c['text'])] += 1
                elif c['status'] == '확정' and c['text'] != chr(int(c['ucs'], 16)):
                    conv_n[(c['font'], c['ucs'], c['text'])] += 1
        if args.format == 'jsonl':
            for i, ln in enumerate(lines):
                chars = [{k: v for k, v in c.items() if not k.startswith('_')} for c in ln['chars']]
                out.write(json.dumps({'page': pno + 1, 'line': i + 1, 'bbox': ln['bbox'], 'text': ln['text'], 'chars': chars}, ensure_ascii=False) + '\n')
        else:
            out.write('=== %d쪽 === 확정 %d · 근사 %d · 미확정 %d · 그대로 %d\n' % (pno + 1, stat['확정'], stat['근사'], stat['미확정'], stat['그대로']))
            for ln in lines:
                out.write(ln['text'] + '\n')
        if args.evidence:
            write_evidence(conv, doc, dg, pno, lines, args.evidence)
    rep = ['# 글자 변환 보고', 'PDF: %s' % args.pdf, '쪽: %s (%d쪽)' % (args.pages or '전체', len(pages)),
           '표 판: %s' % json.dumps(conv.tb.version, ensure_ascii=False),
           '글자 수: 확정 %d · 근사 %d · 미확정 %d · 그대로 %d' % (total['확정'], total['근사'], total['미확정'], total['그대로']),
           '', '## 코드와 다른 글자로 바로잡은 것 (많은 순, %d종)' % len(conv_n)]
    rep += ['- %s U+%s → %s  ×%d' % (k[0], k[1], k[2], v) for k, v in conv_n.most_common(60)]
    rep += ['', '## 근사 (%d종)' % len(appr)] + ['- %s U+%s → %s  ×%d' % (k[0], k[1], k[2], v) for k, v in appr.most_common(60)]
    rep += ['', '## 미확정 (%d종)' % len(unk)] + ['- %s U+%s  ×%d  (%s)' % (k[0], k[1], v, k[2]) for k, v in unk.most_common(80)]
    txt = '\n'.join(rep) + '\n'
    if args.report:
        open(args.report, 'w', encoding='utf-8').write(txt)
    else:
        sys.stderr.write(txt)
    if out is not sys.stdout:
        out.close()
    return 0


def selftest(tdir):
    """표가 읽히는지, 기준 모양끼리 헷갈리는 것이 없는지 본다."""
    tb = Tables(tdir)
    n = 0
    bad = 0
    for nm, rx, t in tb.math + tb.pua:
        ne = len(t['entries'])
        ns = sum(len(e['_shapes']) for e in t['entries'])
        st = collections.Counter(e['status'] for e in t['entries'])
        dup = ns - len(t['by_hash'])
        print('%-10s 항목 %5d · 기준 모양 %5d · 확정 %d · 근사 %d · 미확정 %d%s' % (nm, ne, ns, st['확정'], st['근사'], st['미확정'], (' · 겹치는 모양 %d' % dup) if dup else ''))
        n += ne
        for e in t['entries']:
            if e['status'] not in ('확정', '근사', '미확정') or e.get('pos', 'base') not in ('base', 'sup', 'sub'):
                bad += 1
            if e['status'] != '미확정' and e['text'] != e['text'].strip('\ufeff'):
                bad += 1
    import unicodedata
    s = '\u1103\u1172\u11f0'
    print('옛한글 정규화 주의:', [hex(ord(c)) for c in s], '→ NFC', [hex(ord(c)) for c in unicodedata.normalize('NFC', s)], '(받침이 떨어지므로 NFC를 걸지 않는다)')
    print('항목 합계', n, '· 형식 문제', bad)
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description='PDF 글자층을 글리프 모양으로 확인해 표준 글자로 바꾼다')
    ap.add_argument('pdf', nargs='?')
    ap.add_argument('--pages', help='쪽 범위. 예: 12-14,20 (1부터 센다). 없으면 전체')
    ap.add_argument('--format', choices=['text', 'jsonl'], default='text')
    ap.add_argument('--out', help='결과 파일(없으면 화면)')
    ap.add_argument('--report', help='보고 파일(없으면 표준 오류로 찍음)')
    ap.add_argument('--evidence', help='쪽마다 글자 근거 그림을 이 폴더에 만든다')
    ap.add_argument('--tables', default=GLYPH_DIR, help='대응표 폴더')
    ap.add_argument('--sort', action='store_true', help='줄을 위치 순(위→아래, 왼쪽→오른쪽)으로 다시 놓는다. 기본은 PDF에 적힌 순서')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.tables)
    if not a.pdf:
        ap.error('PDF 경로가 필요해요')
    return run(a)


if __name__ == '__main__':
    sys.exit(main())
