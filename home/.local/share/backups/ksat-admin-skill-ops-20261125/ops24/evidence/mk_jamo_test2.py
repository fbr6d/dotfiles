import unicodedata
pure = ['\u1103\u1172\u11f0', '\u1100\u1161\u11ff', '\u110b\u119e\u11af', '\u1112\u119e', '\u1140\u119e\u11b8', '\u1109\u1173\u11f0', '\u1107\u1161\u11eb', '\u1100\u1173\u11f9']   # 듕 가ᇿ ᄋᆞᆯ ᄒᆞ ᅀᆞᆸ 스ᇰ 바ᇫ 그ᇹ
rows = []
for name, fam in (('Pretendard', "Pretendard, sans-serif"), ('Noto Serif CJK KR', "'Noto Serif CJK KR'"), ('Noto Sans CJK KR', "'Noto Sans CJK KR'")):
    a = ' '.join(pure); b = ' '.join(unicodedata.normalize('NFC', s) for s in pure)
    rows.append(f'<div style="font-family:{fam}"><small>{name} · 첫가끝 그대로:</small> {a}</div>')
    rows.append(f'<div style="font-family:{fam}"><small>{name} · NFC를 건 꼴:</small> {b}</div>')
open('jamo_test2.html', 'w', encoding='utf-8').write('<!doctype html><meta charset="utf-8"><style>body{font-size:40px;margin:20px;line-height:1.6} small{font-size:15px;color:#555;display:inline-block;width:330px}</style>' + '\n'.join(rows))
print([[hex(ord(c)) for c in unicodedata.normalize('NFC', s)] for s in pure[:2]])
