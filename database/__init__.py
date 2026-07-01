import sqlite3
import os
import sys
from dotenv import load_dotenv

# 当直接运行 python database/__init__.py 时，
# 把项目根目录加入搜索路径，from database.seed_all 才能找到
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

load_dotenv()

DATABASE_PATH = os.getenv('DATABASE_PATH', './data/xiamen_travel.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA timezone = 'local'")
    return conn

def init_db():
    conn = get_db_connection()
    with open('./database/schema.sql', 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print('[OK] 数据库表创建完成')

if __name__ == '__main__':
    init_db()
    print('----------------------------')
    print('数据库初始化完成！请运行 python database/seed_all.py 注入初始数据')
