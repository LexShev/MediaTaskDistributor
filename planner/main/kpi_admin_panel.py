import datetime

from django.db import connections
from planner.settings import OPLAN_DB, PLANNER_DB


# @register.filter
# def convert_frames_to_time(frames, fps=25):
#     sec = int(frames)/fps
#     return datetime.timedelta(seconds=sec)

def check_mat_type(param):
    if param == 'film':
        return 5, 6, 10, 11
    elif param == 'season':
        return 4, 12
    else:
        return 4, 5, 6, 10, 11, 12

def check_value(key, value):
    if value:
        return f"AND Task.[{key}] = '{value}'"
    else:
        return ''

def summary_task_list(field_dict):
    with connections[PLANNER_DB].cursor() as cursor:
        columns = [
            ('Task', 'program_id'), ('Task', 'engineer_id'), ('Task', 'duration'),
            ('Task', 'work_date'), ('Task', 'sched_date'), ('Task', 'sched_id'), ('Task', 'task_status'), ('Task', 'file_path'),
            ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'orig_name'), ('Progs', 'keywords'),
            ('Progs', 'production_year'), ('Progs', 'episode_num'), ('Files', 'Name'), ('Files', 'Size'),
            ('Files', 'CreationTime'), ('Files', 'ModificationTime')
        ]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT {sql_columns}
        FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
        JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        JOIN [{OPLAN_DB}].[dbo].[Clip] AS Clips
            ON Progs.[SuitableMaterialForScheduleID] = Clips.[MaterialID]
        JOIN [{OPLAN_DB}].[dbo].[File] AS Files
            ON Clips.[ClipID] = Files.[ClipID]
        WHERE Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND Files.[Deleted] = 0
        AND Files.[PhysicallyDeleted] = 0
        AND Clips.[Deleted] = 0
        {check_value('work_date', field_dict.get('work_date'))}
        ORDER BY Progs.[name];
        '''
        cursor.execute(query)
        result = cursor.fetchall()
    return [dict(zip(django_columns, task)) for task in result] or []

def kpi_summary_calc(field_dict):
    task_list = summary_task_list(field_dict)
    count_dates = len(set(task.get('Task_work_date') for task in task_list))
    count_engineers = len(set(task.get('Task_engineer_id') for task in task_list))
    total_count = len(task_list)
    total_dur = sum(task.get('Task_duration') for task in task_list)
    ready_tasks = len(list(filter(lambda task: task.get('Task_task_status') == 'ready', task_list)))
    not_ready_tasks = len(list(filter(lambda task: task.get('Task_task_status') == 'not_ready', task_list)))
    ready_dur = sum(task.get('Task_duration') for task in task_list if task.get('Task_task_status') == 'ready')
    not_ready_dur = sum(task.get('Task_duration') for task in task_list if task.get('Task_task_status') == 'not_ready')
    try:
        total_kpi = total_dur / (720000.0 * count_dates * count_engineers)
        ready_kpi = ready_dur / (720000.0 * count_dates * count_engineers)
    except Exception as e:
        total_kpi = 0
        ready_kpi = 0
        print(e)
    summary_dict = {'total_count': total_count, 'total_dur': total_dur, 'ready_tasks': ready_tasks,
                    'not_ready_tasks': not_ready_tasks, 'ready_dur': ready_dur, 'not_ready_dur': not_ready_dur,
                    'total_kpi': total_kpi, 'ready_kpi': ready_kpi}
    engineer_id = field_dict.get('engineer_id')
    if engineer_id:
        engineer_id = int(engineer_id)
    material_type = field_dict.get('material_type')
    task_status = field_dict.get('task_status')
    filtered_task_list = filter(lambda task: task.get('Task_engineer_id') == engineer_id or not engineer_id and engineer_id != 0, task_list)
    filtered_task_list = filter(lambda task: task.get('Progs_program_type_id') in check_mat_type(material_type) or not material_type, filtered_task_list)
    filtered_task_list = filter(lambda task: task.get('Task_task_status') == task_status or not task_status, filtered_task_list)

    return filtered_task_list, summary_dict


def personal_task_list(field_dict):
    with connections[PLANNER_DB].cursor() as cursor:
        columns = [('Task', 'program_id'), ('Task', 'engineer_id'), ('Task', 'duration'),
                   ('Task', 'work_date'), ('Task', 'task_status'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                   ('Progs', 'orig_name'), ('Progs', 'keywords'), ('Progs', 'production_year')]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT {sql_columns}
        FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
        JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        WHERE Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        {check_value('work_date', field_dict.get('work_date'))}
        {check_value('engineer_id', field_dict.get('engineer_id'))}
        '''
        cursor.execute(query)
        result = cursor.fetchall()
    return [dict(zip(django_columns, task)) for task in result] or []

def kpi_personal_calc(field_dict):
    task_list = personal_task_list(field_dict)
    total_count = len(task_list)
    total_dur = sum(task.get('Task_duration') for task in task_list)
    ready_tasks = len(list(filter(lambda task: task.get('Task_task_status') == 'ready', task_list)))
    not_ready_tasks = len(list(filter(lambda task: task.get('Task_task_status') == 'not_ready', task_list)))
    ready_dur = sum(task.get('Task_duration') for task in task_list if task.get('Task_task_status') == 'ready')
    not_ready_dur = sum(task.get('Task_duration') for task in task_list if task.get('Task_task_status') == 'not_ready')
    total_kpi = total_dur / 720000.0
    ready_kpi = ready_dur / 720000.0
    summary_dict = {'total_count': total_count, 'total_dur': total_dur, 'ready_tasks': ready_tasks,
                    'not_ready_tasks': not_ready_tasks, 'ready_dur': ready_dur, 'not_ready_dur': not_ready_dur,
                    'total_kpi': total_kpi, 'ready_kpi': ready_kpi}
    material_type = field_dict.get('material_type')
    task_status = field_dict.get('task_status')
    filtered_task_list = filter(lambda task: task.get('Progs_program_type_id') in check_mat_type(material_type) or not material_type, task_list)
    filtered_task_list = filter(lambda task: task.get('Task_task_status') == task_status or not task_status, filtered_task_list)
    return filtered_task_list, summary_dict


def filter_task_list(task_list, date):
    return filter(lambda x: x['Task_work_date'] == date, task_list)
