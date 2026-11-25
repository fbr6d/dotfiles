"""raw PDF 글꼴별 글자 통계 전수(선택한 묶음) — 읽기 전용, 결과는 scratch의 JSONL"""
import collections, json, os, re, sys, time
from multiprocessing import Pool
import pymupdf
R = '/home/leejaeik/Projects/ksat-10000/raw/수능자료/'
MATHPAT = re.compile(r'hwpeq|hancomeq|math|susic|^EH|^Kab|symbol|euclid|mtextra|^MT|cmsy|cmmi|cmex|msam|msbm', re.I)
def cat(u):
    if 0xAC00 <= u <= 0xD7A3 or 0x3131 <= u <= 0x318E: return 'ko'
    if u < 0x80: return 'ascii'
    if 0xE000 <= u <= 0xF8FF: return 'pua'
    if 0x80 <= u <= 0xFF: return 'l1'
    if u == 0xFFFD: return 'fffd'
    if 0x1100 <= u <= 0x11FF or 0xA960 <= u <= 0xA97F or 0xD7B0 <= u <= 0xD7FF: return 'jamo'
    return 'etc'
def one(path):
    t0 = time.time()
    out = {'path': path[len(R):]}
    try:
        doc = pymupdf.open(path)
        out['pages'] = len(doc); out['producer'] = doc.metadata.get('producer'); out['creator'] = doc.metadata.get('creator')
        fonts = {}
        for pno in range(len(doc)):
            for sp in doc[pno].get_texttrace():
                f = re.sub(r'^[A-Z]{6}\+', '', sp['font'])
                try: f = f.encode('latin-1').decode('cp949')
                except Exception: pass
                d = fonts.get(f)
                if d is None:
                    d = fonts[f] = {'n': 0, 'cat': collections.Counter(), 'codes': collections.Counter()}
                keep = bool(MATHPAT.search(f))
                for ucs, gid, org, bbox in sp['chars']:
                    c = cat(ucs); d['n'] += 1; d['cat'][c] += 1
                    if c in ('pua', 'l1', 'fffd', 'jamo') or keep:
                        d['codes'][ucs] += 1
        out['fonts'] = {f: {'n': d['n'], 'cat': dict(d['cat']), 'codes': {f'{k:04X}': v for k, v in d['codes'].items()}} for f, d in fonts.items() if d['codes']}
        out['nfonts'] = len(fonts); out['chars'] = sum(d['n'] for d in fonts.values())
    except Exception as e:
        out['error'] = f'{type(e).__name__}: {e}'
    out['sec'] = round(time.time() - t0, 1)
    return out
if __name__ == '__main__':
    lst = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
    outp = sys.argv[2]
    done = set()
    if os.path.exists(outp):
        for l in open(outp):
            try: done.add(json.loads(l)['path'])
            except Exception: pass
    todo = [p for p in lst if p[len(R):] not in done]
    print('대상', len(lst), '남은 것', len(todo), flush=True)
    t0 = time.time()
    with Pool(int(sys.argv[3]) if len(sys.argv) > 3 else 8) as pool, open(outp, 'a') as fo:
        for i, o in enumerate(pool.imap_unordered(one, todo, chunksize=1)):
            fo.write(json.dumps(o, ensure_ascii=False) + '\n'); fo.flush()
            if (i + 1) % 50 == 0:
                print(i + 1, round(time.time() - t0), 's', flush=True)
    print('끝', len(todo), round(time.time() - t0), 's', flush=True)
