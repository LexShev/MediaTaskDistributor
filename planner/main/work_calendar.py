import calendar
import datetime

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

def my_calendar(cal_year, cal_month):
    # for week in month.monthdatescalendar(2025, 3):
    month_calendar = calendar.Calendar().monthdatescalendar(cal_year, cal_month)
    cal_month_name = month_name(cal_month)
    return month_calendar, {'cal_year': cal_year, 'cal_month': str(cal_month), 'cal_month_name': cal_month_name}
# print()
# print(list(month.itermonthdates(2025, 3)))
# print([day for day in month.itermonthdates(2025, 3) if day.month == 3])
