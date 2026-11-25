import sqlite3, time, datetime, re
db = sqlite3.connect('file:/home/leejaeik/.hermes/kanban/boards/ksat-10000/kanban.db?mode=ro', uri=True)
def ts(t):
    if t is None: return '-'
    return datetime.datetime.fromtimestamp(t).strftime('%m-%d %H:%M')
print('== running / ready')
for r in db.execute("select id,title,assignee,status,model_override,started_at,created_at from tasks where status in ('running','ready') order by started_at"):
    print(r[0], r[3], r[2], r[4], ts(r[5]), '|', r[1][:90])
print('== 오늘 15시 이후 run (시작, 끝, 결과)')
t0 = datetime.datetime(2026,11,25,15,0).timestamp()
for r in db.execute("select r.id,r.task_id,r.profile,r.status,r.outcome,r.started_at,r.ended_at,t.title from task_runs r join tasks t on t.id=r.task_id where r.started_at>=? order by r.started_at", (t0,)):
    print(r[0], r[1], r[2], r[3], r[4], ts(r[5]), ts(r[6]), '|', r[7][:70])
