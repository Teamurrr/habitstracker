# tabs/settings_view.py
from flet import Column, Text, ElevatedButton, FilePicker, FilePickerResultEvent
import db
import json
import os

def build_settings_tab(page, refresh_main_callback):
    # Export / Import buttons
    def export_data(e):
        # dump habits and entries to JSON
        import sqlite3
        con = sqlite3.connect(db.DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT id, name, color, start_date, end_date, status FROM habits")
        habits = [dict(zip(["id","name","color","start_date","end_date","status"], r)) for r in cur.fetchall()]
        cur.execute("SELECT id, habit_id, date, status FROM entries")
        entries = [dict(zip(["id","habit_id","date","status"], r)) for r in cur.fetchall()]
        con.close()
        export = {"habits": habits, "entries": entries}
        path = os.path.join(os.path.dirname(__file__), "..", "data", "export.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(export, f, ensure_ascii=False, indent=2)
        page.snack_bar = None
        page.show_snack_bar("Данные экспортированы в data/export.json")
        page.update()

    def import_data(e):
        # simple import from data/export.json (overwrites)
        path = os.path.join(os.path.dirname(__file__), "..", "data", "export.json")
        if not os.path.exists(path):
            page.show_snack_bar("Нет файла data/export.json")
            page.update()
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        con = db.get_conn()
        cur = con.cursor()
        # naive import: append habits, entries
        for h in data.get("habits", []):
            cur.execute("INSERT INTO habits (name, color, start_date, end_date, status) VALUES (?, ?, ?, ?, ?)",
                (h.get("name"), h.get("color"), h.get("start_date"), h.get("end_date"), h.get("status", 'в процессе')))
        con.commit()
        for en in data.get("entries", []):
            cur.execute("INSERT OR IGNORE INTO entries (habit_id, date, status) VALUES (?, ?, ?)",
                        (en.get("habit_id"), en.get("date"), en.get("status")))
        con.commit()
        con.close()
        page.show_snack_bar("Импорт завершён")
        page.update()
        refresh_main_callback()

    return Column([Text("Настройки"), ElevatedButton("Экспорт данных", on_click=export_data), ElevatedButton("Импорт данных", on_click=import_data)])
