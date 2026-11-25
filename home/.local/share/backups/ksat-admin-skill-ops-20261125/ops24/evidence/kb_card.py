import sqlite3, datetime, sys
db = sqlite3.connect('file:/home/leejaeik/.hermes/kanban/boards/ksat-10000/kanban.db?mode=ro', uri=True)
def ts(t):
    return '-' if t is None else datetime.datetime.fromtimestamp(t).strftime('%m-%d %H:%M:%S')
tid = sys.argv[1]
lim = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
t = db.execute('select id,title,status,assignee,model_override,created_at,started_at,completed_at,block_kind,result,body from tasks where id=?', (tid,)).fetchone()
print('ID', t[0], '|', t[1]); print('상태', t[2], t[3], t[4], '만듦', ts(t[5]), '시작', ts(t[6]), '끝', ts(t[7]), 'block', t[8])
print('--- 본문'); print((t[10] or '')[:lim])
print('--- result'); print((t[9] or '')[:lim])
print('--- runs')
for r in db.execute('select id,profile,status,outcome,started_at,ended_at,summary,error from task_runs where task_id=? order by id', (tid,)):
    print('run', r[0], r[1], r[2], r[3], ts(r[4]), ts(r[5])); print('   요약:', (r[6] or '')[:lim]); 
    if r[7]: print('   오류:', r[7][:400])
print('--- 댓글')
for c in db.execute('select id,author,created_at,body from task_comments where task_id=? order by id', (tid,)):
    print('#', c[0], c[1], ts(c[2])); print((c[3] or '')[:lim]); print()
