import calendar
import os
import datetime

from django.template.defaulttags import register
from django.db import connections

from .distribution import oplan3_engineer


@register.filter
def file_name(full_path):
    if full_path:
        return os.path.basename(full_path)

@register.filter
def dir_name(full_path):
    if full_path:
        return os.path.dirname(full_path).replace('\\\\192.168.80.3\\', "")

@register.filter
def dir_no_host_name(full_path):
    if full_path:
        return full_path.replace('\\\\192.168.80.3\\', "")

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
            program_id_list = []
            total_task_list = []
            for task in task_list:
                if task.get('Progs_program_id') in program_id_list:
                    continue
                if task.get('SchedDay_day_date').date() == day:
                    total_task_list.append(task)
                    program_id_list.append(task.get('Progs_program_id'))

            total_tasks = len(total_task_list)
            ready_tasks = len(list(task for task in total_task_list if task.get('Task_task_status') == 'ready' and task.get('SchedDay_day_date').date() == day))
            not_ready_tasks = len(list(task for task in total_task_list if task.get('Task_task_status') == 'not_ready' and task.get('SchedDay_day_date').date() == day))
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

def oplan_material_list(columns, dates, program_type=(4, 5, 6, 10, 11, 12)):
    start_date, end_date = dates
    with connections['oplan3'].cursor() as cursor:
        schedules_id = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
        order = 'ASC'
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f"""
            SELECT {sql_columns}
            FROM [oplan3].[dbo].[program] AS Progs
            JOIN [oplan3].[dbo].[scheduled_program] AS SchedProg
                ON Progs.[program_id] = SchedProg.[program_id]
            JOIN [oplan3].[dbo].[schedule_day] AS SchedDay
                ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
            JOIN [oplan3].[dbo].[schedule] AS Sched
                ON SchedDay.[schedule_id] = Sched.[schedule_id]
            LEFT JOIN [planner].[dbo].[task_list] AS Task
                ON Progs.[program_id] = Task.[program_id]
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND SchedProg.[Deleted] = 0
            AND SchedDay.[schedule_id] IN {schedules_id}
            AND SchedDay.[day_date] BETWEEN '{start_date}' AND '{end_date}'
            AND Progs.[program_type_id] IN {program_type}
            AND Progs.[program_id] > 0
            ORDER BY SchedProg.[DateTime] {order}
            """
        print(query)
        cursor.execute(query)
        material_list_sql = cursor.fetchall()
    return material_list_sql, django_columns

def report_calendar(cal_year, cal_month, cal_day):
    month_calendar = calendar.Calendar().monthdatescalendar(cal_year, cal_month)
    # columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('SchedDay', 'schedule_id'),
    #            ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'production_year'),
    #            ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
    #            ('Progs', 'duration'), ('Files', 'Name'), ('SchedDay', 'day_date'),
    #            ('Task', 'engineer_id'), ('Task', 'sched_id'), ('Task', 'sched_date'),
    #            ('Task', 'work_date'), ('Task', 'task_status'), ('Task', 'file_path')]
    columns = [
        ('Progs', 'program_id'), ('Progs', 'parent_id'), ('SchedDay', 'schedule_id'),
        ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'production_year'),
        ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'), ('Progs', 'duration'),
        ('SchedDay', 'day_date'), ('Task', 'engineer_id'), ('Task', 'sched_id'),
        ('Task', 'sched_date'), ('Task', 'work_date'), ('Task', 'task_status'), ('Task', 'file_path')
    ]
    program_type = (4, 5, 6, 7, 8, 10, 11, 12, 16, 17, 18, 19, 20)
    material_list, django_columns = oplan_material_list(columns=columns, dates=(cal_day, cal_day), program_type=program_type)

    schedules_id = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
    channels_list = []
    for schedule_id in schedules_id:
        program_id_list = []
        channel = {schedule_id: []}
        for material in material_list:
            if material[2] == schedule_id:
                if material[0] in program_id_list:
                    continue
                temp_dict = dict(zip(django_columns, material))
                if not temp_dict.get('Task_engineer_id') and temp_dict.get('Task_engineer_id') != 0:
                    temp_dict['Task_engineer_id'] = oplan3_engineer(temp_dict['Progs_program_id'])
                channel[schedule_id].append(temp_dict)
                program_id_list.append(material[0])
        channels_list.append(channel)

    # work_dates = tuple(str(day) for day in calendar.Calendar().itermonthdates(cal_year, cal_month) if day.month == cal_month)
    num_days = calendar.monthrange(cal_year, cal_month)[1]
    start_date = datetime.date(cal_year, cal_month, 1)
    end_date = datetime.date(cal_year, cal_month, num_days)

    columns = [('Progs', 'program_id'), ('SchedDay', 'day_date'), ('Task', 'task_status')]

    material_task_list, django_task_columns = oplan_material_list(columns=columns, dates=(start_date, end_date), program_type=program_type)
    task_list = [dict(zip(django_task_columns, material)) for material in material_task_list]
    colorized_calendar = tasks_info(month_calendar, task_list)

    prev_year, prev_month = calc_prev_month(cal_year, cal_month)
    next_year, next_month = calc_next_month(cal_year, cal_month)
    service_dict = {'cal_year': cal_year,
                    'cal_month': cal_month,
                    'cal_day': cal_day,
                    'prev_year': prev_year,
                    'next_year': next_year,
                    'prev_month': prev_month,
                    'next_month': next_month
                    }
    return colorized_calendar, channels_list, service_dict



