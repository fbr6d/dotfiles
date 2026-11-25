# 한양 PUA 표를 도구용 JSON으로 옮긴다.  쓰기: /usr/bin/python3 mk_hanyang.py <hanyang_table_composed.json> <glyph 폴더>
import sys, json, os
src = json.load(open(sys.argv[1], encoding='utf-8'))
m = {('%04X' % int(k, 16)): v for k, v in src.items()}
d = {'version': 1,
     'source': 'hypua2jamo 0.7 (LGPL-3.0-or-later) 의 한양 PUA → 첫가끝(조합형) 표에서 뽑음',
     'note': '참고용 표. 이 표만으로 글자를 바꾸지 않는다(같은 코드가 다른 글꼴에서는 기호다). 실제 변환은 tbl_ko.json 의 기준 모양이 맞을 때만 한다. 값은 유니코드 첫가끝 자모이며 NFC·NFKC를 걸지 않는다.',
     'count': len(m), 'map': dict(sorted(m.items()))}
out = os.path.join(sys.argv[2], 'hanyang_pua.json')
json.dump(d, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('한양 표', len(m), '코드 →', out, os.path.getsize(out) // 1024, 'KB')
