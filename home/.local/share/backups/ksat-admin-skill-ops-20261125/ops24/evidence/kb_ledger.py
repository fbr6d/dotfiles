import sqlite3, datetime, sys
db = sqlite3.connect('file:/home/leejaeik/.hermes/kanban/boards/ksat-10000/kanban.db?mode=ro', uri=True)
def ts(t):
    return datetime.datetime.fromtimestamp(t).strftime('%m-%d %H:%M:%S')
h, m = map(int, sys.argv[1].split(':'))
lim = int(sys.argv[2])
t0 = datetime.datetime(2026,11,25,h,m).timestamp()
for cid, au, ca, body in db.execute("select id,author,created_at,body from task_comments where task_id='t_729e2d91' and created_at>=? order by id", (t0,)):
    print('#', cid, au, ts(ca)); print((body or '')[:lim]); print()
