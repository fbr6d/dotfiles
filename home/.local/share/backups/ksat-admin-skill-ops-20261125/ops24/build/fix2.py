p = 'mk_cells.py'
s = open(p).read()
old = """                ls = best[chr(u)]
                c['label_score'] = ls
                ok = ls >= 0.80 and ls >= top - 0.03 and u == c['label']
"""
new = """                ls = best[chr(u)]
                c['label_score'] = ls
                c['label_rank'] = 1 + sum(1 for ch, v in best.items() if v > ls)
                ok = ls >= TH_SCORE and ls >= top - TH_GAP and u == c['label']
"""
assert old in s
s = s.replace(old, new)
s = s.replace("BAD = ('noembed', 'nolink', 'ambig', 'norender')", "BAD = ('noembed', 'nolink', 'ambig', 'norender')\nTH_SCORE, TH_GAP = 0.80, 0.03")
open(p, 'w').write(s)
print('ok')
