# tabs/week_tab.py
import datetime
from flet import (
    Column, Row, Container, Text, IconButton, Checkbox,
    ElevatedButton, Icons, alignment, border, AlertDialog,
    TextField, Dropdown, dropdown, TextButton, SnackBar
)
from models import date_to_str, today, week_dates
import db


def get_week_habits(start_date):
    habits = db.get_all_habits()
    week_days = week_dates(start_date)
    result = []
    for habit in habits:
        try:
            start = datetime.datetime.strptime(habit["start_date"], "%Y-%m-%d").date() if habit["start_date"] else datetime.date.min
            end = datetime.datetime.strptime(habit["end_date"], "%Y-%m-%d").date() if habit["end_date"] else datetime.date.max
            if start <= week_days[-1] and end >= week_days[0]:
                entries = db.get_entries_between(date_to_str(week_days[0]), date_to_str(week_days[-1]))
                days = [False] * 7
                for i, day in enumerate(week_days):
                    ds = date_to_str(day)
                    for entry in entries:
                        if entry["habit_id"] == habit["id"] and entry["date"] == ds and entry["status"] == "done":
                            days[i] = True
                result.append({"name": habit["name"], "id": habit["id"], "color": habit["color"], "days": days})
        except (ValueError, TypeError):
            continue
    return result


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
        try:
            # Очищаем overlay от предыдущих диалогов
            if hasattr(page, 'overlay') and page.overlay:
                page.overlay[:] = [x for x in page.overlay if not isinstance(x, AlertDialog)]

            # Поля формы
            title_input = TextField(label="Название привычки")
            status_input = Dropdown(
                label="Статус",
                options=[
                    dropdown.Option("в процессе"),
                    dropdown.Option("выполнено"),
                    dropdown.Option("заброшено"),
                ],
                value="в процессе"
            )
            color_input = Dropdown(
                label="Цвет",
                options=[
                    dropdown.Option("red", "Красный"),
                    dropdown.Option("green", "Зелёный"),
                    dropdown.Option("blue", "Синий"),
                    dropdown.Option("yellow", "Жёлтый"),
                ],
                value="blue"
            )
            start_input = TextField(label="Дата начала (ГГГГ-ММ-ДД)", value=date_to_str(today()))
            end_input = TextField(label="Дата окончания (ГГГГ-ММ-ДД)", value="")

            # Сохранение привычки
            def save_habit(e):
                try:
                    if not title_input.value.strip():
                        page.snack_bar = SnackBar(content=Text("Введите название привычки!"))
                        page.snack_bar.open = True
                        page.update()
                        return

                    db.add_habit({
                        "name": title_input.value,
                        "status": status_input.value,
                        "color": color_input.value,
                        "start_date": start_input.value if start_input.value.strip() else None,
                        "end_date": end_input.value if end_input.value.strip() else None
                    })

                    # Закрываем диалог
                    dialog.open = False
                    page.update()

                    # После закрытия обновляем список привычек
                    refresh_view()

                except Exception as ex:
                    page.snack_bar = SnackBar(content=Text(f"Ошибка сохранения: {str(ex)}"))
                    page.snack_bar.open = True
                    page.update()

            # Отмена
            def cancel(e):
                try:
                    dialog.open = False
                    page.update()
                except Exception as ex:
                    page.snack_bar = SnackBar(content=Text(f"Ошибка закрытия: {str(ex)}"))
                    page.snack_bar.open = True
                    page.update()

            # Создаём диалог
            dialog = AlertDialog(
                title=Text("Добавить привычку"),
                content=Column([title_input, status_input, color_input, start_input, end_input], spacing=10),
                actions=[
                    TextButton("Добавить", on_click=save_habit),
                    TextButton("Отмена", on_click=cancel)
                ],
                modal=True
            )

            page.overlay.append(dialog)
            dialog.open = True
            page.update()

        except Exception as ex:
            page.snack_bar = SnackBar(content=Text(f"Ошибка: {str(ex)}"))
            page.snack_bar.open = True
            page.update()

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
