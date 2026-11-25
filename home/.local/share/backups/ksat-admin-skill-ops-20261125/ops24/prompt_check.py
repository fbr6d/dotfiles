import sqlite3, re
p = open('prompt_draft.txt', encoding='utf-8').read()
print('글자 수', len(p), '(1,990 아래여야 함)')
db = sqlite3.connect('file:/home/leejaeik/.hermes/kanban/boards/ksat-10000/kanban.db?mode=ro', uri=True)
for tid in re.findall(r't_[0-9a-f]{8}', p):
    r = db.execute('select status, title from tasks where id=?', (tid,)).fetchone()
    print(' 카드', tid, 'OK' if r else 'NG', r)
ref = open('/home/leejaeik/.hermes/profiles/ksat-administrator/skills/ksat-collaboration/references/source-grounded-wiki.md', encoding='utf-8').read()
print(' 스킬 절 이름', 'OK' if '### 원문 위치키로 추출·판독 근거를 대사한다' in ref else 'NG')
import os
for f in ('tools/pdf_glyph_text.py', 'tools/glyph/README.md'):
    print(' 도구 파일', f, '있음' if os.path.exists('/home/leejaeik/Projects/ksat-10000/' + f) else '아직 없음(마스터 OK 뒤 만듦)')
for s in ('207권', '17,793쪽', '36,643자', '41%'):
    print(' 수치', s, 'OK' if s in open('evidence/findings.md', encoding='utf-8').read().replace('40.9%', '41%') else '확인 필요')
