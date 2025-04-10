import calendar
import os
from django.template.defaulttags import register

from .db_connection import oplan_material_list

@register.filter
def file_name(full_path):
    if full_path:
        return os.path.basename(full_path)

@register.filter
def dir_name(full_path):
    if full_path:
        return os.path.dirname(full_path).replace('\\\\192.168.80.3\\', "")

@register.filter
def schedule_name(schedule_id):
    schedules = {
        3: 'Крепкое',
        5: 'Планета дети',
        6: 'Мировой сериал',
        7: 'Мужской сериал',
        8: 'Наше детство',
        9: 'Романтичный сериал',
        10: 'Наше родное кино',
        11: 'Семейное кино',
        12: 'Советское родное кино',
        20: 'Кино +'
    }
    return schedules.get(schedule_id)


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
            total_tasks = len(list(task for task in task_list if task.get('Task_sched_date') == day))
            ready_tasks = len(list(task for task in task_list if task.get('Task_task_status') == 'ready' and task.get('Task_sched_date') == day))
            not_ready_tasks = len(list(task for task in task_list if task.get('Task_task_status') == 'not_ready' and task.get('Task_sched_date') == day))
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
    material_list, django_columns = oplan_material_list(work_dates)
    task_list = [dict(zip(django_columns, material)) for material in material_list]
    # task_list = []
    # for material in material_list:
    #     task_list.append(dict(zip(django_columns, material)))
    # print(task_list)
    # channels_id = (2, 3, 4, 5, 6, 7, 8, 9, 10, 12)

    # print(list(filter(lambda task: task.get('SchedDay_schedule_id') == 20, task_list)))
    # channels_list = []
    # for material in material_list:
    #     for schedule_id in schedules_id:
    #         if material[2] == schedule_id:
    #             channels_list.append({schedule_id: dict(zip(django_columns, material))})
    # print(channels_list)
    channels_list = []
    schedules_id = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
    for schedule_id in schedules_id:
        channels_list.append([task for task in task_list if task.get('SchedDay_schedule_id') == schedule_id])

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
    return colorized_calendar, channels_list, service_dict

