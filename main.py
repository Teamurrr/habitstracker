import flet
from flet import Page, Column, Row, ElevatedButton, Icons, Container
import db
from tabs import week_tab, month_tab, charts_tab, settings_tab

def main(page: Page):
    page.title = "Трекер привычек"
    page.horizontal_alignment = "stretch"
    page.vertical_alignment = "stretch"
    db.ensure_db()

    active_tab = [0]
    content_column = Column(expand=True, spacing=0)

    # def refresh_main(_=None):
    #     load_tab(active_tab[0])

    def refresh_main(_=None):
        print("Calling refresh_main")  # Отладочный вывод
        load_tab(active_tab[0])

    def make_tab_button(i, label, icon):
        def on_click(e):
            active_tab[0] = i
            load_tab(i)
        return ElevatedButton(
            text=label,
            icon=icon,
            width=160,
            expand=False,
            on_click=on_click
        )

    left_panel = Container(
        content=Column(
            controls=[
                make_tab_button(0, "Неделя", Icons.CALENDAR_MONTH_SHARP),
                make_tab_button(1, "Месяц", Icons.CALENDAR_TODAY_ROUNDED),
                make_tab_button(2, "Графики", Icons.BAR_CHART_SHARP),
                make_tab_button(3, "Настройки", Icons.SETTINGS_ROUNDED)
            ],
            spacing=8,
            expand=True,
        ),
        width=160,
        padding=10,
        bgcolor="#f0f0f0",
    )

    def load_tab(i):
        content_column.controls.clear()
        if i == 0:
            content_column.controls.append(week_tab.build_week_tab(page, refresh_main))
        elif i == 1:
            content_column.controls.append(month_tab.build_month_tab(page, refresh_main))
        elif i == 2:
            content_column.controls.append(charts_tab.build_charts_tab(page, refresh_main))
        elif i == 3:
            content_column.controls.append(settings_tab.build_settings_tab(page, refresh_main))
        page.update()

    layout = Row(
        controls=[
            left_panel,
            Container(content=content_column, expand=True, padding=10)
        ],
        expand=True,
        spacing=0
    )

    load_tab(0)
    page.add(layout)


flet.app(target=main, assets_dir="data")