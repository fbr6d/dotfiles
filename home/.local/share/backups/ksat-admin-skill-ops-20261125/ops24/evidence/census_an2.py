import json, sys
def hy(o): return 0xE0BC <= o <= 0xEFFF or 0xF100 <= o <= 0xF66E or 0xF784 <= o <= 0xF8F7
fam = json.load(open(sys.argv[1]))
rows = []
for f, a in fam.items():
    pc = {int(k, 16): v for k, v in a['codes'].items() if 0xE000 <= int(k, 16) <= 0xF8FF}
    if pc: rows.append((sum(pc.values()), f, a['pdfs'], a['n'], len(pc), sum(v for k, v in pc.items() if hy(k)), sorted(pc.items(), key=lambda kv: -kv[1])[:5]))
rows.sort(reverse=True)
print('PUA가 있는 글꼴', len(rows), 'PUA 합', sum(r[0] for r in rows))
for r in rows[:int(sys.argv[2])]:
    print(f'{r[1][:28]:28s} PDF {r[2]:3d} 글자 {r[3]:8d} PUA {r[0]:7d} 코드 {r[4]:3d}종 한양구역 {r[5]:7d} | ' + ' '.join(f'{k:04X}({v})' for k, v in r[6]))
