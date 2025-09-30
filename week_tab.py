import flet as ft
import sqlite3
from datetime import date, timedelta

DB_NAME = "habits.db"

# -------------------------------
# Работа с БД
# -------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            color TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_habit(title, description, color, start_date, end_date, status="в процессе"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO habits (title, description, color, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, description, color, start_date, end_date, status))
    conn.commit()
    conn.close()

def get_habits():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM habits")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_habit(habit_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habits WHERE id=?", (habit_id,))
    conn.commit()
    conn.close()

def update_status(habit_id, new_status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE habits SET status=? WHERE id=?", (new_status, habit_id))
    conn.commit()
    conn.close()

# -------------------------------
# Интерфейс Flet
# -------------------------------
def build_week_tab(page: ft.Page):
    today = date.today()
    selected_day = today

    # Инициализация базы данных
    init_db()

    # Поля ввода для добавления привычки
    title_input = ft.TextField(label="Название привычки")
    desc_input = ft.TextField(label="Описание")
    color_input = ft.Dropdown(
        label="Цвет",
        options=[
            ft.dropdown.Option("Красный"),
            ft.dropdown.Option("Зелёный"),
            ft.dropdown.Option("Синий"),
            ft.dropdown.Option("Жёлтый"),
        ]
    )
    start_input = ft.TextField(label="Дата начала (ГГГГ-ММ-ДД)")
    end_input = ft.TextField(label="Дедлайн (ГГГГ-ММ-ДД)")

    habit_list = ft.Column(expand=True)

    # Список кнопок для дней недели
    day_buttons = []
    monday = today - timedelta(days=today.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]

    # Функция для фильтрации привычек по выбранному дню
    def filter_habits_by_day(day):
        habits = get_habits()
        filtered = []
        for habit in habits:
            hid, title, desc, color, start_date, end_date, status = habit
            try:
                start = date.fromisoformat(start_date)
                end = date.fromisoformat(end_date) if end_date else date.max
                if start <= day <= end:
                    filtered.append(habit)
            except (ValueError, TypeError):
                continue  # Пропускаем привычки с некорректными датами
        return filtered

    # Обновление списка привычек и кнопок
    def refresh_list(day):
        nonlocal selected_day
        selected_day = day  # Обновляем выбранный день
        habit_list.controls.clear()
        for row in filter_habits_by_day(day):
            hid, title, desc, color, start, end, status = row
            habit_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"{title} ({status})", expand=True),
                        ft.Dropdown(
                            width=130,
                            value=status,
                            options=[
                                ft.dropdown.Option("в процессе"),
                                ft.dropdown.Option("выполнено"),
                                ft.dropdown.Option("заброшено"),
                            ],
                            on_change=lambda e, hid=hid: (
                                update_status(hid, e.control.value),
                                refresh_list(selected_day)
                            )
                        ),
                        ft.IconButton("delete", on_click=lambda e, hid=hid: (
                            delete_habit(hid),
                            refresh_list(selected_day)
                        ))
                    ]),
                    padding=10,
                    bgcolor="lightblue",
                    border_radius=5,
                    margin=5
                )
            )
        # Обновляем цвет кнопок
        for btn in day_buttons:
            btn_day = btn.data
            if btn_day == selected_day:
                btn.bgcolor = "blue"
                btn.color = "white"
            elif btn_day == today:
                btn.bgcolor = "lightgrey"
                btn.color = "black"
            else:
                btn.bgcolor = None
                btn.color = None
        page.update()

    # Добавление привычки
    def add_clicked(e):
        if title_input.value.strip() == "":
            page.snack_bar = ft.SnackBar(ft.Text("Введите название привычки!"))
            page.snack_bar.open = True
            page.update()
            return
        add_habit(
            title_input.value,
            desc_input.value,
            color_input.value,
            start_input.value,
            end_input.value
        )
        title_input.value = ""
        desc_input.value = ""
        color_input.value = None
        start_input.value = ""
        end_input.value = ""
        refresh_list(selected_day)

    # Создание кнопок дней недели
    for d in days:
        is_today = (d == today)
        btn = ft.ElevatedButton(
            text=f"{d.strftime('%a')}\n{d.day}",
            data=d,
            on_click=lambda e, day=d: refresh_list(day),
            width=110,
            height=70,
            bgcolor="lightgrey" if is_today else None,
        )
        day_buttons.append(btn)

    add_button = ft.ElevatedButton("Добавить привычку", on_click=add_clicked)

    # Изначально показываем привычки для текущего дня
    refresh_list(today)

    return ft.Column(
        [
            ft.Row(day_buttons, alignment="spaceAround"),
            ft.Divider(),
            ft.Column([
                title_input,
                desc_input,
                color_input,
                start_input,
                end_input,
                add_button,
                ft.Text("Список привычек:", size=20, weight="bold"),
                habit_list
            ], expand=True)
        ],
        expand=True
    )