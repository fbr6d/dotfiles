import sqlite3, datetime, re, collections
db = sqlite3.connect('file:/home/leejaeik/.hermes/kanban/boards/ksat-10000/kanban.db?mode=ro', uri=True)
def ts(t):
    return '-' if t is None else datetime.datetime.fromtimestamp(t).strftime('%m-%d %H:%M')
pat = re.compile(r'PUA|옛한글|사적 ?영역|사용자 ?정의 ?영역|대조 ?불가|미확인 기호|글리프|첫가끝|U\+E[0-9A-F]{3}|U\+F[0-8][0-9A-F]{2}')
hit = collections.defaultdict(lambda: collections.Counter())
first = {}
for tid, title, body, status in db.execute('select id,title,body,status from tasks'):
    for src, txt in (('title', title or ''), ('body', body or '')):
        n = len(pat.findall(txt))
        if n: hit[tid][src] += n
for tid, body, ca in db.execute('select task_id, body, created_at from task_comments'):
    n = len(pat.findall(body or ''))
    if n: hit[tid]['comment'] += n
for tid, summ, sa in db.execute('select task_id, summary, started_at from task_runs'):
    n = len(pat.findall(summ or ''))
    if n: hit[tid]['run'] += n
rows = []
for tid, c in hit.items():
    t = db.execute('select title,status,assignee,created_at,completed_at from tasks where id=?', (tid,)).fetchone()
    rows.append((t[3], tid, t[1], t[2], t[0], dict(c)))
rows.sort()
print('카드 수', len(rows))
st = collections.Counter(r[2] for r in rows)
print('상태별', dict(st))
for ca, tid, status, asg, title, c in rows:
    print(ts(ca), tid, status, asg, '|', title[:60], '|', c)
