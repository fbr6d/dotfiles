"""'뽑힌 글자가 실제 모양과 같은가'를 프로그램이 스스로 가릴 수 있는지 재기 (읽기 전용)"""
import pickle, sys, collections
import numpy as np
sys.argv = ['x', 'gc4_textbook.pkl', '/dev/null']
src = open('shape_match.py').read().split("G = pickle.load(open(sys.argv[1], 'rb'))")[0]
exec(src)
G = pickle.load(open('gc4_textbook.pkl', 'rb'))
idx = collections.defaultdict(list)
for i, r in enumerate(refs): idx[r[0]].append(i)
rows = []
for k, g in G.items():
    if not k[1].startswith('h:') or not g['rec']: continue
    im = raster(g['rec'], g['upm'] or 1000); ve = vec_em(im); vt, geo = vec_tight(im)
    if ve is None or vt is None: continue
    gs = np.exp(-(((GEO - np.array(geo, dtype=np.float32)) ** 2).sum(axis=1)) / 0.02)
    sc = 0.4 * (ME @ ve) + 0.45 * (MT @ vt) + 0.15 * gs
    u = g['ucs'].most_common(1)[0][0]; ch = chr(u)
    best = float(sc.max()); lab = max((float(sc[i]) for i in idx.get(ch, [])), default=None)
    rows.append((k[0], u, g['n'], lab, best))
# 눈으로 확인한 '뽑힌 글자와 실제 모양이 다른' 글리프 (견본 그림에서 읽은 것)
BAD = {('Amsusic-Bunsu', ';'), ('Amsusic-Bunsu', '!'), ('Amsusic-Yakmul', '<'), ('Amsusic-Italic', '_'), ('Amsusic-Bunsu', "'"), ('EHboNB-Italic', ';'), ('EHSusic-Plain', ':'),
       ('Amsusic-Bunsu', '{'), ('Amsusic-Bunsu', '}'), ('Amsusic-Normal', '_'), ('Amsusic-Italic', '^'), ('EHboNB-Italic', '!'), ('Amsusic-Bunsu', '#'), ('Amsusic-Bunsu', '@'), ('EHSusic-Plain', ')'),
       ('Amsusic-Yakmul', 'h'), ('Amsusic-Yakmul', 'p'), ('Amsusic-Yakmul', 'y'), ('Amsusic-Yakmul', 'r'), ('Amsusic-Yakmul', 'D'), ('EHyak-Plain', 'D'), ('EHyak-Plain', 'y'), ('EHyak-Plain', 'b'),
       ('EHboNB-Italic', '2'), ('EHboNB-Italic', '3'), ('EHSusic-Plain', 'A'), ('EHSunm-Plain', '5'), ('EHSunm-Plain', '2'), ('EHRoot-Plain', '1'), ('Amsusic-Math', '3')} | {('Amsusic-Bunsu', d) for d in '0123456789'}
asc = [r for r in rows if r[1] < 0x80]
print('ASCII로 뽑힌 글리프', len(asc), '종', sum(r[2] for r in asc), '자 / 그 가운데 눈으로 다르다고 확인한 것', sum(1 for r in asc if (r[0], chr(r[1])) in BAD), '종', sum(r[2] for r in asc if (r[0], chr(r[1])) in BAD), '자')
for t in (0.90, 0.85, 0.80, 0.75, 0.70):
    ok = [r for r in asc if r[3] is not None and r[3] >= t and r[3] >= r[4] - 0.03]
    bad_in = [r for r in ok if (r[0], chr(r[1])) in BAD]
    print(f'  기준 {t:.2f}(뽑힌 글자 점수가 이 값 이상이고 1등과 0.03 안): 자동 확정 {len(ok)}종({len(ok) * 100 // len(asc)}%) {sum(r[2] for r in ok)}자({sum(r[2] for r in ok) * 100 // sum(r[2] for r in asc)}%), 그 안에 섞인 틀린 것 {len(bad_in)}종 {[(r[0][:12], chr(r[1]), round(r[3], 2)) for r in bad_in][:6]}')
badrows = [r for r in asc if (r[0], chr(r[1])) in BAD]
print('틀린 것들의 뽑힌-글자 점수 분포:', sorted(round(r[3], 2) if r[3] is not None else None for r in badrows if True)[-12:], '최대')
