import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "database/exam.db"

username = "admin"
password = "admin123"   # change this
role = "admin"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

password_hash = generate_password_hash(password)

cursor.execute("""
INSERT INTO users (username, password_hash, role, is_temp_password)
VALUES (?, ?, ?, 0)
""", (username, password_hash, role))

conn.commit()
conn.close()

print("✅ Admin user created successfully")
print(f"Username: {username}")
print(f"Password: {password}")
