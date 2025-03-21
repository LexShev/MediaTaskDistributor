import calendar
import datetime

from .kpi_admin_panel import summary_task_list


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

def calc_prev_month(cal_year, cal_month):
    if cal_month > 1:
        prev_month = cal_month - 1
        prev_year = cal_year
    else:
        prev_month = 12
        prev_year = cal_year - 1
    return prev_year, prev_month

def calc_next_month(cal_year, cal_month):
    if cal_month < 12:
        next_month = cal_month + 1
        next_year = cal_year
    else:
        next_month = 1
        next_year = cal_year + 1
    return next_year, next_month


def my_calendar(cal_year, cal_month):
    # for week in month.monthdatescalendar(2025, 3):
    month_calendar = calendar.Calendar().monthdatescalendar(cal_year, cal_month)
    cal_month_name = month_name(cal_month)
    prev_year, prev_month = calc_prev_month(cal_year, cal_month)
    next_year, next_month = calc_next_month(cal_year, cal_month)
    service_dict = {'cal_year': cal_year,
                    'cal_month': cal_month,
                    'cal_month_name': cal_month_name,
                    'prev_year': prev_year,
                    'next_year': next_year,
                    'prev_month': prev_month,
                    'next_month': next_month
                    }
    return month_calendar, service_dict

def task_list(cal_year, cal_month):
    work_dates = tuple(str(day) for day in calendar.Calendar().itermonthdates(cal_year, cal_month) if day.month == cal_month)
    return summary_task_list(work_dates)
# print()
# print(list(month.itermonthdates(2025, 3)))
# print([day for day in month.itermonthdates(2025, 3) if day.month == 3])
