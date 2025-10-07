# tabs/charts_view.py
from flet import Column, Text, Dropdown, dropdown, ElevatedButton
import db
from models import today

def build_charts_tab(page, refresh_main_callback):
    # placeholder: показывает простую статистику по месяцам
    year_dd = Dropdown(options=[dropdown.Option(str(y), y) for y in range(2020, 2031)], value=today().year)
    month_dd = Dropdown(options=[dropdown.Option(str(m), m) for m in range(1,13)], value=today().month)
    stats_text = Text("Здесь будут графики (зависит от реализации визуализации).")

    def update(e):
        # compute simple percentages for selected month
        y = year_dd.value
        m = month_dd.value
        entries = db.get_entries_for_month(y, m)
        total = len(entries)
        done = sum(1 for en in entries if en["status"]=="done")
        stats_text.value = f"В {m}/{y}: всего записей {total}, выполнено {done} ({(done/total*100) if total else 0:.1f}%)."
        page.update()

    year_dd.on_change = update
    month_dd.on_change = update

    btn_refresh = ElevatedButton("Обновить", on_click=update)
    return Column([Text("Графики и статистика"), year_dd, month_dd, btn_refresh, stats_text])
