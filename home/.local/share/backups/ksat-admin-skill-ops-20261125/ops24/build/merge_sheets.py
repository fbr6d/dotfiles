# 새로 만든 견본 폴더를 본 견본 폴더에 합친다.  쓰기: /usr/bin/python3 merge_sheets.py <새 폴더> <본 폴더>
import sys, os, json, shutil
src, dst = sys.argv[1], sys.argv[2]
ms = json.load(open(os.path.join(src, 'manifest.json'))); md = json.load(open(os.path.join(dst, 'manifest.json')))
have = {m['sheet'] for m in md}
n = 0
for m in ms:
    if m['sheet'] in have:
        print('이미 있음, 건너뜀:', m['sheet']); continue
    for ext in ('.png', '.cells.json'):
        shutil.copy2(os.path.join(src, m['sheet'] + ext), os.path.join(dst, m['sheet'] + ext))
    md.append(m); n += 1
json.dump(md, open(os.path.join(dst, 'manifest.json'), 'w'), ensure_ascii=False, indent=1)
print('합침', n, '장 → 모두', len(md), '장')
