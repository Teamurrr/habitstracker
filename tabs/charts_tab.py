# tabs/charts_tab.py
import matplotlib
matplotlib.use('Agg')  # Используем неинтерактивный бэкенд для избежания GUI-проблем
from matplotlib import pyplot as plt
from flet import (
    Column, Row, Text, Dropdown, dropdown, ElevatedButton, Image, alignment, padding, Colors, Container
)
import db
from models import today
from datetime import datetime
from io import BytesIO
import base64

def build_charts_tab(page, refresh_main_callback):
    # Состояние: выбранный год и тип графика
    current_year = today().year
    year_dd = Dropdown(
        label="Год",
        options=[dropdown.Option(str(y), str(y)) for y in range(2020, 2031)],
        value=str(current_year),
        width=150
    )
    
    # Dropdown для выбора типа графика
    chart_type_dd = Dropdown(
        label="Тип графика",
        options=[
            dropdown.Option("monthly_percentage", "Процент выполненных задач по месяцам"),
            dropdown.Option("weekday_activity", "Активность по дням недели"),
            dropdown.Option("habit_performance", "Выполнение по конкретным привычкам"),
            dropdown.Option("status_distribution", "Распределение статусов привычек")
        ],
        value="monthly_percentage",
        width=300
    )
    
    # Изображение для отображения графика
    chart_image = Image(src_base64="", width=600, height=400)
    
    # Функции для сбора данных
    def get_monthly_percentage_data(year: int) -> list:
        data = []
        for month in range(1, 13):
            entries = db.get_entries_for_month(year, month)
            total = len(entries)
            done = sum(1 for en in entries if en["status"] == "done")
            percentage = (done / total * 100) if total > 0 else 0
            data.append(percentage)
        return data
    
    def get_weekday_activity_data(year: int) -> tuple:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        entries = db.get_entries_between(start_date, end_date)
        weekdays = [datetime.strptime(en["date"], "%Y-%m-%d").weekday() for en in entries if en["status"] == "done"]
        weekday_counts = [0] * 7
        for w in weekdays:
            weekday_counts[w] += 1
        labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        return labels, weekday_counts
    
    def get_habit_performance_data(year: int) -> tuple:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        habits = db.get_all_habits()
        entries = db.get_entries_between(start_date, end_date)
        habit_counts = {h["name"]: sum(1 for e in entries if e["habit_id"] == h["id"] and e["status"] == "done") for h in habits}
        labels = list(habit_counts.keys())
        data = list(habit_counts.values())
        return labels, data
    
    def get_status_distribution_data() -> tuple:
        habits = db.get_all_habits()
        status_counts = {s: sum(1 for h in habits if h["status"] == s) for s in ["в процессе", "выполнено", "заброшено"]}
        labels = list(status_counts.keys())
        data = list(status_counts.values())
        return labels, data
    
    # Функция обновления графика
    def update_chart(e):
        year = int(year_dd.value)
        chart_type = chart_type_dd.value
        
        # Создание графика с помощью matplotlib
        plt.figure(figsize=(8, 5))
        
        if chart_type == "monthly_percentage":
            data = get_monthly_percentage_data(year)
            plt.bar(range(1, 13), data, color='teal')
            plt.xlabel("Месяц")
            plt.ylabel("Процент выполненных задач (%)")
            plt.xticks(range(1, 13), ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'])
            plt.ylim(0, 100)
        
        elif chart_type == "weekday_activity":
            labels, data = get_weekday_activity_data(year)
            plt.bar(range(7), data, color='purple')
            plt.xlabel("Дни недели")
            plt.ylabel("Количество выполненных задач")
            plt.xticks(range(7), labels)
            plt.ylim(0, max(data) * 1.2 if data else 1)
        
        elif chart_type == "habit_performance":
            labels, data = get_habit_performance_data(year)
            plt.bar(range(len(data)), data, color='orange')
            plt.xlabel("Привычки")
            plt.ylabel("Количество выполненных задач")
            plt.xticks(range(len(data)), labels, rotation=45, ha='right')
            plt.ylim(0, max(data) * 1.2 if data else 1)
        
        elif chart_type == "status_distribution":
            labels, data = get_status_distribution_data()
            plt.pie(data, labels=labels, colors=['#FF9999', '#66B2FF', '#99FF99'], autopct='%1.1f%%')
            plt.ylabel("")  # Убираем ненужную метку оси Y
        
        plt.title(f"Статистика за {year} год" if chart_type != "status_distribution" else "Распределение статусов")
        plt.tight_layout()
        
        # Сохранение графика в base64
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=100)
        buf.seek(0)
        img_str = base64.b64encode(buf.getvalue()).decode()
        plt.close()
        
        chart_image.src_base64 = img_str
        page.update()
    
    # Кнопка обновления
    btn_refresh = ElevatedButton("Обновить график", on_click=update_chart)
    
    # Инициализация графика при загрузке
    update_chart(None)
    
    # Сборка интерфейса
    return Container(
        content=Column([
            Text("Графики и статистика", size=18, weight="bold"),
            Row([year_dd, chart_type_dd, btn_refresh], alignment=alignment.center_left),
            chart_image
        ], spacing=10, expand=True),
        padding=padding.symmetric(vertical=10, horizontal=20),
        expand=True
    )