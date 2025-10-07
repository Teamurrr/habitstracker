# models.py
# Простейшие вспомогательные функции
from datetime import date, timedelta, datetime
import calendar

def date_to_str(d: date) -> str:
    return d.strftime("%Y-%m-%d")

def str_to_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def week_start(d: date) -> date:
    # неделя начинается с понедельника
    return d - timedelta(days=d.weekday())

def week_dates(start: date):
    return [start + timedelta(days=i) for i in range(7)]

def month_name(month:int)->str:
    return calendar.month_name[month]

def today():
    return date.today()