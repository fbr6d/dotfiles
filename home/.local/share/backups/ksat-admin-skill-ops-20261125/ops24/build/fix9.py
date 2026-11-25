p = 'assemble.py'
s = open(p).read()

# 1) 미쿠가 다시 보고 고친 값(fixes.json)을 읽기 결과 위에 덮는다
old = """    tables = collections.defaultdict(list)
    stat = collections.Counter()
    problems = []
"""
new = """    tables = collections.defaultdict(list)
    stat = collections.Counter()
    problems = []
    fixes = {}
    ff = os.path.join(ops, 'fixes.json')
    if os.path.exists(ff):
        fixes = json.load(open(ff, encoding='utf-8'))
    used_fix = 0
"""
assert old in s; s = s.replace(old, new)
old = """            e = {'id': c['id'], 'sheet': '%s#%s' % (name, no), 'src': src, 'n': c['n'], 'npdf': c['npdf']}
"""
new = """            e = {'id': c['id'], 'sheet': '%s#%s' % (name, no), 'src': src, 'n': c['n'], 'npdf': c['npdf']}
            fx = fixes.get('%s#%s' % (name, no))
            if fx is not None:
                r = dict(fx); r.pop('same', None)
                if r.pop('use_cand', False):
                    r.update(text=cinfo.get('cand', ''), status='확정'); r.setdefault('role', 'char')
                t_eff = 'A'; e['src'] = src + '+고침'; used_fix += 1
            else:
                t_eff = t
"""
assert old in s; s = s.replace(old, new)
old = """            if t in ('B', 'C') and r.get('same') is True:
                e.update(text=cinfo['cand'], status='확정', pos=r.get('pos', 'base') if t == 'B' else 'base', role='char', desc=r.get('desc', ''))
            elif t == 'C':
"""
new = """            if t_eff in ('B', 'C') and r.get('same') is True:
                e.update(text=cinfo['cand'], status='확정', pos=r.get('pos', 'base') if t == 'B' else 'base', role='char', desc=r.get('desc', ''))
            elif t_eff == 'C':
"""
assert old in s; s = s.replace(old, new)

# 2) 옛한글 글꼴 목록(근거 자료)
old = """    print('읽기 없는 견본', stat['읽기 없는 견본'], '· 문제', len(problems))
"""
new = """    if 'KO' in tables:
        fc = collections.defaultdict(lambda: [0, 0, 0, 0])
        for e in tables['KO']:
            for cn, u, n in e['keys']:
                f = fc[cn]
                if e['status'] == '미확정':
                    f[2] += 1; f[3] += n
                else:
                    f[0] += 1; f[1] += n
        fl = [{'font': cn, 'verified_glyphs': v[0], 'verified_chars': v[1], 'unverified_glyphs': v[2], 'unverified_chars': v[3]} for cn, v in sorted(fc.items(), key=lambda kv: -kv[1][1])]
        json.dump({'version': 1, 'made': today,
                   'note': '옛한글(한양 PUA) 글리프가 실제로 확인된 글꼴 목록(근거 자료). 도구는 글꼴 이름이 아니라 글리프 모양으로 판정한다. verified = 한양 표 후보와 글리프 그림이 같은 글자임을 눈으로 확인한 것.',
                   'fonts': fl}, open(os.path.join(outdir, 'hanyang_fonts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('옛한글 글꼴 목록', len(fl), '종 → hanyang_fonts.json')
    print('읽기 없는 견본', stat['읽기 없는 견본'], '· 고친 값 적용', used_fix, '/', len(fixes), '· 문제', len(problems))
"""
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
