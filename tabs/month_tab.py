# tabs/month_view.py
from flet import Column, Row, Text, ElevatedButton, Dropdown, dropdown, TextButton, AlertDialog, Container
from datetime import date
import calendar
from models import month_name, today, date_to_str
import db

def build_month_tab(page, refresh_main_callback):
    # state
    if not hasattr(page, "month_year"):
        t = today()
        page.month_year = (t.year, t.month)

    def pick_month(e):
        # open dialog with dropdown for month and year
        months = [{"label": calendar.month_name[i], "value": i} for i in range(1,13)]
        month_dd = Dropdown(width=200, options=[dropdown.Option(m["label"], m["value"]) for m in months], value=page.month_year[1])
        year_dd = Dropdown(width=120, options=[dropdown.Option(str(y), y) for y in range(1970, 2031)], value=page.month_year[0])

        def apply(e):
            page.month_year = (year_dd.value, month_dd.value)
            dialog.open = False
            page.update()
            refresh_main_callback()

        dialog = AlertDialog(
            title=Text("Выберите месяц и год"),
            content=Column([month_dd, year_dd]),
            actions=[TextButton("Применить", on_click=apply), TextButton("Отмена", on_click=lambda e: cancel())]
        )
        def cancel():
            dialog.open = False
            page.update()

        page.dialog = dialog
        dialog.open = True
        page.update()

    def build():
        year, month = page.month_year
        header = Row([Text(f"{month_name(month)} {year}", size=18), ElevatedButton("Выбрать", on_click=pick_month)], alignment="center")

        # get entries for month and habits
        habits = db.get_all_habits()
        entries = db.get_entries_for_month(year, month)
        entries_map = {}
        for e in entries:
            entries_map.setdefault(e["date"], []).append(e)

        # Build calendar grid (simple)
        cal = calendar.Calendar(firstweekday=0)
        weeks = list(cal.monthdatescalendar(year, month))  # list of weeks, each a list of dates
        grid = []
        # header of weekdays
        grid.append(Row([Text(day[:3], width=60) for day in ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]]))
        for week in weeks:
            row_cells = []
            for d in week:
                cell_content = [Text(str(d.day))]
                # find entries on this date across habits
                ds = date_to_str(d)
                for e in entries_map.get(ds, []):
                    # show small colored bar (lookup habit color)
                    h = next((hh for hh in habits if hh["id"]==e["habit_id"]), None)
                    if h:
                        cell_content.append(Container(content=Text(h["name"], size=9), height=16, bgcolor=h["color"], padding=4))
                row_cells.append(Column(cell_content, spacing=4, width=120, height=80))
            grid.append(Row(row_cells, spacing=6))
        return Column([header] + grid, spacing=10)
    return build()
