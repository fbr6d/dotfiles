# 표 항목 가운데 '읽은 글자'와 '글자층 코드'가 서로 헷갈리기 쉬운 짝인 것을 찾는다(AI 없음).
# 쓰기: /usr/bin/python3 an_mix.py <표 폴더> [자세히 볼 견본#칸 …]
import sys, os, json, collections
tdir = sys.argv[1]; want = set(sys.argv[2:])
CLS = ['Il1|∣Ⅰǀ', 'O0o○οΟ', 'xX×χ', 'vVνυ', 'wWω', 'pPρ', 'aα', 'Bβ', 'kKκ', 'cC', 'sS', 'zZ', 'uU', '-−–―_‐', '·.•∙⋅', "'′’‘`", '"″”“', '~∼～', ':∶', '<〈⟨', '>〉⟩', '[〔', ']〕', '/∕⁄', '*∗', '^∧', 'rγ', 'nη', 'tτ', 'yγ', 'dδ∂', 'eε', 'fƒ', 'iι', 'EΕ', 'AΑΛΔ', 'DΔ', 'HΗ', 'MΜ', 'NΝ', 'TΤ', 'YΥ', 'ZΖ', 'qg9', 'b6', 'S5', 'Z2', 'gq']
cls = collections.defaultdict(set)
for i, s in enumerate(CLS):
    for ch in s:
        cls[ch].add(i)
rel = collections.defaultdict(lambda: [0, 0])     # 글꼴 → [ASCII 코드 글리프 가운데 읽기가 코드와 같은 수, 전체]
ents = []
for fn in sorted(os.listdir(tdir)):
    if not (fn.startswith('tbl_') and fn.endswith('.json')):
        continue
    d = json.load(open(os.path.join(tdir, fn), encoding='utf-8'))
    for e in d['entries']:
        ents.append((d['family'], e))
        if e['status'] == '미확정':
            continue
        for cn, u, n in e.get('keys', []):
            u = int(u, 16)
            if 0x21 <= u <= 0x7E:
                rel[cn][1] += 1
                if e['text'] == chr(u):
                    rel[cn][0] += 1
out = []
for fam, e in ents:
    if e['sheet'] in want:
        print('▶', fam, e['sheet'], repr(e['text']), e.get('pos'), e['status'], '| keys:', [(cn, u, n, '%d/%d' % tuple(rel[cn])) for cn, u, n in e.get('keys', [])][:12])
    if e['status'] == '미확정' or len(e['text']) != 1:
        continue
    T = e['text']
    for cn, u, n in e.get('keys', []):
        K = chr(int(u, 16))
        if K != T and cls.get(K) and cls.get(T) and (cls[K] & cls[T]):
            out.append((fam, e['sheet'], T, K, cn, n, rel[cn][0], rel[cn][1]))
print('읽은 글자와 글자층 코드가 헷갈리는 짝인 (항목, 글꼴) 수:', len(out), '· 글자 수', sum(o[5] for o in out))
by = collections.Counter()
for o in out:
    by[(o[0], o[2], o[3])] += o[5]
print('가족·읽기·코드별 글자 수(많은 순):')
for k, v in by.most_common(70):
    print('   %-9s 읽기 %s ← 코드 %s  %d자' % (k[0], k[1], k[2], v))
json.dump(out, open('an_mix.json', 'w'), ensure_ascii=False)
