import calendar
import os
from django.template.defaulttags import register

from .kpi_admin_panel import summary_task_list

@register.filter
def file_name(full_path):
    return os.path.basename(full_path)

@register.filter
def dir_name(full_path):
    return os.path.dirname(full_path).replace('\\\\192.168.80.3\\', "")


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

def tasks_info(month_calendar, task_list):
    colorized_calendar = []
    for week in month_calendar:
        colorized_weeks = []
        for day in week:
            total_tasks = len(list(task for task in task_list if task.get('Task_work_date') == day))
            ready_tasks = len(list(task for task in task_list if task.get('Task_task_status') == 'ready' and task.get('Task_work_date') == day))
            not_ready_tasks = len(list(task for task in task_list if task.get('Task_task_status') == 'not_ready' and task.get('Task_work_date') == day))
            try:
                ready_index = (ready_tasks * 100) / total_tasks
            except Exception:
                ready_index = 'day_off'
            #     проверка на отсутствие задач в текущий день
            if ready_index == 'day_off':
                color = ''
            elif ready_index > 13:
                color = 'btn-outline-success'
            elif 10 < ready_index < 13:
                color = 'btn-outline-warning'
            else:
                color = 'btn-outline-danger'
            colorized_weeks.append({'day': day,
                                    'ready_tasks': ready_tasks,
                                    'not_ready_tasks': not_ready_tasks,
                                    'ready_index': ready_index,
                                    'color': color})
        colorized_calendar.append(colorized_weeks)
    return colorized_calendar

def my_report_calendar(cal_year, cal_month):
    month_calendar = calendar.Calendar().monthdatescalendar(cal_year, cal_month)

    work_dates = tuple(str(day) for day in calendar.Calendar().itermonthdates(cal_year, cal_month) if day.month == cal_month)
    task_list = summary_task_list(work_dates)

    colorized_calendar = tasks_info(month_calendar, task_list)

    prev_year, prev_month = calc_prev_month(cal_year, cal_month)
    next_year, next_month = calc_next_month(cal_year, cal_month)
    service_dict = {'cal_year': cal_year,
                    'cal_month': cal_month,
                    'prev_year': prev_year,
                    'next_year': next_year,
                    'prev_month': prev_month,
                    'next_month': next_month
                    }
    return colorized_calendar, task_list, service_dict

