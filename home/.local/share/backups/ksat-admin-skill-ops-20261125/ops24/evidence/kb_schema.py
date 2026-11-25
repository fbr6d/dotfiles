import sqlite3
db = sqlite3.connect('file:/home/leejaeik/.hermes/kanban/boards/ksat-10000/kanban.db?mode=ro', uri=True)
for name, sql in db.execute("select name, sql from sqlite_master where type='table'"):
    print(name)
    cols = [r[1] for r in db.execute(f'pragma table_info({name})')]
    print('   ', ', '.join(cols))
print(db.execute('select status, count(*) from tasks group by status').fetchall())
