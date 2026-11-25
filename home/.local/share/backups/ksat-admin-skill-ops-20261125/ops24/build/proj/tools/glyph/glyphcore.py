# -*- coding: utf-8 -*-
"""PDF 글리프를 '글꼴 객체에서 바로 그린 모양'으로 다루는 공통 함수.

/usr/bin/python3 의 pymupdf + numpy 만 쓴다(fontTools 없음).
- 글자층에서 뽑힌 코드(ucs)는 글꼴마다 뜻이 달라 믿을 수 없다.
- 그래서 글자마다 (글꼴 객체, 글리프 번호 gid)로 글리프를 따로 그려 그 모양을 열쇠로 쓴다.
"""
import re
import struct
import hashlib
import numpy as np
import pymupdf
from pymupdf import mupdf

pymupdf.TOOLS.set_subset_fontnames(True)

S = 48        # 기준 그림 크기 (픽셀 / em)
THR = 96      # 이진화 문턱 (0~255)
_TAG = re.compile(r'^[A-Z]{6}\+')
_ESC = re.compile(r'#([0-9A-Fa-f]{2})')
_REF = re.compile(r'(\d+)\s+\d+\s+R')
_CMAP = re.compile(r'-(KSC|Identity|UniKS)[A-Za-z0-9-]*$')
_INF = mupdf.FzIrect(mupdf.fz_infinite_irect)
EMPTY = (0, 0, 0, 0, b'')


def clean_name(name):
    """부분집합 꼬리표(ABCDEF+)를 떼고, CP949가 라틴-1로 깨진 한글 이름을 되살린다."""
    n = _TAG.sub('', name or '')
    try:
        raw = n.encode('latin-1')
        if any(b >= 0x80 for b in raw):
            n = raw.decode('cp949')
    except Exception:
        pass
    # CMap 이름이 붙은 꼴(…-KSCms-UHC-H, …-Identity-H)은 떼어 낸다. MuPDF는 글꼴 이름을 31자에서 자르므로 잘린 꼴도 함께 뗀다.
    n = _CMAP.sub('', n)
    return n


_ESCB = re.compile(rb'#([0-9A-Fa-f]{2})')


def _unesc(s):
    """PDF 이름 값을 글자층이 쓰는 꼴(바이트를 라틴-1로 읽은 글)로 바꾼다.

    xref_get_key 는 이름의 바이트를 UTF-8(surrogateescape)로 읽어 주므로, 다시 바이트로 되돌린 뒤 라틴-1로 읽는다.
    """
    s = s.lstrip('/')
    try:
        b = s.encode('utf-8', 'surrogateescape')
    except Exception:
        b = s.encode('utf-8', 'replace')
    b = _ESCB.sub(lambda m: bytes([int(m.group(1), 16)]), b)
    return b.decode('latin-1')


def font_names(doc, xref):
    """글꼴 객체 하나가 글자층에서 불릴 수 있는 이름들(꼬리표 포함)."""
    names = set()

    def add(xr, key):
        try:
            t, v = doc.xref_get_key(xr, key)
        except Exception:
            return
        if t == 'name' and v:
            names.add(_unesc(v))

    add(xref, 'BaseFont')
    add(xref, 'FontDescriptor/FontName')
    try:
        t, v = doc.xref_get_key(xref, 'DescendantFonts')
    except Exception:
        t, v = 'null', ''
    dx = None
    if t == 'array':
        m = _REF.search(v)
        dx = int(m.group(1)) if m else None
    elif t == 'xref':
        m = _REF.search(v)
        if m:
            try:
                arr = doc.xref_object(int(m.group(1)), compressed=True)
                m2 = _REF.search(arr)
                dx = int(m2.group(1)) if m2 else None
            except Exception:
                dx = None
    if dx:
        add(dx, 'BaseFont')
        add(dx, 'FontDescriptor/FontName')
    return names


def render_shape(font, gid, s=S, thr=THR):
    """글리프 하나를 s 픽셀/em 으로 그려 (x, y, w, h, 비트)로 돌려준다. 기준선 원점, y는 아래로 +."""
    ctm = mupdf.FzMatrix(s, 0, 0, -s, 0, 0)
    try:
        pm = mupdf.fz_render_glyph_pixmap(font.this, gid, ctm, _INF, 8)
    except Exception:
        return None
    if pm is None or not getattr(pm, 'm_internal', None):
        return EMPTY
    try:
        px = pymupdf.Pixmap(pm)
        w, h = px.width, px.height
        if w <= 0 or h <= 0:
            return EMPTY
        a = np.frombuffer(px.samples, np.uint8).reshape(h, px.stride)[:, :w]
    except Exception:
        return None
    m = a >= thr
    ys = np.flatnonzero(m.any(1))
    if len(ys) == 0:
        return EMPTY
    xs = np.flatnonzero(m.any(0))
    m = m[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
    return (int(px.x + xs[0]), int(px.y + ys[0]), int(m.shape[1]), int(m.shape[0]), np.packbits(m).tobytes())


def render_gray(font, gid, s):
    """눈으로 볼 그림용: (x, y, 회색 배열) — 값이 클수록 진하다."""
    ctm = mupdf.FzMatrix(s, 0, 0, -s, 0, 0)
    try:
        pm = mupdf.fz_render_glyph_pixmap(font.this, gid, ctm, _INF, 8)
    except Exception:
        return None
    if pm is None or not getattr(pm, 'm_internal', None):
        return (0, 0, np.zeros((0, 0), np.uint8))
    px = pymupdf.Pixmap(pm)
    w, h = px.width, px.height
    if w <= 0 or h <= 0:
        return (0, 0, np.zeros((0, 0), np.uint8))
    a = np.frombuffer(px.samples, np.uint8).reshape(h, px.stride)[:, :w].copy()
    return (int(px.x), int(px.y), a)


def shape_hash(shape):
    if shape is None:
        return 'norender'
    x, y, w, h, bits = shape
    return hashlib.blake2b(struct.pack('<hhHH', x, y, w, h) + bits, digest_size=8).hexdigest()


def shape_mask(shape):
    x, y, w, h, bits = shape
    if w == 0 or h == 0:
        return np.zeros((0, 0), bool)
    return np.unpackbits(np.frombuffer(bits, np.uint8))[:w * h].reshape(h, w).astype(bool)


def _dil(a):
    b = a.copy()
    b[1:, :] |= a[:-1, :]
    b[:-1, :] |= a[1:, :]
    b[:, 1:] |= a[:, :-1]
    b[:, :-1] |= a[:, 1:]
    b[1:, 1:] |= a[:-1, :-1]
    b[:-1, :-1] |= a[1:, 1:]
    b[1:, :-1] |= a[:-1, 1:]
    b[:-1, 1:] |= a[1:, :-1]
    return b


def tol_score(sa, sb):
    """두 모양이 같은 정도(0~1). 테두리 1픽셀 어긋남은 봐준다. 위치(기준선·원점)도 같이 본다."""
    if sa is None or sb is None:
        return 0.0
    ax, ay, aw, ah, _ = sa
    bx, by, bw, bh, _ = sb
    if aw == 0 or bw == 0:
        return 1.0 if (aw == 0 and bw == 0) else 0.0
    x0 = min(ax, bx) - 1
    y0 = min(ay, by) - 1
    x1 = max(ax + aw, bx + bw) + 1
    y1 = max(ay + ah, by + bh) + 1
    A = np.zeros((y1 - y0, x1 - x0), bool)
    B = np.zeros((y1 - y0, x1 - x0), bool)
    A[ay - y0:ay - y0 + ah, ax - x0:ax - x0 + aw] = shape_mask(sa)
    B[by - y0:by - y0 + bh, bx - x0:bx - x0 + bw] = shape_mask(sb)
    na, nb = int(A.sum()), int(B.sum())
    if na == 0 or nb == 0:
        return 0.0
    return float((A & _dil(B)).sum() + (B & _dil(A)).sum()) / (na + nb)


_T3NAME = re.compile(r'^Type3 \((\d+) 0 R\)$')


class FontMap(dict):
    """쪽의 글꼴 이름 → 글꼴 객체 번호 목록. 이름 없는 Type3 글꼴('Type3 (220 0 R)')은 이름에서 번호를 읽는다."""

    def get(self, name, default=()):
        v = dict.get(self, name)
        if v:
            return v
        m = _T3NAME.match(name or '')
        if m:
            return [int(m.group(1))]
        return default


class DocGlyphs:
    """PDF 한 권에서 (글꼴 객체, gid) → 모양을 구해 주는 도우미."""

    def __init__(self, doc):
        self.doc = doc
        self._font = {}       # xref -> Font | None
        self._names = {}      # xref -> names
        self._hash = {}       # (xref, gid) -> hash
        self._type = {}       # xref -> 글꼴 종류(Type3 인지 보려고)
        self._scratch = None  # Type3 글리프를 그릴 때 쓰는 같은 파일의 둘째 손잡이(저장하지 않는다)
        self.shapes = {}      # hash -> shape

    # ---- Type3 글꼴: 글꼴 프로그램이 없어서, 임시 쪽에 그 글자 하나만 찍어 그린다
    def _t3_gray(self, xref, gid, px):
        if gid is None or not (0 <= gid <= 255):
            return None
        try:
            if self._scratch is None:
                sd = pymupdf.open(self.doc.name)
                pg = sd.new_page(width=400, height=400)
                c = sd.get_new_xref()
                sd.update_object(c, '<<>>')
                sd.update_stream(c, b' ')
                sd.xref_set_key(pg.xref, 'Contents', '%d 0 R' % c)
                self._scratch = (sd, pg.number, pg.xref, c)
                del pg            # 쪽 객체를 쥐고 있으면 다음에 새로 읽히지 않는다
            sd, pno, pxref, c = self._scratch
            sd.xref_set_key(pxref, 'Resources', '<</Font<</T3 %d 0 R>>>>' % xref)
            sd.update_stream(c, b'BT /T3 100 Tf 1 0 0 1 100 150 Tm <%02X> Tj ET' % gid)
            pg = sd.load_page(pno)
            z = px / 100.0
            pm = pg.get_pixmap(matrix=pymupdf.Matrix(z, z), colorspace=pymupdf.csGRAY, alpha=False)
            a = 255 - np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.stride)[:, :pm.width]
            ox, oy = int(round(100 * z)), int(round(250 * z))
            ys = np.flatnonzero((a >= 24).any(1))
            if len(ys) == 0:
                return (0, 0, np.zeros((0, 0), np.uint8))
            xs = np.flatnonzero((a >= 24).any(0))
            a = a[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1].copy()
            return (int(xs[0] - ox), int(ys[0] - oy), a)
        except Exception:
            return None

    def gray(self, xref, gid, px):
        """눈으로 볼 그림용 (x, y, 회색 배열). 보통 글꼴과 Type3 글꼴을 모두 다룬다."""
        f = self.font(xref)
        if f is not None:
            return render_gray(f, gid, px)
        if self._type.get(xref) == 'Type3' or self._is_t3(xref):
            return self._t3_gray(xref, gid, px)
        return None

    def gray_any(self, xrefs, gid, px):
        """같은 이름의 글꼴 객체가 여럿이면 그릴 수 있는 첫 객체로 그린다."""
        for x in xrefs:
            g = self.gray(x, gid, px)
            if g is not None and g[2].size:
                return g
        return None

    def _is_t3(self, xref):
        t = self._type.get(xref)
        if t is None:
            try:
                k, v = self.doc.xref_get_key(xref, 'Subtype')
                t = v.lstrip('/')
            except Exception:
                t = ''
            self._type[xref] = t
        return t == 'Type3'

    def advance(self, xref, gid):
        f = self.font(xref)
        if f is None:
            return None
        try:
            return float(mupdf.fz_advance_glyph(f.this, gid, 0))
        except Exception:
            return None

    def page_map(self, page):
        """쪽에서 쓰는 글꼴 이름(꼬리표 포함) → 글꼴 객체 번호 목록."""
        out = FontMap()
        try:
            fl = page.get_fonts(full=True)
        except Exception:
            fl = []
        for f in fl:
            xr = f[0]
            self._type[xr] = f[2]
            nm = self._names.get(xr)
            if nm is None:
                nm = font_names(self.doc, xr)
                if f[3]:
                    nm.add(f[3])
                self._names[xr] = nm
            for n in nm:
                for k in {n, n[:31]}:      # MuPDF는 글꼴 이름을 31자에서 자른다
                    lst = out.setdefault(k, [])
                    if xr not in lst:
                        lst.append(xr)
        return out

    def font(self, xref):
        if xref in self._font:
            return self._font[xref]
        f = None
        try:
            name, ext, typ, buf = self.doc.extract_font(xref)
            if buf:
                f = pymupdf.Font(fontbuffer=buf)
        except Exception:
            f = None
        self._font[xref] = f
        return f

    def glyph_hash(self, xref, gid):
        k = (xref, gid)
        h = self._hash.get(k)
        if h is None:
            f = self.font(xref)
            if f is None:
                h = 'noembed'
                if self._is_t3(xref):
                    g = self._t3_gray(xref, gid, S)
                    if g is not None:
                        m = g[2] >= THR
                        if m.size and m.any():
                            ys = np.flatnonzero(m.any(1)); xs = np.flatnonzero(m.any(0))
                            m = m[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
                            sh = (int(g[0] + xs[0]), int(g[1] + ys[0]), int(m.shape[1]), int(m.shape[0]), np.packbits(m).tobytes())
                        else:
                            sh = EMPTY
                        h = shape_hash(sh)
                        self.shapes[h] = sh
            else:
                sh = render_shape(f, gid)
                h = shape_hash(sh)
                if sh is not None:
                    self.shapes[h] = sh
            self._hash[k] = h
        return h

    def span_hash(self, xrefs, gid):
        """span의 글꼴 이름에 이어진 글꼴 객체들로 글리프 모양 해시를 구한다."""
        if not xrefs:
            return 'nolink'
        if len(xrefs) == 1:
            return self.glyph_hash(xrefs[0], gid)
        hs = {self.glyph_hash(x, gid) for x in xrefs}
        hs.discard('noembed')
        if len(hs) == 1:
            return hs.pop()
        return 'ambig' if hs else 'noembed'
