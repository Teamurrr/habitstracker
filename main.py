import flet
from flet import Page, Column, Row, ElevatedButton, Icons, Container, SnackBar, Text
import db
from tabs import week_tab, month_tab, charts_tab, settings_tab
import threading, time
import datetime

# Добавляем импорт для уведомлений Windows
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    print("Библиотека plyer не установлена. Установите: pip install plyer")
    PLYER_AVAILABLE = False

def main(page: Page):
    page.title = "Трекер привычек"
    page.horizontal_alignment = "stretch"
    page.vertical_alignment = "stretch"
    db.ensure_db()

    active_tab = [0]
    content_column = Column(expand=True, spacing=0)

    def refresh_main(_=None):
        print("Calling refresh_main")
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

    # === Фоновый поток уведомлений ===
    def notification_loop():
        while True:
            try:
                habits = db.get_all_habits()
                now = time.time()
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                
                print(f"Проверка уведомлений. Всего привычек: {len(habits)}, сегодня: {today_str}")
                
                for h in habits:
                    interval = h.get("notification_interval", "")
                    if interval == "Без уведомлений" or not interval:
                        continue

                    # Проверяем, выполнена ли привычка сегодня
                    today_entries = db.get_entries_for_habit_on_date(h["id"], today_str)
                    today_done = any(entry["status"] == "done" for entry in today_entries)
                    
                    if today_done:
                        print(f"Привычка '{h['name']}' уже выполнена сегодня - уведомления отключены")
                        continue  # Пропускаем уведомление, если привычка уже выполнена сегодня

                    # Определяем интервал в секундах
                    if interval == "Каждые 10 секунд":
                        secs = 10
                    elif interval == "Каждый час":
                        secs = 3600
                    elif interval == "Каждые 2 часа":
                        secs = 7200
                    elif interval == "Каждые 4 часа":
                        secs = 14400
                    elif interval == "Каждый день":
                        secs = 86400
                    elif interval == "Раз в неделю":
                        secs = 604800
                    else:
                        continue

                    last = h.get("last_notified", 0) or 0
                    time_since_last = now - last
                    
                    if time_since_last >= secs:
                        print(f"Показываем уведомление для: {h['name']} (интервал: {interval})")
                        show_windows_notification(h)
                        db.update_last_notified(h["id"], now)
                    else:
                        print(f"Уведомление для '{h['name']}' скоро (через {secs - time_since_last:.0f} сек)")
                        
            except Exception as ex:
                print("Ошибка уведомлений:", ex)
            time.sleep(5)

    def show_windows_notification(habit):
        if not PLYER_AVAILABLE:
            print(f"Уведомление: {habit['name']} (библиотека plyer недоступна)")
            return
            
        try:
            notification.notify(
                title="Трекер привычек - Напоминание",
                message=f"Пора выполнить: {habit['name']}",
                timeout=10,  # Уведомление показывается 10 секунд
                app_name="Трекер привычек"
            )
            print(f"✓ Показано уведомление Windows для: {habit['name']}")
        except Exception as e:
            print(f"Ошибка показа уведомления Windows: {e}")

    threading.Thread(target=notification_loop, daemon=True).start()

    load_tab(0)
    page.add(layout)

flet.app(target=main, assets_dir="data")