import sqlite3
conn = sqlite3.connect('./data/xiamen_travel.db')
conn.row_factory = sqlite3.Row
attractions = conn.execute('SELECT id, name, open_time, recommended_duration FROM attractions').fetchall()
for a in attractions:
    print(f"ID:{a['id']} 名称:{a['name']} 开放时间:{a['open_time']} 推荐时长:{a['recommended_duration']}")
conn.close()