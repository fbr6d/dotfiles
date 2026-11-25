import sqlite3, re, collections
db = sqlite3.connect('file:/home/leejaeik/.hermes/kanban/boards/ksat-10000/kanban.db?mode=ro', uri=True)
pat = re.compile(r'옛글자|옛 글자|자형|기호 관측|관측12원키|관측14원키|글리프|PUA')
tot = collections.Counter(); cards = set()
for tid, title, prof, sa, ea in db.execute('select t.id, t.title, r.profile, r.started_at, r.ended_at from task_runs r join tasks t on t.id=r.task_id where r.started_at is not null and r.ended_at is not null'):
    if pat.search(title or ''):
        m = (ea - sa) / 60
        tot[prof] += m; cards.add((tid, title[:44]))
print('제목에 옛글자·자형·기호 관측이 든 카드', len(cards), '장, 실행 분:', {k: round(v) for k, v in tot.items()}, '합', round(sum(tot.values())))
for c in sorted(cards)[:14]: print('  ', c)
# 오늘 수학 기호 관측 줄
t = 0
for tid in ('t_0d2cefb0', 't_795d8f9e', 't_9c4f22bc', 't_dd5160ae', 't_0c8ca0d2', 't_8d124e3f'):
    for sa, ea in db.execute('select started_at, ended_at from task_runs where task_id=? and ended_at is not null', (tid,)): t += (ea - sa) / 60
print('11-25 수학 공통수학1 기호 관측 줄(관측2·대조2·보완1·재확인1) 실행 분 합:', round(t))
