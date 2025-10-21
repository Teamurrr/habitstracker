# tabs/week_tab.py
import datetime
from flet import (
    Column, Row, Container, Text, IconButton, Checkbox,
    ElevatedButton, Icons, alignment, border, AlertDialog,
    TextField, Dropdown, dropdown, TextButton, SnackBar,
    Colors, MainAxisAlignment, ScrollMode, CrossAxisAlignment
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
                result.append({
                    "name": habit["name"],
                    "id": habit["id"],
                    "color": habit["color"],
                    "days": days,
                    "status": habit["status"],
                    "notification_interval": habit.get("notification_interval", "Без уведомлений")
                })
        except (ValueError, TypeError):
            continue
    return result


def build_week_tab(page, refresh_main_callback):
    current_week_start = [datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())]

    def refresh_view():
        week_start = current_week_start[0]
        week_days = [(week_start + datetime.timedelta(days=i)) for i in range(7)]
        habits = get_week_habits(week_start)
        
        # Определяем сегодняшнюю дату
        today_date = datetime.date.today()

        # Заголовок дней недели
        header_row = Row(
            [
                Container(Text("", size=14, weight="bold"), width=200),
                *[
                    Container(
                        Text(
                            day.strftime("%a\n%d.%m"), 
                            size=13, 
                            weight="bold",
                            color=Colors.BLUE if day == today_date else Colors.WHITE  # Выделяем сегодняшний день
                        ),
                        alignment=alignment.center,
                        expand=True,
                        bgcolor=Colors.BLUE_100 if day == today_date else Colors.TRANSPARENT,  # Фон для сегодняшнего дня
                        border_radius=5 if day == today_date else 0,
                        padding=5 if day == today_date else 0,
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
                # Определяем цвет текста в зависимости от статуса
                text_color = (
                    Colors.GREEN if habit["status"] == "выполнено"
                    else Colors.RED if habit["status"] == "заброшено"
                    else Colors.WHITE  # для "в процессе"
                )
                
                # Создаем контейнер для названия привычки
                habit_name_text = Container(
                    content=Text(
                        habit["name"], 
                        color=text_color,
                        size=13,
                    ),
                    margin=5,
                )
                
                # Создаем кнопки
                edit_button = IconButton(
                    Icons.EDIT, 
                    on_click=lambda e, h=habit: edit_habit(e, h),
                    icon_size=18,
                    tooltip="Редактировать"
                )
                
                delete_button = IconButton(
                    Icons.DELETE, 
                    on_click=lambda e, h=habit: delete_habit(e, h),
                    icon_size=18,
                    tooltip="Удалить"
                )
                
                # Используем Column для возможности переноса
                # Если текст короткий - все в одной строке, если длинный - перенос
                habit_content = Column(
                    [
                        Row(
                            [
                                habit_name_text,
                                Row([edit_button, delete_button], spacing=2, tight=True),
                            ],
                            spacing=8,
                            vertical_alignment=CrossAxisAlignment.CENTER,
                            wrap=True,  # Включаем автоматический перенос
                        )
                    ],
                    spacing=2,
                    tight=True,
                )
                
                row = Row(
                    [
                        Container(
                            habit_content, 
                            width=200,
                            padding=5,
                        ),
                        *[
                            Container(
                                Checkbox(
                                    value=habit["days"][i],
                                    on_change=lambda e, day_idx=i, h_id=habit["id"]: checkbox_changed(e, day_idx, h_id)
                                ),
                                alignment=alignment.center,
                                expand=True,
                                bgcolor=Colors.BLUE_50 if week_days[i] == today_date else Colors.TRANSPARENT,  # Выделяем сегодняшний день
                                border_radius=5 if week_days[i] == today_date else 0,
                            )
                            for i in range(7)
                        ],
                    ],
                    spacing=4,
                    vertical_alignment=CrossAxisAlignment.CENTER,
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
                    f"{week_days[0].strftime('%B %Y')} | Неделя {week_days[0].strftime('%d.%m')} – {week_days[-1].strftime('%d.%m')}",
                    size=15, weight="bold"
                ),
                IconButton(Icons.ARROW_FORWARD, on_click=next_week),
                Container(expand=True),
                ElevatedButton("Сегодня", icon=Icons.TODAY, on_click=go_to_today),
                ElevatedButton("Добавить привычку", icon=Icons.ADD, on_click=add_habit)
            ],
            alignment="spaceBetween",
            spacing=10,
        )

        # Основной контейнер
        content.controls.clear()
        content.controls.append(Column([nav_row, header_row, *habit_rows], spacing=8))
        page.update()

    # Обработчик изменения чекбокса
    def checkbox_changed(e, day_idx, habit_id):
        week_start = current_week_start[0]
        week_days = [(week_start + datetime.timedelta(days=i)) for i in range(7)]
        ds = date_to_str(week_days[day_idx])
        status = "done" if e.control.value else "skipped"
        db.set_entry(habit_id, ds, status)
        page.snack_bar = SnackBar(content=Text(f"Статус обновлён для {ds}"))
        page.snack_bar.open = True
        page.update()

    # Обработчики кнопок
    def prev_week(e):
        current_week_start[0] -= datetime.timedelta(days=7)
        refresh_view()

    def next_week(e):
        current_week_start[0] += datetime.timedelta(days=7)
        refresh_view()

    def go_to_today(e):
        current_week_start[0] = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
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

            notification_input = Dropdown(
                label="Частота уведомлений",
                options=[
                    dropdown.Option("Без уведомлений"),
                    dropdown.Option("Каждые 10 секунд"),
                    dropdown.Option("Каждый час"),
                    dropdown.Option("Каждые 2 часа"),
                    dropdown.Option("Каждые 4 часа"),
                    dropdown.Option("Каждый день"),
                    dropdown.Option("Раз в неделю")
                ],
                value="Без уведомлений"
            )

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
                        "end_date": end_input.value if end_input.value.strip() else None,
                        "notification_interval": notification_input.value
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
                content=Column(
                    [title_input, status_input, color_input, start_input, end_input, notification_input],
                    spacing=10
                ),
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

    def edit_habit(e, habit):
        try:
            # Очищаем overlay от предыдущих диалогов
            if hasattr(page, 'overlay') and page.overlay:
                page.overlay[:] = [x for x in page.overlay if not isinstance(x, AlertDialog)]

            # Поля формы с предзаполненными значениями
            title_input = TextField(label="Название привычки", value=habit["name"])
            status_input = Dropdown(
                label="Статус",
                options=[
                    dropdown.Option("в процессе"),
                    dropdown.Option("выполнено"),
                    dropdown.Option("заброшено"),
                ],
                value=habit.get("status", "в процессе")
            )
            color_input = Dropdown(
                label="Цвет",
                options=[
                    dropdown.Option("red", "Красный"),
                    dropdown.Option("green", "Зелёный"),
                    dropdown.Option("blue", "Синий"),
                    dropdown.Option("yellow", "Жёлтый"),
                ],
                value=habit["color"]
            )
            start_input = TextField(label="Дата начала (ГГГГ-ММ-ДД)", value=habit.get("start_date", ""))
            end_input = TextField(label="Дата окончания (ГГГГ-ММ-ДД)", value=habit.get("end_date", ""))

            notification_input = Dropdown(
                label="Частота уведомлений",
                options=[
                    dropdown.Option("Без уведомлений"),
                    dropdown.Option("Каждые 10 секунд"),
                    dropdown.Option("Каждый час"),
                    dropdown.Option("Каждые 2 часа"),
                    dropdown.Option("Каждые 4 часа"),
                    dropdown.Option("Каждый день"),
                    dropdown.Option("Раз в неделю")
                ],
                value=habit.get("notification_interval", "Каждый день")
            )

            # Сохранение изменений
            def save_edit(e):
                try:
                    if not title_input.value.strip():
                        page.snack_bar = SnackBar(content=Text("Введите название привычки!"))
                        page.snack_bar.open = True
                        page.update()
                        return

                    fields = {
                        "name": title_input.value,
                        "status": status_input.value,
                        "color": color_input.value,
                        "start_date": start_input.value if start_input.value.strip() else None,
                        "end_date": end_input.value if end_input.value.strip() else None,
                        "notification_interval": notification_input.value
                    }
                    db.update_habit(habit["id"], fields)

                    # Закрываем диалог
                    dialog.open = False
                    page.update()

                    # Обновляем вид
                    refresh_view()
                    page.update()

                except Exception as ex:
                    page.snack_bar = SnackBar(content=Text(f"Ошибка сохранения: {str(ex)}"))
                    page.snack_bar.open = True
                    page.update()

            # Отмена
            def cancel(e):
                dialog.open = False
                page.update()

            # Создаём диалог
            dialog = AlertDialog(
                title=Text("Изменить привычку"),
                content=Column([title_input, status_input, color_input, start_input, end_input, notification_input], spacing=10),
                actions=[
                    TextButton("Сохранить", on_click=save_edit),
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

    def delete_habit(e, habit):
        try:
            # Подтверждение удаления
            def confirm_delete(e):
                db.delete_habit(habit["id"])
                dialog.open = False
                page.update()
                refresh_view()
                page.snack_bar = SnackBar(content=Text("Привычка удалена"))
                page.snack_bar.open = True
                page.update()

            def cancel(e):
                dialog.open = False
                page.update()

            dialog = AlertDialog(
                title=Text("Удалить привычку?"),
                content=Text(f"Вы уверены, что хотите удалить '{habit['name']}'? Это удалит все связанные записи."),
                actions=[
                    TextButton("Удалить", on_click=confirm_delete),
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