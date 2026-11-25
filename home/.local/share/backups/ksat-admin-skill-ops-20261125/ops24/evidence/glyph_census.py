"""수식 글꼴 글리프 전수: (글꼴, 글리프) 열쇠가 책·쪽이 달라도 같은 모양인지 윤곽선 해시로 확인 (읽기 전용)"""
import collections, hashlib, io, json, pickle, re, sys, time
import pymupdf
from fontTools.ttLib import TTFont
from fontTools.cffLib import CFFFontSet
from fontTools.pens.recordingPen import RecordingPen
PAT = re.compile(sys.argv[1])
paths = sys.argv[3:]
outp = sys.argv[2]
class F:
    def __init__(self, buf, ext):
        self.ext = ext; self.ok = True
        try:
            if ext == 'cff':
                cff = CFFFontSet(); cff.decompile(io.BytesIO(buf), None)
                self.top = cff[0]; self.names = list(self.top.charset); self.cs = self.top.CharStrings; self.gs = None
            else:
                self.tt = TTFont(io.BytesIO(buf), lazy=False)
                self.names = self.tt.getGlyphOrder(); self.gs = self.tt.getGlyphSet()
        except Exception as e:
            self.ok = False; self.err = str(e)
    def rec(self, gid):
        if gid >= len(self.names): return None, None
        nm = self.names[gid]
        pen = RecordingPen()
        try:
            if self.ext == 'cff': self.cs[nm].draw(pen)
            else: self.gs[nm].draw(pen)
        except Exception:
            return nm, None
        return nm, pen.value
def h(val):
    s = repr([(op, tuple(tuple(round(c, 1) for c in pt) if pt is not None else None for pt in pts)) for op, pts in val])
    return hashlib.md5(s.encode()).hexdigest()[:12]
G = {}   # (book, base, key) -> info
t0 = time.time()
for path in paths:
    book = path.split('/')[-1]
    doc = pymupdf.open(path)
    cache = {}
    nfont_fail = 0
    for pno in range(len(doc)):
        page = doc[pno]
        name2x = collections.defaultdict(set)
        for xref, ext, typ, base, rname, enc, _ in page.get_fonts(full=True):
            name2x[base].add(xref)
        for sp in page.get_texttrace():
            tagged = sp['font']
            base = re.sub(r'^[A-Z]{6}\+', '', tagged)
            if not PAT.search(base): continue
            xs = name2x.get(tagged) or set()
            fobj = None
            if len(xs) == 1:
                x = next(iter(xs))
                if x not in cache:
                    try:
                        bn, ext, typ, buf = doc.extract_font(x)
                        cache[x] = F(buf, ext) if buf else None
                    except Exception:
                        cache[x] = None
                fobj = cache[x]
            for ucs, gid, org, bbox in sp['chars']:
                nm = rec = None
                if fobj is not None and fobj.ok:
                    nm, rec = fobj.rec(gid)
                key = nm if (fobj is not None and fobj.ok and fobj.ext == 'cff') else gid
                k = (book, base, key)
                g = G.get(k)
                if g is None:
                    g = G[k] = {'n': 0, 'ucs': collections.Counter(), 'hash': collections.Counter(), 'occ': [], 'rec': None, 'amb': 0, 'size': collections.Counter()}
                g['n'] += 1; g['ucs'][ucs] += 1
                if rec is not None:
                    hh = h(rec); g['hash'][hh] += 1
                    if g['rec'] is None and rec: g['rec'] = rec
                else:
                    g['amb'] += 1
                if len(g['occ']) < 4: g['occ'].append((pno, tuple(bbox), sp['size']))
    print(f'{book}: {len(doc)}쪽, 글꼴 객체 {len(cache)}개 읽음, 누적 열쇠 {len(G)}, {round(time.time()-t0)}s', flush=True)
pickle.dump(G, open(outp, 'wb'))
# 요약
by = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
for (book, base, key), g in G.items():
    b = by[(book, base)]
    b[0] += 1; b[1] += g['n']
    real = [x for x in g['hash']]
    b[2] += (len(real) > 1); b[3] += (len(g['ucs']) > 1); b[4] += (len(real) == 0)
print('책 | 글꼴 | 글리프 종 | 글자 수 | 윤곽선이 둘 이상인 열쇠 | 뽑힌 글자가 둘 이상인 열쇠 | 윤곽선 못 읽은 열쇠')
for (book, base), b in sorted(by.items()):
    print(f'{book[:14]:14s} {base[:22]:22s} {b[0]:4d} {b[1]:6d} {b[2]:3d} {b[3]:3d} {b[4]:3d}')
print('합계: 열쇠', len(G), '글자', sum(g['n'] for g in G.values()))
