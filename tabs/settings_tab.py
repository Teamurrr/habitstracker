# tabs/settings_view.py
from flet import Column, Text, ElevatedButton, FilePicker, FilePickerResultEvent, Row, SnackBar
import db
import json
import os

def build_settings_tab(page, refresh_main_callback):
    # File pickers
    export_file_picker = FilePicker()
    import_file_picker = FilePicker()
    
    # Add file pickers to page
    page.overlay.extend([export_file_picker, import_file_picker])
    
    def show_snack_bar(message):
        page.snack_bar = SnackBar(content=Text(message))
        page.snack_bar.open = True
        page.update()

    def on_export_result(e: FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path
            export_data_to_file(file_path)
        else:
            show_snack_bar("Экспорт отменён")

    def on_import_result(e: FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path
            import_data_from_file(file_path)
        else:
            show_snack_bar("Импорт отменён")

    export_file_picker.on_result = on_export_result
    import_file_picker.on_result = on_import_result

    def export_data(e):
        # Let user choose where to save export file
        export_file_picker.save_file(
            dialog_title="Экспорт данных",
            file_name="habits_export.json",
            file_type="json"
        )

    def export_data_to_file(file_path):
        # dump habits and entries to JSON
        import sqlite3
        con = sqlite3.connect(db.DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT id, name, color, start_date, end_date, status, notification_interval FROM habits")
        habits = [dict(zip(["id","name","color","start_date","end_date","status", "notification_interval"], r)) for r in cur.fetchall()]
        cur.execute("SELECT id, habit_id, date, status FROM entries")
        entries = [dict(zip(["id","habit_id","date","status"], r)) for r in cur.fetchall()]
        con.close()
        export = {"habits": habits, "entries": entries}
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export, f, ensure_ascii=False, indent=2)
            show_snack_bar(f"Данные экспортированы в {file_path}")
        except Exception as ex:
            show_snack_bar(f"Ошибка экспорта: {str(ex)}")

    def import_data(e):
        # Let user choose file to import
        import_file_picker.pick_files(
            dialog_title="Импорт данных",
            file_type="json",
            allow_multiple=False
        )

    def import_data_from_file(file_path):
        try:
            if not os.path.exists(file_path):
                show_snack_bar(f"Файл не найден: {file_path}")
                return
            
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            con = db.get_conn()
            cur = con.cursor()
            
            # Clear existing data before import
            cur.execute("DELETE FROM entries")
            cur.execute("DELETE FROM habits")
            
            # Import habits
            for h in data.get("habits", []):
                cur.execute("""
                    INSERT INTO habits (id, name, color, start_date, end_date, status, notification_interval) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    h.get("id"), h.get("name"), h.get("color"), 
                    h.get("start_date"), h.get("end_date"), 
                    h.get("status", 'в процессе'), h.get("notification_interval", "Без уведомлений")
                ))
            
            # Import entries
            for en in data.get("entries", []):
                cur.execute("""
                    INSERT INTO entries (id, habit_id, date, status) 
                    VALUES (?, ?, ?, ?)
                """, (
                    en.get("id"), en.get("habit_id"), 
                    en.get("date"), en.get("status")
                ))
            
            con.commit()
            con.close()
            
            show_snack_bar("Импорт завершён успешно")
            refresh_main_callback()
            
        except json.JSONDecodeError:
            show_snack_bar("Ошибка: файл имеет неверный формат JSON")
        except Exception as ex:
            show_snack_bar(f"Ошибка импорта: {str(ex)}")

    return Column([
        Text("Настройки", size=20, weight="bold"),
        Row([
            ElevatedButton("Экспорт данных", on_click=export_data),
            ElevatedButton("Импорт данных", on_click=import_data),
        ]),
        Text("Экспорт: сохраняет все привычки и записи в JSON файл", size=12),
        Text("Импорт: загружает данные из JSON файла (заменяет текущие)", size=12),
    ])