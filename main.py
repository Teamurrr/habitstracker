# main.py
import flet as ft
from week_tab import build_week_tab
from month_tab import build_month_tab

def main(page: ft.Page):
    page.title = "Календарь и трекер"
    page.window_width = 900
    page.window_height = 500

    # Вкладка недели
    week_tab_content = build_week_tab(page)

    month_tab_content = build_month_tab(page)

    # Добавляем на страницу
    # page.add(week_tab_content)
    page.add(month_tab_content)

if __name__ == "__main__":
    ft.app(target=main)