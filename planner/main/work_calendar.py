import calendar

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

def color_calendar(cal_month_name, month_calendar):
    colorized_month_calendar = []
    for week in month_calendar:
        colorized_weeks = []
        for day in week:
            color = 'btn-outline-warning'
            colorized_weeks.append((day, color))
        colorized_month_calendar.append(colorized_weeks)
    colorized_month_dict = {cal_month_name: colorized_month_calendar}
    print(colorized_month_dict)
    return colorized_month_dict

def my_work_calendar(cal_year):
    year_calendar = []
    for cal_month in range(1, 13):
        month_calendar = calendar.Calendar().monthdatescalendar(cal_year, cal_month)
        cal_month_name = month_name(cal_month)
        colorized_calendar = color_calendar(cal_month_name, month_calendar)
        year_calendar.append(colorized_calendar)
    return year_calendar