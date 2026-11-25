# 견본 폴더에서 주어진 묶음의 견본을 뺀다(아직 아무도 읽지 않은 것만).  쓰기: /usr/bin/python3 drop_sheets.py <견본 폴더> <묶음> …
import sys, os, json
d = sys.argv[1]; groups = set(sys.argv[2:])
man = json.load(open(os.path.join(d, 'manifest.json')))
keep = []
for m in man:
    if m['group'] in groups:
        rd = os.path.join(os.path.dirname(d.rstrip('/')), 'read', m['sheet'] + '.json')
        if os.path.exists(rd):
            print('이미 읽은 견본이라 그대로 둠:', m['sheet']); keep.append(m); continue
        for ext in ('.png', '.cells.json'):
            fn = os.path.join(d, m['sheet'] + ext)
            if os.path.exists(fn):
                os.remove(fn)
        print('뺌:', m['sheet'])
    else:
        keep.append(m)
json.dump(keep, open(os.path.join(d, 'manifest.json'), 'w'), ensure_ascii=False, indent=1)
print('남은 견본', len(keep))
