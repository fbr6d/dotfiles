"""수식 글꼴 글리프 전수 4판 (읽기 전용).
- 글자마다 실제 글꼴 객체를 부분집합 꼬리표 이름으로 찾아 윤곽선을 읽는다.
- 열쇠 = (글꼴 기본 이름, 윤곽선 해시). 윤곽선을 못 읽으면 (글꼴 기본 이름, 'k:'+GID)."""
import collections, hashlib, io, pickle, re, sys, time
import pymupdf
from fontTools.ttLib import TTFont
from fontTools.cffLib import CFFFontSet
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
pymupdf.TOOLS.set_subset_fontnames(True)
PAT = re.compile(sys.argv[1]); outp = sys.argv[2]; paths = sys.argv[3:]
class F:
    def __init__(self, buf, ext):
        self.ext = ext; self.ok = True; self.memo = {}; self.upm = 1000
        try:
            if ext == 'cff':
                cff = CFFFontSet(); cff.decompile(io.BytesIO(buf), None)
                self.top = cff[0]; self.names = list(self.top.charset); self.cs = self.top.CharStrings
            else:
                self.tt = TTFont(io.BytesIO(buf), lazy=False)
                self.names = self.tt.getGlyphOrder(); self.gs = self.tt.getGlyphSet(); self.upm = self.tt['head'].unitsPerEm
        except Exception:
            self.ok = False
    def rec(self, gid):
        if gid in self.memo: return self.memo[gid]
        r = (None, None)
        if self.ok and gid < len(self.names):
            nm = self.names[gid]
            try:
                if self.ext == 'cff':
                    pen = RecordingPen(); self.cs[nm].draw(pen)
                else:
                    pen = DecomposingRecordingPen(self.gs); self.gs[nm].draw(pen)
                r = (nm, pen.value)
            except Exception:
                r = (nm, None)
        self.memo[gid] = r
        return r
def h(val):
    s = repr([(op, tuple(tuple(round(c, 1) for c in pt) if pt is not None else None for pt in pts)) for op, pts in val])
    return hashlib.md5(s.encode()).hexdigest()[:12]
G = {}; stat = collections.Counter(); t0 = time.time()
for path in paths:
    book = path.split('/')[-1]
    doc = pymupdf.open(path); cache = {}
    for pno in range(len(doc)):
        page = doc[pno]
        tag2x = collections.defaultdict(list)
        for xref, ext, typ, base, rname, enc, _ in page.get_fonts(full=True):
            tag2x[base].append(xref)
        for sp in page.get_texttrace():
            tagged = sp['font']; base = re.sub(r'^[A-Z]{6}\+', '', tagged)
            if not PAT.search(base): continue
            xs = tag2x.get(tagged, [])
            if len(xs) != 1:
                stat['글꼴 객체를 하나로 못 정함' if xs else '글꼴 객체 없음'] += len(sp['chars'])
            fobj = None
            if len(xs) >= 1:
                x = xs[0]
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
                if rec:
                    k = (base, 'h:' + h(rec))
                else:
                    k = (base, f'k:{gid}'); stat['윤곽선 없음(빈 글리프·글꼴 미포함)'] += 1
                g = G.get(k)
                if g is None:
                    g = G[k] = {'n': 0, 'books': collections.Counter(), 'ucs': collections.Counter(), 'gids': collections.Counter(), 'names': collections.Counter(), 'occ': [], 'rec': rec, 'upm': fobj.upm if (fobj and fobj.ok) else None, 'ext': fobj.ext if (fobj and fobj.ok) else None, 'zero_w': 0, 'sizes': collections.Counter()}
                g['n'] += 1; g['books'][book] += 1; g['ucs'][ucs] += 1; g['gids'][gid] += 1
                if nm: g['names'][nm] += 1
                g['sizes'][round(sp['size'])] += 1
                if bbox[2] - bbox[0] < 0.01: g['zero_w'] += 1
                if len(g['occ']) < 3: g['occ'].append((book, pno, tuple(bbox), sp['size'], tuple(org)))
    print(f'{book[:40]}: {len(doc)}쪽, 글꼴 객체 {len(cache)}, 누적 열쇠 {len(G)}, {round(time.time()-t0)}s', flush=True)
pickle.dump(G, open(outp, 'wb'))
print(dict(stat))
out = [k for k in G if k[1].startswith('h:')]; noout = [k for k in G if k[1].startswith('k:')]
print('윤곽선 있는 글리프', len(out), '종', sum(G[k]['n'] for k in out), '자 / 윤곽선 없는 (글꼴, GID)', len(noout), '종', sum(G[k]['n'] for k in noout), '자')
mu = [k for k in out if len(G[k]['ucs']) > 1]
print('같은 윤곽선인데 뽑힌 글자가 여러 가지:', len(mu), '종,', sum(G[k]['n'] for k in mu), '자')
for k in mu[:8]:
    g = G[k]; print('   ', k[0], {f'U+{u:04X}{chr(u)!r}': n for u, n in g['ucs'].most_common(4)}, 'gid', dict(g['gids']), {b[:6]: n for b, n in g['books'].items()})
# 거꾸로: 같은 (글꼴, 뽑힌 글자)인데 윤곽선이 여러 가지
rev = collections.defaultdict(set); revn = collections.Counter()
for k in out:
    for u, n in G[k]['ucs'].items():
        rev[(k[0], u)].add(k[1]); revn[(k[0], u)] += n
mr = {k: v for k, v in rev.items() if len(v) > 1}
print('같은 (글꼴, 뽑힌 글자)인데 윤곽선이 여러 가지:', len(mr), '쌍,', sum(revn[k] for k in mr), '자 / 전체 쌍', len(rev))
for k in sorted(mr, key=lambda k: -revn[k])[:10]:
    print('   ', k[0], f'U+{k[1]:04X}{chr(k[1])!r}', '윤곽선', len(mr[k]), '가지', revn[k], '자')
