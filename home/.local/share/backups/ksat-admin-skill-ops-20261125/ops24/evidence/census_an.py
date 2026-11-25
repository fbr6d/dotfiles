import json, collections, sys, re
def hy(o): return 0xE0BC <= o <= 0xEFFF or 0xF100 <= o <= 0xF66E or 0xF784 <= o <= 0xF8F7
for fn in sys.argv[1:]:
    rows = [json.loads(l) for l in open(fn)]
    err = [r for r in rows if 'error' in r]
    print(f'== {fn}: PDF {len(rows)}, 오류 {len(err)}, 쪽 {sum(r.get("pages", 0) for r in rows)}, 글자 {sum(r.get("chars", 0) for r in rows)}, 초 합 {round(sum(r["sec"] for r in rows))}')
    for r in err[:3]: print('   오류', r['path'][-60:], r['error'][:100])
    notext = [r for r in rows if 'error' not in r and r.get('chars', 0) < 200]
    print('   글자층이 거의 없는 PDF(200자 미만):', len(notext), [r['path'].split('/')[-1][:40] for r in notext[:4]])
    fam = collections.defaultdict(lambda: dict(pdfs=set(), n=0, pua=0, l1=0, fffd=0, jamo=0, codes=collections.Counter()))
    for r in rows:
        for f, d in r.get('fonts', {}).items():
            a = fam[f]; a['pdfs'].add(r['path']); a['n'] += d['n']
            for c in ('pua', 'l1', 'fffd', 'jamo'): a[c] += d['cat'].get(c, 0)
            for k, v in d['codes'].items(): a['codes'][int(k, 16)] += v
    tot_pua = sum(a['pua'] for a in fam.values())
    print(f'   PUA·수상한 글자가 있는 글꼴 {len(fam)}종, PUA 합 {tot_pua}, FFFD 합 {sum(a["fffd"] for a in fam.values())}, 라틴-1 합 {sum(a["l1"] for a in fam.values())}, 첫가끝 자모 합 {sum(a["jamo"] for a in fam.values())}')
    print('   글꼴 | PDF 수 | 글자 | PUA(코드 종) | 한양 구역 안 PUA | FFFD | 라틴-1 | 자모')
    for f, a in sorted(fam.items(), key=lambda kv: -(kv[1]['pua'] + kv[1]['l1']))[:int(28)]:
        pc = {k: v for k, v in a['codes'].items() if 0xE000 <= k <= 0xF8FF}
        print(f'   {f[:30]:30s} {len(a["pdfs"]):4d} {a["n"]:8d} {a["pua"]:7d}({len(pc):3d}) {sum(v for k, v in pc.items() if hy(k)):7d} {a["fffd"]:6d} {a["l1"]:6d} {a["jamo"]:5d}')
    json.dump({f: {'pdfs': len(a['pdfs']), 'n': a['n'], 'pua': a['pua'], 'codes': {hex(k): v for k, v in a['codes'].items()}} for f, a in fam.items()}, open(fn.replace('.jsonl', '_fam.json'), 'w'), ensure_ascii=False)
