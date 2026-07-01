import requests
import sqlite3

conn = sqlite3.connect('data/xiamen_travel.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM comments WHERE user_id = 1")
rows = cursor.fetchall()
print("DB before update:")
for row in rows:
    print(f"  {row}")

login_r = requests.post('http://127.0.0.1:5000/api/auth/login', json={'username':'admin','password':'admin123'})
token = login_r.json()['data']['access_token']

result = requests.put('http://127.0.0.1:5000/api/auth/profile', json={'nickname':'新昵称测试2'}, headers={'Authorization':f'Bearer {token}'})
print(f"Profile update result: {result.json()['message']}")

cursor.execute("SELECT * FROM comments WHERE user_id = 1")
rows = cursor.fetchall()
print("DB after update:")
for row in rows:
    print(f"  {row}")

conn.close()
