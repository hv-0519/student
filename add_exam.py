import sqlite3

# 1. Connect to the database
conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

# 2. Define the exam data (Title, Duration, Total Marks, Max Attempts)
exams_to_add = [
    ('Python Basics', 30, 50, 3),
    ('Advanced Java', 60, 100, 2),
    ('Database Management', 45, 75, 3),
    ('Web Development', 90, 100, 5),
    ('Data Structures', 120, 100, 1)
]

# 3. Execute the insert query
try:
    cursor.execute('''
        INSERT INTO exams (title, duration_minutes, total_marks, max_attempts)
        VALUES (?, ?, ?, ?)
    ''', exams_to_add)
    
    conn.commit()
    print(f"Successfully inserted {cursor.rowcount} exam records.")
except sqlite3.IntegrityError as e:
    print(f"Error: {e} (Check for duplicate titles or constraint violations)")
finally:
    conn.close()