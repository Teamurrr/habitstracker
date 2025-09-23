# week_tab_only.py
from datetime import date, timedelta
import flet as ft

def get_tasks_for_day(d):
    """
    Заглушка. Возвращает список задач для выбранного дня.
    В реальном коде здесь будет SQL запрос к таблице с планами.
    """
    return [
        f"Задача 1 на {d.strftime('%d.%m.%Y')}",
        f"Задача 2 на {d.strftime('%d.%m.%Y')}",
    ]

def build_week_tab(page):
    today = date.today()
    selected_day = today  # День, который выбран пользователем

    # Колонка для блоков планов
    tasks_column = ft.Column(expand=True)

    # Список кнопок для дней недели
    day_buttons = []

    # Вычисляем понедельник недели
    monday = today - timedelta(days=today.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]

    # Функция обновления планов и цвета кнопок
    def update_day(d):
        nonlocal selected_day
        selected_day = d

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

        # Загружаем задачи из БД (заглушка)
        tasks_column.controls = []
        tasks = get_tasks_for_day(d)
        for t in tasks:
            tasks_column.controls.append(
                ft.Container(
                    content=ft.Text(t),
                    padding=10,
                    bgcolor="lightblue",
                    border_radius=5,
                    margin=5,
                )
            )

        page.update()

    # Создание кнопок дней недели
    for d in days:
        is_today = (d == today)
        btn = ft.ElevatedButton(
            text=f"{d.strftime('%a')}\n{d.day}",
            data=d,
            on_click=lambda e, day=d: update_day(day),
            width=110,
            height=70,
            bgcolor="lightgrey" if is_today else None,
        )
        day_buttons.append(btn)

    # Изначально показываем сегодняшний день
    update_day(today)

    # Размещение элементов на странице
    return ft.Column(
        [
            ft.Row(day_buttons, alignment="spaceAround"),
            ft.Divider(),
            tasks_column,
        ],
        expand=True
    )
