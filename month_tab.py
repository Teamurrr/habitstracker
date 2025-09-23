import calendar
from datetime import date
import flet as ft

def get_tasks_for_day(d):
    """
    Заглушка для задач. В будущем заменить на БД.
    Возвращает 0-4 задачи для примера.
    """
    return [f"Задача {i+1}" for i in range(min(4, d.day % 5))]

def build_month_tab(page, selected_year=None, selected_month=None):
    today = date.today()

    if not selected_year:
        selected_year = today.year
    if not selected_month:
        selected_month = today.month

    cal_container = ft.Column(expand=True)

    # Dropdown для выбора года и месяца
    year_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(str(y)) for y in range(today.year - 5, today.year + 6)],
        value=str(selected_year),
        width=100
    )
    month_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(str(m)) for m in range(1, 13)],
        value=str(selected_month),
        width=80
    )

    # Размеры ячеек
    CAL_WIDTH = 900
    CAL_HEIGHT = 500
    CELL_WIDTH = CAL_WIDTH // 7
    CELL_HEIGHT = (CAL_HEIGHT - 100) // 6  # 6 недель максимум

    def update_calendar(e=None):
        nonlocal selected_year, selected_month
        selected_year = int(year_dropdown.value)
        selected_month = int(month_dropdown.value)
        cal_container.controls = build_calendar(selected_year, selected_month)
        page.update()

    year_dropdown.on_change = update_calendar
    month_dropdown.on_change = update_calendar

    def build_calendar(year, month):
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)

        header = ft.Text(f"{calendar.month_name[month]} {year}", size=20, weight=ft.FontWeight.BOLD)

        # Названия дней недели
        week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        header_row = ft.Row(
            [ft.Container(ft.Text(d, weight=ft.FontWeight.BOLD, text_align="center"),
                          width=CELL_WIDTH) for d in week_days],
            spacing=0
        )

        rows = []
        for week in month_days:
            cells = []
            for d in week:
                if d == 0:
                    # Пустая ячейка
                    cells.append(ft.Container(
                        content=ft.Column([]),
                        width=CELL_WIDTH,
                        height=CELL_HEIGHT,
                        border=ft.border.all(1, "lightgrey"),
                        padding=2
                    ))
                else:
                    ddate = date(year, month, d)
                    tasks = get_tasks_for_day(ddate)
                    task_blocks = []
                    for t in tasks:
                        task_blocks.append(
                            ft.Container(
                                content=ft.Text(t, size=10),
                                padding=2,
                                bgcolor="lightblue",
                                border_radius=3,
                                margin=1,
                                height=14
                            )
                        )

                    # Дата в верхнем левом углу
                    cell_content = ft.Column(
                        [
                            ft.Row([ft.Text(str(d), size=12)], alignment="start"),
                            ft.Column(task_blocks, spacing=2)
                        ],
                        alignment="start",
                        spacing=2
                    )

                    bgcolor = "lightgrey" if ddate == today else None

                    cell = ft.Container(
                        content=cell_content,
                        width=CELL_WIDTH,
                        height=CELL_HEIGHT,
                        padding=2,
                        border=ft.border.all(1, "lightgrey"),
                        bgcolor=bgcolor
                    )
                    cells.append(cell)
            rows.append(ft.Row(cells, spacing=0))
        return [header, header_row] + rows

    update_calendar()  # показать текущий месяц

    return ft.Column(
        [
            ft.Row([year_dropdown, month_dropdown], alignment="start"),
            ft.Divider(),
            cal_container
        ],
        expand=True
    )