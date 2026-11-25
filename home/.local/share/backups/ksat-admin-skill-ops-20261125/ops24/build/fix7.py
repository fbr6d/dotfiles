p = 'glyphcore.py'
s = open(p).read()

old = """class DocGlyphs:
    \"\"\"PDF 한 권에서 (글꼴 객체, gid) → 모양을 구해 주는 도우미.\"\"\"

    def __init__(self, doc):
        self.doc = doc
        self._font = {}       # xref -> Font | None
        self._names = {}      # xref -> names
        self._hash = {}       # (xref, gid) -> hash
        self.shapes = {}      # hash -> shape
"""
new = """_T3NAME = re.compile(r'^Type3 \\((\\d+) 0 R\\)$')


class FontMap(dict):
    \"\"\"쪽의 글꼴 이름 → 글꼴 객체 번호 목록. 이름 없는 Type3 글꼴('Type3 (220 0 R)')은 이름에서 번호를 읽는다.\"\"\"

    def get(self, name, default=()):
        v = dict.get(self, name)
        if v:
            return v
        m = _T3NAME.match(name or '')
        if m:
            return [int(m.group(1))]
        return default


class DocGlyphs:
    \"\"\"PDF 한 권에서 (글꼴 객체, gid) → 모양을 구해 주는 도우미.\"\"\"

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
            sd, pno, pxref, c = self._scratch
            sd.xref_set_key(pxref, 'Resources', '<</Font<</T3 %d 0 R>>>>' % xref)
            sd.update_stream(c, b'BT /T3 100 Tf 1 0 0 1 100 150 Tm <%02X> Tj ET' % gid)
            pg = sd.reload_page(sd[pno])
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
        \"\"\"눈으로 볼 그림용 (x, y, 회색 배열). 보통 글꼴과 Type3 글꼴을 모두 다룬다.\"\"\"
        f = self.font(xref)
        if f is not None:
            return render_gray(f, gid, px)
        if self._type.get(xref) == 'Type3' or self._is_t3(xref):
            return self._t3_gray(xref, gid, px)
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
"""
assert old in s; s = s.replace(old, new)

old = """        out = {}
        try:
            fl = page.get_fonts(full=True)
        except Exception:
            fl = []
        for f in fl:
            xr = f[0]
"""
new = """        out = FontMap()
        try:
            fl = page.get_fonts(full=True)
        except Exception:
            fl = []
        for f in fl:
            xr = f[0]
            self._type[xr] = f[2]
"""
assert old in s; s = s.replace(old, new)

old = """            f = self.font(xref)
            if f is None:
                h = 'noembed'
            else:
                sh = render_shape(f, gid)
                h = shape_hash(sh)
                if sh is not None:
                    self.shapes[h] = sh
            self._hash[k] = h
"""
new = """            f = self.font(xref)
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
"""
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
