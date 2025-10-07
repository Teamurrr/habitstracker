import datetime
from flet import (
    Column, Row, Container, Text, IconButton, Checkbox,
    ElevatedButton, Icons, alignment, border
)

# Заглушка для данных (в реальном проекте заменяется запросом к БД)
def get_week_habits(start_date):
    # Пример: возвращаем 2 привычки
    return [
        {"name": "Утренняя зарядка", "days": [True, True, False, True, False, True, False]},
        {"name": "Чтение", "days": [False, True, True, False, False, False, True]},
    ]

def build_week_tab(page, refresh_main_callback):
    current_week_start = [datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())]

    def refresh_view():
        week_start = current_week_start[0]
        week_days = [(week_start + datetime.timedelta(days=i)) for i in range(7)]
        habits = get_week_habits(week_start)

        # Заголовок дней недели
        header_row = Row(
            [
                Container(Text("", size=14, weight="bold"), width=160),
                *[
                    Container(
                        Text(day.strftime("%a\n%d.%m"), size=13, weight="bold"),
                        alignment=alignment.center,
                        expand=True,
                    )
                    for day in week_days
                ],
            ],
            spacing=4,
        )

        # Строки с привычками
        habit_rows = []
        if habits:
            for habit in habits:
                row = Row(
                    [
                        Container(Text(habit["name"]), width=160),
                        *[
                            Container(
                                Checkbox(value=habit["days"][i]),
                                alignment=alignment.center,
                                expand=True,
                            )
                            for i in range(7)
                        ],
                    ],
                    spacing=4,
                )
                habit_rows.append(row)
        else:
            habit_rows.append(
                Container(
                    Text("Нет привычек на эту неделю.", size=13, italic=True),
                    alignment=alignment.center,
                    expand=True,
                )
            )

        # Кнопки навигации
        nav_row = Row(
            [
                IconButton(Icons.ARROW_BACK, on_click=prev_week),
                Text(
                    f"Неделя {week_days[0].strftime('%d.%m')} – {week_days[-1].strftime('%d.%m')}",
                    size=15, weight="bold"
                ),
                IconButton(Icons.ARROW_FORWARD, on_click=next_week),
                Container(expand=True),
                ElevatedButton("Добавить привычку", icon=Icons.ADD, on_click=add_habit)
            ],
            alignment="spaceBetween",
            spacing=10,
        )

        # Основной контейнер
        content.controls.clear()
        content.controls.append(Column([nav_row, header_row, *habit_rows], spacing=10))
        page.update()

    # Обработчики кнопок
    def prev_week(e):
        current_week_start[0] -= datetime.timedelta(days=7)
        refresh_view()

    def next_week(e):
        current_week_start[0] += datetime.timedelta(days=7)
        refresh_view()

    def add_habit(e):
        # В реальном проекте тут будет форма добавления
        print("Добавление новой привычки")
        refresh_main_callback()

    # Основная колонка контента
    content = Column(scroll="auto", expand=True, spacing=10)
    refresh_view()

    return Container(
        content,
        expand=True,
        padding=10,
        border=border.all(1, "transparent"),
        alignment=alignment.top_left,
    )