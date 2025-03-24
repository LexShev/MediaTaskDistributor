from datetime import timedelta, datetime

from django.template.defaulttags import register
from django.db import connections
import calendar


@register.filter
def month_name(cal_month):
    month_dict = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь"}
    return month_dict.get(cal_month)

def check_holidays(month_calendar):
    holidays = holidays_list()
    colorized_calendar = []
    for week in month_calendar:
        colorized_weeks = []
        for day in week:
            if day in holidays:
                day_off = 1
            else:
                day_off = 0
            colorized_weeks.append({'day': day, 'day_off': day_off})
        colorized_calendar.append(colorized_weeks)
    return colorized_calendar

def my_work_calendar(cal_year):
    year_calendar = []
    for cal_month in range(1, 13):
        month_calendar = calendar.Calendar().monthdatescalendar(cal_year, cal_month)
        work_calendar = check_holidays(month_calendar)
        year_calendar.append(work_calendar)
    return year_calendar

def holidays_list():
    with connections['planner'].cursor() as cursor:
        query = 'SELECT [day_off] FROM [planner].[dbo].[days_off]'
        cursor.execute(query)
        return [day[0] for day in cursor.fetchall()]

def drop_day_off(work_date):
    with connections['planner'].cursor() as cursor:
        query = f"DELETE FROM [planner].[dbo].[days_off] WHERE [day_off] = '{work_date}'"
        cursor.execute(query)

def insert_day_off(work_date):
    with connections['planner'].cursor() as cursor:
        query = f"INSERT INTO[planner].[dbo].[days_off] ([day_off]) VALUES ('{work_date}');"
        cursor.execute(query)

def vacation_info(cal_year):
    with connections['planner'].cursor() as cursor:
        columns = ('worker_id', 'worker', 'start_date', 'end_date', 'description')
        sql_columns = ', '.join([f'[{col}]' for col in columns])
        query = f'''
        SELECT {sql_columns}
        FROM [planner].[dbo].[vacation_schedule]
        WHERE year([start_date]) = {cal_year}'''
        cursor.execute(query)
        # [dict(zip(columns, val)) for val in cursor.fetchall()]
        vacation_list = []
        for val in cursor.fetchall():
            vacation_dict = dict(zip(columns, val))
            start_date = vacation_dict.get('start_date')
            end_date = vacation_dict.get('end_date')
            total = (end_date-start_date).days
            vacation_dict['total'] = total
            vacation_list.append(vacation_dict)
        return vacation_list
