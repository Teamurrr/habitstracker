# db.py
import sqlite3
import os
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "habits.db")

def ensure_db():
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # habits: id, name, color, start_date, end_date, description
    cur.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        color TEXT NOT NULL,
        start_date TEXT,  -- YYYY-MM-DD or NULL
        end_date TEXT,
        description TEXT
    )
    """)
    # entries: id, habit_id, date (YYYY-MM-DD), status (in_progress, done, skipped, overdue)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
    )
    """)
    con.commit()
    con.close()

def get_conn():
    ensure_db()
    return sqlite3.connect(DB_PATH)

def add_habit(habit: Dict[str, Any]) -> int:
    con = get_conn()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO habits (name, color, start_date, end_date, description) VALUES (?, ?, ?, ?, ?)",
        (habit["name"], habit["color"], habit.get("start_date"), habit.get("end_date"), habit.get("description"))
    )
    hid = cur.lastrowid
    con.commit()
    con.close()
    return hid

def update_habit(habit_id: int, fields: Dict[str, Any]):
    con = get_conn()
    cur = con.cursor()
    sets = ", ".join([f"{k}=?" for k in fields.keys()])
    params = list(fields.values()) + [habit_id]
    cur.execute(f"UPDATE habits SET {sets} WHERE id=?", params)
    con.commit()
    con.close()

def delete_habit(habit_id: int):
    con = get_conn()
    cur = con.cursor()
    cur.execute("DELETE FROM habits WHERE id=?", (habit_id,))
    cur.execute("DELETE FROM entries WHERE habit_id=?", (habit_id,))
    con.commit()
    con.close()

def get_all_habits() -> List[Dict]:
    con = get_conn()
    cur = con.cursor()
    cur.execute("SELECT id, name, color, start_date, end_date, description FROM habits")
    rows = cur.fetchall()
    con.close()
    return [{"id": r[0], "name": r[1], "color": r[2], "start_date": r[3], "end_date": r[4], "description": r[5]} for r in rows]

def get_habit(hid: int) -> Dict:
    con = get_conn()
    cur = con.cursor()
    cur.execute("SELECT id, name, color, start_date, end_date, description FROM habits WHERE id=?", (hid,))
    r = cur.fetchone()
    con.close()
    if not r: return None
    return {"id": r[0], "name": r[1], "color": r[2], "start_date": r[3], "end_date": r[4], "description": r[5]}

def set_entry(habit_id: int, date: str, status: str):
    con = get_conn()
    cur = con.cursor()
    cur.execute("SELECT id FROM entries WHERE habit_id=? AND date=?", (habit_id, date))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE entries SET status=? WHERE id=?", (status, row[0]))
    else:
        cur.execute("INSERT INTO entries (habit_id, date, status) VALUES (?, ?, ?)", (habit_id, date, status))
    con.commit()
    con.close()

def get_entries_between(start_date: str, end_date: str) -> List[Dict]:
    con = get_conn()
    cur = con.cursor()
    cur.execute("SELECT id, habit_id, date, status FROM entries WHERE date BETWEEN ? AND ?", (start_date, end_date))
    rows = cur.fetchall()
    con.close()
    return [{"id": r[0], "habit_id": r[1], "date": r[2], "status": r[3]} for r in rows]

def get_entries_for_month(year: int, month: int):
    start = f"{year:04d}-{month:02d}-01"
    # naive end - will be used by caller to compute last day or use SQLite date functions; for simplicity fetch month prefix
    con = get_conn()
    cur = con.cursor()
    like = f"{year:04d}-{month:02d}-%"
    cur.execute("SELECT id, habit_id, date, status FROM entries WHERE date LIKE ?", (like,))
    rows = cur.fetchall()
    con.close()
    return [{"id": r[0], "habit_id": r[1], "date": r[2], "status": r[3]} for r in rows]
