import sqlite3
import os

DB_NAME = 'exam.db'
SQL_FILE = 'init_db.sql'

def init_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print('Old Database Removed!!!')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    with open(SQL_FILE,'r') as f:
        sql_script = f.read()

    cursor.executescript(sql_script)

    conn.commit()
    conn.close()

    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
            