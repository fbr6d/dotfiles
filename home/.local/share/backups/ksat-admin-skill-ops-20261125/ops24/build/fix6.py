p = 'mk_sheets.py'
s = open(p).read()
old = "                    sheet.paste(cand_panel(chr(c['label']), L), (x0 + 130, y0 + 4))\n"
new = "                    sheet.paste(cand_panel(c.get('cand_text') or chr(c['label']), L), (x0 + 130, y0 + 4))\n"
assert old in s; s = s.replace(old, new)
old = "                if t == 'B':\n                    cj[str(no)]['cand'] = chr(c['label'])\n"
new = "                if t == 'B':\n                    cj[str(no)]['cand'] = c.get('cand_text') or chr(c['label'])\n                    if c.get('rev'):\n                        cj[str(no)]['rev'] = c['rev']\n"
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
