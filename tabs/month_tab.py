# tabs/month_view.py
from flet import (
    Column, Row, Text, ElevatedButton, Container, Border, BorderSide, 
    Colors, alignment, MainAxisAlignment, CrossAxisAlignment,
    padding, ButtonStyle
)
from datetime import date
import calendar
from models import month_name, today, date_to_str
import db

def build_month_tab(page, refresh_main_callback):
    # State initialization
    if not hasattr(page, "month_year"):
        t = today()
        page.month_year = (t.year, t.month)

    def navigate_month(delta):
        """Navigate to previous/next month"""
        year, month = page.month_year
        month += delta
        if month > 12:
            month = 1
            year += 1
        elif month < 1:
            month = 12
            year -= 1
        page.month_year = (year, month)
        refresh_main_callback()

    def set_today():
        """Return to current month"""
        t = today()
        page.month_year = (t.year, t.month)
        refresh_main_callback()

    def build():
        year, month = page.month_year
        
        # Navigation buttons above the month
        navigation_row = Row([
            ElevatedButton(
                "← Предыдущий месяц", 
                on_click=lambda e: navigate_month(-1),
                style=ButtonStyle(
                    padding=padding.symmetric(horizontal=16, vertical=10)
                )
            ),
            ElevatedButton(
                "Сегодня", 
                on_click=lambda e: set_today(),
                style=ButtonStyle(
                    padding=padding.symmetric(horizontal=20, vertical=10)
                )
            ),
            ElevatedButton(
                "Следующий месяц →", 
                on_click=lambda e: navigate_month(1),
                style=ButtonStyle(
                    padding=padding.symmetric(horizontal=16, vertical=10)
                )
            ),
        ], 
        alignment="center", 
        spacing=20)

        # Month header without picker button
        month_header = Row([
            Text(f"{month_name(month)} {year}", size=28, weight="bold"),
        ], 
        alignment="center")

        # Get data
        habits = db.get_all_habits()
        entries = db.get_entries_for_month(year, month)
        
        # Create entries map for quick lookup
        entries_map = {}
        for e in entries:
            entries_map.setdefault(e["date"], []).append(e)

        # Build calendar
        cal = calendar.Calendar(firstweekday=0)  # Monday first
        weeks = cal.monthdatescalendar(year, month)
        
        # Calendar grid
        calendar_grid = Column(spacing=0, expand=True)

        # Weekday headers
        weekday_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        weekday_header = Row([], spacing=0, expand=True)
        
        for day_name in weekday_names:
            weekday_cell = Container(
                content=Text(
                    day_name, 
                    size=14, 
                    weight="bold", 
                    text_align="center",
                    color=Colors.BLUE_800
                ),
                expand=1,
                height=35,
                padding=5,
                alignment=alignment.center,
                bgcolor=Colors.BLUE_100,
                border=Border(
                    bottom=BorderSide(1, Colors.GREY_400),
                    right=BorderSide(1, Colors.GREY_400)
                )
            )
            weekday_header.controls.append(weekday_cell)
        
        calendar_grid.controls.append(weekday_header)

        # Calendar weeks
        for week in weeks:
            week_row = Row(spacing=0, expand=True)
            
            for day_date in week:
                is_current_month = day_date.month == month
                is_today = day_date == today()
                is_weekend = day_date.weekday() >= 5  # 5=Saturday, 6=Sunday
                
                # Day number and entries
                day_entries = entries_map.get(date_to_str(day_date), [])
                
                # Build day content
                day_content = []
                
                # Day number
                day_number = Container(
                    content=Text(
                        str(day_date.day), 
                        size=14, 
                        weight="bold" if is_today else "bold" if is_weekend else "normal",
                        color=(
                            Colors.RED if is_weekend else 
                            Colors.BLUE_700 if is_today else 
                            Colors.BLACK if is_current_month else Colors.GREY_400
                        )
                    ),
                    alignment=alignment.top_right,
                    padding=padding.only(right=4, top=2)
                )
                day_content.append(day_number)
                
                # Tasks container
                tasks_container = Container(
                    content=Column([], spacing=1, tight=True),
                    height=100,  # Fixed height for tasks
                    padding=padding.symmetric(horizontal=2)
                )
                
                # Add habit entries (max 4 for better visibility)
                for entry in day_entries[:4]:
                    habit = next((h for h in habits if h["id"] == entry["habit_id"]), None)
                    if habit:
                        task_block = Container(
                            content=Text(
                                habit["name"], 
                                size=10,
                                weight="bold",
                                color=Colors.WHITE
                            ),
                            padding=padding.symmetric(horizontal=4, vertical=2),
                            bgcolor=habit["color"],
                            border_radius=4,
                            alignment=alignment.center_left,
                        )
                        tasks_container.content.controls.append(task_block)
                
                day_content.append(tasks_container)
                
                # Show overflow indicator
                if len(day_entries) > 4:
                    overflow_text = Text(
                        f"+{len(day_entries) - 4}",
                        size=9,
                        color=Colors.GREY_600,
                        weight="bold"
                    )
                    day_content.append(overflow_text)
                
                # Day cell
                day_cell = Container(
                    content=Column(
                        day_content,
                        spacing=2,
                        alignment=MainAxisAlignment.START,
                        horizontal_alignment=CrossAxisAlignment.STRETCH,
                    ),
                    expand=1,
                    height=140,  # Fixed cell height
                    border=Border(
                        right=BorderSide(1, Colors.GREY_300),
                        bottom=BorderSide(1, Colors.GREY_300)
                    ),
                    bgcolor=(
                        Colors.BLUE_50 if is_today else 
                        Colors.GREY_50 if not is_current_month else 
                        Colors.WHITE
                    ),
                    opacity=0.7 if not is_current_month else 1.0
                )
                week_row.controls.append(day_cell)
            
            calendar_grid.controls.append(week_row)

        return Column([
            navigation_row,  # Кнопки навигации сверху
            month_header,    # Заголовок месяца
            Container(
                content=calendar_grid,
                padding=15,
                expand=True
            )
        ], expand=True)

    return build()