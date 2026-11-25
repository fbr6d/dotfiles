import json, os, collections
O = os.path.dirname(os.path.abspath(__file__))
man = json.load(open(os.path.join(O, 'sheets', 'manifest.json')))
c = collections.defaultdict(lambda: [0, 0, 0])
for m in man:
    k = (m['group'], m['type']); c[k][0] += 1; c[k][1] += m['cells']; c[k][2] = max(c[k][2], m['bytes'])
tot = [0, 0]
for k, v in sorted(c.items()):
    print(k, '견본', v[0], '장, 칸', v[1], ', 가장 큰 파일', v[2]); tot[0] += v[0]; tot[1] += v[1]
print('합계 견본', tot[0], '장, 칸', tot[1], '| 180KB 넘는 것', sum(1 for m in man if m['bytes'] > 180000))
