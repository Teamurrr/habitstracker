import sqlite3

# Создаём базу и таблицу, если её ещё нет
conn = sqlite3.connect("habits.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    color TEXT,
    start_date TEXT,
    end_date TEXT,
    status TEXT CHECK(status IN ('в процессе', 'выполнено', 'заброшено')) NOT NULL DEFAULT 'в процессе'
)
""")

conn.commit()
conn.close()

print("База данных и таблица готовы ✅")
