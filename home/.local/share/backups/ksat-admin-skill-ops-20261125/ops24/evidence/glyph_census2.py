"""수식 글꼴 글리프 전수 2판: (글꼴 기본 이름, 글리프 열쇠)별 윤곽선 해시·뽑힌 글자·출현 수 (읽기 전용)
열쇠 = TrueType 계열은 글리프 번호(GID), CFF(Type1C)는 글리프 이름."""
import collections, hashlib, io, json, pickle, re, sys, time
import pymupdf
from fontTools.ttLib import TTFont
from fontTools.cffLib import CFFFontSet
from fontTools.pens.recordingPen import RecordingPen
from fontTools import agl
PAT = re.compile(sys.argv[1]); outp = sys.argv[2]; paths = sys.argv[3:]
class F:
    def __init__(self, buf, ext):
        self.ext = ext; self.ok = True; self.memo = {}
        try:
            if ext == 'cff':
                cff = CFFFontSet(); cff.decompile(io.BytesIO(buf), None)
                self.top = cff[0]; self.names = list(self.top.charset); self.cs = self.top.CharStrings
            else:
                self.tt = TTFont(io.BytesIO(buf), lazy=False)
                self.names = self.tt.getGlyphOrder(); self.gs = self.tt.getGlyphSet()
        except Exception as e:
            self.ok = False
    def rec(self, gid):
        if gid in self.memo: return self.memo[gid]
        r = (None, None)
        if self.ok and gid < len(self.names):
            nm = self.names[gid]; pen = RecordingPen()
            try:
                (self.cs[nm] if self.ext == 'cff' else self.gs[nm]).draw(pen)
                r = (nm, pen.value)
            except Exception:
                r = (nm, None)
        self.memo[gid] = r
        return r
def h(val):
    s = repr([(op, tuple(tuple(round(c, 1) for c in pt) if pt is not None else None for pt in pts)) for op, pts in val])
    return hashlib.md5(s.encode()).hexdigest()[:12]
G = {}
t0 = time.time()
stat = collections.Counter()
for path in paths:
    book = path.split('/')[-1]
    doc = pymupdf.open(path); cache = {}
    for pno in range(len(doc)):
        page = doc[pno]
        base2x = collections.defaultdict(list)
        for xref, ext, typ, base, rname, enc, _ in page.get_fonts(full=True):
            b = re.sub(r'^[A-Z]{6}\+', '', base)
            if PAT.search(b): base2x[b].append(xref)
        for sp in page.get_texttrace():
            base = sp['font']
            if not PAT.search(base): continue
            objs = []
            for x in base2x.get(base, []):
                if x not in cache:
                    try:
                        bn, ext, typ, buf = doc.extract_font(x)
                        cache[x] = F(buf, ext) if buf else None
                    except Exception:
                        cache[x] = None
                if cache[x] is not None and cache[x].ok: objs.append(cache[x])
            for ucs, gid, org, bbox in sp['chars']:
                key = gid; rec = None; kind = 'tt'
                cffs = [o for o in objs if o.ext == 'cff']
                if cffs and len(cffs) == len(objs):
                    kind = 'cff'; key = None
                    for o in cffs:
                        nm, r = o.rec(gid)
                        if nm is None: continue
                        try: u = agl.toUnicode(nm)
                        except Exception: u = ''
                        if u == chr(ucs) or (key is None and len(cffs) == 1):
                            key = nm; rec = r; break
                    if key is None:
                        key = f'?gid{gid}/u{ucs:04X}'; stat['cff 이름 못 찾음'] += 1
                else:
                    for o in objs:
                        if o.ext == 'cff': continue
                        nm, r = o.rec(gid)
                        if r: rec = r; break
                    if rec is None: stat['tt 윤곽선 못 찾음(빈 글리프 포함)'] += 1
                k = (base, key)
                g = G.get(k)
                if g is None:
                    g = G[k] = {'n': 0, 'kind': kind, 'books': collections.Counter(), 'ucs': collections.Counter(), 'hash': collections.Counter(), 'occ': [], 'rec': None, 'norec': 0, 'zero_w': 0}
                g['n'] += 1; g['books'][book] += 1; g['ucs'][ucs] += 1
                if bbox[2] - bbox[0] < 0.01: g['zero_w'] += 1
                if rec:
                    g['hash'][h(rec)] += 1
                    if g['rec'] is None: g['rec'] = rec
                else:
                    g['norec'] += 1
                if len(g['occ']) < 3: g['occ'].append((book, pno, tuple(bbox), sp['size']))
    print(f'{book}: {len(doc)}쪽, 글꼴 객체 {len(cache)}, 누적 열쇠 {len(G)}, {round(time.time()-t0)}s', flush=True)
pickle.dump(G, open(outp, 'wb'))
print(dict(stat))
fam = collections.defaultdict(lambda: collections.Counter())
for (base, key), g in G.items():
    f = fam[base]
    f['글리프'] += 1; f['글자'] += g['n']
    f['윤곽선 둘 이상'] += (len(g['hash']) > 1); f['윤곽선 없음'] += (len(g['hash']) == 0)
    f['뽑힌 글자 둘 이상'] += (len(g['ucs']) > 1); f['여러 책'] += (len(g['books']) > 1)
print(f'{"글꼴":24s} 글리프  글자수  윤곽둘↑ 윤곽없음 글자둘↑ 여러책')
for base, f in sorted(fam.items(), key=lambda kv: -kv[1]['글자']):
    print(f'{base[:24]:24s} {f["글리프"]:5d} {f["글자"]:7d} {f["윤곽선 둘 이상"]:6d} {f["윤곽선 없음"]:7d} {f["뽑힌 글자 둘 이상"]:6d} {f["여러 책"]:5d}')
print('합계: 글꼴', len(fam), '열쇠', len(G), '글자', sum(g['n'] for g in G.values()), '윤곽선 둘 이상', sum(len(g['hash']) > 1 for g in G.values()), '윤곽선 없음', sum(len(g['hash']) == 0 for g in G.values()))
