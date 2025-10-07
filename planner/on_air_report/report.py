import calendar
import datetime

from django.core.cache import cache
from django.db import connections

from main.templatetags.custom_filters import engineer_id_to_worker_id
from planner.settings import OPLAN_DB, PLANNER_DB


# program_type = (4, 5, 6, 7, 8, 10, 11, 12, 16, 17, 18, 19, 20)



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
            ready_tasks = len(list(task for task in total_task_list if task.get('Task_task_status')
                                   in ('ready', 'final', 'otk') and task.get('SchedDay_day_date').date() == day))
            not_ready_tasks = len(list(task for task in total_task_list if task.get('Task_task_status')
                                       not in ('ready', 'final', 'otk') and task.get('SchedDay_day_date').date() == day))
            try:
                ready_index = (ready_tasks * 100) / total_tasks
            except Exception as e:
                print(e)
                ready_index = 'day_off'
            #     проверка на отсутствие задач в текущий день
            if ready_index == 'day_off':
                color = ''
            elif ready_index > 70:
                color = 'btn-outline-success'
            elif 30 < ready_index < 70:
                color = 'btn-outline-warning'
            else:
                color = 'btn-outline-danger'
            colorized_weeks.append(
                {'day': day,
                'ready_tasks': ready_tasks,
                'not_ready_tasks': not_ready_tasks,
                'ready_index': ready_index,
                'color': color})
        colorized_calendar.append(colorized_weeks)
    return colorized_calendar

def oplan_material_list(columns, dates, schedules_id=(3, 5, 6, 7, 8, 9, 10, 11, 12, 20), program_type=(4, 5, 6, 10, 11, 12)):
    start_date, end_date = dates
    with connections[OPLAN_DB].cursor() as cursor:
        order = 'ASC'
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f"""
            SELECT {sql_columns}
            FROM [{OPLAN_DB}].[dbo].[program] AS Progs
            JOIN [{OPLAN_DB}].[dbo].[scheduled_program] AS SchedProg
                ON Progs.[program_id] = SchedProg.[program_id]
            JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
                ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
            JOIN [{OPLAN_DB}].[dbo].[schedule] AS Sched
                ON SchedDay.[schedule_id] = Sched.[schedule_id]
            LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
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
        cursor.execute(query)
        material_list_sql = cursor.fetchall()
    return material_list_sql, django_columns

def report_calendar(cal_year, cal_month):
    cache_key = f'calendar_{cal_year}_{cal_month}'
    result_cash = cache.get(cache_key)
    # if result_cash:
    #     return result_cash
    month_calendar = calendar.Calendar().monthdatescalendar(cal_year, cal_month)

    # work_dates = tuple(str(day) for day in calendar.Calendar().itermonthdates(cal_year, cal_month) if day.month == cal_month)
    num_days = calendar.monthrange(cal_year, cal_month)[1]
    start_date = datetime.date(cal_year, cal_month, 1)
    end_date = datetime.date(cal_year, cal_month, num_days)

    columns = [('Progs', 'program_id'), ('SchedDay', 'day_date'), ('Task', 'task_status')]

    material_task_list, django_task_columns = oplan_material_list(columns=columns, dates=(start_date, end_date))
    task_list = [dict(zip(django_task_columns, material)) for material in material_task_list]
    colorized_calendar = tasks_info(month_calendar, task_list)
    cache.set(cache_key, colorized_calendar, timeout=60*60*24)  # Кеш на 24 часа
    return colorized_calendar

def prepare_service_dict(cal_year, cal_month, cal_day, cal_date):
    # prev_year, prev_month = calc_prev_month(cal_year, cal_month)
    # next_year, next_month = calc_next_month(cal_year, cal_month)
    print(cal_year, cal_month, cal_day, cal_date)
    if isinstance(cal_date, str):
        cal_date = datetime.datetime.strptime(cal_date, '%Y-%m-%d')
    prev_date = cal_date - datetime.timedelta(days=1)
    next_date = cal_date + datetime.timedelta(days=1)
    service_dict = {
        'cal_year': cal_year,
        'cal_month': cal_month,
        'cal_day': cal_day,
        'cal_date': cal_date,
        'prev_date': prev_date,
        'next_date': next_date,
    }
    return service_dict

def collect_channels_list(cal_day):
    columns = [
        ('Progs', 'program_id'), ('Progs', 'parent_id'), ('SchedDay', 'schedule_id'),
        ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'production_year'),
        ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'), ('Progs', 'duration'),
        ('SchedDay', 'day_date'), ('Task', 'worker_id'), ('Task', 'sched_id'),
        ('Task', 'sched_date'), ('Task', 'work_date'), ('Task', 'task_status'), ('Task', 'file_path')
    ]
    material_list, django_columns = oplan_material_list(columns=columns, dates=(cal_day, cal_day))
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
                # if not temp_dict.get('Task_file_path'):
                temp_dict['Files_Name'] = find_file_path(temp_dict.get('Progs_program_id'))
                if not temp_dict.get('Task_worker_id') and temp_dict.get('Task_worker_id') != 0:
                    temp_dict['Task_worker_id'] = oplan3_engineer(temp_dict['Progs_program_id'])
                channel[schedule_id].append(temp_dict)
                program_id_list.append(material[0])
        channels_list.append(channel)
    return channels_list

def task_list_for_channel(sched_date, schedule_id, program_type=(4, 5, 6, 7, 8, 10, 11, 12, 16, 19, 20)):
    columns = [
        ('Progs', 'program_id'), ('Progs', 'parent_id'), ('SchedDay', 'schedule_id'),
        ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'production_year'),
        ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'), ('Progs', 'duration'),
        ('SchedDay', 'day_date'), ('SchedProg', 'DateTime'), ('Task', 'worker_id'), ('Task', 'sched_id'),
        ('Task', 'sched_date'), ('Task', 'work_date'), ('Task', 'task_status'), ('Task', 'file_path')
    ]

    with connections[OPLAN_DB].cursor() as cursor:
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f"""
            SELECT DISTINCT {sql_columns}
            FROM [{OPLAN_DB}].[dbo].[program] AS Progs
            JOIN [{OPLAN_DB}].[dbo].[scheduled_program] AS SchedProg
                ON Progs.[program_id] = SchedProg.[program_id]
            JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
                ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
            JOIN [{OPLAN_DB}].[dbo].[schedule] AS Sched
                ON SchedDay.[schedule_id] = Sched.[schedule_id]
            LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
                ON Progs.[program_id] = Task.[program_id]
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND SchedProg.[Deleted] = 0
            AND SchedDay.[schedule_id] = {schedule_id}
            AND SchedDay.[day_date] = '{sched_date}'
            AND Progs.[program_type_id] IN {program_type}
            AND Progs.[program_id] > 0
            ORDER BY SchedProg.[DateTime] ASC
            """
        cursor.execute(query)
        material_list = cursor.fetchall()
        task_list = []
        program_id_list = []
        for material in material_list:
            if material[2] == schedule_id:
                if material[0] in program_id_list:
                    continue
                temp_dict = dict(zip(django_columns, material))
                # if not temp_dict.get('Task_file_path'):
                temp_dict['Files_Name'] = find_file_path(temp_dict.get('Progs_program_id'))
                if not temp_dict.get('Task_worker_id') and temp_dict.get('Task_worker_id') != 0:
                    temp_dict['Task_worker_id'] = oplan3_engineer(temp_dict['Progs_program_id'])
                task_list.append(temp_dict)
                program_id_list.append(material[0])
        # print(task_list)
        return task_list

def oplan3_engineer(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        query_oplan3 = f'''
        SELECT [IntValue]
        FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues] 
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = 15
        '''
        cursor.execute(query_oplan3)
        oplan3_engineer_id = cursor.fetchone()
        if oplan3_engineer_id:
            return engineer_id_to_worker_id(oplan3_engineer_id[0])
        return None

def find_file_path(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT Files.[Name]
        FROM [{OPLAN_DB}].[dbo].[File] AS Files
        JOIN [{OPLAN_DB}].[dbo].[Clip] AS Clips
            ON Files.[ClipID] = Clips.[ClipID]
        JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
            ON Clips.[MaterialID] = Progs.[SuitableMaterialForScheduleID]
        WHERE Files.[Deleted] = 0
        AND Files.[PhysicallyDeleted] = 0
        AND Clips.[Deleted] = 0
        AND Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND Progs.[program_id] = {program_id}
        '''
        cursor.execute(query)
        file_path = cursor.fetchone()
    if file_path:
        return file_path[0]
    return None