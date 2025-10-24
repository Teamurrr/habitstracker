# tabs/charts_tab.py
import matplotlib
matplotlib.use('Agg')  # Используем неинтерактивный бэкенд для избежания GUI-проблем
from matplotlib import pyplot as plt
from flet import (
    Column, Row, Text, Dropdown, dropdown, ElevatedButton, Image, alignment, padding, Colors, Container, ButtonStyle,
    FilePicker, FilePickerResultEvent, SnackBar
)
import db
from models import today
from datetime import datetime, date
from io import BytesIO
import base64
import calendar
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# Регистрируем шрифт с поддержкой кириллицы
try:
    font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
        FONT_NAME = "DejaVuSans"
    else:
        # fallback: шрифт с поддержкой кириллицы
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        FONT_NAME = "STSong-Light"
        print("Предупреждение: DejaVuSans.ttf не найден, используется STSong-Light.")
except Exception as e:
    print(f"Ошибка при регистрации шрифта: {e}")
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    FONT_NAME = "STSong-Light"


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
    
    # FilePicker для выбора директории сохранения
    file_picker = FilePicker()
    page.overlay.append(file_picker)
    page.update()
    
    # Функции для сбора данных
    def get_monthly_percentage_data(year: int) -> list:
        """
        Возвращает список из 12 значений — процент выполненных отметок по месяцам.
        Логика: done / total_possible_days * 100, где total_possible_days —
        суммарное количество дней в месяце, в которые каждая привычка была активна.
        """
        data = []
        habits = db.get_all_habits()

        for month in range(1, 13):
            # интервал месяца
            month_first = date(year, month, 1)
            month_last_day = calendar.monthrange(year, month)[1]
            month_last = date(year, month, month_last_day)

            # посчитать общее количество возможных дней (для всех привычек)
            total_possible = 0
            for h in habits:
                # получить даты начала/окончания привычки
                try:
                    h_start = datetime.strptime(h.get("start_date") or "", "%Y-%m-%d").date()
                except Exception:
                    h_start = date.min
                try:
                    h_end = datetime.strptime(h.get("end_date") or "", "%Y-%m-%d").date()
                except Exception:
                    h_end = date.max

                # пересечение периода привычки с текущим месяцем
                inter_start = month_first if month_first > h_start else h_start
                inter_end = month_last if month_last < h_end else h_end

                if inter_start <= inter_end:
                    total_possible += (inter_end - inter_start).days + 1

            # реальные выполненные записи за месяц
            entries = db.get_entries_for_month(year, month)
            done = sum(1 for en in entries if en.get("status") == "done")

            percentage = (done / total_possible * 100) if total_possible > 0 else 0
            # округлим до 1 знака для аккуратности (опционально)
            data.append(round(percentage, 1))

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
    
    # Функция для создания графика и возврата изображения
    def create_chart(chart_type: str, year: int) -> BytesIO:
        plt.figure(figsize=(8, 5))
        
        if chart_type == "monthly_percentage":
            data = get_monthly_percentage_data(year)
            plt.bar(range(1, 13), data, color='teal')
            plt.xlabel("Месяц")
            plt.ylabel("Процент выполненных задач (%)")
            plt.xticks(range(1, 13), ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'])
            plt.ylim(0, 100)
            plt.title(f"Процент выполненных задач по месяцам за {year} год")
        
        elif chart_type == "weekday_activity":
            labels, data = get_weekday_activity_data(year)
            plt.bar(range(7), data, color='purple')
            plt.xlabel("Дни недели")
            plt.ylabel("Количество выполненных задач")
            plt.xticks(range(7), labels)
            plt.ylim(0, max(data) * 1.2 if data else 1)
            plt.title(f"Активность по дням недели за {year} год")
        
        elif chart_type == "habit_performance":
            labels, data = get_habit_performance_data(year)
            plt.bar(range(len(data)), data, color='orange')
            plt.xlabel("Привычки")
            plt.ylabel("Количество выполненных задач")
            plt.xticks(range(len(data)), labels, rotation=45, ha='right')
            plt.ylim(0, max(data) * 1.2 if data else 1)
            plt.title(f"Выполнение по конкретным привычкам за {year} год")
        
        elif chart_type == "status_distribution":
            labels, data = get_status_distribution_data()
            plt.pie(data, labels=labels, colors=['#FF9999', '#66B2FF', '#99FF99'], autopct='%1.1f%%')
            plt.ylabel("")  # Убираем ненужную метку оси Y
            plt.title("Распределение статусов привычек")
        
        plt.tight_layout()
        
        # Сохранение графика в BytesIO
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=100)
        buf.seek(0)
        plt.close()
        
        return buf
    
    # Функция обновления графика
    def update_chart(e):
        year = int(year_dd.value)
        chart_type = chart_type_dd.value
        
        buf = create_chart(chart_type, year)
        img_str = base64.b64encode(buf.getvalue()).decode()
        
        chart_image.src_base64 = img_str
        page.update()
    
    # Функция для переноса текста с учетом ширины
    def draw_wrapped_text(c, text, x, y, max_width, line_height=14, font_name="DejaVuSans", font_size=10):
        """Рисует текст с переносом строк, чтобы не выходил за правый край."""
        c.setFont(font_name, font_size)
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = c.stringWidth(test_line, font_name, font_size)
            if test_width <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))

        for line in lines:
            if y < 60:
                c.showPage()
                y = A4[1] - 60
                c.setFont(font_name, font_size)
            c.drawString(x, y, line)
            y -= line_height
        return y

    # Функция экспорта всех графиков в PDF
    def export_to_pdf(e):
        try:
            year = int(year_dd.value)
            chart_types = [
                ("monthly_percentage", "Процент выполненных задач по месяцам"),
                ("weekday_activity", "Активность по дням недели"),
                ("habit_performance", "Выполнение по конкретным привычкам"),
                ("status_distribution", "Распределение статусов привычек")
            ]
            
            chart_explanations = {
                "monthly_percentage": (
                    "Данный график показывает, как изменялся процент выполнения привычек по месяцам. "
                    "Он помогает определить периоды высокой и низкой продуктивности. "
                    "Если значения падают, возможно, стоит пересмотреть нагрузку или мотивацию в эти месяцы."
                ),
                "weekday_activity": (
                    "На этом графике показана активность по дням недели. "
                    "Он отражает, в какие дни пользователь чаще завершает привычки. "
                    "Высокие значения указывают на дни с большей концентрацией или временем для выполнения задач."
                ),
                "habit_performance": (
                    "Здесь показано количество выполнений по каждой привычке за год. "
                    "Это позволяет выявить наиболее устойчивые привычки и те, которые требуют дополнительного внимания. "
                    "Если какая-то привычка сильно отстаёт, возможно, стоит изменить подход к ней."
                ),
                "status_distribution": (
                    "Диаграмма показывает текущее распределение статусов привычек. "
                    "Она отражает долю активных, завершённых и заброшенных привычек. "
                    "Большая доля 'выполнено' говорит о высоком уровне дисциплины и стабильности."
                ),
            }
            
            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=A4)
            width, height = A4
            
            # Поля документа
            margin_left = 50
            margin_right = 50
            text_width = width - margin_left - margin_right
            
            # Заголовок
            c.setFont(FONT_NAME, 16)
            c.drawString(margin_left, height - 50, f"Отчет по статистике привычек за {year} год")
            c.setFont(FONT_NAME, 10)
            c.drawString(margin_left, height - 70, f"Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            y_position = height - 120

            for i, (chart_type, chart_name) in enumerate(chart_types):
                if y_position < 350:
                    c.showPage()
                    c.setFont(FONT_NAME, 10)
                    y_position = height - 60

                c.setFont(FONT_NAME, 12)
                c.drawString(margin_left, y_position, f"{i + 1}. {chart_name}")
                y_position -= 25

                buf = create_chart(chart_type, year)
                img = ImageReader(buf)

                # Увеличенные и пропорциональные графики
                img_width = text_width
                img_height = img_width * 0.5

                if y_position - img_height < 100:
                    c.showPage()
                    c.setFont(FONT_NAME, 12)
                    y_position = height - 60
                    c.drawString(margin_left, y_position, f"{i + 1}. {chart_name}")
                    y_position -= 25

                c.drawImage(img, margin_left, y_position - img_height, width=img_width, height=img_height, preserveAspectRatio=True)

                explanation = chart_explanations.get(chart_type, "")
                y_position = draw_wrapped_text(c, explanation, margin_left, y_position - img_height - 15,
                                            text_width, font_name=FONT_NAME, font_size=10)
                y_position -= 30

            c.save()
            pdf_buffer.seek(0)
            save_path = os.path.join(os.path.expanduser("~"), "Downloads", f"habits_report_{year}.pdf")

            with open(save_path, "wb") as f:
                f.write(pdf_buffer.getvalue())

            page.snack_bar = SnackBar(content=Text(f"✅ PDF успешно сохранён!\nПуть: {save_path}"), duration=4000)
            page.snack_bar.open = True
            page.update()
        except Exception as e:
            page.snack_bar = SnackBar(content=Text(f"❌ Ошибка: {e}"), duration=4000)
            page.snack_bar.open = True
            page.update()
    # Кнопка обновления
    btn_refresh = ElevatedButton("Обновить график", on_click=update_chart)
    
    # Кнопка экспорта в PDF
    btn_export_pdf = ElevatedButton(
        "Экспортировать в PDF", 
        on_click=export_to_pdf,
        icon="picture_as_pdf",
        style=ButtonStyle(color=Colors.WHITE, bgcolor=Colors.RED_700)
    )
    
    # Инициализация графика при загрузке
    update_chart(None)
    
    # Сборка интерфейса
    return Container(
        content=Column([
            Text("Графики и статистика", size=18, weight="bold"),
            Row([year_dd, chart_type_dd, btn_refresh, btn_export_pdf], alignment=alignment.center_left),
            chart_image
        ], spacing=10, expand=True),
        padding=padding.symmetric(vertical=10, horizontal=20),
        expand=True
    )