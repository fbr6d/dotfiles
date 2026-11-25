import sqlite3, datetime, re, sys
db = sqlite3.connect('file:/home/leejaeik/.hermes/kanban/boards/ksat-10000/kanban.db?mode=ro', uri=True)
def ts(t):
    return '-' if t is None else datetime.datetime.fromtimestamp(t).strftime('%m-%d %H:%M')
pat = re.compile(r'PUA|옛한글|사적 ?영역|대조 ?불가|미확인 기호|글리프|첫가끝')
t0 = datetime.datetime(2026,11,25,0,0).timestamp()
def sents(txt):
    out = []
    for s in re.split(r'(?<=[.!?요다음])\s+|\n', txt or ''):
        if pat.search(s):
            out.append(s.strip()[:330])
    return out
seen = 0
for tid, title, status in db.execute('select id,title,status from tasks where created_at>=? order by created_at', (t0,)):
    lines = []
    for rid, st, oc, sa, summ in db.execute('select id,status,outcome,started_at,summary from task_runs where task_id=? order by id', (tid,)):
        for s in sents(summ):
            lines.append(f'  run{rid}({oc},{ts(sa)}): {s}')
    for cid, au, ca, body in db.execute('select id,author,created_at,body from task_comments where task_id=? order by id', (tid,)):
        if au == 'ksat-administrator':
            for s in sents(body)[:2]:
                lines.append(f'  총괄#{cid}({ts(ca)}): {s}')
    if lines:
        seen += 1
        print(tid, status, '|', title[:70])
        print('\n'.join(lines[:5]))
print('카드', seen)
